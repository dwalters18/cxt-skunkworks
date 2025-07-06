"""WebSocket endpoints for real-time TMS communication."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
import logging
import json
import asyncio

from websocket_manager import ConnectionManager, broadcast_event_to_websockets

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])

# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/events")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time event streaming."""
    await manager.connect(websocket)
    logger.info("WebSocket client connected")
    
    try:
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "message": "Connected to TMS event stream"
        }))
        
        # Keep the connection alive by listening for client disconnect or optional messages
        while True:
            try:
                # Use asyncio.wait_for with timeout to prevent blocking
                data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                message = json.loads(data)
                
                # Handle client messages if needed (e.g., subscription filters)
                if message.get("type") == "subscribe":
                    # Client wants to subscribe to specific event types
                    event_types = message.get("event_types", [])
                    logger.info(f"Client subscribed to event types: {event_types}")
                    
                    # Send acknowledgment
                    await websocket.send_text(json.dumps({
                        "type": "subscription_confirmed",
                        "event_types": event_types,
                        "message": "Successfully subscribed to events"
                    }))
                
                elif message.get("type") == "ping":
                    # Handle ping/pong for connection health
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    }))
                    
            except asyncio.TimeoutError:
                # Timeout is normal - client doesn't need to send messages
                # Just continue to keep connection alive
                continue
            except json.JSONDecodeError:
                logger.warning("Received invalid JSON from WebSocket client")
                continue
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.get("/active-connections")
async def get_active_connections():
    """Get count of active WebSocket connections."""
    try:
        return {
            "active_connections": len(manager.active_connections),
            "status": "healthy" if len(manager.active_connections) >= 0 else "no_connections"
        }
    except Exception as e:
        logger.error(f"Error getting active connections: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get connection status: {str(e)}")


@router.post("/broadcast")
async def broadcast_message(message: dict):
    """Manually broadcast a message to all connected clients (for testing)."""
    try:
        # Validate message structure
        if "type" not in message:
            raise HTTPException(status_code=400, detail="Message must have a 'type' field")
        
        # Broadcast to all connected clients
        await manager.broadcast(message)
        
        return {
            "message": "Broadcast sent successfully",
            "recipients": len(manager.active_connections),
            "data": message
        }
    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to broadcast message: {str(e)}")


# Helper function for broadcasting events (used by other routers)
async def broadcast_event_to_websockets(event_data: dict):
    """Broadcast event to all WebSocket connections."""
    try:
        await manager.broadcast({
            "type": "event",
            "data": event_data
        })
    except Exception as e:
        logger.error(f"Error broadcasting event to WebSockets: {e}")
