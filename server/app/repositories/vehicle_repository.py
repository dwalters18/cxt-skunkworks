"""
Vehicle Repository for TMS API.
Handles all database operations related to vehicles.
"""

import logging
from typing import Optional
from .base import PostgresRepository

logger = logging.getLogger(__name__)


class VehicleRepository(PostgresRepository):
    """Repository for vehicle operations"""
    
    async def get_available_vehicles(self, carrier_id: Optional[str] = None):
        """Get available vehicles"""
        if carrier_id:
            query = """
            SELECT *,
                   ST_Y(current_location::geometry) as latitude,
                   ST_X(current_location::geometry) as longitude
            FROM vehicles 
            WHERE status = 'AVAILABLE' AND carrier_id = $1
            """
            results = await self.execute_query(query, carrier_id)
        else:
            query = """
            SELECT *,
                   ST_Y(current_location::geometry) as latitude,
                   ST_X(current_location::geometry) as longitude
            FROM vehicles 
            WHERE status = 'AVAILABLE'
            """
            results = await self.execute_query(query)
        
        # Debug: Log the first result to see what fields are available
        if results:
            logger.info(f"Vehicle record keys: {list(results[0].keys())}")
            logger.info(f"First vehicle: {dict(results[0])}")
        
        return results
    
    async def update_vehicle_location(self, vehicle_id: str, latitude: float, longitude: float):
        """Update vehicle location"""
        query = """
        UPDATE vehicles 
        SET current_location = ST_GeogFromText($1), updated_at = CURRENT_TIMESTAMP 
        WHERE id = $2
        """
        point_wkt = f"POINT({longitude} {latitude})"
        await self.execute_command(query, point_wkt, vehicle_id)
