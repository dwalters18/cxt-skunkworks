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
from services.route_optimization import route_optimizer
from database.connections import get_neo4j_repository, get_timescale_repository

# TMS Imports
from models.domain import (
    CreateLoadRequest, AssignLoadRequest, UpdateLocationRequest,
    LoadSearchRequest, VehicleTrackingData, Load, Vehicle, Driver
)
from models.events import EventType, BaseEvent
from database.connections import (
    get_db_manager, get_load_repository, get_vehicle_repository,
    get_audit_repository, DatabaseManager
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
        
        # Properly serialize loads with location data
        serialized_loads = []
        for load in loads:
            load_dict = dict(load)
            
            # Convert pickup location coordinates to Location object
            if 'pickup_latitude' in load_dict and 'pickup_longitude' in load_dict and load_dict['pickup_latitude'] is not None and load_dict['pickup_longitude'] is not None:
                load_dict['pickup_location'] = {
                    'latitude': float(load_dict['pickup_latitude']),
                    'longitude': float(load_dict['pickup_longitude'])
                }
                # Remove the raw extracted coordinates
                load_dict.pop('pickup_latitude', None)
                load_dict.pop('pickup_longitude', None)
            else:
                load_dict['pickup_location'] = None
            
            # Convert delivery location coordinates to Location object
            if 'delivery_latitude' in load_dict and 'delivery_longitude' in load_dict and load_dict['delivery_latitude'] is not None and load_dict['delivery_longitude'] is not None:
                load_dict['delivery_location'] = {
                    'latitude': float(load_dict['delivery_latitude']),
                    'longitude': float(load_dict['delivery_longitude'])
                }
                # Remove the raw extracted coordinates
                load_dict.pop('delivery_latitude', None)
                load_dict.pop('delivery_longitude', None)
            else:
                load_dict['delivery_location'] = None
            
            serialized_loads.append(load_dict)
        
        return serialized_loads
        
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
                "old_status": "PENDING",
                "new_status": "ASSIGNED"
            },
            EventType.LOAD_ASSIGNED
        )
        
        return {"status": "ASSIGNED"}
        
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


# Driver Management Endpoints
@app.get("/api/drivers")
async def get_drivers(
    status: Optional[str] = None,
    available_only: bool = False,
    limit: int = 50,
    offset: int = 0
):
    """Get drivers with optional filtering for assignment workflows"""
    try:
        load_repository = await get_load_repository()
        
        # Build query with optional filters
        where_conditions = []
        params = []
        param_count = 0
        
        if status:
            param_count += 1
            where_conditions.append(f"d.status = ${param_count}")
            params.append(status)
            
        if available_only:
            param_count += 1
            where_conditions.append(f"d.status = ${param_count}")
            params.append('AVAILABLE')
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        query = f"""
        SELECT d.id, d.first_name, d.last_name, d.license_number,
               d.phone, d.email, d.status, d.hours_driven_today,
               d.hours_remaining_today, d.current_latitude, d.current_longitude,
               d.last_location_update, d.carrier_id,
               c.name as carrier_name,
               COUNT(l.id) as active_loads
        FROM drivers d
        LEFT JOIN carriers c ON d.carrier_id = c.id
        LEFT JOIN loads l ON l.assigned_driver_id = d.id AND l.status IN ('ASSIGNED', 'IN_TRANSIT')
        WHERE {where_clause}
        GROUP BY d.id, c.name
        ORDER BY d.last_name, d.first_name
        LIMIT ${param_count + 1} OFFSET ${param_count + 2}
        """
        
        params.extend([limit, offset])
        results = await load_repository.execute_query(query, *params)
        
        drivers = []
        for row in results:
            drivers.append({
                "driver_id": str(row['id']),
                "name": f"{row['first_name']} {row['last_name']}",
                "first_name": row['first_name'],
                "last_name": row['last_name'],
                "license_number": row['license_number'],
                "phone": row['phone'],
                "email": row['email'],
                "status": row['status'],
                "carrier_id": str(row['carrier_id']) if row['carrier_id'] else None,
                "carrier_name": row['carrier_name'],
                "hours_driven_today": float(row['hours_driven_today'] or 0),
                "hours_remaining_today": float(row['hours_remaining_today'] or 0),
                "current_location": {
                    "latitude": float(row['current_latitude']) if row['current_latitude'] else None,
                    "longitude": float(row['current_longitude']) if row['current_longitude'] else None
                },
                "last_location_update": row['last_location_update'].isoformat() if row['last_location_update'] else None,
                "active_loads": row['active_loads']
            })
        
        return {
            "drivers": drivers,
            "total": len(drivers),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error fetching drivers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/drivers/{driver_id}")
async def get_driver(driver_id: str):
    """Get detailed driver information"""
    try:
        load_repository = await get_load_repository()
        
        query = """
        SELECT d.*, c.name as carrier_name,
               COUNT(l.id) as total_loads,
               COUNT(CASE WHEN l.status = 'DELIVERED' THEN 1 END) as completed_loads,
               AVG(CASE WHEN l.status = 'DELIVERED' THEN 
                   EXTRACT(EPOCH FROM (l.delivered_at - l.picked_up_at))/3600 
               END) as avg_delivery_hours
        FROM drivers d
        LEFT JOIN carriers c ON d.carrier_id = c.id
        LEFT JOIN loads l ON l.assigned_driver_id = d.id
        WHERE d.id = $1
        GROUP BY d.id, c.name
        """
        
        result = await load_repository.execute_single(query, driver_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Driver not found")
        
        return {
            "driver_id": str(result['id']),
            "name": f"{result['first_name']} {result['last_name']}",
            "first_name": result['first_name'],
            "last_name": result['last_name'],
            "license_number": result['license_number'],
            "phone": result['phone'],
            "email": result['email'],
            "status": result['status'],
            "carrier_id": str(result['carrier_id']) if result['carrier_id'] else None,
            "carrier_name": result['carrier_name'],
            "hours_driven_today": float(result['hours_driven_today'] or 0),
            "hours_remaining_today": float(result['hours_remaining_today'] or 0),
            "current_location": {
                "latitude": float(result['current_latitude']) if result['current_latitude'] else None,
                "longitude": float(result['current_longitude']) if result['current_longitude'] else None
            },
            "last_location_update": result['last_location_update'].isoformat() if result['last_location_update'] else None,
            "performance": {
                "total_loads": result['total_loads'],
                "completed_loads": result['completed_loads'],
                "completion_rate": float(result['completed_loads'] / result['total_loads']) if result['total_loads'] > 0 else 0,
                "avg_delivery_hours": float(result['avg_delivery_hours'] or 0)
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching driver details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced Load Management Endpoints
@app.get("/api/loads/unassigned")
async def get_unassigned_loads(limit: int = 50, offset: int = 0):
    """Get unassigned loads for dispatcher assignment workflows"""
    return await search_loads(status="PENDING", limit=limit, offset=offset)

@app.get("/api/loads/by-status/{status}")
async def get_loads_by_status(status: str, limit: int = 50, offset: int = 0):
    """Get loads filtered by specific status"""
    valid_statuses = ['PENDING', 'ASSIGNED', 'PICKED_UP', 'IN_TRANSIT', 'DELIVERED', 'CANCELLED']
    if status.upper() not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
    
    return await search_loads(status=status.upper(), limit=limit, offset=offset)

# Vehicle Management Endpoints
@app.get("/api/vehicles")
async def get_vehicles(carrier_id: Optional[str] = None, status: Optional[str] = None):
    """Get vehicles with optional filters"""
    try:
        vehicle_repo = await get_vehicle_repository()
        
        if status and status.upper() == "AVAILABLE":
            vehicles = await vehicle_repo.get_available_vehicles(carrier_id)
        else:
            # For now, just get available vehicles as example
            vehicles = await vehicle_repo.get_available_vehicles(carrier_id)
        
        # Properly serialize vehicles with location data
        serialized_vehicles = []
        for vehicle in vehicles:
            vehicle_dict = dict(vehicle)
            
            # Convert PostGIS geometry to Location object if coordinates are available
            if 'latitude' in vehicle_dict and 'longitude' in vehicle_dict and vehicle_dict['latitude'] is not None and vehicle_dict['longitude'] is not None:
                vehicle_dict['current_location'] = {
                    'latitude': float(vehicle_dict['latitude']),
                    'longitude': float(vehicle_dict['longitude'])
                }
                # Remove the raw extracted coordinates
                vehicle_dict.pop('latitude', None)
                vehicle_dict.pop('longitude', None)
            else:
                # Set current_location to None if no coordinates available
                vehicle_dict['current_location'] = None
            
            serialized_vehicles.append(vehicle_dict)
        
        return serialized_vehicles
        
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


# Route Management Endpoints
@app.get("/api/routes")
async def get_routes(
    status: Optional[str] = None,
    active_only: bool = False,
    limit: int = 50,
    offset: int = 0
):
    """Get routes with optional filtering for map display and management"""
    try:
        load_repository = await get_load_repository()
        
        # Build query with optional filters
        where_conditions = []
        params = []
        param_count = 0
        
        if status:
            param_count += 1
            where_conditions.append(f"r.status = ${param_count}")
            params.append(status)
            
        if active_only:
            param_count += 1
            where_conditions.append(f"r.status = ${param_count}")
            params.append('ACTIVE')
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        query = f"""
        SELECT r.id, r.load_id, r.driver_id, r.vehicle_id, r.status,
               r.planned_distance_miles, r.planned_duration_minutes, 
               r.optimization_score, r.fuel_estimate, r.toll_estimate,
               r.estimated_arrival, r.created_at,
               l.load_number, l.pickup_address, l.delivery_address,
               CONCAT(d.first_name, ' ', d.last_name) as driver_name,
               CONCAT(v.make, ' ', v.model) as vehicle_info,
               ST_AsGeoJSON(r.route_geometry) as route_geojson,
               ST_AsGeoJSON(r.origin_location) as origin_geojson,
               ST_AsGeoJSON(r.destination_location) as destination_geojson
        FROM routes r
        JOIN loads l ON r.load_id = l.id
        LEFT JOIN drivers d ON r.driver_id = d.id
        LEFT JOIN vehicles v ON r.vehicle_id = v.id
        WHERE {where_clause}
        ORDER BY r.created_at DESC
        LIMIT ${param_count + 1} OFFSET ${param_count + 2}
        """
        
        params.extend([limit, offset])
        results = await load_repository.execute_query(query, *params)
        
        routes = []
        for row in results:
            # Parse geometry data for frontend
            route_coords = []
            origin_coords = None
            dest_coords = None
            
            if row['route_geojson']:
                import json
                geojson = json.loads(row['route_geojson'])
                route_coords = geojson.get('coordinates', [])
                
            if row['origin_geojson']:
                import json
                origin_geojson = json.loads(row['origin_geojson'])
                origin_coords = origin_geojson.get('coordinates')
                
            if row['destination_geojson']:
                import json
                dest_geojson = json.loads(row['destination_geojson'])
                dest_coords = dest_geojson.get('coordinates')
            
            routes.append({
                "route_id": str(row['id']),
                "load_id": str(row['load_id']),
                "load_number": row['load_number'],
                "driver_id": str(row['driver_id']) if row['driver_id'] else None,
                "driver_name": row['driver_name'],
                "vehicle_id": str(row['vehicle_id']) if row['vehicle_id'] else None,
                "vehicle_info": row['vehicle_info'],
                "status": row['status'],
                "pickup_address": row['pickup_address'],
                "delivery_address": row['delivery_address'],
                "distance_miles": float(row['planned_distance_miles'] or 0),
                "duration_minutes": row['planned_duration_minutes'],
                "optimization_score": float(row['optimization_score'] or 0),
                "fuel_estimate": float(row['fuel_estimate'] or 0),
                "toll_estimate": float(row['toll_estimate'] or 0),
                "estimated_arrival": row['estimated_arrival'].isoformat() if row['estimated_arrival'] else None,
                "route_coordinates": route_coords,
                "origin_coordinates": origin_coords,
                "destination_coordinates": dest_coords,
                "created_at": row['created_at'].isoformat() if row['created_at'] else None
            })
        
        return {
            "routes": routes,
            "total": len(routes),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error fetching routes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/routes/active")
async def get_active_routes():
    """Get all active routes with geometry for real-time map display"""
    return await get_routes(status="ACTIVE", active_only=True)

@app.get("/api/routes/performance")
async def get_route_performance(time_range: str = "24h"):
    """Get route performance metrics and analytics"""
    try:
        load_repository = await get_load_repository()
        
        # Calculate time filter based on range
        time_filter = {
            "1h": "1 HOUR",
            "24h": "1 DAY", 
            "7d": "7 DAYS",
            "30d": "30 DAYS"
        }.get(time_range, "1 DAY")
        
        query = f"""
        SELECT 
            COUNT(*) as total_routes,
            COUNT(CASE WHEN r.status = 'ACTIVE' THEN 1 END) as active_routes,
            COUNT(CASE WHEN r.status = 'COMPLETED' THEN 1 END) as completed_routes,
            COUNT(CASE WHEN r.status = 'DELAYED' THEN 1 END) as delayed_routes,
            AVG(r.optimization_score) as avg_optimization_score,
            AVG(r.planned_distance_miles) as avg_distance_miles,
            AVG(r.planned_duration_minutes) as avg_duration_minutes,
            AVG(r.fuel_estimate) as avg_fuel_estimate,
            SUM(r.fuel_estimate) as total_fuel_estimate,
            SUM(r.toll_estimate) as total_toll_estimate,
            COUNT(CASE WHEN r.optimization_score >= 0.8 THEN 1 END) as high_efficiency_routes,
            COUNT(CASE WHEN r.optimization_score < 0.6 THEN 1 END) as low_efficiency_routes
        FROM routes r
        WHERE r.created_at >= NOW() - INTERVAL '{time_filter}'
        """
        
        result = await load_repository.execute_single(query)
        
        if not result:
            return {
                "performance_metrics": {
                    "total_routes": 0,
                    "active_routes": 0,
                    "completed_routes": 0,
                    "delayed_routes": 0,
                    "completion_rate": 0,
                    "avg_optimization_score": 0,
                    "avg_distance_miles": 0,
                    "avg_duration_minutes": 0,
                    "avg_fuel_estimate": 0,
                    "total_fuel_estimate": 0,
                    "total_toll_estimate": 0,
                    "efficiency_distribution": {
                        "high_efficiency": 0,
                        "medium_efficiency": 0,
                        "low_efficiency": 0
                    }
                },
                "time_range": time_range
            }
        
        total_routes = result['total_routes'] or 0
        completed_routes = result['completed_routes'] or 0
        high_efficiency = result['high_efficiency_routes'] or 0
        low_efficiency = result['low_efficiency_routes'] or 0
        medium_efficiency = total_routes - high_efficiency - low_efficiency
        
        return {
            "performance_metrics": {
                "total_routes": total_routes,
                "active_routes": result['active_routes'] or 0,
                "completed_routes": completed_routes,
                "delayed_routes": result['delayed_routes'] or 0,
                "completion_rate": float(completed_routes / total_routes) if total_routes > 0 else 0,
                "avg_optimization_score": float(result['avg_optimization_score'] or 0),
                "avg_distance_miles": float(result['avg_distance_miles'] or 0),
                "avg_duration_minutes": float(result['avg_duration_minutes'] or 0),
                "avg_fuel_estimate": float(result['avg_fuel_estimate'] or 0),
                "total_fuel_estimate": float(result['total_fuel_estimate'] or 0),
                "total_toll_estimate": float(result['total_toll_estimate'] or 0),
                "efficiency_distribution": {
                    "high_efficiency": high_efficiency,
                    "medium_efficiency": medium_efficiency,
                    "low_efficiency": low_efficiency
                }
            },
            "time_range": time_range
        }
        
    except Exception as e:
        logger.error(f"Error fetching route performance: {e}")
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


class OptimizeLoadRouteRequest(BaseModel):
    load_id: str
    driver_id: Optional[str] = None
    vehicle_id: str
    priority: Optional[str] = "normal"  # normal, urgent, eco

@app.post("/api/routes/optimize-load")
async def optimize_load_route(request: OptimizeLoadRouteRequest, background_tasks: BackgroundTasks):
    """
    Calculate optimized street-level route for load assignment using Google Maps API
    """
    try:
        from uuid import UUID
        
        result = await route_optimizer.optimize_route(
            load_id=UUID(request.load_id),
            driver_id=UUID(request.driver_id) if request.driver_id else None,
            vehicle_id=UUID(request.vehicle_id)
        )
        
        return {
            "success": True,
            "message": "Route optimization completed",
            **result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Route optimization failed: {str(e)}")

@app.get("/api/routes/{route_id}")
async def get_route_details(route_id: str):
    """Get detailed route information including turn-by-turn directions"""
    try:
        load_repository = await get_load_repository()
        
        query = """
        SELECT r.*, l.load_number, 
               CONCAT(d.first_name, ' ', d.last_name) as driver_name, 
               v.make, v.model
        FROM routes r
        JOIN loads l ON r.load_id = l.id
        LEFT JOIN drivers d ON r.driver_id = d.id
        JOIN vehicles v ON r.vehicle_id = v.id
        WHERE r.id = $1
        """
        
        result = await load_repository.execute_single(query, route_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Route not found")
        
        # Convert route geometry to coordinates for frontend
        route_coords = []
        if result['route_geometry']:
            # Extract coordinates from PostGIS LINESTRING
            coords_query = """
            SELECT ST_AsGeoJSON(route_geometry) as geojson
            FROM routes WHERE id = $1
            """
            geojson_result = await load_repository.execute_single(coords_query, route_id)
            
            if geojson_result and geojson_result['geojson']:
                import json
                geojson = json.loads(geojson_result['geojson'])
                route_coords = geojson.get('coordinates', [])
        
        return {
            "route_id": str(result['id']),
            "load_id": str(result['load_id']),
            "load_number": result['load_number'],
            "driver_name": result['driver_name'],
            "vehicle": f"{result['make']} {result['model']}",
            "distance_miles": float(result['planned_distance_miles'] or 0),
            "duration_minutes": result['planned_duration_minutes'],
            "optimization_score": float(result['optimization_score'] or 0),
            "status": result['status'],
            "route_coordinates": route_coords,  # For map display
            "fuel_estimate": float(result['fuel_estimate'] or 0),
            "toll_estimate": float(result['toll_estimate'] or 0)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get route details: {str(e)}")


# Event Management Endpoints
class EventSubscription(BaseModel):
    topics: List[str]
    webhook_url: Optional[str] = None


@app.get("/api/events/recent")
async def get_recent_events(limit: int = 10):
    """Get recent events from TimescaleDB"""
    try:
        timescale_repo = await get_timescale_repository()
        
        # Query recent load events from TimescaleDB
        query = """
        SELECT 
            time,
            load_id,
            event_type,
            status,
            ST_Y(location::geometry) as location_lat,
            ST_X(location::geometry) as location_lng,
            driver_id,
            vehicle_id,
            details
        FROM load_events 
        ORDER BY time DESC 
        LIMIT $1
        """
        
        events = await timescale_repo.execute_query(query, limit)
        
        # Format events for UI consumption
        formatted_events = []
        for event in events:
            formatted_event = {
                "id": f"load_event_{event['load_id']}_{int(event['time'].timestamp())}",
                "timestamp": event['time'].isoformat(),
                "type": event['event_type'],
                "title": event['status'] or f"Load {event['event_type']}",
                "description": event['status'] or f"Load {event['load_id']} status: {event['event_type']}",
                "entity_type": "load",
                "entity_id": str(event['load_id']),
                "location": {
                    "lat": event['location_lat'],
                    "lng": event['location_lng']
                } if event['location_lat'] and event['location_lng'] else None,
                "metadata": event['details'] or {},
                "driver_id": str(event['driver_id']) if event['driver_id'] else None,
                "vehicle_id": str(event['vehicle_id']) if event['vehicle_id'] else None
            }
            formatted_events.append(formatted_event)
        
        return {
            "events": formatted_events,
            "total": len(formatted_events),
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error fetching recent events: {e}")
        # Return empty events list instead of error to prevent UI crashes
        return {
            "events": [],
            "total": 0,
            "limit": limit,
            "error": "Unable to fetch events at this time"
        }


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
        active_loads = await load_repo.execute_query("SELECT COUNT(*) as count FROM loads WHERE status IN ('ASSIGNED', 'PICKED_UP', 'IN_TRANSIT')")
        
        # Get loads by status
        loads_by_status = await load_repo.execute_query(
            "SELECT status, COUNT(*) as count FROM loads GROUP BY status"
        )
        loads_status_dict = {row['status']: row['count'] for row in loads_by_status}
        
        # Get vehicle statistics
        total_vehicles = await vehicle_repo.execute_query("SELECT COUNT(*) as count FROM vehicles")
        active_vehicles = await vehicle_repo.execute_query("SELECT COUNT(*) as count FROM vehicles WHERE status = 'IN_TRANSIT'")
        
        # Get vehicles by status
        vehicles_by_status = await vehicle_repo.execute_query(
            "SELECT status, COUNT(*) as count FROM vehicles GROUP BY status"
        )
        vehicles_status_dict = {row['status']: row['count'] for row in vehicles_by_status}
        
        # Get recent events from TimescaleDB
        recent_events = await timescale_repo.execute_query(
            "SELECT event_type, 'load' as source, time as timestamp, details as data FROM load_events ORDER BY time DESC LIMIT 50"
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
