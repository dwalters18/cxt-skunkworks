"""Demo reset — return the entire system to the seed state.

    make reset            (wraps: docker compose exec api python -m tools.demo_reset)

Order of operations:
  1. delete + recreate every lip.* topic (empty canonical backbone; the
     cdc.raw.* inbox is left alone — it is Debezium's, and source material
     rather than canonical state)
  2. truncate the Timescale projections (event_stream, driver_locations)
  3. wipe the Neo4j graph
  4. truncate + reseed Postgres from seed.sql — Debezium immediately re-emits
     the world as cdc.raw changes, the normalizer turns them into
     *.record-created events, and the projector rebuilds Timescale + Neo4j
  5. emit genesis intent events (order.created, route.planned) and the
     system.demo-reset marker, as lip-seeder

The seed is deterministic, so every reset lands on the identical world;
stop windows are relative to CURRENT_DATE, so it always reads as "today".
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
import time

from core.config import TENANT_ID
from core.envelope import EntityRef, EntityType, SourceSystem
from db.connections import databases
from eventbus.admin import reset_canonical_topics
from eventbus.publisher import EventPublisher

logger = logging.getLogger("demo_reset")

SEED_SQL_PATH = os.getenv("SEED_SQL_PATH", "/seed/seed.sql")
SEED_VERSION = "austin-v1"


async def reseed_postgres() -> None:
    pg = await databases.connect_postgres()
    sql = open(SEED_SQL_PATH).read()
    async with pg.acquire() as conn:
        await conn.execute(sql)
    logger.info("postgres reseeded from %s", SEED_SQL_PATH)


async def truncate_timescale() -> None:
    ts = await databases.connect_timescale()
    await ts.execute("TRUNCATE event_stream, driver_locations")
    logger.info("timescale projections truncated")


async def wipe_neo4j() -> None:
    driver = await databases.connect_neo4j()
    async with driver.session() as session:
        await session.run("MATCH (n) DETACH DELETE n")
    logger.info("neo4j graph wiped")


async def emit_genesis_events(publisher: EventPublisher) -> dict:
    """Re-narrate the seed world as intent events, so the business topics
    carry the world's origin story after a reset."""
    pg = await databases.connect_postgres()

    routes = await pg.fetch(
        """
        SELECT r.id, r.route_number, r.service_date, r.driver_id, r.vehicle_id,
               (SELECT COUNT(*) FROM stops s WHERE s.route_id = r.id) AS stop_count
        FROM routes r ORDER BY r.route_number
        """
    )
    for r in routes:
        await publisher.emit(
            "route.planned",
            SourceSystem.SEEDER,
            entity_refs=[
                EntityRef(type=EntityType.ROUTE, id=str(r["id"])),
                *([EntityRef(type=EntityType.DRIVER, id=str(r["driver_id"]))] if r["driver_id"] else []),
                *([EntityRef(type=EntityType.VEHICLE, id=str(r["vehicle_id"]))] if r["vehicle_id"] else []),
            ],
            payload={
                "routeId": str(r["id"]),
                "routeNumber": r["route_number"],
                "serviceDate": r["service_date"].isoformat(),
                "driverId": str(r["driver_id"]) if r["driver_id"] else None,
                "vehicleId": str(r["vehicle_id"]) if r["vehicle_id"] else None,
                "stopCount": r["stop_count"],
            },
        )

    orders = await pg.fetch(
        """
        SELECT o.id, o.order_number, o.service_level, o.notes,
               c.id AS customer_id, c.name AS customer_name,
               (SELECT COUNT(*) FROM parcels p WHERE p.order_id = o.id) AS parcel_count
        FROM orders o JOIN customers c ON c.id = o.customer_id
        ORDER BY o.order_number
        """
    )
    stops = await pg.fetch(
        """
        SELECT s.order_id, s.id, s.kind, s.address, s.window_start, s.window_end,
               ST_Y(s.location::geometry) AS lat, ST_X(s.location::geometry) AS lng
        FROM stops s
        """
    )
    stops_by_order = {}
    for s in stops:
        stops_by_order.setdefault(s["order_id"], {})[s["kind"]] = s

    def snapshot(s) -> dict:
        return {
            "stopId": str(s["id"]),
            "kind": s["kind"],
            "address": s["address"],
            "location": {"latitude": float(s["lat"]), "longitude": float(s["lng"])},
            "windowStart": s["window_start"].isoformat() if s["window_start"] else None,
            "windowEnd": s["window_end"].isoformat() if s["window_end"] else None,
        }

    for o in orders:
        pair = stops_by_order.get(o["id"], {})
        if "PICKUP" not in pair or "DELIVERY" not in pair:
            continue
        await publisher.emit(
            "order.created",
            SourceSystem.SEEDER,
            entity_refs=[
                EntityRef(type=EntityType.ORDER, id=str(o["id"])),
                EntityRef(type=EntityType.CUSTOMER, id=str(o["customer_id"])),
            ],
            payload={
                "orderId": str(o["id"]),
                "orderNumber": o["order_number"],
                "customerId": str(o["customer_id"]),
                "customerName": o["customer_name"],
                "serviceLevel": o["service_level"],
                "parcelCount": o["parcel_count"],
                "pickup": snapshot(pair["PICKUP"]),
                "delivery": snapshot(pair["DELIVERY"]),
                "notes": o["notes"],
            },
        )

    counts = {
        "routes": len(routes),
        "orders": len(orders),
        "drivers": await pg.fetchval("SELECT COUNT(*) FROM drivers"),
        "vehicles": await pg.fetchval("SELECT COUNT(*) FROM vehicles"),
        "customers": await pg.fetchval("SELECT COUNT(*) FROM customers"),
        "parcels": await pg.fetchval("SELECT COUNT(*) FROM parcels"),
        "stops": await pg.fetchval("SELECT COUNT(*) FROM stops"),
    }
    await publisher.emit(
        "system.demo-reset",
        SourceSystem.SEEDER,
        entity_refs=[EntityRef(type=EntityType.TENANT, id=TENANT_ID)],
        payload={"seedVersion": SEED_VERSION, "counts": counts},
    )
    return counts


async def main() -> int:
    t0 = time.monotonic()
    logger.info("=== demo reset: %s ===", SEED_VERSION)

    logger.info("[1/5] resetting kafka topics")
    await reset_canonical_topics()

    logger.info("[2/5] truncating timescale projections")
    await truncate_timescale()

    logger.info("[3/5] wiping neo4j graph")
    await wipe_neo4j()

    logger.info("[4/5] reseeding postgres world model")
    await reseed_postgres()

    logger.info("[5/5] emitting genesis events")
    publisher = EventPublisher()
    await publisher.start()
    try:
        counts = await emit_genesis_events(publisher)
    finally:
        await publisher.stop()

    await databases.close()
    elapsed = time.monotonic() - t0
    logger.info("=== demo reset complete in %.1fs — world: %s ===", elapsed, counts)
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    sys.exit(asyncio.run(main()))
