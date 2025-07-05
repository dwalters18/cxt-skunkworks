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
    """Search loads with filters."""
    try:
        # Build search criteria
        criteria = {}
        if status:
            criteria['status'] = status
        if carrier_id:
            criteria['carrier_id'] = carrier_id
        
        # Get loads from repository
        loads = await load_repo.search_loads(criteria, limit=limit, offset=offset)
        
        # Get total count for pagination
        total_count = await load_repo.count_loads(criteria)
        
        return {
            "loads": loads,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total_count
        }
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
