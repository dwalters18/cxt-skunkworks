"""FastAPI dependencies shared by all routers."""
from __future__ import annotations

import asyncpg
from fastapi import Request

from db.connections import databases
from eventbus.publisher import EventPublisher, get_publisher


async def get_pg() -> asyncpg.Pool:
    return await databases.connect_postgres()


async def get_ts() -> asyncpg.Pool:
    return await databases.connect_timescale()


async def get_events(request: Request) -> EventPublisher:
    return await get_publisher()


def get_trace_id(request: Request) -> str | None:
    """Propagate a caller-supplied trace id so one UI action correlates its events."""
    return request.headers.get("x-trace-id")
