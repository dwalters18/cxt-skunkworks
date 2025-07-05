# TMS Knowledge Management Index

**Document Type:** PKM Index
**Created:** 2025-01-03
**Updated:** 2025-07-05
**Tags:** #TMS-Core #PKM-index
**Status:** #status/implemented

---

## 📋 Product Requirements Documents (PRDs)
*Business requirements, objectives, and product vision*

### Core Business Requirements
- [[PRD-Overview]] - System overview and high-level architecture #product-requirements #TMS-Core
- [[PRD-Dispatching-Interface]] - Dispatch operations and user interface requirements #product-requirements #TMS-Frontend #dispatching

---

## 🔧 Technical Specifications (SPECs)
*Implementation details, system design, and technical architecture*

### Backend & Infrastructure
- [[SPEC-Backend-System]] - Backend services and API architecture #technical-spec #TMS-Backend
- [[SPEC-Database-Schema]] - Data models and persistence layer #technical-spec #TMS-Data
- [[SPEC-Polyglot-Persistence]] - Multi-database architecture #technical-spec #TMS-Data #polyglot-persistence
- [[SPEC-Object-Relationships]] - Object model relationships #technical-spec #TMS-Data

### Event-Driven Architecture
- [[SPEC-Events-Schema]] - Event-driven architecture specification #technical-spec #TMS-Events
- [[SPEC-Stream-Processing]] - Event streaming and processing #technical-spec #TMS-Events #streaming
- [[SPEC-Real-time-Analytics]] - Analytics and reporting systems #technical-spec #TMS-Analytics #real-time

### Frontend & User Experience
- [[SPEC-Frontend-Application]] - Frontend application architecture #technical-spec #TMS-Frontend
- [[SPEC-Route-Optimization-Setup]] - Route optimization implementation #technical-spec #route-optimization #TMS-Backend

### AI & Machine Learning
- [[SPEC-Machine-Learning]] - ML models and AI features #technical-spec #TMS-ML

---

## 📋 Project Management & Operations

### Planning & Documentation
- [[ROADMAP]] - Development roadmap and milestones #TMS-Core
- [[DATABASE-UI-ACCESS]] - Database access and UI tools #TMS-Infrastructure
- [[PKM-Setup-Guide]] - PKM system setup and usage guide #PKM-setup

## 📈 Development Status Overview

### Implemented Features #status/implemented
```dataview
LIST
FROM #status/implemented
WHERE contains(file.name, "PRD")
```

### In Progress #status/in-progress
```dataview
LIST
FROM #status/in-progress
WHERE contains(file.name, "PRD")
```

### Planned Features #status/planned
```dataview
LIST  
FROM #status/planned
WHERE contains(file.name, "PRD")
```

## 🏷️ Tag Categories

### System Categories
- **#TMS-Core** - Core system components
- **#TMS-Backend** - Backend services and APIs
- **#TMS-Frontend** - User interfaces
- **#TMS-Data** - Data models and persistence
- **#TMS-Events** - Event-driven architecture
- **#TMS-ML** - Machine learning components
- **#TMS-Analytics** - Analytics and reporting
- **#TMS-Infrastructure** - Infrastructure and ops

### Feature Tags
- **#route-optimization** - Route optimization features
- **#real-time** - Real-time processing
- **#polyglot-persistence** - Multi-database architecture
- **#dispatching** - Dispatching workflows
- **#streaming** - Stream processing

### Status Tags
- **#status/implemented** - Completed features
- **#status/in-progress** - Active development
- **#status/planned** - Future development

### Priority Tags
- **#priority/high** - Critical items
- **#priority/medium** - Standard priority
- **#priority/low** - Future enhancements

## 🔗 Relationship Map

### Core Dependencies
```
PRD-Overview ──► SPEC-Backend-System
             ├─► SPEC-Database-Schema  
             └─► SPEC-Events-Schema

SPEC-Backend-System ──► SPEC-Polyglot-Persistence
                   └─► SPEC-Route-Optimization-Setup

SPEC-Database-Schema ──► SPEC-Object-Relationships
                     └─► SPEC-Real-time-Analytics

SPEC-Events-Schema ──► SPEC-Stream-Processing
                   └─► SPEC-Real-time-Analytics
```

### Cross-Component Integration
- **Dispatching Interface** ↔ **Backend System** ↔ **Real-time Analytics**
- **Machine Learning** ↔ **Route Optimization** ↔ **Stream Processing**  
- **Database Schema** ↔ **Polyglot Persistence** ↔ **Events Schema**

## 📚 Quick Navigation

### By Development Phase
- **Architecture**: [[PRD-Overview]], [[SPEC-Backend-System]], [[SPEC-Database-Schema]]
- **Data Layer**: [[SPEC-Polyglot-Persistence]], [[SPEC-Events-Schema]], [[SPEC-Object-Relationships]]
- **Processing**: [[SPEC-Stream-Processing]], [[SPEC-Real-time-Analytics]]
- **Intelligence**: [[SPEC-Machine-Learning]], [[SPEC-Route-Optimization-Setup]]
- **User Experience**: [[PRD-Dispatching-Interface]]

### By Priority
- **High Priority**: Route optimization, Real-time analytics, Dispatching interface
- **Medium Priority**: Machine learning, Stream processing
- **Future**: Advanced analytics, Extended ML features

---

*This index is automatically maintained through Obsidian's linking system. Cross-references and backlinks will show related documents.*
