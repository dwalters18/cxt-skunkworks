"""
Pytest Configuration and Fixtures for PRD Alignment Tests

This module provides shared fixtures and configuration for all TMS validation tests.
"""
import pytest
import sys
import os
from datetime import datetime, timezone
from typing import Dict, List, Any
from uuid import uuid4
import json

# Add the parent directory to the Python path to fix imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.domain import (
    Load, Vehicle, Driver, Route, Carrier, Location,
    LoadStatus, VehicleStatus, DriverStatus,
    CreateLoadRequest, AssignLoadRequest
)
from models.events import (
    EventType, BaseEvent, LoadCreatedEvent, VehicleLocationEvent
)


# Test Configuration
pytest_plugins = []


@pytest.fixture
def sample_location():
    """Provide a sample Location for testing"""
    return Location(latitude=40.7128, longitude=-74.0060)


@pytest.fixture
def sample_carrier():
    """Provide a sample Carrier for testing"""
    return Carrier(
        name="Test Logistics Inc",
        mc_number="MC123456",
        dot_number="DOT789012",
        phone="555-123-4567",
        email="dispatch@testlogistics.com",
        address="123 Carrier Ave, Logistics City, LC 12345"
    )


@pytest.fixture
def sample_vehicle(sample_carrier):
    """Provide a sample Vehicle for testing"""
    return Vehicle(
        carrier_id=sample_carrier.id,
        vehicle_number="TRUCK-001",
        vehicle_type="DRY_VAN",
        capacity_weight=40000.0,
        capacity_volume=2500.0,
        status=VehicleStatus.AVAILABLE,
        current_location=Location(latitude=40.7128, longitude=-74.0060),
        fuel_level=75.5,
        odometer=125000
    )


@pytest.fixture
def sample_driver(sample_carrier):
    """Provide a sample Driver for testing"""
    return Driver(
        carrier_id=sample_carrier.id,
        license_number="DL123456789",
        name="John Driver",
        phone="555-987-6543",
        email="john.driver@testlogistics.com",
        status=DriverStatus.AVAILABLE,
        hours_remaining=8.5
    )


@pytest.fixture
def sample_load():
    """Provide a sample Load for testing"""
    return Load(
        load_number="LOAD-2025-001",
        pickup_location=Location(latitude=40.7128, longitude=-74.0060),
        delivery_location=Location(latitude=34.0522, longitude=-118.2437),
        pickup_address="123 Main Street, New York, NY 10001",
        delivery_address="456 Oak Avenue, Los Angeles, CA 90210",
        pickup_datetime=datetime.now(timezone.utc),
        delivery_datetime=datetime.now(timezone.utc).replace(hour=23),
        weight=25000.0,
        volume=1500.0,
        rate=2500.00,
        status=LoadStatus.PENDING,
        notes="Handle with care - fragile items"
    )


@pytest.fixture
def sample_route(sample_load):
    """Provide a sample Route for testing"""
    return Route(
        load_id=sample_load.id,
        origin_location=sample_load.pickup_location,
        destination_location=sample_load.delivery_location,
        distance_miles=2789.5,
        estimated_duration=2400,  # 40 hours in minutes
        optimization_score=0.85,
        fuel_estimate=450.75,
        toll_estimate=125.50
    )


@pytest.fixture
def sample_create_load_request():
    """Provide a sample CreateLoadRequest for API testing"""
    return CreateLoadRequest(
        load_number="LOAD-2025-001",
        pickup_address="123 Main Street, New York, NY 10001",
        delivery_address="456 Oak Avenue, Los Angeles, CA 90210",
        pickup_datetime=datetime.now(timezone.utc),
        delivery_datetime=datetime.now(timezone.utc).replace(hour=23),
        weight=25000.0,
        volume=1500.0,
        rate=2500.00,
        notes="Test load request"
    )


@pytest.fixture
def sample_assign_load_request():
    """Provide a sample AssignLoadRequest for API testing"""
    return AssignLoadRequest(
        load_id=str(uuid4()),
        carrier_id=str(uuid4()),
        vehicle_id=str(uuid4()),
        driver_id=str(uuid4()),
        estimated_pickup_time=datetime.now(timezone.utc),
        estimated_delivery_time=datetime.now(timezone.utc).replace(hour=12)
    )


@pytest.fixture
def sample_load_created_event(sample_load):
    """Provide a sample LoadCreatedEvent for event testing"""
    return LoadCreatedEvent(
        source="tms-api",
        data={
            "load_id": sample_load.id,
            "load_number": sample_load.load_number,
            "pickup_address": sample_load.pickup_address,
            "delivery_address": sample_load.delivery_address,
            "weight": sample_load.weight,
            "volume": sample_load.volume,
            "rate": sample_load.rate,
            "status": sample_load.status.value
        }
    )


@pytest.fixture
def sample_vehicle_location_event(sample_vehicle):
    """Provide a sample VehicleLocationEvent for event testing"""
    return VehicleLocationEvent(
        source="vehicle-tracking-service",
        data={
            "vehicle_id": sample_vehicle.id,
            "driver_id": str(uuid4()),
            "latitude": 40.7128,
            "longitude": -74.0060,
            "speed": 65.5,
            "heading": 180.0,
            "fuel_level": 75.5,
            "is_moving": True
        }
    )


@pytest.fixture
def prd_event_types():
    """Provide complete list of PRD event types for validation"""
    return [
        # Load Events
        "LOAD_CREATED", "LOAD_ASSIGNED", "LOAD_PICKED_UP", "LOAD_IN_TRANSIT",
        "LOAD_DELIVERED", "LOAD_CANCELLED", "LOAD_DELAYED", "LOAD_UPDATED",

        # Vehicle Events
        "VEHICLE_LOCATION_UPDATED", "VEHICLE_STATUS_CHANGED", "VEHICLE_MAINTENANCE_DUE",
        "VEHICLE_BREAKDOWN", "VEHICLE_FUEL_LOW", "VEHICLE_ASSIGNED", "VEHICLE_INSPECTION_DUE",

        # Driver Events
        "DRIVER_STATUS_CHANGED", "DRIVER_LOCATION_UPDATED", "DRIVER_HOS_VIOLATION",
        "DRIVER_ASSIGNED", "DRIVER_BREAK_STARTED", "DRIVER_BREAK_ENDED",
        "DRIVER_LOGIN", "DRIVER_LOGOUT",

        # Route Events
        "ROUTE_OPTIMIZED", "ROUTE_DEVIATION", "ROUTE_COMPLETED", "ROUTE_UPDATED",
        "TRAFFIC_ALERT", "ROUTE_ETA_UPDATED",

        # System Events
        "SYSTEM_ALERT", "AI_PREDICTION", "INTEGRATION_ERROR"
    ]


@pytest.fixture
def prd_load_statuses():
    """Provide PRD-compliant load status values"""
    return ["CREATED", "ASSIGNED", "PICKED_UP", "IN_TRANSIT", "DELIVERED", "CANCELLED", "DELAYED"]


@pytest.fixture
def prd_vehicle_types():
    """Provide PRD-compliant vehicle type values"""
    return ["DRY_VAN", "REFRIGERATED", "FLATBED", "TANKER", "CONTAINER", "LOWBOY", "HEAVY_HAUL", "BOX_TRUCK"]


@pytest.fixture
def prd_vehicle_statuses():
    """Provide PRD-compliant vehicle status values"""
    return ["AVAILABLE", "ASSIGNED", "IN_TRANSIT", "MAINTENANCE", "OUT_OF_SERVICE"]


@pytest.fixture
def prd_driver_statuses():
    """Provide PRD-compliant driver status values"""
    return ["AVAILABLE", "DRIVING", "ON_DUTY", "OFF_DUTY", "SLEEPER_BERTH"]


@pytest.fixture
def coordinate_test_cases():
    """Provide test cases for coordinate validation"""
    return {
        "valid": [
            (0.0, 0.0),           # Equator/Prime Meridian
            (90.0, 180.0),        # North Pole/Date Line
            (-90.0, -180.0),      # South Pole/Date Line
            (40.7128, -74.0060),  # New York
            (34.0522, -118.2437), # Los Angeles
            (51.5074, -0.1278),   # London
            (35.6762, 139.6503)   # Tokyo
        ],
        "invalid": [
            (91.0, 0.0),     # Latitude too high
            (-91.0, 0.0),    # Latitude too low
            (0.0, 181.0),    # Longitude too high
            (0.0, -181.0),   # Longitude too low
            (999.0, 0.0),    # Extreme latitude
            (0.0, 999.0)     # Extreme longitude
        ]
    }


@pytest.fixture
def business_constraint_test_cases():
    """Provide test cases for business logic validation"""
    return {
        "vehicle_capacity": {
            "valid": [
                {"weight": 40000.0, "volume": 2500.0},    # Standard dry van
                {"weight": 80000.0, "volume": 4000.0},    # Maximum legal
                {"weight": 26000.0, "volume": 1800.0}     # Box truck
            ],
            "invalid": [
                {"weight": 0.0, "volume": 2500.0},        # Zero weight
                {"weight": 40000.0, "volume": 0.0},       # Zero volume
                {"weight": -1000.0, "volume": 2500.0},    # Negative weight
                {"weight": 100000.0, "volume": 2500.0}    # Over DOT limit
            ]
        },
        "driver_hours": {
            "valid": [0.0, 5.5, 8.0, 11.0],              # Valid HOS remaining
            "invalid": [-1.0, 12.0, 24.0, 100.0]         # Invalid HOS
        },
        "load_weight": {
            "valid": [1000.0, 25000.0, 40000.0, 80000.0], # Valid weights
            "invalid": [0.0, -1000.0, 100000.0]          # Invalid weights
        }
    }


@pytest.fixture(scope="session")
def test_database_url():
    """Provide test database URL if available"""
    return os.getenv("TEST_DATABASE_URL", "postgresql://test:test@localhost/tms_test")


@pytest.fixture(scope="session")
def test_kafka_config():
    """Provide test Kafka configuration if available"""
    return {
        "bootstrap_servers": os.getenv("TEST_KAFKA_SERVERS", "localhost:9092"),
        "group_id": "tms-test-group",
        "auto_offset_reset": "earliest"
    }


def pytest_configure(config):
    """Configure pytest markers and options"""
    config.addinivalue_line(
        "markers", "prd_alignment: mark test as PRD alignment validation"
    )
    config.addinivalue_line(
        "markers", "database_schema: mark test as database schema validation"
    )
    config.addinivalue_line(
        "markers", "api_compatibility: mark test as API compatibility validation"
    )
    config.addinivalue_line(
        "markers", "event_validation: mark test as event schema validation"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires external services)"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file names"""
    for item in items:
        # Add markers based on test file names
        if "test_prd_alignment" in item.nodeid:
            item.add_marker(pytest.mark.prd_alignment)
        elif "test_schema_validation" in item.nodeid:
            item.add_marker(pytest.mark.database_schema)
        elif "test_api_compatibility" in item.nodeid:
            item.add_marker(pytest.mark.api_compatibility)
        elif "test_event" in item.nodeid:
            item.add_marker(pytest.mark.event_validation)


@pytest.fixture
def mock_google_maps_response():
    """Provide mock Google Maps API response for route optimization tests"""
    return {
        "routes": [{
            "legs": [{
                "distance": {"value": 4486540, "text": "2,789.5 mi"},
                "duration": {"value": 144000, "text": "40 hours 0 mins"},
                "start_location": {"lat": 40.7128, "lng": -74.0060},
                "end_location": {"lat": 34.0522, "lng": -118.2437}
            }],
            "overview_polyline": {
                "points": "encoded_polyline_string_here"
            }
        }],
        "status": "OK"
    }


@pytest.fixture
def sample_timeseries_data():
    """Provide sample time-series data for TimescaleDB testing"""
    base_time = datetime.now(timezone.utc)
    vehicle_id = str(uuid4())

    return [
        {
            "vehicle_id": vehicle_id,
            "timestamp": base_time,
            "latitude": 40.7128,
            "longitude": -74.0060,
            "speed": 0.0,
            "fuel_level": 100.0,
            "is_moving": False
        },
        {
            "vehicle_id": vehicle_id,
            "timestamp": base_time.replace(minute=base_time.minute + 15),
            "latitude": 40.7500,
            "longitude": -74.0200,
            "speed": 55.0,
            "fuel_level": 98.5,
            "is_moving": True
        },
        {
            "vehicle_id": vehicle_id,
            "timestamp": base_time.replace(minute=base_time.minute + 30),
            "latitude": 40.8000,
            "longitude": -74.1000,
            "speed": 65.0,
            "fuel_level": 97.0,
            "is_moving": True
        }
    ]
