"""Graph endpoints — the world-model-as-graph demo surface (Neo4j).

The projector maintains the graph from canonical events; these queries show why
a graph projection earns its keep: blast-radius questions are one traversal.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from db.connections import databases

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/impact/driver/{driver_id}")
async def driver_impact(driver_id: str):
    """If this driver goes down right now, what work is affected?"""
    driver = await databases.connect_neo4j()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (d:Driver {id: $driver_id})
            OPTIONAL MATCH (r:Route)-[:ASSIGNED_TO]->(d)
            OPTIONAL MATCH (r)-[:HAS_STOP]->(s:Stop)
            OPTIONAL MATCH (s)-[:FOR_ORDER]->(o:Order)
            OPTIONAL MATCH (c:Customer)-[:PLACED]->(o)
            WITH d, r, s, o, c
            RETURN d.name AS driver_name,
                   collect(DISTINCT {id: r.id, routeNumber: r.routeNumber, status: r.status}) AS routes,
                   count(DISTINCT s) AS stop_count,
                   collect(DISTINCT {id: o.id, orderNumber: o.orderNumber, status: o.status,
                                     customer: c.name}) AS orders
            """,
            driver_id=driver_id,
        )
        record = await result.single()
    if not record or record["driver_name"] is None:
        raise HTTPException(404, "driver not found in graph (projector may still be catching up)")
    routes = [r for r in record["routes"] if r["id"] is not None]
    orders = [o for o in record["orders"] if o["id"] is not None]
    open_orders = [o for o in orders if o["status"] not in ("COMPLETED", "CANCELLED")]
    return {
        "driverId": driver_id,
        "driverName": record["driver_name"],
        "routes": routes,
        "stopCount": record["stop_count"],
        "ordersAffected": orders,
        "openOrdersAffected": open_orders,
        "summary": (
            f"{record['driver_name']}: {len(routes)} route(s), "
            f"{record['stop_count']} stop(s), {len(open_orders)} open order(s) affected"
        ),
    }


@router.get("/overview")
async def graph_overview():
    """Node/relationship counts — proves the graph projection is alive."""
    driver = await databases.connect_neo4j()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS c ORDER BY label"
        )
        nodes = {r["label"]: r["c"] async for r in result}
        result = await session.run(
            "MATCH ()-[r]->() RETURN type(r) AS rel, count(r) AS c ORDER BY rel"
        )
        rels = {r["rel"]: r["c"] async for r in result}
    return {"nodes": nodes, "relationships": rels}
