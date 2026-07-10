"""WebSocket endpoint: /ws — streams every canonical event to the UI."""
from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from services.wsbus import manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            # Client messages are ignored; the socket is a one-way event feed.
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception:
        manager.disconnect(ws)
