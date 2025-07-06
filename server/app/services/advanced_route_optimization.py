"""Advanced Route Optimization Service leveraging Neo4j Graph Relationships"""
import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID
from dataclasses import dataclass
from datetime import datetime, timedelta
import math

from repositories.neo4j_repository import Neo4jRepository
from repositories.load_repository import LoadRepository
from repositories.driver_repository import DriverRepository
from repositories.vehicle_repository import VehicleRepository
from services.route_optimization import RouteOptimizationService


logger = logging.getLogger(__name__)


@dataclass
class OptimizationConstraints:
    """Optimization constraints for advanced route planning"""
    max_driver_distance_miles: float = 50.0
    max_route_duration_hours: float = 11.0  # HOS compliance
    min_driver_rating: float = 3.0
    min_carrier_performance: float = 70.0
    consider_traffic: bool = True
    allow_multi_load: bool = False
    max_loads_per_route: int = 3


@dataclass
class RouteCandidate:
    """Candidate route with optimization scores"""
    driver_id: str
    vehicle_id: str
    load_ids: List[str]
    total_distance: float
    total_duration: float
    optimization_score: float
    driver_proximity_score: float
    vehicle_suitability_score: float
    carrier_performance_score: float
    cost_efficiency_score: float
    timeline_feasibility_score: float


class AdvancedRouteOptimizationService:
    """Enhanced route optimization using Neo4j graph relationships"""
    
    def __init__(self, neo4j_repo: Neo4jRepository):
        self.neo4j_repo = neo4j_repo
        self.basic_optimizer = RouteOptimizationService()
        
    async def optimize_load_assignment(
        self, 
        load_id: str, 
        constraints: Optional[OptimizationConstraints] = None
    ) -> Dict[str, Any]:
        """
        Advanced load assignment optimization using graph relationships
        """
        constraints = constraints or OptimizationConstraints()
        
        try:
            # Get load details from PostgreSQL via graph data
            load_query = """
            MATCH (l:Load {load_id: $load_id})
            RETURN l.pickup_lat as pickup_lat,
                   l.pickup_lng as pickup_lng,
                   l.delivery_lat as delivery_lat,
                   l.delivery_lng as delivery_lng,
                   l.weight_lbs as weight_lbs,
                   l.load_type as load_type,
                   l.pickup_date as pickup_date,
                   l.delivery_date as delivery_date
            """
            
            load_results = await self.neo4j_repo.execute_query(load_query, {"load_id": load_id})
            if not load_results:
                return {
                    'success': False,
                    'error': f'Load {load_id} not found in graph database'
                }
                
            load_data = load_results[0]
            
            pickup_lat = float(load_data['pickup_lat'])
            pickup_lng = float(load_data['pickup_lng'])
            delivery_lat = float(load_data['delivery_lat'])
            delivery_lng = float(load_data['delivery_lng'])
            
            # Find candidate drivers near pickup location using Neo4j
            candidates = await self._find_optimization_candidates(
                pickup_location=(pickup_lat, pickup_lng),
                delivery_location=(delivery_lat, delivery_lng),
                load_requirements=load_data,
                constraints=constraints
            )
            
            if not candidates:
                raise ValueError("No suitable drivers/vehicles found for optimization")
            
            # Score and rank candidates
            scored_candidates = await self._score_route_candidates(
                candidates, 
                load_data,
                constraints
            )
            
            # Select best candidate
            best_candidate = scored_candidates[0]
            
            # Calculate detailed route using Google Maps
            detailed_route = await self.basic_optimizer._calculate_google_route(
                pickup=(pickup_lat, pickup_lng),
                delivery=(delivery_lat, delivery_lng)
            )
            
            # Enhanced optimization result
            result = {
                'success': True,
                'optimization_method': 'advanced_graph_based',
                'selected_driver_id': best_candidate.driver_id,
                'selected_vehicle_id': best_candidate.vehicle_id,
                'optimization_score': best_candidate.optimization_score,
                'route_details': detailed_route,
                'optimization_factors': {
                    'driver_proximity_score': best_candidate.driver_proximity_score,
                    'vehicle_suitability_score': best_candidate.vehicle_suitability_score,
                    'carrier_performance_score': best_candidate.carrier_performance_score,
                    'cost_efficiency_score': best_candidate.cost_efficiency_score,
                    'timeline_feasibility_score': best_candidate.timeline_feasibility_score
                },
                'alternatives_considered': len(scored_candidates),
                'constraints_applied': {
                    'max_driver_distance': constraints.max_driver_distance_miles,
                    'max_route_duration': constraints.max_route_duration_hours,
                    'min_driver_rating': constraints.min_driver_rating,
                    'min_carrier_performance': constraints.min_carrier_performance
                }
            }
            
            logger.info(f"Advanced optimization completed for load {load_id}: "
                       f"selected driver {best_candidate.driver_id}, "
                       f"score {best_candidate.optimization_score}")
            
            return result
            
        except Exception as e:
            logger.error(f"Advanced route optimization failed for load {load_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_available': True
            }
    
    async def _find_optimization_candidates(
        self,
        pickup_location: Tuple[float, float],
        delivery_location: Tuple[float, float],
        load_requirements: Dict,
        constraints: OptimizationConstraints
    ) -> List[Dict[str, Any]]:
        """Find candidate drivers and vehicles using Neo4j graph queries"""
        
        pickup_lat, pickup_lng = pickup_location
        max_distance = constraints.max_driver_distance_miles
        
        # Advanced Neo4j query to find suitable driver-vehicle combinations
        query = """
        // Find drivers near pickup location with available vehicles
        MATCH (d:Driver)-[:DRIVES]->(v:Vehicle)-[:OWNED_BY]->(c:Carrier)
        WHERE d.status = 'AVAILABLE' 
          AND v.status = 'AVAILABLE'
          AND d.current_latitude IS NOT NULL 
          AND d.current_longitude IS NOT NULL
        
        // Calculate distance from driver to pickup
        WITH d, v, c,
             distance(
                point({latitude: d.current_latitude, longitude: d.current_longitude}),
                point({latitude: $pickup_lat, longitude: $pickup_lng})
             ) / 1609.34 AS distance_miles  // Convert meters to miles
        
        WHERE distance_miles <= $max_distance
          AND v.capacity_weight >= $required_weight
          AND v.capacity_volume >= $required_volume
        
        // Get carrier performance metrics
        OPTIONAL MATCH (c)-[perf:HAS_PERFORMANCE]->(p:Performance)
        
        // Get driver rating from completed loads
        OPTIONAL MATCH (d)-[:ASSIGNED_TO]->(completed_load:Load {status: 'DELIVERED'})
        WITH d, v, c, distance_miles, perf, p,
             avg(completed_load.driver_rating) AS avg_driver_rating,
             count(completed_load) AS completed_loads
        
        RETURN 
            d.id AS driver_id,
            d.first_name + ' ' + d.last_name AS driver_name,
            d.current_latitude AS driver_lat,
            d.current_longitude AS driver_lng,
            d.hours_of_service_remaining AS hos_remaining,
            v.id AS vehicle_id,
            v.vehicle_number AS vehicle_number,
            v.vehicle_type AS vehicle_type,
            v.capacity_weight AS vehicle_capacity_weight,
            v.capacity_volume AS vehicle_capacity_volume,
            c.id AS carrier_id,
            c.name AS carrier_name,
            distance_miles,
            COALESCE(avg_driver_rating, 4.0) AS driver_rating,
            completed_loads,
            COALESCE(p.on_time_percentage, 85.0) AS carrier_performance,
            COALESCE(p.avg_delivery_time, 0.0) AS avg_delivery_time
        
        ORDER BY distance_miles ASC, driver_rating DESC, carrier_performance DESC
        LIMIT 10
        """
        
        # Calculate required capacity based on load
        required_weight = float(load_requirements.get('weight_lbs', 0))
        required_volume = float(load_requirements.get('volume_cubic_feet', 0))
        
        candidates = await self.neo4j_repo.execute_query(
            query,
            pickup_lat=pickup_lat,
            pickup_lng=pickup_lng,
            max_distance=max_distance,
            required_weight=required_weight,
            required_volume=required_volume
        )
        
        logger.info(f"Found {len(candidates)} candidate driver/vehicle combinations")
        return candidates
    
    async def _score_route_candidates(
        self,
        candidates: List[Dict[str, Any]],
        load: Dict,
        constraints: OptimizationConstraints
    ) -> List[RouteCandidate]:
        """Score and rank route candidates using multiple optimization factors"""
        
        scored_candidates = []
        
        for candidate in candidates:
            # Calculate individual scores
            proximity_score = self._calculate_proximity_score(
                candidate['distance_miles'], 
                constraints.max_driver_distance_miles
            )
            
            vehicle_score = self._calculate_vehicle_suitability_score(
                candidate, 
                load
            )
            
            carrier_score = self._calculate_carrier_performance_score(
                candidate['carrier_performance']
            )
            
            cost_score = self._calculate_cost_efficiency_score(
                candidate['distance_miles'],
                candidate['carrier_performance']
            )
            
            timeline_score = self._calculate_timeline_feasibility_score(
                candidate['hos_remaining'],
                candidate['distance_miles']
            )
            
            # Weighted composite score
            composite_score = (
                proximity_score * 0.25 +
                vehicle_score * 0.20 +
                carrier_score * 0.20 +
                cost_score * 0.20 +
                timeline_score * 0.15
            )
            
            route_candidate = RouteCandidate(
                driver_id=candidate['driver_id'],
                vehicle_id=candidate['vehicle_id'],
                load_ids=[load['load_id']],
                total_distance=candidate['distance_miles'],
                total_duration=candidate['distance_miles'] * 2,  # Rough estimate
                optimization_score=composite_score,
                driver_proximity_score=proximity_score,
                vehicle_suitability_score=vehicle_score,
                carrier_performance_score=carrier_score,
                cost_efficiency_score=cost_score,
                timeline_feasibility_score=timeline_score
            )
            
            scored_candidates.append(route_candidate)
        
        # Sort by optimization score (highest first)
        scored_candidates.sort(key=lambda x: x.optimization_score, reverse=True)
        
        logger.info(f"Scored {len(scored_candidates)} candidates, "
                   f"best score: {scored_candidates[0].optimization_score:.2f}")
        
        return scored_candidates
    
    def _calculate_proximity_score(self, distance_miles: float, max_distance: float) -> float:
        """Score based on driver proximity to pickup location"""
        if distance_miles > max_distance:
            return 0.0
        # Linear decay: closer = better score
        return max(0.0, 100.0 * (1 - distance_miles / max_distance))
    
    def _calculate_vehicle_suitability_score(self, candidate: Dict, load: Dict) -> float:
        """Score based on vehicle suitability for the load"""
        vehicle_weight_capacity = candidate['vehicle_capacity_weight']
        vehicle_volume_capacity = candidate['vehicle_capacity_volume']
        
        required_weight = float(load.get('weight_lbs', 0))
        required_volume = float(load.get('volume_cubic_feet', 0))
        
        # Check if vehicle can handle the load
        if vehicle_weight_capacity < required_weight or vehicle_volume_capacity < required_volume:
            return 0.0
        
        # Efficiency scoring: prefer vehicles not over-sized for the load
        weight_utilization = required_weight / vehicle_weight_capacity if vehicle_weight_capacity > 0 else 0
        volume_utilization = required_volume / vehicle_volume_capacity if vehicle_volume_capacity > 0 else 0
        
        # Optimal utilization range: 60-90%
        avg_utilization = (weight_utilization + volume_utilization) / 2
        
        if 0.6 <= avg_utilization <= 0.9:
            return 100.0
        elif avg_utilization < 0.6:
            return 60.0 + (avg_utilization / 0.6) * 40.0  # Scale up to optimal
        else:
            return 100.0 - (avg_utilization - 0.9) * 200.0  # Penalty for over-utilization
    
    def _calculate_carrier_performance_score(self, carrier_performance: float) -> float:
        """Score based on carrier historical performance"""
        # Carrier performance is already a percentage (0-100)
        return min(100.0, max(0.0, carrier_performance))
    
    def _calculate_cost_efficiency_score(self, distance_miles: float, carrier_performance: float) -> float:
        """Score based on cost efficiency (shorter routes + reliable carriers)"""
        # Combine distance efficiency with carrier reliability
        distance_efficiency = max(0.0, 100.0 - distance_miles)  # Shorter is better
        reliability_bonus = carrier_performance * 0.3  # Reliable carriers get bonus
        
        return min(100.0, distance_efficiency + reliability_bonus)
    
    def _calculate_timeline_feasibility_score(self, hos_remaining: float, distance_miles: float) -> float:
        """Score based on hours of service and timeline feasibility"""
        if hos_remaining is None:
            hos_remaining = 11.0  # Default to full HOS
        
        # Estimate time needed (including service time)
        estimated_drive_time = distance_miles / 50.0  # Assume 50 mph average
        estimated_total_time = estimated_drive_time + 2.0  # Add 2 hours for loading/unloading
        
        if estimated_total_time > hos_remaining:
            return 0.0  # Cannot complete within HOS
        
        # Score based on HOS utilization (prefer reasonable utilization)
        hos_utilization = estimated_total_time / hos_remaining
        
        if hos_utilization <= 0.8:
            return 100.0  # Good buffer
        else:
            return 100.0 * (1.0 - hos_utilization)  # Penalty for tight timeline
    
    async def optimize_multi_load_route(
        self,
        load_ids: List[str],
        constraints: Optional[OptimizationConstraints] = None
    ) -> Dict[str, Any]:
        """Optimize route for multiple loads (consolidation optimization)"""
        constraints = constraints or OptimizationConstraints()
        constraints.allow_multi_load = True
        
        if not constraints.allow_multi_load:
            raise ValueError("Multi-load optimization not enabled in constraints")
        
        # This is a complex optimization that would involve:
        # 1. Finding loads that can be efficiently combined
        # 2. Calculating optimal pickup/delivery sequences
        # 3. Ensuring capacity and time constraints
        # 4. Using Neo4j to find best driver/vehicle combinations
        
        logger.info(f"Multi-load route optimization requested for {len(load_ids)} loads")
        
        # For now, return a placeholder indicating advanced feature
        return {
            'success': False,
            'error': 'Multi-load route optimization is a planned advanced feature',
            'loads_count': len(load_ids),
            'recommendation': 'Use single-load optimization for each load individually'
        }


# Global service instance
async def get_advanced_route_optimizer(neo4j_repo: Neo4jRepository) -> AdvancedRouteOptimizationService:
    """Get advanced route optimization service instance"""
    return AdvancedRouteOptimizationService(neo4j_repo)
