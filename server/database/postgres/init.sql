-- LIP world model — system of record (PostgreSQL + PostGIS)
--
-- Canonical vocabulary: Customer, Order, Stop, Route, Driver, Vehicle, Parcel, Depot.
--   * Orders have exactly two stops: one PICKUP and one DELIVERY (stops.order_id + kind).
--   * Stops belong to routes: assigning an order to a route sets route_id + sequence
--     on its stops. Unrouted orders have stops with route_id NULL.
--   * Parcels belong to orders.
--
-- Everything is tenant-scoped; the demo runs a single tenant ('cxt-demo').

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

CREATE TYPE order_status AS ENUM ('CREATED', 'ASSIGNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED');
CREATE TYPE stop_kind    AS ENUM ('PICKUP', 'DELIVERY');
CREATE TYPE stop_status  AS ENUM ('PENDING', 'ARRIVED', 'COMPLETED', 'FAILED');
CREATE TYPE route_status AS ENUM ('PLANNED', 'ACTIVE', 'COMPLETED');
CREATE TYPE driver_status  AS ENUM ('AVAILABLE', 'ON_ROUTE', 'OFF_DUTY');
CREATE TYPE vehicle_status AS ENUM ('AVAILABLE', 'IN_SERVICE', 'MAINTENANCE');
CREATE TYPE parcel_status  AS ENUM ('PENDING', 'PICKED_UP', 'DELIVERED');

CREATE TABLE tenants (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE customers (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   TEXT NOT NULL REFERENCES tenants(id),
    code        TEXT UNIQUE NOT NULL,
    name        TEXT NOT NULL,
    contact_name TEXT,
    email       TEXT,
    phone       TEXT,
    address     TEXT NOT NULL,
    location    GEOGRAPHY(POINT, 4326) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE depots (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   TEXT NOT NULL REFERENCES tenants(id),
    name        TEXT NOT NULL,
    address     TEXT NOT NULL,
    location    GEOGRAPHY(POINT, 4326) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE drivers (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id     TEXT NOT NULL REFERENCES tenants(id),
    driver_number TEXT UNIQUE NOT NULL,
    first_name    TEXT NOT NULL,
    last_name     TEXT NOT NULL,
    phone         TEXT,
    email         TEXT,
    status        driver_status NOT NULL DEFAULT 'AVAILABLE',
    home_depot_id UUID REFERENCES depots(id),
    current_location    GEOGRAPHY(POINT, 4326),
    location_updated_at TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE vehicles (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id      TEXT NOT NULL REFERENCES tenants(id),
    vehicle_number TEXT UNIQUE NOT NULL,
    kind           TEXT NOT NULL,               -- VAN | BOX_TRUCK
    make           TEXT,
    model          TEXT,
    capacity_parcels INTEGER,
    status         vehicle_status NOT NULL DEFAULT 'AVAILABLE',
    home_depot_id  UUID REFERENCES depots(id),
    current_location GEOGRAPHY(POINT, 4326),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE routes (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id    TEXT NOT NULL REFERENCES tenants(id),
    route_number TEXT UNIQUE NOT NULL,
    service_date DATE NOT NULL,
    status       route_status NOT NULL DEFAULT 'PLANNED',
    driver_id    UUID REFERENCES drivers(id),
    vehicle_id   UUID REFERENCES vehicles(id),
    started_at   TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE orders (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id    TEXT NOT NULL REFERENCES tenants(id),
    order_number TEXT UNIQUE NOT NULL,
    customer_id  UUID NOT NULL REFERENCES customers(id),
    status       order_status NOT NULL DEFAULT 'CREATED',
    notes        TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE stops (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id    TEXT NOT NULL REFERENCES tenants(id),
    order_id     UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    route_id     UUID REFERENCES routes(id),
    kind         stop_kind NOT NULL,
    sequence     INTEGER,                        -- position within the route, when routed
    status       stop_status NOT NULL DEFAULT 'PENDING',
    address      TEXT NOT NULL,
    location     GEOGRAPHY(POINT, 4326) NOT NULL,
    window_start TIMESTAMPTZ,
    window_end   TIMESTAMPTZ,
    eta          TIMESTAMPTZ,
    arrived_at   TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (order_id, kind)                      -- an order has one pickup and one delivery
);

CREATE TABLE parcels (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   TEXT NOT NULL REFERENCES tenants(id),
    order_id    UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    barcode     TEXT UNIQUE NOT NULL,
    description TEXT,
    weight_kg   NUMERIC(6, 2),
    status      parcel_status NOT NULL DEFAULT 'PENDING',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_orders_status      ON orders (status);
CREATE INDEX idx_orders_customer    ON orders (customer_id);
CREATE INDEX idx_stops_order        ON stops (order_id);
CREATE INDEX idx_stops_route        ON stops (route_id, sequence);
CREATE INDEX idx_stops_status       ON stops (status);
CREATE INDEX idx_parcels_order      ON parcels (order_id);
CREATE INDEX idx_routes_status      ON routes (status);
CREATE INDEX idx_routes_driver      ON routes (driver_id);
CREATE INDEX idx_drivers_status     ON drivers (status);
CREATE INDEX idx_vehicles_status    ON vehicles (status);
CREATE INDEX idx_stops_location     ON stops USING GIST (location);
CREATE INDEX idx_drivers_location   ON drivers USING GIST (current_location);

-- updated_at maintenance
CREATE OR REPLACE FUNCTION touch_updated_at() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY['customers','depots','drivers','vehicles','routes','orders','stops','parcels']
    LOOP
        EXECUTE format(
            'CREATE TRIGGER trg_%s_updated_at BEFORE UPDATE ON %s
             FOR EACH ROW EXECUTE FUNCTION touch_updated_at()', t, t);
    END LOOP;
END $$;

-- Debezium: full row images on update/delete so record-changed events carry
-- an honest before/after pair.
ALTER TABLE customers REPLICA IDENTITY FULL;
ALTER TABLE depots    REPLICA IDENTITY FULL;
ALTER TABLE drivers   REPLICA IDENTITY FULL;
ALTER TABLE vehicles  REPLICA IDENTITY FULL;
ALTER TABLE routes    REPLICA IDENTITY FULL;
ALTER TABLE orders    REPLICA IDENTITY FULL;
ALTER TABLE stops     REPLICA IDENTITY FULL;
ALTER TABLE parcels   REPLICA IDENTITY FULL;
