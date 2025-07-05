# Product Requirements Document (PRD)
## TMS Frontend Application

**Version:** 1.0  
**Date:** July 4, 2025  
**Authors:** Development Team  
**Tags:** #TMS-Frontend #UI-UX #route-optimization #status/active #priority/high #react
**Related:** [[PRD-Dispatching-Interface]] | [[PRD-Backend-System]] | [[PRD-Events-Schema]]
**Dependencies:** [[PRD-Backend-System]], Google Maps API, React ecosystem
**Features:** Route optimization UI, Google Maps integration, component architecture, SaaS navigation

---

## 1. Executive Summary

### 1.1 Product Overview
The TMS Frontend Application is a React-based single-page application that provides dispatchers with a comprehensive interface for managing loads, vehicles, drivers, and route optimization. The application emphasizes real-time data visualization, intuitive user workflows, and scalable component architecture.

### 1.2 Current Implementation Status
**Recently Completed ✅:**
- **Route Optimization Workflow**: Complete end-to-end route optimization with validation
- **Load & Vehicle Selection**: Enforced UI validation before route optimization
- **WKT LINESTRING Parsing**: Backend route geometry integration and visualization
- **Google Maps Integration**: Interactive map with route rendering and load markers
- **Real-time Updates**: WebSocket integration for live event streaming
- **Validation & Error Handling**: Comprehensive user feedback and error recovery

**Next Phase 📋:**
- **Component Architecture Refactoring**: Break down monolithic components
- **Navigation & SaaS Structure**: Professional navigation bar and app layout
- **Mobile Responsiveness**: Tablet and mobile optimization
- **Advanced UI Components**: Reusable component library

---

## 2. Route Optimization Feature Requirements

### 2.1 User Workflow
**Current Implemented Workflow:**
1. **Load Discovery**: User views loads on interactive map
2. **Load Selection**: Click on load marker to open InfoWindow
3. **Vehicle Selection**: Required dropdown selection from available vehicles
4. **Validation**: UI enforces vehicle selection before enabling optimization
5. **Route Optimization**: API call to `/api/routes/optimize-load` endpoint
6. **Results Display**: Route geometry, metrics, and optimization score shown
7. **Map Visualization**: Optimized route rendered as polyline on map

**Business Rules:**
- Cannot optimize route without selecting a vehicle
- Must have valid load and vehicle IDs before API call
- Loading states prevent multiple simultaneous optimizations
- Success/error feedback provided to user
- Route metrics displayed: distance, duration, optimization score

### 2.2 Technical Implementation

**Frontend Components:**
- `DispatchMapView.js`: Main component (needs refactoring)
- Google Maps integration via `@react-google-maps/api`
- Route geometry parsing from WKT LINESTRING format
- State management for optimized routes and UI interactions

**API Integration:**
- `POST /api/routes/optimize-load`: Route optimization endpoint
- `GET /api/routes/{route_id}`: Route details retrieval
- Environment variable: `REACT_APP_BACKEND_URL`
- Error handling and retry logic

**Data Flow:**
```
Load Selection → Vehicle Selection → Validation → API Call → 
Route Details Fetch → WKT Parsing → Map Rendering → User Feedback
```

### 2.3 UI/UX Requirements

**Visual Design:**
- Load markers with status-based colors
- Vehicle selection dropdown in InfoWindow
- Disabled/enabled states for optimization button
- Loading spinners during API calls
- Success messages with route metrics
- Route polylines with optimization indicators

**User Experience:**
- Clear validation messages
- Intuitive selection workflow
- Immediate visual feedback
- Error recovery options
- Achievement notifications for high optimization scores

---

## 3. Component Architecture Requirements

### 3.1 Current State Analysis
**DispatchMapView.js Issues:**
- 800+ lines in single component
- Mixed concerns: data fetching, UI rendering, business logic
- State management complexity
- Difficult to test and maintain
- No separation between map logic and data management

### 3.2 Proposed Component Structure

**Container Components:**
- `DispatchDashboard`: Main layout and navigation
- `MapContainer`: Google Maps integration and route rendering
- `LoadManagement`: Load data fetching and state management
- `VehicleManagement`: Vehicle data fetching and operations

**Presentation Components:**
- `LoadInfoWindow`: Load details and vehicle selection UI
- `RouteOptimizationPanel`: Route metrics and controls
- `MapMarker`: Reusable marker component
- `VehicleSelector`: Dropdown component for vehicle selection
- `RoutePolyline`: Route visualization component

**Utility Components:**
- `LoadingSpinner`: Reusable loading indicator
- `ErrorBoundary`: Error handling wrapper
- `ToastNotification`: Success/error messages
- `AchievementNotification`: Gamification feedback

**Custom Hooks:**
- `useMapData`: Load and vehicle data management
- `useRouteOptimization`: Route optimization logic
- `useWebSocket`: Real-time event handling
- `useCoordinateParsing`: WKT LINESTRING parsing

### 3.3 Data Flow Architecture

**State Management:**
- Context API for global application state
- Local state for component-specific data
- Custom hooks for business logic
- Optimistic updates for better UX

**API Layer:**
- Centralized API service functions
- Error handling and retry logic
- Response transformation utilities
- Environment-based configuration

---

## 4. SaaS Application Structure Requirements

### 4.1 Navigation Requirements - **IMPLEMENTED**

**Navigation Bar Structure:**
- **Brand Section**: CXT Dispatch logo with animated truck icon
- **Primary Navigation**: 
  - 🎯 **Dispatch Command** (primary focus, gamified styling with pulse animation)
  - 📊 **Dashboard** (KPI overview and quick actions)
  - 📈 **Analytics** (performance insights and data visualization)
- **Management Dropdown**: ⚡ Management with hover/click access to:
  - 📦 **Load Management** (load creation and tracking)
  - 🚛 **Fleet Management** (vehicle monitoring and management)
  - 👥 **Driver Management** (driver profiles and scheduling)
  - ⚙️ **Settings** (system configuration and preferences)
- **User Section**: 👨‍💼 Dispatcher profile with avatar

**Design Features:**
- Gradient blue background (blue-800 to blue-600)
- Sticky navigation bar with shadow and border
- Hover effects with scale transforms and color transitions
- Active state indicators with yellow accent colors
- Responsive design with mobile breakpoints
- Dropdown animations with smooth transitions

**Routing Structure:**
- React Router v6 implementation
- AppLayout wrapper with Outlet for nested routes
- Primary route: `/` → DispatchPage (main gamified interface)
- Management routes: `/loads`, `/fleet`, `/drivers`, `/settings`
- Analytics routes: `/dashboard`, `/analytics`

### 4.2 Gamified Dispatching Interface - **IMPLEMENTED**

**DispatchPage Structure:**
- **Gamified Header**: 
  - Animated 🎯 target icon with bounce effect
  - "Dispatch Command Center" title with mission-focused messaging
  - Real-time performance stats: Score, Routes Optimized, Active Loads
  - Gradient background with game-like aesthetics
- **Main Interface**: Full-screen DispatchMapView integration
- **Performance Metrics**: Live gamification stats with colored indicators

**Page Structure Implemented:**
- **DashboardPage**: KPI cards, quick actions, performance overview
- **AnalyticsPage**: Chart placeholders and data visualization areas
- **LoadsPage**: Load management interface with add/edit capabilities
- **FleetPage**: Vehicle tracking and fleet management tools
- **DriversPage**: Driver profiles and scheduling management
- **SettingsPage**: System configuration and user preferences

**AppLayout Structure:**
- **NavigationBar**: Sticky header with all navigation elements
- **Main Content**: Outlet for route-specific page content
- **Status Bar**: System status indicators and version info

**Primary Navigation:**
- Dashboard: Overview and metrics
- Dispatch: Map view and route optimization
- Loads: Load management interface
- Fleet: Vehicle and driver management
- Analytics: Reports and insights
- Settings: Configuration and preferences

**Navigation Features:**
- Persistent navigation bar
- Active route highlighting
- Breadcrumb navigation for deep pages
- Mobile-responsive hamburger menu
- Search functionality
- Quick actions menu

### 4.2 Layout Structure

**Application Shell:**
```
┌─────────────────────────────────┐
│ Navigation Bar                  │
├─────────────────────────────────┤
│ Breadcrumbs                     │
├─────────────────────────────────┤
│                                 │
│ Main Content Area               │
│ (Route-specific components)     │
│                                 │
├─────────────────────────────────┤
│ Status Bar / Notifications      │
└─────────────────────────────────┘
```

**Responsive Design:**
- Desktop: Full navigation sidebar
- Tablet: Collapsible navigation
- Mobile: Bottom navigation tabs
- Breakpoints: 768px, 1024px, 1440px

### 4.3 Professional UI Standards

**Design System:**
- Consistent color palette
- Typography hierarchy
- Component library (buttons, inputs, cards)
- Icon system
- Spacing and layout grid

**Accessibility:**
- WCAG 2.1 AA compliance
- Keyboard navigation
- Screen reader support
- High contrast mode
- Focus management

---

## 5. Technical Specifications

### 5.1 Technology Stack
- **Framework**: React 18+ with functional components
- **State Management**: Context API + custom hooks
- **Routing**: React Router v6
- **Maps**: Google Maps API via @react-google-maps/api
- **Styling**: Tailwind CSS ONLY (NO custom CSS files allowed)
- **Build Tool**: Create React App or Vite
- **Testing**: Jest + React Testing Library

### 5.2 Performance Requirements
- Initial load time: < 3 seconds
- Map rendering: < 1 second
- Route optimization response: < 2 seconds
- Component re-render optimization
- Lazy loading for route components
- Image optimization and CDN usage

### 5.3 Environment Configuration
```javascript
// Required Environment Variables
REACT_APP_BACKEND_URL=http://localhost:8000
REACT_APP_GOOGLE_MAPS_API_KEY=your_api_key
REACT_APP_WEBSOCKET_URL=ws://localhost:8000/ws
REACT_APP_ENVIRONMENT=development|staging|production
```

---

## 6. Data Integration Requirements

### 6.1 WKT LINESTRING Parsing
**Technical Implementation:**
- Parse backend route geometry in WKT format
- Convert to Google Maps coordinate objects
- Handle coordinate validation and filtering
- Support for complex route geometries

**Example Data Flow:**
```javascript
// Backend Response
"route_geometry": "LINESTRING(-96.79608 32.77689,-96.78086 32.77948,...)"

// Parsed for Google Maps
[
  { lat: 32.77689, lng: -96.79608 },
  { lat: 32.77948, lng: -96.78086 },
  // ...
]
```

### 6.2 Real-time Data Integration
- WebSocket connection for live updates
- Event-driven UI updates
- Optimistic updates for user actions
- Conflict resolution for concurrent edits
- Offline capability (future requirement)

---

## 7. User Experience Requirements

### 7.1 Route Optimization UX
**Workflow Steps:**
1. **Discovery**: Visual load identification on map
2. **Selection**: Single-click load selection
3. **Configuration**: Vehicle selection with validation
4. **Execution**: One-click route optimization
5. **Review**: Immediate results with visual feedback
6. **Action**: Accept/modify/retry options

**Feedback Mechanisms:**
- Progress indicators during optimization
- Success notifications with metrics
- Error messages with retry options
- Achievement badges for optimization scores >80%
- Historical optimization tracking

### 7.2 Gamification Elements
- **Points System**: Points for completed optimizations
- **Achievements**: Badges for milestones and excellence
- **Leaderboards**: Team performance tracking
- **Progress Tracking**: Daily/weekly optimization goals

---

## 8. Testing Requirements

### 8.1 Component Testing
- Unit tests for all utility functions
- Component tests for UI interactions
- Integration tests for API calls
- E2E tests for critical workflows

### 8.2 Route Optimization Testing
- Test cases for valid/invalid selections
- API integration testing
- WKT parsing edge cases
- Map rendering validation
- Error handling scenarios

---

## 9. Deployment & DevOps

### 9.1 Build Pipeline
- Automated testing on PR
- Build optimization and bundling
- Environment-specific configurations
- Docker containerization
- CDN deployment for static assets

### 9.2 Monitoring & Analytics
- User interaction tracking
- Performance metrics
- Error reporting (Sentry integration)
- Route optimization success rates
- User engagement metrics

---

## 10. Future Roadmap

### 10.1 Phase 2 Features
- **Multi-route Optimization**: Batch route processing
- **Driver Assignment**: Integrated driver selection
- **Real-time Tracking**: Live vehicle tracking on routes
- **Mobile App**: React Native companion app
- **Advanced Analytics**: Route performance insights

### 10.2 Phase 3 Features
- **AI/ML Integration**: Predictive route optimization
- **IoT Integration**: Real-time vehicle telemetry
- **Customer Portal**: External customer tracking
- **API Marketplace**: Third-party integrations

---

## 11. Success Metrics

### 11.1 Technical Metrics
- Component reusability: >80%
- Code coverage: >90%
- Performance score: >95 (Lighthouse)
- Accessibility score: >95 (Lighthouse)

### 11.2 User Experience Metrics
- Route optimization completion rate: >95%
- User task completion time: <30 seconds
- User satisfaction score: >4.5/5
- Error rate: <1%

### 11.3 Business Metrics
- Dispatcher productivity increase: >30%
- Route optimization adoption: >90%
- Customer satisfaction improvement: >25%
- Operational cost reduction: >15%

---

## 12. Risk Assessment

### 12.1 Technical Risks
- **Google Maps API Limits**: Rate limiting and cost management
- **Component Complexity**: Over-engineering small components
- **State Management**: Complex state synchronization issues
- **Performance**: Large dataset rendering on maps

### 12.2 Mitigation Strategies
- API usage monitoring and caching
- Progressive enhancement approach
- Comprehensive testing strategy
- Performance profiling and optimization

---

**Document Status:** Active Development  
**Next Review:** July 11, 2025  
**Stakeholders:** Development Team, Product Team, Operations Team
