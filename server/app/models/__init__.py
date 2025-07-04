# TMS Domain Models

from .domain import (
    # Enums
    EntityStatus, LoadStatus, VehicleStatus, DriverStatus,
    
    # Base Models
    BaseEntity, Location,
    
    # Domain Entities
    Carrier, Vehicle, Driver, Load, Shipment, Route,
    
    # Request Models
    CreateLoadRequest, AssignLoadRequest, UpdateLocationRequest,
    LoadSearchRequest, VehicleTrackingData, PerformanceMetric,
    
    # Response Models
    LoadResponse, VehicleResponse, DriverResponse,
    
    # AI/ML Models
    RoutePrediction, LoadMatchingRequest, OptimizationRequest
)

from .events import (
    # Event Types
    EventType,
    
    # Base Event
    BaseEvent,
    
    # Specific Events
    LoadCreatedEvent, LoadAssignedEvent, LoadStatusEvent,
    VehicleLocationEvent, VehicleStatusEvent,
    DriverStatusEvent, RouteOptimizedEvent, RouteDeviationEvent,
    AIPredictionEvent, SystemAlertEvent,
    
    # Event Factory
    create_event
)

__all__ = [
    # Enums
    'EntityStatus', 'LoadStatus', 'VehicleStatus', 'DriverStatus',
    
    # Base Models
    'BaseEntity', 'Location',
    
    # Domain Entities
    'Carrier', 'Vehicle', 'Driver', 'Load', 'Shipment', 'Route',
    
    # Request Models
    'CreateLoadRequest', 'AssignLoadRequest', 'UpdateLocationRequest',
    'LoadSearchRequest', 'VehicleTrackingData', 'PerformanceMetric',
    
    # Response Models
    'LoadResponse', 'VehicleResponse', 'DriverResponse',
    
    # AI/ML Models
    'RoutePrediction', 'LoadMatchingRequest', 'OptimizationRequest',
    
    # Event Types
    'EventType',
    
    # Base Event
    'BaseEvent',
    
    # Specific Events
    'LoadCreatedEvent', 'LoadAssignedEvent', 'LoadStatusEvent',
    'VehicleLocationEvent', 'VehicleStatusEvent',
    'DriverStatusEvent', 'RouteOptimizedEvent', 'RouteDeviationEvent',
    'AIPredictionEvent', 'SystemAlertEvent',
    
    # Event Factory
    'create_event'
]
