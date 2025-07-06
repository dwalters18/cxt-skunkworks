"""Vehicle management endpoints for TMS API."""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Optional
import logging

from models.domain import UpdateLocationRequest
from dependencies import get_vehicle_repo, get_timescale_repo, get_kafka_producer
from kafka.producer import emit_vehicle_location_update
from websocket_manager import broadcast_event_to_websockets

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("/")
async def get_vehicles(
    carrier_id: Optional[str] = None, 
    status: Optional[str] = None,
    vehicle_repo=Depends(get_vehicle_repo)
):
    """Get vehicles with optional filters."""
    try:
        # Build query conditions
        conditions = []
        params = []
        param_count = 0
        
        if carrier_id:
            param_count += 1
            conditions.append(f"carrier_id = ${param_count}")
            params.append(carrier_id)
            
        if status:
            param_count += 1
            conditions.append(f"status = ${param_count}")
            params.append(status)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        query = f"""
            SELECT 
                id, carrier_id, vehicle_number, vehicle_type, 
                capacity_weight, capacity_volume, status, current_location,
                fuel_level, odometer, created_at, updated_at
            FROM vehicles 
            {where_clause}
            ORDER BY vehicle_number
        """
        
        vehicles = await vehicle_repo.execute_query(query, params)
        return {"vehicles": vehicles}
    except Exception as e:
        logger.error(f"Error retrieving vehicles: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve vehicles: {str(e)}")


@router.put("/{vehicle_id}/location")
async def update_vehicle_location(
    vehicle_id: str, 
    location_update: UpdateLocationRequest, 
    background_tasks: BackgroundTasks,
    vehicle_repo=Depends(get_vehicle_repo),
    timescale_repo=Depends(get_timescale_repo),
    producer=Depends(get_kafka_producer)
):
    """Update vehicle location and emit tracking event."""
    try:
        # Update vehicle location in PostgreSQL
        update_query = """
            UPDATE vehicles 
            SET current_location = ST_GeogFromText($1), updated_at = NOW()
            WHERE id = $2
            RETURNING id, vehicle_number, status
        """
        point_wkt = f"POINT({location_update.longitude} {location_update.latitude})"
        vehicle = await vehicle_repo.execute_single(update_query, point_wkt, vehicle_id)
        
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        # Store tracking data in TimescaleDB
        tracking_insert = """
            INSERT INTO vehicle_tracking 
            (vehicle_id, latitude, longitude, speed, heading, fuel_level, timestamp, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
        """
        tracking_params = [
            vehicle_id,
            location_update.latitude,
            location_update.longitude,
            location_update.speed,
            location_update.heading,
            None,  # fuel_level - would come from vehicle telematics
            location_update.timestamp or 'NOW()'
        ]
        await timescale_repo.execute_command(tracking_insert, *tracking_params)
        
        # Emit location update event
        event_data = {
            "vehicle_id": vehicle_id,
            "latitude": location_update.latitude,
            "longitude": location_update.longitude,
            "speed": location_update.speed,
            "heading": location_update.heading,
            "timestamp": str(location_update.timestamp)
        }
        
        background_tasks.add_task(emit_vehicle_location_update, vehicle_id, event_data)
        
        # Broadcast to WebSocket clients for real-time tracking
        background_tasks.add_task(broadcast_event_to_websockets, {
            "event_type": "VEHICLE_LOCATION_UPDATED",
            "data": event_data
        })
        
        return {
            "message": "Vehicle location updated successfully",
            "vehicle_id": vehicle_id,
            "location": {
                "latitude": location_update.latitude,
                "longitude": location_update.longitude
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating vehicle location {vehicle_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update vehicle location: {str(e)}")


@router.get("/{vehicle_id}/tracking")
async def get_vehicle_tracking(
    vehicle_id: str, 
    hours: int = 24,
    timescale_repo=Depends(get_timescale_repo)
):
    """Get vehicle tracking history."""
    try:
        query = """
            SELECT 
                vehicle_id, latitude, longitude, speed, heading, 
                fuel_level, timestamp, created_at
            FROM vehicle_tracking 
            WHERE vehicle_id = $1 
                AND timestamp >= NOW() - INTERVAL '$2 hours'
            ORDER BY timestamp DESC
            LIMIT 1000
        """
        
        tracking_data = await timescale_repo.execute_query(query, [vehicle_id, hours])
        
        return {
            "vehicle_id": vehicle_id,
            "tracking_data": tracking_data,
            "hours": hours,
            "data_points": len(tracking_data)
        }
    except Exception as e:
        logger.error(f"Error retrieving vehicle tracking {vehicle_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve vehicle tracking: {str(e)}")
