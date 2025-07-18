"""Route management and optimization endpoints for TMS API."""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Optional
import logging

from services.route_optimization import route_optimizer
from services.advanced_route_optimization import get_advanced_route_optimizer, OptimizationConstraints
from dependencies import get_neo4j_repo, get_load_repo
from websocket_manager import broadcast_event_to_websockets
from models.domain import AdvancedOptimizeLoadRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/routes", tags=["routes"])


class OptimizeLoadRouteRequest(BaseModel):
    """Request model for load route optimization."""
    load_id: str
    driver_id: Optional[str] = None
    vehicle_id: str
    priority: Optional[str] = "normal"


@router.get("")
async def get_routes(
    status: Optional[str] = None,
    active_only: bool = False,
    limit: int = 50,
    offset: int = 0,
    load_repo=Depends(get_load_repo)
):
    """Get routes with optional filtering for map display and management."""
    try:
        # Build query conditions
        conditions = []
        params = []
        param_count = 0
        
        if status:
            param_count += 1
            conditions.append(f"r.status = ${param_count}")
            params.append(status)
            
        if active_only:
            conditions.append("r.status IN ('PLANNED', 'ACTIVE')")
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        # Get routes with load information
        param_count += 1
        limit_param = param_count
        param_count += 1
        offset_param = param_count
        query = f"""
            SELECT
                r.id, r.load_id, r.driver_id, r.vehicle_id,
                r.origin_location, r.destination_location, r.waypoints,
                r.route_geometry, r.planned_distance_miles, r.planned_duration_minutes,
                r.actual_distance_miles, r.actual_duration_minutes, r.estimated_arrival,
                r.actual_arrival, r.optimization_score, r.fuel_estimate, r.toll_estimate,
                r.status, r.created_at, r.updated_at,
                l.load_number, l.pickup_address, l.delivery_address, l.pickup_date, l.delivery_date,
                l.assigned_vehicle_id, l.assigned_driver_id
            FROM routes r
            JOIN loads l ON r.load_id = l.id
            {where_clause}
            ORDER BY r.created_at DESC
            LIMIT ${limit_param} OFFSET ${offset_param}
        """
        params.extend([limit, offset])
        
        routes = await load_repo.execute_query(query, *params)
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*) as total 
            FROM routes r
            JOIN loads l ON r.load_id = l.id
            {where_clause}
        """
        count_params = params[:-2]  # Remove limit and offset
        count_result = await load_repo.execute_single(count_query, *count_params)
        total_count = count_result['total'] if count_result else 0
        
        return {
            "routes": routes,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total_count
        }
    except Exception as e:
        logger.error(f"Error retrieving routes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve routes: {str(e)}")


@router.get("/active")
async def get_active_routes(load_repo=Depends(get_load_repo)):
    """Get all active routes with geometry for real-time map display."""
    return await get_routes(active_only=True, load_repo=load_repo)


@router.get("/performance")
async def get_route_performance(
    time_range: str = "24h",
    load_repo=Depends(get_load_repo)
):
    """Get route performance metrics and analytics."""
    try:
        # Parse time range
        if time_range == "24h":
            interval = "24 hours"
        elif time_range == "7d":
            interval = "7 days"
        elif time_range == "30d":
            interval = "30 days"
        else:
            interval = "24 hours"
        
        # Get performance metrics
        performance_query = f"""
            SELECT
                COUNT(*) as total_routes,
                COUNT(CASE WHEN r.status = 'COMPLETED' THEN 1 END) as completed_routes,
                AVG(r.actual_distance_miles) as avg_distance_miles,
                AVG(r.actual_duration_minutes) as avg_duration_minutes,
                AVG(r.optimization_score) as avg_optimization_score,
                AVG(r.fuel_estimate) as avg_fuel_cost,
                AVG(r.toll_estimate) as avg_toll_cost,
                SUM(r.fuel_estimate) as total_fuel_cost,
                SUM(r.toll_estimate) as total_toll_cost
            FROM routes r
            WHERE r.created_at >= NOW() - INTERVAL '{interval}'
        """
        
        performance = await load_repo.execute_single(performance_query)
        
        # Get on-time performance
        ontime_query = f"""
            SELECT
                COUNT(*) as total_deliveries,
                COUNT(CASE WHEN l.updated_at <= l.delivery_date THEN 1 END) as ontime_deliveries
            FROM routes r
            JOIN loads l ON r.load_id = l.id
            WHERE r.created_at >= NOW() - INTERVAL '{interval}'
                AND l.status = 'DELIVERED'
        """
        
        ontime = await load_repo.execute_single(ontime_query)
        
        # Calculate on-time percentage
        ontime_percentage = 0
        if ontime and ontime['total_deliveries'] > 0:
            ontime_percentage = (ontime['ontime_deliveries'] / ontime['total_deliveries']) * 100
        
        return {
            "time_range": time_range,
            "performance": performance or {},
            "on_time_performance": {
                "total_deliveries": ontime['total_deliveries'] if ontime else 0,
                "ontime_deliveries": ontime['ontime_deliveries'] if ontime else 0,
                "ontime_percentage": round(ontime_percentage, 2)
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving route performance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve route performance: {str(e)}")


@router.post("/optimize")
async def optimize_route(
    start_location: str, 
    end_location: str,
    neo4j_repo=Depends(get_neo4j_repo)
):
    """Find optimal route between locations using Neo4j."""
    try:
        # Use route optimization service
        optimized_route = await route_optimizer.find_optimal_route(
            start_location, 
            end_location,
            neo4j_repo
        )
        
        if not optimized_route:
            raise HTTPException(status_code=404, detail="No route found between specified locations")
        
        return {
            "start_location": start_location,
            "end_location": end_location,
            "optimized_route": optimized_route
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing route from {start_location} to {end_location}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to optimize route: {str(e)}")


@router.post("/optimize-load")
async def optimize_load_route(
    request: OptimizeLoadRouteRequest, 
    background_tasks: BackgroundTasks,
    load_repo=Depends(get_load_repo),
    neo4j_repo=Depends(get_neo4j_repo)
):
    """
    Calculate optimized street-level route for load assignment using Google Maps API.
    """
    try:
        # Get load details
        load = await load_repo.get_load(request.load_id)
        if not load:
            raise HTTPException(status_code=404, detail="Load not found")
        
        # Use route optimization service to calculate optimal route
        from uuid import UUID
        
        load_id = UUID(request.load_id)
        vehicle_id = UUID(request.vehicle_id)
        driver_id = UUID(request.driver_id) if request.driver_id else None
        
        optimized_route = await route_optimizer.optimize_route(
            load_id=load_id,
            vehicle_id=vehicle_id,
            driver_id=driver_id
        )
        
        # Broadcast optimization result
        background_tasks.add_task(broadcast_event_to_websockets, {
            "event_type": "ROUTE_OPTIMIZED",
            "data": {
                "load_id": request.load_id,
                "vehicle_id": request.vehicle_id,
                "route": optimized_route
            }
        })
        
        return optimized_route
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing load route: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to optimize load route: {str(e)}")


@router.post("/advanced-optimize-load")
async def advanced_optimize_load_route(
    request: AdvancedOptimizeLoadRequest, 
    background_tasks: BackgroundTasks,
    load_repo=Depends(get_load_repo),
    neo4j_repo=Depends(get_neo4j_repo)
):
    """
    Calculate optimized street-level route for load assignment using graph relationships.
    """
    try:
        # Get load details
        load = await load_repo.get_load(request.load_id)
        if not load:
            raise HTTPException(status_code=404, detail="Load not found")
        
        # Use advanced route optimization service to calculate optimal route
        advanced_optimizer = get_advanced_route_optimizer(neo4j_repo)
        constraints = OptimizationConstraints(
            max_driver_distance_miles=request.max_driver_distance_miles,
            max_route_duration_hours=request.max_route_duration_hours,
            min_driver_rating=request.min_driver_rating,
            min_carrier_performance=request.min_carrier_performance,
            consider_traffic=request.consider_traffic
        )
        
        optimized_route = await advanced_optimizer.optimize_route(
            load_id=request.load_id,
            constraints=constraints
        )
        
        # Broadcast optimization result
        background_tasks.add_task(broadcast_event_to_websockets, {
            "event_type": "ROUTE_OPTIMIZED",
            "data": {
                "load_id": request.load_id,
                "route": optimized_route
            }
        })
        
        return optimized_route
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing load route: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to optimize load route: {str(e)}")


@router.get("/{route_id}")
async def get_route_details(
    route_id: str,
    load_repo=Depends(get_load_repo)
):
    """Get detailed route information including turn-by-turn directions."""
    try:
        # Get route with load information
        query = """
            SELECT
                r.id, r.load_id, r.driver_id, r.vehicle_id,
                r.origin_location, r.destination_location, r.waypoints,
                r.route_geometry, r.planned_distance_miles, r.planned_duration_minutes,
                r.actual_distance_miles, r.actual_duration_minutes, r.estimated_arrival,
                r.actual_arrival, r.optimization_score, r.fuel_estimate, r.toll_estimate,
                r.status, r.created_at, r.updated_at,
                l.load_number, l.pickup_address, l.delivery_address, l.pickup_date, l.delivery_date,
                l.assigned_vehicle_id, l.assigned_driver_id, l.status as load_status
            FROM routes r
            JOIN loads l ON r.load_id = l.id
            WHERE r.id = $1
        """
        
        route = await load_repo.execute_single(query, route_id)
        
        if not route:
            raise HTTPException(status_code=404, detail="Route not found")
        
        return route
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving route details {route_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve route details: {str(e)}")
