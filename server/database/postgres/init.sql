-- PostgreSQL initialization for TMS OLTP database
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- Create TMS domain tables
CREATE TABLE carriers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    mc_number VARCHAR(50),
    dot_number VARCHAR(50),
    contact_info JSONB,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE vehicles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    carrier_id UUID REFERENCES carriers(id),
    vehicle_number VARCHAR(100) NOT NULL,
    vehicle_type VARCHAR(100),
    capacity_weight DECIMAL(10,2),
    capacity_volume DECIMAL(10,2),
    status VARCHAR(50) DEFAULT 'available',
    current_location GEOGRAPHY(POINT),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE drivers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    carrier_id UUID REFERENCES carriers(id),
    license_number VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(255),
    status VARCHAR(50) DEFAULT 'available',
    current_location GEOGRAPHY(POINT),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE loads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    load_number VARCHAR(100) UNIQUE NOT NULL,
    shipper_id UUID,
    consignee_id UUID,
    carrier_id UUID REFERENCES carriers(id),
    vehicle_id UUID REFERENCES vehicles(id),
    driver_id UUID REFERENCES drivers(id),
    pickup_location GEOGRAPHY(POINT),
    delivery_location GEOGRAPHY(POINT),
    pickup_address TEXT,
    delivery_address TEXT,
    pickup_datetime TIMESTAMP,
    delivery_datetime TIMESTAMP,
    weight DECIMAL(10,2),
    volume DECIMAL(10,2),
    rate DECIMAL(10,2),
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE shipments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    load_id UUID REFERENCES loads(id),
    shipment_number VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    weight DECIMAL(10,2),
    dimensions JSONB,
    value DECIMAL(12,2),
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE routes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    load_id UUID REFERENCES loads(id),
    route_data JSONB,
    estimated_distance DECIMAL(10,2),
    estimated_duration INTEGER, -- in minutes
    actual_distance DECIMAL(10,2),
    actual_duration INTEGER,
    status VARCHAR(50) DEFAULT 'planned',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit Logs Table\nCREATE TABLE audit_logs (\n    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),\n    table_name TEXT NOT NULL,\n    record_id UUID NOT NULL,\n    action VARCHAR(50) NOT NULL,\n    changed_data JSONB,\n    user_id UUID,\n    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n);\n\n-- Create indexes for performance
CREATE INDEX idx_carriers_status ON carriers(status);
CREATE INDEX idx_vehicles_carrier_id ON vehicles(carrier_id);
CREATE INDEX idx_vehicles_status ON vehicles(status);
CREATE INDEX idx_drivers_carrier_id ON drivers(carrier_id);
CREATE INDEX idx_drivers_status ON drivers(status);
CREATE INDEX idx_loads_carrier_id ON loads(carrier_id);
CREATE INDEX idx_loads_status ON loads(status);
CREATE INDEX idx_loads_pickup_datetime ON loads(pickup_datetime);
CREATE INDEX idx_shipments_load_id ON shipments(load_id);
CREATE INDEX idx_routes_load_id ON routes(load_id);

-- Spatial indexes
CREATE INDEX idx_vehicles_location ON vehicles USING GIST(current_location);
CREATE INDEX idx_drivers_location ON drivers USING GIST(current_location);
CREATE INDEX idx_loads_pickup_location ON loads USING GIST(pickup_location);
CREATE INDEX idx_loads_delivery_location ON loads USING GIST(delivery_location);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_carriers_updated_at BEFORE UPDATE ON carriers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_vehicles_updated_at BEFORE UPDATE ON vehicles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_drivers_updated_at BEFORE UPDATE ON drivers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_loads_updated_at BEFORE UPDATE ON loads FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_shipments_updated_at BEFORE UPDATE ON shipments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_routes_updated_at BEFORE UPDATE ON routes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data
INSERT INTO carriers (name, mc_number, dot_number, contact_info) VALUES
('ABC Transportation', 'MC123456', 'DOT789012', '{"phone": "+1-555-0101", "email": "dispatch@abc-transport.com"}'),
('XYZ Logistics', 'MC234567', 'DOT890123', '{"phone": "+1-555-0102", "email": "ops@xyz-logistics.com"}'),
('FastTrack Freight', 'MC345678', 'DOT901234', '{"phone": "+1-555-0103", "email": "bookings@fasttrack.com"}');

INSERT INTO vehicles (carrier_id, vehicle_number, vehicle_type, capacity_weight, capacity_volume, current_location) 
SELECT 
    c.id, 
    'TRK-' || (ROW_NUMBER() OVER())::text,
    'Semi-Truck',
    80000.00,
    4000.00,
    ST_GeogFromText('POINT(-95.3698 29.7604)') -- Houston, TX
FROM carriers c;

INSERT INTO drivers (carrier_id, license_number, name, phone, email, current_location)
SELECT 
    c.id,
    'DL' || LPAD((ROW_NUMBER() OVER())::text, 8, '0'),
    'Driver ' || (ROW_NUMBER() OVER())::text,
    '+1-555-' || LPAD((1000 + ROW_NUMBER() OVER())::text, 4, '0'),
    'driver' || (ROW_NUMBER() OVER())::text || '@example.com',
    ST_GeogFromText('POINT(-95.3698 29.7604)') -- Houston, TX
FROM carriers c;
