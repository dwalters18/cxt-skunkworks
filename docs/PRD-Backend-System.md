# Product Requirements Document: TMS Backend System

> **Revision Note – July 2025**  
> This PRD has been updated to reflect the July 2025 architecture review. The addenda below clarify caching strategy, authentication, schema governance, observability, disaster-recovery, and Google Maps cost controls.

## July 2025 Addenda
1. **Caching Strategy** – Redis is optional. Decision due Sprint 0: either remove completely or implement as:
   • Geocode result cache (Google Maps)  
   • WebSocket session store  
   • Dashboard hotspot cache (TTL ≤ 60 s)
2. **Authentication & RBAC** – Adopt OAuth 2.1 (Keycloak) with role matrix: *Admin, Dispatcher, CSR, Driver*. Add epics in Sprint 2.
3. **Kafka Schema Governance** – Introduce Confluent Schema Registry (or open-source equivalent) with Avro schemas; enforce compatibility=BACKWARD.
4. **Observability** – Standardise on OpenTelemetry tracing + Prometheus metrics + Grafana dashboards. Deliver in Sprint 0.
5. **Disaster Recovery Targets** – RPO ≤ 15 min, RTO ≤ 1 hr. Add cross-AZ Postgres replica, Timescale continuous archiving, Neo4j backup cron.
6. **Google Maps Cost Control** – Enable daily quota caps, cache geocoding responses, and throttle Directions requests.
7. **Accessibility & UX Performance** – All APIs used by UI must support data shaping/pagination; bundle size target ≤ 200 KB gzip; WCAG 2.1-AA.

---

## Executive Summary

The Transportation Management System (TMS) Backend provides a comprehensive, event-driven microservices architecture designed to manage logistics operations including load management, vehicle tracking, driver coordination, route optimization, and real-time analytics. Built on FastAPI with a multi-database architecture and Kafka-based event streaming, the system supports both operational workflows and real-time monitoring capabilities.

## Problem Statement

Transportation and logistics operations require robust, scalable backend systems that can:
- Handle high-volume transactional operations (loads, vehicles, drivers)
- Process real-time location and status updates
- Provide complex routing and optimization capabilities
- Support real-time monitoring and analytics
- Integrate with external systems and APIs
- Maintain data consistency across multiple data stores

## Goals and Success Metrics

### Primary Goals
- **Operational Efficiency**: Streamline load assignment, vehicle tracking, and driver management
- **Real-time Visibility**: Provide instant updates on operational status across all entities
- **Scalability**: Support growing transaction volumes and concurrent users
- **Data Integrity**: Maintain consistent data across multiple databases and systems
- **System Reliability**: Ensure 99.9% uptime with robust error handling and recovery

### Success Metrics
- API response times < 200ms for 95% of requests
- Event processing latency < 100ms
- Zero data loss during event streaming
- 99.9% API uptime
- Support for 10,000+ concurrent WebSocket connections

## Current System Architecture

### Technology Stack
- **API Framework**: FastAPI (Python)
- **Event Streaming**: Apache Kafka (KRaft mode)
- **Databases**:
  - PostgreSQL (OLTP operations, core entities)
  - TimescaleDB (time-series data, tracking)
  - Neo4j (graph operations, route optimization)
- **Caching**: Redis (configured, currently unused)
- **Real-time**: WebSocket connections
- **Containerization**: Docker with docker-compose

### Database Architecture
1. **PostgreSQL**: Core business entities (loads, vehicles, drivers, carriers)
2. **TimescaleDB**: Time-series data (vehicle tracking, driver activity, load events)
3. **Neo4j**: Graph relationships and route optimization queries

## Supported Functionality

### 1. Load Management API

#### Core Operations
- **Create Load** (`POST /api/loads`)
  - Generate new load records with pickup/delivery details
  - Support for weight, volume, rate specifications
  - Automatic load number generation and validation

- **Assign Load** (`POST /api/loads/{load_id}/assign`)
  - Assign carriers, vehicles, and drivers to loads
  - Validation of entity availability and compatibility
  - Automatic status transitions and event emission

- **Update Load Status** (`PUT /api/loads/{load_id}/status`)
  - Status progression (pending → assigned → picked_up → in_transit → delivered)
  - Automatic event generation for status changes
  - Integration with tracking and analytics systems

- **Search Loads** (`GET /api/loads/search`)
  - Advanced filtering by status, carrier, location, date ranges
  - Pagination support (limit/offset)
  - Full-text search capabilities

- **Load Details** (`GET /api/loads/{load_id}`)
  - Complete load information including assignments
  - Related entity details (carrier, vehicle, driver)
  - Status history and tracking information

#### Data Model Features
- UUID-based primary keys
- PostGIS geography support for locations
- JSONB fields for flexible metadata
- Audit trail with created/updated timestamps
- Status enum validation

### 2. Vehicle Management API

#### Core Operations
- **Get Vehicles** (`GET /api/vehicles`)
  - Filter by carrier, status, availability
  - Location-based queries using PostGIS
  - Capacity and capability filtering

- **Update Vehicle Location** (`PUT /api/vehicles/{vehicle_id}/location`)
  - Real-time GPS coordinate updates
  - Integration with TimescaleDB for tracking history
  - Automatic event emission for location changes

- **Vehicle Tracking History** (`GET /api/vehicles/{vehicle_id}/tracking`)
  - Historical location data from TimescaleDB
  - Time-range filtering and aggregation
  - Speed, heading, and telemetry data

#### Vehicle Features
- Real-time location tracking with PostGIS
- Capacity management (weight/volume)
- Status tracking (available, assigned, in_transit, maintenance)
- Carrier association and fleet management
- Telemetry data integration (fuel, odometer, engine hours)

### 3. Driver Management

#### Capabilities
- Driver status management (available, driving, on_duty, off_duty, sleeper_berth)
- HOS (Hours of Service) compliance tracking
- License validation and management
- Real-time location updates
- Carrier assignment and fleet coordination

#### Data Integration
- TimescaleDB integration for activity tracking
- Driver performance metrics
- Compliance monitoring and alerting
- Contact information management

### 4. Route Optimization API

#### Neo4j Integration
- **Find Optimal Route** (`POST /api/routes/optimize`)
  - Graph-based route calculations
  - Multi-constraint optimization (distance, time, cost)
  - Real-time traffic and condition integration
  - Waypoint and stop optimization

#### Optimization Features
- Multiple optimization strategies (distance, time, fuel efficiency)
- Constraint handling (vehicle restrictions, driver hours)
- Real-time route adjustments
- Performance analytics and reporting

### 5. Event Management System

#### Event Publishing
- **Manual Event Publishing** (`POST /api/events/publish`)
  - Support for all event types defined in EventType enum
  - Payload validation and schema enforcement
  - Automatic topic routing based on event type

- **Event Topics** (`GET /api/events/topics`)
  - List all active Kafka topics
  - Topic health and status monitoring
  - Consumer group management

#### Event Types Supported
- **Load Events**: created, assigned, picked_up, in_transit, delivered, cancelled
- **Vehicle Events**: location_updated, status_changed, maintenance_due
- **Driver Events**: status_changed, location_updated, hos_violation  
- **Route Events**: optimized, deviation, completed
- **Carrier Events**: performance_updated, capacity_changed
- **System Events**: alerts, AI predictions

#### Kafka Integration
- **Topics**: tms.loads, tms.vehicles, tms.vehicles.tracking, tms.drivers, tms.routes, tms.carriers, tms.system.alerts, tms.ai.predictions
- **Event Routing**: Automatic topic assignment based on event type
- **Error Handling**: Dead letter queue support and retry mechanisms
- **Consumer Groups**: Organized event processing with load balancing

### 6. Real-time WebSocket API

#### WebSocket Endpoint (`/ws`)
- Real-time event streaming to connected clients
- Automatic event broadcasting from Kafka consumers
- Connection management and client tracking
- JSON-based message protocol

#### Features
- Multi-client support with connection pooling
- Event filtering and subscription management
- Heartbeat and connection health monitoring
- Graceful disconnect handling

### 7. Analytics and Dashboard API

#### Dashboard Data (`GET /api/dashboard`)
- Real-time operational metrics
- Load status distribution
- Vehicle utilization statistics
- Driver activity summaries
- Performance KPIs and trends

#### Analytics Features
- Time-series data aggregation from TimescaleDB
- Cross-database queries and joins
- Cached results for performance optimization
- Customizable date ranges and filters

### 8. Health and Monitoring

#### Health Check (`GET /health`)
- Database connection status
- Kafka producer/consumer health
- System resource monitoring
- Dependency service status

#### Monitoring Features
- Structured logging with correlation IDs
- Error tracking and alerting
- Performance metrics collection
- Database connection pooling status

## Data Models and Schema

### Core Domain Entities

#### Load
```python
class Load(BaseEntity):
    load_number: str
    shipper_id: Optional[str]
    consignee_id: Optional[str]
    carrier_id: Optional[str]
    vehicle_id: Optional[str]
    driver_id: Optional[str]
    pickup_location: Location
    delivery_location: Location
    pickup_address: str
    delivery_address: str
    pickup_datetime: datetime
    delivery_datetime: datetime
    weight: Optional[float]
    volume: Optional[float]
    rate: Optional[float]
    status: LoadStatus
```

#### Vehicle
```python
class Vehicle(BaseEntity):
    carrier_id: str
    vehicle_number: str
    vehicle_type: str
    capacity_weight: Optional[float]
    capacity_volume: Optional[float]
    status: VehicleStatus
    current_location: Optional[Location]
    fuel_level: Optional[float]
    odometer: Optional[float]
```

#### Driver
```python
class Driver(BaseEntity):
    carrier_id: str
    license_number: str
    name: str
    phone: Optional[str]
    email: Optional[str]
    status: DriverStatus
    current_location: Optional[Location]
    hours_remaining: Optional[float]
```

### Status Enumerations
- **LoadStatus**: pending, assigned, picked_up, in_transit, delivered, cancelled
- **VehicleStatus**: available, assigned, in_transit, maintenance, out_of_service
- **DriverStatus**: available, driving, on_duty, off_duty, sleeper_berth

## API Design Principles

### RESTful Architecture
- Resource-based URLs with consistent naming
- HTTP methods aligned with operations (GET, POST, PUT, DELETE)
- Proper HTTP status codes and error responses
- JSON request/response format

### Request/Response Patterns
- Consistent error response format with error codes
- Pagination support for list endpoints
- Optional parameters for filtering and sorting
- Comprehensive input validation with Pydantic models

### Authentication and Security
- CORS middleware for cross-origin requests
- Input validation and sanitization
- SQL injection prevention through parameterized queries
- Error message sanitization to prevent information leakage

## Performance and Scalability

### Database Optimization
- Connection pooling for all databases
- Asynchronous database operations
- Proper indexing on frequently queried fields
- Query optimization with EXPLAIN analysis

### Caching Strategy
- Redis infrastructure (configured, ready for implementation)
- Repository-level caching patterns
- Response caching for dashboard endpoints
- Event deduplication and caching

### Horizontal Scaling
- Stateless API design
- Database connection pooling
- Kafka consumer group scaling
- Docker container orchestration ready

## Event-Driven Architecture

### Event Flow
1. **Event Generation**: API operations trigger events
2. **Event Publishing**: TMSEventProducer publishes to Kafka topics
3. **Event Processing**: TMSEventConsumer processes events asynchronously
4. **Event Broadcasting**: WebSocket connections receive real-time updates
5. **Event Storage**: Events stored in TimescaleDB for analytics

### Event Handling Patterns
- Asynchronous event processing with background tasks
- Event deduplication and idempotency
- Error handling with retry mechanisms
- Event versioning and schema evolution

## Integration Capabilities

### Internal Integration
- Multi-database transaction coordination
- Cross-service event communication
- Shared data models and validation
- Unified logging and monitoring

### External Integration Ready
- RESTful API for third-party integrations
- Webhook support for external notifications
- Event streaming for real-time integrations
- Standard authentication mechanisms (ready for implementation)

## Error Handling and Resilience

### Database Resilience
- Connection retry logic with exponential backoff
- Connection pool health monitoring
- Graceful degradation on database unavailability
- Transaction rollback and cleanup

### Event Processing Resilience
- Kafka consumer retry mechanisms
- Dead letter queue handling
- Event processing idempotency
- Consumer group rebalancing

### API Resilience
- Comprehensive exception handling
- Structured error responses
- Request timeout handling
- Circuit breaker patterns (ready for implementation)

## Security Considerations

### Current Security Features
- Input validation with Pydantic models
- SQL injection prevention
- CORS configuration
- Error message sanitization

### Security Ready Features
- Authentication middleware integration points
- Authorization framework compatibility
- API key management infrastructure
- Rate limiting infrastructure

## Deployment and Operations

### Container Architecture
- Docker-based deployment
- docker-compose orchestration
- Environment-based configuration
- Health check integration

### Monitoring and Observability
- Structured logging with Python logging
- Database connection monitoring
- API performance metrics
- Event processing metrics

### Configuration Management
- Environment variable configuration
- Database connection strings
- Kafka connection parameters
- Feature flags (ready for implementation)

## Future Enhancements

### Performance Optimizations
- Redis caching implementation
- Query optimization and indexing
- Connection pooling tuning
- Response compression

### Feature Extensions
- Advanced analytics and reporting
- Machine learning integration points
- External API integrations
- Enhanced security features

### Scalability Improvements
- Microservice decomposition readiness
- Kubernetes deployment preparation
- Database sharding strategies
- Event streaming optimization

## Success Criteria

### Functional Requirements Met
- Complete CRUD operations for all core entities
- Real-time event streaming and processing
- Multi-database integration and management
- RESTful API with comprehensive endpoints
- WebSocket real-time communication

### Performance Requirements Met
- Asynchronous operations and non-blocking I/O
- Connection pooling and resource management
- Event-driven architecture with Kafka integration
- Structured error handling and resilience

### Integration Requirements Met
- Multi-database transaction coordination
- Event-driven communication patterns
- Standard API interfaces for external integration
- Real-time data synchronization

## Conclusion

The TMS Backend System provides a robust, scalable foundation for transportation management operations. With its event-driven architecture, multi-database integration, and real-time capabilities, it supports comprehensive logistics workflows while maintaining the flexibility for future enhancements and integrations.

The system successfully addresses the core requirements of load management, vehicle tracking, driver coordination, and real-time monitoring while providing the architectural foundation for advanced features like AI-powered optimization and external system integrations.