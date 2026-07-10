"""Analytics endpoints — honest aggregates over the world model and event log."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from routers.deps import get_pg, get_ts

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
async def summary(pg=Depends(get_pg), ts=Depends(get_ts)):
    orders = await pg.fetchrow(
        """
        SELECT COUNT(*) AS total,
               COUNT(*) FILTER (WHERE status = 'CREATED')     AS created,
               COUNT(*) FILTER (WHERE status = 'ASSIGNED')    AS assigned,
               COUNT(*) FILTER (WHERE status = 'IN_PROGRESS') AS in_progress,
               COUNT(*) FILTER (WHERE status = 'COMPLETED')   AS completed,
               COUNT(*) FILTER (WHERE status = 'CANCELLED')   AS cancelled
        FROM orders
        """
    )
    stops = await pg.fetchrow(
        """
        SELECT COUNT(*) AS total,
               COUNT(*) FILTER (WHERE status = 'COMPLETED') AS completed,
               COUNT(*) FILTER (WHERE status = 'COMPLETED'
                                AND completed_at <= window_end) AS completed_in_window
        FROM stops
        """
    )
    routes = await pg.fetchrow(
        """
        SELECT COUNT(*) AS total,
               COUNT(*) FILTER (WHERE status = 'PLANNED')   AS planned,
               COUNT(*) FILTER (WHERE status = 'ACTIVE')    AS active,
               COUNT(*) FILTER (WHERE status = 'COMPLETED') AS completed
        FROM routes
        """
    )
    drivers = await pg.fetchrow(
        """
        SELECT COUNT(*) AS total,
               COUNT(*) FILTER (WHERE status = 'AVAILABLE') AS available,
               COUNT(*) FILTER (WHERE status = 'ON_ROUTE')  AS on_route,
               COUNT(*) FILTER (WHERE status = 'OFF_DUTY')  AS off_duty
        FROM drivers
        """
    )
    vehicles = await pg.fetchrow(
        """
        SELECT COUNT(*) AS total,
               COUNT(*) FILTER (WHERE status = 'AVAILABLE')   AS available,
               COUNT(*) FILTER (WHERE status = 'IN_SERVICE')  AS in_service,
               COUNT(*) FILTER (WHERE status = 'MAINTENANCE') AS maintenance
        FROM vehicles
        """
    )
    parcels = await pg.fetchrow(
        """
        SELECT COUNT(*) AS total,
               COUNT(*) FILTER (WHERE status = 'DELIVERED') AS delivered
        FROM parcels
        """
    )
    events_last_hour = await ts.fetchval(
        "SELECT COUNT(*) FROM event_stream WHERE time > NOW() - INTERVAL '1 hour'"
    )

    completed = stops["completed"] or 0
    in_window = stops["completed_in_window"] or 0
    on_time_pct = round(100.0 * in_window / completed, 1) if completed else None

    return {
        "orders": dict(orders),
        "stops": {**dict(stops), "onTimePercentage": on_time_pct},
        "routes": dict(routes),
        "drivers": dict(drivers),
        "vehicles": dict(vehicles),
        "parcels": dict(parcels),
        "eventsLastHour": events_last_hour,
    }


@router.get("/events-by-type")
async def events_by_type(hours: int = 24, ts=Depends(get_ts)):
    rows = await ts.fetch(
        """
        SELECT event_type, source_system, COUNT(*) AS count
        FROM event_stream
        WHERE time > NOW() - make_interval(hours => $1)
        GROUP BY event_type, source_system
        ORDER BY count DESC
        """,
        hours,
    )
    return {"buckets": [dict(r) for r in rows], "hours": hours}


@router.get("/event-volume")
async def event_volume(minutes: int = 60, ts=Depends(get_ts)):
    rows = await ts.fetch(
        """
        SELECT time_bucket('1 minute', time) AS minute,
               COUNT(*) AS count
        FROM event_stream
        WHERE time > NOW() - make_interval(mins => $1)
        GROUP BY minute ORDER BY minute
        """,
        minutes,
    )
    return {
        "points": [
            {"minute": r["minute"].isoformat(), "count": r["count"]} for r in rows
        ],
        "minutes": minutes,
    }
