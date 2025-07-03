# Product Requirements Document (PRD)
## TMS Database Schema

**Version:** 1.0  
**Date:** July 3, 2025  
**Authors:** Product Team  

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

## 4. Neo4j Graph Schema (Relationship Data)

### 4.1 Node Types

#### 4.1.1 Driver Nodes
```cypher
// Driver Node Structure
(:Driver {
    id: String,
    driver_number: String,
    name: String,
    license_class: String,
    experience_years: Integer,
    rating: Float,
    current_location: Point,
    status: String,
    specializations: [String]
})
```

#### 4.1.2 Vehicle Nodes  
```cypher
// Vehicle Node Structure
(:Vehicle {
    id: String,
    vehicle_number: String,
    type: String,
    capacity_weight: Float,
    capacity_volume: Float,
    fuel_efficiency: Float,
    current_location: Point,
    status: String,
    features: [String]
})
```

#### 4.1.3 Location Nodes
```cypher
// Location Node Structure
(:Location {
    id: String,
    name: String,
    address: String,
    coordinates: Point,
    type: String, // 'PICKUP', 'DELIVERY', 'HUB', 'FUEL_STATION'
    operating_hours: String,
    dock_count: Integer
})
```

#### 4.1.4 Route Network Nodes
```cypher
// Route Network Node Structure
(:RouteNode {
    id: String,
    coordinates: Point,
    type: String, // 'INTERSECTION', 'HIGHWAY_ENTRY', 'TOLL_BOOTH'
    traffic_weight: Float,
    restrictions: [String]
})
```

### 4.2 Relationship Types

#### 4.2.1 Driver-Vehicle Relationships
```cypher
// Driver qualified to operate vehicle
(:Driver)-[:QUALIFIED_FOR {
    certification_date: Date,
    expiry_date: Date,
    training_completed: Boolean
}]->(:Vehicle)

// Current assignment
(:Driver)-[:CURRENTLY_ASSIGNED {
    assigned_at: DateTime,
    expected_duration: Duration
}]->(:Vehicle)
```

#### 4.2.2 Route Network Relationships
```cypher
// Route connections
(:RouteNode)-[:CONNECTS_TO {
    distance: Float,
    travel_time: Integer,
    road_type: String,
    traffic_factor: Float,
    toll_cost: Float
}]->(:RouteNode)

// Optimal paths
(:Location)-[:OPTIMAL_ROUTE {
    total_distance: Float,
    total_time: Integer,
    total_cost: Float,
    waypoints: [String],
    calculated_at: DateTime
}]->(:Location)
```

#### 4.2.3 Service History Relationships
```cypher
// Driver service history
(:Driver)-[:HAS_SERVED {
    route_id: String,
    service_date: Date,
    performance_score: Float,
    on_time_delivery: Boolean
}]->(:Location)

// Vehicle service history  
(:Vehicle)-[:HAS_VISITED {
    visit_date: Date,
    load_id: String,
    fuel_consumed: Float,
    mileage_added: Integer
}]->(:Location)
```

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
CREATE INDEX ON vehicle_tracking (vehicle_id, time DESC);
CREATE INDEX ON vehicle_tracking USING GIST (location);
```

#### 5.1.2 Performance Metrics
```sql
CREATE TABLE performance_metrics (
    time TIMESTAMPTZ NOT NULL,
    entity_type VARCHAR(20) NOT NULL, -- 'DRIVER', 'VEHICLE', 'ROUTE'
    entity_id UUID NOT NULL,
    metric_name VARCHAR(50) NOT NULL,
    metric_value DECIMAL(15,4) NOT NULL,
    tags JSONB
);

SELECT create_hypertable('performance_metrics', 'time');
CREATE INDEX ON performance_metrics (entity_type, entity_id, time DESC);
CREATE INDEX ON performance_metrics (metric_name, time DESC);
```

#### 5.1.3 Event Stream Data
```sql
CREATE TABLE event_stream (
    time TIMESTAMPTZ NOT NULL,
    event_id UUID NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    source_system VARCHAR(50) NOT NULL,
    entity_type VARCHAR(20),
    entity_id UUID,
    event_data JSONB NOT NULL,
    correlation_id UUID,
    trace_id UUID
);

SELECT create_hypertable('event_stream', 'time');
CREATE INDEX ON event_stream (event_type, time DESC);
CREATE INDEX ON event_stream (entity_type, entity_id, time DESC);
CREATE INDEX ON event_stream (correlation_id);
```

### 5.2 Continuous Aggregates

#### 5.2.1 Hourly Performance Summary
```sql
CREATE MATERIALIZED VIEW hourly_performance
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', time) AS bucket,
    entity_type,
    entity_id,
    metric_name,
    AVG(metric_value) AS avg_value,
    MAX(metric_value) AS max_value,
    MIN(metric_value) AS min_value,
    COUNT(*) AS sample_count
FROM performance_metrics
GROUP BY bucket, entity_type, entity_id, metric_name;

SELECT add_continuous_aggregate_policy('hourly_performance',
    start_offset => INTERVAL '1 day',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');
```

#### 5.2.2 Daily Vehicle Utilization
```sql
CREATE MATERIALIZED VIEW daily_vehicle_utilization
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 day', time) AS bucket,
    vehicle_id,
    COUNT(DISTINCT load_id) AS loads_served,
    SUM(CASE WHEN speed > 0 THEN 1 ELSE 0 END) * 5 / 60.0 AS driving_hours, -- 5-minute intervals
    MAX(odometer) - MIN(odometer) AS miles_driven,
    AVG(fuel_level) AS avg_fuel_level
FROM vehicle_tracking
GROUP BY bucket, vehicle_id;

SELECT add_continuous_aggregate_policy('daily_vehicle_utilization',
    start_offset => INTERVAL '7 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 hour');
```

### 5.3 Retention Policies
```sql
-- Retain raw tracking data for 90 days
SELECT add_retention_policy('vehicle_tracking', INTERVAL '90 days');

-- Retain raw performance metrics for 180 days  
SELECT add_retention_policy('performance_metrics', INTERVAL '180 days');

-- Retain raw events for 365 days
SELECT add_retention_policy('event_stream', INTERVAL '365 days');
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

## 8. Security and Compliance

### 8.1 Data Protection
- Column-level encryption for sensitive data
- Row-level security policies
- Database audit logging
- Access control and authentication

### 8.2 Compliance Requirements
- Data retention policies per regulatory requirements
- Audit trail maintenance
- Personal data protection (GDPR compliance)
- Industry-specific compliance (DOT, FMCSA)

This comprehensive database schema provides the foundation for a scalable, performant, and feature-rich Transportation Management System while leveraging the strengths of each specialized database technology.
