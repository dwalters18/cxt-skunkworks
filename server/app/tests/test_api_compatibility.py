"""
API Compatibility Validation Tests

This module validates that API request and response models are compatible
with actual API endpoints and maintain consistency across system layers.
"""
import pytest
import sys
import os
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
from uuid import uuid4
import json
from decimal import Decimal
from pydantic import ValidationError

# Add the parent directory to the Python path to fix imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.domain import (
    Load, Vehicle, Driver, Route, Carrier, Location,
    LoadStatus, VehicleStatus, DriverStatus, EntityStatus,
    CreateLoadRequest, AssignLoadRequest, UpdateLocationRequest,
    LoadSearchRequest, VehicleTrackingData, PerformanceMetric,
    RoutePrediction, LoadMatchingRequest, OptimizationRequest,
    BaseEntity, Shipment, LoadResponse, VehicleResponse, DriverResponse
)

from models.events import (
    EventType, BaseEvent, LoadCreatedEvent, LoadAssignedEvent,
    LoadStatusEvent, VehicleLocationEvent, VehicleStatusEvent,
    DriverStatusEvent, RouteOptimizedEvent, RouteDeviationEvent,
    AIPredictionEvent, SystemAlertEvent, create_event
)


class TestAPIRequestValidation:
    """Test API request models validate correctly"""
    
    def test_create_load_request_valid_data(self):
        """Test CreateLoadRequest accepts valid load data"""
        
        valid_request_data = {
            "load_number": "LOAD-2025-001",
            "pickup_address": "123 Main Street, New York, NY 10001",
            "delivery_address": "456 Oak Avenue, Los Angeles, CA 90210",
            "pickup_datetime": datetime.now(timezone.utc),
            "delivery_datetime": datetime.now(timezone.utc).replace(hour=23),
            "weight": 25000.0,
            "volume": 1500.0,
            "rate": 2500.00,
            "notes": "Handle with care"
        }
        
        request = CreateLoadRequest(**valid_request_data)
        
        # Verify all fields are properly set
        assert request.load_number == "LOAD-2025-001"
        assert request.pickup_address == "123 Main Street, New York, NY 10001"
        assert request.delivery_address == "456 Oak Avenue, Los Angeles, CA 90210"
        assert request.weight == 25000.0
        assert request.volume == 1500.0
        assert request.rate == 2500.00
        assert request.notes == "Handle with care"
        
        # Verify datetime fields are timezone-aware
        assert request.pickup_datetime.tzinfo is not None
        assert request.delivery_datetime.tzinfo is not None
    
    def test_create_load_request_missing_required_fields(self):
        """Test CreateLoadRequest validation fails for missing required fields"""
        
        # Missing load_number (required)
        with pytest.raises(ValidationError) as exc_info:
            CreateLoadRequest(
                pickup_address="123 Main St",
                delivery_address="456 Oak Ave",
                pickup_datetime=datetime.now(timezone.utc),
                delivery_datetime=datetime.now(timezone.utc)
            )
        
        assert "load_number" in str(exc_info.value)
        
        # Missing pickup_address (required)
        with pytest.raises(ValidationError) as exc_info:
            CreateLoadRequest(
                load_number="LOAD-001",
                delivery_address="456 Oak Ave", 
                pickup_datetime=datetime.now(timezone.utc),
                delivery_datetime=datetime.now(timezone.utc)
            )
        
        assert "pickup_address" in str(exc_info.value)
    
    def test_assign_load_request_valid_data(self):
        """Test AssignLoadRequest accepts valid assignment data"""
        
        valid_request_data = {
            "load_id": str(uuid4()),
            "carrier_id": str(uuid4()),
            "vehicle_id": str(uuid4()),
            "driver_id": str(uuid4()),
            "estimated_pickup_time": datetime.now(timezone.utc),
            "estimated_delivery_time": datetime.now(timezone.utc).replace(hour=23)
        }
        
        request = AssignLoadRequest(**valid_request_data)
        
        # Verify UUID fields
        assert request.load_id
        assert request.carrier_id
        assert request.vehicle_id
        assert request.driver_id
        
        # Verify optional datetime fields
        assert request.estimated_pickup_time.tzinfo is not None
        assert request.estimated_delivery_time.tzinfo is not None
    
    def test_assign_load_request_uuid_validation(self):
        """Test AssignLoadRequest validates UUID format"""
        
        # Invalid UUID should raise validation error
        with pytest.raises(ValidationError):
            AssignLoadRequest(
                load_id="not-a-uuid",
                carrier_id=str(uuid4()),
                vehicle_id=str(uuid4()),
                driver_id=str(uuid4())
            )
    
    def test_update_location_request_valid_data(self):
        """Test UpdateLocationRequest accepts valid location data"""
        
        valid_request_data = {
            "entity_id": str(uuid4()),
            "entity_type": "vehicle",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "speed": 65.5,
            "heading": 180.0,
            "timestamp": datetime.now(timezone.utc)
        }
        
        request = UpdateLocationRequest(**valid_request_data)
        
        # Verify coordinate validation
        assert -90 <= request.latitude <= 90
        assert -180 <= request.longitude <= 180
        assert request.speed >= 0 if request.speed is not None else True
        assert 0 <= request.heading < 360 if request.heading is not None else True
        assert request.timestamp.tzinfo is not None


class TestAPIResponseValidation:
    """Test API response models match domain models"""
    
    def test_load_response_domain_compatibility(self):
        """Test LoadResponse matches Load domain model"""
        
        # Create domain Load
        domain_load = Load(
            load_number="LOAD-2025-001",
            pickup_location=Location(latitude=40.7128, longitude=-74.0060),
            delivery_location=Location(latitude=34.0522, longitude=-118.2437),
            pickup_address="New York, NY",
            delivery_address="Los Angeles, CA",
            pickup_datetime=datetime.now(timezone.utc),
            delivery_datetime=datetime.now(timezone.utc).replace(hour=23),
            weight=25000.0,
            volume=1500.0,
            rate=2500.00,
            status=LoadStatus.PENDING
        )
        
        # Convert to API response
        response_data = {
            "id": domain_load.id,
            "load_number": domain_load.load_number,
            "pickup_location": {
                "latitude": domain_load.pickup_location.latitude,
                "longitude": domain_load.pickup_location.longitude
            },
            "delivery_location": {
                "latitude": domain_load.delivery_location.latitude,
                "longitude": domain_load.delivery_location.longitude
            },
            "pickup_address": domain_load.pickup_address,
            "delivery_address": domain_load.delivery_address,
            "pickup_datetime": domain_load.pickup_datetime,
            "delivery_datetime": domain_load.delivery_datetime,
            "weight": domain_load.weight,
            "volume": domain_load.volume,
            "rate": domain_load.rate,
            "status": domain_load.status.value,
            "created_at": domain_load.created_at,
            "updated_at": domain_load.updated_at
        }
        
        response = LoadResponse(**response_data)
        
        # Verify compatibility
        assert response.id == domain_load.id
        assert response.load_number == domain_load.load_number
        assert response.pickup_location.latitude == domain_load.pickup_location.latitude
        assert response.pickup_location.longitude == domain_load.pickup_location.longitude
        assert response.status == domain_load.status.value
    
    def test_vehicle_response_domain_compatibility(self):
        """Test VehicleResponse matches Vehicle domain model"""
        
        domain_vehicle = Vehicle(
            carrier_id=str(uuid4()),
            vehicle_number="TRUCK-001",
            vehicle_type="DRY_VAN",
            capacity_weight=40000.0,
            capacity_volume=2500.0,
            status=VehicleStatus.AVAILABLE,
            current_location=Location(latitude=40.7128, longitude=-74.0060)
        )
        
        response_data = {
            "id": domain_vehicle.id,
            "carrier_id": domain_vehicle.carrier_id,
            "vehicle_number": domain_vehicle.vehicle_number,
            "vehicle_type": domain_vehicle.vehicle_type,
            "capacity_weight": domain_vehicle.capacity_weight,
            "capacity_volume": domain_vehicle.capacity_volume,
            "status": domain_vehicle.status.value,
            "current_location": {
                "latitude": domain_vehicle.current_location.latitude,
                "longitude": domain_vehicle.current_location.longitude
            } if domain_vehicle.current_location else None,
            "created_at": domain_vehicle.created_at,
            "updated_at": domain_vehicle.updated_at
        }
        
        response = VehicleResponse(**response_data)
        
        assert response.id == domain_vehicle.id
        assert response.vehicle_number == domain_vehicle.vehicle_number
        assert response.status == domain_vehicle.status.value
    
    def test_driver_response_domain_compatibility(self):
        """Test DriverResponse matches Driver domain model"""
        
        domain_driver = Driver(
            carrier_id=str(uuid4()),
            license_number="DL123456789",
            name="John Driver",
            status=DriverStatus.AVAILABLE,
            phone="555-123-4567",
            email="john.driver@example.com"
        )
        
        response_data = {
            "id": domain_driver.id,
            "carrier_id": domain_driver.carrier_id,
            "license_number": domain_driver.license_number,
            "name": domain_driver.name,
            "status": domain_driver.status.value,
            "phone": domain_driver.phone,
            "email": domain_driver.email,
            "current_location": None,
            "hours_remaining": domain_driver.hours_remaining,
            "created_at": domain_driver.created_at,
            "updated_at": domain_driver.updated_at
        }
        
        response = DriverResponse(**response_data)
        
        assert response.id == domain_driver.id
        assert response.name == domain_driver.name
        assert response.status == domain_driver.status.value


class TestEventAPICompatibility:
    """Test event models are compatible with API endpoints"""
    
    def test_event_publish_api_compatibility(self):
        """Test events can be serialized for API publishing"""
        
        # Create event
        event = LoadCreatedEvent(
            source="tms-api",
            data={
                "load_id": str(uuid4()),
                "load_number": "LOAD-2025-001",
                "pickup_address": "New York, NY",
                "delivery_address": "Los Angeles, CA",
                "weight": 25000.0,
                "rate": 2500.00,
                "status": "CREATED"
            }
        )
        
        # Serialize to dict (as would happen in API)
        event_dict = event.model_dump()
        
        # Verify API-compatible structure
        assert "event_id" in event_dict
        assert "event_type" in event_dict
        assert "timestamp" in event_dict
        assert "source" in event_dict
        assert "data" in event_dict
        assert "metadata" in event_dict
        assert "version" in event_dict
        
        # Verify event type is string
        assert isinstance(event_dict["event_type"], str)
        assert event_dict["event_type"] == "LOAD_CREATED"
        
        # Verify timestamp is serializable
        assert isinstance(event_dict["timestamp"], (str, datetime))
    
    def test_route_optimized_event_api_compatibility(self):
        """Test RouteOptimizedEvent matches API expectations"""
        
        event = RouteOptimizedEvent(
            source="route-optimization-service",
            data={
                "route_id": str(uuid4()),
                "load_ids": [str(uuid4()), str(uuid4())],
                "optimization_score": 0.85,
                "traffic_considered": True,
                "fuel_estimate": 45.50,
                "estimated_duration": 480,
                "distance_miles": 350.2
            }
        )
        
        event_dict = event.model_dump()
        
        # Verify route optimization specific fields
        assert event_dict["event_type"] == "ROUTE_OPTIMIZED"
        assert "route_id" in event_dict["data"]
        assert "load_ids" in event_dict["data"]
        assert "optimization_score" in event_dict["data"]
        assert "traffic_considered" in event_dict["data"]
        
        # Verify data types for JSON serialization
        assert isinstance(event_dict["data"]["optimization_score"], (int, float))
        assert isinstance(event_dict["data"]["traffic_considered"], bool)
        assert isinstance(event_dict["data"]["load_ids"], list)


class TestCrossLayerCompatibility:
    """Test compatibility between API, Domain, and Event layers"""
    
    def test_load_creation_workflow_compatibility(self):
        """Test complete load creation workflow across layers"""
        
        # 1. API Request
        api_request = CreateLoadRequest(
            load_number="LOAD-2025-001",
            pickup_address="New York, NY",
            delivery_address="Los Angeles, CA",
            pickup_datetime=datetime.now(timezone.utc),
            delivery_datetime=datetime.now(timezone.utc).replace(hour=23),
            weight=25000.0,
            rate=2500.00
        )
        
        # 2. Domain Model Creation
        domain_load = Load(
            load_number=api_request.load_number,
            pickup_location=Location(latitude=40.7128, longitude=-74.0060),
            delivery_location=Location(latitude=34.0522, longitude=-118.2437),
            pickup_address=api_request.pickup_address,
            delivery_address=api_request.delivery_address,
            pickup_datetime=api_request.pickup_datetime,
            delivery_datetime=api_request.delivery_datetime,
            weight=api_request.weight,
            rate=api_request.rate,
            status=LoadStatus.PENDING
        )
        
        # 3. Event Creation
        event = LoadCreatedEvent(
            source="tms-api",
            data={
                "load_id": domain_load.id,
                "load_number": domain_load.load_number,
                "pickup_address": domain_load.pickup_address,
                "delivery_address": domain_load.delivery_address,
                "weight": domain_load.weight,
                "rate": domain_load.rate,
                "status": domain_load.status.value
            }
        )
        
        # 4. API Response
        api_response = LoadResponse(
            id=domain_load.id,
            load_number=domain_load.load_number,
            pickup_location=domain_load.pickup_location,
            delivery_location=domain_load.delivery_location,
            pickup_address=domain_load.pickup_address,
            delivery_address=domain_load.delivery_address,
            pickup_datetime=domain_load.pickup_datetime,
            delivery_datetime=domain_load.delivery_datetime,
            weight=domain_load.weight,
            rate=domain_load.rate,
            status=domain_load.status.value,
            created_at=domain_load.created_at,
            updated_at=domain_load.updated_at
        )
        
        # Verify consistency across all layers
        assert api_request.load_number == domain_load.load_number == event.data["load_number"] == api_response.load_number
        assert api_request.pickup_address == domain_load.pickup_address == event.data["pickup_address"] == api_response.pickup_address
        assert api_request.weight == domain_load.weight == event.data["weight"] == api_response.weight
        assert api_request.rate == domain_load.rate == event.data["rate"] == api_response.rate
    
    def test_vehicle_assignment_workflow_compatibility(self):
        """Test vehicle assignment workflow across layers"""
        
        # API Assignment Request
        assignment_request = AssignLoadRequest(
            load_id=str(uuid4()),
            carrier_id=str(uuid4()),
            vehicle_id=str(uuid4()),
            driver_id=str(uuid4()),
            estimated_pickup_time=datetime.now(timezone.utc),
            estimated_delivery_time=datetime.now(timezone.utc).replace(hour=12)
        )
        
        # Domain Model Updates (simulated)
        updated_load_status = LoadStatus.ASSIGNED
        updated_vehicle_status = VehicleStatus.ASSIGNED
        updated_driver_status = DriverStatus.DRIVING
        
        # Event Creation
        assignment_event = LoadAssignedEvent(
            source="tms-api",
            data={
                "load_id": assignment_request.load_id,
                "carrier_id": assignment_request.carrier_id,
                "vehicle_id": assignment_request.vehicle_id,
                "driver_id": assignment_request.driver_id,
                "estimated_pickup_time": assignment_request.estimated_pickup_time.isoformat(),
                "estimated_delivery_time": assignment_request.estimated_delivery_time.isoformat()
            }
        )
        
        # Verify assignment consistency
        assert assignment_event.data["load_id"] == assignment_request.load_id
        assert assignment_event.data["vehicle_id"] == assignment_request.vehicle_id
        assert assignment_event.data["driver_id"] == assignment_request.driver_id
        assert assignment_event.event_type == EventType.LOAD_ASSIGNED


class TestValidationConsistency:
    """Test validation rules are consistent across layers"""
    
    def test_coordinate_validation_consistency(self):
        """Test coordinate validation is consistent across all models"""
        
        valid_lat, valid_lon = 40.7128, -74.0060
        invalid_lat, invalid_lon = 91.0, 181.0
        
        # Location model validation
        location = Location(latitude=valid_lat, longitude=valid_lon)
        assert location.latitude == valid_lat
        assert location.longitude == valid_lon
        
        with pytest.raises(ValidationError):
            Location(latitude=invalid_lat, longitude=valid_lon)
        
        # UpdateLocationRequest validation
        location_request = UpdateLocationRequest(
            entity_id=str(uuid4()),
            entity_type="vehicle",
            latitude=valid_lat,
            longitude=valid_lon,
            timestamp=datetime.now(timezone.utc)
        )
        assert location_request.latitude == valid_lat
        
        with pytest.raises(ValidationError):
            UpdateLocationRequest(
                entity_id=str(uuid4()),
                entity_type="vehicle",
                latitude=invalid_lat,
                longitude=valid_lon,
                timestamp=datetime.now(timezone.utc)
            )
    
    def test_datetime_validation_consistency(self):
        """Test datetime validation is consistent across models"""
        
        utc_datetime = datetime.now(timezone.utc)
        naive_datetime = datetime.now()  # No timezone
        
        # All models should accept timezone-aware datetimes
        load_request = CreateLoadRequest(
            load_number="LOAD-001",
            pickup_address="New York",
            delivery_address="Los Angeles",
            pickup_datetime=utc_datetime,
            delivery_datetime=utc_datetime.replace(hour=23)
        )
        
        assert load_request.pickup_datetime.tzinfo is not None
        assert load_request.delivery_datetime.tzinfo is not None
    
    def test_enum_validation_consistency(self):
        """Test enum validation is consistent across layers"""
        
        # Valid enum values should work across all models
        valid_load_status = LoadStatus.PENDING
        valid_vehicle_status = VehicleStatus.AVAILABLE
        valid_driver_status = DriverStatus.AVAILABLE
        
        # Domain models
        load = Load(
            load_number="LOAD-001",
            pickup_location=Location(latitude=40.7128, longitude=-74.0060),
            delivery_location=Location(latitude=34.0522, longitude=-118.2437),
            pickup_address="New York",
            delivery_address="Los Angeles",
            pickup_datetime=datetime.now(timezone.utc),
            delivery_datetime=datetime.now(timezone.utc),
            status=valid_load_status
        )
        
        vehicle = Vehicle(
            carrier_id=str(uuid4()),
            vehicle_number="TRUCK-001",
            vehicle_type="DRY_VAN",
            capacity_weight=40000.0,
            capacity_volume=2500.0,
            status=valid_vehicle_status
        )
        
        driver = Driver(
            carrier_id=str(uuid4()),
            license_number="DL123456789",
            name="Test Driver",
            status=valid_driver_status
        )
        
        # Verify enum values are consistent
        assert load.status == valid_load_status
        assert vehicle.status == valid_vehicle_status
        assert driver.status == valid_driver_status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
