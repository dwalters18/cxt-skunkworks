"""
Comprehensive PRD Alignment Validation Tests

This module contains tests to validate that all TMS domain models, event models,
and API request/response models are strictly aligned with Product Requirements Documents (PRDs).
"""
import pytest
import sys
import os
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from uuid import uuid4
from decimal import Decimal
from pydantic import ValidationError

# Add the parent directory to the Python path to fix imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import domain models
from models.domain import (
    Load, Vehicle, Driver, Route, Carrier, Location,
    LoadStatus, VehicleStatus, DriverStatus, EntityStatus,
    CreateLoadRequest, AssignLoadRequest, UpdateLocationRequest,
    LoadSearchRequest, VehicleTrackingData, PerformanceMetric,
    RoutePrediction, LoadMatchingRequest, OptimizationRequest,
    BaseEntity, Shipment
)

# Import event models
from models.events import (
    EventType, BaseEvent, LoadCreatedEvent, LoadAssignedEvent,
    LoadStatusEvent, VehicleLocationEvent, VehicleStatusEvent,
    DriverStatusEvent, RouteOptimizedEvent, RouteDeviationEvent,
    AIPredictionEvent, SystemAlertEvent, create_event
)


class TestPRDDomainModelAlignment:
    """Test domain models align with PRD Database Schema specifications"""

    def test_load_model_prd_compliance(self):
        """Validate Load model matches PRD-Database-Schema.md loads table"""

        # Test required fields from PRD
        valid_load_data = {
            "load_number": "LOAD-2025-001",
            "pickup_location": Location(latitude=40.7128, longitude=-74.0060),
            "delivery_location": Location(latitude=34.0522, longitude=-118.2437),
            "pickup_address": "123 Main St, New York, NY 10001",
            "delivery_address": "456 Oak Ave, Los Angeles, CA 90210",
            "pickup_datetime": datetime.now(timezone.utc),
            "delivery_datetime": datetime.now(timezone.utc),
            "status": LoadStatus.PENDING
        }

        load = Load(**valid_load_data)

        # Verify PRD-required fields exist
        assert hasattr(load, 'id')
        assert hasattr(load, 'created_at')
        assert hasattr(load, 'updated_at')
        assert hasattr(load, 'load_number')
        assert hasattr(load, 'pickup_location')
        assert hasattr(load, 'delivery_location')
        assert hasattr(load, 'pickup_address')
        assert hasattr(load, 'delivery_address')
        assert hasattr(load, 'pickup_datetime')
        assert hasattr(load, 'delivery_datetime')
        assert hasattr(load, 'weight')
        assert hasattr(load, 'volume')
        assert hasattr(load, 'rate')
        assert hasattr(load, 'status')

        # Verify enum values match PRD
        assert load.status in [LoadStatus.PENDING, LoadStatus.ASSIGNED,
                              LoadStatus.PICKED_UP, LoadStatus.IN_TRANSIT,
                              LoadStatus.DELIVERED, LoadStatus.CANCELLED,
                              LoadStatus.DELAYED]

    def test_vehicle_model_prd_compliance(self):
        """Validate Vehicle model matches PRD vehicle table schema"""

        valid_vehicle_data = {
            "carrier_id": str(uuid4()),
            "vehicle_number": "TRUCK-001",
            "vehicle_type": "DRY_VAN",
            "capacity_weight": 40000.0,
            "capacity_volume": 2500.0,
            "status": VehicleStatus.AVAILABLE
        }

        vehicle = Vehicle(**valid_vehicle_data)

        # Verify PRD-required fields exist
        assert hasattr(vehicle, 'id')
        assert hasattr(vehicle, 'carrier_id')
        assert hasattr(vehicle, 'vehicle_number')
        assert hasattr(vehicle, 'vehicle_type')
        assert hasattr(vehicle, 'capacity_weight')
        assert hasattr(vehicle, 'capacity_volume')
        assert hasattr(vehicle, 'status')
        assert hasattr(vehicle, 'current_location')
        assert hasattr(vehicle, 'fuel_level')
        assert hasattr(vehicle, 'odometer')

        # Test enum values
        assert vehicle.status in [VehicleStatus.AVAILABLE, VehicleStatus.ASSIGNED,
                                 VehicleStatus.IN_TRANSIT, VehicleStatus.MAINTENANCE,
                                 VehicleStatus.OUT_OF_SERVICE]

    def test_driver_model_prd_compliance(self):
        """Validate Driver model matches PRD driver table schema"""

        valid_driver_data = {
            "carrier_id": str(uuid4()),
            "license_number": "DL123456789",
            "name": "John Driver",
            "status": DriverStatus.AVAILABLE
        }

        driver = Driver(**valid_driver_data)

        # Verify PRD-required fields exist
        assert hasattr(driver, 'id')
        assert hasattr(driver, 'carrier_id')
        assert hasattr(driver, 'license_number')
        assert hasattr(driver, 'name')
        assert hasattr(driver, 'phone')
        assert hasattr(driver, 'email')
        assert hasattr(driver, 'status')
        assert hasattr(driver, 'current_location')
        assert hasattr(driver, 'hours_remaining')

        # Test enum values
        assert driver.status in [DriverStatus.AVAILABLE, DriverStatus.DRIVING,
                                DriverStatus.ON_DUTY, DriverStatus.OFF_DUTY,
                                DriverStatus.SLEEPER_BERTH]

    def test_location_model_spatial_compliance(self):
        """Validate Location model supports PostGIS GEOGRAPHY requirements"""

        # Test valid coordinates
        location = Location(latitude=40.7128, longitude=-74.0060)
        assert isinstance(location.latitude, float)
        assert isinstance(location.longitude, float)
        assert -90 <= location.latitude <= 90
        assert -180 <= location.longitude <= 180

        # Test invalid coordinates should raise validation error
        with pytest.raises(ValidationError):
            Location(latitude=91.0, longitude=0.0)  # Invalid latitude

        with pytest.raises(ValidationError):
            Location(latitude=0.0, longitude=181.0)  # Invalid longitude


class TestPRDEventModelAlignment:
    """Test event models align with PRD-Events-Schema.md specifications"""

    def test_base_event_structure(self):
        """Validate BaseEvent matches PRD base event structure"""

        event_data = {
            "event_type": EventType.LOAD_CREATED,
            "source": "tms-api",
            "data": {"load_id": str(uuid4())}
        }

        event = BaseEvent(**event_data)

        # Verify PRD-required fields exist
        assert hasattr(event, 'event_id')
        assert hasattr(event, 'event_type')
        assert hasattr(event, 'timestamp')
        assert hasattr(event, 'source')
        assert hasattr(event, 'correlation_id')
        assert hasattr(event, 'version')
        assert hasattr(event, 'metadata')

        # Verify default values
        assert event.version == "1.0"
        assert isinstance(event.metadata, dict)

    def test_event_types_prd_compliance(self):
        """Validate all EventType enums match PRD-Events-Schema.md"""

        # Load Events (from PRD)
        prd_load_events = [
            "LOAD_CREATED", "LOAD_ASSIGNED", "LOAD_PICKED_UP", "LOAD_IN_TRANSIT",
            "LOAD_DELIVERED", "LOAD_CANCELLED", "LOAD_DELAYED", "LOAD_UPDATED"
        ]

        # Vehicle Events (from PRD)
        prd_vehicle_events = [
            "VEHICLE_LOCATION_UPDATED", "VEHICLE_STATUS_CHANGED", "VEHICLE_MAINTENANCE_DUE",
            "VEHICLE_BREAKDOWN", "VEHICLE_FUEL_LOW", "VEHICLE_ASSIGNED", "VEHICLE_INSPECTION_DUE"
        ]

        # Driver Events (from PRD)
        prd_driver_events = [
            "DRIVER_STATUS_CHANGED", "DRIVER_LOCATION_UPDATED", "DRIVER_HOS_VIOLATION",
            "DRIVER_ASSIGNED", "DRIVER_BREAK_STARTED", "DRIVER_BREAK_ENDED",
            "DRIVER_LOGIN", "DRIVER_LOGOUT"
        ]

        # Route Events (from PRD)
        prd_route_events = [
            "ROUTE_OPTIMIZED", "ROUTE_DEVIATION", "ROUTE_COMPLETED", "ROUTE_UPDATED",
            "TRAFFIC_ALERT", "ROUTE_ETA_UPDATED"
        ]

        # System Events (from PRD)
        prd_system_events = [
            "SYSTEM_ALERT", "AI_PREDICTION", "INTEGRATION_ERROR"
        ]

        all_prd_events = (prd_load_events + prd_vehicle_events + prd_driver_events +
                         prd_route_events + prd_system_events)

        # Verify all PRD events exist in EventType enum
        for event_name in all_prd_events:
            assert hasattr(EventType, event_name), f"Missing event type: {event_name}"
            assert getattr(EventType, event_name) == event_name

    def test_route_optimized_event_schema(self):
        """Validate RouteOptimizedEvent matches PRD implementation"""

        event_data = {
            "source": "route-optimization-service",
            "data": {
                "route_id": str(uuid4()),
                "load_ids": [str(uuid4()), str(uuid4())],
                "optimization_score": 0.85,
                "traffic_considered": True,
                "fuel_estimate": 45.50,
                "estimated_duration": 480,
                "distance_miles": 350.2
            }
        }

        event = RouteOptimizedEvent(**event_data)

        # Verify event structure matches PRD schema
        assert event.event_type == EventType.ROUTE_OPTIMIZED
        assert "route_id" in event.data
        assert "load_ids" in event.data
        assert "optimization_score" in event.data
        assert "traffic_considered" in event.data

        # Verify data types
        assert isinstance(event.data["optimization_score"], (int, float))
        assert isinstance(event.data["traffic_considered"], bool)
        assert isinstance(event.data["load_ids"], list)


class TestAPIRequestResponseAlignment:
    """Test API request/response models align with PRD specifications"""

    def test_create_load_request_validation(self):
        """Validate CreateLoadRequest matches API contract"""

        valid_request = {
            "load_number": "LOAD-2025-001",
            "pickup_address": "123 Main St, New York, NY",
            "delivery_address": "456 Oak Ave, Los Angeles, CA",
            "pickup_datetime": datetime.now(timezone.utc),
            "delivery_datetime": datetime.now(timezone.utc),
            "weight": 25000.0,
            "volume": 1500.0,
            "rate": 2500.00
        }

        request = CreateLoadRequest(**valid_request)

        # Verify required fields
        assert request.load_number
        assert request.pickup_address
        assert request.delivery_address
        assert request.pickup_datetime
        assert request.delivery_datetime

        # Test validation fails for invalid data
        with pytest.raises(ValidationError):
            CreateLoadRequest(
                load_number="",  # Empty string should fail
                pickup_address="Valid address",
                delivery_address="Valid address",
                pickup_datetime=datetime.now(),
                delivery_datetime=datetime.now()
            )

    def test_assign_load_request_validation(self):
        """Validate AssignLoadRequest for proper UUID validation"""

        valid_request = {
            "load_id": str(uuid4()),
            "carrier_id": str(uuid4()),
            "vehicle_id": str(uuid4()),
            "driver_id": str(uuid4())
        }

        request = AssignLoadRequest(**valid_request)

        # Verify all IDs are present
        assert request.load_id
        assert request.carrier_id
        assert request.vehicle_id
        assert request.driver_id


class TestCrossSystemCompatibility:
    """Test data compatibility across API, Database, and Event systems"""

    def test_load_data_roundtrip_compatibility(self):
        """Test Load data can roundtrip between API, Domain, and Event models"""

        # Start with API request
        api_request = CreateLoadRequest(
            load_number="LOAD-2025-001",
            pickup_address="123 Main St, New York, NY",
            delivery_address="456 Oak Ave, Los Angeles, CA",
            pickup_datetime=datetime.now(timezone.utc),
            delivery_datetime=datetime.now(timezone.utc),
            weight=25000.0,
            rate=2500.00
        )

        # Convert to domain model
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

        # Convert to event
        event_data = {
            "source": "tms-api",
            "data": {
                "load_id": domain_load.id,
                "load_number": domain_load.load_number,
                "pickup_address": domain_load.pickup_address,
                "delivery_address": domain_load.delivery_address,
                "weight": domain_load.weight,
                "rate": domain_load.rate,
                "status": domain_load.status.value
            }
        }

        event = LoadCreatedEvent(**event_data)

        # Verify data consistency across models
        assert event.data["load_number"] == api_request.load_number
        assert event.data["pickup_address"] == api_request.pickup_address
        assert event.data["weight"] == api_request.weight
        assert event.data["rate"] == api_request.rate

    def test_vehicle_tracking_data_compatibility(self):
        """Test VehicleTrackingData aligns with TimescaleDB schema"""

        tracking_data = VehicleTrackingData(
            vehicle_id=str(uuid4()),
            driver_id=str(uuid4()),
            latitude=40.7128,
            longitude=-74.0060,
            speed=65.5,
            heading=180.0,
            fuel_level=75.5,
            is_moving=True
        )

        # Verify spatial data compatibility
        assert -90 <= tracking_data.latitude <= 90
        assert -180 <= tracking_data.longitude <= 180

        # Verify data types match TimescaleDB expectations
        assert isinstance(tracking_data.speed, (int, float, type(None)))
        assert isinstance(tracking_data.heading, (int, float, type(None)))
        assert isinstance(tracking_data.fuel_level, (int, float, type(None)))
        assert isinstance(tracking_data.is_moving, bool)
        assert isinstance(tracking_data.timestamp, datetime)


class TestDataValidationRules:
    """Test business logic validation rules"""

    def test_load_datetime_validation(self):
        """Validate pickup datetime is before delivery datetime"""

        pickup_time = datetime.now(timezone.utc)
        delivery_time = pickup_time.replace(hour=pickup_time.hour + 2)

        # Valid case
        valid_load = Load(
            load_number="LOAD-001",
            pickup_location=Location(latitude=40.7128, longitude=-74.0060),
            delivery_location=Location(latitude=34.0522, longitude=-118.2437),
            pickup_address="New York",
            delivery_address="Los Angeles",
            pickup_datetime=pickup_time,
            delivery_datetime=delivery_time,
            status=LoadStatus.PENDING
        )

        assert valid_load.pickup_datetime < valid_load.delivery_datetime

    def test_vehicle_capacity_validation(self):
        """Validate vehicle capacity constraints"""

        vehicle = Vehicle(
            carrier_id=str(uuid4()),
            vehicle_number="TRUCK-001",
            vehicle_type="DRY_VAN",
            capacity_weight=40000.0,
            capacity_volume=2500.0,
            status=VehicleStatus.AVAILABLE
        )

        # Verify capacity values are positive
        assert vehicle.capacity_weight > 0
        assert vehicle.capacity_volume > 0

    def test_driver_hours_of_service_validation(self):
        """Validate driver hours of service constraints"""

        driver = Driver(
            carrier_id=str(uuid4()),
            license_number="DL123456789",
            name="John Driver",
            status=DriverStatus.AVAILABLE,
            hours_remaining=8.5
        )

        # HOS should be between 0 and 11 hours (DOT regulation)
        if driver.hours_remaining is not None:
            assert 0 <= driver.hours_remaining <= 11


class TestSchemaEvolution:
    """Test schema evolution and backward compatibility"""

    def test_event_versioning(self):
        """Test event versioning supports schema evolution"""

        # Test v1.0 event
        v1_event = BaseEvent(
            event_type=EventType.LOAD_CREATED,
            source="tms-api",
            version="1.0",
            data={"load_id": str(uuid4())}
        )

        assert v1_event.version == "1.0"

        # Future version should be backward compatible
        v2_event = BaseEvent(
            event_type=EventType.LOAD_CREATED,
            source="tms-api",
            version="2.0",
            data={"load_id": str(uuid4()), "new_field": "value"}
        )

        assert v2_event.version == "2.0"
        assert "load_id" in v2_event.data  # Backward compatibility

    def test_optional_field_compatibility(self):
        """Test optional fields maintain compatibility"""

        # Minimal valid load
        minimal_load = Load(
            load_number="LOAD-001",
            pickup_location=Location(latitude=40.7128, longitude=-74.0060),
            delivery_location=Location(latitude=34.0522, longitude=-118.2437),
            pickup_address="New York",
            delivery_address="Los Angeles",
            pickup_datetime=datetime.now(timezone.utc),
            delivery_datetime=datetime.now(timezone.utc),
            status=LoadStatus.PENDING
        )

        # Should work without optional fields
        assert minimal_load.weight is None
        assert minimal_load.volume is None
        assert minimal_load.rate is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
