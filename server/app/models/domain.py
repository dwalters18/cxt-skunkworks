"""TMS Domain Models"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Location(BaseModel):
    latitude: float
    longitude: float
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
    rate: Optional[float] = None
    status: LoadStatus = LoadStatus.PENDING


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
    status: str = "planned"


# Request/Response Models
class CreateLoadRequest(BaseModel):
    load_number: str
    pickup_address: str
    delivery_address: str
    pickup_datetime: datetime
    delivery_datetime: datetime
    weight: Optional[float] = None
    volume: Optional[float] = None
    rate: Optional[float] = None
    shipper_id: Optional[str] = None
    consignee_id: Optional[str] = None


class AssignLoadRequest(BaseModel):
    load_id: str
    carrier_id: str
    vehicle_id: str
    driver_id: str


class UpdateLocationRequest(BaseModel):
    entity_id: str
    entity_type: str  # vehicle, driver
    latitude: float
    longitude: float
    timestamp: Optional[datetime] = None
    speed: Optional[float] = None
    heading: Optional[float] = None


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
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PerformanceMetric(BaseModel):
    metric_type: str
    entity_type: str
    entity_id: str
    metric_value: float
    unit: str
    period: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


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
