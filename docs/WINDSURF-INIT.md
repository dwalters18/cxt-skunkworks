I'm building an event-driven Transportation Management System (TMS) with a primary focus on dispatching and real-time analytics. To ensure clarity and reflect the current state in Windsurf IDE, please review the following key documents:

### **Primary Product Requirements Documents (PRDs) and Technical Specifications:**

* **Main PRD**: Overview – Core vision, values, and high-level requirements. (`/docs/PRD-Overview.md`)  
* **User Interface**: Dispatching Interface – Requirements for dispatching interactions. (`/docs/PRD-Dispatching-Interface.md`)  
* **Backend System**: Backend System Requirements (`/docs/PRD-Backend-System.md`)  
  * Database Schema (`/docs/PRD-Database-Schema.md`)  
  * Events Schema (`/docs/PRD-Events-Schema.md`)  
  * Event Streaming (Kafka) – Selected for its high-throughput, distributed, fault-tolerant capabilities suitable for handling real-time event streams efficiently. (`/docs/PRD-Stream-Processing.md`)  
  * Stream Processing (Flink) – Chosen for its powerful stream-processing engine, enabling low latency and real-time analytics essential for logistics. (`/docs/PRD-Stream-Processing.md`)  
  * Polyglot Persistence: (`/docs/PRD-Polyglot-Persistence.md`)  
    * **Postgres/PostGIS** – Ideal for spatial data management and geospatial queries critical in logistics routing and dispatching.  
    * **Neo4j** – Optimal for handling complex graph data, enabling efficient relationship mapping and route optimization through graph traversal algorithms.  
    * **TimescaleDB** – Specifically designed for high-performance storage and querying of time-series data, crucial for historical and real-time analytics.  
  * Real-time Analytics – Provides optimized real-time insights on logistics operations. (`/docs/PRD-Real-time-Analytics.md`)  
  * Machine Learning – Enables real-time predictive analytics and anomaly detection capabilities essential for dynamic operational improvements. (`/docs/PRD-Machine-Learning.md`)

### **Project Vision and Objectives:**

This TMS leverages a modern event-driven architecture and polyglot persistence approach, selecting optimal databases for each specific use case:

* **Spatial data**: Postgres with PostGIS (`/docs/PRD-Polyglot-Persistence.md`)  
* **Graph data**: Neo4j (`/docs/PRD-Polyglot-Persistence.md`)  
* **Time-series data**: TimescaleDB (`/docs/PRD-Polyglot-Persistence.md`)

Event streaming will be managed by Kafka, while Flink will handle real-time event processing. The system will also integrate machine learning through Flink ML for real-time analytics, anomaly detection, and route optimization.

The dispatching interface will utilize Google Maps APIs, offering a gamified, real-time interaction for dispatchers managing daily loads, drivers, and demands. A separate management interface will facilitate operational activities like managing loads, drivers, routes, and viewing analytics.

### **Key Pillars:**

* **Transparency**: Complete visibility of events, both real-time and historical.  
* **Real-time Operations**: Instant visibility and response to system events.  
* **Gamification**: Interactive, engaging dispatch experience.  
* **AI/ML Integration**: Real-time analytics and machine learning enhancements.

### **Performance and Scalability:**

The system will be distributed and scalable to efficiently manage thousands to potentially billions of shipments, loads, drivers, and vehicles.

---

## Current Goals

ADD_GOALS_HERE

---
