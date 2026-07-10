"""WebSocket bus — one ConnectionManager, fed by one Kafka consumer.

The API process runs a single background task that consumes every canonical
topic and fans each envelope out to all connected UI clients verbatim (camelCase
wire form). The UI therefore sees exactly what is on the backbone — the Event
Console renders raw envelopes, the dispatch map picks out driver.location-updated.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Set

from fastapi import WebSocket

from core.catalog import CANONICAL_TOPICS
from eventbus.consumer import build_consumer, envelopes

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.add(ws)
        logger.info("ws client connected (%d total)", len(self._connections))

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.discard(ws)

    @property
    def count(self) -> int:
        return len(self._connections)

    async def broadcast_json(self, data: dict) -> None:
        if not self._connections:
            return
        text = json.dumps(data)
        dead = []
        for ws in self._connections:
            try:
                await ws.send_text(text)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


async def pump_events_to_websockets() -> None:
    """Consume lip.* and broadcast every envelope to connected clients. Runs forever."""
    while True:
        consumer = build_consumer(CANONICAL_TOPICS, group_id="lip-ws-bridge")
        try:
            await consumer.start()
            logger.info("ws bridge consuming %s", CANONICAL_TOPICS)
            async for _topic, envelope in envelopes(consumer):
                await manager.broadcast_json(envelope.to_wire())
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.warning("ws bridge consumer error (%s); reconnecting in 3s", e)
            await asyncio.sleep(3)
        finally:
            try:
                await consumer.stop()
            except Exception:
                pass
