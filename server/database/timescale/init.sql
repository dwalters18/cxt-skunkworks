-- TimescaleDB initialization for TMS time-series data
-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS postgis;

-- Vehicle tracking hypertable - aligned with PRD
CREATE TABLE vehicle_tracking (
    time TIMESTAMPTZ NOT NULL,
    vehicle_id UUID NOT NULL,
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    speed DECIMAL(5,2),
    heading INTEGER,
    altitude DECIMAL(8,2),
    accuracy DECIMAL(6,2),
    odometer INTEGER,
    fuel_level DECIMAL(5,2),
    engine_hours DECIMAL(8,2),
    driver_id UUID,
    load_id UUID
);

-- Convert to hypertable
SELECT create_hypertable('vehicle_tracking', 'time');

-- Create indexes for performance
CREATE INDEX ON vehicle_tracking (vehicle_id, time DESC);
CREATE INDEX ON vehicle_tracking USING GIST (location);
CREATE INDEX ON vehicle_tracking (driver_id, time DESC);
CREATE INDEX ON vehicle_tracking (load_id, time DESC);

-- Driver activity hypertable - aligned with PRD
CREATE TABLE driver_activity (
    time TIMESTAMPTZ NOT NULL,
    driver_id UUID NOT NULL,
    activity_type VARCHAR(50) NOT NULL, -- 'DRIVING', 'ON_DUTY', 'OFF_DUTY', 'SLEEPER'
    location GEOGRAPHY(POINT, 4326),
    vehicle_id UUID,
    load_id UUID,
    hos_remaining DECIMAL(4,2),
    duration_minutes INTEGER,
    metadata JSONB
);

SELECT create_hypertable('driver_activity', 'time');
CREATE INDEX ON driver_activity (driver_id, time DESC);
CREATE INDEX ON driver_activity (activity_type, time DESC);
CREATE INDEX ON driver_activity USING GIST (location);

-- Load events hypertable - aligned with PRD
CREATE TABLE load_events (
    time TIMESTAMPTZ NOT NULL,
    load_id UUID NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    status VARCHAR(50),
    location GEOGRAPHY(POINT, 4326),
    driver_id UUID,
    vehicle_id UUID,
    details JSONB,
    created_by UUID
);

SELECT create_hypertable('load_events', 'time');
CREATE INDEX ON load_events (load_id, time DESC);
CREATE INDEX ON load_events (event_type, time DESC);
CREATE INDEX ON load_events (driver_id, time DESC);
CREATE INDEX ON load_events (vehicle_id, time DESC);
CREATE INDEX ON load_events USING GIST (location);

-- Performance metrics hypertable - aligned with PRD
CREATE TABLE performance_metrics (
    time TIMESTAMPTZ NOT NULL,
    entity_type VARCHAR(20) NOT NULL, -- 'DRIVER', 'VEHICLE', 'ROUTE'
    entity_id UUID NOT NULL,
    metric_name VARCHAR(50) NOT NULL,
    metric_value DECIMAL(15,4) NOT NULL,
    tags JSONB
);

SELECT create_hypertable('performance_metrics', 'time');
CREATE INDEX ON performance_metrics (entity_type, entity_id, time DESC);
CREATE INDEX ON performance_metrics (metric_name, time DESC);
CREATE INDEX ON performance_metrics USING GIN (tags);

-- Event stream hypertable - aligned with PRD
CREATE TABLE event_stream (
    time TIMESTAMPTZ NOT NULL,
    event_id UUID NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    source_system VARCHAR(50) NOT NULL,
    entity_type VARCHAR(20),
    entity_id UUID,
    event_data JSONB NOT NULL,
    correlation_id UUID,
    trace_id UUID
);

SELECT create_hypertable('event_stream', 'time');
CREATE INDEX ON event_stream (event_type, time DESC);
CREATE INDEX ON event_stream (entity_type, entity_id, time DESC);
CREATE INDEX ON event_stream (correlation_id);
CREATE INDEX ON event_stream (trace_id);
CREATE INDEX ON event_stream USING GIN (event_data);

-- Route analytics hypertable
CREATE TABLE route_analytics (
    time TIMESTAMPTZ NOT NULL,
    route_id UUID NOT NULL,
    load_id UUID NOT NULL,
    driver_id UUID NOT NULL,
    vehicle_id UUID NOT NULL,
    segment_start GEOGRAPHY(POINT, 4326),
    segment_end GEOGRAPHY(POINT, 4326),
    distance_miles DECIMAL(8,2),
    duration_minutes INTEGER,
    average_speed DECIMAL(5,2),
    fuel_consumed DECIMAL(8,2),
    traffic_delay_minutes INTEGER,
    weather_conditions VARCHAR(50),
    optimization_score DECIMAL(5,2)
);

SELECT create_hypertable('route_analytics', 'time');
CREATE INDEX ON route_analytics (route_id, time DESC);
CREATE INDEX ON route_analytics (load_id, time DESC);
CREATE INDEX ON route_analytics (driver_id, time DESC);
CREATE INDEX ON route_analytics (vehicle_id, time DESC);
CREATE INDEX ON route_analytics USING GIST (segment_start);
CREATE INDEX ON route_analytics USING GIST (segment_end);

-- Continuous aggregates for performance optimization
-- Hourly performance summary - aligned with PRD
CREATE MATERIALIZED VIEW hourly_performance
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', time) AS bucket,
    entity_type,
    entity_id,
    metric_name,
    AVG(metric_value) AS avg_value,
    MAX(metric_value) AS max_value,
    MIN(metric_value) AS min_value,
    COUNT(*) AS sample_count
FROM performance_metrics
GROUP BY bucket, entity_type, entity_id, metric_name;

SELECT add_continuous_aggregate_policy('hourly_performance',
    start_offset => INTERVAL '1 day',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

-- Daily vehicle utilization
CREATE MATERIALIZED VIEW daily_vehicle_utilization
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 day', time) AS day,
    vehicle_id,
    COUNT(*) AS tracking_points,
    AVG(speed) AS avg_speed,
    MAX(speed) AS max_speed,
    SUM(CASE WHEN speed > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS utilization_percent,
    AVG(fuel_level) AS avg_fuel_level,
    MAX(odometer) - MIN(odometer) AS miles_driven
FROM vehicle_tracking
WHERE speed IS NOT NULL
GROUP BY day, vehicle_id;

SELECT add_continuous_aggregate_policy('daily_vehicle_utilization',
    start_offset => INTERVAL '7 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day');

-- Hourly load status summary
CREATE MATERIALIZED VIEW hourly_load_status
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', time) AS bucket,
    event_type,
    status,
    COUNT(*) AS event_count,
    COUNT(DISTINCT load_id) AS unique_loads
FROM load_events
GROUP BY bucket, event_type, status;

SELECT add_continuous_aggregate_policy('hourly_load_status',
    start_offset => INTERVAL '1 day',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

-- Data retention policies
SELECT add_retention_policy('vehicle_tracking', INTERVAL '1 year');
SELECT add_retention_policy('driver_activity', INTERVAL '2 years');
SELECT add_retention_policy('load_events', INTERVAL '3 years');
SELECT add_retention_policy('performance_metrics', INTERVAL '1 year');
SELECT add_retention_policy('event_stream', INTERVAL '6 months');
SELECT add_retention_policy('route_analytics', INTERVAL '2 years');
