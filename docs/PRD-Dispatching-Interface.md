# Product Requirements Document (PRD)
## TMS Dispatching Interface

**Version:** 1.0  
**Date:** July 2, 2025  
**Authors:** Product Team  
**Tags:** #product-requirements #TMS-Frontend #dispatching #status/implemented #priority/high #real-time
**Related:** [[PRD-Overview]] | [[SPEC-Backend-System]] | [[SPEC-Events-Schema]] | [[SPEC-Route-Optimization-Setup]]
**Dependencies:** [[SPEC-Backend-System]], [[SPEC-Events-Schema]]
**Features:** Google Maps integration, route optimization, real-time tracking, gamification

---

## 1. Executive Summary

### 1.1 Product Overview
The TMS Dispatching Interface serves as a learning platform for building modern, real-time logistics interfaces. Starting with basic load and vehicle management capabilities, the system demonstrates progressive enhancement toward a comprehensive, gamified dispatching experience with Google Maps integration.

### 1.2 Learning Objectives
- **Real-time UI Development**: Build responsive interfaces with live event updates
- **Complex State Management**: Handle multiple data streams and user interactions
- **Maps Integration**: Learn Google Maps API integration patterns (planned)
- **Gamification Design**: Implement engaging UX patterns for operational software
- **Event-Driven UI**: Master WebSocket integration and real-time data handling

### 1.3 Implementation Status
**Currently Implemented ✅:**
- **Basic Dispatch View**: Simple map placeholder with event console
- **Load Management**: Create, assign, and track load lifecycle
- **Vehicle Tracking**: Real-time location updates and status monitoring
- **Event Console**: Live event streaming with categorization and filtering
- **WebSocket Integration**: Real-time data flow from backend to UI

**🚨 CRITICAL PRIORITY - ROUTE VISUALIZATION 🚨:**
- **Street-Level Route Geometry**: MUST display optimized routes with precise street-level geometry
- **Real-Time Route Updates**: Live route modifications based on traffic and conditions
- **Interactive Route Elements**: Clickable routes with detailed information overlays
- **Multiple Route Display**: Simultaneous visualization of multiple active routes
- **Route Performance Metrics**: Visual indicators for efficiency, delays, and optimization scores

**Planned Development 📋:**
- **Google Maps Integration**: Interactive mapping with vehicle/load visualization
- **Gamification Features**: Points, achievements, and engagement mechanics  
- **Mobile-Responsive Design**: Tablet and mobile dispatcher interfaces
- **Advanced Assignment Logic**: AI-powered load-to-vehicle matching

---

## 2. Goals & Success Metrics

### 2.1 Business Goals
- **Operational Efficiency**: Reduce dispatch response time by 40%
- **Proactive Management**: Increase preventive interventions by 60%
- **Cost Reduction**: Decrease operational costs through optimized resource allocation
- **Customer Satisfaction**: Improve on-time delivery rates by 25%

### 2.2 Success Metrics
- **Event Response Time**: Average time from event occurrence to dispatcher action
- **Issue Resolution Rate**: Percentage of issues resolved before customer impact
- **System Adoption**: Daily active dispatcher usage rates
- **Operational KPIs**: Load completion rates, vehicle utilization, driver satisfaction

---

## 3. User Personas & Use Cases

### 3.1 Primary Users

#### Lead Dispatcher
- **Role**: Oversees all dispatch operations, handles escalations
- **Needs**: System-wide visibility, performance analytics, resource optimization
- **Pain Points**: Information silos, reactive problem-solving

#### Operations Dispatcher
- **Role**: Manages day-to-day load assignments and driver coordination
- **Needs**: Real-time status updates, exception handling, communication tools
- **Pain Points**: Manual status tracking, delayed notifications

#### Customer Service Representative
- **Role**: Provides updates to customers, handles inquiries
- **Needs**: Accurate load status, ETA information, proactive alerts
- **Pain Points**: Inconsistent information, delayed updates

### 3.2 Key Use Cases

#### UC1: Real-Time Load Monitoring
- **Actor**: Operations Dispatcher
- **Goal**: Monitor all active loads and respond to status changes
- **Flow**: View load dashboard → Receive real-time updates → Take corrective actions
- **Events**: `load.created`, `load.assigned`, `load.picked_up`, `load.in_transit`, `load.delivered`

#### UC2: Vehicle Exception Handling
- **Actor**: Lead Dispatcher
- **Goal**: Identify and resolve vehicle-related issues before they impact operations
- **Flow**: Receive vehicle alert → Assess situation → Coordinate resolution
- **Events**: `vehicle.status_changed`, `vehicle.maintenance_due`, `vehicle.location_updated`

#### UC3: Route Optimization Management
- **Actor**: Operations Dispatcher
- **Goal**: Monitor route performance and handle deviations
- **Flow**: Review optimized routes → Monitor execution → Handle deviations
- **Events**: `route.optimized`, `route.deviation`, `route.completed`

---

## 4. Functional Requirements

### 4.1 Event Monitoring & Display

#### 4.1.1 Real-Time Event Dashboard
- **Display all event types** from the TMS event system:
  - Load Events: Created, Assigned, Picked Up, In Transit, Delivered, Cancelled
  - Vehicle Events: Location Updates, Status Changes, Maintenance Due
  - Driver Events: Status Changes, Location Updates, HOS Violations
  - Route Events: Optimized, Deviations, Completed
  - Carrier Events: Performance Updates, Capacity Changes
  - System Events: Alerts, AI Predictions

#### 4.1.2 Event Filtering & Search
- Filter by event type, source, time range, priority level
- Search by load ID, vehicle ID, driver ID, correlation ID
- Saved filter configurations for common workflows

#### 4.1.3 Event Prioritization
- Automatic priority assignment based on business impact
- Color-coded visual indicators (Critical, High, Medium, Low)
- Escalation workflows for unhandled high-priority events

### 4.2 Operational Workflows

#### 4.2.1 Load Management Workflow
- **Load Creation**: Validate load details, assign optimal carrier/driver
- **Load Tracking**: Real-time status updates, ETA calculations
- **Exception Handling**: Delayed pickups, delivery issues, customer changes

#### 4.2.2 Vehicle & Driver Coordination
- **Resource Assignment**: Match vehicles/drivers to loads based on availability, location, capacity
- **Status Monitoring**: Track driver hours, vehicle maintenance, location updates
- **Compliance Management**: HOS violations, DOT requirements, safety alerts

#### 4.2.3 Route Optimization Integration
- **Route Review**: Validate AI-optimized routes before execution
- **Deviation Management**: Handle route changes, traffic impacts, customer requests
- **Performance Tracking**: Monitor route efficiency, fuel consumption, on-time performance

### 4.3 Communication & Collaboration

#### 4.3.1 Notification System
- Real-time alerts for critical events
- Configurable notification preferences (email, SMS, in-app)
- Escalation chains for unacknowledged alerts

#### 4.3.2 Driver Communication
- Direct messaging integration
- Load instruction delivery
- Status update requests

#### 4.3.3 Customer Updates
- Automated delivery notifications
- Proactive delay communications
- Self-service tracking links

### 4.4 Analytics & Reporting

#### 4.4.1 Operational Dashboards
- Key performance indicators (KPIs) visualization
- Real-time metrics: active loads, available vehicles, driver utilization
- Trend analysis and historical comparisons

#### 4.4.2 Performance Analytics
- Carrier performance scorecards
- Route efficiency analysis
- Driver productivity metrics

---

## 5. Technical Requirements

### 5.1 Event Integration

#### 5.1.1 Kafka Topic Subscription
- Subscribe to all TMS Kafka topics:
  - `tms.loads`, `tms.vehicles`, `tms.vehicles.tracking`
  - `tms.drivers`, `tms.drivers.tracking`, `tms.drivers.compliance`
  - `tms.routes`, `tms.routes.alerts`
  - `tms.carriers`, `tms.system.alerts`, `tms.ai.predictions`

#### 5.1.2 Event Processing
- Real-time event consumption and processing
- Event correlation and relationship mapping
- State management for multi-step workflows

#### 5.1.3 WebSocket Integration  
- Real-time UI updates via WebSocket connections
- Event broadcasting to multiple connected clients
- Connection management and reconnection handling

### 5.2 Data Architecture

#### 5.2.1 Database Integration
- **PostgreSQL**: Core operational data (loads, vehicles, drivers)
- **TimescaleDB**: Time-series data (locations, metrics, performance)
- **Neo4j**: Relationship mapping (carrier networks, route optimization)

#### 5.2.2 Caching Strategy
- Redis integration for session management and temporary data
- Event buffering for high-throughput scenarios
- Performance optimization for real-time queries

### 5.3 API Requirements

#### 5.3.1 REST API Integration
- Leverage existing FastAPI endpoints
- Load management: Create, update, assign loads
- Vehicle tracking: Location updates, status changes
- Driver management: Status updates, communication

#### 5.3.2 Event Publishing
- Manual event publishing for testing and corrections
- Bulk event operations for batch processing
- Event replay capabilities for troubleshooting

### 5.4 Security & Compliance

#### 5.4.1 Authentication & Authorization
- Role-based access control (RBAC)
- Single sign-on (SSO) integration
- API key management for system integrations

#### 5.4.2 Audit & Compliance
- Complete audit trail for all dispatch actions
- Compliance reporting for DOT regulations
- Data retention policies for historical events

---

## 6. User Experience Design

### 6.1 Interface Layout

#### 6.1.1 Primary Dashboard
- **Event Stream Panel**: Real-time event feed with filtering
- **Operations Overview**: Key metrics and system status
- **Quick Actions**: Common dispatch operations
- **Alert Center**: Critical notifications and escalations

#### 6.1.2 Detailed Views
- **Load Detail**: Complete load lifecycle and documentation
- **Vehicle Dashboard**: Fleet status, locations, maintenance
- **Driver Portal**: Driver status, communications, compliance
- **Route Planner**: Route visualization and optimization tools

### 6.2 Workflow Design

#### 6.2.1 Event-Driven Workflows
- Context-aware interfaces that adapt to current events
- Guided workflows for complex multi-step operations
- Intelligent suggestions based on historical patterns

#### 6.2.2 Mobile Responsiveness
- Tablet-optimized interface for mobile dispatching
- Essential functionality available on mobile devices
- Offline capability for critical operations

---

## 7. Integration Requirements

### 7.1 System Integrations

#### 7.1.1 TMS Core Systems
- Load management system integration
- Vehicle tracking system connectivity
- Driver mobile app integration
- Customer portal synchronization

#### 7.1.2 External Systems
- ELD (Electronic Logging Device) integration
- Carrier TMS systems via API
- Customer systems for automated updates
- Financial systems for billing automation

### 7.2 Data Synchronization

#### 7.2.1 Real-Time Sync
- Event-driven data updates across all systems
- Conflict resolution for concurrent updates
- Data consistency validation and correction

#### 7.2.2 Batch Processing
- Scheduled data reconciliation
- Historical data import/export
- Backup and disaster recovery procedures

---

## 8. Performance Requirements

### 8.1 System Performance
- **Event Processing**: Handle 10,000+ events per minute
- **Response Time**: UI updates within 100ms of event occurrence
- **Concurrent Users**: Support 50+ simultaneous dispatchers
- **Uptime**: 99.9% availability during business hours

### 8.2 Scalability
- Horizontal scaling for increased event volume
- Load balancing for multiple dispatcher workstations
- Geographic distribution for multi-location operations

---

## 9. Implementation Phases

### 9.1 Phase 1: Core Event Monitoring (Weeks 1-4)
- Basic event dashboard implementation
- Real-time event streaming integration
- Essential filtering and search capabilities
- Basic notification system

### 9.2 Phase 2: Operational Workflows (Weeks 5-8)
- Load management workflow implementation
- Vehicle and driver coordination features
- Route optimization integration
- Communication tools

### 9.3 Phase 3: Advanced Features (Weeks 9-12)
- Analytics and reporting dashboards
- Mobile interface development
- Advanced automation and AI integration
- Performance optimization

### 9.4 Phase 4: Integration & Launch (Weeks 13-16)
- External system integrations
- User training and change management
- Production deployment and monitoring
- Performance tuning and optimization

---

## 10. Success Criteria & Testing

### 10.1 Acceptance Criteria
- All 22 event types properly displayed and actionable
- Real-time updates with <2 second latency
- 95% user adoption within 30 days of launch
- Zero critical bugs in production

### 10.2 Testing Strategy
- Unit testing for all event processing logic
- Integration testing with Kafka and database systems
- Performance testing under peak load conditions
- User acceptance testing with dispatcher teams

---

## 11. Risks & Mitigation

### 11.1 Technical Risks
- **Event Volume Overload**: Implement event buffering and prioritization
- **System Integration Complexity**: Phased rollout with fallback procedures
- **Real-Time Performance**: Caching strategies and connection optimization

### 11.2 Operational Risks
- **User Adoption**: Comprehensive training and change management
- **Business Continuity**: Maintain existing systems during transition
- **Data Quality**: Validation and cleansing procedures

---

## 12. Appendices

### 12.1 Event Schema Reference
```json
{
  "event_id": "uuid",
  "event_type": "load.created|vehicle.location_updated|...",
  "timestamp": "ISO 8601",
  "source": "tms-api|tracking-service|...",
  "correlation_id": "optional uuid",
  "data": {...},
  "metadata": {...}
}
```

### 12.2 Kafka Topic Mapping
- **Load Events** → `tms.loads`
- **Vehicle Tracking** → `tms.vehicles.tracking`
- **Driver Events** → `tms.drivers`, `tms.drivers.tracking`
- **Route Events** → `tms.routes`, `tms.routes.alerts`
- **System Events** → `tms.system.alerts`, `tms.ai.predictions`

### 12.3 Database Schema Requirements
- Event correlation tables for tracking related events
- Dispatcher action logs for audit trails
- Performance metrics storage for analytics
- Configuration tables for user preferences