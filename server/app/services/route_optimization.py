"""
Route Optimization Service
Handles Google Maps API integration for calculating optimized routes
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
import googlemaps
from dependencies import get_load_repo
from models.events import EventType, RouteOptimizedEvent
from kafka.producer import get_producer
from uuid import UUID
import json

logger = logging.getLogger(__name__)

class RouteOptimizationService:
    def __init__(self, google_maps_key: Optional[str] = None):
        self.google_maps_key = google_maps_key or os.getenv('MAPS_API_KEY')
        
        if not self.google_maps_key:
            logger.warning("Google Maps API key not provided, falling back to straight-line calculations")
            self.gmaps = None
        else:
            self.gmaps = googlemaps.Client(key=self.google_maps_key)
        
        # Kafka producer will be initialized when needed
        self.kafka_producer = None
    
    async def optimize_route(self, load_id: UUID, vehicle_id: UUID, driver_id: Optional[UUID] = None) -> Dict:
        """
        Optimize route for a load assignment to a vehicle
        Driver assignment is optional since route optimization is primarily about the vehicle and load
        """
        load_repository = await get_load_repo()
        
        try:
            # Get load details
            load_result = await load_repository.get_load(str(load_id))
            
            if not load_result:
                raise ValueError(f"Load {load_id} not found")
            
            pickup_coords = (load_result['pickup_latitude'], load_result['pickup_longitude'])  # lat, lng
            delivery_coords = (load_result['delivery_latitude'], load_result['delivery_longitude'])  # lat, lng
            
            # Calculate route using Google Maps if available
            if self.gmaps:
                route_data = await self._calculate_google_route(pickup_coords, delivery_coords)
            else:
                route_data = self._calculate_straight_line_route(pickup_coords, delivery_coords)
            
            # Save optimized route to database
            route_id = await self._save_optimized_route(
                load_id, driver_id, vehicle_id, route_data, load_result, load_repository
            )
            
            # Publish route optimization event
            await self._publish_route_optimized_event(
                route_id, load_id, driver_id, vehicle_id, route_data
            )
            
            return {
                'success': True,
                'route_id': route_id,
                'distance_miles': route_data['distance_miles'],
                'duration_minutes': route_data['duration_minutes'],
                'optimization_score': route_data['optimization_score'],
                'route_geometry': route_data['route_geometry']
            }
            
        except Exception as e:
            logger.error(f"Route optimization failed for load {load_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _calculate_google_route(self, pickup: Tuple[float, float], delivery: Tuple[float, float]) -> Dict:
        """Calculate route using Google Maps Directions API"""
        try:
            # Request optimized route with traffic considerations
            directions_result = self.gmaps.directions(
                origin=pickup,
                destination=delivery,
                mode="driving",
                departure_time="now",  # Use current traffic
                traffic_model="best_guess",
                optimize_waypoints=True,
                alternatives=False  # Get single best route
            )
            
            if not directions_result:
                raise Exception("No route found by Google Maps")
            
            route = directions_result[0]
            leg = route['legs'][0]
            
            # Extract route geometry (encoded polyline)
            polyline_points = route['overview_polyline']['points']
            
            # Convert to coordinates for database storage
            route_coords = googlemaps.convert.decode_polyline(polyline_points)
            
            # Create LINESTRING geometry for PostGIS
            linestring_coords = [[coord['lng'], coord['lat']] for coord in route_coords]
            route_geometry = f"LINESTRING({','.join([f'{lng} {lat}' for lng, lat in linestring_coords])})"
            
            return {
                'distance_miles': round(leg['distance']['value'] * 0.000621371, 2),  # meters to miles
                'duration_minutes': round(leg['duration']['value'] / 60),  # seconds to minutes
                'duration_in_traffic_minutes': round(leg.get('duration_in_traffic', {}).get('value', leg['duration']['value']) / 60),
                'route_geometry': route_geometry,
                'encoded_polyline': polyline_points,
                'steps': self._extract_turn_by_turn_directions(leg['steps']),
                'optimization_score': self._calculate_optimization_score(leg),
                'traffic_considered': True
            }
            
        except Exception as e:
            logger.error(f"Google Maps route calculation failed: {str(e)}")
            # Fallback to straight line
            return self._calculate_straight_line_route(pickup, delivery)
    
    def _calculate_straight_line_route(self, pickup: Tuple[float, float], delivery: Tuple[float, float]) -> Dict:
        """Fallback straight-line route calculation"""
        import math
        
        # Haversine formula for distance
        lat1, lon1 = math.radians(pickup[0]), math.radians(pickup[1])
        lat2, lon2 = math.radians(delivery[0]), math.radians(delivery[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        distance_miles = 3959 * c  # Earth radius in miles
        
        # Simple LINESTRING for straight line
        route_geometry = f"LINESTRING({pickup[1]} {pickup[0]}, {delivery[1]} {delivery[0]})"
        
        return {
            'distance_miles': round(distance_miles, 2),
            'duration_minutes': round(distance_miles * 2),  # Rough estimate: 30 mph average
            'duration_in_traffic_minutes': round(distance_miles * 2.5),  # With traffic
            'route_geometry': route_geometry,
            'encoded_polyline': None,
            'steps': [],
            'optimization_score': 50.0,  # Neutral score
            'traffic_considered': False
        }
    
    def _extract_turn_by_turn_directions(self, steps: List[Dict]) -> List[Dict]:
        """Extract simplified turn-by-turn directions"""
        directions = []
        for step in steps:
            instruction = step.get('html_instructions', '')
            # Handle HTML entities and tags safely
            if isinstance(instruction, str):
                instruction = instruction.replace('\\u003cb\\u003e', '').replace('\\u003c/b\\u003e', '')
                instruction = instruction.replace('<b>', '').replace('</b>', '')
            directions.append({
                'instruction': instruction,
                'distance': step['distance']['text'],
                'duration': step['duration']['text'],
                'maneuver': step.get('maneuver', 'straight')
            })
        return directions
    
    def _calculate_optimization_score(self, leg: Dict) -> float:
        """Calculate route optimization score based on efficiency metrics"""
        base_score = 70.0
        
        # Factor in traffic vs non-traffic duration
        normal_duration = leg['duration']['value']
        traffic_duration = leg.get('duration_in_traffic', {}).get('value', normal_duration)
        
        if traffic_duration > normal_duration:
            traffic_penalty = min(30.0, (traffic_duration - normal_duration) / normal_duration * 100)
            base_score -= traffic_penalty
        
        return round(max(10.0, min(100.0, base_score)), 2)
    
    async def _save_optimized_route(self, load_id: UUID, driver_id: Optional[UUID], vehicle_id: UUID, 
                                   route_data: Dict, load_result: Dict, load_repository) -> UUID:
        """Save optimized route to database"""
        
        insert_query = """
            INSERT INTO routes (
                load_id, driver_id, vehicle_id, origin_location, destination_location,
                route_geometry, planned_distance_miles, planned_duration_minutes,
                optimization_score, status
            ) VALUES (
                $1, $2, $3, 
                ST_GeogFromText('POINT(' || $4 || ' ' || $5 || ')'), 
                ST_GeogFromText('POINT(' || $6 || ' ' || $7 || ')'),
                ST_GeogFromText($8),
                $9, $10, $11, 'PLANNED'
            ) RETURNING id
        """
        
        result = await load_repository.execute_single(insert_query,
            str(load_id), str(driver_id) if driver_id else None, str(vehicle_id),
            str(load_result['pickup_longitude']), str(load_result['pickup_latitude']),  # pickup lng, lat
            str(load_result['delivery_longitude']), str(load_result['delivery_latitude']),  # delivery lng, lat
            route_data['route_geometry'],
            route_data['distance_miles'],
            route_data['duration_minutes'],
            route_data['optimization_score']
        )
        
        return result['id']  # asyncpg already returns UUID objects
    
    async def _publish_route_optimized_event(self, route_id: UUID, load_id: UUID, 
                                           driver_id: Optional[UUID], vehicle_id: UUID, route_data: Dict):
        """Publish ROUTE_OPTIMIZED event to Kafka"""
        if not self.kafka_producer:
            self.kafka_producer = await get_producer()
        
        event = RouteOptimizedEvent(
            source="route_optimization_service",
            data={
                'route_id': str(route_id),
                'load_ids': [str(load_id)],
                'vehicle_id': str(vehicle_id),
                'driver_id': str(driver_id) if driver_id else None,
                'original_distance': route_data.get('straight_line_distance', route_data['distance_miles']),
                'optimized_distance': route_data['distance_miles'],
                'time_saved': 0.0,  # Could be calculated if we had original time estimate
                'fuel_saved': 0.0,  # Could be calculated based on distance savings
                'algorithm_used': 'google_maps_api',
                'optimization_score': route_data['optimization_score'],
                'traffic_considered': route_data['traffic_considered'],
                'steps_count': len(route_data['steps']),
                'encoded_polyline': route_data.get('encoded_polyline')
            }
        )
        
        await self.kafka_producer.send_event(event)
        logger.info(f"Published ROUTE_OPTIMIZED event for route {route_id}")

# Global service instance
route_optimizer = RouteOptimizationService()
