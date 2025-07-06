"""Analytics and dashboard endpoints for TMS API."""
from fastapi import APIRouter, HTTPException, Depends
import logging

from dependencies import get_load_repo, get_timescale_repo

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
            WHERE created_at >= NOW() - INTERVAL '7 days'
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
