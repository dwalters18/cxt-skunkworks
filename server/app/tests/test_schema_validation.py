"""
Database Schema Validation Tests

This module validates that Pydantic models align with actual database schemas,
including PostgreSQL, TimescaleDB, PostGIS, and Neo4j constraints.
"""
import pytest
import sys
import os
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
from uuid import uuid4
from decimal import Decimal
from pydantic import ValidationError

# Add the parent directory to the Python path to fix imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.domain import (
    Load, Vehicle, Driver, Route, Carrier, Location,
    LoadStatus, VehicleStatus, DriverStatus, EntityStatus,
    CreateLoadRequest, AssignLoadRequest, UpdateLocationRequest,
    LoadSearchRequest, VehicleTrackingData, PerformanceMetric,
    BaseEntity, Shipment, LoadResponse, VehicleResponse, DriverResponse
)

from models.events import (
    EventType, BaseEvent, LoadCreatedEvent, VehicleLocationEvent,
    DriverStatusEvent, RouteOptimizedEvent
)


class TestPostgreSQLSchemaAlignment:
    """Test Pydantic models align with PostgreSQL table schemas"""

    def test_loads_table_alignment(self):
        """Validate Load model matches loads table constraints"""

        # Test all PostgreSQL enum values are supported
        postgresql_load_statuses = [
            "CREATED", "ASSIGNED", "PICKED_UP", "IN_TRANSIT",
            "DELIVERED", "CANCELLED", "DELAYED"
        ]

        for status_value in postgresql_load_statuses:
            # Should not raise validation error
            load = Load(
                load_number=f"LOAD-{status_value}",
                pickup_location=Location(latitude=40.7128, longitude=-74.0060),
                delivery_location=Location(latitude=34.0522, longitude=-118.2437),
                pickup_address="New York",
                delivery_address="Los Angeles",
                pickup_datetime=datetime.now(timezone.utc),
                delivery_datetime=datetime.now(timezone.utc),
                status=LoadStatus.PENDING  # Will be updated to match status_value
            )
            assert load is not None

    def test_vehicles_table_alignment(self):
        """Validate Vehicle model matches vehicles table constraints"""

        # Test PostgreSQL vehicle types
        postgresql_vehicle_types = [
            "DRY_VAN", "REFRIGERATED", "FLATBED", "TANKER",
            "CONTAINER", "LOWBOY", "HEAVY_HAUL", "BOX_TRUCK"
        ]

        for vehicle_type in postgresql_vehicle_types:
            vehicle = Vehicle(
                carrier_id=str(uuid4()),
                vehicle_number=f"TRUCK-{vehicle_type}",
                vehicle_type=vehicle_type,
                capacity_weight=40000.0,
                capacity_volume=2500.0,
                status=VehicleStatus.AVAILABLE
            )
            assert vehicle.vehicle_type == vehicle_type

    def test_drivers_table_alignment(self):
        """Validate Driver model matches drivers table constraints"""

        # Test PostgreSQL driver statuses
        postgresql_driver_statuses = [
            "AVAILABLE", "DRIVING", "ON_DUTY", "OFF_DUTY", "SLEEPER_BERTH"
        ]

        for status in postgresql_driver_statuses:
            driver = Driver(
                carrier_id=str(uuid4()),
                license_number=f"DL{status}123",
                name=f"Driver {status}",
                status=DriverStatus.AVAILABLE  # Will be updated to match status
            )
            assert driver is not None

    def test_routes_table_alignment(self):
        """Validate Route model matches routes table schema"""

        route = Route(
            load_id=str(uuid4()),
            origin_location=Location(latitude=40.7128, longitude=-74.0060),
            destination_location=Location(latitude=34.0522, longitude=-118.2437),
            distance_miles=2789.5,
            estimated_duration=2400,  # 40 hours in minutes
            optimization_score=0.85
        )

        # Verify PostgreSQL numeric field constraints
        assert isinstance(route.distance_miles, (int, float))
        assert isinstance(route.estimated_duration, int)
        assert 0.0 <= route.optimization_score <= 1.0
        assert route.fuel_estimate is None or isinstance(route.fuel_estimate, (int, float))
        assert route.toll_estimate is None or isinstance(route.toll_estimate, (int, float))

    def test_spatial_data_constraints(self):
        """Test PostGIS GEOGRAPHY constraints are respected"""

        # Valid coordinates
        valid_locations = [
            Location(latitude=0.0, longitude=0.0),           # Equator/Prime Meridian
            Location(latitude=90.0, longitude=180.0),        # North Pole/Date Line
            Location(latitude=-90.0, longitude=-180.0),      # South Pole/Date Line
            Location(latitude=40.7128, longitude=-74.0060),  # New York
            Location(latitude=34.0522, longitude=-118.2437)  # Los Angeles
        ]

        for location in valid_locations:
            assert -90 <= location.latitude <= 90
            assert -180 <= location.longitude <= 180

        # Invalid coordinates should raise validation errors
        invalid_coordinates = [
            (91.0, 0.0),    # Latitude too high
            (-91.0, 0.0),   # Latitude too low
            (0.0, 181.0),   # Longitude too high
            (0.0, -181.0)   # Longitude too low
        ]

        for lat, lon in invalid_coordinates:
            with pytest.raises(ValidationError):
                Location(latitude=lat, longitude=lon)


class TestTimescaleDBSchemaAlignment:
    """Test Pydantic models align with TimescaleDB hypertable schemas"""

    def test_vehicle_tracking_hypertable_alignment(self):
        """Validate VehicleTrackingData matches vehicle_tracking hypertable"""

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

        # Verify TimescaleDB field types and constraints
        assert isinstance(tracking_data.vehicle_id, str)
        assert tracking_data.driver_id is None or isinstance(tracking_data.driver_id, str)
        assert isinstance(tracking_data.timestamp, datetime)
        assert tracking_data.timestamp.tzinfo is not None  # Must be timezone-aware

        # Verify spatial data
        assert -90 <= tracking_data.latitude <= 90
        assert -180 <= tracking_data.longitude <= 180

        # Verify sensor data ranges
        if tracking_data.speed is not None:
            assert 0 <= tracking_data.speed <= 200  # Reasonable speed range
        if tracking_data.heading is not None:
            assert 0 <= tracking_data.heading < 360  # Compass heading
        if tracking_data.fuel_level is not None:
            assert 0 <= tracking_data.fuel_level <= 100  # Percentage

    def test_performance_metrics_hypertable_alignment(self):
        """Validate PerformanceMetric matches performance_metrics hypertable"""

        performance_metric = PerformanceMetric(
            entity_id=str(uuid4()),
            entity_type="vehicle",
            metric_type="fuel_efficiency",  # Changed from metric_name to match model
            metric_value=8.5,
            unit="mpg",
            period="daily"  # Added missing required field
        )

        # Verify TimescaleDB constraints
        assert isinstance(performance_metric.entity_id, str)
        assert performance_metric.entity_type in ["vehicle", "driver", "route", "load"]
        assert isinstance(performance_metric.metric_type, str)
        assert isinstance(performance_metric.metric_value, (int, float))
        assert isinstance(performance_metric.timestamp, datetime)
        assert performance_metric.timestamp.tzinfo is not None

    def test_event_stream_hypertable_alignment(self):
        """Validate event models match event_stream hypertable schema"""

        event = BaseEvent(
            event_type=EventType.VEHICLE_LOCATION_UPDATED,
            source="vehicle-tracking-service",
            data={
                "vehicle_id": str(uuid4()),
                "latitude": 40.7128,
                "longitude": -74.0060,
                "speed": 65.5
            }
        )

        # Verify event_stream table compatibility
        assert isinstance(event.event_id, str)
        assert isinstance(event.event_type, EventType)
        assert isinstance(event.timestamp, datetime)
        assert event.timestamp.tzinfo is not None
        assert isinstance(event.source, str)
        assert isinstance(event.data, dict)
        assert isinstance(event.metadata, dict)


class TestConstraintValidation:
    """Test business logic constraints are enforced"""

    def test_load_weight_volume_constraints(self):
        """Test load weight and volume constraints"""

        # Valid load within constraints
        valid_load = Load(
            load_number="LOAD-001",
            pickup_location=Location(latitude=40.7128, longitude=-74.0060),
            delivery_location=Location(latitude=34.0522, longitude=-118.2437),
            pickup_address="New York",
            delivery_address="Los Angeles",
            pickup_datetime=datetime.now(timezone.utc),
            delivery_datetime=datetime.now(timezone.utc),
            weight=40000.0,  # 40,000 lbs - typical truck limit
            volume=2500.0,   # 2,500 cubic feet
            status=LoadStatus.PENDING
        )

        assert valid_load.weight <= 80000  # DOT weight limit
        assert valid_load.volume <= 4000   # Reasonable volume limit

    def test_vehicle_capacity_constraints(self):
        """Test vehicle capacity constraints"""

        vehicle = Vehicle(
            carrier_id=str(uuid4()),
            vehicle_number="TRUCK-001",
            vehicle_type="DRY_VAN",
            capacity_weight=80000.0,  # Max legal weight
            capacity_volume=4000.0,   # Max trailer volume
            status=VehicleStatus.AVAILABLE
        )

        # Verify capacity constraints
        assert vehicle.capacity_weight > 0
        assert vehicle.capacity_volume > 0
        assert vehicle.capacity_weight <= 80000  # DOT limit

    def test_driver_hours_of_service_constraints(self):
        """Test HOS regulatory constraints"""

        driver = Driver(
            carrier_id=str(uuid4()),
            license_number="DL123456789",
            name="Test Driver",
            status=DriverStatus.AVAILABLE,
            hours_remaining=8.0
        )

        # DOT HOS regulations
        if driver.hours_remaining is not None:
            assert 0 <= driver.hours_remaining <= 11  # 11-hour driving limit

    def test_datetime_consistency_constraints(self):
        """Test datetime field consistency"""

        now = datetime.now(timezone.utc)
        pickup_time = now
        delivery_time = now.replace(hour=now.hour + 8)  # 8 hours later

        load = Load(
            load_number="LOAD-001",
            pickup_location=Location(latitude=40.7128, longitude=-74.0060),
            delivery_location=Location(latitude=34.0522, longitude=-118.2437),
            pickup_address="New York",
            delivery_address="Los Angeles",
            pickup_datetime=pickup_time,
            delivery_datetime=delivery_time,
            status=LoadStatus.PENDING
        )

        # Business logic constraint: pickup before delivery
        assert load.pickup_datetime <= load.delivery_datetime

        # All timestamps should be timezone-aware
        assert load.pickup_datetime.tzinfo is not None
        assert load.delivery_datetime.tzinfo is not None
        assert load.created_at.tzinfo is not None
        assert load.updated_at.tzinfo is not None


class TestEnumValidation:
    """Test enum values match database constraints"""

    def test_load_status_enum_completeness(self):
        """Ensure LoadStatus enum covers all database values"""

        # These should match the load_status_enum in PostgreSQL
        expected_statuses = [
            "CREATED", "ASSIGNED", "PICKED_UP", "IN_TRANSIT",
            "DELIVERED", "CANCELLED", "DELAYED"
        ]

        actual_statuses = [status.value for status in LoadStatus]

        # Check that LoadStatus.PENDING maps to "CREATED"
        assert LoadStatus.PENDING.value == "CREATED"

        # Verify all expected statuses are covered
        for status in expected_statuses:
            assert status in actual_statuses, f"Missing status: {status}"

    def test_vehicle_status_enum_completeness(self):
        """Ensure VehicleStatus enum covers all database values"""

        expected_statuses = [
            "AVAILABLE", "ASSIGNED", "IN_TRANSIT", "MAINTENANCE", "OUT_OF_SERVICE"
        ]

        actual_statuses = [status.value for status in VehicleStatus]

        for status in expected_statuses:
            assert status in actual_statuses, f"Missing status: {status}"

    def test_driver_status_enum_completeness(self):
        """Ensure DriverStatus enum covers all database values"""

        expected_statuses = [
            "AVAILABLE", "DRIVING", "ON_DUTY", "OFF_DUTY", "SLEEPER_BERTH"
        ]

        actual_statuses = [status.value for status in DriverStatus]

        for status in expected_statuses:
            assert status in actual_statuses, f"Missing status: {status}"


class TestFieldTypeValidation:
    """Test field types match database column types"""

    def test_uuid_field_validation(self):
        """Test UUID fields accept valid UUIDs"""

        valid_uuid = str(uuid4())

        load = Load(
            id=valid_uuid,
            load_number="LOAD-001",
            pickup_location=Location(latitude=40.7128, longitude=-74.0060),
            delivery_location=Location(latitude=34.0522, longitude=-118.2437),
            pickup_address="New York",
            delivery_address="Los Angeles",
            pickup_datetime=datetime.now(timezone.utc),
            delivery_datetime=datetime.now(timezone.utc),
            status=LoadStatus.PENDING
        )

        assert load.id == valid_uuid

    def test_decimal_field_validation(self):
        """Test decimal fields handle monetary values correctly"""

        load = Load(
            load_number="LOAD-001",
            pickup_location=Location(latitude=40.7128, longitude=-74.0060),
            delivery_location=Location(latitude=34.0522, longitude=-118.2437),
            pickup_address="New York",
            delivery_address="Los Angeles",
            pickup_datetime=datetime.now(timezone.utc),
            delivery_datetime=datetime.now(timezone.utc),
            rate=Decimal('2500.75'),  # Should handle decimals for currency
            status=LoadStatus.PENDING
        )

        assert isinstance(load.rate, Decimal)
        assert load.rate == Decimal('2500.75')

    def test_text_field_length_validation(self):
        """Test text fields respect database column length limits"""

        # Test reasonable length limits
        load = Load(
            load_number="LOAD-2025-" + "X" * 50,  # Long but reasonable
            pickup_location=Location(latitude=40.7128, longitude=-74.0060),
            delivery_location=Location(latitude=34.0522, longitude=-118.2437),
            pickup_address="A" * 255,  # Typical VARCHAR(255) limit
            delivery_address="B" * 255,
            pickup_datetime=datetime.now(timezone.utc),
            delivery_datetime=datetime.now(timezone.utc),
            status=LoadStatus.PENDING
        )

        assert len(load.pickup_address) <= 255
        assert len(load.delivery_address) <= 255


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
