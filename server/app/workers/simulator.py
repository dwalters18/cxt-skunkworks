"""Driver simulator — the demo's perception plane stand-in.

For every ACTIVE route it moves the driver toward the next open stop at a
scaled city speed and, on arrival, walks the stop through ARRIVED -> COMPLETED
via the API (the action plane) exactly as a driver app would. Between stops it
emits `driver.location-updated` telemetry directly onto the canonical backbone
through the validated publisher — the third producer flow after the API and CDC.

Reading route state straight from Postgres is a deliberate demo shortcut (a
real driver app would receive its itinerary); mutations always go through the
API so business events and CDC observations happen for real.
"""
from __future__ import annotations

import asyncio
import logging
import math
from datetime import datetime, timezone
from typing import Dict, List, Optional

import asyncpg
import httpx

from core.config import (
    API_BASE_URL,
    SIM_AUTO_START_ROUTES,
    SIM_DWELL_SECONDS,
    SIM_SPEED_MPH,
    SIM_SPEED_MULTIPLIER,
    SIM_TICK_SECONDS,
)
from core.envelope import EntityRef, EntityType, SourceSystem
from db.connections import databases
from eventbus.publisher import EventPublisher

logger = logging.getLogger(__name__)

ARRIVAL_RADIUS_MILES = 0.05  # ~80 m
EARTH_MILES = 3958.8


def haversine_miles(lat1, lng1, lat2, lng2) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return EARTH_MILES * 2 * math.asin(math.sqrt(h))


def heading_deg(lat1, lng1, lat2, lng2) -> float:
    y = math.sin(math.radians(lng2 - lng1)) * math.cos(math.radians(lat2))
    x = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - math.sin(
        math.radians(lat1)
    ) * math.cos(math.radians(lat2)) * math.cos(math.radians(lng2 - lng1))
    return (math.degrees(math.atan2(y, x)) + 360) % 360


class DriverSim:
    def __init__(self, driver_id: str, lat: float, lng: float):
        self.driver_id = driver_id
        self.lat = lat
        self.lng = lng
        self.dwell_until: Optional[datetime] = None

    def step_toward(self, lat: float, lng: float, miles: float) -> float:
        """Move up to `miles` toward the target; returns the heading."""
        dist = haversine_miles(self.lat, self.lng, lat, lng)
        hdg = heading_deg(self.lat, self.lng, lat, lng)
        if dist <= miles or dist == 0:
            self.lat, self.lng = lat, lng
        else:
            f = miles / dist
            self.lat += (lat - self.lat) * f
            self.lng += (lng - self.lng) * f
        return hdg


async def fetch_world(pg: asyncpg.Pool) -> Dict:
    """Active routes with their open stops, plus driver/vehicle positions."""
    routes = await pg.fetch(
        """
        SELECT r.id, r.route_number, r.driver_id, r.vehicle_id,
               ST_Y(d.current_location::geometry) AS lat,
               ST_X(d.current_location::geometry) AS lng
        FROM routes r JOIN drivers d ON d.id = r.driver_id
        WHERE r.status = 'ACTIVE' AND r.driver_id IS NOT NULL
        ORDER BY r.route_number
        """
    )
    stops = await pg.fetch(
        """
        SELECT s.id, s.route_id, s.sequence, s.status, s.kind,
               ST_Y(s.location::geometry) AS lat, ST_X(s.location::geometry) AS lng
        FROM stops s JOIN routes r ON r.id = s.route_id
        WHERE r.status = 'ACTIVE' AND s.status IN ('PENDING', 'ARRIVED')
        ORDER BY s.route_id, s.sequence
        """
    )
    stops_by_route: Dict[str, List] = {}
    for s in stops:
        stops_by_route.setdefault(str(s["route_id"]), []).append(s)
    return {"routes": routes, "stops_by_route": stops_by_route}


async def maybe_auto_start(pg: asyncpg.Pool, api: httpx.AsyncClient) -> None:
    """If nothing is active and auto-start is on, start the next staffed planned route."""
    candidate = await pg.fetchrow(
        """
        SELECT r.id, r.route_number FROM routes r
        WHERE r.status = 'PLANNED' AND r.driver_id IS NOT NULL AND r.vehicle_id IS NOT NULL
          AND EXISTS (SELECT 1 FROM stops s WHERE s.route_id = r.id)
        ORDER BY r.route_number LIMIT 1
        """
    )
    if candidate:
        logger.info("auto-starting route %s", candidate["route_number"])
        await api.post(f"/api/routes/{candidate['id']}/start")


async def run() -> None:
    pg = await databases.connect_postgres()
    publisher = EventPublisher()
    await publisher.start()
    sims: Dict[str, DriverSim] = {}

    step_miles = SIM_SPEED_MPH * SIM_SPEED_MULTIPLIER * SIM_TICK_SECONDS / 3600.0
    logger.info(
        "simulator: tick=%.1fs speed=%.0fmph x%.0f (%.2f mi/tick) dwell=%.0fs auto_start=%s",
        SIM_TICK_SECONDS, SIM_SPEED_MPH, SIM_SPEED_MULTIPLIER, step_miles,
        SIM_DWELL_SECONDS, SIM_AUTO_START_ROUTES,
    )

    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=10) as api:
        last_poll = 0.0
        world = {"routes": [], "stops_by_route": {}}
        while True:
            now = asyncio.get_event_loop().time()
            if now - last_poll >= 5.0:
                try:
                    world = await fetch_world(pg)
                    if SIM_AUTO_START_ROUTES and not world["routes"]:
                        await maybe_auto_start(pg, api)
                        world = await fetch_world(pg)
                    # Drop sims for drivers no longer on an active route.
                    active_ids = {str(r["driver_id"]) for r in world["routes"]}
                    for gone in set(sims) - active_ids:
                        del sims[gone]
                    last_poll = now
                except Exception as e:
                    logger.warning("world refresh failed: %s", e)
                    await asyncio.sleep(SIM_TICK_SECONDS)
                    continue

            for route in world["routes"]:
                driver_id = str(route["driver_id"])
                route_id = str(route["id"])
                open_stops = world["stops_by_route"].get(route_id, [])
                if not open_stops:
                    continue
                stop = open_stops[0]

                sim = sims.get(driver_id)
                if sim is None:
                    lat = route["lat"] if route["lat"] is not None else stop["lat"]
                    lng = route["lng"] if route["lng"] is not None else stop["lng"]
                    sim = sims[driver_id] = DriverSim(driver_id, float(lat), float(lng))

                speed = 0.0
                hdg = None
                wall_now = datetime.now(timezone.utc)

                if stop["status"] == "ARRIVED":
                    if sim.dwell_until is None:
                        sim.dwell_until = wall_now
                    if wall_now >= sim.dwell_until:
                        try:
                            resp = await api.post(f"/api/stops/{stop['id']}/status", json={"status": "COMPLETED"})
                            if resp.status_code >= 400:
                                logger.warning("complete stop failed: %s", resp.text)
                            sim.dwell_until = None
                            last_poll = 0  # re-read world next loop
                        except Exception as e:
                            logger.warning("complete stop error: %s", e)
                else:
                    dist = haversine_miles(sim.lat, sim.lng, float(stop["lat"]), float(stop["lng"]))
                    if dist <= ARRIVAL_RADIUS_MILES:
                        try:
                            resp = await api.post(f"/api/stops/{stop['id']}/status", json={"status": "ARRIVED"})
                            if resp.status_code >= 400:
                                logger.warning("arrive stop failed: %s", resp.text)
                            from datetime import timedelta

                            sim.dwell_until = wall_now + timedelta(seconds=SIM_DWELL_SECONDS)
                            last_poll = 0
                        except Exception as e:
                            logger.warning("arrive stop error: %s", e)
                    else:
                        hdg = sim.step_toward(float(stop["lat"]), float(stop["lng"]), step_miles)
                        speed = SIM_SPEED_MPH

                try:
                    await publisher.emit(
                        "driver.location-updated",
                        SourceSystem.SIMULATOR,
                        entity_refs=[
                            EntityRef(type=EntityType.DRIVER, id=driver_id),
                            EntityRef(type=EntityType.ROUTE, id=route_id),
                        ],
                        payload={
                            "driverId": driver_id,
                            "vehicleId": str(route["vehicle_id"]) if route["vehicle_id"] else None,
                            "routeId": route_id,
                            "location": {"latitude": round(sim.lat, 6), "longitude": round(sim.lng, 6)},
                            "speedMph": speed,
                            "headingDeg": round(hdg, 1) if hdg is not None else None,
                        },
                    )
                except Exception as e:
                    logger.warning("telemetry emit failed: %s", e)

            await asyncio.sleep(SIM_TICK_SECONDS)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    while True:
        try:
            asyncio.run(run())
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error("simulator crashed (%s); restarting in 5s", e)
            import time

            time.sleep(5)


if __name__ == "__main__":
    main()
