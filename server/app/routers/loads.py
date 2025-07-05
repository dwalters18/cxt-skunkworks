"""Load management endpoints for TMS API."""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Dict, Optional
import logging

from models.domain import CreateLoadRequest, AssignLoadRequest
from dependencies import get_load_repo, get_kafka_producer
from kafka.producer import emit_load_created, emit_load_status_change
from websocket_manager import broadcast_event_to_websockets

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/loads", tags=["loads"])


@router.post("/", status_code=201)
async def create_load(
    load_request: CreateLoadRequest, 
    background_tasks: BackgroundTasks,
    load_repo=Depends(get_load_repo),
    producer=Depends(get_kafka_producer)
):
    """Create a new load and emit event."""
    try:
        # Create the load
        load = await load_repo.create_load(load_request)
        
        # Emit load created event
        background_tasks.add_task(emit_load_created, load.id, {
            "load_id": load.id,
            "load_number": load.load_number,
            "pickup_address": load.pickup_address,
            "delivery_address": load.delivery_address,
            "status": load.status
        })
        
        return load
    except Exception as e:
        logger.error(f"Error creating load: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create load: {str(e)}")


@router.get("/")
async def search_loads(
    status: Optional[str] = None,
    carrier_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    load_repo=Depends(get_load_repo)
):
    """Get loads with basic filtering (kept for backward compatibility)."""
    # Implementation remains the same for backward compatibility
    return await _search_loads_internal(status, carrier_id, limit, offset, load_repo)


@router.get("/search")
async def search_loads_advanced(
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    date_range: Optional[str] = None,
    location_radius: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    load_repo=Depends(get_load_repo)
):
    """Search and filter loads with complex criteria as per SPEC."""
    try:
        # Build query conditions
        conditions = []
        params = []
        
        if status:
            conditions.append("status = %s")
            params.append(status)
            
        if customer_id:
            conditions.append("customer_id = %s")
            params.append(customer_id)
        
        if date_range:
            # Parse date range (format: "2025-01-01,2025-01-31")
            try:
                start_date, end_date = date_range.split(',')
                conditions.append("pickup_date >= %s AND pickup_date <= %s")
                params.extend([start_date.strip(), end_date.strip()])
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_range format. Use: YYYY-MM-DD,YYYY-MM-DD")
        
        if location_radius:
            # Parse location radius (format: "lat,lng,radius_km")
            try:
                lat, lng, radius = location_radius.split(',')
                lat, lng, radius = float(lat), float(lng), float(radius)
                # Use PostGIS spatial query for location-based search
                conditions.append(
                    "ST_DWithin(pickup_location::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s)"
                )
                params.extend([lng, lat, radius * 1000])  # Convert km to meters
            except (ValueError, IndexError):
                raise HTTPException(status_code=400, detail="Invalid location_radius format. Use: lat,lng,radius_km")
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        # Get loads with pagination
        query = f"""
            SELECT 
                id, load_number, customer_id, carrier_id, pickup_address, delivery_address,
                pickup_date, delivery_date, status, rate, distance, weight, commodity,
                pickup_location, delivery_location, created_at, updated_at
            FROM loads 
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        
        loads = await load_repo.execute_query(query, params)
        
        # Get total count for pagination
        count_query = f"SELECT COUNT(*) as total FROM loads {where_clause}"
        count_params = params[:-2]  # Remove limit and offset from params
        count_result = await load_repo.execute_single(count_query, count_params)
        total_count = count_result['total'] if count_result else 0
        
        return {
            "loads": loads or [],
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "filters_applied": {
                "status": status,
                "customer_id": customer_id,
                "date_range": date_range,
                "location_radius": location_radius
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching loads: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search loads: {str(e)}")


@router.get("/unassigned")
async def get_unassigned_loads(
    limit: int = 50, 
    offset: int = 0,
    load_repo=Depends(get_load_repo)
):
    """Get unassigned loads for dispatcher assignment workflows."""
    return await search_loads(status="CREATED", limit=limit, offset=offset, load_repo=load_repo)


@router.get("/status/{status}")
async def get_loads_by_status(
    status: str, 
    limit: int = 50, 
    offset: int = 0,
    load_repo=Depends(get_load_repo)
):
    """Get loads filtered by specific status."""
    return await search_loads(status=status, limit=limit, offset=offset, load_repo=load_repo)


@router.get("/{load_id}")
async def get_load(
    load_id: str,
    load_repo=Depends(get_load_repo)
):
    """Get load details."""
    try:
        load = await load_repo.get_load(load_id)
        if not load:
            raise HTTPException(status_code=404, detail="Load not found")
        return load
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving load {load_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve load: {str(e)}")


@router.put("/{load_id}/assign")
async def assign_load(
    load_id: str, 
    assignment: AssignLoadRequest, 
    background_tasks: BackgroundTasks,
    load_repo=Depends(get_load_repo),
    producer=Depends(get_kafka_producer)
):
    """Assign load to carrier/vehicle/driver."""
    try:
        # Update load assignment
        updated_load = await load_repo.assign_load(load_id, assignment)
        if not updated_load:
            raise HTTPException(status_code=404, detail="Load not found")
        
        # Emit load assignment event
        background_tasks.add_task(emit_load_status_change, load_id, "ASSIGNED", {
            "load_id": load_id,
            "carrier_id": assignment.carrier_id,
            "vehicle_id": assignment.vehicle_id,
            "driver_id": assignment.driver_id,
            "status": "ASSIGNED"
        })
        
        return updated_load
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning load {load_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to assign load: {str(e)}")


@router.put("/{load_id}/status")
async def update_load_status(
    load_id: str, 
    status_update: Dict[str, str], 
    background_tasks: BackgroundTasks,
    load_repo=Depends(get_load_repo),
    producer=Depends(get_kafka_producer)
):
    """Update load status."""
    try:
        new_status = status_update.get("status")
        if not new_status:
            raise HTTPException(status_code=400, detail="Status is required")
        
        # Update load status
        updated_load = await load_repo.update_load_status(load_id, new_status)
        if not updated_load:
            raise HTTPException(status_code=404, detail="Load not found")
        
        # Emit status change event
        background_tasks.add_task(emit_load_status_change, load_id, new_status, {
            "load_id": load_id,
            "status": new_status,
            "previous_status": status_update.get("previous_status"),
            "timestamp": status_update.get("timestamp")
        })
        
        # Broadcast to WebSocket clients
        background_tasks.add_task(broadcast_event_to_websockets, {
            "event_type": "LOAD_STATUS_UPDATED",
            "data": {
                "load_id": load_id,
                "status": new_status
            }
        })
        
        return updated_load
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating load status {load_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update load status: {str(e)}")


async def _search_loads_internal(
    status: Optional[str] = None,
    carrier_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    load_repo=None
):
    """Internal function for basic load search (backward compatibility)."""
    try:
        # Build query conditions
        conditions = []
        params = []
        
        if status:
            conditions.append("status = %s")
            params.append(status)
            
        if carrier_id:
            conditions.append("carrier_id = %s")
            params.append(carrier_id)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        # Get loads with pagination
        query = f"""
            SELECT 
                id, load_number, customer_id, carrier_id, pickup_address, delivery_address,
                pickup_date, delivery_date, status, rate, distance, weight, commodity,
                created_at, updated_at
            FROM loads 
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        
        loads = await load_repo.execute_query(query, params)
        
        return {
            "loads": loads or [],
            "total": len(loads) if loads else 0,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error searching loads: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search loads: {str(e)}")
