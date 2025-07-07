"""Analytics and dashboard endpoints for TMS API."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
import logging

from dependencies import get_load_repo, get_timescale_repo, get_neo4j_repo
from services.graph_query_service import get_graph_query_service
from models.domain import OptimalDriverVehiclePairsRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
async def get_dashboard_data(
    time_range: str = "24h",
    load_repo=Depends(get_load_repo),
    timescale_repo=Depends(get_timescale_repo)
):
    """Get comprehensive dashboard analytics data."""
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
        
        # Get load statistics
        load_stats_query = f"""
            SELECT 
                COUNT(*) as total_loads,
                COUNT(CASE WHEN status = 'CREATED' THEN 1 END) as pending_loads,
                COUNT(CASE WHEN status = 'ASSIGNED' THEN 1 END) as assigned_loads,
                COUNT(CASE WHEN status = 'PICKED_UP' THEN 1 END) as picked_up_loads,
                COUNT(CASE WHEN status = 'IN_TRANSIT' THEN 1 END) as in_transit_loads,
                COUNT(CASE WHEN status = 'DELIVERED' THEN 1 END) as delivered_loads,
                COUNT(CASE WHEN status = 'CANCELLED' THEN 1 END) as cancelled_loads,
                AVG(CASE WHEN rate IS NOT NULL THEN rate::numeric END) as avg_rate
            FROM loads 
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """
        
        load_stats = await load_repo.execute_single(load_stats_query)
        
        # Get vehicle statistics
        vehicle_stats_query = """
            SELECT 
                COUNT(*) as total_vehicles,
                COUNT(CASE WHEN status = 'AVAILABLE' THEN 1 END) as available_vehicles,
                COUNT(CASE WHEN status = 'ASSIGNED' THEN 1 END) as assigned_vehicles,
                COUNT(CASE WHEN status = 'IN_TRANSIT' THEN 1 END) as in_transit_vehicles,
                COUNT(CASE WHEN status = 'MAINTENANCE' THEN 1 END) as maintenance_vehicles
            FROM vehicles
        """
        
        vehicle_stats = await load_repo.execute_single(vehicle_stats_query)
        
        # Get driver statistics
        driver_stats_query = """
            SELECT 
                COUNT(*) as total_drivers,
                COUNT(CASE WHEN status = 'AVAILABLE' THEN 1 END) as available_drivers,
                COUNT(CASE WHEN status = 'DRIVING' THEN 1 END) as driving_drivers,
                COUNT(CASE WHEN status = 'ON_DUTY' THEN 1 END) as on_duty_drivers,
                COUNT(CASE WHEN status = 'OFF_DUTY' THEN 1 END) as off_duty_drivers
            FROM drivers
        """
        
        driver_stats = await load_repo.execute_single(driver_stats_query)
        
        # Get recent events from TimescaleDB
        recent_events_query = f"""
            SELECT 
                event_type,
                COUNT(*) as event_count
            FROM load_events 
            WHERE time >= NOW() - INTERVAL '7 days'
            GROUP BY event_type
            ORDER BY event_count DESC
            LIMIT 10
        """
        
        try:
            recent_events = await timescale_repo.execute_query(recent_events_query)
        except Exception as e:
            logger.warning(f"Error fetching recent events: {e}")
            recent_events = []
        
        # Calculate performance metrics
        performance_query = f"""
            SELECT 
                COUNT(CASE WHEN status = 'DELIVERED' AND updated_at <= delivery_date THEN 1 END) as ontime_deliveries,
                COUNT(CASE WHEN status = 'DELIVERED' THEN 1 END) as total_deliveries,
                AVG(CASE WHEN status = 'DELIVERED' THEN 
                    EXTRACT(EPOCH FROM (updated_at - created_at))/3600 
                END) as avg_delivery_hours
            FROM loads 
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """
        
        performance = await load_repo.execute_single(performance_query)
        
        # Calculate on-time percentage
        ontime_percentage = 0
        if performance and performance['total_deliveries'] and performance['total_deliveries'] > 0:
            ontime_percentage = (performance['ontime_deliveries'] / performance['total_deliveries']) * 100
        
        # Get revenue data
        revenue_query = f"""
            SELECT 
                SUM(CASE WHEN rate IS NOT NULL THEN rate::numeric ELSE 0 END) as total_revenue,
                COUNT(CASE WHEN status = 'DELIVERED' THEN 1 END) as completed_loads_count
            FROM loads 
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """
        
        revenue = await load_repo.execute_single(revenue_query)
        
        return {
            "time_range": time_range,
            "summary": {
                "total_loads": load_stats['total_loads'] if load_stats else 0,
                "total_vehicles": vehicle_stats['total_vehicles'] if vehicle_stats else 0,
                "total_drivers": driver_stats['total_drivers'] if driver_stats else 0,
                "total_revenue": float(revenue['total_revenue']) if revenue and revenue['total_revenue'] else 0.0,
                "ontime_percentage": round(ontime_percentage, 2)
            },
            "loads": {
                "total": load_stats['total_loads'] if load_stats else 0,
                "pending": load_stats['pending_loads'] if load_stats else 0,
                "assigned": load_stats['assigned_loads'] if load_stats else 0,
                "picked_up": load_stats['picked_up_loads'] if load_stats else 0,
                "in_transit": load_stats['in_transit_loads'] if load_stats else 0,
                "delivered": load_stats['delivered_loads'] if load_stats else 0,
                "cancelled": load_stats['cancelled_loads'] if load_stats else 0,
                "avg_rate": float(load_stats['avg_rate']) if load_stats and load_stats['avg_rate'] else 0.0
            },
            "vehicles": {
                "total": vehicle_stats['total_vehicles'] if vehicle_stats else 0,
                "available": vehicle_stats['available_vehicles'] if vehicle_stats else 0,
                "assigned": vehicle_stats['assigned_vehicles'] if vehicle_stats else 0,
                "in_transit": vehicle_stats['in_transit_vehicles'] if vehicle_stats else 0,
                "maintenance": vehicle_stats['maintenance_vehicles'] if vehicle_stats else 0
            },
            "drivers": {
                "total": driver_stats['total_drivers'] if driver_stats else 0,
                "available": driver_stats['available_drivers'] if driver_stats else 0,
                "driving": driver_stats['driving_drivers'] if driver_stats else 0,
                "on_duty": driver_stats['on_duty_drivers'] if driver_stats else 0,
                "off_duty": driver_stats['off_duty_drivers'] if driver_stats else 0
            },
            "performance": {
                "ontime_deliveries": performance['ontime_deliveries'] if performance else 0,
                "total_deliveries": performance['total_deliveries'] if performance else 0,
                "ontime_percentage": round(ontime_percentage, 2),
                "avg_delivery_hours": round(float(performance['avg_delivery_hours']), 2) if performance and performance['avg_delivery_hours'] else 0.0
            },
            "recent_events": recent_events or [],
            "revenue": {
                "total": float(revenue['total_revenue']) if revenue and revenue['total_revenue'] else 0.0,
                "completed_loads": revenue['completed_loads_count'] if revenue else 0
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving dashboard data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve dashboard data: {str(e)}")


@router.get("/loads/trend")
async def get_loads_trend(
    days: int = 7,
    load_repo=Depends(get_load_repo)
):
    """Get load creation trend over time."""
    try:
        query = f"""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as load_count,
                COUNT(CASE WHEN status = 'DELIVERED' THEN 1 END) as delivered_count
            FROM loads 
            WHERE created_at >= NOW() - INTERVAL '{days} days'
            GROUP BY DATE(created_at)
            ORDER BY date
        """
        
        trend_data = await load_repo.execute_query(query)
        
        return {
            "period_days": days,
            "trend_data": trend_data
        }
    except Exception as e:
        logger.error(f"Error retrieving loads trend: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve loads trend: {str(e)}")


@router.get("/performance/carriers")
async def get_carrier_performance(
    days: int = 30,
    load_repo=Depends(get_load_repo)
):
    """Get carrier performance metrics."""
    try:
        query = f"""
            SELECT 
                c.name as carrier_name,
                COUNT(l.id) as total_loads,
                COUNT(CASE WHEN l.status = 'DELIVERED' THEN 1 END) as delivered_loads,
                COUNT(CASE WHEN l.status = 'DELIVERED' AND l.updated_at <= l.delivery_date THEN 1 END) as ontime_loads,
                AVG(CASE WHEN l.rate IS NOT NULL THEN l.rate::numeric END) as avg_rate
            FROM carriers c
            LEFT JOIN vehicles v ON c.id = v.carrier_id
            LEFT JOIN loads l ON v.id = l.assigned_vehicle_id 
                AND l.created_at >= NOW() - INTERVAL '{days} days'
            GROUP BY c.id, c.name
            HAVING COUNT(l.id) > 0
            ORDER BY delivered_loads DESC, ontime_loads DESC
        """
        
        carrier_performance = await load_repo.execute_query(query)
        
        # Calculate percentages
        for carrier in carrier_performance:
            if carrier['total_loads'] > 0:
                carrier['delivery_rate'] = round((carrier['delivered_loads'] / carrier['total_loads']) * 100, 2)
            else:
                carrier['delivery_rate'] = 0.0
                
            if carrier['delivered_loads'] > 0:
                carrier['ontime_rate'] = round((carrier['ontime_loads'] / carrier['delivered_loads']) * 100, 2)
            else:
                carrier['ontime_rate'] = 0.0
                
            carrier['avg_rate'] = float(carrier['avg_rate']) if carrier['avg_rate'] else 0.0
        
        return {
            "period_days": days,
            "carrier_performance": carrier_performance
        }
    except Exception as e:
        logger.error(f"Error retrieving carrier performance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve carrier performance: {str(e)}")


# Advanced Neo4j Analytics Endpoints
@router.get("/nearby-drivers")
async def find_nearby_drivers(
    pickup_lat: float,
    pickup_lng: float,
    radius_miles: float = 50.0,
    status_filter: str = "AVAILABLE",
    min_rating: Optional[float] = None,
    vehicle_type_filter: Optional[str] = None,
    neo4j_repo=Depends(get_neo4j_repo)
):
    """
    Find drivers within specified radius of pickup location using Neo4j graph queries.
    
    This endpoint uses Neo4j spatial functions to efficiently find drivers based on:
    - Geographic proximity to pickup location
    - Driver availability status
    - Minimum rating requirements
    - Vehicle type compatibility
    """
    try:
        graph_service = await get_graph_query_service(neo4j_repo)
        
        nearby_drivers = await graph_service.find_nearby_drivers(
            pickup_lat=pickup_lat,
            pickup_lng=pickup_lng,
            radius_miles=radius_miles,
            status_filter=status_filter,
            min_rating=min_rating,
            vehicle_type_filter=vehicle_type_filter
        )
        
        return {
            "success": True,
            "drivers_found": len(nearby_drivers),
            "search_criteria": {
                "pickup_location": {"lat": pickup_lat, "lng": pickup_lng},
                "radius_miles": radius_miles,
                "status_filter": status_filter,
                "min_rating": min_rating,
                "vehicle_type_filter": vehicle_type_filter
            },
            "drivers": [{
                "driver_id": driver.driver_id,
                "driver_name": driver.driver_name,
                "current_location": driver.current_location,
                "distance_miles": driver.distance_miles,
                "status": driver.status,
                "carrier_name": driver.carrier_name,
                "vehicle_type": driver.vehicle_type,
                "rating": driver.rating,
                "hours_available": driver.hours_available
            } for driver in nearby_drivers]
        }
        
    except Exception as e:
        logger.error(f"Error finding nearby drivers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to find nearby drivers: {str(e)}")


@router.get("/carrier-performance")
async def get_advanced_carrier_performance(
    carrier_id: Optional[str] = None,
    time_period_days: int = 90,
    neo4j_repo=Depends(get_neo4j_repo)
):
    """
    Get comprehensive carrier performance analytics from Neo4j graph relationships.
    
    Analyzes carrier performance metrics including:
    - On-time delivery rates
    - Average load ratings
    - Cost efficiency scores
    - Revenue generation
    - Active fleet metrics
    """
    try:
        graph_service = await get_graph_query_service(neo4j_repo)
        
        carrier_metrics = await graph_service.get_carrier_performance_metrics(
            carrier_id=carrier_id,
            time_period_days=time_period_days
        )
        
        return {
            "success": True,
            "analysis_period_days": time_period_days,
            "carriers_analyzed": len(carrier_metrics),
            "carrier_metrics": [{
                "carrier_id": metrics.carrier_id,
                "carrier_name": metrics.carrier_name,
                "total_loads_completed": metrics.total_loads_completed,
                "on_time_delivery_rate": metrics.on_time_delivery_rate,
                "average_rating": metrics.average_rating,
                "cost_efficiency_score": metrics.cost_efficiency_score,
                "revenue_generated": metrics.revenue_generated,
                "active_drivers": metrics.active_drivers,
                "active_vehicles": metrics.active_vehicles,
                "specialties": metrics.specialties
            } for metrics in carrier_metrics]
        }
        
    except Exception as e:
        logger.error(f"Error getting advanced carrier performance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get carrier performance: {str(e)}")


@router.get("/fleet-utilization")
async def get_fleet_utilization_analytics(
    neo4j_repo=Depends(get_neo4j_repo)
):
    """
    Get comprehensive fleet utilization metrics from Neo4j graph analysis.
    
    Provides insights into:
    - Fleet utilization rates
    - Average miles per vehicle
    - Maintenance requirements
    - Fuel efficiency metrics
    - Revenue per vehicle
    """
    try:
        graph_service = await get_graph_query_service(neo4j_repo)
        
        fleet_metrics = await graph_service.get_fleet_utilization_metrics()
        
        return {
            "success": True,
            "fleet_metrics": {
                "total_vehicles": fleet_metrics.total_vehicles,
                "active_vehicles": fleet_metrics.active_vehicles,
                "utilization_rate": fleet_metrics.utilization_rate,
                "average_miles_per_vehicle": fleet_metrics.average_miles_per_vehicle,
                "maintenance_due_count": fleet_metrics.maintenance_due_count,
                "fuel_efficiency_avg": fleet_metrics.fuel_efficiency_avg,
                "revenue_per_vehicle": fleet_metrics.revenue_per_vehicle
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting fleet utilization analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get fleet utilization: {str(e)}")


@router.post("/optimal-driver-vehicle-pairs")
async def find_optimal_driver_vehicle_pairs(
    request: OptimalDriverVehiclePairsRequest,
    neo4j_repo=Depends(get_neo4j_repo)
):
    """
    Find optimal driver-vehicle pairs for specific load requirements using graph analysis.
    
    Uses composite scoring algorithm considering:
    - Driver proximity to pickup location
    - Vehicle capacity and suitability
    - Carrier performance history
    - Cost efficiency factors
    """
    try:
        graph_service = await get_graph_query_service(neo4j_repo)
        
        optimal_pairs = await graph_service.find_optimal_driver_vehicle_pairs(
            pickup_lat=request.pickup_lat,
            pickup_lng=request.pickup_lng,
            delivery_lat=request.delivery_lat,
            delivery_lng=request.delivery_lng,
            load_weight=request.load_weight,
            load_type=request.load_type,
            max_distance_miles=request.max_distance_miles
        )
        
        return {
            "success": True,
            "load_requirements": {
                "pickup_location": {"lat": request.pickup_lat, "lng": request.pickup_lng},
                "delivery_location": {"lat": request.delivery_lat, "lng": request.delivery_lng},
                "load_weight": request.load_weight,
                "load_type": request.load_type,
                "max_distance_miles": request.max_distance_miles
            },
            "optimal_pairs_found": len(optimal_pairs),
            "driver_vehicle_pairs": optimal_pairs
        }
        
    except Exception as e:
        logger.error(f"Error finding optimal driver-vehicle pairs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to find optimal pairs: {str(e)}")
