"""World model service — reads and mutations over the canonical entities.

Every mutation follows the same discipline:
  1. write the world model (Postgres, the system of record)
  2. emit the matching business event through the canonical envelope

CDC picks up the row changes independently and emits *.record-* observation
events, so consumers can watch either the intent stream or the change stream.

API JSON is camelCase — the same wire dialect as the event payloads.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import asyncpg

from core.envelope import EntityRef, EntityType, SourceSystem
from eventbus.publisher import EventPublisher

logger = logging.getLogger(__name__)


class WorldError(Exception):
    """Domain-rule violation (maps to HTTP 4xx in routers)."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _iso(v: Optional[datetime]) -> Optional[str]:
    return v.astimezone(timezone.utc).isoformat().replace("+00:00", "Z") if v else None


# ---------------------------------------------------------------------------
# Row -> JSON shapes
# ---------------------------------------------------------------------------

STOP_COLUMNS = """
    s.id AS stop_id, s.order_id, s.route_id, s.kind, s.sequence, s.status AS stop_status,
    s.address, ST_Y(s.location::geometry) AS latitude, ST_X(s.location::geometry) AS longitude,
    s.window_start, s.window_end, s.eta, s.arrived_at, s.completed_at
"""


def stop_json(r: asyncpg.Record) -> Dict[str, Any]:
    return {
        "stopId": str(r["stop_id"]),
        "orderId": str(r["order_id"]),
        "routeId": str(r["route_id"]) if r["route_id"] else None,
        "kind": r["kind"],
        "sequence": r["sequence"],
        "status": r["stop_status"],
        "address": r["address"],
        "latitude": float(r["latitude"]),
        "longitude": float(r["longitude"]),
        "windowStart": _iso(r["window_start"]),
        "windowEnd": _iso(r["window_end"]),
        "eta": _iso(r["eta"]),
        "arrivedAt": _iso(r["arrived_at"]),
        "completedAt": _iso(r["completed_at"]),
    }


def parcel_json(r: asyncpg.Record) -> Dict[str, Any]:
    return {
        "id": str(r["id"]),
        "barcode": r["barcode"],
        "description": r["description"],
        "weightKg": float(r["weight_kg"]) if r["weight_kg"] is not None else None,
        "status": r["status"],
    }


async def _compose_orders(pg: asyncpg.Pool, order_rows: List[asyncpg.Record]) -> List[Dict[str, Any]]:
    if not order_rows:
        return []
    ids = [r["id"] for r in order_rows]
    stop_rows = await pg.fetch(
        f"SELECT {STOP_COLUMNS} FROM stops s WHERE s.order_id = ANY($1)", ids
    )
    parcel_rows = await pg.fetch(
        "SELECT id, order_id, barcode, description, weight_kg, status FROM parcels WHERE order_id = ANY($1) ORDER BY barcode",
        ids,
    )
    route_rows = await pg.fetch(
        """
        SELECT r.id AS route_id, r.route_number, r.status AS route_status,
               d.id AS driver_id, d.first_name || ' ' || d.last_name AS driver_name
        FROM routes r LEFT JOIN drivers d ON d.id = r.driver_id
        WHERE r.id IN (SELECT DISTINCT route_id FROM stops WHERE order_id = ANY($1) AND route_id IS NOT NULL)
        """,
        ids,
    )
    routes_by_id = {str(r["route_id"]): r for r in route_rows}
    stops_by_order: Dict[Any, Dict[str, Dict[str, Any]]] = {}
    for s in stop_rows:
        stops_by_order.setdefault(s["order_id"], {})[s["kind"]] = stop_json(s)
    parcels_by_order: Dict[Any, List[Dict[str, Any]]] = {}
    for p in parcel_rows:
        parcels_by_order.setdefault(p["order_id"], []).append(parcel_json(p))

    out = []
    for r in order_rows:
        stops = stops_by_order.get(r["id"], {})
        pickup = stops.get("PICKUP")
        delivery = stops.get("DELIVERY")
        route_id = (pickup or delivery or {}).get("routeId")
        route = routes_by_id.get(route_id) if route_id else None
        out.append(
            {
                "id": str(r["id"]),
                "orderNumber": r["order_number"],
                "status": r["status"],
                "notes": r["notes"],
                "customer": {
                    "id": str(r["customer_id"]),
                    "code": r["customer_code"],
                    "name": r["customer_name"],
                },
                "parcelCount": len(parcels_by_order.get(r["id"], [])),
                "parcels": parcels_by_order.get(r["id"], []),
                "pickup": pickup,
                "delivery": delivery,
                "routeId": route_id,
                "routeNumber": route["route_number"] if route else None,
                "driverName": route["driver_name"] if route else None,
                "createdAt": _iso(r["created_at"]),
                "updatedAt": _iso(r["updated_at"]),
            }
        )
    return out


ORDER_BASE_QUERY = """
    SELECT o.id, o.order_number, o.status, o.notes, o.created_at, o.updated_at,
           c.id AS customer_id, c.code AS customer_code, c.name AS customer_name
    FROM orders o JOIN customers c ON c.id = o.customer_id
"""


async def list_orders(
    pg: asyncpg.Pool,
    status: Optional[str] = None,
    unassigned: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> Dict[str, Any]:
    conditions, params = [], []
    if status:
        params.append(status.upper())
        conditions.append(f"o.status = ${len(params)}::order_status")
    if unassigned:
        conditions.append(
            "NOT EXISTS (SELECT 1 FROM stops s WHERE s.order_id = o.id AND s.route_id IS NOT NULL)"
        )
        conditions.append("o.status NOT IN ('CANCELLED', 'COMPLETED')")
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.extend([limit, offset])
    rows = await pg.fetch(
        f"{ORDER_BASE_QUERY} {where} ORDER BY o.order_number LIMIT ${len(params)-1} OFFSET ${len(params)}",
        *params,
    )
    count_params = params[:-2]
    total = await pg.fetchval(
        f"SELECT COUNT(*) FROM orders o {where}", *count_params
    )
    return {"orders": await _compose_orders(pg, rows), "total": total, "limit": limit, "offset": offset}


async def get_order(pg: asyncpg.Pool, order_id: str) -> Dict[str, Any]:
    rows = await pg.fetch(f"{ORDER_BASE_QUERY} WHERE o.id = $1", _uuid(order_id))
    if not rows:
        raise WorldError("order not found", 404)
    return (await _compose_orders(pg, rows))[0]


def _uuid(v: str):
    import uuid as _u

    try:
        return _u.UUID(v)
    except ValueError:
        raise WorldError(f"invalid id: {v}", 400)


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------


async def create_order(
    pg: asyncpg.Pool,
    publisher: EventPublisher,
    tenant_id: str,
    customer_id: str,
    pickup: Dict[str, Any],
    delivery: Dict[str, Any],
    parcel_count: int = 1,
    notes: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create an order with its pickup and delivery stops and its parcels."""
    customer = await pg.fetchrow(
        "SELECT id, code, name FROM customers WHERE id = $1", _uuid(customer_id)
    )
    if not customer:
        raise WorldError("customer not found", 404)

    async with pg.acquire() as conn:
        async with conn.transaction():
            order_number = await conn.fetchval(
                "SELECT 'ORD-' || (1000 + COUNT(*) + 1)::text FROM orders"
            )
            # Avoid rare collisions with cancelled/legacy numbering.
            exists = await conn.fetchval(
                "SELECT 1 FROM orders WHERE order_number = $1", order_number
            )
            if exists:
                order_number = await conn.fetchval(
                    "SELECT 'ORD-' || (EXTRACT(EPOCH FROM NOW())::bigint)::text"
                )
            row = await conn.fetchrow(
                """
                INSERT INTO orders (tenant_id, order_number, customer_id, status, notes)
                VALUES ($1, $2, $3, 'CREATED', $4) RETURNING id
                """,
                tenant_id,
                order_number,
                customer["id"],
                notes,
            )
            order_pk = row["id"]
            for kind, side in (("PICKUP", pickup), ("DELIVERY", delivery)):
                await conn.execute(
                    """
                    INSERT INTO stops (tenant_id, order_id, kind, status, address, location, window_start, window_end)
                    VALUES ($1, $2, $3::stop_kind, 'PENDING', $4,
                            ST_SetSRID(ST_MakePoint($5, $6), 4326)::geography, $7, $8)
                    """,
                    tenant_id,
                    order_pk,
                    kind,
                    side["address"],
                    side["longitude"],
                    side["latitude"],
                    side.get("windowStart"),
                    side.get("windowEnd"),
                )
            for k in range(1, parcel_count + 1):
                await conn.execute(
                    """
                    INSERT INTO parcels (tenant_id, order_id, barcode, description, status)
                    VALUES ($1, $2, $3, 'Parcel', 'PENDING')
                    """,
                    tenant_id,
                    order_pk,
                    f"PCL-{order_number.removeprefix('ORD-')}-{k}",
                )

    order = await get_order(pg, str(order_pk))
    await publisher.emit(
        "order.created",
        SourceSystem.API,
        entity_refs=[
            EntityRef(type=EntityType.ORDER, id=str(order_pk)),
            EntityRef(type=EntityType.CUSTOMER, id=str(customer["id"])),
        ],
        payload={
            "orderId": str(order_pk),
            "orderNumber": order_number,
            "customerId": str(customer["id"]),
            "customerName": customer["name"],
            "parcelCount": parcel_count,
            "pickup": _stop_snapshot(order["pickup"]),
            "delivery": _stop_snapshot(order["delivery"]),
            "notes": notes,
        },
        trace_id=trace_id,
    )
    return order


def _stop_snapshot(stop: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "stopId": stop["stopId"],
        "kind": stop["kind"],
        "address": stop["address"],
        "location": {"latitude": stop["latitude"], "longitude": stop["longitude"]},
        "windowStart": stop["windowStart"],
        "windowEnd": stop["windowEnd"],
    }


async def assign_order_to_route(
    pg: asyncpg.Pool,
    publisher: EventPublisher,
    order_id: str,
    route_id: str,
    trace_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Attach the order's stops to a route (pickup then delivery, at the end)."""
    order_pk, route_pk = _uuid(order_id), _uuid(route_id)
    order = await pg.fetchrow("SELECT id, order_number, status FROM orders WHERE id = $1", order_pk)
    if not order:
        raise WorldError("order not found", 404)
    if order["status"] not in ("CREATED",):
        raise WorldError(f"order {order['order_number']} is {order['status']}; only CREATED orders can be assigned")
    route = await pg.fetchrow(
        """
        SELECT r.id, r.route_number, r.status, r.driver_id, r.vehicle_id
        FROM routes r WHERE r.id = $1
        """,
        route_pk,
    )
    if not route:
        raise WorldError("route not found", 404)
    if route["status"] == "COMPLETED":
        raise WorldError(f"route {route['route_number']} is completed")

    async with pg.acquire() as conn:
        async with conn.transaction():
            max_seq = await conn.fetchval(
                "SELECT COALESCE(MAX(sequence), 0) FROM stops WHERE route_id = $1", route_pk
            )
            await conn.execute(
                """
                UPDATE stops SET route_id = $1,
                       sequence = CASE kind WHEN 'PICKUP' THEN $2 ELSE $3 END
                WHERE order_id = $4
                """,
                route_pk,
                max_seq + 1,
                max_seq + 2,
                order_pk,
            )
            await conn.execute(
                "UPDATE orders SET status = 'ASSIGNED' WHERE id = $1", order_pk
            )

    await publisher.emit(
        "order.assigned",
        SourceSystem.API,
        entity_refs=[
            EntityRef(type=EntityType.ORDER, id=str(order_pk)),
            EntityRef(type=EntityType.ROUTE, id=str(route_pk)),
            *( [EntityRef(type=EntityType.DRIVER, id=str(route["driver_id"]))] if route["driver_id"] else [] ),
            *( [EntityRef(type=EntityType.VEHICLE, id=str(route["vehicle_id"]))] if route["vehicle_id"] else [] ),
        ],
        payload={
            "orderId": str(order_pk),
            "orderNumber": order["order_number"],
            "routeId": str(route_pk),
            "routeNumber": route["route_number"],
            "driverId": str(route["driver_id"]) if route["driver_id"] else None,
            "vehicleId": str(route["vehicle_id"]) if route["vehicle_id"] else None,
        },
        trace_id=trace_id,
    )
    return await get_order(pg, order_id)


async def cancel_order(
    pg: asyncpg.Pool,
    publisher: EventPublisher,
    order_id: str,
    reason: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> Dict[str, Any]:
    order_pk = _uuid(order_id)
    order = await pg.fetchrow("SELECT id, order_number, status FROM orders WHERE id = $1", order_pk)
    if not order:
        raise WorldError("order not found", 404)
    if order["status"] in ("COMPLETED", "CANCELLED"):
        raise WorldError(f"order is already {order['status']}")

    async with pg.acquire() as conn:
        async with conn.transaction():
            await conn.execute("UPDATE orders SET status = 'CANCELLED' WHERE id = $1", order_pk)
            await conn.execute(
                """
                UPDATE stops SET route_id = NULL, sequence = NULL, status = 'FAILED'
                WHERE order_id = $1 AND status IN ('PENDING', 'ARRIVED')
                """,
                order_pk,
            )

    await publisher.emit(
        "order.cancelled",
        SourceSystem.API,
        entity_refs=[EntityRef(type=EntityType.ORDER, id=str(order_pk))],
        payload={
            "orderId": str(order_pk),
            "orderNumber": order["order_number"],
            "reason": reason,
        },
        trace_id=trace_id,
    )
    return await get_order(pg, order_id)


# --- Routes ---------------------------------------------------------------

ROUTE_BASE_QUERY = """
    SELECT r.id, r.route_number, r.service_date, r.status, r.started_at, r.completed_at,
           r.created_at, r.updated_at,
           d.id AS driver_id, d.first_name || ' ' || d.last_name AS driver_name,
           v.id AS vehicle_id, v.vehicle_number
    FROM routes r
    LEFT JOIN drivers d ON d.id = r.driver_id
    LEFT JOIN vehicles v ON v.id = r.vehicle_id
"""


async def _compose_routes(pg: asyncpg.Pool, route_rows: List[asyncpg.Record]) -> List[Dict[str, Any]]:
    if not route_rows:
        return []
    ids = [r["id"] for r in route_rows]
    stop_rows = await pg.fetch(
        f"""
        SELECT {STOP_COLUMNS}, o.order_number
        FROM stops s JOIN orders o ON o.id = s.order_id
        WHERE s.route_id = ANY($1)
        ORDER BY s.sequence NULLS LAST
        """,
        ids,
    )
    stops_by_route: Dict[Any, List[Dict[str, Any]]] = {}
    for s in stop_rows:
        j = stop_json(s)
        j["orderNumber"] = s["order_number"]
        stops_by_route.setdefault(s["route_id"], []).append(j)

    out = []
    for r in route_rows:
        stops = stops_by_route.get(r["id"], [])
        out.append(
            {
                "id": str(r["id"]),
                "routeNumber": r["route_number"],
                "serviceDate": r["service_date"].isoformat(),
                "status": r["status"],
                "driver": {"id": str(r["driver_id"]), "name": r["driver_name"]} if r["driver_id"] else None,
                "vehicle": {"id": str(r["vehicle_id"]), "vehicleNumber": r["vehicle_number"]} if r["vehicle_id"] else None,
                "stops": stops,
                "stopsTotal": len(stops),
                "stopsCompleted": sum(1 for s in stops if s["status"] == "COMPLETED"),
                "startedAt": _iso(r["started_at"]),
                "completedAt": _iso(r["completed_at"]),
            }
        )
    return out


async def list_routes(pg: asyncpg.Pool, status: Optional[str] = None) -> List[Dict[str, Any]]:
    conditions, params = [], []
    if status:
        params.append(status.upper())
        conditions.append(f"r.status = ${len(params)}::route_status")
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = await pg.fetch(f"{ROUTE_BASE_QUERY} {where} ORDER BY r.route_number")
    return await _compose_routes(pg, rows)


async def get_route(pg: asyncpg.Pool, route_id: str) -> Dict[str, Any]:
    rows = await pg.fetch(f"{ROUTE_BASE_QUERY} WHERE r.id = $1", _uuid(route_id))
    if not rows:
        raise WorldError("route not found", 404)
    return (await _compose_routes(pg, rows))[0]


async def create_route(
    pg: asyncpg.Pool,
    publisher: EventPublisher,
    tenant_id: str,
    driver_id: Optional[str] = None,
    vehicle_id: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> Dict[str, Any]:
    async with pg.acquire() as conn:
        async with conn.transaction():
            route_number = await conn.fetchval(
                "SELECT 'RT-' || (100 + COUNT(*) + 1)::text FROM routes"
            )
            row = await conn.fetchrow(
                """
                INSERT INTO routes (tenant_id, route_number, service_date, status, driver_id, vehicle_id)
                VALUES ($1, $2, CURRENT_DATE, 'PLANNED', $3, $4) RETURNING id
                """,
                tenant_id,
                route_number,
                _uuid(driver_id) if driver_id else None,
                _uuid(vehicle_id) if vehicle_id else None,
            )
    route = await get_route(pg, str(row["id"]))
    await publisher.emit(
        "route.planned",
        SourceSystem.API,
        entity_refs=[
            EntityRef(type=EntityType.ROUTE, id=route["id"]),
            *( [EntityRef(type=EntityType.DRIVER, id=driver_id)] if driver_id else [] ),
            *( [EntityRef(type=EntityType.VEHICLE, id=vehicle_id)] if vehicle_id else [] ),
        ],
        payload={
            "routeId": route["id"],
            "routeNumber": route["routeNumber"],
            "serviceDate": route["serviceDate"],
            "driverId": driver_id,
            "vehicleId": vehicle_id,
            "stopCount": 0,
        },
        trace_id=trace_id,
    )
    return route


async def start_route(
    pg: asyncpg.Pool,
    publisher: EventPublisher,
    route_id: str,
    trace_id: Optional[str] = None,
) -> Dict[str, Any]:
    route_pk = _uuid(route_id)
    route = await pg.fetchrow(
        "SELECT id, route_number, status, driver_id, vehicle_id FROM routes WHERE id = $1", route_pk
    )
    if not route:
        raise WorldError("route not found", 404)
    if route["status"] != "PLANNED":
        raise WorldError(f"route {route['route_number']} is {route['status']}; only PLANNED routes can start")
    if not route["driver_id"] or not route["vehicle_id"]:
        raise WorldError(f"route {route['route_number']} needs a driver and a vehicle before starting")
    has_stops = await pg.fetchval("SELECT 1 FROM stops WHERE route_id = $1 LIMIT 1", route_pk)
    if not has_stops:
        raise WorldError(f"route {route['route_number']} has no stops")

    async with pg.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "UPDATE routes SET status = 'ACTIVE', started_at = NOW() WHERE id = $1", route_pk
            )
            await conn.execute(
                "UPDATE drivers SET status = 'ON_ROUTE' WHERE id = $1", route["driver_id"]
            )
            await conn.execute(
                "UPDATE vehicles SET status = 'IN_SERVICE' WHERE id = $1", route["vehicle_id"]
            )
            await conn.execute(
                "UPDATE orders SET status = 'IN_PROGRESS' WHERE status = 'ASSIGNED' AND id IN (SELECT DISTINCT order_id FROM stops WHERE route_id = $1)",
                route_pk,
            )

    await publisher.emit(
        "route.started",
        SourceSystem.API,
        entity_refs=[
            EntityRef(type=EntityType.ROUTE, id=str(route_pk)),
            EntityRef(type=EntityType.DRIVER, id=str(route["driver_id"])),
            EntityRef(type=EntityType.VEHICLE, id=str(route["vehicle_id"])),
        ],
        payload={
            "routeId": str(route_pk),
            "routeNumber": route["route_number"],
            "driverId": str(route["driver_id"]),
            "vehicleId": str(route["vehicle_id"]),
        },
        trace_id=trace_id,
    )
    return await get_route(pg, route_id)


# --- Stops ------------------------------------------------------------------

VALID_STOP_TRANSITIONS = {
    "PENDING": {"ARRIVED", "FAILED"},
    "ARRIVED": {"COMPLETED", "FAILED"},
    "COMPLETED": set(),
    "FAILED": set(),
}


async def update_stop_status(
    pg: asyncpg.Pool,
    publisher: EventPublisher,
    stop_id: str,
    new_status: str,
    trace_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Move a stop through its lifecycle, cascading order/route/driver state."""
    new_status = new_status.upper()
    stop_pk = _uuid(stop_id)
    stop = await pg.fetchrow(
        """
        SELECT s.id, s.order_id, s.route_id, s.kind, s.status, o.order_number
        FROM stops s JOIN orders o ON o.id = s.order_id WHERE s.id = $1
        """,
        stop_pk,
    )
    if not stop:
        raise WorldError("stop not found", 404)
    if new_status not in VALID_STOP_TRANSITIONS:
        raise WorldError(f"invalid stop status {new_status}")
    if new_status not in VALID_STOP_TRANSITIONS[stop["status"]]:
        raise WorldError(
            f"stop is {stop['status']}; cannot transition to {new_status}"
        )

    order_completed = False
    route_completed_id = None
    async with pg.acquire() as conn:
        async with conn.transaction():
            ts_col = {"ARRIVED": "arrived_at", "COMPLETED": "completed_at"}.get(new_status)
            set_ts = f", {ts_col} = NOW()" if ts_col else ""
            await conn.execute(
                f"UPDATE stops SET status = $1::stop_status{set_ts} WHERE id = $2",
                new_status,
                stop_pk,
            )
            if new_status == "COMPLETED":
                if stop["kind"] == "PICKUP":
                    await conn.execute(
                        "UPDATE parcels SET status = 'PICKED_UP' WHERE order_id = $1 AND status = 'PENDING'",
                        stop["order_id"],
                    )
                    await conn.execute(
                        "UPDATE orders SET status = 'IN_PROGRESS' WHERE id = $1 AND status IN ('CREATED','ASSIGNED')",
                        stop["order_id"],
                    )
                else:  # DELIVERY completes the order
                    await conn.execute(
                        "UPDATE parcels SET status = 'DELIVERED' WHERE order_id = $1", stop["order_id"]
                    )
                    await conn.execute(
                        "UPDATE orders SET status = 'COMPLETED' WHERE id = $1", stop["order_id"]
                    )
                    order_completed = True
            # Route completion: no PENDING/ARRIVED stops left
            if stop["route_id"]:
                open_stops = await conn.fetchval(
                    "SELECT COUNT(*) FROM stops WHERE route_id = $1 AND status IN ('PENDING','ARRIVED')",
                    stop["route_id"],
                )
                if open_stops == 0:
                    route = await conn.fetchrow(
                        "UPDATE routes SET status = 'COMPLETED', completed_at = NOW() WHERE id = $1 AND status = 'ACTIVE' RETURNING id, route_number, driver_id, vehicle_id",
                        stop["route_id"],
                    )
                    if route:
                        route_completed_id = route
                        if route["driver_id"]:
                            await conn.execute(
                                "UPDATE drivers SET status = 'AVAILABLE' WHERE id = $1", route["driver_id"]
                            )
                        if route["vehicle_id"]:
                            await conn.execute(
                                "UPDATE vehicles SET status = 'AVAILABLE' WHERE id = $1", route["vehicle_id"]
                            )

    refs = [
        EntityRef(type=EntityType.STOP, id=str(stop_pk)),
        EntityRef(type=EntityType.ORDER, id=str(stop["order_id"])),
    ]
    if stop["route_id"]:
        refs.append(EntityRef(type=EntityType.ROUTE, id=str(stop["route_id"])))
    await publisher.emit(
        "stop.status-updated",
        SourceSystem.API,
        entity_refs=refs,
        payload={
            "stopId": str(stop_pk),
            "orderId": str(stop["order_id"]),
            "routeId": str(stop["route_id"]) if stop["route_id"] else None,
            "kind": stop["kind"],
            "previousStatus": stop["status"],
            "status": new_status,
        },
        trace_id=trace_id,
    )
    if order_completed:
        await publisher.emit(
            "order.completed",
            SourceSystem.API,
            entity_refs=[EntityRef(type=EntityType.ORDER, id=str(stop["order_id"]))],
            payload={
                "orderId": str(stop["order_id"]),
                "orderNumber": stop["order_number"],
                "routeId": str(stop["route_id"]) if stop["route_id"] else None,
            },
            trace_id=trace_id,
        )
    if route_completed_id:
        await publisher.emit(
            "route.completed",
            SourceSystem.API,
            entity_refs=[EntityRef(type=EntityType.ROUTE, id=str(route_completed_id["id"]))],
            payload={
                "routeId": str(route_completed_id["id"]),
                "routeNumber": route_completed_id["route_number"],
            },
            trace_id=trace_id,
        )

    row = await pg.fetchrow(f"SELECT {STOP_COLUMNS} FROM stops s WHERE s.id = $1", stop_pk)
    return stop_json(row)


# --- Drivers / Vehicles / Customers / Depots --------------------------------


async def list_drivers(pg: asyncpg.Pool) -> List[Dict[str, Any]]:
    rows = await pg.fetch(
        """
        SELECT d.id, d.driver_number, d.first_name, d.last_name, d.phone, d.email, d.status,
               ST_Y(d.current_location::geometry) AS latitude,
               ST_X(d.current_location::geometry) AS longitude,
               d.location_updated_at,
               r.id AS route_id, r.route_number, r.status AS route_status
        FROM drivers d
        LEFT JOIN routes r ON r.driver_id = d.id AND r.status = 'ACTIVE'
        ORDER BY d.driver_number
        """
    )
    return [
        {
            "id": str(r["id"]),
            "driverNumber": r["driver_number"],
            "firstName": r["first_name"],
            "lastName": r["last_name"],
            "name": f"{r['first_name']} {r['last_name']}",
            "phone": r["phone"],
            "email": r["email"],
            "status": r["status"],
            "latitude": float(r["latitude"]) if r["latitude"] is not None else None,
            "longitude": float(r["longitude"]) if r["longitude"] is not None else None,
            "locationUpdatedAt": _iso(r["location_updated_at"]),
            "activeRouteId": str(r["route_id"]) if r["route_id"] else None,
            "activeRouteNumber": r["route_number"],
        }
        for r in rows
    ]


async def update_driver_status(
    pg: asyncpg.Pool,
    publisher: EventPublisher,
    driver_id: str,
    new_status: str,
    trace_id: Optional[str] = None,
) -> Dict[str, Any]:
    new_status = new_status.upper()
    if new_status not in ("AVAILABLE", "ON_ROUTE", "OFF_DUTY"):
        raise WorldError(f"invalid driver status {new_status}")
    prev = await pg.fetchval("SELECT status FROM drivers WHERE id = $1", _uuid(driver_id))
    if prev is None:
        raise WorldError("driver not found", 404)
    row = await pg.fetchrow(
        "UPDATE drivers SET status = $1::driver_status WHERE id = $2 RETURNING id, first_name, last_name, status",
        new_status,
        _uuid(driver_id),
    )
    await publisher.emit(
        "driver.status-updated",
        SourceSystem.API,
        entity_refs=[EntityRef(type=EntityType.DRIVER, id=driver_id)],
        payload={
            "driverId": driver_id,
            "driverName": f"{row['first_name']} {row['last_name']}",
            "previousStatus": prev,
            "status": new_status,
        },
        trace_id=trace_id,
    )
    drivers = await list_drivers(pg)
    return next(d for d in drivers if d["id"] == driver_id)


async def list_vehicles(pg: asyncpg.Pool) -> List[Dict[str, Any]]:
    rows = await pg.fetch(
        """
        SELECT v.id, v.vehicle_number, v.kind, v.make, v.model, v.capacity_parcels, v.status,
               ST_Y(v.current_location::geometry) AS latitude,
               ST_X(v.current_location::geometry) AS longitude,
               r.id AS route_id, r.route_number
        FROM vehicles v
        LEFT JOIN routes r ON r.vehicle_id = v.id AND r.status = 'ACTIVE'
        ORDER BY v.vehicle_number
        """
    )
    return [
        {
            "id": str(r["id"]),
            "vehicleNumber": r["vehicle_number"],
            "kind": r["kind"],
            "make": r["make"],
            "model": r["model"],
            "capacityParcels": r["capacity_parcels"],
            "status": r["status"],
            "latitude": float(r["latitude"]) if r["latitude"] is not None else None,
            "longitude": float(r["longitude"]) if r["longitude"] is not None else None,
            "activeRouteId": str(r["route_id"]) if r["route_id"] else None,
            "activeRouteNumber": r["route_number"],
        }
        for r in rows
    ]


async def update_vehicle_status(
    pg: asyncpg.Pool,
    publisher: EventPublisher,
    vehicle_id: str,
    new_status: str,
    trace_id: Optional[str] = None,
) -> Dict[str, Any]:
    new_status = new_status.upper()
    if new_status not in ("AVAILABLE", "IN_SERVICE", "MAINTENANCE"):
        raise WorldError(f"invalid vehicle status {new_status}")
    prev = await pg.fetchval("SELECT status FROM vehicles WHERE id = $1", _uuid(vehicle_id))
    if prev is None:
        raise WorldError("vehicle not found", 404)
    row = await pg.fetchrow(
        "UPDATE vehicles SET status = $1::vehicle_status WHERE id = $2 RETURNING id, vehicle_number",
        new_status,
        _uuid(vehicle_id),
    )
    await publisher.emit(
        "vehicle.status-updated",
        SourceSystem.API,
        entity_refs=[EntityRef(type=EntityType.VEHICLE, id=vehicle_id)],
        payload={
            "vehicleId": vehicle_id,
            "vehicleNumber": row["vehicle_number"],
            "previousStatus": prev,
            "status": new_status,
        },
        trace_id=trace_id,
    )
    vehicles = await list_vehicles(pg)
    return next(v for v in vehicles if v["id"] == vehicle_id)


async def list_customers(pg: asyncpg.Pool) -> List[Dict[str, Any]]:
    rows = await pg.fetch(
        """
        SELECT c.id, c.code, c.name, c.contact_name, c.email, c.phone, c.address,
               ST_Y(c.location::geometry) AS latitude, ST_X(c.location::geometry) AS longitude,
               COUNT(o.id) AS order_count
        FROM customers c LEFT JOIN orders o ON o.customer_id = c.id
        GROUP BY c.id ORDER BY c.name
        """
    )
    return [
        {
            "id": str(r["id"]),
            "code": r["code"],
            "name": r["name"],
            "contactName": r["contact_name"],
            "email": r["email"],
            "phone": r["phone"],
            "address": r["address"],
            "latitude": float(r["latitude"]),
            "longitude": float(r["longitude"]),
            "orderCount": r["order_count"],
        }
        for r in rows
    ]


async def list_depots(pg: asyncpg.Pool) -> List[Dict[str, Any]]:
    rows = await pg.fetch(
        """
        SELECT id, name, address,
               ST_Y(location::geometry) AS latitude, ST_X(location::geometry) AS longitude
        FROM depots ORDER BY name
        """
    )
    return [
        {
            "id": str(r["id"]),
            "name": r["name"],
            "address": r["address"],
            "latitude": float(r["latitude"]),
            "longitude": float(r["longitude"]),
        }
        for r in rows
    ]
