"""WebSocket connection manager for TMS real-time events."""
import json
import logging
from typing import List, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time event broadcasting."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.websocket_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection and add it to active connections."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.websocket_connections.add(websocket)
        logger.info(f"WebSocket connection established. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection from active connections."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.websocket_connections:
            self.websocket_connections.remove(websocket)
        logger.info(f"WebSocket connection removed. Active connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        """Broadcast a message to all active WebSocket connections."""
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_json(self, data: dict):
        """Broadcast JSON data to all active WebSocket connections."""
        message = json.dumps(data)
        await self.broadcast(message)


# Global connection manager instance
manager = ConnectionManager()


async def broadcast_event_to_websockets(event_data: dict):
    """Broadcast event to all connected WebSocket clients."""
    if manager.active_connections:
        try:
            await manager.broadcast_json(event_data)
            logger.info(f"Broadcasted event to {len(manager.active_connections)} WebSocket clients")
        except Exception as e:
            logger.error(f"Error broadcasting event to WebSocket clients: {e}")
    else:
        logger.debug("No active WebSocket connections to broadcast to")
