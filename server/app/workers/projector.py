"""Projector — the stream-processing worker that maintains read projections.

Consumes every canonical topic and keeps three views of the world current:

  1. TimescaleDB event_stream      — every envelope, queryable event log
  2. TimescaleDB driver_locations  — GPS telemetry as a hypertable
     (+ rate-limited current_location updates back into Postgres so the
      world model always knows roughly where everyone is)
  3. Neo4j graph                   — entities and relationships, built from
     *.record-* observation events (the world model as a graph)

Everything here is derivable from the event log; wipe the projections and they
rebuild from replay. That property is what demo reset leans on.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from core.catalog import CANONICAL_TOPICS
from core.envelope import EventEnvelope
from db.connections import databases
from eventbus.consumer import build_consumer, envelopes

logger = logging.getLogger(__name__)

# Neo4j uniqueness constraints — one per canonical node label.
CONSTRAINTS = [
    "CREATE CONSTRAINT customer_id IF NOT EXISTS FOR (n:Customer) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT depot_id    IF NOT EXISTS FOR (n:Depot)    REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT driver_id   IF NOT EXISTS FOR (n:Driver)   REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT vehicle_id  IF NOT EXISTS FOR (n:Vehicle)  REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT route_id    IF NOT EXISTS FOR (n:Route)    REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT order_id    IF NOT EXISTS FOR (n:Order)    REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT stop_id     IF NOT EXISTS FOR (n:Stop)     REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT parcel_id   IF NOT EXISTS FOR (n:Parcel)   REQUIRE n.id IS UNIQUE",
]


async def write_event_stream(envelope: EventEnvelope) -> None:
    ts = await databases.connect_timescale()
    await ts.execute(
        """
        INSERT INTO event_stream
            (time, event_id, event_type, event_version, source_system, tenant_id,
             trace_id, entity_refs, occurred_at, payload)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        ON CONFLICT DO NOTHING
        """,
        envelope.observed_at,
        envelope.event_id,
        envelope.event_type,
        envelope.event_version,
        envelope.source_system.value,
        envelope.tenant_id,
        envelope.trace_id,
        json.dumps([r.model_dump() for r in envelope.entity_refs]),
        envelope.occurred_at,
        json.dumps(envelope.payload),
    )


# --- driver telemetry -------------------------------------------------------

_last_pg_location_write: Dict[str, datetime] = {}
PG_LOCATION_WRITE_INTERVAL_S = 10


async def project_driver_location(envelope: EventEnvelope) -> None:
    p = envelope.payload
    loc = p.get("location") or {}
    lat, lng = loc.get("latitude"), loc.get("longitude")
    if lat is None or lng is None:
        return
    ts = await databases.connect_timescale()
    await ts.execute(
        """
        INSERT INTO driver_locations (time, tenant_id, driver_id, vehicle_id, route_id, location, speed_mph, heading_deg)
        VALUES ($1, $2, $3, $4, $5, ST_SetSRID(ST_MakePoint($6, $7), 4326)::geography, $8, $9)
        ON CONFLICT DO NOTHING
        """,
        envelope.occurred_at,
        envelope.tenant_id,
        p["driverId"],
        p.get("vehicleId"),
        p.get("routeId"),
        lng,
        lat,
        p.get("speedMph"),
        p.get("headingDeg"),
    )

    # Rate-limited write-back into the world model (which CDC then observes —
    # one hop, no loop: driver.record-updated events don't update Postgres).
    now = datetime.now(timezone.utc)
    last = _last_pg_location_write.get(p["driverId"])
    if last is None or (now - last).total_seconds() >= PG_LOCATION_WRITE_INTERVAL_S:
        _last_pg_location_write[p["driverId"]] = now
        pg = await databases.connect_postgres()
        await pg.execute(
            """
            UPDATE drivers SET current_location = ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography,
                   location_updated_at = $3
            WHERE id = $4::uuid
            """,
            lng,
            lat,
            now,
            p["driverId"],
        )
        if p.get("vehicleId"):
            await pg.execute(
                """
                UPDATE vehicles SET current_location = ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography
                WHERE id = $3::uuid
                """,
                lng,
                lat,
                p["vehicleId"],
            )


# --- graph projection --------------------------------------------------------

def _s(v: Any) -> Optional[str]:
    return str(v) if v is not None else None


async def project_graph(envelope: EventEnvelope) -> None:
    """Maintain the Neo4j projection from *.record-* observation events."""
    p = envelope.payload
    table, op = p.get("table"), p.get("op")
    row = p.get("after") or p.get("before") or {}
    node_id = _s(row.get("id"))
    if not table or not node_id:
        return

    driver = await databases.connect_neo4j()
    async with driver.session() as session:
        if op == "deleted":
            label = {
                "customers": "Customer", "depots": "Depot", "drivers": "Driver",
                "vehicles": "Vehicle", "routes": "Route", "orders": "Order",
                "stops": "Stop", "parcels": "Parcel",
            }.get(table)
            if label:
                await session.run(f"MATCH (n:{label} {{id: $id}}) DETACH DELETE n", id=node_id)
            return

        # Relationship targets are MERGEd as placeholder nodes so event order
        # never matters: if a parcel's event arrives before its order's, the
        # order node is created bare and filled in when its own event lands.
        if table == "customers":
            await session.run(
                "MERGE (n:Customer {id: $id}) SET n.name = $name, n.code = $code",
                id=node_id, name=row.get("name"), code=row.get("code"),
            )
        elif table == "depots":
            await session.run(
                "MERGE (n:Depot {id: $id}) SET n.name = $name",
                id=node_id, name=row.get("name"),
            )
        elif table == "drivers":
            await session.run(
                """
                MERGE (n:Driver {id: $id})
                SET n.name = $name, n.driverNumber = $number, n.status = $status
                """,
                id=node_id,
                name=f"{row.get('first_name', '')} {row.get('last_name', '')}".strip(),
                number=row.get("driver_number"),
                status=row.get("status"),
            )
            if row.get("home_depot_id"):
                await session.run(
                    """
                    MATCH (n:Driver {id: $id})
                    MERGE (d:Depot {id: $depot_id})
                    MERGE (n)-[:BASED_AT]->(d)
                    """,
                    id=node_id, depot_id=_s(row.get("home_depot_id")),
                )
        elif table == "vehicles":
            await session.run(
                """
                MERGE (n:Vehicle {id: $id})
                SET n.vehicleNumber = $number, n.status = $status, n.kind = $kind
                """,
                id=node_id,
                number=row.get("vehicle_number"),
                status=row.get("status"),
                kind=row.get("kind"),
            )
            if row.get("home_depot_id"):
                await session.run(
                    """
                    MATCH (n:Vehicle {id: $id})
                    MERGE (d:Depot {id: $depot_id})
                    MERGE (n)-[:BASED_AT]->(d)
                    """,
                    id=node_id, depot_id=_s(row.get("home_depot_id")),
                )
        elif table == "routes":
            await session.run(
                """
                MERGE (n:Route {id: $id})
                SET n.routeNumber = $number, n.status = $status, n.serviceDate = $service_date
                WITH n
                OPTIONAL MATCH (n)-[old:ASSIGNED_TO]->(:Driver) DELETE old
                WITH DISTINCT n
                OPTIONAL MATCH (n)-[oldv:USES]->(:Vehicle) DELETE oldv
                """,
                id=node_id,
                number=row.get("route_number"),
                status=row.get("status"),
                service_date=row.get("service_date"),
            )
            if row.get("driver_id"):
                await session.run(
                    """
                    MATCH (n:Route {id: $id})
                    MERGE (d:Driver {id: $driver_id})
                    MERGE (n)-[:ASSIGNED_TO]->(d)
                    """,
                    id=node_id, driver_id=_s(row.get("driver_id")),
                )
            if row.get("vehicle_id"):
                await session.run(
                    """
                    MATCH (n:Route {id: $id})
                    MERGE (v:Vehicle {id: $vehicle_id})
                    MERGE (n)-[:USES]->(v)
                    """,
                    id=node_id, vehicle_id=_s(row.get("vehicle_id")),
                )
        elif table == "orders":
            await session.run(
                """
                MERGE (n:Order {id: $id})
                SET n.orderNumber = $number, n.status = $status
                WITH n
                MERGE (c:Customer {id: $customer_id})
                MERGE (c)-[:PLACED]->(n)
                """,
                id=node_id,
                number=row.get("order_number"),
                status=row.get("status"),
                customer_id=_s(row.get("customer_id")),
            )
        elif table == "stops":
            await session.run(
                """
                MERGE (n:Stop {id: $id})
                SET n.kind = $kind, n.status = $status, n.sequence = $sequence, n.address = $address
                WITH n
                MERGE (o:Order {id: $order_id})
                MERGE (n)-[:FOR_ORDER]->(o)
                WITH n
                OPTIONAL MATCH (:Route)-[old:HAS_STOP]->(n) DELETE old
                """,
                id=node_id,
                kind=row.get("kind"),
                status=row.get("status"),
                sequence=row.get("sequence"),
                address=row.get("address"),
                order_id=_s(row.get("order_id")),
            )
            if row.get("route_id"):
                await session.run(
                    """
                    MATCH (n:Stop {id: $id})
                    MERGE (r:Route {id: $route_id})
                    MERGE (r)-[:HAS_STOP]->(n)
                    """,
                    id=node_id, route_id=_s(row.get("route_id")),
                )
        elif table == "parcels":
            await session.run(
                """
                MERGE (n:Parcel {id: $id})
                SET n.barcode = $barcode, n.status = $status
                WITH n
                MERGE (o:Order {id: $order_id})
                MERGE (o)-[:HAS_PARCEL]->(n)
                """,
                id=node_id,
                barcode=row.get("barcode"),
                status=row.get("status"),
                order_id=_s(row.get("order_id")),
            )


async def ensure_constraints() -> None:
    driver = await databases.connect_neo4j()
    async with driver.session() as session:
        for stmt in CONSTRAINTS:
            await session.run(stmt)
    logger.info("neo4j constraints ensured")


async def run() -> None:
    await databases.connect_timescale()
    await databases.connect_postgres()
    await ensure_constraints()

    # Groupless, replay-from-earliest: every start rebuilds projections from the
    # whole backbone. Writes are idempotent, so this is safe — and it IS the
    # demo's event-sourcing claim, exercised on every boot and every reset.
    # No consumer group + auto_offset_reset=earliest -> always reads from offset 0.
    consumer = build_consumer(CANONICAL_TOPICS, group_id=None, from_beginning=True)
    await consumer.start()
    logger.info("projector replaying %s from the beginning", CANONICAL_TOPICS)

    processed = 0
    try:
        async for _topic, envelope in envelopes(consumer):
            try:
                await write_event_stream(envelope)
                if envelope.event_type == "driver.location-updated":
                    await project_driver_location(envelope)
                elif envelope.event_type.split(".", 1)[1].startswith("record-"):
                    await project_graph(envelope)
                processed += 1
                if processed % 200 == 0:
                    logger.info("projected %d events", processed)
            except Exception as e:
                logger.error("projection error for %s: %s", envelope.event_type, e)
    finally:
        await consumer.stop()
        await databases.close()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    while True:
        try:
            asyncio.run(run())
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error("projector crashed (%s); restarting in 5s", e)
            import time

            time.sleep(5)


if __name__ == "__main__":
    main()
