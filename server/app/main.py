"""LIP demo API — FastAPI entrypoint.

Action plane + experience plane gateway: REST mutations over the world model
(each emitting canonical events), read endpoints over the three projections,
and a WebSocket that mirrors the canonical event backbone to the UI.
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.connections import databases
from eventbus.publisher import get_publisher
from routers import analytics, customers, drivers, events_api, graph, health, orders, routes_api, stops, vehicles, ws
from services.wsbus import pump_events_to_websockets

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("LIP API starting")
    await databases.connect_postgres()
    await databases.connect_timescale()
    await databases.connect_neo4j()
    await get_publisher()
    ws_pump = asyncio.create_task(pump_events_to_websockets())
    logger.info("LIP API ready")
    yield
    ws_pump.cancel()
    try:
        await ws_pump
    except asyncio.CancelledError:
        pass
    await databases.close()
    publisher = await get_publisher()
    await publisher.stop()
    logger.info("LIP API stopped")


app = FastAPI(
    title="LIP Demo API",
    description="Logistics Intelligence Platform proof-of-concept — canonical event backbone demo",
    version="1.0.0",
    lifespan=lifespan,
)

# The UI is served same-origin through nginx in Docker; CORS covers local dev
# (CRA dev server on :3000 talking straight to :8000).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (health, orders, routes_api, stops, drivers, vehicles, customers, events_api, analytics, graph):
    app.include_router(r.router, prefix="/api")
app.include_router(ws.router)
