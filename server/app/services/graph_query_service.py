"""
Neo4j Graph Query Service
Provides analytics and query functionality for Neo4j graph database
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from repositories.neo4j_repository import Neo4jRepository
from models.domain import (
    NearbyDriverResponse,
    CarrierPerformanceMetrics, 
    FleetUtilizationMetrics,
    OptimalDriverVehiclePair
)

logger = logging.getLogger(__name__)


class GraphQueryService:
    """Service for executing analytics queries against Neo4j graph database"""
    
    def __init__(self, neo4j_repo: Neo4jRepository):
        self.neo4j_repo = neo4j_repo
    
    async def find_nearby_drivers(
        self, 
        pickup_lat: float, 
        pickup_lng: float, 
        radius_miles: float = 50.0,
        status_filter: str = "AVAILABLE",
        min_rating: Optional[float] = None,
        vehicle_type_filter: Optional[str] = None
    ) -> List[NearbyDriverResponse]:
        """Find drivers within specified radius of pickup location"""
        
        # Convert miles to meters for Neo4j spatial functions
        radius_meters = radius_miles * 1609.34
        
        query = """
        MATCH (d:Driver)-[:DRIVES]->(v:Vehicle)
        WHERE d.status = $status_filter
        AND d.current_latitude IS NOT NULL 
        AND d.current_longitude IS NOT NULL
        AND distance(
            point({latitude: d.current_latitude, longitude: d.current_longitude}),
            point({latitude: $pickup_lat, longitude: $pickup_lng})
        ) <= $radius_meters
        """
        
        params = {
            "pickup_lat": pickup_lat,
            "pickup_lng": pickup_lng,
            "radius_meters": radius_meters,
            "status_filter": status_filter
        }
        
        # Add optional filters
        if min_rating is not None:
            query += " AND d.rating >= $min_rating"
            params["min_rating"] = min_rating
            
        if vehicle_type_filter is not None:
            query += " AND v.vehicle_type = $vehicle_type_filter"
            params["vehicle_type_filter"] = vehicle_type_filter
        
        query += """
        RETURN d.driver_id as driver_id, 
               d.name as driver_name,
               d.phone as driver_phone,
               d.rating as driver_rating,
               d.current_latitude as latitude,
               d.current_longitude as longitude,
               v.vehicle_id as vehicle_id,
               v.vehicle_type as vehicle_type,
               v.capacity_weight as capacity_weight,
               distance(
                   point({latitude: d.current_latitude, longitude: d.current_longitude}),
                   point({latitude: $pickup_lat, longitude: $pickup_lng})
               ) / 1609.34 as distance_miles
        ORDER BY distance_miles ASC
        LIMIT 50
        """
        
        try:
            results = await self.neo4j_repo.execute_query(query, params)
            return [
                NearbyDriverResponse(
                    driver_id=record["driver_id"],
                    driver_name=record["driver_name"], 
                    driver_phone=record["driver_phone"],
                    driver_rating=record["driver_rating"],
                    latitude=record["latitude"],
                    longitude=record["longitude"],
                    vehicle_id=record["vehicle_id"],
                    vehicle_type=record["vehicle_type"],
                    capacity_weight=record["capacity_weight"],
                    distance_miles=record["distance_miles"]
                ) for record in results
            ]
        except Exception as e:
            logger.error(f"Error finding nearby drivers: {e}")
            return []
    
    async def get_carrier_performance_metrics(
        self, 
        carrier_id: Optional[str] = None,
        time_period_days: int = 90
    ) -> List[CarrierPerformanceMetrics]:
        """Get comprehensive carrier performance metrics from graph relationships"""
        
        base_query = """
        MATCH (c:Carrier)
        """
        
        params = {"days_ago": time_period_days}
        
        if carrier_id:
            base_query += " WHERE c.carrier_id = $carrier_id"
            params["carrier_id"] = carrier_id
        
        query = base_query + """
        OPTIONAL MATCH (c)-[:OWNS]->(v:Vehicle)-[:ASSIGNED_TO]->(l:Load)
        WHERE l.created_at >= datetime() - duration({days: $days_ago})
        
        WITH c, 
             count(DISTINCT l) as total_loads,
             count(DISTINCT v) as active_vehicles,
             avg(CASE WHEN l.status = 'DELIVERED' AND l.delivered_at <= l.scheduled_delivery THEN 1.0 ELSE 0.0 END) as on_time_rate,
             avg(l.rate) as avg_rate,
             sum(l.rate) as total_revenue
        
        RETURN c.carrier_id as carrier_id,
               c.name as carrier_name,
               total_loads,
               active_vehicles,
               ROUND(on_time_rate * 100, 2) as on_time_percentage,
               ROUND(avg_rate, 2) as average_rate,
               ROUND(total_revenue, 2) as total_revenue,
               CASE WHEN active_vehicles > 0 THEN ROUND(total_revenue / active_vehicles, 2) ELSE 0 END as revenue_per_vehicle
        ORDER BY total_revenue DESC
        """
        
        try:
            results = await self.neo4j_repo.execute_query(query, params)
            return [
                CarrierPerformanceMetrics(
                    carrier_id=record["carrier_id"],
                    carrier_name=record["carrier_name"],
                    total_loads_completed=record["total_loads"],
                    on_time_delivery_rate=record["on_time_percentage"],
                    average_rating=4.2,  # Default rating since not in query
                    cost_efficiency_score=0.85,  # Default score
                    revenue_generated=record["total_revenue"],
                    active_drivers=0,  # Would need separate query
                    active_vehicles=record["active_vehicles"],
                    specialties=["General Freight"]  # Default specialties
                ) for record in results
            ]
        except Exception as e:
            logger.error(f"Error getting carrier performance analytics: {e}")
            return []
    
    async def get_fleet_utilization_metrics(self) -> FleetUtilizationMetrics:
        """Get comprehensive fleet utilization metrics from graph analysis"""
        
        query = """
        MATCH (v:Vehicle)
        OPTIONAL MATCH (v)-[:ASSIGNED_TO]->(l:Load)
        WHERE l.created_at >= datetime() - duration({days: 30})
        
        WITH v,
             count(l) as loads_last_30_days,
             sum(l.distance_miles) as total_miles,
             avg(l.rate) as avg_revenue_per_load
        
        RETURN count(v) as total_vehicles,
               count(CASE WHEN loads_last_30_days > 0 THEN 1 END) as active_vehicles,
               ROUND(avg(loads_last_30_days), 2) as avg_loads_per_vehicle,
               ROUND(avg(total_miles), 2) as avg_miles_per_vehicle,
               ROUND(avg(avg_revenue_per_load), 2) as avg_revenue_per_load,
               ROUND(sum(total_miles * avg_revenue_per_load) / count(v), 2) as revenue_per_vehicle,
               ROUND((count(CASE WHEN loads_last_30_days > 0 THEN 1 END) * 100.0) / count(v), 2) as utilization_percentage
        """
        
        try:
            results = await self.neo4j_repo.execute_query(query)
            if results:
                record = results[0]
                return FleetUtilizationMetrics(
                    total_vehicles=record["total_vehicles"],
                    active_vehicles=record["active_vehicles"],
                    utilization_rate=record["utilization_percentage"],  # Map to expected field name
                    average_miles_per_vehicle=record["avg_miles_per_vehicle"],
                    maintenance_due_count=0,  # Default value since not in query
                    fuel_efficiency_avg=25.0,  # Default value since not in query
                    revenue_per_vehicle=record["revenue_per_vehicle"]
                )
            else:
                return FleetUtilizationMetrics()
        except Exception as e:
            logger.error(f"Error getting fleet utilization analytics: {e}")
            return FleetUtilizationMetrics()
    
    async def find_optimal_driver_vehicle_pairs(
        self,
        pickup_lat: float,
        pickup_lng: float,
        delivery_lat: float,
        delivery_lng: float,
        weight_lbs: float,
        commodity_type: str,
        max_pairs: int = 10
    ) -> List[OptimalDriverVehiclePair]:
        """Find optimal driver-vehicle pairs using composite scoring algorithm"""
        
        query = """
        MATCH (d:Driver)-[:DRIVES]->(v:Vehicle)-[:OWNED_BY]->(c:Carrier)
        WHERE d.status = 'AVAILABLE'
        AND v.capacity_weight >= $weight_lbs
        AND d.current_latitude IS NOT NULL
        AND d.current_longitude IS NOT NULL
        
        WITH d, v, c,
             distance(
                 point({latitude: d.current_latitude, longitude: d.current_longitude}),
                 point({latitude: $pickup_lat, longitude: $pickup_lng})
             ) / 1609.34 as pickup_distance_miles,
             distance(
                 point({latitude: $pickup_lat, longitude: $pickup_lng}),
                 point({latitude: $delivery_lat, longitude: $delivery_lng})
             ) / 1609.34 as route_distance_miles
        
        // Composite scoring algorithm
        WITH d, v, c, pickup_distance_miles, route_distance_miles,
             // Distance score (closer is better, max 50 points)
             CASE 
                 WHEN pickup_distance_miles <= 10 THEN 50
                 WHEN pickup_distance_miles <= 25 THEN 40
                 WHEN pickup_distance_miles <= 50 THEN 30
                 WHEN pickup_distance_miles <= 100 THEN 20
                 ELSE 10 
             END as distance_score,
             
             // Driver rating score (max 25 points)
             COALESCE(d.rating, 3.0) * 5 as rating_score,
             
             // Carrier performance score (max 25 points)  
             COALESCE(c.performance_score, 3.0) * 5 as carrier_score
        
        WITH d, v, c, pickup_distance_miles, route_distance_miles,
             distance_score + rating_score + carrier_score as composite_score
        
        RETURN d.driver_id as driver_id,
               d.name as driver_name, 
               d.phone as driver_phone,
               d.rating as driver_rating,
               v.vehicle_id as vehicle_id,
               v.vehicle_type as vehicle_type,
               v.capacity_weight as vehicle_capacity,
               c.carrier_id as carrier_id,
               c.name as carrier_name,
               ROUND(pickup_distance_miles, 2) as pickup_distance_miles,
               ROUND(route_distance_miles, 2) as route_distance_miles,
               ROUND(composite_score, 2) as composite_score
        
        ORDER BY composite_score DESC
        LIMIT $max_pairs
        """
        
        params = {
            "pickup_lat": pickup_lat,
            "pickup_lng": pickup_lng,
            "delivery_lat": delivery_lat,
            "delivery_lng": delivery_lng,
            "weight_lbs": weight_lbs,
            "max_pairs": max_pairs
        }
        
        try:
            results = await self.neo4j_repo.execute_query(query, params)
            return [
                OptimalDriverVehiclePair(
                    driver_id=record["driver_id"],
                    driver_name=record["driver_name"],
                    driver_phone=record["driver_phone"],
                    driver_rating=record["driver_rating"],
                    vehicle_id=record["vehicle_id"],
                    vehicle_type=record["vehicle_type"],
                    vehicle_capacity=record["vehicle_capacity"],
                    carrier_id=record["carrier_id"],
                    carrier_name=record["carrier_name"],
                    pickup_distance_miles=record["pickup_distance_miles"],
                    route_distance_miles=record["route_distance_miles"],
                    composite_score=record["composite_score"]
                ) for record in results
            ]
        except Exception as e:
            logger.error(f"Error finding optimal driver-vehicle pairs: {e}")
            return []


async def get_graph_query_service(neo4j_repo: Neo4jRepository) -> GraphQueryService:
    """Factory function to create GraphQueryService instance"""
    return GraphQueryService(neo4j_repo)
