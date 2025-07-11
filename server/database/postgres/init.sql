-- PostgreSQL initialization for TMS OLTP database
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- Create enums first
CREATE TYPE load_status_enum AS ENUM (
    'CREATED', 'ASSIGNED', 'PICKED_UP', 'IN_TRANSIT', 
    'DELIVERED', 'CANCELLED', 'DELAYED'
);

CREATE TYPE vehicle_type_enum AS ENUM (
    'TRUCK', 'TRAILER', 'VAN', 'FLATBED', 'REFRIGERATED'
);

CREATE TYPE fuel_type_enum AS ENUM (
    'DIESEL', 'GASOLINE', 'ELECTRIC', 'HYBRID'
);

CREATE TYPE vehicle_status_enum AS ENUM (
    'AVAILABLE', 'ASSIGNED', 'IN_TRANSIT', 'MAINTENANCE', 'OUT_OF_SERVICE'
);

CREATE TYPE driver_status_enum AS ENUM (
    'AVAILABLE', 'ASSIGNED', 'DRIVING', 'ON_DUTY', 'OFF_DUTY', 'ON_BREAK', 'SLEEPER'
);

CREATE TYPE route_status_enum AS ENUM (
    'PLANNED', 'ACTIVE', 'COMPLETED', 'CANCELLED', 'DELAYED'
);

-- Core entity tables aligned with PRD specification
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_code VARCHAR(50) UNIQUE NOT NULL,
    company_name VARCHAR(200) NOT NULL,
    contact_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    zipcode VARCHAR(20),
    country VARCHAR(50) DEFAULT 'USA',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE carriers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    mc_number VARCHAR(50),
    dot_number VARCHAR(50),
    contact_info JSONB,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE vehicles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    carrier_id UUID REFERENCES carriers(id),
    vehicle_number VARCHAR(50) UNIQUE NOT NULL,
    make VARCHAR(50) NOT NULL,
    model VARCHAR(50) NOT NULL,
    year INTEGER NOT NULL,
    vin VARCHAR(17) UNIQUE NOT NULL,
    license_plate VARCHAR(20) UNIQUE NOT NULL,
    vehicle_type vehicle_type_enum NOT NULL,
    capacity_weight DECIMAL(10,2) NOT NULL,
    capacity_volume DECIMAL(10,2) NOT NULL,
    fuel_type fuel_type_enum NOT NULL,
    current_location GEOGRAPHY(POINT, 4326),
    current_address TEXT,
    status vehicle_status_enum NOT NULL DEFAULT 'AVAILABLE',
    last_maintenance_date DATE,
    next_maintenance_due DATE,
    mileage INTEGER,
    fuel_level DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE drivers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    carrier_id UUID REFERENCES carriers(id),
    driver_number VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20) NOT NULL,
    license_number VARCHAR(50) UNIQUE NOT NULL,
    license_class VARCHAR(10) NOT NULL,
    license_expiry DATE NOT NULL,
    date_of_birth DATE NOT NULL,
    hire_date DATE NOT NULL,
    current_location GEOGRAPHY(POINT, 4326),
    current_address TEXT,
    status driver_status_enum NOT NULL DEFAULT 'AVAILABLE',
    hours_of_service_remaining DECIMAL(4,2),
    last_hos_reset TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE loads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    load_number VARCHAR(50) UNIQUE NOT NULL,
    customer_id UUID NOT NULL REFERENCES customers(id),
    pickup_location GEOGRAPHY(POINT, 4326) NOT NULL,
    delivery_location GEOGRAPHY(POINT, 4326) NOT NULL,
    pickup_address TEXT NOT NULL,
    delivery_address TEXT NOT NULL,
    pickup_date TIMESTAMP WITH TIME ZONE NOT NULL,
    delivery_date TIMESTAMP WITH TIME ZONE NOT NULL,
    weight DECIMAL(10,2),
    volume DECIMAL(10,2),
    commodity_type VARCHAR(100),
    special_requirements TEXT[],
    status load_status_enum NOT NULL DEFAULT 'CREATED',
    assigned_driver_id UUID REFERENCES drivers(id),
    assigned_vehicle_id UUID REFERENCES vehicles(id),
    rate DECIMAL(10,2),
    distance_miles DECIMAL(8,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    load_id UUID NOT NULL REFERENCES loads(id),
    driver_id UUID REFERENCES drivers(id),
    vehicle_id UUID NOT NULL REFERENCES vehicles(id),
    origin_location GEOGRAPHY(POINT, 4326) NOT NULL,
    destination_location GEOGRAPHY(POINT, 4326) NOT NULL,
    waypoints GEOGRAPHY(POINT, 4326)[],
    route_geometry GEOGRAPHY(LINESTRING, 4326),
    planned_distance_miles DECIMAL(8,2),
    actual_distance_miles DECIMAL(8,2),
    planned_duration_minutes INTEGER,
    actual_duration_minutes INTEGER,
    estimated_arrival TIMESTAMP WITH TIME ZONE,
    actual_arrival TIMESTAMP WITH TIME ZONE,
    status route_status_enum NOT NULL DEFAULT 'PLANNED',
    optimization_score DECIMAL(5,2),
    fuel_estimate DECIMAL(8,2),
    toll_estimate DECIMAL(8,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Legacy shipments table for compatibility
CREATE TABLE shipments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    load_id UUID REFERENCES loads(id),
    shipment_number VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    weight DECIMAL(10,2),
    dimensions JSONB,
    value DECIMAL(12,2),
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Audit Logs Table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name TEXT NOT NULL,
    record_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL,
    changed_data JSONB,
    user_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_customers_company_name ON customers(company_name);
CREATE INDEX idx_carriers_status ON carriers(status);
CREATE INDEX idx_vehicles_carrier_id ON vehicles(carrier_id);
CREATE INDEX idx_vehicles_status ON vehicles(status);
CREATE INDEX idx_vehicles_type ON vehicles(vehicle_type);
CREATE INDEX idx_drivers_carrier_id ON drivers(carrier_id);
CREATE INDEX idx_drivers_status ON drivers(status);
CREATE INDEX idx_drivers_license_number ON drivers(license_number);
CREATE INDEX idx_loads_customer_id ON loads(customer_id);
CREATE INDEX idx_loads_status ON loads(status);
CREATE INDEX idx_loads_pickup_date ON loads(pickup_date);
CREATE INDEX idx_loads_assigned_driver ON loads(assigned_driver_id);
CREATE INDEX idx_loads_assigned_vehicle ON loads(assigned_vehicle_id);
CREATE INDEX idx_routes_load_id ON routes(load_id);
CREATE INDEX idx_routes_driver_id ON routes(driver_id);
CREATE INDEX idx_routes_vehicle_id ON routes(vehicle_id);
CREATE INDEX idx_routes_status ON routes(status);
CREATE INDEX idx_shipments_load_id ON shipments(load_id);

-- Spatial indexes
CREATE INDEX idx_vehicles_location ON vehicles USING GIST(current_location);
CREATE INDEX idx_drivers_location ON drivers USING GIST(current_location);
CREATE INDEX idx_loads_pickup_location ON loads USING GIST(pickup_location);
CREATE INDEX idx_loads_delivery_location ON loads USING GIST(delivery_location);
CREATE INDEX idx_routes_origin ON routes USING GIST(origin_location);
CREATE INDEX idx_routes_destination ON routes USING GIST(destination_location);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_carriers_updated_at BEFORE UPDATE ON carriers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_vehicles_updated_at BEFORE UPDATE ON vehicles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_drivers_updated_at BEFORE UPDATE ON drivers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_loads_updated_at BEFORE UPDATE ON loads FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_routes_updated_at BEFORE UPDATE ON routes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_shipments_updated_at BEFORE UPDATE ON shipments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data from sample_data.sql
\i /docker-entrypoint-initdb.d/sample_data.sql