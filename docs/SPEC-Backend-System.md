# TMS Backend System Technical Specification

**Version:** 1.0
**Date:** July 5, 2025
**Authors:** Development Team
**Tags:** #technical-spec #TMS-Backend #TMS-Core #status/implemented #priority/high #route-optimization
**Related:** [[PRD-Overview]] | [[SPEC-Database-Schema]] | [[SPEC-Events-Schema]] | [[SPEC-Route-Optimization-Setup]] | [[SPEC-Polyglot-Persistence]]
**Dependencies:** [[SPEC-Database-Schema]], [[SPEC-Events-Schema]]
**Used By:** [[PRD-Dispatching-Interface]], Frontend Applications

---

## Executive Summary

Comprehensive FastAPI-based backend system implementing event-driven microservices architecture with polyglot persistence (PostgreSQL, TimescaleDB, Neo4j) and Kafka-based event streaming. Features async operations, WebSocket real-time communication, and Google Maps API integration for route optimization.

---

## Implementation Status

**Currently Implemented ✅:**
- **FastAPI Framework**: Complete REST API with async operations
- **Polyglot Persistence**: PostgreSQL, TimescaleDB, and Neo4j integrations
- **Event Streaming**: Full Kafka producer/consumer implementation
- **Real-time Communication**: WebSocket support for live updates
- **CRUD Operations**: Comprehensive load, vehicle, and driver management
- **Route Optimization**: Google Maps API integration with PostGIS storage
- **Analytics Endpoints**: Dashboard data and metrics APIs
- **Data Validation**: Pydantic V2 models with comprehensive validation
- **Spatial Data Processing**: PostGIS LINESTRING route geometry storage
- **Comprehensive Testing**: 100% test pass rate (49/49 tests) with full API compatibility validation
- **Google Maps API Integration**: Coordinate validation compatible with Maps API standards
- **Financial Precision**: Decimal type usage for accurate monetary calculations
- **UUID Validation**: Pydantic V2-compatible UUID pattern validation
- **Request/Response Models**: Complete API model coverage with LoadResponse, VehicleResponse, DriverResponse

**Testing & Quality Assurance ✅:**
- **49/49 Tests Passing**: Complete test suite validation in Docker environment
- **API Compatibility Tests**: Request/response model validation
- **Schema Validation Tests**: Database schema alignment verification
- **Cross-layer Compatibility**: End-to-end workflow validation
- **Coordinate Validation**: Google Maps API-compatible lat/lon validation
- **Event Model Tests**: Complete event schema validation
- **PRD Alignment Tests**: Model compliance with PRD specifications

**Areas for Enhancement 🔄:**
- **Advanced ML Integration**: MLserver API integration (planned)
- **Caching Strategy**: Redis utilization for performance optimization
- **Advanced Security**: Authentication and authorization implementation
- **Performance Optimization**: Database query optimization and indexing

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
  - PostgreSQL (OLTP operations, core entities, uses PostGIS for geospatial data support)
  - TimescaleDB (time-series data, tracking)
  - Neo4j (graph operations, route optimization)
- **Caching**: Redis (TBD, currently unused)
- **Real-time**: WebSocket connections
- **Containerization**: Docker with docker-compose

### Database Architecture
1. **PostgreSQL**: Core business entities (loads, vehicles, drivers, carriers)
2. **TimescaleDB**: Time-series data (vehicle tracking, driver activity, load events)
3. **Neo4j**: Graph relationships and route optimization queries

#### Database Infrastructure Requirements

**PostgreSQL + PostGIS:**
- Standard `postgis/postgis:16-3.4` image provides both PostgreSQL and PostGIS
- Required for spatial operations on pickup/delivery locations
- Supports `GEOGRAPHY` and `GEOMETRY` data types

**TimescaleDB + PostGIS:**
- **CRITICAL:** Must use `timescale/timescaledb-ha:pg16` (includes PostGIS)
- **DO NOT USE:** `timescale/timescaledb:latest-pg16` (lacks PostGIS extension)
- Required for vehicle tracking spatial analysis and route analytics
- Enables `GEOGRAPHY(POINT, 4326)` for GPS coordinates

**Docker Compose Configuration:**
```yaml
# Correct TimescaleDB configuration
timescaledb:
  image: timescale/timescaledb-ha:pg16  # PostGIS included
  environment:
    POSTGRES_DB: tms_timeseries
    POSTGRES_USER: timescale_user
    POSTGRES_PASSWORD: timescale_password
  # init.sql requires both TimescaleDB and PostGIS extensions

# PostgreSQL configuration  
postgres:
  image: postgis/postgis:16-3.4  # PostGIS included
  environment:
    POSTGRES_DB: tms_oltp
    POSTGRES_USER: tms_user
    POSTGRES_PASSWORD: tms_password
```

**Extension Verification:**
Both databases require these extensions to be available:
- `timescaledb` (TimescaleDB only)
- `postgis` (both databases)

#### Troubleshooting PostGIS Issues

**Common Error: "extension 'postgis' is not available"**
- **Cause:** Using TimescaleDB image without PostGIS support
- **Solution:** Switch to `timescale/timescaledb-ha:pg16`
- **Verification:** `docker exec container_name psql -U user -d db -c "SELECT extname FROM pg_extension WHERE extname='postgis';"`

**Container Startup Failures:**
- Check logs: `docker logs container_name`
- Verify image supports PostGIS before deployment
- Ensure init.sql scripts don't reference unavailable extensions

### Supported Functionality

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
- Status tracking (AVAILABLE, ASSIGNED, IN_TRANSIT, MAINTENANCE)
- Carrier association and fleet management
- Telemetry data integration (fuel, odometer, engine hours)

### 3. Driver Management

#### Capabilities
- Driver status management (AVAILABLE, DRIVING, ON_DUTY, OFF_DUTY, SLEEPER_BERTH)
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

#### Google Maps Integration
Our production-ready route optimization service uses Google Maps Directions API for street-level routing:

- **Optimize Load Route** (`POST /api/routes/optimize-load`)
  - Load + Vehicle + Optional Driver optimization
  - Google Maps Directions API integration
  - Traffic-aware routing with real-time conditions
  - PostGIS LINESTRING storage for precise coordinates
  - Fallback to straight-line calculation when API unavailable

- **Get Route Details** (`GET /api/routes/{route_id}`)
  - Detailed route information with coordinates
  - Turn-by-turn directions and waypoints
  - Optimization metrics and performance scores
  - Map-ready coordinate arrays for frontend display

#### Service Architecture
```python
# services/route_optimization.py
class RouteOptimizationService:
    - Google Maps API client with traffic optimization
    - PostGIS geometry storage (LINESTRING)
    - Kafka event publishing for ROUTE_OPTIMIZED
    - Optimization scoring algorithm (0-100 scale)
    - Flexible driver assignment (nullable driver_id)
```

#### Database Integration
- **Routes Table**: PostGIS-enabled with LINESTRING geometry
- **Spatial Queries**: ST_GeogFromText for origin/destination points
- **Optimization Metrics**: Score, fuel estimate, toll estimate storage
- **Flexible Assignment**: Nullable driver_id supports operational changes

#### Event Integration
- **ROUTE_OPTIMIZED Events**: Published to `tms.routes` Kafka topic
- **Real-time Updates**: WebSocket broadcasting to connected clients
- **Event Schema**: Aligned with PRD Events Schema specification
- **Structured Data**: Route metrics, optimization details, coordinates

#### Optimization Features
- **Traffic Consideration**: Real-time traffic data integration
- **Flexible Driver Assignment**: Routes survive driver changes
- **Optimization Scoring**: 0-100 efficiency rating system
- **Fallback Strategy**: Straight-line calculation when Maps API unavailable
- **Performance Analytics**: Route efficiency and fuel consumption estimates

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
- **Load Events**: CREATED, ASSIGNED, PICKED_UP, IN_TRANSIT, DELIVERED, CANCELLED, DELAYED
- **Vehicle Events**: LOCATION_UPDATED, STATUS_CHANGED, MAINTENANCE_DUE
- **Driver Events**: STATUS_CHANGED, LOCATION_UPDATED, HOS_VIOLATION  
- **Route Events**: OPTIMIZED, DEVIATION, COMPLETED
- **Carrier Events**: PERFORMANCE_UPDATED, CAPACITY_CHANGED
- **System Events**: ALERTS, AI_PREDICTIONS

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
**CRITICAL NAMING CONVENTION:**
All enum values MUST be UPPERCASE with underscores for separation (SCREAMING_SNAKE_CASE). This ensures consistency between Python code, database schemas, and API interfaces. Never use lowercase or camelCase for enum values.

- **LoadStatus**: CREATED, ASSIGNED, PICKED_UP, IN_TRANSIT, DELIVERED, CANCELLED, DELAYED
- **VehicleStatus**: AVAILABLE, ASSIGNED, IN_TRANSIT, MAINTENANCE, OUT_OF_SERVICE  
- **DriverStatus**: AVAILABLE, DRIVING, ON_DUTY, OFF_DUTY, SLEEPER_BERTH

**Examples:**
```python
# ✅ CORRECT - Uppercase enum values
class VehicleStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    IN_TRANSIT = "IN_TRANSIT"

# ❌ INCORRECT - Lowercase enum values
class VehicleStatus(str, Enum):
    available = "available"
    in_transit = "in_transit"
```

**Database Schema Alignment:**
```sql
-- ✅ CORRECT - Database enums must match Python enums exactly
CREATE TYPE vehicle_status_enum AS ENUM ('AVAILABLE', 'ASSIGNED', 'IN_TRANSIT', 'MAINTENANCE', 'OUT_OF_SERVICE');

-- ❌ INCORRECT - Case mismatch causes runtime errors
CREATE TYPE vehicle_status_enum AS ENUM ('available', 'assigned', 'in_transit');
```

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

## 7. Audit & Change-Data-Capture Roadmap

### Current State
Application-level Kafka producers emit domain events (e.g. `LOAD_ASSIGNED`) directly from FastAPI endpoints.  There is no permanent audit table and Debezium is running without connectors.

### Target State (Q3-2025)
1. **Audit Table** – `audit_logs` (UUID id, table_name, record_id, action, changed_data JSONB, user_id, created_at).
2. **Application Audit Writes** – Repositories write an audit row for every mutating action **before** emitting the domain event.
3. **Debezium CDC** – A single Postgres connector captures changes for: `loads`, `drivers`, `vehicles`, `carriers`, `routes`, `audit_logs`.
   • Connector name: `tms-pg-cdc`  
   • Topic pattern: `tms.cdc.<table>`  
   • Offset / status topics stored in Kafka (`debezium_offsets`, `debezium_status`).
4. **Audit Event Stream** – Flink job `AuditAnomalyJob` consumes `tms.cdc.audit_logs` and writes results to:
   • `audit_logs` table (back-write via JDBC sink) – ensures idempotent persistence.  
   • `tms.anomalies` topic when an anomaly is detected.
5. **Anomaly Detection (Phase-1 stub)** – Simple rule engine (rate > 1 msg/s for same user_id triggers `ANOMALY_SUSPECTED`).  Phase-2 will swap in an ML model hosted on ML-Server.

### Success Criteria
• 100 % of mutating API calls produce a corresponding audit row.  
• Debezium lag < 2 s under 1 k rps.  
• Flink job end-to-end latency < 1 s (95-th percentile).  
• Anomalies forwarded to `tms.anomalies` within 3 s.

---

## Conclusion

The TMS Backend System provides a robust, scalable foundation for transportation management operations. With its event-driven architecture, multi-database integration, and real-time capabilities, it supports comprehensive logistics workflows while maintaining the flexibility for future enhancements and integrations.

The system successfully addresses the core requirements of load management, vehicle tracking, driver coordination, and real-time monitoring while providing the architectural foundation for advanced features like AI-powered optimization and external system integrations.