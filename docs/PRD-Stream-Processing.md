# Product Requirements Document (PRD)
## TMS Event Streaming & Stream Processing

**Version:** 1.0  
**Date:** July 3, 2025  
**Authors:** Product Team  

---

## 1. Executive Summary

### 1.1 Overview
The TMS Stream Processing system demonstrates event-driven architecture using Apache Kafka for high-throughput event streaming and Apache Flink for real-time stream processing. Currently implemented with basic audit monitoring, the system provides a foundation for learning advanced stream processing patterns and real-time ML applications.

### 1.2 Implementation Status
**Currently Implemented ✅:**
- **Kafka Infrastructure**: KRaft mode deployment with comprehensive topic structure
- **Basic Flink Job**: Audit event monitoring with simple anomaly detection
- **Event Streaming**: Full event taxonomy across TMS domains
- **Real-time Consumers**: Backend integration for live event processing

**Planned Development 📋:**
- **Advanced ML Stream Processing**: Real-time predictive analytics
- **Route Optimization Jobs**: Dynamic routing based on live traffic
- **Complex Event Processing**: Multi-stream correlation and pattern detection
- **Streaming Aggregations**: Real-time KPI calculation and alerting

### 1.3 Learning Objectives
- **Event-Driven Architecture**: Master Kafka and stream processing patterns
- **Real-time Analytics**: Implement low-latency data processing pipelines
- **Stream Processing**: Understand Flink stateful processing and windowing
- **Scalability Patterns**: Design for high-throughput event streams

---

## 2. Current Stream Processing Implementation

### 2.1 Kafka Event Streaming
```yaml
Current Topics:
  - tms.loads: Load lifecycle events
  - tms.vehicles: Vehicle operational events  
  - tms.vehicles.tracking: High-frequency location updates
  - tms.drivers: Driver management events
  - tms.drivers.tracking: Driver status and location
  - tms.routes: Route planning and optimization
  - tms.audit: System audit events (currently monitored)
  - tms.system.alerts: System-wide notifications
```

### 2.2 Flink Audit Monitoring
**Current Implementation:**
- **Source**: `tms.audit` Kafka topic
- **Processing**: Placeholder anomaly detection model
- **Output**: Anomaly alerts and system health metrics
- **Latency**: Sub-second processing for real-time monitoring

**File**: `/streaming/flink_audit_anomaly.py`
```python
# Current Flink job monitors audit events for:
# - Unusual system access patterns
# - Data quality issues
# - Performance degradation indicators
# - Security anomalies
```

---

## 3. Planned Stream Processing Expansions

### 3.1 Real-Time ML Operations
**Planned Flink ML Applications:**

#### 3.1.1 Predictive Maintenance
- **Input**: Vehicle telemetry, maintenance history
- **Processing**: ML models predicting component failures
- **Output**: Proactive maintenance scheduling alerts
- **Business Impact**: Reduce unplanned downtime by 40%

#### 3.1.2 Demand Forecasting
- **Input**: Historical load patterns, market data
- **Processing**: Time-series ML models
- **Output**: Capacity planning recommendations
- **Business Impact**: Optimize fleet utilization

#### 3.1.3 Driver Performance Analytics
- **Input**: Driver behavior data, safety metrics
- **Processing**: Performance scoring algorithms
- **Output**: Training recommendations, safety alerts
- **Business Impact**: Improve safety scores and efficiency

### 3.2 Route Optimization Operations
**Real-Time Route Processing:**

#### 3.2.1 Dynamic Route Adjustment
- **Input**: Traffic data, vehicle locations, delivery windows
- **Processing**: Graph-based optimization algorithms
- **Output**: Updated route recommendations
- **Trigger**: Traffic incidents, customer changes, delays

#### 3.2.2 Load Consolidation
- **Input**: Available loads, vehicle capacity, geographic proximity
- **Processing**: Optimization algorithms for load matching
- **Output**: Consolidated load recommendations
- **Business Impact**: Increase vehicle utilization by 25%

---

## 4. Logistics-Specific Stream Processing Requirements

### 4.1 Real-Time Vehicle Tracking Analytics
```yaml
Processing Requirements:
  - Vehicle location aggregation (every 30 seconds)
  - Speed and fuel efficiency calculations
  - Geofence violation detection
  - Route deviation alerts
  - ETA recalculation based on current progress
```

### 4.2 Driver Hours of Service (HOS) Monitoring
```yaml
Real-Time HOS Processing:
  - Continuous duty time calculation
  - Break requirement predictions
  - Violation prevention alerts
  - Automatic status updates
  - Compliance reporting
```

### 4.3 Load Status Progression
```yaml
Load Lifecycle Monitoring:
  - Pickup/delivery confirmation processing
  - Customer notification triggers
  - Delay detection and escalation
  - Performance KPI calculations
  - Revenue recognition events
```

### 4.4 Fleet Performance Analytics
```yaml
Real-Time Fleet Metrics:
  - Vehicle utilization rates
  - Fuel efficiency trending
  - Driver productivity scores
  - Route performance analysis
  - Cost per mile calculations
```

---

## 5. Stream Processing Architecture

### 5.1 Kafka Cluster Configuration
```yaml
Kafka Setup (KRaft Mode):
  brokers: 3
  partitions_per_topic: 12-24 (based on throughput)
  replication_factor: 3
  retention: 7-30 days (topic dependent)
  compression: lz4/snappy
  acks: all (for critical events)
```

### 5.2 Flink Cluster Architecture
```yaml
Flink Configuration:
  task_managers: 4
  slots_per_tm: 4
  parallelism: 16
  checkpointing: 30 seconds
  savepoint_strategy: on_failure
  memory_config: optimized for streaming
```

### 5.3 Processing Patterns

#### 5.3.1 Event Time Processing
- **Use Case**: Vehicle tracking, HOS calculations
- **Watermarks**: Handle late-arriving events (5-minute tolerance)
- **Windows**: Tumbling windows for aggregations

#### 5.3.2 Real-Time Alerting
- **Pattern**: CEP (Complex Event Processing) for pattern detection
- **Use Cases**: Route deviations, HOS violations, vehicle breakdowns
- **Latency**: Sub-second alert generation

#### 5.3.3 Stateful Processing
- **State**: Driver HOS remaining, vehicle locations, load progress
- **Persistence**: RocksDB with periodic checkpointing
- **Recovery**: Exactly-once processing guarantees

---

## 6. Integration with ML Server

### 6.1 Model Deployment Architecture
```yaml
ML Integration:
  model_server: FastAPI-based ML Server
  model_formats: ONNX, TensorFlow, scikit-learn
  inference_latency: <100ms
  model_versioning: A/B testing support
  fallback_strategy: default_rules_engine
```

### 6.2 Real-Time Model Inference
```python
# Flink integration with ML Server
class MLInferenceFunction(ProcessFunction):
    def process_element(self, event, ctx):
        # Extract features from event
        features = self.extract_features(event)
        
        # Call ML Server for prediction
        prediction = self.ml_client.predict(features)
        
        # Emit prediction event
        yield PredictionEvent(event.id, prediction)
```

---

## 7. Performance Requirements & SLAs

### 7.1 Processing Latency SLAs
```yaml
Latency Requirements:
  audit_anomaly_detection: <1 second
  vehicle_tracking_aggregation: <5 seconds
  route_optimization: <30 seconds
  hos_violation_detection: <10 seconds
  predictive_maintenance: <60 seconds
```

### 7.2 Throughput Requirements
```yaml
Event Processing Volume:
  vehicle_tracking: 50,000 events/day
  driver_events: 10,000 events/day
  load_events: 5,000 events/day
  audit_events: 2,000 events/day
  peak_throughput: 1,000 events/second
```

### 7.3 Availability and Reliability
```yaml
Reliability Requirements:
  uptime: 99.9%
  data_durability: exactly_once_processing
  failover_time: <2 minutes
  checkpoint_interval: 30 seconds
  recovery_time: <5 minutes
```

---

## 8. Monitoring and Observability

### 8.1 Stream Processing Metrics
- **Kafka Metrics**: Throughput, lag, partition distribution
- **Flink Metrics**: Processing latency, checkpoint duration, backpressure
- **Application Metrics**: Business KPIs, model accuracy, alert rates

### 8.2 Alerting Thresholds
```yaml
Critical Alerts:
  - kafka_consumer_lag > 10,000 messages
  - flink_processing_latency > SLA + 50%
  - checkpoint_failure_rate > 1%
  - model_inference_errors > 5%

Warning Alerts:
  - event_processing_delay > 30 seconds
  - memory_utilization > 80%
  - network_errors > 1/minute
```

---

## 9. Future Roadmap

### 9.1 Phase 1: Enhanced Anomaly Detection (Weeks 1-4)
- Improve audit anomaly detection models
- Add vehicle behavior anomaly detection
- Implement driver performance anomaly alerts

### 9.2 Phase 2: Real-Time Route Optimization (Weeks 5-12)
- Dynamic route recalculation based on traffic
- Load consolidation optimization
- Integration with Google Maps APIs for real-time traffic

### 9.3 Phase 3: Advanced ML Operations (Weeks 13-20)
- Predictive maintenance models
- Demand forecasting pipeline
- Customer behavior analytics

### 9.4 Phase 4: Full Logistics Intelligence (Weeks 21-26)
- Complete fleet optimization algorithms
- Automated dispatch decision support
- Comprehensive predictive analytics suite

---

## 10. Security and Compliance

### 10.1 Data Security
- **Encryption**: All stream data encrypted in transit
- **Authentication**: Kafka SASL/SSL, Flink Kerberos
- **Authorization**: Topic-level access controls
- **Audit**: All processing activities logged

### 10.2 Compliance Requirements
- **Data Retention**: Automatic cleanup per compliance policies
- **PII Handling**: Sensitive data tokenization in streams
- **Audit Trails**: Complete processing lineage tracking
- **Regulatory**: DOT/FMCSA compliance for HOS processing

This stream processing architecture provides the foundation for real-time logistics intelligence while maintaining the simplicity and focus appropriate for the current project scope, with clear expansion paths for advanced ML and optimization capabilities.
