"""
TimescaleDB Repository for TMS API.
Handles all database operations related to time-series data.
"""

from typing import Dict, Any
from .base import TimescaleRepository as BaseTimescaleRepository


class TimescaleRepository(BaseTimescaleRepository):
    """Repository for TimescaleDB operations"""
    
    async def insert_vehicle_tracking(self, tracking_data: Dict[str, Any]):
        """Insert vehicle tracking data"""
        query = """
        INSERT INTO vehicle_tracking 
        (time, vehicle_id, latitude, longitude, speed, heading, fuel_level, is_moving, driver_id)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """
        await self.execute_command(
            query,
            tracking_data['timestamp'],
            tracking_data['vehicle_id'],
            tracking_data['latitude'],
            tracking_data['longitude'],
            tracking_data.get('speed'),
            tracking_data.get('heading'),
            tracking_data.get('fuel_level'),
            tracking_data.get('is_moving', False),
            tracking_data.get('driver_id')
        )
    
    async def get_vehicle_tracking_history(self, vehicle_id: str, hours: int = 24):
        """Get vehicle tracking history"""
        query = """
        SELECT * FROM vehicle_tracking 
        WHERE vehicle_id = $1 AND time >= NOW() - INTERVAL '$2 hours'
        ORDER BY time DESC
        """
        return await self.execute_query(query, vehicle_id, hours)
