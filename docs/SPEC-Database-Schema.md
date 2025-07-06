# Technical Specification (SPEC)
## TMS Database Schema

**Version:** 1.0  
**Date:** July 3, 2025  
**Authors:** Development Team  
**Tags:** #technical-spec #TMS-Data #TMS-Core #status/implemented #priority/high #polyglot-persistence
**Related:** [[PRD-Overview]] | [[SPEC-Backend-System]] | [[SPEC-Polyglot-Persistence]] | [[SPEC-Object-Relationships]]
**Dependencies:** [[PRD-Overview]]
**Used By:** [[SPEC-Backend-System]], [[SPEC-Real-time-Analytics]], [[SPEC-Events-Schema]]

---

## 1. Executive Summary

### 1.1 Overview
The TMS Database Schema defines the comprehensive data model for the Transportation Management System, spanning multiple specialized databases in a polyglot persistence architecture. This schema supports all operational, analytical, and relational data requirements while ensuring optimal performance, scalability, and data integrity.

### 1.2 Scope
This document covers the complete database schema across three primary data stores:
- **PostgreSQL with PostGIS**: Operational data and spatial queries
- **Neo4j**: Graph relationships and network analysis  
- **TimescaleDB**: Time-series data and analytics

---

## 2. Database Architecture

### 2.1 Polyglot Persistence Strategy
The system employs multiple specialized databases, each optimized for specific data patterns and query requirements:

#### 2.1.1 PostgreSQL with PostGIS
- **Primary Role**: OLTP operations, spatial data management
- **Data Types**: Loads, vehicles, drivers, routes, locations
- **Key Features**: ACID compliance, spatial indexing, complex joins

#### 2.1.2 Neo4j Graph Database  
- **Primary Role**: Relationship modeling, route optimization
- **Data Types**: Driver-vehicle relationships, route networks, optimization graphs
- **Key Features**: Graph traversal, relationship queries, pathfinding algorithms

#### 2.1.3 TimescaleDB
- **Primary Role**: Time-series analytics, performance metrics
- **Data Types**: Event history, performance data, analytics aggregations
- **Key Features**: Time-based partitioning, continuous aggregations, retention policies

---

## 3. PostgreSQL Schema (Operational Data)

### 3.1 Core Entity Tables

#### 3.1.1 Loads Table
```sql
CREATE TABLE loads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    load_number VARCHAR(50) UNIQUE NOT NULL,
    customer_id UUID NOT NULL,
    pickup_location GEOGRAPHY(POINT, 4326) NOT NULL,
    delivery_location GEOGRAPHY(POINT, 4326) NOT NULL,
    pickup_address TEXT NOT NULL,
    delivery_address TEXT NOT NULL,
    pickup_date TIMESTAMP WITH TIME ZONE NOT NULL,
    delivery_date TIMESTAMP WITH TIME ZONE NOT NULL,
    weight DECIMAL(10,2),
    volume DECIMAL(10,2),
    commodity_type VARCHAR(100),
    special_requirements TEXT[],
    status load_status_enum NOT NULL DEFAULT 'CREATED',
    assigned_driver_id UUID,
    assigned_vehicle_id UUID,
    rate DECIMAL(10,2),
    distance_miles DECIMAL(8,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_loads_driver FOREIGN KEY (assigned_driver_id) REFERENCES drivers(id),
    CONSTRAINT fk_loads_vehicle FOREIGN KEY (assigned_vehicle_id) REFERENCES vehicles(id)
    -- assigned_driver_id must reference a valid UUID in the drivers table
    -- null is allowed for unassigned loads
);

CREATE TYPE load_status_enum AS ENUM (
    'CREATED', 'ASSIGNED', 'PICKED_UP', 'IN_TRANSIT', 
    'DELIVERED', 'CANCELLED', 'DELAYED'
);
```

#### 3.1.2 Vehicles Table
```sql
CREATE TABLE vehicles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_number VARCHAR(50) UNIQUE NOT NULL,
    make VARCHAR(50) NOT NULL,
    model VARCHAR(50) NOT NULL,
    year INTEGER NOT NULL,
    vin VARCHAR(17) UNIQUE NOT NULL,
    license_plate VARCHAR(20) UNIQUE NOT NULL,
    vehicle_type vehicle_type_enum NOT NULL,
    capacity_weight DECIMAL(10,2) NOT NULL,
    capacity_volume DECIMAL(10,2) NOT NULL,
    fuel_type fuel_type_enum NOT NULL,
    current_location GEOGRAPHY(POINT, 4326),
    current_address TEXT,
    status vehicle_status_enum NOT NULL DEFAULT 'AVAILABLE',
    last_maintenance_date DATE,
    next_maintenance_due DATE,
    mileage INTEGER,
    fuel_level DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TYPE vehicle_type_enum AS ENUM ('TRUCK', 'TRAILER', 'VAN', 'FLATBED', 'REFRIGERATED');
CREATE TYPE fuel_type_enum AS ENUM ('DIESEL', 'GASOLINE', 'ELECTRIC', 'HYBRID');
CREATE TYPE vehicle_status_enum AS ENUM ('AVAILABLE', 'ASSIGNED', 'IN_TRANSIT', 'MAINTENANCE', 'OUT_OF_SERVICE');
```

#### 3.1.3 Drivers Table
```sql
CREATE TABLE drivers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    driver_number VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20) NOT NULL,
    license_number VARCHAR(50) UNIQUE NOT NULL,
    license_class VARCHAR(10) NOT NULL,
    license_expiry DATE NOT NULL,
    date_of_birth DATE NOT NULL,
    hire_date DATE NOT NULL,
    current_location GEOGRAPHY(POINT, 4326),
    current_address TEXT,
    status driver_status_enum NOT NULL DEFAULT 'AVAILABLE',
    hours_of_service_remaining DECIMAL(4,2),
    last_hos_reset TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TYPE driver_status_enum AS ENUM ('AVAILABLE', 'ASSIGNED', 'DRIVING', 'OFF_DUTY', 'ON_BREAK', 'SLEEPER');
```

#### 3.1.4 Routes Table
```sql
CREATE TABLE routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    load_id UUID NOT NULL,
    driver_id UUID NOT NULL,
    vehicle_id UUID NOT NULL,
    origin_location GEOGRAPHY(POINT, 4326) NOT NULL,
    destination_location GEOGRAPHY(POINT, 4326) NOT NULL,
    waypoints GEOGRAPHY(POINT, 4326)[],
    route_geometry GEOGRAPHY(LINESTRING, 4326),
    planned_distance_miles DECIMAL(8,2),
    actual_distance_miles DECIMAL(8,2),
    planned_duration_minutes INTEGER,
    actual_duration_minutes INTEGER,
    estimated_arrival TIMESTAMP WITH TIME ZONE,
    actual_arrival TIMESTAMP WITH TIME ZONE,
    status route_status_enum NOT NULL DEFAULT 'PLANNED',
    optimization_score DECIMAL(5,2),
    fuel_estimate DECIMAL(8,2),
    toll_estimate DECIMAL(8,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_routes_load FOREIGN KEY (load_id) REFERENCES loads(id),
    CONSTRAINT fk_routes_driver FOREIGN KEY (driver_id) REFERENCES drivers(id),
    CONSTRAINT fk_routes_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
);

CREATE TYPE route_status_enum AS ENUM ('PLANNED', 'ACTIVE', 'COMPLETED', 'CANCELLED', 'DELAYED');
```

### 3.2 Supporting Tables

#### 3.2.1 Customers Table
```sql
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_code VARCHAR(50) UNIQUE NOT NULL,
    company_name VARCHAR(200) NOT NULL,
    contact_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(20),
    billing_address TEXT NOT NULL,
    credit_limit DECIMAL(12,2),
    payment_terms INTEGER DEFAULT 30,
    status customer_status_enum NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TYPE customer_status_enum AS ENUM ('ACTIVE', 'INACTIVE', 'SUSPENDED', 'PROSPECT');
```

#### 3.2.2 Load Events Table
```sql
CREATE TABLE load_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    load_id UUID NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB NOT NULL,
    location GEOGRAPHY(POINT, 4326),
    address TEXT,
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_load_events_load FOREIGN KEY (load_id) REFERENCES loads(id)
);
```

### 3.3 Indexes and Performance Optimization

#### 3.3.1 Spatial Indexes
```sql
CREATE INDEX idx_loads_pickup_location ON loads USING GIST (pickup_location);
CREATE INDEX idx_loads_delivery_location ON loads USING GIST (delivery_location);
CREATE INDEX idx_vehicles_current_location ON vehicles USING GIST (current_location);
CREATE INDEX idx_drivers_current_location ON drivers USING GIST (current_location);
CREATE INDEX idx_routes_geometry ON routes USING GIST (route_geometry);
```

#### 3.3.2 Performance Indexes
```sql
CREATE INDEX idx_loads_status ON loads (status);
CREATE INDEX idx_loads_pickup_date ON loads (pickup_date);
CREATE INDEX idx_vehicles_status ON vehicles (status);
CREATE INDEX idx_drivers_status ON drivers (status);
CREATE INDEX idx_load_events_load_id ON load_events (load_id);
CREATE INDEX idx_load_events_occurred_at ON load_events (occurred_at);
```

---

## 4. Neo4j Schema (Graph Data)

### 4.1 Graph Purpose and Applications
The Neo4j graph database serves as the relationship and network optimization layer of the TMS, enabling:
- **Route Optimization**: Advanced pathfinding algorithms for efficient route planning
- **Driver-Vehicle Matching**: Intelligent pairing based on proximity, capacity, and compatibility
- **Network Analysis**: Identification of bottlenecks, hub locations, and optimization opportunities
- **Supply Chain Network Visualization**: End-to-end visibility of goods movement across the network

### 4.2 Event-Driven Graph Synchronization

#### 4.2.1 Real-Time Graph Population
The Neo4j graph database is kept synchronized with PostgreSQL operational data through **event-driven synchronization** using Kafka events:

**Synchronization Architecture:**
- **Event Source**: Kafka topics (`tms.loads`, `tms.vehicles`, `tms.drivers`, `tms.routes`)
- **Sync Service**: `GraphSyncService` processes Kafka events and updates Neo4j
- **Integration Point**: Kafka consumer pipeline automatically invokes graph sync for all relevant events
- **Consistency Model**: Eventually consistent - graph updates occur within seconds of operational data changes

**Supported Event Types:**
```yaml
Load Events:
  - LOAD_CREATED: Creates Load node with pickup/delivery locations
  - LOAD_ASSIGNED: Creates ASSIGNED_TO relationship (Driver-Load)
  - LOAD_PICKED_UP: Updates Load status and creates location relationships
  - LOAD_DELIVERED: Updates Load status and delivery timestamp
  - LOAD_CANCELLED: Updates Load status and removes active relationships

Vehicle Events:
  - VEHICLE_LOCATION_UPDATED: Updates Vehicle location and creates VISITED relationships
  - VEHICLE_STATUS_CHANGED: Updates Vehicle availability status

Driver Events:
  - DRIVER_LOCATION_UPDATED: Updates Driver location for proximity queries
  - DRIVER_STATUS_CHANGED: Updates Driver availability status

Route Events:
  - ROUTE_OPTIMIZED: Creates Route node with optimized path geometry
  - ROUTE_STARTED: Creates EXECUTING relationship (Driver-Route)
  - ROUTE_COMPLETED: Updates Route completion status
```

**Graph Update Operations:**
- **Node Creation**: Automatic creation of missing nodes with MERGE operations
- **Relationship Management**: Dynamic creation/removal of relationships based on business events
- **Status Updates**: Real-time status synchronization for availability queries
- **Location Tracking**: Continuous location updates for proximity-based optimization

#### 4.2.2 Data Consistency and Error Handling
- **Idempotent Operations**: All graph updates use MERGE operations to prevent duplicates
- **Error Recovery**: Failed sync operations are logged with retry capability
- **Data Validation**: Event data validated before graph updates
- **Monitoring**: Comprehensive logging of sync operations and errors

### 4.3 Core Node Types

#### 4.3.1 Geographic Network Nodes

```cypher
// Physical Locations
(:Location {
    id: String,
    name: String,
    address: String,
    coordinates: Point,
    location_type: String, // 'CUSTOMER', 'WAREHOUSE', 'HUB', 'FUEL_STATION', 'WEIGH_STATION', 'REST_AREA'
    operating_hours: Map, // {monday: "08:00-17:00", tuesday: "08:00-17:00", ...}
    dock_count: Integer,
    max_vehicle_length: Float,
    weight_restrictions: [String],
    hazmat_allowed: Boolean,
    parking_spaces: Integer,
    services_available: [String], // ['FUEL', 'MAINTENANCE', 'FOOD', 'SHOWER']
    contact_info: Map,
    timezone: String,
    elevation: Float,
    weather_zone: String
})

// Route Network Nodes (for pathfinding optimization)
(:RouteNode {
    id: String,
    coordinates: Point,
    node_type: String, // 'INTERSECTION', 'HIGHWAY_ENTRY', 'EXIT_RAMP', 'TOLL_BOOTH', 'BRIDGE', 'TUNNEL'
    traffic_weight_base: Float,
    restrictions: [String], // ['NO_TRUCKS', 'HAZMAT_PROHIBITED', 'WEIGHT_LIMIT_40000']
    speed_limit: Integer,
    elevation: Float,
    congestion_patterns: Map, // Historical traffic patterns by hour/day
    weather_impact_factor: Float,
    road_surface_type: String,
    bridge_clearance: Float,
    created_at: DateTime,
    last_updated: DateTime
})

// Geographic Regions for Territory Management
(:Region {
    id: String,
    name: String,
    region_type: String, // 'STATE', 'CITY', 'COUNTY', 'POSTAL_CODE', 'CUSTOM_TERRITORY'
    boundary: Polygon,
    population: Integer,
    economic_indicators: Map,
    seasonal_demand_patterns: Map,
    regulatory_requirements: [String]
})
```

#### 4.3.2 Business Entity Nodes

```cypher
// Enhanced Driver Profiles
(:Driver {
    id: String,
    driver_number: String,
    first_name: String,
    last_name: String,
    license_class: [String], // ['CDL-A', 'CDL-B', 'HAZMAT']
    certifications: [String],
    experience_years: Integer,
    preferred_routes: [String],
    home_location: Point,
    performance_score: Float,
    on_time_percentage: Float,
    safety_score: Float,
    preferred_vehicle_types: [String],
    languages: [String],
    availability_schedule: Map,
    max_hours_per_day: Integer,
    rest_preferences: Map,
    emergency_contact: Map,
    hire_date: Date,
    status: String // 'ACTIVE', 'ON_LEAVE', 'TERMINATED'
})

// Enhanced Vehicle Profiles  
(:Vehicle {
    id: String,
    vehicle_number: String,
    make: String,
    model: String,
    year: Integer,
    vin: String,
    vehicle_type: String, // 'DRY_VAN', 'REFRIGERATED', 'FLATBED', 'TANKER', 'CONTAINER'
    capacity_weight: Float,
    capacity_volume: Float,
    fuel_type: String,
    fuel_efficiency: Float, // miles per gallon
    maintenance_schedule: Map,
    last_maintenance: Date,
    next_maintenance_due: Date,
    equipment: [String], // ['LIFTGATE', 'CHAINS', 'STRAPS', 'TEMPERATURE_CONTROL']
    restrictions: [String],
    insurance_info: Map,
    inspection_due: Date,
    home_base: String, // Location ID
    operating_cost_per_mile: Float,
    status: String // 'AVAILABLE', 'IN_USE', 'MAINTENANCE', 'OUT_OF_SERVICE'
})

// Customer/Shipper Entities
(:Customer {
    id: String,
    company_name: String,
    customer_type: String, // 'SHIPPER', 'CONSIGNEE', 'BROKER', '3PL'
    industry: String,
    credit_rating: String,
    payment_terms: Integer,
    preferred_carriers: [String],
    volume_commitments: Map,
    service_requirements: [String],
    contact_persons: [Map],
    billing_address: Map,
    seasonal_patterns: Map,
    priority_level: String
})

// Carrier/Fleet Entities
(:Carrier {
    id: String,
    company_name: String,
    dot_number: String,
    mc_number: String,
    carrier_type: String, // 'ASSET', 'OWNER_OPERATOR', 'BROKER'
    fleet_size: Integer,
    service_areas: [String],
    equipment_types: [String],
    insurance_info: Map,
    safety_rating: String,
    preferred_lanes: [String],
    capacity_commitment: Map,
    performance_metrics: Map,
    contract_terms: Map
})

// Load/Shipment Entities
(:Load {
    id: String,
    load_number: String,
    load_type: String, // 'FTL', 'LTL', 'PARTIAL'
    commodity_type: String,
    weight: Float,
    volume: Float,
    value: Float,
    special_requirements: [String],
    pickup_window: Map, // {start: DateTime, end: DateTime}
    delivery_window: Map,
    temperature_requirements: Map,
    hazmat_class: String,
    priority: String, // 'STANDARD', 'EXPEDITED', 'CRITICAL'
    rate: Float,
    fuel_surcharge: Float,
    accessorial_charges: [Map],
    status: String,
    created_at: DateTime
})
```

#### 4.3.3 Operational Entity Nodes

```cypher
// Route Plans/Templates
(:Route {
    id: String,
    route_name: String,
    route_type: String, // 'DEDICATED', 'REGULAR', 'SPOT', 'MILK_RUN'
    total_distance: Float,
    estimated_duration: Integer, // minutes
    fuel_cost_estimate: Float,
    toll_cost_estimate: Float,
    difficulty_rating: Float,
    seasonal_viability: Map,
    preferred_vehicle_types: [String],
    driver_skill_requirements: [String],
    created_at: DateTime,
    last_optimized: DateTime,
    usage_count: Integer,
    success_rate: Float
})

// Time Windows for Scheduling
(:TimeWindow {
    id: String,
    window_type: String, // 'PICKUP', 'DELIVERY', 'BREAK', 'MAINTENANCE'
    start_time: DateTime,
    end_time: DateTime,
    flexibility_minutes: Integer,
    priority: String,
    cost_per_hour_late: Float,
    associated_entity_id: String,
    recurring_pattern: String // 'DAILY', 'WEEKLY', 'MONTHLY'
})

// Optimization Scenarios
(:OptimizationScenario {
    id: String,
    scenario_name: String,
    objective_function: String, // 'MIN_COST', 'MIN_TIME', 'MAX_UTILIZATION', 'BALANCED'
    constraints: Map,
    parameters: Map,
    created_at: DateTime,
    executed_at: DateTime,
    results: Map,
    performance_metrics: Map
})
```

### 4.4 Relationship Types

#### 4.4.1 Network & Geographic Relationships

```cypher
// Route Network Connections
(:RouteNode)-[:CONNECTS_TO {
    distance: Float,
    travel_time_base: Integer, // minutes in ideal conditions
    road_type: String, // 'HIGHWAY', 'ARTERIAL', 'LOCAL', 'RURAL'
    traffic_patterns: Map, // hourly traffic multipliers
    weather_impact: Map, // weather condition multipliers
    toll_cost: Float,
    fuel_consumption_rate: Float,
    restriction_flags: [String],
    congestion_probability: Map, // probability by time of day
    accident_frequency: Float,
    construction_zones: [Map],
    grade_percentage: Float, // for fuel calculations
    curve_difficulty: Float,
    last_updated: DateTime
}]->(:RouteNode)

// Location Network Relationships
(:Location)-[:NEARBY_LOCATION {
    distance: Float,
    travel_time: Integer,
    accessibility_score: Float,
    service_compatibility: [String]
}]->(:Location)

// Regional Containment
(:Location)-[:WITHIN_REGION {
    administrative_level: String
}]->(:Region)

// Service Area Coverage
(:Carrier)-[:SERVES_REGION {
    service_level: String, // 'PRIMARY', 'SECONDARY', 'OCCASIONAL'
    response_time_hours: Float,
    capacity_allocation: Float,
    rate_multiplier: Float
}]->(:Region)
```

#### 4.4.2 Operational Relationships

```cypher
// Driver-Vehicle Compatibility & Assignment
(:Driver)-[:QUALIFIED_FOR {
    certification_date: Date,
    expiry_date: Date,
    proficiency_score: Float,
    training_hours: Integer,
    last_operated: Date
}]->(:Vehicle)

(:Driver)-[:CURRENTLY_ASSIGNED {
    assigned_at: DateTime,
    expected_end: DateTime,
    assignment_type: String, // 'DEDICATED', 'FLEXIBLE', 'TEMPORARY'
    performance_target: Map
}]->(:Vehicle)

(:Driver)-[:PREFERS_VEHICLE {
    preference_score: Float,
    reason: String,
    performance_delta: Float
}]->(:Vehicle)

// Load Assignment & Routing
(:Load)-[:ASSIGNED_TO {
    assigned_at: DateTime,
    pickup_sequence: Integer,
    delivery_sequence: Integer,
    special_instructions: String,
    estimated_pickup: DateTime,
    estimated_delivery: DateTime
}]->(:Vehicle)

(:Load)-[:ORIGIN_LOCATION {
    pickup_window_start: DateTime,
    pickup_window_end: DateTime,
    dock_requirements: [String],
    special_equipment_needed: [String]
}]->(:Location)

(:Load)-[:DESTINATION_LOCATION {
    delivery_window_start: DateTime,
    delivery_window_end: DateTime,
    unloading_time_minutes: Integer,
    signature_required: Boolean
}]->(:Location)

// Route Optimization Relationships
(:Route)-[:INCLUDES_STOP {
    stop_sequence: Integer,
    estimated_arrival: DateTime,
    service_time_minutes: Integer,
    stop_type: String, // 'PICKUP', 'DELIVERY', 'FUEL', 'REST'
    coordinates: Point
}]->(:Location)

(:Route)-[:OPTIMIZED_FOR {
    optimization_date: DateTime,
    objective_achieved: Float, // percentage of optimal
    constraints_satisfied: [String],
    total_cost: Float,
    total_time: Integer,
    fuel_consumption: Float,
    utilization_rate: Float
}]->(:OptimizationScenario)

(:Vehicle)-[:FOLLOWS_ROUTE {
    route_start: DateTime,
    route_end: DateTime,
    actual_vs_planned_variance: Map,
    fuel_consumed: Float,
    actual_distance: Float,
    performance_score: Float
}]->(:Route)
```

#### 4.4.3 Performance & Historical Relationships

```cypher
// Service History & Performance
(:Driver)-[:HAS_SERVED {
    service_date: Date,
    load_id: String,
    on_time_pickup: Boolean,
    on_time_delivery: Boolean,
    customer_rating: Float,
    fuel_efficiency: Float,
    hours_of_service_compliance: Boolean,
    incidents: [String],
    distance_driven: Float,
    weather_conditions: String
}]->(:Location)

(:Vehicle)-[:HAS_VISITED {
    visit_date: Date,
    load_id: String,
    driver_id: String,
    fuel_consumed: Float,
    mileage_added: Integer,
    maintenance_needs_identified: [String],
    performance_metrics: Map,
    utilization_hours: Float
}]->(:Location)

// Customer Relationship History
(:Customer)-[:HAS_SHIPPING_PATTERN {
    frequency: String, // 'DAILY', 'WEEKLY', 'MONTHLY', 'SEASONAL'
    volume_pattern: Map,
    seasonal_variations: Map,
    preferred_times: [String],
    service_requirements: [String],
    rate_sensitivity: Float,
    loyalty_score: Float
}]->(:Location)

(:Customer)-[:PREFERS_CARRIER {
    preference_score: Float,
    historical_performance: Map,
    contract_terms: Map,
    volume_commitment: Float,
    rate_agreement: Map
}]->(:Carrier)

// Network Effect Relationships  
(:Location)-[:INFLUENCES_DEMAND {
    influence_strength: Float,
    seasonal_factor: Map,
    economic_correlation: Float,
    lag_days: Integer
}]->(:Location)

(:Route)-[:COMPETES_WITH {
    overlap_percentage: Float,
    cost_differential: Float,
    time_differential: Integer,
    service_differential: Map
}]->(:Route)
```

### 4.5 Advanced Graph Patterns for Optimization

#### 4.5.1 Multi-Modal Transportation Networks

```cypher
// Intermodal Connections
(:Location)-[:INTERMODAL_TRANSFER {
    transfer_type: String, // 'RAIL_TO_TRUCK', 'PORT_TO_TRUCK', 'AIR_TO_TRUCK'
    transfer_time_hours: Float,
    transfer_cost: Float,
    capacity_constraints: Map,
    equipment_requirements: [String],
    operating_schedule: Map
}]->(:Location)

// Load Consolidation Opportunities
(:Load)-[:CAN_CONSOLIDATE_WITH {
    compatibility_score: Float,
    weight_utilization: Float,
    volume_utilization: Float,
    time_window_overlap: Float,
    geographic_efficiency: Float,
    cost_savings_potential: Float
}]->(:Load)
```

#### 4.5.2 Dynamic Constraint Networks

```cypher
// Time-Based Constraints
(:TimeWindow)-[:CONSTRAINS {
    constraint_type: String, // 'HARD', 'SOFT', 'PREFERRED'
    penalty_cost: Float,
    flexibility_minutes: Integer
}]->(:Load)

// Capacity Constraints
(:Vehicle)-[:CAPACITY_CONSTRAINT {
    constraint_type: String, // 'WEIGHT', 'VOLUME', 'COUNT'
    max_value: Float,
    current_utilization: Float,
    efficiency_threshold: Float
}]->(:Load)

// Driver Hours of Service
(:Driver)-[:HOS_CONSTRAINT {
    drive_time_remaining: Integer, // minutes
    duty_time_remaining: Integer,
    required_break_at: DateTime,
    weekly_hours_used: Float,
    reset_available: DateTime
}]->(:TimeWindow)
```

### 4.6 Graph Algorithms & Use Cases

#### 4.6.1 Route Optimization Queries

```cypher
// Find optimal multi-stop route
MATCH (start:Location {id: $startId})
MATCH (end:Location {id: $endId})  
MATCH (stops:Location) WHERE stops.id IN $stopIds
CALL apoc.algo.dijkstra(start, end, 'CONNECTS_TO', 'travel_time_base') 
YIELD path, weight
RETURN path, weight

// Find best driver-vehicle-load combination
MATCH (d:Driver)-[:QUALIFIED_FOR]->(v:Vehicle)
MATCH (l:Load)-[:ORIGIN_LOCATION]->(origin:Location)
MATCH (l)-[:DESTINATION_LOCATION]->(dest:Location)
WHERE d.status = 'AVAILABLE' 
  AND v.status = 'AVAILABLE'
  AND l.status = 'UNASSIGNED'
WITH d, v, l, origin, dest
MATCH path = (origin)-[:CONNECTS_TO*]-(dest)
RETURN d, v, l, 
       reduce(totalTime = 0, rel in relationships(path) | totalTime + rel.travel_time_base) as routeTime,
       (d.performance_score + v.fuel_efficiency) as combinedScore
ORDER BY combinedScore DESC, routeTime ASC
LIMIT 10
```

#### 4.6.2 Network Analysis Queries

```cypher
// Identify bottleneck locations
MATCH (l:Location)<-[:INCLUDES_STOP]-(r:Route)
WITH l, count(r) as route_frequency
WHERE route_frequency > 10
MATCH (l)-[:CONNECTS_TO]-(connected)
RETURN l.name, route_frequency, count(connected) as connectivity_score
ORDER BY route_frequency DESC, connectivity_score ASC

// Find load consolidation opportunities
MATCH (l1:Load), (l2:Load)
WHERE l1.id <> l2.id 
  AND l1.status = 'UNASSIGNED' 
  AND l2.status = 'UNASSIGNED'
MATCH (l1)-[:ORIGIN_LOCATION]->(o1:Location)
MATCH (l1)-[:DESTINATION_LOCATION]->(d1:Location)  
MATCH (l2)-[:ORIGIN_LOCATION]->(o2:Location)
MATCH (l2)-[:DESTINATION_LOCATION]->(d2:Location)
WHERE distance(o1.coordinates, o2.coordinates) < 50000 // 50km
  AND distance(d1.coordinates, d2.coordinates) < 50000
  AND l1.weight + l2.weight <= 40000 // max truck weight
RETURN l1, l2, 
       distance(o1.coordinates, o2.coordinates) as pickup_proximity,
       distance(d1.coordinates, d2.coordinates) as delivery_proximity
ORDER BY pickup_proximity + delivery_proximity
```

This comprehensive Neo4j schema transforms the TMS into an intelligent, relationship-driven system that can optimize operations across multiple dimensions simultaneously, enabling advanced use cases like dynamic routing, predictive maintenance, demand forecasting, and supply chain optimization.

---

## 5. TimescaleDB Schema (Time-Series Data)

### 5.1 Hypertables

#### 5.1.1 Vehicle Tracking Data
```sql
CREATE TABLE vehicle_tracking (
    time TIMESTAMPTZ NOT NULL,
    vehicle_id UUID NOT NULL,
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    speed DECIMAL(5,2),
    heading INTEGER,
    altitude DECIMAL(8,2),
    accuracy DECIMAL(6,2),
    odometer INTEGER,
    fuel_level DECIMAL(5,2),
    engine_hours DECIMAL(8,2),
    driver_id UUID,
    load_id UUID
);

SELECT create_hypertable('vehicle_tracking', 'time');
```

#### 5.1.2 Event Stream Data
```sql
CREATE TABLE event_stream (
    time TIMESTAMPTZ NOT NULL,
    event_id UUID NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB NOT NULL DEFAULT '{}',
    source_system VARCHAR(100) NOT NULL,
    correlation_id UUID,
    entity_type VARCHAR(50),
    entity_id UUID,
    location GEOGRAPHY(POINT, 4326),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

SELECT create_hypertable('event_stream', 'time');
```

#### 5.1.3 Audit Events Data
```sql
CREATE TABLE audit_events (
    time TIMESTAMPTZ NOT NULL,
    event_id UUID NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    source VARCHAR(100) NOT NULL,
    correlation_id UUID,
    version VARCHAR(10) NOT NULL DEFAULT '1.0',
    entity_type VARCHAR(50),
    entity_id UUID,
    location GEOGRAPHY(POINT, 4326),
    metadata JSONB NOT NULL DEFAULT '{}',
    data JSONB NOT NULL DEFAULT '{}',
    severity VARCHAR(20) DEFAULT 'INFO',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

SELECT create_hypertable('audit_events', 'time', chunk_time_interval => INTERVAL '1 day');
```

#### 5.1.4 Driver Activity Data
```sql
CREATE TABLE driver_activity (
    time TIMESTAMPTZ NOT NULL,
    driver_id UUID NOT NULL,
    activity_type VARCHAR(50) NOT NULL, -- 'DRIVING', 'ON_DUTY', 'OFF_DUTY', 'SLEEPER'
    location GEOGRAPHY(POINT, 4326),
    vehicle_id UUID,
    load_id UUID,
    hos_remaining DECIMAL(4,2),
    duration_minutes INTEGER,
    metadata JSONB
);

SELECT create_hypertable('driver_activity', 'time');
```

#### 5.1.5 Performance Metrics Data
```sql
CREATE TABLE performance_metrics (
    time TIMESTAMPTZ NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4) NOT NULL,
    entity_type VARCHAR(50) NOT NULL, -- 'DRIVER', 'VEHICLE', 'ROUTE', 'LOAD'
    entity_id UUID NOT NULL,
    dimensions JSONB DEFAULT '{}',
    tags JSONB DEFAULT '{}'
);

SELECT create_hypertable('performance_metrics', 'time');
```

### 5.2 Continuous Aggregates

#### 5.2.1 Event Hourly Summary
```sql
CREATE MATERIALIZED VIEW event_hourly_summary
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', time) AS hour,
    event_type,
    source,
    severity,
    COUNT(*) as event_count,
    COUNT(DISTINCT entity_id) as unique_entities
FROM audit_events
GROUP BY hour, event_type, source, severity
WITH NO DATA;

SELECT add_continuous_aggregate_policy('event_hourly_summary',
    start_offset => INTERVAL '4 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '30 minutes');
```

#### 5.2.2 Vehicle Performance Summary
```sql
CREATE MATERIALIZED VIEW vehicle_performance_hourly
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', time) AS hour,
    vehicle_id,
    AVG(speed) as avg_speed,
    MAX(speed) as max_speed,
    AVG(fuel_level) as avg_fuel_level,
    COUNT(*) as tracking_points
FROM vehicle_tracking
GROUP BY hour, vehicle_id
WITH NO DATA;

SELECT add_continuous_aggregate_policy('vehicle_performance_hourly',
    start_offset => INTERVAL '4 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '30 minutes');
```

### 5.3 Retention Policies
```sql
-- Keep detailed events for 90 days
SELECT add_retention_policy('audit_events', INTERVAL '90 days');
SELECT add_retention_policy('event_stream', INTERVAL '90 days');

-- Keep vehicle tracking for 1 year
SELECT add_retention_policy('vehicle_tracking', INTERVAL '1 year');

-- Keep driver activity for 2 years (regulatory compliance)
SELECT add_retention_policy('driver_activity', INTERVAL '2 years');

-- Keep performance metrics for 6 months
SELECT add_retention_policy('performance_metrics', INTERVAL '6 months');

-- Keep aggregated summaries for 1 year
SELECT add_retention_policy('event_hourly_summary', INTERVAL '1 year');
SELECT add_retention_policy('vehicle_performance_hourly', INTERVAL '1 year');
```

### 5.4 Indexes for Performance
```sql
-- Event stream indexes
CREATE INDEX ON event_stream (event_type, time DESC);
CREATE INDEX ON event_stream (entity_type, entity_id, time DESC);
CREATE INDEX ON event_stream (source_system, time DESC);
CREATE INDEX ON event_stream USING GIN (event_data);

-- Audit events indexes
CREATE INDEX ON audit_events (event_type, time DESC);
CREATE INDEX ON audit_events (entity_type, entity_id, time DESC);
CREATE INDEX ON audit_events (source, time DESC);
CREATE INDEX ON audit_events (correlation_id, time DESC) WHERE correlation_id IS NOT NULL;
CREATE INDEX ON audit_events USING GIN (metadata);
CREATE INDEX ON audit_events USING GIN (data);
CREATE INDEX ON audit_events USING GIST (location) WHERE location IS NOT NULL;
CREATE INDEX ON audit_events (severity, time DESC);

-- Vehicle tracking indexes
CREATE INDEX ON vehicle_tracking (vehicle_id, time DESC);
CREATE INDEX ON vehicle_tracking USING GIST (location);
CREATE INDEX ON vehicle_tracking (driver_id, time DESC);
CREATE INDEX ON vehicle_tracking (load_id, time DESC);

-- Driver activity indexes
CREATE INDEX ON driver_activity (driver_id, time DESC);
CREATE INDEX ON driver_activity (activity_type, time DESC);
CREATE INDEX ON driver_activity USING GIST (location) WHERE location IS NOT NULL;

-- Performance metrics indexes
CREATE INDEX ON performance_metrics (metric_name, time DESC);
CREATE INDEX ON performance_metrics (entity_type, entity_id, time DESC);
CREATE INDEX ON performance_metrics USING GIN (dimensions);
CREATE INDEX ON performance_metrics USING GIN (tags);
```

---

## 6. Data Consistency & Synchronization

### 6.1 Event-Driven Synchronization
- All database changes trigger events via Kafka
- Neo4j relationships updated based on PostgreSQL entity changes
- TimescaleDB populated via event stream processing
- Eventual consistency model with conflict resolution

### 6.2 Data Integrity Constraints
- UUID-based primary keys for cross-database consistency
- Foreign key constraints within PostgreSQL
- Graph constraints in Neo4j for relationship validity
- Time-series constraints in TimescaleDB for data quality

### 6.3 Backup and Recovery
- PostgreSQL: Continuous WAL archiving with point-in-time recovery
- Neo4j: Regular graph database dumps with transaction log backup
- TimescaleDB: Compressed backups with time-based retention
- Cross-database consistency verification procedures

---

## 7. Performance Considerations

### 7.1 Query Optimization
- Proper indexing strategies for each database type
- Query plan analysis and optimization
- Connection pooling and caching strategies  
- Read replica configurations for analytics workloads

### 7.2 Scalability Design
- Horizontal partitioning strategies
- Database sharding considerations
- Archive and purge policies for historical data
- Performance monitoring and alerting

---

## 8. Schema Validation and Testing

### 8.1 Comprehensive Test Coverage
The database schema has been thoroughly validated through a comprehensive test suite achieving **100% pass rate (49/49 tests)** in Docker environment:

#### 8.1.1 Schema Alignment Tests
- **PostgreSQL Schema Alignment**: Validates all table structures, constraints, and data types
- **TimescaleDB Hypertable Alignment**: Verifies time-series table configurations and partitioning
- **Spatial Data Constraints**: Tests PostGIS spatial data types and coordinate validation

#### 8.1.2 Model Validation Tests
- **Pydantic V2 Compatibility**: All models use modern Pydantic V2 patterns with proper validation
- **Google Maps API Compatibility**: Coordinate validation ensures lat/lon ranges comply with Maps API standards
  - Latitude: -90.0° to 90.0° (South Pole to North Pole)
  - Longitude: -180.0° to 180.0° (International Date Line)
- **UUID Validation**: Proper UUID pattern validation for all identifier fields
- **Financial Precision**: Decimal type usage for all monetary fields to ensure accuracy

#### 8.1.3 Cross-Layer Integration Tests
- **API Compatibility**: Request/response model validation ensures API-database alignment
- **Event Schema Alignment**: Event models properly map to database structures
- **Workflow Validation**: End-to-end data flow validation from API to database

### 8.2 Enhanced Model Attributes
The schema includes comprehensive attributes for operational excellence:

#### 8.2.1 Route Optimization Fields
- `optimization_score`: DECIMAL(5,2) - Route efficiency scoring (0-100)
- `fuel_estimate`: DECIMAL(8,2) - Estimated fuel consumption cost
- `toll_estimate`: DECIMAL(8,2) - Estimated toll costs
- `distance_miles`: DECIMAL(8,2) - Calculated route distance

#### 8.2.2 Request/Response Model Coverage
- **CreateLoadRequest**: Enhanced with `notes` field and string validation (min_length=1)
- **AssignLoadRequest**: Includes `estimated_pickup_time` and `estimated_delivery_time`
- **UpdateLocationRequest**: Google Maps API-compatible coordinate validation
- **Response Models**: Complete coverage with LoadResponse, VehicleResponse, DriverResponse

### 8.3 Validation Rules and Constraints

#### 8.3.1 String Validation
- Required string fields enforce `min_length=1` to prevent empty values
- Address fields validated for proper formatting and completeness

#### 8.3.2 Spatial Data Validation
- Coordinate bounds validation ensures data integrity
- PostGIS spatial constraints enforce proper geometry types
- Location updates validated for realistic coordinate ranges

#### 8.3.3 Business Logic Validation
- Load datetime validation ensures pickup before delivery
- Vehicle capacity constraints prevent overloading
- Driver hours-of-service validation maintains compliance
