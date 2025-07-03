# TMS Implementation Roadmap

> **Revision Note – July 2025**  
> The roadmap has been updated based on the July 2025 product review. The new content introduces a 10-week MVP delivery plan, addresses identified gaps (auth/RBAC, schema registry, observability, Redis decision, DR planning, Google Maps cost controls, accessibility & UX performance), and lists immediate next steps.

## Refined MVP Roadmap (July – Sept 2025)
| Sprint | Milestone & Key Deliverables | Dependencies |
|--------|-----------------------------|--------------|
| **0 – Foundations (1 wk)** | • Confirm Redis role (remove or cache layer)  
• Introduce Schema Registry  
• Deploy OpenTelemetry + Prometheus/Grafana | none |
| **1-2 – Real Analytics (2 wks)** | • Replace mock AnalyticsDashboard data  
• `/analytics/dashboard` API w/ Timescale Continuous Aggregates  
• WebSocket live push | Foundations |
| **3-4 – Dispatch Core UI (2 wks)** | • Event stream panel with filters/search  
• WebSocket subscription lib | Analytics APIs |
| **5-6 – Load Assignment (2 wks)** | • `POST /loads/{id}/assign` + validation & Kafka events  
• Drag-and-drop UI; real-time updates | Dispatch Core |
| **7 – Google Maps Baseline (1 wk)** | • Replace placeholder map  
• Vehicle & load markers; geocoding service  
• Secure API key storage | Foundations |
| **8-9 – Neo4j Relationships (2 wks)** | • Event-driven LOAD/VEHICLE/DRIVER graph population  
• "Nearby vehicles" query | Assignment events, Maps |
| **10 – Hardening & Pilot Launch (1 wk)** | • k6 & gatling load tests (5 k evts/min)  
• WCAG 2.1 AA & bundle ≤ 200 KB  
• DR run-book draft | All previous |

### Immediate Actions (July 2025)
1. Decide on Redis retention vs removal.
2. Approve schema-registry & observability stack specs.
3. Allocate squads for Sprints 0-2 and schedule kickoff.
4. Secure Google Maps billing account and set quota alerts.

---

## Overview
This roadmap outlines the remaining implementation tasks to complete the Transportation Management System (TMS). The focus is on enhancing the analytics dashboard, improving data relationships, adding dispatch functionality, integrating Google Maps, and implementing route optimization.

## Current System Status
- ✅ Kafka-based event streaming architecture (KRaft mode)
- ✅ FastAPI backend with PostgreSQL, TimescaleDB, and Neo4j
- ✅ React frontend with multiple UI components
- ✅ Real-time WebSocket communication
- ✅ Load, Vehicle, and Driver management APIs
- ✅ Event Console with real event streaming
- ⚠️ Analytics Dashboard (needs real data integration)
- ⚠️ Neo4j relationships (needs population from actions)
- ⚠️ Dispatch Board (needs Google Maps and assignment functionality)

## Implementation Phases

### Phase 1: Analytics Dashboard Enhancement
**Priority:** High  
**Estimated Timeline:** 1-2 weeks

#### 1.1 Fix Analytics Data Integration
- **Current Issue:** AnalyticsDashboard uses mocked data instead of real backend APIs
- **Tasks:**
  - Replace mock data with real API calls to backend analytics endpoints
  - Ensure proper data aggregation from TimescaleDB
  - Implement real-time data updates via WebSocket
  - Add loading states and error handling

#### 1.2 Analytics API Development
- **Backend Changes:**
  - Enhance `/analytics/dashboard` endpoint with comprehensive metrics
  - Add endpoints for:
    - Load performance metrics (on-time delivery, average transit time)
    - Vehicle utilization statistics
    - Driver performance analytics
    - Route efficiency metrics
  - Implement time-range filtering for analytics queries

#### 1.3 Analytics UI Improvements
- **Frontend Changes:**
  - Add date range selectors
  - Implement interactive charts with drill-down capability
  - Add real-time metric updates
  - Improve visual design and responsiveness

### Phase 2: Neo4j Relationship Population
**Priority:** High  
**Estimated Timeline:** 2-3 weeks

#### 2.1 Relationship Modeling
- **Design Neo4j Graph Schema:**
  - `LOAD` nodes with properties (id, origin, destination, weight, status)
  - `VEHICLE` nodes with properties (id, type, capacity, location)
  - `DRIVER` nodes with properties (id, name, license, status)
  - `ROUTE` nodes with properties (id, waypoints, distance, duration)
  - Relationships:
    - `(LOAD)-[:ASSIGNED_TO]->(VEHICLE)`
    - `(LOAD)-[:DRIVEN_BY]->(DRIVER)`
    - `(VEHICLE)-[:FOLLOWS]->(ROUTE)`
    - `(DRIVER)-[:DRIVES]->(VEHICLE)`

#### 2.2 Event-Driven Neo4j Updates
- **Kafka Event Handlers:**
  - `LOAD_ASSIGNED` → Create ASSIGNED_TO relationship
  - `VEHICLE_STATUS_CHANGED` → Update vehicle node properties
  - `DRIVER_STATUS_CHANGED` → Update driver node properties
  - `ROUTE_OPTIMIZED` → Create/update route nodes and relationships

#### 2.3 Neo4j Service Enhancement
- **Backend Changes:**
  - Implement relationship creation/update methods
  - Add graph traversal queries for route optimization
  - Create analytics queries using graph relationships
  - Add Neo4j transaction handling for consistency

### Phase 3: Dispatch Board Assignment Functionality
**Priority:** Medium  
**Estimated Timeline:** 2-3 weeks

#### 3.1 Load Assignment UI
- **Frontend Features:**
  - Drag-and-drop interface for assigning loads to vehicles/drivers
  - Modal dialogs for assignment confirmation
  - Real-time status updates
  - Assignment history tracking

#### 3.2 Assignment API Development
- **Backend APIs:**
  - `POST /loads/{id}/assign` endpoint
  - Validation logic for assignment constraints
  - Event publishing for assignment actions
  - Assignment rollback functionality

#### 3.3 Real-time Event Integration
- **WebSocket Events:**
  - Broadcast assignment events to all connected clients
  - Update dispatch board in real-time
  - Show notifications for assignment changes
  - Implement event history display

### Phase 4: Google Maps Integration
**Priority:** High  
**Estimated Timeline:** 3-4 weeks

#### 4.1 Google Maps Setup
- **Requirements:**
  - Google Cloud Platform account and API keys
  - Enable required APIs:
    - Maps JavaScript API
    - Directions API
    - Distance Matrix API
    - Places API

#### 4.2 Map Component Development
- **Frontend Changes:**
  - Replace current map placeholder with Google Maps
  - Implement vehicle location markers with real-time updates
  - Add load pickup/delivery location markers
  - Create route visualization with polylines
  - Add map controls for zoom, pan, and layer toggles

#### 4.3 Location Services
- **Backend Integration:**
  - Store Google Maps API keys securely in environment variables
  - Create service classes for Google Maps API calls
  - Implement geocoding for address-to-coordinates conversion
  - Add reverse geocoding for coordinates-to-address

### Phase 5: Route Optimization & Directions
**Priority:** High  
**Estimated Timeline:** 4-5 weeks

#### 5.1 Google Directions Integration
- **Features:**
  - Calculate optimal routes between pickup and delivery points
  - Consider real-time traffic data
  - Support for multiple waypoints
  - Route alternatives with cost/time comparisons

#### 5.2 Route Optimization Service
- **Backend Development:**
  - Implement optimization algorithms using Neo4j graph traversal
  - Integration with Google Directions API
  - Consider constraints:
    - Vehicle capacity
    - Driver hours of service
    - Time windows for pickup/delivery
    - Traffic patterns

#### 5.3 Kafka Event Integration
- **Event Handling:**
  - `ROUTE_OPTIMIZATION_REQUESTED` → Trigger optimization process
  - `ROUTE_OPTIMIZED` → Update Neo4j relationships and notify UI
  - `ROUTE_DEVIATION` → Recalculate and suggest alternative routes
  - `VEHICLE_LOCATION_UPDATED` → Update ETA calculations

### Phase 6: System Integration & Testing
**Priority:** Medium  
**Estimated Timeline:** 2-3 weeks

#### 6.1 End-to-End Testing
- **Test Scenarios:**
  - Complete load lifecycle from creation to delivery
  - Route optimization with multiple vehicles and loads
  - Real-time event propagation across all components
  - Google Maps integration with live traffic data

#### 6.2 Performance Optimization
- **Areas of Focus:**
  - Database query optimization
  - Kafka message processing efficiency
  - Frontend rendering performance
  - Google Maps API usage optimization

#### 6.3 Error Handling & Resilience
- **Improvements:**
  - Graceful degradation when external APIs are unavailable
  - Retry mechanisms for failed operations
  - Comprehensive error logging and monitoring
  - User-friendly error messages

## Technical Considerations

### Security
- Secure storage of Google Maps API keys
- Input validation for all assignment operations
- Rate limiting for API endpoints
- Authentication for sensitive operations

### Performance
- Implement caching for frequently accessed route data
- Optimize Neo4j queries for large datasets
- Use WebSocket connection pooling
- Implement lazy loading for map components

### Scalability
- Design for horizontal scaling of backend services
- Consider Kafka partitioning strategies
- Implement database connection pooling
- Plan for multi-region deployment

## Dependencies & Prerequisites

### External Services
- Google Cloud Platform account with billing enabled
- Google Maps API quota and rate limits
- Neo4j database with sufficient memory allocation

### Development Environment
- Docker and Docker Compose
- Node.js 18+ for frontend development
- Python 3.11+ for backend development
- Kafka cluster (already configured)

## Success Metrics

### Analytics Dashboard
- Real-time data updates with <5 second latency
- Support for date range filtering
- Interactive charts with drill-down capability

### Neo4j Integration
- All business actions result in proper graph relationships
- Graph queries execute in <1 second for typical use cases
- Relationship integrity maintained across all operations

### Dispatch Board
- Load assignment workflow completion in <30 seconds
- Real-time updates visible within 2 seconds
- Support for drag-and-drop assignment operations

### Google Maps Integration
- Map loads in <3 seconds with real-time vehicle positions
- Route calculations complete in <10 seconds
- Accurate ETA calculations with traffic consideration

### Route Optimization
- Optimization algorithms process multiple loads/vehicles in <60 seconds
- Integration with Kafka events for automated optimization triggers
- Measurable improvement in route efficiency (distance/time reduction)

## Risk Assessment

### High Risk
- Google Maps API costs and quota limits
- Complex route optimization algorithm performance
- Real-time data synchronization across all components

### Medium Risk
- Neo4j learning curve for complex graph queries
- WebSocket connection stability under load
- Frontend performance with large datasets

### Low Risk
- Analytics dashboard data integration
- Load assignment UI development
- Basic Google Maps integration

## Next Steps

1. **Immediate (Week 1-2):** Begin Phase 1 - Analytics Dashboard Enhancement
2. **Short-term (Week 3-5):** Start Phase 2 - Neo4j Relationship Population
3. **Medium-term (Week 6-8):** Initiate Phase 4 - Google Maps Integration (parallel with Phase 3)
4. **Long-term (Week 9-13):** Phase 5 - Route Optimization & Phase 6 - Integration Testing

## Conclusion

This roadmap provides a structured approach to completing the TMS implementation with a focus on data integrity, real-time functionality, and user experience. The phased approach allows for iterative development and testing while building upon the solid foundation already established in the system.
