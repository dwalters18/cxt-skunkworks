# server/app/main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List, Optional

# TMS Imports
from models.domain import (
    CreateLoadRequest, AssignLoadRequest, UpdateLocationRequest,
    LoadSearchRequest, VehicleTrackingData, Load, Vehicle, Driver
)
from models.events import EventType, BaseEvent
from database.connections import (
    get_db_manager, get_load_repository, get_vehicle_repository,
    get_timescale_repository, get_neo4j_repository, DatabaseManager
)
from kafka.producer import get_producer, emit_load_created, emit_vehicle_location_update, emit_load_status_change
from kafka.consumer import get_consumer, TMSEventConsumer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
consumer_task: Optional[asyncio.Task] = None


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
        
        return {"status": "published" if success else "failed", "event_id": event.event_id}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid event type: {e}")
    except Exception as e:
        logger.error(f"Error publishing event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Analytics Endpoints
@app.get("/api/analytics/dashboard")
async def get_dashboard_data():
    """Get dashboard analytics data"""
    try:
        load_repo = await get_load_repository()
        
        # Get basic stats
        total_loads = await load_repo.execute_query("SELECT COUNT(*) as count FROM loads")
        active_loads = await load_repo.execute_query("SELECT COUNT(*) as count FROM loads WHERE status IN ('assigned', 'picked_up', 'in_transit')")
        
        return {
            "total_loads": total_loads[0]['count'] if total_loads else 0,
            "active_loads": active_loads[0]['count'] if active_loads else 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
