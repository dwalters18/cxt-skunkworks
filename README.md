# TMS Event-Driven Architecture

A comprehensive Transportation Management System (TMS) built with modern event-driven architecture using Kafka, Flink, and multiple specialized databases.

## 🚀 Architecture Overview

This project demonstrates a full-scale TMS implementation with:

- **Event-Driven Design**: Kafka for event streaming with Flink for real-time stream processing
- **Polyglot Persistence**: Multiple specialized databases for different data patterns
- **Microservices**: FastAPI-based services with Docker containerization
- **Modern Frontend**: React-based dashboard for operations management

## 🏗️ Technology Stack

### Backend Services
- **FastAPI**: Python-based API gateway and services
- **Apache Kafka**: Event streaming platform for real-time data flows
- **Apache Flink**: Stream processing for real-time analytics and event processing

### Data Layer
- **PostgreSQL**: OLTP database with CDC (Change Data Capture) support
- **Neo4j**: Graph database for routing, networks, and relationships
- **TimescaleDB**: Time-series database for tracking data and metrics
- **Debezium**: CDC connector for real-time data streaming

### Frontend
- **React**: Modern web application with comprehensive TMS functionality
- **Docker**: Containerized deployment with Nginx

### Infrastructure
- **Docker Compose**: Full-stack orchestration
- **Kafka UI**: Web interface for Kafka cluster management

## 📋 Features

### Load Management
- Load creation and lifecycle management
- Status tracking and updates
- Route optimization
- Customer and carrier management

### Vehicle Tracking
- Real-time GPS tracking
- Location history and analytics
- Speed and heading monitoring
- Fleet management dashboard

### Event Console
- Live event stream visualization
- Event publishing and testing
- Topic monitoring and management
- Real-time system debugging

### Analytics Dashboard
- KPI monitoring and reporting
- Performance metrics and charts
- System health indicators
- Status distribution analytics

## 🚀 Getting Started

### Prerequisites
- Docker and Docker Compose
- Git

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/cxt-skunkworks.git
   cd cxt-skunkworks
   ```

2. **Configure environment**
   ```bash
   cp server/app/.env.example server/app/.env
   # Edit .env with your configuration
   ```

3. **Start the full stack**
   ```bash
   docker-compose up -d
   ```

4. **Access the applications**
   - **TMS Dashboard**: http://localhost:3000
   - **API Documentation**: http://localhost:8000/docs
   - **Kafka UI**: http://localhost:8080
   - **Flink Dashboard**: http://localhost:8081
   - **Neo4j Browser**: http://localhost:7474

## 🔧 Development

### Service Ports
| Service | Port | Description |
|---------|------|-------------|
| React UI | 3000 | Main TMS Dashboard |
| FastAPI | 8000 | API Gateway |
| Kafka UI | 8080 | Kafka Management |
| Flink UI | 8081 | Stream Processing Dashboard |
| Neo4j | 7474 | Graph Database Browser |
| PostgreSQL | 5432 | OLTP Database |
| TimescaleDB | 5433 | Time-Series Database |
| Kafka | 9092 | Event Streaming |
| Debezium | 8083 | CDC Connector |

### Project Structure
```
├── ui/                     # React frontend application
│   ├── src/components/     # TMS dashboard components
│   └── Dockerfile         # Frontend container
├── server/                # Backend services
│   ├── app/              # FastAPI application
│   ├── database/         # Database initialization scripts
│   └── Dockerfile        # Backend container
└── docker-compose.yml   # Full stack orchestration
```

## 🎯 Event-Driven Workflows

### Load Management Events
- `load.created` - New load entered into system
- `load.assigned` - Load assigned to carrier/driver
- `load.picked_up` - Pickup completed
- `load.delivered` - Delivery completed
- `load.status_changed` - Status updates

### Vehicle Tracking Events
- `vehicle.location_updated` - GPS position updates
- `vehicle.status_changed` - Vehicle availability changes
- `vehicle.maintenance_due` - Maintenance scheduling

### System Events
- `system.health_check` - System monitoring
- `analytics.metrics_updated` - Real-time analytics

## 📊 Monitoring & Operations

- **Real-time Dashboards**: Monitor all system operations through the React UI
- **Event Streaming**: View live event flows through the Event Console
- **Database Health**: Monitor all database connections and performance
- **System Metrics**: Track KPIs and operational metrics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with the full Docker stack
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Documentation

- [Kafka Documentation](https://kafka.apache.org/documentation/)
- [Flink Documentation](https://nightlies.apache.org/flink/flink-docs-stable/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
