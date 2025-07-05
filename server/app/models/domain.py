"""TMS Domain Models"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from decimal import Decimal
import uuid


class EntityStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class LoadStatus(str, Enum):
    PENDING = "CREATED"
    ASSIGNED = "ASSIGNED"
    PICKED_UP = "PICKED_UP"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    DELAYED = "DELAYED"


class VehicleStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    ASSIGNED = "ASSIGNED"
    IN_TRANSIT = "IN_TRANSIT"
    MAINTENANCE = "MAINTENANCE"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"


class DriverStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    DRIVING = "DRIVING"
    ON_DUTY = "ON_DUTY"
    OFF_DUTY = "OFF_DUTY"
    SLEEPER_BERTH = "SLEEPER_BERTH"


# Base Models
class BaseEntity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Location(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zipcode: Optional[str] = None


# Domain Entities
class Carrier(BaseEntity):
    name: str
    mc_number: Optional[str] = None
    dot_number: Optional[str] = None
    contact_info: Dict[str, Any] = Field(default_factory=dict)
    status: EntityStatus = EntityStatus.ACTIVE
    fleet_size: int = 0
    service_areas: List[str] = Field(default_factory=list)


class Vehicle(BaseEntity):
    carrier_id: str
    vehicle_number: str
    vehicle_type: str
    capacity_weight: Optional[float] = None
    capacity_volume: Optional[float] = None
    status: VehicleStatus = VehicleStatus.AVAILABLE
    current_location: Optional[Location] = None
    fuel_level: Optional[float] = None
    odometer: Optional[float] = None


class Driver(BaseEntity):
    carrier_id: str
    license_number: str
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    status: DriverStatus = DriverStatus.AVAILABLE
    current_location: Optional[Location] = None
    hours_remaining: Optional[float] = None  # HOS compliance


class Load(BaseEntity):
    load_number: str
    shipper_id: Optional[str] = None
    consignee_id: Optional[str] = None
    carrier_id: Optional[str] = None
    vehicle_id: Optional[str] = None
    driver_id: Optional[str] = None
    pickup_location: Location
    delivery_location: Location
    pickup_address: str
    delivery_address: str
    pickup_datetime: datetime
    delivery_datetime: datetime
    weight: Optional[float] = None
    volume: Optional[float] = None
    rate: Optional[Decimal] = None
    status: LoadStatus = LoadStatus.PENDING
    
    model_config = ConfigDict(
        # Preserve Decimal types instead of converting to float
        arbitrary_types_allowed=True
    )


class Shipment(BaseEntity):
    load_id: str
    shipment_number: str
    description: Optional[str] = None
    weight: Optional[float] = None
    dimensions: Dict[str, float] = Field(default_factory=dict)
    value: Optional[float] = None
    status: str = "pending"


class Route(BaseEntity):
    load_id: str
    route_data: Dict[str, Any] = Field(default_factory=dict)
    estimated_distance: Optional[float] = None
    estimated_duration: Optional[int] = None  # minutes
    actual_distance: Optional[float] = None
    actual_duration: Optional[int] = None
    distance_miles: Optional[float] = None
    optimization_score: Optional[float] = None
    fuel_estimate: Optional[float] = None
    toll_estimate: Optional[float] = None
    status: str = "planned"


# Request/Response Models
class CreateLoadRequest(BaseModel):
    load_number: str = Field(..., min_length=1)
    pickup_address: str = Field(..., min_length=1)
    delivery_address: str = Field(..., min_length=1)
    pickup_datetime: datetime
    delivery_datetime: datetime
    weight: Optional[float] = None
    volume: Optional[float] = None
    rate: Optional[Decimal] = None
    shipper_id: Optional[str] = None
    consignee_id: Optional[str] = None
    notes: Optional[str] = None


class AssignLoadRequest(BaseModel):
    load_id: str = Field(..., pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
    carrier_id: str = Field(..., pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
    vehicle_id: str = Field(..., pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
    driver_id: str = Field(..., pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
    estimated_pickup_time: Optional[datetime] = None
    estimated_delivery_time: Optional[datetime] = None


class UpdateLocationRequest(BaseModel):
    entity_id: str
    entity_type: str  # vehicle, driver
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    timestamp: Optional[datetime] = None
    speed: Optional[float] = Field(None, ge=0.0)  # Speed cannot be negative
    heading: Optional[float] = Field(None, ge=0.0, lt=360.0)  # Heading 0-359 degrees


class LoadSearchRequest(BaseModel):
    status: Optional[LoadStatus] = None
    carrier_id: Optional[str] = None
    pickup_state: Optional[str] = None
    delivery_state: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = 50
    offset: int = 0


class VehicleTrackingData(BaseModel):
    vehicle_id: str
    driver_id: Optional[str] = None
    latitude: float
    longitude: float
    speed: Optional[float] = None
    heading: Optional[float] = None
    fuel_level: Optional[float] = None
    is_moving: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PerformanceMetric(BaseModel):
    metric_type: str
    entity_type: str
    entity_id: str
    metric_value: float
    unit: str
    period: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# AI/ML Models
class RoutePrediction(BaseModel):
    route_id: str
    predicted_duration: float
    predicted_fuel_consumption: float
    confidence: float
    factors: List[str]


class LoadMatchingRequest(BaseModel):
    load_id: str
    max_distance: float = 100.0  # miles
    carrier_preferences: List[str] = Field(default_factory=list)


class OptimizationRequest(BaseModel):
    vehicle_ids: List[str]
    load_ids: List[str]
    optimization_type: str = "distance"  # distance, time, cost
    constraints: Dict[str, Any] = Field(default_factory=dict)


# Response Models (needed by tests)
class LoadResponse(BaseModel):
    """Response model for Load API endpoints"""
    id: str
    load_number: str
    shipper_id: Optional[str] = None
    consignee_id: Optional[str] = None
    carrier_id: Optional[str] = None
    vehicle_id: Optional[str] = None
    driver_id: Optional[str] = None
    pickup_location: Location
    delivery_location: Location
    pickup_address: str
    delivery_address: str
    pickup_datetime: datetime
    delivery_datetime: datetime
    weight: Optional[float] = None
    volume: Optional[float] = None
    rate: Optional[Decimal] = None
    status: LoadStatus
    created_at: datetime
    updated_at: datetime


class VehicleResponse(BaseModel):
    """Response model for Vehicle API endpoints"""
    id: str
    carrier_id: str
    vehicle_number: str
    vehicle_type: str
    capacity_weight: Optional[float] = None
    capacity_volume: Optional[float] = None
    status: VehicleStatus
    current_location: Optional[Location] = None
    fuel_level: Optional[float] = None
    odometer: Optional[float] = None
    created_at: datetime
    updated_at: datetime


class DriverResponse(BaseModel):
    """Response model for Driver API endpoints"""
    id: str
    carrier_id: str
    license_number: str
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    status: DriverStatus
    current_location: Optional[Location] = None
    hours_remaining: Optional[float] = None
    created_at: datetime
    updated_at: datetime


# Driver Request Models
class CreateDriverRequest(BaseModel):
    """Request model for creating a new driver as per SPEC."""
    driver_number: str = Field(..., min_length=1, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=1, max_length=20)
    email: str = Field(..., min_length=1, max_length=255)
    license_number: str = Field(..., min_length=1, max_length=50, description="CDL number as per SPEC")
    license_class: str = Field(..., min_length=1, max_length=10)
    license_expiry: datetime = Field(..., description="CDL expiry date as per SPEC")
    date_of_birth: datetime
    hire_date: datetime
    carrier_id: Optional[str] = None
    current_location: Location = Field(..., description="Current location with latitude/longitude")
    current_address: Optional[str] = None
    status: DriverStatus = DriverStatus.AVAILABLE
