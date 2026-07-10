"""Database connections: Postgres (world model), TimescaleDB (projections), Neo4j (graph)."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

import asyncpg
from neo4j import AsyncDriver, AsyncGraphDatabase

from core.config import (
    NEO4J_PASSWORD,
    NEO4J_URL,
    NEO4J_USER,
    POSTGRES_URL,
    TIMESCALE_URL,
)

logger = logging.getLogger(__name__)


async def _pool_with_retry(url: str, name: str, **kwargs: Any) -> asyncpg.Pool:
    delay = 2.0
    for attempt in range(6):
        try:
            pool = await asyncpg.create_pool(url, min_size=1, max_size=10, **kwargs)
            logger.info("%s pool ready", name)
            return pool
        except Exception as e:
            if attempt == 5:
                raise
            logger.warning("%s not ready (%s); retrying in %.0fs", name, e, delay)
            await asyncio.sleep(delay)
            delay = min(delay * 2, 15)
    raise RuntimeError("unreachable")


class Databases:
    """Lazily-initialized connection holder shared within a process."""

    def __init__(self) -> None:
        self.pg: Optional[asyncpg.Pool] = None
        self.ts: Optional[asyncpg.Pool] = None
        self.neo4j: Optional[AsyncDriver] = None

    async def connect_postgres(self) -> asyncpg.Pool:
        if self.pg is None:
            self.pg = await _pool_with_retry(POSTGRES_URL, "postgres")
        return self.pg

    async def connect_timescale(self) -> asyncpg.Pool:
        if self.ts is None:
            self.ts = await _pool_with_retry(TIMESCALE_URL, "timescale")
        return self.ts

    async def connect_neo4j(self) -> AsyncDriver:
        if self.neo4j is None:
            driver = AsyncGraphDatabase.driver(NEO4J_URL, auth=(NEO4J_USER, NEO4J_PASSWORD))
            delay = 2.0
            for attempt in range(6):
                try:
                    await driver.verify_connectivity()
                    break
                except Exception as e:
                    if attempt == 5:
                        raise
                    logger.warning("neo4j not ready (%s); retrying in %.0fs", e, delay)
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, 15)
            self.neo4j = driver
            logger.info("neo4j driver ready")
        return self.neo4j

    async def close(self) -> None:
        if self.pg:
            await self.pg.close()
        if self.ts:
            await self.ts.close()
        if self.neo4j:
            await self.neo4j.close()


databases = Databases()
