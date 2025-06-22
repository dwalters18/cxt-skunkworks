-- TimescaleDB initialization for TMS time-series data
-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Vehicle tracking data (GPS coordinates, telemetry)
CREATE TABLE vehicle_tracking (
    time TIMESTAMPTZ NOT NULL,
    vehicle_id UUID NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    speed DOUBLE PRECISION, -- mph
    heading DOUBLE PRECISION, -- degrees
    altitude DOUBLE PRECISION, -- feet
    fuel_level DOUBLE PRECISION, -- percentage
    engine_hours DOUBLE PRECISION,
    odometer DOUBLE PRECISION, -- miles
    engine_temp DOUBLE PRECISION, -- fahrenheit
    is_moving BOOLEAN DEFAULT false,
    driver_id UUID,
    load_id UUID
);

-- Convert to hypertable (partitioned by time)
SELECT create_hypertable('vehicle_tracking', 'time');

-- Driver activity tracking
CREATE TABLE driver_activity (
    time TIMESTAMPTZ NOT NULL,
    driver_id UUID NOT NULL,
    activity_type VARCHAR(50), -- driving, on_duty, off_duty, sleeper_berth
    duration_minutes INTEGER,
    location_lat DOUBLE PRECISION,
    location_lng DOUBLE PRECISION,
    vehicle_id UUID,
    load_id UUID,
    notes TEXT
);

SELECT create_hypertable('driver_activity', 'time');

-- Load status events
CREATE TABLE load_events (
    time TIMESTAMPTZ NOT NULL,
    load_id UUID NOT NULL,
    event_type VARCHAR(100), -- picked_up, in_transit, delivered, exception
    event_description TEXT,
    location_lat DOUBLE PRECISION,
    location_lng DOUBLE PRECISION,
    driver_id UUID,
    vehicle_id UUID,
    metadata JSONB
);

SELECT create_hypertable('load_events', 'time');

-- Performance metrics
CREATE TABLE performance_metrics (
    time TIMESTAMPTZ NOT NULL,
    metric_type VARCHAR(100), -- fuel_efficiency, on_time_delivery, utilization
    entity_type VARCHAR(50), -- vehicle, driver, carrier, route
    entity_id UUID NOT NULL,
    metric_value DOUBLE PRECISION,
    unit VARCHAR(20),
    period VARCHAR(20), -- hourly, daily, weekly, monthly
    metadata JSONB
);

SELECT create_hypertable('performance_metrics', 'time');

-- Route analytics
CREATE TABLE route_analytics (
    time TIMESTAMPTZ NOT NULL,
    route_id UUID NOT NULL,
    actual_distance DOUBLE PRECISION,
    actual_duration INTEGER, -- minutes
    planned_distance DOUBLE PRECISION,
    planned_duration INTEGER,
    fuel_consumed DOUBLE PRECISION,
    toll_cost DOUBLE PRECISION,
    average_speed DOUBLE PRECISION,
    stops_count INTEGER,
    weather_conditions JSONB,
    traffic_conditions JSONB
);

SELECT create_hypertable('route_analytics', 'time');

-- Carrier performance data
CREATE TABLE carrier_performance (
    time TIMESTAMPTZ NOT NULL,
    carrier_id UUID NOT NULL,
    loads_completed INTEGER DEFAULT 0,
    loads_in_progress INTEGER DEFAULT 0,
    on_time_percentage DOUBLE PRECISION,
    average_transit_time DOUBLE PRECISION, -- hours
    fuel_efficiency DOUBLE PRECISION, -- mpg
    safety_score DOUBLE PRECISION,
    customer_rating DOUBLE PRECISION,
    revenue DOUBLE PRECISION,
    costs DOUBLE PRECISION
);

SELECT create_hypertable('carrier_performance', 'time');

-- Create indexes for better query performance
CREATE INDEX idx_vehicle_tracking_vehicle_time ON vehicle_tracking (vehicle_id, time DESC);
CREATE INDEX idx_driver_activity_driver_time ON driver_activity (driver_id, time DESC);
CREATE INDEX idx_load_events_load_time ON load_events (load_id, time DESC);
CREATE INDEX idx_performance_metrics_entity_time ON performance_metrics (entity_id, time DESC);
CREATE INDEX idx_route_analytics_route_time ON route_analytics (route_id, time DESC);
CREATE INDEX idx_carrier_performance_carrier_time ON carrier_performance (carrier_id, time DESC);

-- Create continuous aggregates for common queries
CREATE MATERIALIZED VIEW hourly_vehicle_stats
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', time) AS hour,
    vehicle_id,
    AVG(speed) as avg_speed,
    MAX(speed) as max_speed,
    AVG(fuel_level) as avg_fuel_level,
    SUM(CASE WHEN is_moving THEN 1 ELSE 0 END) * 5 / 60.0 as hours_moving, -- assuming 5min intervals
    COUNT(*) as data_points
FROM vehicle_tracking
GROUP BY hour, vehicle_id;

CREATE MATERIALIZED VIEW daily_carrier_summary
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 day', time) AS day,
    carrier_id,
    AVG(on_time_percentage) as avg_on_time_percentage,
    AVG(fuel_efficiency) as avg_fuel_efficiency,
    SUM(loads_completed) as total_loads_completed,
    AVG(revenue) as avg_daily_revenue
FROM carrier_performance
GROUP BY day, carrier_id;

-- Set up data retention policies (keep detailed data for 90 days, aggregated data longer)
SELECT add_retention_policy('vehicle_tracking', INTERVAL '90 days');
SELECT add_retention_policy('driver_activity', INTERVAL '90 days');
SELECT add_retention_policy('load_events', INTERVAL '1 year');

-- Refresh policies for continuous aggregates
SELECT add_continuous_aggregate_policy('hourly_vehicle_stats',
    start_offset => INTERVAL '1 day',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

SELECT add_continuous_aggregate_policy('daily_carrier_summary',
    start_offset => INTERVAL '7 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day');

-- Insert sample tracking data
INSERT INTO vehicle_tracking (time, vehicle_id, latitude, longitude, speed, heading, fuel_level, is_moving) 
VALUES 
    (NOW() - INTERVAL '1 hour', '00000000-0000-0000-0000-000000000001', 29.7604, -95.3698, 65.5, 180, 85.2, true),
    (NOW() - INTERVAL '50 minutes', '00000000-0000-0000-0000-000000000001', 29.6604, -95.3698, 68.2, 180, 84.8, true),
    (NOW() - INTERVAL '40 minutes', '00000000-0000-0000-0000-000000000001', 29.5604, -95.3698, 0, 180, 84.8, false);

INSERT INTO load_events (time, load_id, event_type, event_description, location_lat, location_lng)
VALUES 
    (NOW() - INTERVAL '2 hours', '00000000-0000-0000-0000-000000000001', 'picked_up', 'Load picked up from shipper', 29.7604, -95.3698),
    (NOW() - INTERVAL '1 hour', '00000000-0000-0000-0000-000000000001', 'in_transit', 'Load in transit to destination', 29.6604, -95.3698);
