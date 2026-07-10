-- LIP time-series projections (TimescaleDB)
--
-- Two hypertables, both written by the projector worker:
--   event_stream     every canonical event, verbatim envelope fields (the queryable event log)
--   driver_locations driver GPS telemetry unpacked for time/space queries

CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE event_stream (
    time          TIMESTAMPTZ NOT NULL,          -- observedAt
    event_id      UUID NOT NULL,
    event_type    TEXT NOT NULL,
    event_version TEXT NOT NULL,
    source_system TEXT NOT NULL,
    tenant_id     TEXT NOT NULL,
    trace_id      UUID,
    entity_refs   JSONB NOT NULL,
    occurred_at   TIMESTAMPTZ NOT NULL,
    payload       JSONB NOT NULL
);

SELECT create_hypertable('event_stream', 'time', chunk_time_interval => INTERVAL '1 day');

-- The projector replays the whole backbone on every start (event-sourced
-- projections); this unique index makes re-inserts no-ops.
CREATE UNIQUE INDEX ON event_stream (time, event_id);
CREATE INDEX ON event_stream (event_type, time DESC);
CREATE INDEX ON event_stream (source_system, time DESC);
CREATE INDEX ON event_stream USING GIN (entity_refs);

CREATE TABLE driver_locations (
    time        TIMESTAMPTZ NOT NULL,
    tenant_id   TEXT NOT NULL,
    driver_id   UUID NOT NULL,
    vehicle_id  UUID,
    route_id    UUID,
    location    GEOGRAPHY(POINT, 4326) NOT NULL,
    speed_mph   DOUBLE PRECISION,
    heading_deg DOUBLE PRECISION
);

SELECT create_hypertable('driver_locations', 'time', chunk_time_interval => INTERVAL '1 day');

CREATE UNIQUE INDEX ON driver_locations (time, driver_id);
CREATE INDEX ON driver_locations (driver_id, time DESC);
CREATE INDEX ON driver_locations USING GIST (location);
