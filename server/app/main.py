# server/app/main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import asyncio
import logging
import json
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List, Optional, Set

# TMS Imports
from models.domain import (
    CreateLoadRequest, AssignLoadRequest, UpdateLocationRequest,
    LoadSearchRequest, VehicleTrackingData, Load, Vehicle, Driver
)
from models.events import EventType, BaseEvent
from database.connections import (
    get_db_manager, get_load_repository, get_vehicle_repository,
    get_timescale_repository, get_neo4j_repository, get_audit_repository, DatabaseManager
)
from kafka.producer import get_producer, emit_load_created, emit_vehicle_location_update, emit_load_status_change
from kafka.consumer import get_consumer, TMSEventConsumer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
consumer_task: Optional[asyncio.Task] = None
websocket_connections: Set[WebSocket] = set()

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        websocket_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections.copy():
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                self.disconnect(connection)

manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting TMS API...")
    
    # Initialize database connections
    db_manager = await get_db_manager()
    
    # Initialize Kafka producer
    producer = await get_producer()
    
    # Start Kafka consumer in background
    global consumer_task
    consumer = await get_consumer("tms-api-group")
    await consumer.start()
    consumer_task = asyncio.create_task(consumer.consume_events())
    
    logger.info("TMS API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down TMS API...")
    
    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
    
    consumer = await get_consumer()
    await consumer.stop()
    
    await db_manager.close()
    logger.info("TMS API shutdown complete")


app = FastAPI(
    title="TMS Event-Driven API",
    description="Transportation Management System with Event-Driven Architecture",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health Check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "tms-api"
    }


# Load Management Endpoints
@app.post("/api/loads", response_model=Dict[str, str])
async def create_load(load_request: CreateLoadRequest, background_tasks: BackgroundTasks):
    """Create a new load and emit event"""
    try:
        load_repo = await get_load_repository()
        
        # Create load in database
        load_data = load_request.model_dump()
        load_id = await load_repo.create_load(load_data)
        # Audit log
        audit_repo = await get_audit_repository()
        await audit_repo.log_action("loads", load_id, "create", load_data)
        
        # Emit load created event
        background_tasks.add_task(
            emit_load_created, 
            {**load_data, "load_id": load_id}
        )
        
        return {"load_id": load_id, "status": "created"}
        
    except Exception as e:
        logger.error(f"Error creating load: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/loads", response_model=List[Dict])
async def search_loads(
    status: Optional[str] = None,
    carrier_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Search loads with filters"""
    try:
        load_repo = await get_load_repository()
        
        filters = {}
        if status:
            filters['status'] = status
        if carrier_id:
            filters['carrier_id'] = carrier_id
        
        loads = await load_repo.search_loads(filters, limit, offset)
        return [dict(load) for load in loads]
        
    except Exception as e:
        logger.error(f"Error searching loads: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/loads/{load_id}")
async def get_load(load_id: str):
    """Get load details"""
    try:
        load_repo = await get_load_repository()
        load = await load_repo.get_load(load_id)
        
        if not load:
            raise HTTPException(status_code=404, detail="Load not found")
        
        return dict(load)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting load: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/loads/{load_id}/assign")
async def assign_load(load_id: str, assignment: AssignLoadRequest, background_tasks: BackgroundTasks):
    """Assign load to carrier/vehicle/driver"""
    try:
        load_repo = await get_load_repository()
        
        # Assign load in database
        await load_repo.assign_load(
            load_id,
            assignment.carrier_id,
            assignment.vehicle_id,
            assignment.driver_id
        )
        # Audit log
        audit_repo = await get_audit_repository()
        await audit_repo.log_action("loads", load_id, "assign", assignment.model_dump())
        
        # Emit load assigned event
        background_tasks.add_task(
            emit_load_status_change,
            {
                "load_id": load_id,
                "carrier_id": assignment.carrier_id,
                "vehicle_id": assignment.vehicle_id,
                "driver_id": assignment.driver_id,
                "old_status": "pending",
                "new_status": "assigned"
            },
            EventType.LOAD_ASSIGNED
        )
        
        return {"status": "assigned"}
        
    except Exception as e:
        logger.error(f"Error assigning load: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/loads/{load_id}/status")
async def update_load_status(load_id: str, status_update: Dict[str, str], background_tasks: BackgroundTasks):
    """Update load status"""
    try:
        new_status = status_update.get("status")
        if not new_status:
            raise HTTPException(status_code=400, detail="Status is required")
        
        load_repo = await get_load_repository()
        
        # Get current load to determine old status
        current_load = await load_repo.get_load(load_id)
        if not current_load:
            raise HTTPException(status_code=404, detail="Load not found")
        
        old_status = current_load['status']
        
        # Update status in database
        await load_repo.update_load_status(load_id, new_status)
        
        # Emit appropriate event based on new status
        event_type_mapping = {
            "picked_up": EventType.LOAD_PICKED_UP,
            "in_transit": EventType.LOAD_IN_TRANSIT,
            "delivered": EventType.LOAD_DELIVERED,
            "cancelled": EventType.LOAD_CANCELLED
        }
        
        event_type = event_type_mapping.get(new_status, EventType.LOAD_IN_TRANSIT)
        
        background_tasks.add_task(
            emit_load_status_change,
            {
                "load_id": load_id,
                "old_status": old_status,
                "new_status": new_status
            },
            event_type
        )
        
        return {"status": "updated"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating load status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Vehicle Management Endpoints
@app.get("/api/vehicles")
async def get_vehicles(carrier_id: Optional[str] = None, status: Optional[str] = None):
    """Get vehicles with optional filters"""
    try:
        vehicle_repo = await get_vehicle_repository()
        
        if status == "available":
            vehicles = await vehicle_repo.get_available_vehicles(carrier_id)
        else:
            # For now, just get available vehicles as example
            vehicles = await vehicle_repo.get_available_vehicles(carrier_id)
        
        return [dict(vehicle) for vehicle in vehicles]
        
    except Exception as e:
        logger.error(f"Error getting vehicles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/vehicles/{vehicle_id}/location")
async def update_vehicle_location(vehicle_id: str, location_update: UpdateLocationRequest, background_tasks: BackgroundTasks):
    """Update vehicle location and emit tracking event"""
    try:
        vehicle_repo = await get_vehicle_repository()
        timescale_repo = await get_timescale_repository()
        
        # Update location in PostgreSQL
        await vehicle_repo.update_vehicle_location(
            vehicle_id, 
            location_update.latitude, 
            location_update.longitude
        )
        
        # Store tracking data in TimescaleDB
        tracking_data = {
            "vehicle_id": vehicle_id,
            "latitude": location_update.latitude,
            "longitude": location_update.longitude,
            "speed": location_update.speed,
            "heading": location_update.heading,
            "timestamp": location_update.timestamp or datetime.utcnow(),
            "is_moving": location_update.speed and location_update.speed > 0
        }
        
        await timescale_repo.insert_vehicle_tracking(tracking_data)
        
        # Emit vehicle location event
        background_tasks.add_task(
            emit_vehicle_location_update,
            {
                "vehicle_id": vehicle_id,
                "location": {
                    "latitude": location_update.latitude,
                    "longitude": location_update.longitude
                },
                "speed": location_update.speed,
                "heading": location_update.heading,
                "is_moving": tracking_data["is_moving"]
            }
        )
        
        return {"status": "location_updated"}
        
    except Exception as e:
        logger.error(f"Error updating vehicle location: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/vehicles/{vehicle_id}/tracking")
async def get_vehicle_tracking(vehicle_id: str, hours: int = 24):
    """Get vehicle tracking history"""
    try:
        timescale_repo = await get_timescale_repository()
        tracking_data = await timescale_repo.get_vehicle_tracking_history(vehicle_id, hours)
        
        return [dict(track) for track in tracking_data]
        
    except Exception as e:
        logger.error(f"Error getting vehicle tracking: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Route Optimization Endpoints
@app.post("/api/routes/optimize")
async def optimize_route(start_location: str, end_location: str):
    """Find optimal route between locations using Neo4j"""
    try:
        neo4j_repo = await get_neo4j_repository()
        route_result = await neo4j_repo.find_shortest_route(start_location, end_location)
        
        if not route_result:
            raise HTTPException(status_code=404, detail="Route not found")
        
        return {
            "total_distance": route_result["total_distance"],
            "route_found": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing route: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Event Management Endpoints
class EventSubscription(BaseModel):
    topics: List[str]
    webhook_url: Optional[str] = None


@app.get("/api/events/topics")
async def get_event_topics():
    """Get available event topics"""
    return {
        "topics": [
            "tms.loads",
            "tms.vehicles", 
            "tms.vehicles.tracking",
            "tms.drivers",
            "tms.routes",
            "tms.carriers",
            "tms.system.alerts",
            "tms.ai.predictions"
        ]
    }


@app.post("/api/events/publish")
async def publish_event(event_data: Dict, background_tasks: BackgroundTasks):
    """Manually publish an event (for testing)"""
    try:
        # Basic event structure validation
        if "event_type" not in event_data:
            raise HTTPException(status_code=400, detail="event_type is required")
        
        event_type = EventType(event_data["event_type"])
        
        # Create and send event
        from models.events import create_event
        event = create_event(
            event_type=event_type,
            data=event_data.get("data", {}),
            source=event_data.get("source", "manual"),
            correlation_id=event_data.get("correlation_id")
        )
        
        producer = await get_producer()
        success = await producer.send_event(event)
        
        # Broadcast to WebSocket clients
        if success:
            event_dict = {
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "source": event.source,
                "timestamp": event.timestamp.isoformat(),
                "data": event.data
            }
            background_tasks.add_task(broadcast_event_to_websockets, event_dict)
        
        return {"status": "published" if success else "failed", "event_id": event.event_id}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid event type: {e}")
    except Exception as e:
        logger.error(f"Error publishing event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket Endpoint for Real-time Events
@app.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time event streaming"""
    await manager.connect(websocket)
    logger.info(f"WebSocket client connected. Total connections: {len(manager.active_connections)}")
    
    try:
        while True:
            # Keep the connection alive and wait for disconnect
            data = await websocket.receive_text()
            # Echo back any received messages (optional)
            if data:
                await manager.send_personal_message(f"Echo: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"WebSocket client disconnected. Total connections: {len(manager.active_connections)}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# Function to broadcast events to WebSocket clients
async def broadcast_event_to_websockets(event_data: dict):
    """Broadcast event to all connected WebSocket clients"""
    if manager.active_connections:
        message = json.dumps({
            "type": "event",
            "data": event_data
        })
        await manager.broadcast(message)
        logger.info(f"Broadcasted event {event_data.get('event_type')} to {len(manager.active_connections)} WebSocket clients")


# Analytics Endpoints
@app.get("/api/analytics/dashboard")
async def get_dashboard_data(time_range: str = "24h"):
    """Get comprehensive dashboard analytics data"""
    try:
        load_repo = await get_load_repository()
        vehicle_repo = await get_vehicle_repository()
        timescale_repo = await get_timescale_repository()
        
        # Get load statistics
        total_loads = await load_repo.execute_query("SELECT COUNT(*) as count FROM loads")
        active_loads = await load_repo.execute_query("SELECT COUNT(*) as count FROM loads WHERE status IN ('assigned', 'picked_up', 'in_transit')")
        
        # Get loads by status
        loads_by_status = await load_repo.execute_query(
            "SELECT status, COUNT(*) as count FROM loads GROUP BY status"
        )
        loads_status_dict = {row['status']: row['count'] for row in loads_by_status}
        
        # Get vehicle statistics
        total_vehicles = await vehicle_repo.execute_query("SELECT COUNT(*) as count FROM vehicles")
        active_vehicles = await vehicle_repo.execute_query("SELECT COUNT(*) as count FROM vehicles WHERE status = 'in_transit'")
        
        # Get vehicles by status
        vehicles_by_status = await vehicle_repo.execute_query(
            "SELECT status, COUNT(*) as count FROM vehicles GROUP BY status"
        )
        vehicles_status_dict = {row['status']: row['count'] for row in vehicles_by_status}
        
        # Get recent events from TimescaleDB
        recent_events = await timescale_repo.execute_query(
            "SELECT event_type, 'load' as source, time as timestamp, metadata as data FROM load_events ORDER BY time DESC LIMIT 50"
        )
        
        # Get hourly load creation trend
        hourly_loads = await timescale_repo.execute_query(
            """SELECT 
                EXTRACT(hour FROM time) as hour,
                COUNT(*) as loads
            FROM load_events 
            WHERE event_type = 'picked_up' 
            AND time >= NOW() - INTERVAL '24 hours'
            GROUP BY EXTRACT(hour FROM time)
            ORDER BY hour"""
        )
        
        return {
            "total_loads": total_loads[0]['count'] if total_loads else 0,
            "active_loads": active_loads[0]['count'] if active_loads else 0,
            "total_vehicles": total_vehicles[0]['count'] if total_vehicles else 0,
            "active_vehicles": active_vehicles[0]['count'] if active_vehicles else 0,
            "loads_by_status": loads_status_dict,
            "vehicles_by_status": vehicles_status_dict,
            "recent_events": [
                {
                    "event_id": f"evt-{event['timestamp'].strftime('%Y%m%d%H%M%S')}",
                    "event_type": event['event_type'],
                    "source": event['source'],
                    "timestamp": event['timestamp'].isoformat(),
                    "data": event['data']
                } for event in recent_events
            ],
            "hourly_loads": [
                {"hour": int(row['hour']), "loads": row['loads']} 
                for row in hourly_loads
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard data")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
