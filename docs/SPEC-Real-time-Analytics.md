# Product Requirements Document (PRD)
## TMS Real-time Analytics

**Version:** 1.0  
**Date:** July 3, 2025  
**Authors:** Product Team  
**Tags:** #TMS-Analytics #real-time #status/implemented #priority/high #streaming
**Related:** [[PRD-Overview]] | [[PRD-Events-Schema]] | [[PRD-Stream-Processing]] | [[PRD-Polyglot-Persistence]]
**Dependencies:** [[PRD-Events-Schema]], [[PRD-Database-Schema]], [[PRD-Stream-Processing]]
**Used By:** [[PRD-Dispatching-Interface]], [[PRD-Machine-Learning]]
**Features:** Real-time dashboards, KPI monitoring, event analytics, time-series data

---

## 1. Executive Summary

### 1.1 Overview
The TMS Real-time Analytics system serves as a learning platform for implementing modern analytics patterns in transportation management. Starting with basic dashboard capabilities, the system demonstrates progressive enhancement from simple real-time displays to advanced predictive analytics and automated decision-making.

### 1.2 Learning Objectives
Real-time analytics implementation focuses on:
- **Time-Series Data Management**: Master TimescaleDB and time-series patterns
- **Stream Processing Analytics**: Implement real-time aggregations and KPI calculations
- **Dashboard Development**: Build responsive, real-time UI components
- **Data Pipeline Design**: Create reliable data flow from events to insights
- **Performance Optimization**: Handle high-frequency analytics workloads

### 1.3 Implementation Status
**Currently Implemented ✅:**
- **Basic Dashboard**: Real-time load, vehicle, and driver status displays
- **WebSocket Integration**: Live event streaming to UI components
- **API Analytics Endpoints**: Basic metrics and KPI calculations
- **TimescaleDB Setup**: Time-series database infrastructure ready
- **Event-Driven Updates**: Real-time data flow from Kafka to dashboard

**Planned Development 📋:**
- **Advanced Stream Processing**: Flink-based real-time analytics jobs
- **Predictive Analytics**: ML-powered demand forecasting and route optimization
- **Automated Alerting**: Threshold-based and anomaly detection alerts
- **Complex Dashboards**: Multi-dimensional analytics and drill-down capabilities
- **Self-Service Analytics**: User-configurable dashboards and reports

---

## 2. Analytics Architecture

### 2.1 Data Pipeline Architecture
```yaml
Data Flow:
  Operational Systems → Kafka Events → Stream Processing → Analytics Storage → Visualization
  
Components:
  - Event Sources: TMS API, vehicle telemetry, driver apps, external systems
  - Stream Processing: Apache Flink for real-time calculations
  - Storage: TimescaleDB for time-series, PostgreSQL for dimensions
  - Visualization: React dashboards with real-time WebSocket updates
```

### 2.2 Analytics Stack
```yaml
Real-time Processing:
  - Apache Flink: Stream processing engine
  - Kafka: Event streaming platform
  - TimescaleDB: Time-series analytics database
  
Analytics Storage:
  - TimescaleDB: Metrics, KPIs, time-series data
  - PostgreSQL: Dimensional data, configurations
  - Redis: Real-time caching layer
  
Visualization:
  - React Components: Interactive dashboards
  - WebSocket: Real-time data updates
  - Chart.js/D3: Data visualization libraries
```

---

## 3. Real-time Analytics Use Cases

### 3.1 Fleet Performance Analytics

#### 3.1.1 Vehicle Utilization Monitoring
```yaml
Metrics:
  - Active vehicles per hour/day
  - Miles driven vs. available capacity
  - Fuel efficiency trending
  - Maintenance cost per mile
  - Downtime analysis

Real-time Calculations:
  - Current utilization percentage
  - Idle time detection
  - Performance comparison to historical averages
  - Efficiency deviation alerts
```

#### 3.1.2 Driver Performance Analytics
```yaml
Metrics:
  - Hours of service utilization
  - On-time delivery performance
  - Safety incident rates
  - Fuel efficiency by driver
  - Customer satisfaction scores

Real-time Monitoring:
  - HOS violation prevention
  - Performance scoring updates
  - Safety alert generation
  - Training recommendation triggers
```

### 3.2 Operational Analytics

#### 3.2.1 Load Management Analytics
```yaml
Metrics:
  - Load creation to delivery cycle time
  - Assignment efficiency
  - Delivery performance (on-time %)
  - Revenue per mile
  - Customer satisfaction

Real-time Processing:
  - Load status progression tracking
  - Delay detection and escalation
  - Capacity utilization monitoring
  - Revenue recognition events
```

#### 3.2.2 Route Optimization Analytics
```yaml
Metrics:
  - Planned vs. actual route performance
  - Traffic impact analysis
  - Route efficiency scores
  - Fuel consumption optimization
  - Delivery time predictions

Real-time Calculations:
  - ETA updates based on current progress
  - Route deviation impact assessment
  - Traffic-adjusted optimization
  - Dynamic re-routing recommendations
```

### 3.3 Business Intelligence

#### 3.3.1 Financial Analytics
```yaml
Metrics:
  - Revenue per load, per mile, per day
  - Cost breakdown analysis
  - Profit margin tracking
  - Customer profitability
  - Carrier performance

Real-time Processing:
  - Revenue recognition automation
  - Cost allocation updates
  - Profitability alerts
  - Budget variance tracking
```

#### 3.3.2 Customer Analytics
```yaml
Metrics:
  - Service level performance
  - Customer satisfaction trends
  - Load volume patterns
  - Payment performance
  - Service quality scores

Real-time Monitoring:
  - Service level breach alerts
  - Customer communication triggers
  - Volume trend analysis
  - Quality score updates
```

---

## 4. Analytics Data Models

### 4.1 Time-Series Metrics Schema
```sql
-- Core metrics table structure
CREATE TABLE metrics (
    time TIMESTAMPTZ NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,  -- 'VEHICLE', 'DRIVER', 'LOAD', 'ROUTE'
    entity_id UUID NOT NULL,
    metric_value DECIMAL(15,4) NOT NULL,
    dimensions JSONB,  -- Additional context
    tags JSONB         -- Metadata for filtering
);

SELECT create_hypertable('metrics', 'time');
CREATE INDEX ON metrics (metric_name, entity_type, time DESC);
```

### 4.2 KPI Definitions
```yaml
Vehicle KPIs:
  utilization_rate: (active_hours / available_hours) * 100
  fuel_efficiency: miles_driven / fuel_consumed
  maintenance_cost_per_mile: maintenance_cost / miles_driven
  downtime_percentage: (maintenance_hours / total_hours) * 100

Driver KPIs:
  on_time_delivery_rate: (on_time_deliveries / total_deliveries) * 100
  hos_utilization: (driving_hours / available_hours) * 100
  safety_score: calculated_safety_score (0-100)
  customer_rating: average_customer_rating (1-5)

Load KPIs:
  cycle_time: delivery_time - creation_time
  assignment_time: assigned_time - creation_time
  delivery_performance: actual_delivery_time vs. promised_time
  revenue_per_mile: load_revenue / route_distance
```

### 4.3 Aggregation Tables
```sql
-- Pre-computed hourly aggregations
CREATE MATERIALIZED VIEW hourly_fleet_metrics
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', time) AS hour,
    entity_type,
    COUNT(DISTINCT entity_id) AS active_entities,
    AVG(metric_value) AS avg_value,
    MAX(metric_value) AS max_value,
    MIN(metric_value) AS min_value,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY metric_value) AS p95_value
FROM metrics
WHERE metric_name IN ('utilization_rate', 'fuel_efficiency', 'on_time_rate')
GROUP BY hour, entity_type, metric_name;

-- Daily business metrics
CREATE MATERIALIZED VIEW daily_business_metrics
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 day', time) AS day,
    SUM(CASE WHEN metric_name = 'revenue' THEN metric_value ELSE 0 END) AS total_revenue,
    SUM(CASE WHEN metric_name = 'cost' THEN metric_value ELSE 0 END) AS total_cost,
    COUNT(DISTINCT CASE WHEN metric_name = 'load_delivered' THEN entity_id END) AS loads_delivered,
    AVG(CASE WHEN metric_name = 'customer_rating' THEN metric_value END) AS avg_customer_rating
FROM metrics
GROUP BY day;
```

---

## 5. Real-time Processing Implementation

### 5.1 Flink Stream Processing Jobs

#### 5.1.1 Vehicle Metrics Processor
```python
# Flink job for real-time vehicle analytics
class VehicleMetricsProcessor(ProcessFunction):
    def process_element(self, event, ctx):
        if event.event_type == 'VEHICLE_LOCATION_UPDATED':
            # Calculate real-time metrics
            speed = event.data.get('speed', 0)
            fuel_level = event.data.get('fuel_level', 0)
            
            # Emit utilization metric
            if speed > 5:  # Vehicle is moving
                yield MetricEvent(
                    metric_name='vehicle_active',
                    entity_type='VEHICLE',
                    entity_id=event.entity_id,
                    metric_value=1.0,
                    timestamp=event.timestamp
                )
            
            # Emit fuel efficiency metric
            if hasattr(self, 'previous_location'):
                distance = calculate_distance(
                    self.previous_location, 
                    event.data['location']
                )
                fuel_consumed = self.previous_fuel_level - fuel_level
                if fuel_consumed > 0:
                    efficiency = distance / fuel_consumed
                    yield MetricEvent(
                        metric_name='fuel_efficiency',
                        entity_type='VEHICLE',
                        entity_id=event.entity_id,
                        metric_value=efficiency,
                        timestamp=event.timestamp
                    )
```

#### 5.1.2 Load Performance Processor
```python
# Flink job for load performance analytics
class LoadPerformanceProcessor(ProcessFunction):
    def process_element(self, event, ctx):
        if event.event_type == 'LOAD_DELIVERED':
            # Calculate delivery performance
            load_data = self.get_load_data(event.entity_id)
            
            planned_delivery = load_data['planned_delivery_time']
            actual_delivery = event.timestamp
            
            # On-time performance
            on_time = 1.0 if actual_delivery <= planned_delivery else 0.0
            
            yield MetricEvent(
                metric_name='on_time_delivery',
                entity_type='LOAD',
                entity_id=event.entity_id,
                metric_value=on_time,
                timestamp=event.timestamp
            )
            
            # Cycle time calculation
            cycle_time = (actual_delivery - load_data['created_at']).total_seconds() / 3600
            
            yield MetricEvent(
                metric_name='cycle_time_hours',
                entity_type='LOAD',
                entity_id=event.entity_id,
                metric_value=cycle_time,
                timestamp=event.timestamp
            )
```

### 5.2 Anomaly Detection
```python
# Real-time anomaly detection
class AnomalyDetector(ProcessFunction):
    def __init__(self):
        self.baseline_metrics = {}
        self.anomaly_threshold = 2.0  # Standard deviations
    
    def process_element(self, metric_event, ctx):
        metric_key = f"{metric_event.entity_type}_{metric_event.metric_name}"
        
        if metric_key in self.baseline_metrics:
            baseline = self.baseline_metrics[metric_key]
            z_score = abs(metric_event.metric_value - baseline['mean']) / baseline['std']
            
            if z_score > self.anomaly_threshold:
                yield AnomalyAlert(
                    entity_type=metric_event.entity_type,
                    entity_id=metric_event.entity_id,
                    metric_name=metric_event.metric_name,
                    expected_value=baseline['mean'],
                    actual_value=metric_event.metric_value,
                    severity='HIGH' if z_score > 3.0 else 'MEDIUM',
                    timestamp=metric_event.timestamp
                )
```

---

## 6. Dashboard and Visualization

### 6.1 Real-time Dashboard Components
```yaml
Fleet Overview Dashboard:
  - Active vehicles map with real-time locations
  - Fleet utilization gauge (percentage active)
  - Fuel efficiency trending chart
  - Maintenance alerts and upcoming due dates
  - Driver status distribution (available, driving, break)

Operations Dashboard:
  - Load status pipeline (created → assigned → in transit → delivered)
  - On-time delivery performance (current day vs. target)
  - Route efficiency metrics and deviation alerts
  - Customer satisfaction scores trending
  - Revenue and cost tracking (real-time)

Performance Analytics:
  - KPI scorecards with real-time updates
  - Comparative performance charts (current vs. historical)
  - Drill-down capabilities for detailed analysis
  - Anomaly detection alerts and explanations
  - Predictive trend indicators
```

### 6.2 Real-time Data Updates
```javascript
// WebSocket integration for real-time dashboard updates
class RealTimeAnalytics {
    constructor() {
        this.socket = new WebSocket('ws://localhost:8000/ws/analytics');
        this.metrics = new Map();
    }
    
    handleMessage(message) {
        const data = JSON.parse(message.data);
        
        switch(data.type) {
            case 'METRIC_UPDATE':
                this.updateMetric(data.metric);
                break;
            case 'ANOMALY_ALERT':
                this.showAnomalyAlert(data.alert);
                break;
            case 'KPI_UPDATE':
                this.updateKPI(data.kpi);
                break;
        }
    }
    
    updateMetric(metric) {
        // Update dashboard component with new metric value
        const component = document.getElementById(`metric-${metric.name}`);
        if (component) {
            component.textContent = metric.value;
            component.classList.add('updated');
        }
    }
}
```

---

## 7. Alerting and Notifications

### 7.1 Alert Categories
```yaml
Critical Alerts (Immediate Action Required):
  - Vehicle breakdown or emergency
  - Driver HOS violations
  - Load delivery failures
  - System outages or data quality issues
  - Safety incidents

Warning Alerts (Attention Required):
  - Performance degradation trends
  - Capacity utilization thresholds
  - Maintenance due dates approaching
  - Customer satisfaction drops
  - Cost variance exceeding budgets

Informational Alerts:
  - Performance milestones achieved
  - Efficiency improvements detected
  - New optimization opportunities
  - System health status updates
```

### 7.2 Alert Processing
```python
# Alert processing and notification system
class AlertProcessor:
    def __init__(self):
        self.alert_rules = self.load_alert_rules()
        self.notification_channels = self.setup_channels()
    
    def process_metric(self, metric):
        for rule in self.alert_rules:
            if self.evaluate_rule(rule, metric):
                alert = self.create_alert(rule, metric)
                self.send_notifications(alert)
    
    def evaluate_rule(self, rule, metric):
        if rule['metric_name'] != metric.metric_name:
            return False
        
        return self.check_threshold(rule, metric.metric_value)
    
    def send_notifications(self, alert):
        # Send to appropriate channels based on severity
        if alert.severity == 'CRITICAL':
            self.send_sms(alert)
            self.send_email(alert)
            self.send_slack(alert)
        elif alert.severity == 'WARNING':
            self.send_email(alert)
            self.send_slack(alert)
        else:
            self.send_slack(alert)
```

---

## 8. Performance Requirements

### 8.1 Real-time Processing SLAs
```yaml
Processing Latency:
  - Metric calculation: < 5 seconds
  - Anomaly detection: < 10 seconds
  - Alert generation: < 15 seconds
  - Dashboard updates: < 3 seconds
  - KPI aggregation: < 30 seconds

Throughput Requirements:
  - 10,000 events/second processing capacity
  - 1,000 concurrent dashboard users
  - 100 simultaneous analytics queries
  - 24/7 availability with 99.9% uptime

Data Freshness:
  - Vehicle locations: < 30 seconds
  - Load status: < 1 minute
  - Performance metrics: < 5 minutes
  - Business KPIs: < 15 minutes
```

### 8.2 Scalability Design
```yaml
Horizontal Scaling:
  - Flink cluster scaling based on event volume
  - TimescaleDB multi-node for large datasets
  - Load balancing for dashboard traffic
  - Kafka partitioning for parallel processing

Performance Optimization:
  - Pre-computed aggregations for common queries
  - Caching layer for frequently accessed metrics
  - Efficient indexing strategies
  - Query optimization and performance tuning
```

---

## 9. Machine Learning Integration

### 9.1 Predictive Analytics
```yaml
Demand Forecasting:
  - Historical load patterns analysis
  - Seasonal and trend decomposition
  - External factors integration (weather, holidays)
  - Capacity planning recommendations

Performance Prediction:
  - Vehicle maintenance needs prediction
  - Driver performance forecasting
  - Route efficiency optimization
  - Fuel consumption estimation

Anomaly Detection:
  - Statistical anomaly detection
  - Machine learning-based pattern recognition
  - Behavioral analysis for fraud detection
  - System health monitoring
```

### 9.2 Real-time ML Inference
```python
# Real-time ML model integration
class MLInferenceProcessor(ProcessFunction):
    def __init__(self):
        self.model_client = MLServerClient()
        self.feature_cache = {}
    
    def process_element(self, event, ctx):
        # Extract features for ML inference
        features = self.extract_features(event)
        
        # Get prediction from ML server
        prediction = self.model_client.predict(
            model_name='demand_forecast',
            features=features
        )
        
        # Emit prediction event
        yield PredictionEvent(
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            prediction_type='demand_forecast',
            prediction_value=prediction['value'],
            confidence=prediction['confidence'],
            timestamp=event.timestamp
        )
```

---

## 10. Data Quality and Governance

### 10.1 Data Quality Monitoring
```yaml
Quality Metrics:
  - Data completeness (missing values)
  - Data accuracy (validation rules)
  - Data timeliness (freshness checks)
  - Data consistency (cross-source validation)

Quality Checks:
  - Real-time validation rules
  - Anomaly detection for data quality
  - Automated data profiling
  - Quality score calculation and trending
```

### 10.2 Governance Framework
```yaml
Data Lineage:
  - Complete data flow tracking
  - Source system identification
  - Transformation documentation
  - Impact analysis capabilities

Access Control:
  - Role-based analytics access
  - Data sensitivity classification
  - Audit logging for all access
  - Privacy protection compliance
```

---

## 11. Future Enhancements

### 11.1 Advanced Analytics (Phase 2)
- **Graph Analytics**: Network analysis using Neo4j for route optimization
- **Geospatial Analytics**: Advanced location-based insights
- **Customer Journey Analytics**: End-to-end customer experience tracking
- **Supply Chain Analytics**: Extended visibility beyond transportation

### 11.2 AI/ML Expansion (Phase 3)
- **Deep Learning Models**: Advanced pattern recognition
- **Reinforcement Learning**: Dynamic optimization algorithms
- **Natural Language Processing**: Automated report generation
- **Computer Vision**: Image-based vehicle and cargo monitoring

This real-time analytics system provides the TMS with comprehensive operational intelligence, enabling data-driven decision making and proactive management of transportation operations while maintaining the performance and scalability required for logistics operations.
