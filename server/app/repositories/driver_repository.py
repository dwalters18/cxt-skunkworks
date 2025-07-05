"""Driver Repository for TMS API."""
import logging
from typing import List, Optional, Dict, Any
from decimal import Decimal

from .base import PostgresRepository

logger = logging.getLogger(__name__)


class DriverRepository(PostgresRepository):
    """Repository for driver-related database operations."""

    async def get_drivers(self, conditions: List[str] = None, params: List[Any] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get drivers with optional filtering."""
        conditions = conditions or []
        params = params or []
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        # Build parameter placeholders for asyncpg ($1, $2, etc.)
        param_offset = len(params)
        limit_placeholder = f"${param_offset + 1}"
        offset_placeholder = f"${param_offset + 2}"
        
        query = f"""
            SELECT 
                id, carrier_id, driver_number, first_name, last_name, email, phone,
                license_number, license_class, license_expiry, date_of_birth, hire_date,
                current_location, current_address, status, hours_of_service_remaining,
                last_hos_reset, created_at, updated_at
            FROM drivers 
            {where_clause}
            ORDER BY first_name, last_name
            LIMIT {limit_placeholder} OFFSET {offset_placeholder}
        """
        params.extend([limit, offset])
        
        logger.info(f"Executing query: {query}")
        logger.info(f"With parameters: {params}")
        
        return await self.execute_query(query, *params)

    async def count_drivers(self, conditions: List[str] = None, params: List[Any] = None) -> int:
        """Count drivers with optional filtering."""
        conditions = conditions or []
        params = params or []
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        query = f"SELECT COUNT(*) as total FROM drivers {where_clause}"
        result = await self.execute_single(query, *params)
        return result['total'] if result else 0

    async def get_driver_by_id(self, driver_id: str) -> Optional[Dict[str, Any]]:
        """Get driver by ID."""
        query = """
            SELECT 
                id, carrier_id, driver_number, first_name, last_name, email, phone,
                license_number, license_class, license_expiry, date_of_birth, hire_date,
                current_location, current_address, status, hours_of_service_remaining,
                last_hos_reset, created_at, updated_at
            FROM drivers 
            WHERE id = $1
        """
        return await self.execute_single(query, driver_id)

    async def create_driver(self, driver_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new driver."""
        query = """
            INSERT INTO drivers (
                carrier_id, driver_number, first_name, last_name, email, phone,
                license_number, license_class, license_expiry, date_of_birth, hire_date,
                current_location, current_address, status
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11,
                ST_SetSRID(ST_MakePoint($12, $13), 4326)::geography,
                $14, $15
            )
            RETURNING 
                id, carrier_id, driver_number, first_name, last_name, email, phone,
                license_number, license_class, license_expiry, date_of_birth, hire_date,
                current_location, current_address, status, hours_of_service_remaining,
                last_hos_reset, created_at, updated_at
        """
        
        # Extract parameters in the correct order for asyncpg
        params = [
            driver_data.get('carrier_id'),
            driver_data.get('driver_number'),
            driver_data.get('first_name'),
            driver_data.get('last_name'),
            driver_data.get('email'),
            driver_data.get('phone'),
            driver_data.get('license_number'),
            driver_data.get('license_class'),
            driver_data.get('license_expiry'),
            driver_data.get('date_of_birth'),
            driver_data.get('hire_date'),
            driver_data.get('longitude'),
            driver_data.get('latitude'),
            driver_data.get('current_address'),
            driver_data.get('status', 'AVAILABLE')
        ]
        
        return await self.execute_single(query, *params)

    async def update_driver_status(self, driver_id: str, status: str) -> Optional[Dict[str, Any]]:
        """Update driver status."""
        query = """
            UPDATE drivers 
            SET status = $1, updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
            RETURNING 
                id, carrier_id, driver_number, first_name, last_name, email, phone,
                license_number, license_class, license_expiry, date_of_birth, hire_date,
                current_location, current_address, status, hours_of_service_remaining,
                last_hos_reset, created_at, updated_at
        """
        return await self.execute_single(query, status, driver_id)

    async def update_driver_location(self, driver_id: str, latitude: float, longitude: float, address: str = None) -> Optional[Dict[str, Any]]:
        """Update driver location."""
        query = """
            UPDATE drivers 
            SET 
                current_location = ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography,
                current_address = COALESCE($3, current_address),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $4
            RETURNING 
                id, carrier_id, driver_number, first_name, last_name, email, phone,
                license_number, license_class, license_expiry, date_of_birth, hire_date,
                current_location, current_address, status, hours_of_service_remaining,
                last_hos_reset, created_at, updated_at
        """
        return await self.execute_single(query, longitude, latitude, address, driver_id)
