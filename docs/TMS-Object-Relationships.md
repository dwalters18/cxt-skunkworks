# TMS Object Relationships & Design Architecture

## Core Business Objects

### 1. **Loads** - Independent Cargo Assignments
- **Purpose**: Represent shipments that need transportation from pickup to delivery
- **Lifecycle**: Created → Assigned → In Transit → Delivered
- **Key Attributes**: 
  - Pickup/delivery locations and times
  - Weight, volume, commodity type
  - Customer requirements and constraints
- **Independence**: Loads exist independently of vehicles or drivers

### 2. **Vehicles** - Physical Transportation Assets
- **Purpose**: Tractors, trucks, trailers that can transport loads
- **Lifecycle**: Available → Assigned → In Use → Maintenance → Available
- **Key Attributes**:
  - Capacity (weight/volume), location, fuel type
  - Status, maintenance schedules, capabilities
- **Asset Management**: Owned by carriers, tracked for utilization and maintenance

### 3. **Drivers** - Human Resources (Optional & Flexible)
- **Purpose**: Licensed operators who can drive vehicles
- **Lifecycle**: Available → On Duty → Off Duty → Available
- **Key Challenges**:
  - **High Turnover**: Drivers come and go frequently in the trucking industry
  - **Shift Changes**: Multiple drivers may use the same vehicle across shifts
  - **Flexibility**: Some routes may be autonomous or driver assignments may change
- **Design Decision**: Driver assignment is **optional and flexible**

### 4. **Routes** - Optimized Transportation Plans
- **Purpose**: Calculated paths between pickup and delivery locations
- **Core Relationship**: **Load ↔ Vehicle** (Primary)
- **Optional Relationship**: **Driver** (Secondary, can be assigned later)
- **Focus**: Route optimization is about finding the most efficient path for a specific vehicle to handle a specific load

## Relationship Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    LOAD     │    │   VEHICLE   │    │   DRIVER    │
│ (Required)  │    │ (Required)  │    │ (Optional)  │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       │                   │                   │
       └─────────┬─────────┘                   │
                 │                             │
                 ▼                             │
         ┌─────────────┐                       │
         │    ROUTE    │◄──────────────────────┘
         │ (Optimized) │
         └─────────────┘
```

## Route Optimization Design Philosophy

### Primary Optimization: Load + Vehicle
- **Core Question**: "What's the most efficient route for this vehicle to transport this load?"
- **Factors Considered**:
  - Vehicle capabilities (capacity, fuel efficiency, restrictions)
  - Load requirements (weight, volume, special handling)
  - Geographic constraints (pickup/delivery locations, traffic, regulations)
  - Time constraints (pickup/delivery windows)

### Secondary Assignment: Driver (When Available)
- **Flexible Assignment**: Drivers can be assigned to routes during dispatch
- **Change Management**: Driver assignments can change without affecting route optimization
- **Shift Handling**: Routes may span multiple driver shifts
- **Autonomous Ready**: Architecture supports future autonomous vehicle integration

## Database Schema Decisions

### Routes Table
```sql
CREATE TABLE routes (
    id UUID PRIMARY KEY,
    load_id UUID NOT NULL REFERENCES loads(id),    -- Always required
    vehicle_id UUID NOT NULL REFERENCES vehicles(id), -- Always required  
    driver_id UUID REFERENCES drivers(id),         -- NULLABLE - Optional assignment
    -- ... route optimization data
);
```

### Benefits of This Design
1. **Route Optimization Independence**: Routes can be calculated without driver assignment
2. **Operational Flexibility**: Dispatch can assign/reassign drivers as needed
3. **Data Integrity**: Core route data remains stable even when driver assignments change
4. **Industry Reality**: Reflects actual trucking operations where driver assignments are fluid

## API Design Patterns

### Route Optimization Endpoint
```json
POST /api/routes/optimize-load
{
  "load_id": "uuid",      // Required - what to transport
  "vehicle_id": "uuid",   // Required - how to transport
  "driver_id": "uuid"     // Optional - who might transport
}
```

### Driver Assignment Endpoint (Future)
```json
PATCH /api/routes/{route_id}/assign-driver
{
  "driver_id": "uuid",    // Assign or reassign driver
  "effective_time": "timestamp"
}
```

## Operational Workflows

### 1. Route Planning (Core)
1. Load created with pickup/delivery requirements
2. Available vehicles identified based on capacity/location
3. **Route optimization performed for Load + Vehicle combination**
4. Optimized route stored with vehicle assignment

### 2. Driver Dispatch (Flexible)
1. Dispatch reviews optimized routes
2. Available drivers identified based on location/schedule
3. Driver assigned to route when ready for execution
4. Driver assignment can change during route execution

### 3. Execution & Tracking
1. Vehicle begins route with assigned load
2. Driver status tracked independently
3. Route progress monitored regardless of driver changes
4. Completion recorded for all objects

This architecture provides the operational flexibility needed in modern transportation management while maintaining clear optimization focus and data integrity.
