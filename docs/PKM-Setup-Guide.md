# TMS Personal Knowledge Management (PKM) Setup Guide

**Tags:** #PKM-setup #TMS-Core #documentation #knowledge-management
**Created:** 2025-01-03
**Purpose:** Guide for using the TMS knowledge management system in Obsidian

## 🎯 Overview

This guide explains how to effectively use the Personal Knowledge Management (PKM) system set up for the TMS project documentation. The system is designed to provide powerful cross-referencing, tagging, and knowledge discovery capabilities.

## 🔧 Obsidian Configuration

### Required Community Plugins
The following plugins are configured and recommended:

1. **Dataview** - Dynamic content queries and lists
2. **Tag Wrangler** - Advanced tag management with colors
3. **Templater** - Template system for consistent document creation
4. **Obsidian Git** - Version control integration
5. **Mind Map** - Visual knowledge mapping
6. **Projects** - Project management views
7. **Kanban** - Task and status boards

### Installation
1. Open Obsidian Settings (⚙️)
2. Go to **Community plugins**
3. Turn off **Safe mode**
4. Browse and install the plugins listed above
5. Enable each plugin after installation

## 🏷️ Tagging System

### Primary Category Tags
- **#TMS-Core** - Core system components and architecture
- **#TMS-Backend** - Backend services, APIs, and system architecture  
- **#TMS-Frontend** - User interfaces and frontend components
- **#TMS-Data** - Data models, schemas, and persistence
- **#TMS-Events** - Event-driven architecture and real-time processing
- **#TMS-ML** - Machine learning and AI components
- **#TMS-Analytics** - Analytics, reporting, and business intelligence
- **#TMS-Infrastructure** - Infrastructure, deployment, and operations

### Feature-Specific Tags
- **#route-optimization** - Route optimization algorithms and services
- **#real-time** - Real-time data processing and streaming
- **#polyglot-persistence** - Multi-database architecture
- **#dispatching** - Dispatching workflows and interfaces
- **#streaming** - Stream processing and event streaming

### Status Tags
- **#status/implemented** - Features that have been implemented
- **#status/in-progress** - Features currently being developed
- **#status/planned** - Features planned for future development

### Priority Tags
- **#priority/high** - High priority items requiring immediate attention
- **#priority/medium** - Medium priority items
- **#priority/low** - Low priority items

## 🔗 Linking Conventions

### Document Headers
Each PRD document includes:
```markdown
**Tags:** #primary-category #feature-tags #status/current #priority/level
**Related:** [[Document1]] | [[Document2]] | [[Document3]]
**Dependencies:** [[Required-Doc1]], [[Required-Doc2]]
**Used By:** [[Dependent-Doc1]], [[Dependent-Doc2]]
```

### Cross-References
- Use `[[Document Name]]` for internal links
- Include **Related** section for loose associations
- Include **Dependencies** for required prerequisites
- Include **Used By** for documents that depend on this one

## 📋 Navigation

### Master Index
- **[[TMS-PKM-Index]]** - Central navigation hub for all PRD documents
- Contains dynamic queries showing documents by status and priority
- Includes relationship maps and quick navigation sections

### Starred Documents
The following documents are starred for quick access:
- 📋 [[TMS-PKM-Index]] - Central index
- 🏗️ [[PRD-Overview]] - System overview
- ⚙️ [[PRD-Backend-System]] - Backend architecture
- 🗃️ [[PRD-Database-Schema]] - Data models
- ⚡ [[PRD-Events-Schema]] - Event architecture
- 🎯 [[PRD-Dispatching-Interface]] - UI components
- 🛣️ [[Route-Optimization-Setup]] - Route optimization
- 📈 [[ROADMAP]] - Development roadmap

## 🎨 Visual Features

### Graph View
- **Cmd+Shift+G** to open the graph view
- Color-coded nodes by tag categories:
  - Blue: #TMS-Core
  - Green: #TMS-Backend  
  - Purple: #TMS-Data
  - Red: #TMS-Events
  - Pink: #TMS-Analytics
  - Orange: #route-optimization

### Tag Colors
Tags are color-coded for visual identification:
- **System Categories**: Blue family colors
- **Features**: Orange/Red family colors  
- **Status**: Green (implemented), Yellow (in-progress), Gray (planned)
- **Priority**: Red (high), Yellow (medium), Green (low)

## 📝 Templates

### PRD Template
Use `.obsidian/templates/PRD-Template.md` for new PRD documents:
- Standardized header with tags and relationships
- Consistent structure and sections
- Placeholder content and guidelines

### Quick Note Template
Use `.obsidian/templates/Quick-Note.md` for capturing ideas:
- Simple structure for rapid note-taking
- Automatic tagging and timestamps
- Links to related documents

## ⌨️ Keyboard Shortcuts

- **Cmd+T** - Open tag pane
- **Cmd+Shift+T** - Create tags from selection
- **Cmd+Shift+R** - Refresh dataview queries
- **Cmd+Shift+N** - Insert template
- **Cmd+Shift+G** - Open graph view

## 🔍 Search and Discovery

### Dynamic Queries
The PKM system includes several dataview queries:

#### By Status
```dataview
LIST
FROM #status/implemented
WHERE contains(file.name, "PRD")
```

#### By Priority  
```dataview
LIST
FROM #priority/high
WHERE contains(file.name, "PRD")
```

### Tag-Based Navigation
- Click any tag to see all documents with that tag
- Use tag combinations for precise filtering
- Use the Tag Pane for comprehensive tag management

## 🔄 Maintenance

### Regular Tasks
1. **Update Status Tags** - Keep implementation status current
2. **Review Cross-References** - Ensure links remain accurate
3. **Tag Consistency** - Use consistent tagging patterns
4. **Document Updates** - Update related documents when making changes

### Best Practices
1. **Always Tag New Documents** - Use at least 3-4 relevant tags
2. **Link Related Content** - Create bidirectional relationships
3. **Update Dependencies** - Maintain dependency relationships
4. **Use Templates** - Maintain consistency with provided templates
5. **Regular Reviews** - Periodically check for broken links and outdated content

## 🚀 Advanced Features

### Project Views
Use the Projects plugin to create:
- Implementation status boards
- Priority matrices
- Development timelines
- Feature roadmaps

### Mind Maps
Create visual representations of:
- System architecture relationships
- Feature dependencies
- Knowledge hierarchies
- Decision trees

### Kanban Boards
Track progress with:
- Status-based columns (Planned → In Progress → Implemented)
- Priority-based swimlanes
- Team assignment boards
- Sprint planning boards

---

This PKM system provides a powerful foundation for navigating and understanding the complex TMS architecture. Regular use of the tagging, linking, and query features will significantly enhance knowledge discovery and project navigation.

**Next Steps:**
1. Install and configure the recommended plugins
2. Familiarize yourself with the tagging system
3. Explore the graph view and relationships
4. Use templates for new document creation
5. Experiment with custom dataview queries
