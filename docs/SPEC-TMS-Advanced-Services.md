# TMS Advanced Services Specification

## Executive Summary

This document specifies the advanced Neo4j-powered analytics and optimization services for the Transportation Management System (TMS). These services leverage graph database relationships to provide intelligent insights, route optimization, and fleet analytics that go beyond traditional CRUD operations.

## Table of Contents

1. [Advanced Route Optimization](#advanced-route-optimization)
2. [Neo4j Analytics Services](#neo4j-analytics-services)
3. [Data Models](#data-models)
4. [Event Integration](#event-integration)
5. [Performance Requirements](#performance-requirements)
6. [Database Schema Alignment](#database-schema-alignment)

## Advanced Route Optimization

### POST /api/routes/advanced-optimize-load

**Purpose**: Multi-constraint route optimization leveraging Neo4j graph relationships for intelligent driver-vehicle assignment.

**Request Schema**:
```json
{
  "load_id": "UUID",
  "max_driver_distance_miles": 100.0,
  "max_route_duration_hours": 12.0,
  "min_driver_rating": 4.0,
  "min_carrier_performance": 0.85,
  "consider_traffic": true
}
```

**Response Schema**:
```json
{
  "success": true,
  "load_id": "UUID",
  "selected_driver_id": "UUID",
  "selected_vehicle_id": "UUID",
  "selected_carrier_id": "UUID",
  "optimization_score": 0.92,
  "alternatives_considered": 15,
  "distance_miles": 485.2,
  "duration_minutes": 528,
  "estimated_fuel_cost": 185.40,
  "route_geometry": "LINESTRING(...)",
  "optimization_factors": {
    "proximity_score": 0.85,
    "vehicle_suitability_score": 0.95,
    "carrier_performance_score": 0.88,
    "cost_efficiency_score": 0.92,
    "timeline_feasibility_score": 0.94
  }
}
```

**Graph Queries Used**:
- Load node retrieval with pickup/delivery coordinates
- Nearby driver discovery using spatial functions
- Vehicle capacity and compatibility matching
- Carrier performance history analysis
- Cost optimization calculations

**Events Published**: `ADVANCED_ROUTE_OPTIMIZED`

## Neo4j Analytics Services

### GET /api/analytics/nearby-drivers

**Purpose**: Find available drivers within specified radius using Neo4j spatial queries.

**Parameters**:
- `pickup_lat` (required): Pickup latitude
- `pickup_lng` (required): Pickup longitude  
- `radius_miles` (default: 50.0): Search radius
- `status_filter` (default: "AVAILABLE"): Driver status filter
- `min_rating` (optional): Minimum driver rating
- `vehicle_type_filter` (optional): Vehicle type requirement

**Response Schema**:
```json
{
  "success": true,
  "drivers_found": 12,
  "search_criteria": {
    "pickup_location": {"lat": 41.8781, "lng": -87.6298},
    "radius_miles": 50.0,
    "status_filter": "AVAILABLE",
    "min_rating": 4.0,
    "vehicle_type_filter": "DRY_VAN"
  },
  "drivers": [
    {
      "driver_id": "UUID",
      "driver_name": "John Smith",
      "current_location": {"lat": 41.8945, "lng": -87.6512},
      "distance_miles": 12.3,
      "status": "AVAILABLE",
      "carrier_name": "ABC Trucking",
      "vehicle_type": "DRY_VAN",
      "rating": 4.2,
      "hours_available": 8.5
    }
  ]
}
```

### GET /api/analytics/carrier-performance

**Purpose**: Comprehensive carrier performance analytics from graph relationships.

**Parameters**:
- `carrier_id` (optional): Specific carrier to analyze
- `time_period_days` (default: 90): Analysis time window

**Response Schema**:
```json
{
  "success": true,
  "analysis_period_days": 90,
  "carriers_analyzed": 5,
  "carrier_metrics": [
    {
      "carrier_id": "UUID",
      "carrier_name": "ABC Trucking",
      "total_loads_completed": 245,
      "on_time_delivery_rate": 0.92,
      "average_rating": 4.3,
      "cost_efficiency_score": 0.88,
      "revenue_generated": 125000.00,
      "active_drivers": 8,
      "active_vehicles": 12,
      "specialties": ["DRY_VAN", "REFRIGERATED"]
    }
  ]
}
```

### GET /api/analytics/fleet-utilization

**Purpose**: Fleet utilization metrics and efficiency analysis.

**Response Schema**:
```json
{
  "success": true,
  "fleet_metrics": {
    "total_vehicles": 45,
    "active_vehicles": 38,
    "utilization_rate": 0.84,
    "average_miles_per_vehicle": 8500.5,
    "maintenance_due_count": 3,
    "fuel_efficiency_avg": 6.8,
    "revenue_per_vehicle": 15250.00
  }
}
```

### POST /api/analytics/optimal-driver-vehicle-pairs

**Purpose**: Find optimal driver-vehicle combinations for specific load requirements.

**Request Schema**:
```json
{
  "pickup_lat": 41.8781,
  "pickup_lng": -87.6298,
  "delivery_lat": 40.7589,
  "delivery_lng": -73.9851,
  "load_weight": 35000.0,
  "load_type": "DRY_GOODS",
  "max_distance_miles": 100.0
}
```

**Response Schema**:
```json
{
  "success": true,
  "load_requirements": {
    "pickup_location": {"lat": 41.8781, "lng": -87.6298},
    "delivery_location": {"lat": 40.7589, "lng": -73.9851},
    "load_weight": 35000.0,
    "load_type": "DRY_GOODS",
    "max_distance_miles": 100.0
  },
  "optimal_pairs_found": 8,
  "driver_vehicle_pairs": [
    {
      "driver_id": "UUID",
      "vehicle_id": "UUID",
      "composite_score": 0.94,
      "distance_to_pickup": 15.2,
      "carrier_name": "ABC Trucking",
      "estimated_cost": 1250.00
    }
  ]
}
```

## Data Models

### Optimization Constraints
```python
class OptimizationConstraints(BaseModel):
    max_driver_distance_miles: Optional[float] = 100.0
    max_route_duration_hours: Optional[float] = 12.0
    min_driver_rating: Optional[float] = None
    min_carrier_performance: Optional[float] = None
    consider_traffic: Optional[bool] = True
```

### Graph Query Results
```python
class NearbyDriver(BaseModel):
    driver_id: str
    driver_name: str
    current_location: dict
    distance_miles: float
    status: str
    carrier_name: str
    vehicle_type: str
    rating: float
    hours_available: float

class CarrierMetrics(BaseModel):
    carrier_id: str
    carrier_name: str
    total_loads_completed: int
    on_time_delivery_rate: float
    average_rating: float
    cost_efficiency_score: float
    revenue_generated: float
    active_drivers: int
    active_vehicles: int
    specialties: List[str]

class FleetMetrics(BaseModel):
    total_vehicles: int
    active_vehicles: int
    utilization_rate: float
    average_miles_per_vehicle: float
    maintenance_due_count: int
    fuel_efficiency_avg: float
    revenue_per_vehicle: float
```

## Event Integration

### Published Events

**ADVANCED_ROUTE_OPTIMIZED**
```json
{
  "event_type": "ADVANCED_ROUTE_OPTIMIZED",
  "data": {
    "load_id": "UUID",
    "selected_driver_id": "UUID",
    "selected_vehicle_id": "UUID",
    "optimization_score": 0.92,
    "optimization_method": "graph_based_multi_constraint",
    "alternatives_considered": 15,
    "distance_miles": 485.2,
    "duration_minutes": 528
  }
}
```

### Kafka Topics
- `route-optimization-events`: Advanced route optimization results
- `analytics-queries`: Query execution metrics and performance data

## Performance Requirements

### Response Time Targets
- **Advanced Route Optimization**: < 3 seconds for complex multi-constraint optimization
- **Nearby Drivers Query**: < 500ms for spatial queries within 100-mile radius
- **Carrier Performance Analytics**: < 2 seconds for 90-day analysis
- **Fleet Utilization**: < 1 second for current fleet metrics
- **Optimal Pairs Discovery**: < 2 seconds for driver-vehicle matching

### Concurrency
- Support up to 50 concurrent advanced optimization requests
- Handle 200+ concurrent analytics queries
- Maintain sub-second response times under normal load

### Data Volume Capacity
- Neo4j graph queries optimized for 10,000+ driver nodes
- Spatial indexing for efficient geographic proximity searches
- Performance analytics over 100,000+ historical load records

## Database Schema Alignment

### Neo4j Node Requirements
The advanced services require the following Neo4j node types and properties (aligned with SPEC-Database-Schema.md):

**Driver Nodes**:
```cypher
(:Driver {
  id: String,
  driver_number: String,
  first_name: String,
  last_name: String,
  license_class: [String],
  certifications: [String],
  experience_years: Integer,
  performance_score: Float,
  on_time_percentage: Float,
  safety_score: Float,
  home_location: Point,
  preferred_vehicle_types: [String],
  max_hours_per_day: Integer,
  status: String // 'ACTIVE', 'ON_LEAVE', 'TERMINATED'
})
```

**Vehicle Nodes**:
```cypher
(:Vehicle {
  id: String,
  vehicle_number: String,
  make: String,
  model: String,
  vehicle_type: String, // 'DRY_VAN', 'REFRIGERATED', 'FLATBED', 'TANKER', 'CONTAINER'
  capacity_weight: Float,
  capacity_volume: Float,
  fuel_efficiency: Float,
  equipment: [String],
  home_base: String, // Location ID
  operating_cost_per_mile: Float,
  status: String // 'AVAILABLE', 'IN_USE', 'MAINTENANCE', 'OUT_OF_SERVICE'
})
```

**Carrier Nodes**:
```cypher
(:Carrier {
  id: String,
  company_name: String,
  dot_number: String,
  mc_number: String,
  carrier_type: String, // 'ASSET', 'OWNER_OPERATOR', 'BROKER'
  fleet_size: Integer,
  service_areas: [String],
  equipment_types: [String],
  safety_rating: String,
  performance_metrics: Map
})
```

**Load Nodes**:
```cypher
(:Load {
  id: String,
  load_number: String,
  load_type: String, // 'FTL', 'LTL', 'PARTIAL'
  commodity_type: String,
  weight: Float,
  volume: Float,
  pickup_window: Map, // {start: DateTime, end: DateTime}
  delivery_window: Map,
  priority: String, // 'STANDARD', 'EXPEDITED', 'CRITICAL'
  rate: Float,
  status: String
})
```

**Location Nodes** (for spatial queries):
```cypher
(:Location {
  id: String,
  name: String,
  location_type: String, // 'PICKUP', 'DELIVERY', 'DEPOT', 'REST_AREA'
  coordinates: Point,
  address: Map,
  timezone: String,
  operating_hours: Map
})
```

### Required Relationships
```cypher
// Core Business Relationships
(:Driver)-[:DRIVES]->(:Vehicle)
(:Driver)-[:WORKS_FOR]->(:Carrier)
(:Vehicle)-[:OWNED_BY]->(:Carrier)
(:Driver)-[:ASSIGNED_TO]->(:Load)
(:Load)-[:TRANSPORTED_BY]->(:Vehicle)

// Spatial and Route Relationships  
(:Load)-[:PICKUP_AT]->(:Location)
(:Load)-[:DELIVERY_AT]->(:Location)
(:Driver)-[:LOCATED_AT]->(:Location)
(:Vehicle)-[:STATIONED_AT]->(:Location)

// Performance and Analytics Relationships
(:Driver)-[:HAS_CERTIFICATION]->(:Certification)
(:Driver)-[:QUALIFIED_FOR]->(:Equipment)
(:Vehicle)-[:REQUIRES]->(:Maintenance)
(:Carrier)-[:SERVES]->(:ServiceArea)
```

### Spatial Indexing
Neo4j spatial indexes required for efficient proximity queries (using Point data type):
```cypher
// Location-based spatial indexes
CREATE INDEX location_coordinates FOR (l:Location) ON (l.coordinates)
CREATE INDEX driver_home_location FOR (d:Driver) ON (d.home_location)

// Composite indexes for performance
CREATE INDEX driver_status_location FOR (d:Driver) ON (d.status, d.home_location)
CREATE INDEX vehicle_status_location FOR (v:Vehicle) ON (v.status, v.home_base)
CREATE INDEX load_priority_status FOR (l:Load) ON (l.priority, l.status)

// Performance optimization indexes
CREATE INDEX carrier_performance FOR (c:Carrier) ON (c.safety_rating, c.fleet_size)
CREATE INDEX driver_performance FOR (d:Driver) ON (d.performance_score, d.on_time_percentage)
```

---

*This specification complements the main TMS API specification and focuses specifically on advanced Neo4j-powered services and analytics capabilities.*
