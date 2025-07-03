# Database UI Access Guide

This guide covers how to access and manage your TMS project databases through web-based UI tools.

## Neo4j Browser (Graph Database)

**Already Available** - No additional setup required!

- **URL:** http://localhost:7474
- **Username:** `neo4j`
- **Password:** `tms_graph_password`
- **Features:**
  - Run Cypher queries
  - Visualize graph relationships
  - Explore nodes and relationships
  - Monitor database performance

### Sample Neo4j Queries
```cypher
// View all nodes
MATCH (n) RETURN n LIMIT 10

// View load-vehicle relationships
MATCH (l:Load)-[:ASSIGNED_TO]->(v:Vehicle) RETURN l, v

// Find routes
MATCH (r:Route) RETURN r
```

## pgAdmin (PostgreSQL & TimescaleDB)

- **URL:** http://localhost:5050
- **Username:** `admin@tms.local`
- **Password:** `admin_password`
- **Pre-configured Connections:**
  - **TMS PostgreSQL (OLTP)** - Main transactional database
  - **TMS TimescaleDB (Time-Series)** - Time-series analytics data

### Database Passwords for pgAdmin
When connecting for the first time, you'll need these passwords:
- **PostgreSQL:** `tms_password`
- **TimescaleDB:** `timescale_password`

### Key Tables to Explore

#### PostgreSQL (tms_oltp)
- `loads` - Load/shipment data
- `vehicles` - Vehicle fleet information
- `drivers` - Driver records
- `load_events` - Load status events
- `routes` - Route information

#### TimescaleDB (tms_timeseries)
- `vehicle_locations` - Real-time vehicle tracking
- `driver_locations` - Driver location history
- `performance_metrics` - System performance data

## Other Available UIs

### Kafka UI
- **URL:** http://localhost:8080
- **Purpose:** View Kafka topics, messages, consumers
- **Key Topics:** `tms.loads`, `tms.vehicles`, `tms.drivers`

### Flink Dashboard
- **URL:** http://localhost:8081
- **Purpose:** Monitor stream processing jobs
- **Features:** Job monitoring, task manager status

## Getting Started

1. **Start all services:**
   ```bash
   docker-compose up -d
   ```

2. **Wait for services to be ready** (check logs):
   ```bash
   docker-compose logs pgadmin neo4j
   ```

3. **Access UIs:**
   - Neo4j Browser: http://localhost:7474
   - pgAdmin: http://localhost:5050
   - Kafka UI: http://localhost:8080
   - Flink Dashboard: http://localhost:8081

## Troubleshooting

### pgAdmin Connection Issues
- Ensure PostgreSQL/TimescaleDB containers are running
- Check that services are on the same Docker network (`tms-network`)
- Verify database passwords in pgAdmin connection settings

### Neo4j Connection Issues
- Check if Neo4j container is healthy: `docker-compose ps neo4j`
- Verify port 7474 is accessible
- Ensure password matches: `tms_graph_password`

### Network Issues
All database UI services are configured to use the `tms-network` Docker network for internal communication while exposing web interfaces on localhost ports.
