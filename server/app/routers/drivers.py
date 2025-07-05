"""Driver management endpoints for TMS API."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import logging

from dependencies import get_load_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.get("/")
async def get_drivers(
    status: Optional[str] = None,
    available_only: bool = False,
    limit: int = 50,
    offset: int = 0,
    load_repo=Depends(get_load_repo)
):
    """Get drivers with optional filtering for assignment workflows."""
    try:
        # Build query conditions
        conditions = []
        params = []
        
        if status:
            conditions.append("status = %s")
            params.append(status)
            
        if available_only:
            conditions.append("status = %s")
            params.append("AVAILABLE")
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        # Get drivers with pagination
        query = f"""
            SELECT 
                id, carrier_id, license_number, name, phone, email, 
                status, current_location, hours_remaining, created_at, updated_at
            FROM drivers 
            {where_clause}
            ORDER BY name
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        
        drivers = await load_repo.execute_query(query, params)
        
        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM drivers {where_clause}"
        count_params = params[:-2]  # Remove limit and offset
        count_result = await load_repo.execute_single(count_query, count_params)
        total_count = count_result['total'] if count_result else 0
        
        return {
            "drivers": drivers,
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
    load_repo=Depends(get_load_repo)
):
    """Get detailed driver information."""
    try:
        # Get driver details
        driver_query = """
            SELECT 
                id, carrier_id, license_number, name, phone, email, 
                status, current_location, hours_remaining, created_at, updated_at
            FROM drivers 
            WHERE id = %s
        """
        driver = await load_repo.execute_single(driver_query, [driver_id])
        
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        
        # Get current assignment (if any)
        assignment_query = """
            SELECT 
                l.id as load_id, l.load_number, l.status as load_status,
                l.pickup_address, l.delivery_address, l.pickup_datetime, l.delivery_datetime
            FROM loads l
            WHERE l.driver_id = %s AND l.status IN ('ASSIGNED', 'PICKED_UP', 'IN_TRANSIT')
            ORDER BY l.pickup_datetime
            LIMIT 1
        """
        current_assignment = await load_repo.execute_single(assignment_query, [driver_id])
        
        # Get recent loads (last 10)
        recent_loads_query = """
            SELECT 
                l.id as load_id, l.load_number, l.status,
                l.pickup_address, l.delivery_address, l.pickup_datetime, l.delivery_datetime
            FROM loads l
            WHERE l.driver_id = %s
            ORDER BY l.updated_at DESC
            LIMIT 10
        """
        recent_loads = await load_repo.execute_query(recent_loads_query, [driver_id])
        
        # Get performance metrics
        performance_query = """
            SELECT 
                COUNT(*) as total_loads,
                COUNT(CASE WHEN status = 'DELIVERED' THEN 1 END) as completed_loads,
                AVG(CASE WHEN status = 'DELIVERED' THEN 
                    EXTRACT(EPOCH FROM (updated_at - created_at))/3600 
                END) as avg_completion_hours
            FROM loads 
            WHERE driver_id = %s AND created_at >= NOW() - INTERVAL '30 days'
        """
        performance = await load_repo.execute_single(performance_query, [driver_id])
        
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
