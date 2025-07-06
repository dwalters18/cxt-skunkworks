"""
Load Repository for TMS API.
Handles all database operations related to loads.
"""

from typing import Dict, Any, Union
from .base import PostgresRepository


class LoadRepository(PostgresRepository):
    """Repository for load operations"""
    
    async def create_load(self, load_request) -> dict:
        """Create a new load from CreateLoadRequest model"""
        # Handle both dict and Pydantic model input
        if hasattr(load_request, 'model_dump'):
            # It's a Pydantic model
            load_data = load_request.model_dump()
        else:
            # It's already a dict
            load_data = load_request
            
        query = """
        INSERT INTO loads (
            load_number, customer_id, pickup_location, delivery_location,
            pickup_address, delivery_address, pickup_date, delivery_date, 
            weight, volume, commodity_type, special_requirements, rate, status
        )
        VALUES (
            $1, $2, ST_GeogFromText($3), ST_GeogFromText($4),
            $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
        )
        RETURNING id, load_number, customer_id, pickup_address, delivery_address,
                  pickup_date, delivery_date, weight, volume, commodity_type, 
                  special_requirements, rate, status, created_at, updated_at,
                  ST_Y(pickup_location::geometry) as pickup_latitude,
                  ST_X(pickup_location::geometry) as pickup_longitude,
                  ST_Y(delivery_location::geometry) as delivery_latitude,
                  ST_X(delivery_location::geometry) as delivery_longitude
        """
        
        # Prepare location WKT strings
        pickup_wkt = f"POINT({load_data['pickup_location']['longitude']} {load_data['pickup_location']['latitude']})"
        delivery_wkt = f"POINT({load_data['delivery_location']['longitude']} {load_data['delivery_location']['latitude']})"
        
        # Handle special_requirements as PostgreSQL array
        special_req = load_data.get('special_requirements')
        # PostgreSQL expects a Python list, not a JSON string
        if not isinstance(special_req, list):
            special_req = None
        
        result = await self.execute_single(
            query,
            load_data['load_number'],
            load_data['customer_id'],
            pickup_wkt,
            delivery_wkt,
            load_data['pickup_address'],
            load_data['delivery_address'],
            load_data['pickup_date'],
            load_data['delivery_date'],
            load_data.get('weight'),
            load_data.get('volume'),
            load_data.get('commodity_type'),
            special_req,
            load_data.get('rate'),
            'CREATED'  # Use proper enum status
        )
        return dict(result)
    
    async def get_load(self, load_id: str):
        """Get load by ID"""
        query = """
        SELECT *,
               ST_Y(pickup_location::geometry) as pickup_latitude,
               ST_X(pickup_location::geometry) as pickup_longitude,
               ST_Y(delivery_location::geometry) as delivery_latitude,
               ST_X(delivery_location::geometry) as delivery_longitude
        FROM loads 
        WHERE id = $1
        """
        return await self.execute_single(query, load_id)
    
    async def update_load_status(self, load_id: str, status: str):
        """Update load status"""
        query = "UPDATE loads SET status = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2"
        await self.execute_command(query, status, load_id)
    
    async def assign_load(self, load_id: str, vehicle_id: str, driver_id: str):
        """Assign load to vehicle/driver"""
        query = """
        UPDATE loads 
        SET assigned_vehicle_id = $1, assigned_driver_id = $2, 
            status = 'ASSIGNED', updated_at = CURRENT_TIMESTAMP 
        WHERE id = $3
        """
        await self.execute_command(query, vehicle_id, driver_id, load_id)
    
    async def search_loads(self, filters: Dict[str, Any], limit: int = 50, offset: int = 0):
        """Search loads with various filters"""
        where_clauses = []
        params = []
        param_count = 0
        
        if filters.get('status'):
            param_count += 1
            where_clauses.append(f"status = ${param_count}")
            params.append(filters['status'])
        
        if filters.get('date_from'):
            param_count += 1
            where_clauses.append(f"pickup_date >= ${param_count}")
            params.append(filters['date_from'])
        
        if filters.get('date_to'):
            param_count += 1
            where_clauses.append(f"pickup_date <= ${param_count}")
            params.append(filters['date_to'])
        
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # Add limit and offset parameters
        param_count += 1
        params.append(limit)
        param_count += 1 
        params.append(offset)
        
        query = f"""
        SELECT *,
               ST_Y(pickup_location::geometry) as pickup_latitude,
               ST_X(pickup_location::geometry) as pickup_longitude,
               ST_Y(delivery_location::geometry) as delivery_latitude,
               ST_X(delivery_location::geometry) as delivery_longitude
        FROM loads 
        {where_sql}
        ORDER BY created_at DESC 
        LIMIT ${param_count-1} OFFSET ${param_count}
        """
        
        return await self.execute_query(query, *params)
    
    async def count_loads(self, filters: Dict[str, Any]) -> int:
        """Count loads matching the given filters"""
        where_conditions = []
        params = []
        param_counter = 1
        
        for key, value in filters.items():
            if key == 'status':
                where_conditions.append(f"status = ${param_counter}")
                params.append(value)
                param_counter += 1
        
        where_sql = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        query = f"""
        SELECT COUNT(*) as count
        FROM loads 
        {where_sql}
        """
        
        result = await self.execute_single(query, *params)
        return result['count'] if result else 0
