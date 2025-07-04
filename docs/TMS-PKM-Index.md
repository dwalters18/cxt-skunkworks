# TMS Knowledge Management Index

**Document Type:** PKM Index
**Created:** 2025-01-03
**Tags:** #TMS-Core #PKM-index
**Status:** #status/implemented

## 📋 Core System Architecture

### Primary PRDs
- [[PRD-Overview]] - System overview and high-level architecture #TMS-Core
- [[PRD-Backend-System]] - Backend services and API architecture #TMS-Backend
- [[PRD-Database-Schema]] - Data models and persistence layer #TMS-Data
- [[PRD-Events-Schema]] - Event-driven architecture specification #TMS-Events

## 🎯 User Interfaces & Experience

### Frontend Components
- [[PRD-Dispatching-Interface]] - Dispatch operations and UI #TMS-Frontend #dispatching

## 📊 Data & Analytics

### Data Management
- [[PRD-Polyglot-Persistence]] - Multi-database architecture #TMS-Data #polyglot-persistence
- [[PRD-Real-time-Analytics]] - Analytics and reporting systems #TMS-Analytics #real-time
- [[PRD-Stream-Processing]] - Event streaming and processing #TMS-Events #streaming

## 🤖 Intelligence & Optimization

### AI/ML Components
- [[PRD-Machine-Learning]] - ML models and AI features #TMS-ML
- [[Route-Optimization-Setup]] - Route optimization implementation #route-optimization #TMS-Backend

## 🔧 Implementation & Operations

### Technical Documentation
- [[TMS-Object-Relationships]] - Object model relationships #TMS-Data
- [[ROADMAP]] - Development roadmap and milestones #TMS-Core
- [[DATABASE-UI-ACCESS]] - Database access and UI tools #TMS-Infrastructure

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
PRD-Overview ──► PRD-Backend-System
             ├─► PRD-Database-Schema  
             └─► PRD-Events-Schema

PRD-Backend-System ──► PRD-Polyglot-Persistence
                   └─► Route-Optimization-Setup

PRD-Database-Schema ──► TMS-Object-Relationships
                    └─► PRD-Real-time-Analytics

PRD-Events-Schema ──► PRD-Stream-Processing
                  └─► PRD-Real-time-Analytics
```

### Cross-Component Integration
- **Dispatching Interface** ↔ **Backend System** ↔ **Real-time Analytics**
- **Machine Learning** ↔ **Route Optimization** ↔ **Stream Processing**  
- **Database Schema** ↔ **Polyglot Persistence** ↔ **Events Schema**

## 📚 Quick Navigation

### By Development Phase
- **Architecture**: [[PRD-Overview]], [[PRD-Backend-System]], [[PRD-Database-Schema]]
- **Data Layer**: [[PRD-Polyglot-Persistence]], [[PRD-Events-Schema]], [[TMS-Object-Relationships]]
- **Processing**: [[PRD-Stream-Processing]], [[PRD-Real-time-Analytics]]
- **Intelligence**: [[PRD-Machine-Learning]], [[Route-Optimization-Setup]]
- **User Experience**: [[PRD-Dispatching-Interface]]

### By Priority
- **High Priority**: Route optimization, Real-time analytics, Dispatching interface
- **Medium Priority**: Machine learning, Stream processing
- **Future**: Advanced analytics, Extended ML features

---

*This index is automatically maintained through Obsidian's linking system. Cross-references and backlinks will show related documents.*
