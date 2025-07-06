"""Driver management endpoints for TMS API."""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
import logging

from dependencies import get_driver_repo, get_load_repo
from models.domain import Location, DriverStatus, CreateDriverRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.post("")
async def create_driver(
    driver_request: CreateDriverRequest,
    background_tasks: BackgroundTasks,
    driver_repo=Depends(get_driver_repo)
):
    """Create a new driver as per SPEC requirements."""
    try:
        # Prepare driver data for database insertion
        driver_data = {
            "carrier_id": driver_request.carrier_id,
            "driver_number": driver_request.driver_number,
            "first_name": driver_request.first_name,
            "last_name": driver_request.last_name,
            "email": driver_request.email,
            "phone": driver_request.phone,
            "license_number": driver_request.license_number,
            "license_class": driver_request.license_class,
            "license_expiry": driver_request.license_expiry.date(),
            "date_of_birth": driver_request.date_of_birth.date(),
            "hire_date": driver_request.hire_date.date(),
            "latitude": driver_request.current_location.latitude,
            "longitude": driver_request.current_location.longitude,
            "current_address": driver_request.current_address,
            "status": driver_request.status.value
        }
        
        # Create driver in database
        new_driver = await driver_repo.create_driver(driver_data)
        if not new_driver:
            raise HTTPException(status_code=500, detail="Failed to create driver")
        
        # TODO: Publish DRIVER_CREATED event to Kafka as per SPEC
        # background_tasks.add_task(publish_driver_event, "DRIVER_CREATED", new_driver)
        
        return new_driver
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating driver: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create driver: {str(e)}")


@router.get("")
async def get_drivers(
    status: Optional[str] = None,
    available_only: bool = False,
    limit: int = 50,
    offset: int = 0,
    driver_repo=Depends(get_driver_repo)
):
    """Get drivers with optional filtering for assignment workflows."""
    try:
        # Build query conditions
        conditions = []
        params = []
        
        # Handle status filtering - available_only takes precedence
        if available_only:
            conditions.append(f"status = ${len(params) + 1}")
            params.append("AVAILABLE")
        elif status:
            conditions.append(f"status = ${len(params) + 1}")
            params.append(status)
        
        # Get drivers using the proper driver repository
        drivers = await driver_repo.get_drivers(conditions, params, limit, offset)
        
        # Get total count
        total_count = await driver_repo.count_drivers(conditions, params)
        
        return {
            "drivers": drivers or [],
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total_count
        }
    except Exception as e:
        logger.error(f"Error retrieving drivers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve drivers: {str(e)}")


@router.get("/{driver_id}")
async def get_driver(
    driver_id: str,
    driver_repo=Depends(get_driver_repo),
    load_repo=Depends(get_load_repo)
):
    """Get detailed driver information."""
    try:
        # Get driver details using the proper driver repository
        driver = await driver_repo.get_driver_by_id(driver_id)
        
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        
        # Get current assignment (if any)
        assignment_query = """
            SELECT 
                l.id as load_id, l.load_number, l.status as load_status,
                l.pickup_address, l.delivery_address, l.pickup_date, l.delivery_date
            FROM loads l
            WHERE l.driver_id = $1 AND l.status IN ('ASSIGNED', 'PICKED_UP', 'IN_TRANSIT')
            ORDER BY l.pickup_date
            LIMIT 1
        """
        current_assignment = await load_repo.execute_single(assignment_query, driver_id)
        
        # Get recent loads (last 10)
        recent_loads_query = """
            SELECT 
                l.id as load_id, l.load_number, l.status,
                l.pickup_address, l.delivery_address, l.pickup_date, l.delivery_date
            FROM loads l
            WHERE l.driver_id = $1
            ORDER BY l.updated_at DESC
            LIMIT 10
        """
        recent_loads = await load_repo.execute_query(recent_loads_query, driver_id)
        
        # Get performance metrics
        performance_query = """
            SELECT 
                COUNT(*) as total_loads,
                COUNT(CASE WHEN status = 'DELIVERED' THEN 1 END) as completed_loads,
                AVG(CASE WHEN status = 'DELIVERED' THEN 
                    EXTRACT(EPOCH FROM (updated_at - created_at))/3600 
                END) as avg_completion_hours
            FROM loads 
            WHERE driver_id = $1 AND created_at >= NOW() - INTERVAL '30 days'
        """
        performance = await load_repo.execute_single(performance_query, driver_id)
        
        return {
            "driver": driver,
            "current_assignment": current_assignment,
            "recent_loads": recent_loads,
            "performance_30d": performance or {
                "total_loads": 0,
                "completed_loads": 0,
                "avg_completion_hours": None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving driver {driver_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve driver: {str(e)}")
