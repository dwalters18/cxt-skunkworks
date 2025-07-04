# Product Requirements Document (PRD)
## TMS Events Schema

**Version:** 1.0  
**Date:** July 3, 2025  
**Authors:** Product Team  
**Tags:** #TMS-Events #TMS-Core #status/implemented #priority/high #real-time #streaming
**Related:** [[PRD-Overview]] | [[PRD-Backend-System]] | [[PRD-Stream-Processing]] | [[PRD-Real-time-Analytics]]
**Dependencies:** [[PRD-Database-Schema]]
**Used By:** [[PRD-Backend-System]], [[PRD-Stream-Processing]], [[PRD-Real-time-Analytics]]

---

## 1. Executive Summary

### 1.1 Overview
The TMS Events Schema defines the comprehensive event taxonomy and data structures for the Transportation Management System's event-driven architecture. This schema enables complete operational transparency, real-time system state awareness, and comprehensive audit trails across all TMS operations.

### 1.2 Scope
This document covers:
- Complete event taxonomy across all TMS domains
- Event data structures and schemas
- Event routing and topic organization
- Event versioning and evolution strategies
- Event processing patterns and workflows

### 1.3 Event-Driven Architecture Benefits
- **Complete Transparency**: Every system operation generates trackable events
- **Real-time State Management**: Immediate propagation of state changes
- **Audit and Compliance**: Immutable event history for all operations
- **Decoupled Architecture**: Services communicate through well-defined events
- **Scalable Processing**: Events can be processed independently and in parallel

---

## 2. Event Categories and Taxonomy

### 2.1 Core Event Categories

#### 2.1.1 Load Events
Events related to shipment and load lifecycle management:

| Event Type | Description | Frequency | Criticality |
|------------|-------------|-----------|-------------|
| LOAD_CREATED | New load entered into system | ~1000/day | High |
| LOAD_ASSIGNED | Load assigned to driver/vehicle | ~800/day | High |
| LOAD_PICKED_UP | Load picked up from origin | ~800/day | Critical |
| LOAD_IN_TRANSIT | Load status updated during transport | ~2000/day | High |
| LOAD_DELIVERED | Load successfully delivered | ~750/day | Critical |
| LOAD_CANCELLED | Load cancelled before completion | ~50/day | Medium |
| LOAD_DELAYED | Load delayed beyond scheduled time | ~100/day | High |
| LOAD_UPDATED | Load details modified | ~300/day | Medium |

#### 2.1.2 Vehicle Events
Events related to vehicle operations and status:

| Event Type | Description | Frequency | Criticality |
|------------|-------------|-----------|-------------|
| VEHICLE_LOCATION_UPDATED | GPS location update | ~50000/day | Medium |
| VEHICLE_STATUS_CHANGED | Vehicle operational status change | ~500/day | High |
| VEHICLE_MAINTENANCE_DUE | Maintenance reminder triggered | ~20/day | High |
| VEHICLE_BREAKDOWN | Vehicle breakdown or emergency | ~5/day | Critical |
| VEHICLE_FUEL_LOW | Low fuel alert | ~50/day | Medium |
| VEHICLE_ASSIGNED | Vehicle assigned to load/driver | ~400/day | High |
| VEHICLE_INSPECTION_DUE | DOT inspection reminder | ~10/day | High |

#### 2.1.3 Driver Events
Events related to driver management and compliance:

| Event Type | Description | Frequency | Criticality |
|------------|-------------|-----------|-------------|
| DRIVER_STATUS_CHANGED | Driver duty status change | ~2000/day | High |
| DRIVER_LOCATION_UPDATED | Driver location update | ~10000/day | Medium |
| DRIVER_HOS_VIOLATION | Hours of Service violation | ~10/day | Critical |
| DRIVER_ASSIGNED | Driver assigned to load/vehicle | ~400/day | High |
| DRIVER_BREAK_STARTED | Driver mandatory break started | ~800/day | Medium |
| DRIVER_BREAK_ENDED | Driver break completed | ~800/day | Medium |
| DRIVER_LOGIN | Driver logged into system | ~200/day | Low |
| DRIVER_LOGOUT | Driver logged out of system | ~200/day | Low |

#### 2.1.4 Route Events
Events related to routing and optimization:

| Event Type | Description | Frequency | Criticality |
|------------|-------------|-----------|-------------|
| ROUTE_OPTIMIZED | New optimal route calculated | ~400/day | High |
| ROUTE_DEVIATION | Vehicle deviated from planned route | ~50/day | Medium |
| ROUTE_COMPLETED | Route successfully completed | ~350/day | High |
| ROUTE_UPDATED | Route modified during transit | ~100/day | Medium |
| TRAFFIC_ALERT | Traffic condition affecting route | ~200/day | Medium |
| ROUTE_ETA_UPDATED | Estimated arrival time updated | ~1000/day | Medium |

#### 2.1.5 System Events
Events related to system operations and alerts:

| Event Type | Description | Frequency | Criticality |
|------------|-------------|-----------|-------------|
| SYSTEM_ALERT | General system alert | ~100/day | High |
| AI_PREDICTION | ML model prediction generated | ~500/day | Medium |
| INTEGRATION_ERROR | External system integration error | ~20/day | High |
| DATA_QUALITY_ISSUE | Data validation failure | ~30/day | Medium |
| PERFORMANCE_DEGRADATION | System performance alert | ~10/day | High |

---

## 3. Event Schema Definitions

### 3.1 Base Event Structure
All events inherit from a common base structure:

```json
{
  "eventId": "uuid",
  "eventType": "string",
  "eventVersion": "string",
  "timestamp": "ISO 8601 datetime",
  "source": {
    "system": "string",
    "service": "string",
    "version": "string"
  },
  "correlationId": "uuid",
  "traceId": "uuid",
  "entityType": "string",
  "entityId": "uuid",
  "data": {
    // Event-specific payload
  },
  "metadata": {
    "userId": "uuid",
    "sessionId": "uuid",
    "ipAddress": "string",
    "userAgent": "string"
  }
}
```

### 3.2 Load Event Schemas

#### 3.2.1 LOAD_CREATED
```json
{
  "eventType": "LOAD_CREATED",
  "eventVersion": "1.0",
  "entityType": "LOAD",
  "entityId": "load-uuid",
  "data": {
    "loadNumber": "string",
    "customerId": "uuid",
    "pickupLocation": {
      "latitude": "number",
      "longitude": "number",
      "address": "string"
    },
    "deliveryLocation": {
      "latitude": "number", 
      "longitude": "number",
      "address": "string"
    },
    "pickupDate": "ISO 8601 datetime",
    "deliveryDate": "ISO 8601 datetime",
    "weight": "number",
    "volume": "number",
    "commodityType": "string",
    "specialRequirements": ["string"],
    "rate": "number"
  }
}
```

#### 3.2.2 LOAD_ASSIGNED
```json
{
  "eventType": "LOAD_ASSIGNED",
  "eventVersion": "1.0",
  "entityType": "LOAD",
  "entityId": "load-uuid",
  "data": {
    "loadNumber": "string",
    "driverId": "uuid",
    "vehicleId": "uuid",
    "assignedBy": "uuid",
    "assignmentDate": "ISO 8601 datetime",
    "estimatedPickupTime": "ISO 8601 datetime",
    "estimatedDeliveryTime": "ISO 8601 datetime"
  }
}
```

#### 3.2.3 LOAD_STATUS_UPDATED
```json
{
  "eventType": "LOAD_STATUS_UPDATED",
  "eventVersion": "1.0",
  "entityType": "LOAD",
  "entityId": "load-uuid",
  "data": {
    "loadNumber": "string",
    "previousStatus": "string",
    "newStatus": "string",
    "location": {
      "latitude": "number",
      "longitude": "number",
      "address": "string"
    },
    "statusReason": "string",
    "updatedBy": "uuid"
  }
}
```

### 3.3 Vehicle Event Schemas

#### 3.3.1 VEHICLE_LOCATION_UPDATED
```json
{
  "eventType": "VEHICLE_LOCATION_UPDATED",
  "eventVersion": "1.0",
  "entityType": "VEHICLE",
  "entityId": "vehicle-uuid",
  "data": {
    "vehicleNumber": "string",
    "location": {
      "latitude": "number",
      "longitude": "number",
      "accuracy": "number",
      "altitude": "number"
    },
    "speed": "number",
    "heading": "number",
    "odometer": "number",
    "fuelLevel": "number",
    "engineHours": "number",
    "driverId": "uuid",
    "loadId": "uuid"
  }
}
```

#### 3.3.2 VEHICLE_STATUS_CHANGED
```json
{
  "eventType": "VEHICLE_STATUS_CHANGED",
  "eventVersion": "1.0",
  "entityType": "VEHICLE",
  "entityId": "vehicle-uuid",
  "data": {
    "vehicleNumber": "string",
    "previousStatus": "string",
    "newStatus": "string",
    "statusReason": "string",
    "location": {
      "latitude": "number",
      "longitude": "number"
    },
    "changedBy": "uuid"
  }
}
```

### 3.4 Driver Event Schemas

#### 3.4.1 DRIVER_STATUS_CHANGED
```json
{
  "eventType": "DRIVER_STATUS_CHANGED",
  "eventVersion": "1.0",
  "entityType": "DRIVER",
  "entityId": "driver-uuid",
  "data": {
    "driverNumber": "string",
    "previousStatus": "string",
    "newStatus": "string",
    "location": {
      "latitude": "number",
      "longitude": "number"
    },
    "hoursRemaining": "number",
    "nextBreakDue": "ISO 8601 datetime",
    "vehicleId": "uuid"
  }
}
```

#### 3.4.2 DRIVER_HOS_VIOLATION
```json
{
  "eventType": "DRIVER_HOS_VIOLATION",
  "eventVersion": "1.0",
  "entityType": "DRIVER",
  "entityId": "driver-uuid",
  "data": {
    "driverNumber": "string",
    "violationType": "string",
    "violationDetails": "string",
    "currentHours": "number",
    "maxAllowedHours": "number",
    "location": {
      "latitude": "number",
      "longitude": "number"
    },
    "severity": "string",
    "actionRequired": "string"
  }
}
```

### 3.5 Route Event Schemas

#### 3.5.1 ROUTE_OPTIMIZED
```json
{
  "eventType": "ROUTE_OPTIMIZED",
  "eventVersion": "1.0",
  "entityType": "ROUTE",
  "entityId": "route-uuid",
  "data": {
    "route_id": "uuid",
    "load_ids": ["uuid"],
    "vehicle_id": "uuid",
    "driver_id": "uuid (optional)",
    "original_distance": "number (miles)",
    "optimized_distance": "number (miles)",
    "time_saved": "number (minutes)",
    "fuel_saved": "number (gallons)",
    "algorithm_used": "string (google_maps_api, straight_line, etc.)",
    "optimization_score": "number (0-100)",
    "traffic_considered": "boolean",
    "steps_count": "number",
    "encoded_polyline": "string (optional - Google Maps encoded polyline)"
  }
}
```

#### 3.5.2 ROUTE_DEVIATION
```json
{
  "eventType": "ROUTE_DEVIATION",
  "eventVersion": "1.0",
  "entityType": "ROUTE",
  "entityId": "route-uuid",
  "data": {
    "loadId": "uuid",
    "vehicleId": "uuid",
    "driverId": "uuid",
    "plannedLocation": {
      "latitude": "number",
      "longitude": "number"
    },
    "actualLocation": {
      "latitude": "number",
      "longitude": "number"
    },
    "deviationDistance": "number",
    "deviationReason": "string",
    "impactOnETA": "number",
    "actionTaken": "string"
  }
}
```

---

## 4. Kafka Topic Organization

### 4.1 Topic Structure
Events are organized into Kafka topics based on domain and processing requirements:

#### 4.1.1 Core Domain Topics
```
tms.loads          - All load-related events
tms.vehicles       - Vehicle operational events  
tms.vehicles.tracking - High-frequency location updates
tms.drivers        - Driver management events
tms.drivers.tracking - Driver location and status updates
tms.routes         - Route planning and optimization events
tms.routes.alerts  - Route deviations and traffic alerts
tms.customers      - Customer-related events
tms.system.alerts  - System-wide alerts and notifications
tms.ai.predictions - Machine learning predictions and insights
```

#### 4.1.2 Topic Configuration
```yaml
topics:
  tms.loads:
    partitions: 12
    replication-factor: 3
    retention.ms: 604800000  # 7 days
    compression.type: lz4
    
  tms.vehicles.tracking:
    partitions: 24
    replication-factor: 3
    retention.ms: 86400000   # 1 day
    compression.type: snappy
    
  tms.drivers:
    partitions: 8
    replication-factor: 3
    retention.ms: 2592000000 # 30 days
    compression.type: lz4
    
  tms.system.alerts:
    partitions: 4
    replication-factor: 3
    retention.ms: 2592000000 # 30 days
    compression.type: gzip
```

### 4.2 Event Routing Strategy

#### 4.2.1 Partitioning Strategy
- **Load Events**: Partition by customer_id for load balancing
- **Vehicle Events**: Partition by vehicle_id for ordered processing
- **Driver Events**: Partition by driver_id for state consistency
- **Route Events**: Partition by geographic region for locality

#### 4.2.2 Message Ordering
- Critical for state-dependent events (driver status, vehicle location)
- Ensured through consistent partitioning keys
- Dead letter queues for processing failures

---

## 5. Event Processing Patterns

### 5.1 Event Sourcing Pattern
```json
{
  "pattern": "Event Sourcing",
  "description": "All state changes captured as events",
  "benefits": [
    "Complete audit trail",
    "State reconstruction capability", 
    "Temporal queries",
    "Event replay for testing"
  ],
  "implementation": {
    "storage": "Kafka + TimescaleDB",
    "snapshots": "PostgreSQL",
    "projections": "Real-time materialized views"
  }
}
```

### 5.2 CQRS (Command Query Responsibility Segregation)
```json
{
  "pattern": "CQRS",
  "description": "Separate read and write models",
  "commands": [
    "CREATE_LOAD",
    "ASSIGN_DRIVER", 
    "UPDATE_LOCATION",
    "COMPLETE_DELIVERY"
  ],
  "queries": [
    "GET_LOAD_STATUS",
    "FIND_AVAILABLE_DRIVERS",
    "CALCULATE_ROUTE_EFFICIENCY",
    "GENERATE_ANALYTICS_REPORT"
  ]
}
```

### 5.3 Saga Pattern
```json
{
  "pattern": "Saga",
  "description": "Distributed transaction management",
  "use_cases": [
    "Load assignment workflow",
    "Route optimization process",
    "Driver compliance checking",
    "Multi-step dispatch operations"
  ],
  "compensation_events": [
    "LOAD_ASSIGNMENT_FAILED",
    "ROUTE_OPTIMIZATION_TIMEOUT",
    "DRIVER_UNAVAILABLE", 
    "VEHICLE_BREAKDOWN_RECOVERY"
  ]
}
```

---

## 6. Event Versioning and Evolution

### 6.1 Versioning Strategy
```json
{
  "strategy": "Semantic Versioning",
  "format": "MAJOR.MINOR.PATCH",
  "rules": {
    "MAJOR": "Breaking changes to event structure",
    "MINOR": "Backward-compatible additions",
    "PATCH": "Bug fixes and clarifications"
  },
  "examples": {
    "1.0.0": "Initial event schema",
    "1.1.0": "Added optional fields",
    "2.0.0": "Changed required field types"
  }
}
```

### 6.2 Schema Evolution
```json
{
  "backward_compatibility": {
    "required": true,
    "duration": "minimum 6 months",
    "strategy": "Field deprecation with migration period"
  },
  "migration_process": {
    "step1": "Deploy new schema version",
    "step2": "Dual-write to old and new versions",
    "step3": "Migrate consumers to new version",
    "step4": "Stop writing old version",
    "step5": "Remove old schema support"
  }
}
```

---

## 7. Event Monitoring and Observability

### 7.1 Key Metrics
- **Event Volume**: Events per second by type and topic
- **Processing Latency**: End-to-end event processing time
- **Error Rates**: Failed events by type and reason
- **Consumer Lag**: Delay in event processing by consumer
- **Schema Validation**: Invalid events by schema version

### 7.2 Alerting Thresholds
```json
{
  "critical_alerts": {
    "DRIVER_HOS_VIOLATION": "immediate",
    "VEHICLE_BREAKDOWN": "immediate",
    "LOAD_DELIVERY_FAILED": "5 minutes"
  },
  "warning_alerts": {
    "HIGH_EVENT_VOLUME": "> 150% normal rate",
    "CONSUMER_LAG": "> 5 minutes",
    "SCHEMA_VALIDATION_ERRORS": "> 1% of events"
  }
}
```

### 7.3 Event Replay and Recovery
- **Point-in-time Recovery**: Replay events from specific timestamp
- **State Reconstruction**: Rebuild system state from event history
- **Testing Support**: Event replay for integration testing
- **Debugging**: Trace event flow through distributed system

---

## 8. Security and Compliance

### 8.1 Event Security
- **Encryption**: All events encrypted in transit and at rest
- **Authentication**: Producer authentication for event publishing
- **Authorization**: Consumer authorization for topic access
- **Audit**: All event access logged and monitored

### 8.2 Event Schema Validation and Testing

#### 8.2.1 Comprehensive Test Coverage
The event schema has been thoroughly validated through comprehensive testing achieving **100% pass rate** in our test suite:

**Event Model Tests:**
- **Base Event Structure**: Validates all required fields (`eventType`, `timestamp`, `entityType`, `entityId`)
- **Event Type Compliance**: Ensures all event types align with PRD specifications
- **Route Optimized Event Schema**: Validates route optimization event structure and data payload
- **Event API Compatibility**: Tests event publishing and consumption workflows
- **Cross-system Event Flow**: Validates event propagation across services

#### 8.2.2 Enhanced Event Models
The event models include comprehensive validation and enhanced attributes:

**BaseEvent Enhancements:**
- **Data Attribute**: Added flexible `data` field for event-specific payload
- **Timezone-Aware Timestamps**: All datetime fields use timezone-aware formatting
- **UUID Validation**: Proper UUID pattern validation for `eventId`, `correlationId`, `traceId`
- **Pydantic V2 Compatibility**: Modern validation patterns and field definitions

**Route Optimization Events:**
- **Enhanced Payload**: Includes `optimization_score`, `fuel_estimate`, `toll_estimate`
- **Spatial Data**: Google Maps API-compatible coordinate validation
- **Performance Metrics**: Route efficiency and cost estimation data

#### 8.2.3 Event Validation Rules

**Schema Validation:**
- **Required Fields**: All base event fields properly validated as required
- **Type Safety**: Strong typing for all event fields with proper validation
- **Enum Validation**: Event types validated against defined enums
- **Payload Validation**: Event-specific data validated according to schema

**Business Logic Validation:**
- **Event Sequencing**: Ensures logical event ordering (e.g., LOAD_CREATED before LOAD_ASSIGNED)
- **State Consistency**: Validates event data consistency with entity state
- **Correlation Tracking**: Proper correlation ID usage for event tracing

### 8.3 Data Privacy
- **PII Protection**: Sensitive data tokenized or encrypted
- **Retention Policies**: Automatic deletion per compliance requirements
- **Access Controls**: Role-based access to event data
- **Anonymization**: PII removed from non-production environments

### 8.3 Compliance Requirements
- **DOT Regulations**: Driver hours and vehicle inspection events
- **FMCSA Rules**: Hours of service violation tracking
- **SOX Compliance**: Financial transaction event audit trails
- **Data Retention**: Industry-specific retention requirements

This comprehensive events schema provides the foundation for a transparent, scalable, and compliant event-driven Transportation Management System, enabling real-time operations and comprehensive system observability.
