"""TMS Event Schemas for Kafka messaging"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum
import uuid


class EventType(str, Enum):
    # Load Events
    LOAD_CREATED = "LOAD_CREATED"
    LOAD_ASSIGNED = "LOAD_ASSIGNED"
    LOAD_PICKED_UP = "LOAD_PICKED_UP"
    LOAD_IN_TRANSIT = "LOAD_IN_TRANSIT"
    LOAD_DELIVERED = "LOAD_DELIVERED"
    LOAD_CANCELLED = "LOAD_CANCELLED"
    LOAD_DELAYED = "LOAD_DELAYED"
    LOAD_UPDATED = "LOAD_UPDATED"
    
    # Vehicle Events
    VEHICLE_LOCATION_UPDATED = "VEHICLE_LOCATION_UPDATED"
    VEHICLE_STATUS_CHANGED = "VEHICLE_STATUS_CHANGED"
    VEHICLE_MAINTENANCE_DUE = "VEHICLE_MAINTENANCE_DUE"
    VEHICLE_BREAKDOWN = "VEHICLE_BREAKDOWN"
    VEHICLE_FUEL_LOW = "VEHICLE_FUEL_LOW"
    VEHICLE_ASSIGNED = "VEHICLE_ASSIGNED"
    VEHICLE_INSPECTION_DUE = "VEHICLE_INSPECTION_DUE"
    
    # Driver Events
    DRIVER_STATUS_CHANGED = "DRIVER_STATUS_CHANGED"
    DRIVER_LOCATION_UPDATED = "DRIVER_LOCATION_UPDATED"
    DRIVER_HOS_VIOLATION = "DRIVER_HOS_VIOLATION"
    DRIVER_ASSIGNED = "DRIVER_ASSIGNED"
    DRIVER_BREAK_STARTED = "DRIVER_BREAK_STARTED"
    DRIVER_BREAK_ENDED = "DRIVER_BREAK_ENDED"
    DRIVER_LOGIN = "DRIVER_LOGIN"
    DRIVER_LOGOUT = "DRIVER_LOGOUT"
    
    # Route Events
    ROUTE_OPTIMIZED = "ROUTE_OPTIMIZED"
    ROUTE_DEVIATION = "ROUTE_DEVIATION"
    ROUTE_COMPLETED = "ROUTE_COMPLETED"
    ROUTE_UPDATED = "ROUTE_UPDATED"
    TRAFFIC_ALERT = "TRAFFIC_ALERT"
    ROUTE_ETA_UPDATED = "ROUTE_ETA_UPDATED"
    
    # System Events
    SYSTEM_ALERT = "SYSTEM_ALERT"
    AI_PREDICTION = "AI_PREDICTION"
    INTEGRATION_ERROR = "INTEGRATION_ERROR"
    DATA_QUALITY_ISSUE = "DATA_QUALITY_ISSUE"
    PERFORMANCE_DEGRADATION = "PERFORMANCE_DEGRADATION"


class BaseEvent(BaseModel):
    """Base event structure for all TMS events"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str
    correlation_id: Optional[str] = None
    version: str = "1.0"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    data: Dict[str, Any] = Field(default_factory=dict)


class Location(BaseModel):
    """Geographic location"""
    latitude: float
    longitude: float
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zipcode: Optional[str] = None


# Load Events
class LoadCreatedEvent(BaseEvent):
    event_type: EventType = EventType.LOAD_CREATED
    data: Dict[str, Any] = Field(..., description="Load creation data")
    
    class LoadData(BaseModel):
        load_id: str
        load_number: str
        shipper_id: Optional[str]
        consignee_id: Optional[str]
        pickup_location: Location
        delivery_location: Location
        pickup_date: datetime
        delivery_date: datetime
        weight: float
        rate: float


class LoadAssignedEvent(BaseEvent):
    event_type: EventType = EventType.LOAD_ASSIGNED
    data: Dict[str, Any] = Field(..., description="Load assignment data")
    
    class AssignmentData(BaseModel):
        load_id: str
        carrier_id: str
        vehicle_id: str
        driver_id: str
        assigned_at: datetime


class LoadStatusEvent(BaseEvent):
    """Generic load status change event"""
    data: Dict[str, Any] = Field(..., description="Load status data")
    
    class StatusData(BaseModel):
        load_id: str
        old_status: str
        new_status: str
        location: Optional[Location]
        notes: Optional[str]


# Vehicle Events
class VehicleLocationEvent(BaseEvent):
    event_type: EventType = EventType.VEHICLE_LOCATION_UPDATED
    data: Dict[str, Any] = Field(..., description="Vehicle location data")
    
    class LocationData(BaseModel):
        vehicle_id: str
        driver_id: Optional[str]
        location: Location
        speed: Optional[float]
        heading: Optional[float]
        fuel_level: Optional[float]
        is_moving: bool = False


class VehicleStatusEvent(BaseEvent):
    event_type: EventType = EventType.VEHICLE_STATUS_CHANGED
    data: Dict[str, Any] = Field(..., description="Vehicle status data")
    
    class StatusData(BaseModel):
        vehicle_id: str
        old_status: str
        new_status: str
        reason: Optional[str]


# Driver Events
class DriverStatusEvent(BaseEvent):
    event_type: EventType = EventType.DRIVER_STATUS_CHANGED
    data: Dict[str, Any] = Field(..., description="Driver status data")
    
    class StatusData(BaseModel):
        driver_id: str
        old_status: str
        new_status: str
        location: Optional[Location]
        hours_remaining: Optional[float]


# Route Events
class RouteOptimizedEvent(BaseEvent):
    event_type: EventType = EventType.ROUTE_OPTIMIZED
    data: Dict[str, Any] = Field(..., description="Route optimization data")
    
    class OptimizationData(BaseModel):
        route_id: str
        load_ids: List[str]
        original_distance: float
        optimized_distance: float
        time_saved: float
        fuel_saved: float
        algorithm_used: str


class RouteDeviationEvent(BaseEvent):
    event_type: EventType = EventType.ROUTE_DEVIATION
    data: Dict[str, Any] = Field(..., description="Route deviation data")
    
    class DeviationData(BaseModel):
        vehicle_id: str
        driver_id: str
        route_id: str
        current_location: Location
        deviation_distance: float
        estimated_delay: float
        reason: Optional[str]


# AI/ML Events
class AIPredictionEvent(BaseEvent):
    event_type: EventType = EventType.AI_PREDICTION
    data: Dict[str, Any] = Field(..., description="AI prediction data")
    
    class PredictionData(BaseModel):
        ml_model_name: str
        prediction_type: str
        entity_id: str
        entity_type: str
        prediction: Dict[str, Any]
        confidence: float
        features_used: List[str]


# System Events
class SystemAlertEvent(BaseEvent):
    event_type: EventType = EventType.SYSTEM_ALERT
    data: Dict[str, Any] = Field(..., description="System alert data")
    
    class AlertData(BaseModel):
        alert_id: str
        severity: str  # critical, warning, info
        component: str
        message: str
        affected_entities: List[str]
        actions_required: List[str]


# Event factory for creating events from dictionaries
EVENT_TYPE_MAPPING = {
    EventType.LOAD_CREATED: LoadCreatedEvent,
    EventType.LOAD_ASSIGNED: LoadAssignedEvent,
    EventType.LOAD_PICKED_UP: LoadStatusEvent,
    EventType.LOAD_IN_TRANSIT: LoadStatusEvent,
    EventType.LOAD_DELIVERED: LoadStatusEvent,
    EventType.LOAD_CANCELLED: LoadStatusEvent,
    EventType.VEHICLE_LOCATION_UPDATED: VehicleLocationEvent,
    EventType.VEHICLE_STATUS_CHANGED: VehicleStatusEvent,
    EventType.DRIVER_STATUS_CHANGED: DriverStatusEvent,
    EventType.ROUTE_OPTIMIZED: RouteOptimizedEvent,
    EventType.ROUTE_DEVIATION: RouteDeviationEvent,
    EventType.AI_PREDICTION: AIPredictionEvent,
    EventType.SYSTEM_ALERT: SystemAlertEvent,
}


def create_event(event_type: EventType, data: Dict[str, Any], **kwargs) -> BaseEvent:
    """Factory function to create events"""
    event_class = EVENT_TYPE_MAPPING.get(event_type, BaseEvent)
    return event_class(
        event_type=event_type,
        data=data,
        **kwargs
    )
