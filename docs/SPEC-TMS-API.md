# TMS API Technical Specification

**Version:** 1.0  
**Date:** July 5, 2025  
**Authors:** Development Team  
**Tags:** #technical-spec #TMS-API #TMS-Core #status/implemented #priority/critical #api-contract
**Related:** [[PRD-Overview]] | [[PRD-Dispatching-Interface]] | [[SPEC-Backend-System]] | [[SPEC-Database-Schema]] | [[SPEC-Events-Schema]] | [[SPEC-Polyglot-Persistence]]
**Dependencies:** All TMS technical specifications
**Used By:** Frontend Applications, External Integrations, Internal Services

---

## 1. Executive Summary

### 1.1 Overview
The TMS API serves as the definitive contract for all external and internal API interactions within the Transportation Management System. This RESTful API implements event-driven architecture with real-time capabilities, leveraging polyglot persistence across PostgreSQL, TimescaleDB, and Neo4j databases [1,3,4]. The API provides comprehensive functionality for load management, vehicle tracking, driver management, route optimization, and real-time analytics [1,2,3].

### 1.2 Core Architectural Principles
- **Event-Driven Architecture**: Complete system transparency through comprehensive event streaming [1,5]
- **Polyglot Persistence**: Optimal database selection for specialized use cases [1,4,6]  
- **Real-Time Communication**: WebSocket integration for live operational updates [1,3,5]
- **Strict Data Validation**: Pydantic V2 compliance with comprehensive validation [3]
- **Spatial Data Processing**: PostGIS integration for geographic operations [3,4]
- **Modular Architecture**: Organized into domain-specific routers for maintainability and scalability [3]

### 1.3 API Scope
This specification covers all TMS API endpoints including Load Management, Vehicle Management, Driver Management, Route Optimization, Event Management, Analytics, and WebSocket real-time communication [3]. The API serves as the primary interface for the dispatching interface and external system integrations [2,3].

### 1.4 API Architecture
The TMS API is organized into modular, domain-specific routers:
- **Health Router** (`/health`): System health and status monitoring
- **Loads Router** (`/api/loads`): Load management and lifecycle operations
- **Drivers Router** (`/api/drivers`): Driver management and assignment workflows
- **Vehicles Router** (`/api/vehicles`): Vehicle tracking and management
- **Routes Router** (`/api/routes`): Route optimization and management
- **Events Router** (`/events`): Event management and streaming
- **Analytics Router** (`/analytics`): Dashboard and performance analytics
- **WebSocket Router** (`/ws`): Real-time communication endpoints

### 1.5 Backend Repository Architecture
The TMS API implements a clean **Repository Pattern** for data access layer separation, providing improved maintainability, testability, and separation of concerns:

**Repository Pattern Benefits:**
- **Separation of Concerns**: Database connection management separated from domain-specific data access logic
- **Maintainability**: Each repository has dedicated files making code easier to navigate and maintain
- **Testability**: Repository classes can be easily mocked and tested independently
- **Scalability**: New repository methods can be added without cluttering connection management code

**Application Structure:**
- **`/repositories/`**: Domain-specific data access layer with dedicated repository classes
  - `load_repository.py`: LoadRepository for load CRUD operations and search functionality
  - `vehicle_repository.py`: VehicleRepository for vehicle tracking and management
  - `audit_repository.py`: AuditRepository for audit logging and compliance tracking
  - `timescale_repository.py`: TimescaleRepository for time-series data operations
  - `neo4j_repository.py`: Neo4jRepository for graph database operations and route optimization
  - `base.py`: Base repository classes for PostgreSQL, TimescaleDB, and Neo4j
- **`/database/`**: Database connection management and pooling
  - `connections.py`: DatabaseManager class handling connection pools for all databases
- **`/dependencies.py`**: FastAPI dependency injection layer importing repositories for endpoint injection
- **`/models/`**: Pydantic data models and validation schemas
  - `domain.py`: Core business entity models (Load, Vehicle, Driver, etc.)
  - `events.py`: Event schema models for Kafka messaging
- **`/kafka/`**: Event streaming infrastructure
  - `producer.py`: Kafka event publishing logic
  - `consumer.py`: Kafka event consumption and processing
- **`/services/`**: Business logic layer
  - `route_optimization.py`: Route calculation and optimization services
- **`/websocket_manager.py`**: WebSocket connection management for real-time communication

### 1.6 SQL Parameter Formatting Standards

The TMS API implements **asyncpg-compliant parameter formatting** for all database queries to ensure compatibility with PostgreSQL's async driver and prevent SQL injection vulnerabilities.

**Parameter Placeholder Format:**
- **Use**: Numbered placeholders (`$1`, `$2`, `$3`, etc.)
- **Avoid**: Old-style `%s` placeholders (psycopg2 format)

**Dynamic Parameter Counting Pattern:**
```python
# Standard implementation pattern
conditions = []
params = []
param_counter = 1

if status:
    conditions.append(f"status = ${param_counter}")
    params.append(status)
    param_counter += 1
    
if customer_id:
    conditions.append(f"customer_id = ${param_counter}")
    params.append(customer_id)
    param_counter += 1

# Build final query with proper parameter numbering
query = f"SELECT * FROM table WHERE {' AND '.join(conditions)} LIMIT ${param_counter} OFFSET ${param_counter + 1}"
params.extend([limit, offset])
```

**Key Benefits:**
- **Compatibility**: Required for asyncpg PostgreSQL driver
- **Security**: Prevents SQL injection through proper parameterization
- **Maintainability**: Dynamic counter ensures correct numbering regardless of conditional filters
- **Scalability**: Easy to add/remove query conditions without renumbering parameters

**Implementation Examples:**
- **Single Condition**: `WHERE status = $1`
- **Multiple Conditions**: `WHERE status = $1 AND customer_id = $2`
- **Date Ranges**: `WHERE pickup_date >= $1 AND pickup_date <= $2`
- **PostGIS Spatial**: `WHERE ST_DWithin(location, ST_MakePoint($1, $2), $3)`
- **Pagination**: `LIMIT $n OFFSET $n+1`

This standard must be applied consistently across all repository classes and SQL query construction in the TMS API.

---

## 2. Core API Principles

### 2.1 RESTful Architecture
The TMS API follows RESTful design principles with consistent HTTP methods, status codes, and resource naming conventions [3]. All endpoints use standard HTTP verbs (GET, POST, PUT, DELETE) with appropriate status codes for success and error scenarios [3].

### 2.2 Event-Driven Nature
Every API operation that modifies system state publishes corresponding events to Kafka topics, enabling real-time system transparency and decoupled service communication [3,5]. Events are published across specialized topics including `tms.loads`, `tms.vehicles`, `tms.drivers`, `tms.routes`, and `tms.system.alerts` [5].

### 2.3 Real-Time Capabilities
WebSocket endpoints provide real-time communication for live operational updates, leveraging Kafka event streams to push immediate notifications to connected clients [3,5]. This enables responsive dispatching interfaces and proactive exception handling [2,3].

### 2.4 Data Validation Standards
All API endpoints implement strict data validation using Pydantic V2 models with comprehensive validation rules [3]:
- **UUID Pattern Validation**: All entity identifiers use UUID format with Pydantic V2-compatible validation [3]
- **Google Maps API Compatibility**: Spatial data validates against Google Maps API coordinate ranges [3]
- **Financial Precision**: Monetary values use Decimal types for accurate calculations [3]
- **Enum Standards**: All enum values follow SCREAMING_SNAKE_CASE convention [3]

---

## 3. Authentication & Authorization

### 3.1 Current Status
The current API implementation focuses on core functionality with basic security measures including:
- **Input Validation**: Comprehensive Pydantic model validation for all API requests and responses [3]
- **SQL Injection Prevention**: Parameterized queries used throughout repository layer [3]  
- **CORS Configuration**: Currently disabled for development/POC environment [3]
- **Basic Error Handling**: Standard FastAPI error responses without sensitive data exposure [3]

**Note**: This is a proof-of-concept implementation. Production deployment will require additional security hardening including authentication, authorization, CORS configuration, and comprehensive security monitoring [3].

---

## 4. API Endpoints by Domain

### 4.1 Load Management API

#### 4.1.1 Create Load
- **Purpose**: Create new load entry in the TMS system [3]
- **HTTP Method & Path**: `POST /api/loads` [3]
- **Request Body**:
  ```json
  {
    "load_number": "string (required, unique)",
    "customer_id": "uuid (required)",
    "pickup_location": {
      "latitude": "decimal (required, -90 to 90)",
      "longitude": "decimal (required, -180 to 180)"
    },
    "delivery_location": {
      "latitude": "decimal (required, -90 to 90)", 
      "longitude": "decimal (required, -180 to 180)"
    },
    "pickup_address": "string (required)",
    "delivery_address": "string (required)",
    "pickup_date": "datetime (required, ISO 8601)",
    "delivery_date": "datetime (required, ISO 8601)",
    "weight": "decimal (optional, kg)",
    "volume": "decimal (optional, m³)",
    "commodity_type": "string (optional)",
    "special_requirements": "array[string] (optional)",
    "rate": "decimal (optional, currency precision)"
  }
  ```
- **Response Body** (Success 201):
  ```json
  {
    "id": "uuid",
    "load_number": "string",
    "status": "CREATED",
    "created_at": "datetime",
    "pickup_location": "geography_point",
    "delivery_location": "geography_point",
    // ... all load details
  }
  ```
- **Database Interactions**: Stores core load details in PostgreSQL for ACID compliance and spatial data using PostGIS GEOGRAPHY columns [3,4,6]. Load creation leverages PostgreSQL's transactional guarantees for data integrity [4,6].
- **Events Published**: `LOAD_CREATED` event published to `tms.loads` Kafka topic [3,5]

#### 4.1.2 Assign Load
- **Purpose**: Assign load to specific driver and vehicle [3]
- **HTTP Method & Path**: `PUT /api/loads/{load_id}/assign` [3]
- **Request Body**:
  ```json
  {
    "driver_id": "uuid (required)",
    "vehicle_id": "uuid (required)"
  }
  ```
- **Response Body** (Success 200): Complete load details with assignment information [3]
- **Database Interactions**: Updates PostgreSQL loads table with foreign key references to drivers and vehicles tables, maintaining referential integrity [3,4]
- **Events Published**: `LOAD_ASSIGNED` event published to `tms.loads` topic [3,5]

#### 4.1.3 Update Load Status
- **Purpose**: Update load status throughout lifecycle [3]
- **HTTP Method & Path**: `PUT /api/loads/{load_id}/status` [3]
- **Request Body**:
  ```json
  {
    "status": "enum (CREATED|ASSIGNED|PICKED_UP|IN_TRANSIT|DELIVERED|CANCELLED|DELAYED)",
    "notes": "string (optional)"
  }
  ```
- **Database Interactions**: Updates PostgreSQL loads table status enum field [3,4]
- **Events Published**: Status-specific events (`LOAD_PICKED_UP`, `LOAD_IN_TRANSIT`, `LOAD_DELIVERED`, etc.) to `tms.loads` topic [5]

#### 4.1.4 Get All Loads
- **Purpose**: Retrieve paginated list of all loads with optional filtering [3]
- **HTTP Method & Path**: `GET /api/loads` [3]
- **Query Parameters**:
  - `limit`: Maximum number of results (default: 50)
  - `offset`: Number of results to skip (default: 0)
  - `status`: Filter by load status
  - `customer_id`: Customer UUID filter
- **Response Body** (Success 200): Paginated list of loads with metadata
- **Database Interactions**: Queries PostgreSQL loads table with optional filtering and pagination [3,4]
- **Events Published**: None (read-only operation) [3]

#### 4.1.5 Search Loads
- **Purpose**: Search and filter loads with complex criteria [3]
- **HTTP Method & Path**: `GET /api/loads/search` [3]
- **Query Parameters**: 
  - `status`: Load status filter
  - `customer_id`: Customer UUID filter
  - `date_range`: Pickup/delivery date range
  - `location_radius`: Geographic proximity search
- **Database Interactions**: Executes complex PostgreSQL queries with spatial operations using PostGIS for location-based searches [3,4,6]
- **Events Published**: None (read-only operation) [3]

#### 4.1.6 Get Unassigned Loads
- **Purpose**: Retrieve all loads that have not been assigned to drivers/vehicles [3]
- **HTTP Method & Path**: `GET /api/loads/unassigned` [3]
- **Response Body** (Success 200): List of unassigned loads
- **Database Interactions**: Queries PostgreSQL loads table for loads with NULL driver_id and vehicle_id [3,4]
- **Events Published**: None (read-only operation) [3]

#### 4.1.7 Get Loads by Status
- **Purpose**: Retrieve loads filtered by specific status [3]
- **HTTP Method & Path**: `GET /api/loads/status/{status}` [3]
- **Path Parameters**: `status` - Load status enum value
- **Response Body** (Success 200): List of loads with specified status
- **Database Interactions**: Queries PostgreSQL loads table with status filter [3,4]
- **Events Published**: None (read-only operation) [3]

#### 4.1.8 Get Load by ID
- **Purpose**: Retrieve detailed information for a specific load [3]
- **HTTP Method & Path**: `GET /api/loads/{load_id}` [3]
- **Path Parameters**: `load_id` - UUID of the load
- **Response Body** (Success 200): Complete load details
- **Database Interactions**: Queries PostgreSQL loads table by primary key [3,4]
- **Events Published**: None (read-only operation) [3]

#### 4.1.9 Optimize Load Route
- **Purpose**: Generate optimized route for load using Google Maps API and Neo4j graph algorithms [3,7,10]
- **HTTP Method & Path**: `POST /api/loads/{load_id}/optimize-route` [3]
- **Request Body**:
  ```json
  {
    "vehicle_id": "uuid (required)",
    "driver_id": "uuid (required)",
    "optimization_preferences": {
      "priority": "enum (DISTANCE|TIME|FUEL_EFFICIENCY)",
      "avoid_tolls": "boolean (optional)",
      "avoid_highways": "boolean (optional)"
    }
  }
  ```
- **Response Body** (Success 200):
  ```json
  {
    "route_id": "uuid",
    "optimized_route": {
      "total_distance_miles": "decimal",
      "estimated_duration_minutes": "integer",
      "route_geometry": "string (WKT LINESTRING)",
      "optimization_score": "integer (0-100)"
    },
    "waypoints": "array[coordinates]",
    "traffic_considerations": "object"
  }
  ```
- **Database Interactions**: 
  - **Neo4j**: Current role involves basic route optimization using graph algorithms for pathfinding [3,7,10]. Stores route networks and optimization graphs for traversal queries [4,6,7]
  - **PostgreSQL**: Stores route geometry as PostGIS LINESTRING for street-level precision [3,4,6]
  - **Planned Neo4j Enhancement**: Advanced ML-driven optimization with real-time traffic integration and complex route relationship modeling [7,11]
- **Events Published**: `ROUTE_OPTIMIZED` event published to `tms.routes` Kafka topic [3,5]

#### 4.1.10 Advanced Optimize Load Route
- **Purpose**: Calculate optimized route using Neo4j graph relationships for multi-constraint optimization
- **HTTP Method & Path**: `POST /api/routes/advanced-optimize-load`
- **Request Body**:
  ```json
  {
    "load_id": "string (UUID)",
    "max_driver_distance_miles": 50.0,
    "max_route_duration_hours": 11.0,
    "min_driver_rating": 3.0,
    "min_carrier_performance": 70.0,
    "consider_traffic": true
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "selected_driver_id": "string (UUID)",
    "selected_vehicle_id": "string (UUID)", 
    "optimization_score": 85.2,
    "optimization_method": "graph_based_multi_constraint",
    "alternatives_considered": 12,
    "distance_miles": 247.8,
    "duration_minutes": 285,
    "route_geometry": "LINESTRING(...)",
    "cost_estimate": 1247.50,
    "timeline_feasible": true,
    "candidate_details": {
      "driver_proximity_score": 92.5,
      "vehicle_suitability_score": 88.0,
      "carrier_performance_score": 78.5,
      "cost_efficiency_score": 85.0,
      "timeline_feasibility_score": 95.0
    }
  }
  ```
- **Multi-Constraint Optimization Features**:
  - **Driver Proximity**: Uses Neo4j spatial queries to find drivers within specified distance of pickup location
  - **Vehicle Suitability**: Matches vehicle capacity, type, and equipment requirements with load specifications
  - **Carrier Performance**: Leverages historical performance metrics stored in graph relationships
  - **Cost Efficiency**: Considers fuel costs, driver rates, and route efficiency
  - **Timeline Feasibility**: Validates Hours-of-Service compliance and delivery time windows
  - **Traffic Awareness**: Integrates real-time traffic data for accurate duration estimates
- **Database Operations**:
  - **Neo4j**: Graph traversal queries for candidate discovery, relationship scoring
  - **PostgreSQL**: Load details, driver/vehicle availability, route persistence
  - **Google Maps API**: Traffic-aware route calculation and geometry generation
- **Event Publishing**: Publishes `ADVANCED_ROUTE_OPTIMIZED` event to Kafka for downstream processing

### 4.2 Vehicle Management API

#### 4.2.1 Get All Vehicles
- **Purpose**: Retrieve paginated list of all vehicles with optional filtering [3]
- **HTTP Method & Path**: `GET /api/vehicles` [3]
- **Query Parameters**:
  - `limit`: Maximum number of results (default: 50)
  - `offset`: Number of results to skip (default: 0)
  - `status`: Filter by vehicle status
  - `vehicle_type`: Filter by vehicle type
- **Response Body** (Success 200): Paginated list of vehicles with metadata
- **Database Interactions**: Queries PostgreSQL vehicles table with optional filtering and pagination [3,4]
- **Events Published**: None (read-only operation) [3]

#### 4.2.2 Get Vehicle Tracking Data
- **Purpose**: Retrieve historical tracking data for a specific vehicle [3]
- **HTTP Method & Path**: `GET /api/vehicles/{vehicle_id}/tracking` [3]
- **Path Parameters**: `vehicle_id` - UUID of the vehicle
- **Query Parameters**:
  - `start_date`: Start date for tracking data range
  - `end_date`: End date for tracking data range
  - `limit`: Maximum number of tracking records
- **Response Body** (Success 200): List of vehicle tracking records with locations and timestamps
- **Database Interactions**: Queries TimescaleDB vehicle_tracking hypertable for time-series location data [3,4,6]
- **Events Published**: None (read-only operation) [3]

#### 4.2.3 Create Vehicle
- **Purpose**: Register new vehicle in the TMS system [3]
- **HTTP Method & Path**: `POST /api/vehicles` [3]
- **Request Body**:
  ```json
  {
    "vehicle_number": "string (required, unique)",
    "make": "string (required)",
    "model": "string (required)",
    "year": "integer (required)",
    "vin": "string (required, unique, 17 chars)",
    "license_plate": "string (required, unique)",
    "vehicle_type": "enum (TRUCK|TRAILER|VAN|FLATBED)",
    "capacity_weight": "decimal (required, kg)",
    "capacity_volume": "decimal (required, m³)",
    "fuel_type": "enum (DIESEL|GASOLINE|ELECTRIC|HYBRID)",
    "current_location": {
      "latitude": "decimal (required)",
      "longitude": "decimal (required)"
    }
  }
  ```
- **Response Body** (Success 201): Complete vehicle details with system-generated UUID [3]
- **Database Interactions**: Stores vehicle data in PostgreSQL vehicles table with PostGIS GEOGRAPHY for location tracking [3,4,6]
- **Events Published**: `VEHICLE_CREATED` event published to `tms.vehicles` topic [3,5]

#### 4.2.4 Update Vehicle Location
- **Purpose**: Update real-time vehicle GPS location for tracking [3]
- **HTTP Method & Path**: `PUT /api/vehicles/{vehicle_id}/location` [3]
- **Request Body**:
  ```json
  {
    "latitude": "decimal (required, -90 to 90)",
    "longitude": "decimal (required, -180 to 180)",
    "timestamp": "datetime (required, ISO 8601)",
    "speed": "decimal (optional, km/h)",
    "heading": "decimal (optional, degrees)"
  }
  ```
- **Database Interactions**: 
  - **PostgreSQL**: Updates current location in vehicles table using PostGIS GEOGRAPHY type [3,4,6]
  - **TimescaleDB**: Stores historical location data in vehicle_tracking hypertable for time-series analysis [3,4,6]
- **Events Published**: `VEHICLE_LOCATION_UPDATED` event published to `tms.vehicles.tracking` topic [3,5]

#### 4.2.5 Update Vehicle Status
- **Purpose**: Change vehicle operational status [3]
- **HTTP Method & Path**: `PUT /api/vehicles/{vehicle_id}/status` [3]
- **Request Body**:
  ```json
  {
    "status": "enum (AVAILABLE|ASSIGNED|IN_TRANSIT|MAINTENANCE|OUT_OF_SERVICE)",
    "notes": "string (optional)"
  }
  ```
- **Database Interactions**: Updates PostgreSQL vehicles table status enum field [3,4]
- **Events Published**: `VEHICLE_STATUS_CHANGED` event published to `tms.vehicles` topic [3,5]

### 4.3 Route Management API

#### 4.3.1 Get All Routes
- **Purpose**: Retrieve paginated list of all routes with optional filtering [3]
- **HTTP Method & Path**: `GET /api/routes` [3]
- **Query Parameters**:
  - `limit`: Maximum number of results (default: 50)
  - `offset`: Number of results to skip (default: 0)
  - `status`: Filter by route status
  - `load_id`: Filter by associated load
- **Response Body** (Success 200): Paginated list of routes with metadata
- **Database Interactions**: Queries PostgreSQL routes table with optional filtering and pagination [3,4]
- **Events Published**: None (read-only operation) [3]

#### 4.3.2 Get Active Routes
- **Purpose**: Retrieve all currently active routes [3]
- **HTTP Method & Path**: `GET /api/routes/active` [3]
- **Response Body** (Success 200): List of active routes with current status
- **Database Interactions**: Queries PostgreSQL routes table for routes with active status [3,4]
- **Events Published**: None (read-only operation) [3]

#### 4.3.3 Get Route Performance Metrics
- **Purpose**: Retrieve performance analytics for routes [3]
- **HTTP Method & Path**: `GET /api/routes/performance` [3]
- **Query Parameters**:
  - `start_date`: Start date for performance data range
  - `end_date`: End date for performance data range
  - `route_id`: Specific route ID filter
- **Response Body** (Success 200): Route performance metrics and analytics
- **Database Interactions**: Queries TimescaleDB for route performance aggregations [3,4,6]
- **Events Published**: None (read-only operation) [3]

#### 4.3.4 Get Route by ID
- **Purpose**: Retrieve detailed information for a specific route [3]
- **HTTP Method & Path**: `GET /api/routes/{route_id}` [3]
- **Path Parameters**: `route_id` - UUID of the route
- **Response Body** (Success 200): Complete route details including geometry and waypoints
- **Database Interactions**: Queries PostgreSQL routes table by primary key [3,4]
- **Events Published**: None (read-only operation) [3]

### 4.4 Driver Management API

#### 4.4.1 Get All Drivers
- **Purpose**: Retrieve paginated list of drivers with optional filtering [3]
- **HTTP Method & Path**: `GET /api/drivers` [3]
- **Query Parameters**:
  - `limit`: Maximum number of results (default: 50)
  - `offset`: Number of results to skip (default: 0)
  - `status`: Filter by driver status (AVAILABLE, DRIVING, ON_DUTY, OFF_DUTY, SLEEPER, ON_BREAK)
  - `available_only`: Boolean to show only available drivers
- **Response Body** (Success 200):
  ```json
  {
    "drivers": [
      {
        "id": "uuid",
        "carrier_id": "uuid",
        "driver_number": "string",
        "first_name": "string",
        "last_name": "string",
        "email": "string",
        "phone": "string",
        "license_number": "string",
        "license_class": "string",
        "license_expiry": "date",
        "date_of_birth": "date",
        "hire_date": "date",
        "current_location": "geography",
        "current_address": "string",
        "status": "enum",
        "hours_of_service_remaining": "decimal",
        "last_hos_reset": "timestamp",
        "created_at": "timestamp",
        "updated_at": "timestamp"
      }
    ],
    "total": "integer",
    "limit": "integer",
    "offset": "integer",
    "has_more": "boolean"
  }
  ```
- **Database Interactions**: Queries PostgreSQL drivers table with optional filtering and pagination [3,4]
- **Performance**: Optimized with proper indexing on status and driver_number columns [3]

#### 4.4.2 Get Driver by ID
- **Purpose**: Retrieve detailed information for a specific driver [3]
- **HTTP Method & Path**: `GET /api/drivers/{driver_id}` [3]
- **Path Parameters**: `driver_id` - UUID of the driver
- **Response Body** (Success 200): Complete driver details including current status and location
- **Database Interactions**: Queries PostgreSQL drivers table by primary key [3,4]
- **Events Published**: None (read-only operation) [3]

#### 4.4.3 Create Driver
- **Purpose**: Register new driver in the TMS system [3]
- **HTTP Method & Path**: `POST /api/drivers` [3]
- **Request Body**:
  ```json
  {
    "driver_number": "string (required, unique, max 50 chars)",
    "first_name": "string (required, max 100 chars)",
    "last_name": "string (required, max 100 chars)",
    "phone": "string (required, max 20 chars)",
    "email": "string (required, email format, max 255 chars)",
    "license_number": "string (required, unique, max 50 chars)",
    "license_class": "string (required, max 10 chars)",
    "license_expiry": "date (required)",
    "date_of_birth": "date (required)",
    "hire_date": "date (required)",
    "carrier_id": "uuid (optional)",
    "current_location": {
      "latitude": "decimal (required)",
      "longitude": "decimal (required)"
    },
    "current_address": "string (optional)",
    "status": "enum (optional, default: AVAILABLE)"
  }
  ```
- **Response Body** (Success 201): Complete driver details with system-generated UUID [3]
- **Validation**: Comprehensive field validation using Pydantic with business rule enforcement [3]
- **Database Interactions**: Stores driver data in PostgreSQL drivers table with PostGIS GEOGRAPHY for location tracking [3,4,6]
- **Events Published**: `DRIVER_CREATED` event published to `tms.drivers` topic [3,5]

#### 4.4.4 Update Driver Status
- **Purpose**: Update driver duty status for Hours of Service compliance [3]
- **HTTP Method & Path**: `PUT /api/drivers/{driver_id}/status` [3]
- **Request Body**:
  ```json
  {
    "status": "enum (AVAILABLE|DRIVING|ON_DUTY|OFF_DUTY|SLEEPER_BERTH)",
    "location": {
      "latitude": "decimal (required)",
      "longitude": "decimal (required)"
    },
    "notes": "string (optional)"
  }
  ```
- **Database Interactions**: Updates PostgreSQL drivers table status and location fields [3,4]
- **Events Published**: `DRIVER_STATUS_CHANGED` event published to `tms.drivers` topic [3,5]

#### 4.4.5 Track Driver Hours of Service
- **Purpose**: Monitor and enforce HOS regulations compliance [3]
- **HTTP Method & Path**: `GET /api/drivers/{driver_id}/hos` [3]
- **Response Body**:
  ```json
  {
    "driver_id": "uuid",
    "current_status": "enum",
    "hours_driven_today": "decimal",
    "hours_on_duty_today": "decimal",
    "required_break_in_minutes": "integer",
    "violation_alerts": "array[object]"
  }
  ```
- **Database Interactions**: Queries TimescaleDB driver_activity hypertable for time-series HOS data analysis [3,4,6]
- **Events Published**: `DRIVER_HOS_VIOLATION` event if violations detected, published to `tms.drivers` topic [3,5]

### 4.5 Event Management API

#### 4.5.1 Get Recent Events
- **Purpose**: Retrieve recent events for operational visibility [3,5]
- **HTTP Method & Path**: `GET /api/events/recent` [3]
- **Query Parameters**:
  - `limit`: Maximum number of events to return (default: 100)
  - `event_type`: Filter by specific event types
  - `entity_type`: Filter by entity (LOAD, VEHICLE, DRIVER, ROUTE)
- **Response Body** (Success 200): List of recent events with timestamps and details
- **Database Interactions**: Queries TimescaleDB load_events hypertable for recent time-series event data [3,4,6]
- **Events Published**: None (read-only operation) [3]

#### 4.5.2 Get Event Topics
- **Purpose**: Retrieve list of available Kafka event topics [3,5]
- **HTTP Method & Path**: `GET /api/events/topics` [3]
- **Response Body** (Success 200): List of available Kafka topics with metadata
- **Database Interactions**: Queries Kafka cluster metadata for topic information [3,5]
- **Events Published**: None (read-only operation) [3]

#### 4.5.3 Filter Events
- **Purpose**: Advanced event filtering with complex criteria [3,5]
- **HTTP Method & Path**: `GET /api/events/filter` [3]
- **Query Parameters**:
  - `event_type`: Filter by specific event types
  - `entity_type`: Filter by entity (LOAD, VEHICLE, DRIVER, ROUTE)
  - `start_date`: Start of date range
  - `end_date`: End of date range
  - `limit`: Maximum events to return
- **Database Interactions**: Queries TimescaleDB load_events hypertable for time-series event data [3,4,6]
- **Events Published**: None (read-only operation) [3]

#### 4.5.4 Publish Custom Event
- **Purpose**: Allow external systems to publish events into TMS event stream [3,5]
- **HTTP Method & Path**: `POST /api/events` [3]
- **Request Body**:
  ```json
  {
    "event_type": "string (required)",
    "entity_type": "enum (LOAD|VEHICLE|DRIVER|ROUTE|SYSTEM)",
    "entity_id": "uuid (required)",
    "event_data": "object (required)",
    "severity": "enum (LOW|MEDIUM|HIGH|CRITICAL)"
  }
  ```
- **Database Interactions**: Stores event in TimescaleDB load_events hypertable [3,4,6]
- **Events Published**: Custom event published to appropriate Kafka topic based on entity_type [3,5]

### 4.6 Analytics API

#### 4.6.1 Dashboard Metrics
- **Purpose**: Provide key performance indicators for TMS dashboard [3,9]
- **HTTP Method & Path**: `GET /api/analytics/dashboard` [3]
- **Response Body**:
  ```json
  {
    "active_loads": "integer",
    "available_vehicles": "integer",
    "active_drivers": "integer",
    "completion_rate": "decimal (percentage)",
    "average_delivery_time": "decimal (hours)",
    "total_revenue_today": "decimal",
    "alerts_count": "integer"
  }
  ```
- **Database Interactions**: Executes complex aggregation queries across PostgreSQL and TimescaleDB for real-time metrics [3,4,6,9]
- **Events Published**: None (read-only operation) [3]

#### 4.6.2 Loads Trend Analytics
- **Purpose**: Retrieve load volume trends over time [3,9]
- **HTTP Method & Path**: `GET /api/analytics/loads/trend` [3]
- **Query Parameters**:
  - `start_date`: Start date for trend analysis
  - `end_date`: End date for trend analysis
  - `granularity`: Time granularity (daily, weekly, monthly)
- **Response Body** (Success 200): Time-series data showing load volume trends
- **Database Interactions**: Queries TimescaleDB continuous aggregations for load trend analysis [4,6,9]
- **Events Published**: None (read-only operation) [3]

#### 4.6.3 Carrier Performance Analytics
- **Purpose**: Detailed carrier performance analysis for operational optimization [3,9]
- **HTTP Method & Path**: `GET /api/analytics/performance/carriers` [3]
- **Query Parameters**:
  - `start_date`: Start date for performance analysis
  - `end_date`: End date for performance analysis
  - `carrier_id`: Specific carrier ID filter
- **Response Body** (Success 200): Carrier performance metrics including on-time delivery, efficiency scores
- **Database Interactions**: Queries TimescaleDB continuous aggregations for carrier performance metrics analysis [4,6,9]
- **Events Published**: None (read-only operation) [3]

### 4.7 Health Management API

#### 4.7.1 System Health Check
- **Purpose**: Retrieve system health status and service availability [3]
- **HTTP Method & Path**: `GET /health` [3]
- **Response Body** (Success 200):
  ```json
  {
    "status": "healthy",
    "timestamp": "datetime (ISO 8601)",
    "services": {
      "database": "healthy",
      "kafka": "healthy",
      "neo4j": "healthy",
      "timescale": "healthy"
    },
    "version": "string",
    "uptime": "duration"
  }
  ```
- **Database Interactions**: Performs basic connectivity checks to all database services [3,4]
- **Events Published**: None (read-only operation) [3]

---

## 5. Real-time WebSocket API

### 5.1 WebSocket Endpoint
- **Purpose**: Provide real-time operational updates for responsive dispatching interfaces [2,3,5]
- **WebSocket URL**: `ws://localhost:8000/ws` [3]
- **Connection Protocol**: Standard WebSocket protocol with JSON message format [3]

### 5.2 Real-time Event Broadcasting
The WebSocket endpoint leverages Kafka event streams to push immediate notifications to connected clients, enabling real-time system transparency [3,5]. All API operations that modify system state trigger corresponding WebSocket messages to subscribed clients [3,5].

### 5.3 Message Format
```json
{
  "event_type": "string (LOAD_CREATED, VEHICLE_LOCATION_UPDATED, etc.)",
  "entity_type": "enum (LOAD|VEHICLE|DRIVER|ROUTE)",
  "entity_id": "uuid",
  "timestamp": "datetime (ISO 8601)",
  "data": "object (entity-specific payload)"
}
```

### 5.4 Connection Stability
Implemented solutions for WebSocket connection stability include automatic reconnection logic, heartbeat mechanisms, and graceful error handling to ensure reliable real-time communication [3].

### 5.5 Scalability Support
The system supports up to 10,000+ concurrent WebSocket connections for large-scale dispatching operations [1,3].

---

## 6. API Data Models & Compatibility

### 6.1 Pydantic V2 Compliance
All API endpoints implement comprehensive data validation using Pydantic V2 models with strict validation rules [3]. This ensures data integrity, type safety, and consistent API behavior across all operations [3].

### 6.2 Google Maps API Compatibility
Spatial data validation ensures compatibility with Google Maps API coordinate standards [3]:
- **Latitude Range**: -90.0 to 90.0 degrees
- **Longitude Range**: -180.0 to 180.0 degrees
- **Coordinate Precision**: Up to 6 decimal places for meter-level accuracy
- **Spatial Reference System**: WGS84 (EPSG:4326) for global compatibility

### 6.3 UUID Pattern Validation
All entity identifiers use UUID format with Pydantic V2-compatible validation patterns [3]. This ensures globally unique identifiers and prevents ID collision across distributed systems [3].

### 6.4 Financial Precision
Monetary values use Decimal types for accurate financial calculations, preventing floating-point precision errors in rate calculations and revenue reporting [3].

### 6.5 Enum Standards
All enum values follow SCREAMING_SNAKE_CASE convention for consistency between Python code, database schemas, and API interfaces [3]:
- **LoadStatus**: CREATED, ASSIGNED, PICKED_UP, IN_TRANSIT, DELIVERED, CANCELLED, DELAYED
- **VehicleStatus**: AVAILABLE, ASSIGNED, IN_TRANSIT, MAINTENANCE, OUT_OF_SERVICE
- **DriverStatus**: AVAILABLE, DRIVING, ON_DUTY, OFF_DUTY, SLEEPER_BERTH

---

## 7. API and Event-Driven Architecture Integration

### 7.1 Comprehensive Event Flow
Every API operation that modifies system state follows a consistent event-driven pattern [3,5]:
1. **API Request Validation**: Pydantic models validate incoming data
2. **Database Transaction**: ACID-compliant database operation
3. **Event Publishing**: Kafka event published to appropriate topic
4. **WebSocket Broadcast**: Real-time notification to connected clients
5. **Event Processing**: Downstream services consume and react to events

### 7.2 Event-Driven Database Synchronization
The polyglot persistence architecture maintains consistency through event-driven synchronization [4,6]:
- **PostgreSQL**: Primary operational data with immediate consistency
- **TimescaleDB**: Time-series data populated via Kafka event streams
- **Neo4j**: Graph relationships updated through event-driven processes

### 7.3 Kafka Topic Organization
Events are organized across specialized Kafka topics for optimal processing [5]:
- `tms.loads`: Load lifecycle events (LOAD_CREATED, LOAD_ASSIGNED, etc.)
- `tms.vehicles`: Vehicle operational events (VEHICLE_STATUS_CHANGED, etc.)
- `tms.vehicles.tracking`: High-frequency location updates
- `tms.drivers`: Driver management and HOS events
- `tms.routes`: Route optimization and deviation events
- `tms.system.alerts`: System-wide alerts and notifications

### 7.4 Event Processing Patterns
Implemented event processing patterns include [5,12]:
- **Event Sourcing**: Immutable event history for audit trails
- **CQRS (Command Query Responsibility Segregation)**: Separate read/write models
- **Event Streaming**: Real-time event processing with Kafka and Flink
- **Eventual Consistency**: Distributed system consistency through event propagation

---

## 8. Performance & Scalability Requirements

### 8.1 API Response Time Targets
- **Standard Operations**: < 200ms for 95% of requests [1,3]
- **Complex Queries**: < 500ms for spatial and analytics operations [3]
- **Route Optimization**: < 2 seconds for real-time optimization [2,3]

### 8.2 Event Processing Performance
- **Event Processing Latency**: < 100ms from API operation to Kafka publication [1,3]
- **WebSocket Notification**: < 50ms from event to client notification [3]
- **Throughput**: Support 10,000+ events per second processing [1]

### 8.3 Concurrent User Support
- **API Concurrent Requests**: Support 100+ simultaneous dispatchers [1]
- **WebSocket Connections**: Up to 10,000+ concurrent connections [1,3]
- **Database Connections**: Optimized connection pooling for high concurrency [3]

### 8.4 Data Volume Capabilities
- **Historical Data**: Process billions of historical records [1]
- **Real-time Tracking**: Handle 50,000+ daily location updates [5]
- **Event Storage**: Scalable time-series event storage in TimescaleDB [4,6]

---

## 9. Use Cases Enabled by the API

### 9.1 Real-Time Load Monitoring
- **API Endpoints**: Load Management API, Event Management API, WebSocket API [3]
- **Business Value**: Proactive issue resolution and customer communication [2]
- **Events**: LOAD_CREATED, LOAD_ASSIGNED, LOAD_IN_TRANSIT, LOAD_DELIVERED [5]
- **Implementation Status**: Fully implemented with event handlers and producers

### 9.2 Vehicle Exception Handling
- **API Endpoints**: Vehicle Management API, Analytics API, Event Management API [3]
- **Business Value**: Preventive maintenance and operational efficiency [2]
- **Events**: VEHICLE_BREAKDOWN, VEHICLE_MAINTENANCE_DUE, VEHICLE_STATUS_CHANGED [5]
- **Implementation Status**: Event schemas defined, operational logic not yet implemented

### 9.3 Route Optimization Management
- **API Endpoints**: Load Route Optimization API, Analytics API [3,7,10]
- **Business Value**: Cost reduction through optimized routing [2]
- **Events**: ROUTE_OPTIMIZED, ROUTE_DEVIATION, TRAFFIC_ALERT [5]
- **Implementation Status**: ROUTE_OPTIMIZED events implemented in optimization service

### 9.4 Driver Hours of Service Compliance
- **API Endpoints**: Driver Management API, Event Management API [3]
- **Business Value**: Regulatory compliance and driver safety [2]
- **Events**: DRIVER_STATUS_CHANGED, DRIVER_HOS_VIOLATION, DRIVER_BREAK_STARTED [5]
- **Implementation Status**: Event schemas and Kafka topics configured

### 9.5 Operational Analytics and Reporting
- **API Endpoints**: Analytics API, Event Management API [3,9]
- **Business Value**: Data-driven decision making and performance optimization [2]
- **Database Integration**: Basic PostgreSQL and TimescaleDB queries [4,6,9]
- **Implementation Status**: Basic analytics implemented, advanced continuous aggregations not yet configured

---

## 10. Security Considerations (API Specific)

### 10.1 Current Security Features
Implemented security measures include [3]:
- **Input Validation**: Comprehensive Pydantic model validation for all API requests and responses [3]
- **SQL Injection Prevention**: Parameterized queries used throughout repository layer [3]  
- **CORS Configuration**: Currently disabled for development/POC environment [3]
- **Basic Error Handling**: Standard FastAPI error responses without sensitive data exposure [3]

**Note**: This is a proof-of-concept implementation. Production deployment will require additional security hardening including authentication, authorization, CORS configuration, and comprehensive security monitoring [3].

---

## Source Document References

[1] PRD-Overview.md  
[2] PRD-Dispatching-Interface.md  
[3] SPEC-Backend-System.md  
[4] SPEC-Database-Schema.md  
[5] SPEC-Events-Schema.md  
[6] SPEC-Polyglot-Persistence.md  
[7] SPEC-Object-Relationships.md  
[8] SPEC-Machine-Learning.md  
[9] SPEC-Real-time-Analytics.md  
[10] SPEC-Route-Optimization-Setup.md  
[11] SPEC-Stream-Processing.md  
[12] Additional inference from event-driven architecture patterns
