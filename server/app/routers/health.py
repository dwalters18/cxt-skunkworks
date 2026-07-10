"""Health endpoints. /api/health/live is liveness (always 200 once the app is up);
/api/health reports each dependency so `make up` and humans can see readiness."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, Response

from db.connections import databases
from eventbus.publisher import get_publisher

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def live():
    return {"status": "ok"}


@router.get("")
async def health(response: Response):
    checks = {}

    async def check(name, coro):
        try:
            await asyncio.wait_for(coro, timeout=5)
            checks[name] = "ok"
        except Exception as e:
            checks[name] = f"error: {e}"

    async def pg_check():
        pool = await databases.connect_postgres()
        await pool.fetchval("SELECT 1")

    async def ts_check():
        pool = await databases.connect_timescale()
        await pool.fetchval("SELECT 1")

    async def neo4j_check():
        driver = await databases.connect_neo4j()
        await driver.verify_connectivity()

    async def kafka_check():
        await get_publisher()  # connects on first call

    await asyncio.gather(
        check("postgres", pg_check()),
        check("timescale", ts_check()),
        check("neo4j", neo4j_check()),
        check("kafka", kafka_check()),
    )

    healthy = all(v == "ok" for v in checks.values())
    if not healthy:
        response.status_code = 503
    return {"status": "ok" if healthy else "degraded", "dependencies": checks}
