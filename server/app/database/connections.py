"""Database connection utilities for TMS"""
import os
import asyncio
from typing import Optional, Dict, Any
import asyncpg
from neo4j import AsyncGraphDatabase
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages connections to all TMS databases"""
    
    def __init__(self):
        self.postgres_pool: Optional[asyncpg.Pool] = None
        self.timescale_pool: Optional[asyncpg.Pool] = None
        self.neo4j_driver: Optional[Any] = None
        
    async def initialize(self):
        """Initialize all database connections"""
        await self._init_postgres()
        await self._init_timescale()
        await self._init_neo4j()
        logger.info("All database connections initialized")
    
    async def _init_postgres(self):
        """Initialize PostgreSQL connection pool"""
        postgres_url = os.getenv("POSTGRES_URL", 
            "postgresql://tms_user:tms_password@localhost:5432/tms_oltp")
        
        max_retries = 5
        retry_delay = 2  # Initial delay in seconds
        
        for attempt in range(max_retries):
            try:
                self.postgres_pool = await asyncpg.create_pool(
                    postgres_url,
                    min_size=5,
                    max_size=20,
                    command_timeout=60,
                    server_settings={
                        'application_name': 'tms_api',
                    }
                )
                logger.info("PostgreSQL connection pool created")
                return
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Failed to connect to PostgreSQL (attempt {attempt + 1}/{max_retries}): {e}")
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Failed to initialize PostgreSQL after {max_retries} attempts: {e}")
                    raise
    
    async def _init_timescale(self):
        """Initialize TimescaleDB connection pool"""
        timescale_url = os.getenv("TIMESCALE_URL",
            "postgresql://timescale_user:timescale_password@localhost:5433/tms_timeseries")
        
        max_retries = 5
        retry_delay = 2  # Initial delay in seconds
        
        for attempt in range(max_retries):
            try:
                self.timescale_pool = await asyncpg.create_pool(
                    timescale_url,
                    min_size=3,
                    max_size=15,
                    command_timeout=60,
                    server_settings={
                        'application_name': 'tms_timeseries',
                    }
                )
                logger.info("TimescaleDB connection pool created")
                return
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Failed to connect to TimescaleDB (attempt {attempt + 1}/{max_retries}): {e}")
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Failed to initialize TimescaleDB after {max_retries} attempts: {e}")
                    raise
    
    async def _init_neo4j(self):
        """Initialize Neo4j connection"""
        neo4j_url = os.getenv("NEO4J_URL", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "tms_graph_password")
        
        max_retries = 5
        retry_delay = 2  # Initial delay in seconds
        
        for attempt in range(max_retries):
            try:
                self.neo4j_driver = AsyncGraphDatabase.driver(
                    neo4j_url,
                    auth=(neo4j_user, neo4j_password),
                    max_connection_lifetime=3600,
                    max_connection_pool_size=50,
                    connection_acquisition_timeout=60
                )
                
                # Verify connectivity
                await self.neo4j_driver.verify_connectivity()
                logger.info("Neo4j driver initialized")
                return
                
            except Exception as e:
                if attempt < max_retries - 1:  # Don't sleep on the last attempt
                    logger.warning(f"Failed to connect to Neo4j (attempt {attempt + 1}/{max_retries}): {e}")
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Failed to initialize Neo4j after {max_retries} attempts: {e}")
                    raise
    
    async def close(self):
        """Close all database connections"""
        if self.postgres_pool:
            await self.postgres_pool.close()
        if self.timescale_pool:
            await self.timescale_pool.close()
        if self.neo4j_driver:
            await self.neo4j_driver.close()
        logger.info("All database connections closed")
    
    def get_postgres_connection(self):
        """Get a PostgreSQL connection from the pool"""
        if not self.postgres_pool:
            raise RuntimeError("PostgreSQL pool not initialized")
        return self.postgres_pool.acquire()
    
    def get_timescale_connection(self):
        """Get a TimescaleDB connection from the pool"""
        if not self.timescale_pool:
            raise RuntimeError("TimescaleDB pool not initialized")
        return self.timescale_pool.acquire()
    
    async def get_neo4j_session(self):
        """Get a Neo4j session"""
        if not self.neo4j_driver:
            raise RuntimeError("Neo4j driver not initialized")
        return self.neo4j_driver.session()


# Repository Classes
class PostgresRepository:
    """Base repository for PostgreSQL operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def execute_query(self, query: str, *args):
        """Execute a query and return results"""
        async with self.db_manager.get_postgres_connection() as conn:
            return await conn.fetch(query, *args)
    
    async def execute_single(self, query: str, *args):
        """Execute a query and return single result"""
        async with self.db_manager.get_postgres_connection() as conn:
            return await conn.fetchrow(query, *args)
    
    async def execute_command(self, query: str, *args):
        """Execute a command (INSERT/UPDATE/DELETE)"""
        async with self.db_manager.get_postgres_connection() as conn:
            return await conn.execute(query, *args)


class LoadRepository(PostgresRepository):
    """Repository for load operations"""
    
    async def create_load(self, load_data: Dict[str, Any]) -> str:
        """Create a new load"""
        query = """
        INSERT INTO loads (load_number, pickup_address, delivery_address, 
                          pickup_datetime, delivery_datetime, weight, rate, status)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING id
        """
        result = await self.execute_single(
            query,
            load_data['load_number'],
            load_data['pickup_address'],
            load_data['delivery_address'],
            load_data['pickup_datetime'],
            load_data['delivery_datetime'],
            load_data.get('weight'),
            load_data.get('rate'),
            'pending'
        )
        return str(result['id'])
    
    async def get_load(self, load_id: str):
        """Get load by ID"""
        query = "SELECT * FROM loads WHERE id = $1"
        return await self.execute_single(query, load_id)
    
    async def update_load_status(self, load_id: str, status: str):
        """Update load status"""
        query = "UPDATE loads SET status = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2"
        await self.execute_command(query, status, load_id)
    
    async def assign_load(self, load_id: str, carrier_id: str, vehicle_id: str, driver_id: str):
        """Assign load to carrier/vehicle/driver"""
        query = """
        UPDATE loads 
        SET carrier_id = $1, vehicle_id = $2, driver_id = $3, 
            status = 'assigned', updated_at = CURRENT_TIMESTAMP 
        WHERE id = $4
        """
        await self.execute_command(query, carrier_id, vehicle_id, driver_id, load_id)
    
    async def search_loads(self, filters: Dict[str, Any], limit: int = 50, offset: int = 0):
        """Search loads with filters"""
        where_clauses = []
        params = []
        param_count = 0
        
        if filters.get('status'):
            param_count += 1
            where_clauses.append(f"status = ${param_count}")
            params.append(filters['status'])
        
        if filters.get('carrier_id'):
            param_count += 1
            where_clauses.append(f"carrier_id = ${param_count}")
            params.append(filters['carrier_id'])
        
        if filters.get('date_from'):
            param_count += 1
            where_clauses.append(f"pickup_datetime >= ${param_count}")
            params.append(filters['date_from'])
        
        if filters.get('date_to'):
            param_count += 1
            where_clauses.append(f"pickup_datetime <= ${param_count}")
            params.append(filters['date_to'])
        
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        param_count += 1
        limit_param = f"${param_count}"
        params.append(limit)
        
        param_count += 1
        offset_param = f"${param_count}"
        params.append(offset)
        
        query = f"""
        SELECT * FROM loads 
        {where_sql}
        ORDER BY created_at DESC 
        LIMIT {limit_param} OFFSET {offset_param}
        """
        
        return await self.execute_query(query, *params)


class VehicleRepository(PostgresRepository):
    """Repository for vehicle operations"""
    
    async def get_available_vehicles(self, carrier_id: Optional[str] = None):
        """Get available vehicles"""
        if carrier_id:
            query = "SELECT * FROM vehicles WHERE status = 'available' AND carrier_id = $1"
            return await self.execute_query(query, carrier_id)
        else:
            query = "SELECT * FROM vehicles WHERE status = 'available'"
            return await self.execute_query(query)
    
    async def update_vehicle_location(self, vehicle_id: str, latitude: float, longitude: float):
        """Update vehicle location"""
        query = """
        UPDATE vehicles 
        SET current_location = ST_GeogFromText($1), updated_at = CURRENT_TIMESTAMP 
        WHERE id = $2
        """
        point_wkt = f"POINT({longitude} {latitude})"
        await self.execute_command(query, point_wkt, vehicle_id)


class TimescaleRepository:
    """Repository for TimescaleDB operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def execute_query(self, query: str, *args):
        """Execute a query and return results"""
        async with self.db_manager.get_timescale_connection() as conn:
            return await conn.fetch(query, *args)
    
    async def execute_single(self, query: str, *args):
        """Execute a query and return single result"""
        async with self.db_manager.get_timescale_connection() as conn:
            return await conn.fetchrow(query, *args)
    
    async def execute_command(self, query: str, *args):
        """Execute a command (INSERT/UPDATE/DELETE)"""
        async with self.db_manager.get_timescale_connection() as conn:
            return await conn.execute(query, *args)
    
    async def insert_vehicle_tracking(self, tracking_data: Dict[str, Any]):
        """Insert vehicle tracking data"""
        async with self.db_manager.get_timescale_connection() as conn:
            query = """
            INSERT INTO vehicle_tracking 
            (time, vehicle_id, latitude, longitude, speed, heading, fuel_level, is_moving, driver_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """
            await conn.execute(
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
        async with self.db_manager.get_timescale_connection() as conn:
            query = """
            SELECT * FROM vehicle_tracking 
            WHERE vehicle_id = $1 AND time >= NOW() - INTERVAL '%s hours'
            ORDER BY time DESC
            """ % hours
            return await conn.fetch(query, vehicle_id)


class Neo4jRepository:
    """Repository for Neo4j graph operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def find_shortest_route(self, start_location_id: str, end_location_id: str):
        """Find shortest route between locations"""
        async with self.db_manager.get_neo4j_session() as session:
            query = """
            MATCH (start:Location {id: $start_id}), (end:Location {id: $end_id})
            CALL apoc.algo.dijkstra(start, end, 'ROUTE_SEGMENT', 'distance') 
            YIELD path, weight
            RETURN path, weight as total_distance
            """
            result = await session.run(query, start_id=start_location_id, end_id=end_location_id)
            return await result.single()
    
    async def find_nearby_carriers(self, location_id: str, service_type: str = None):
        """Find carriers serving a location"""
        async with self.db_manager.get_neo4j_session() as session:
            query = """
            MATCH (c:Carrier)-[s:SERVICES]->(l:Location {id: $location_id})
            """
            if service_type:
                query += " WHERE s.service_type = $service_type"
                result = await session.run(query, location_id=location_id, service_type=service_type)
            else:
                result = await session.run(query, location_id=location_id)
            
            records = []
            async for record in result:
                records.append(record)
            return records


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


async def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        await _db_manager.initialize()
    return _db_manager


async def get_load_repository() -> LoadRepository:
    """Get load repository instance"""
    db_manager = await get_db_manager()
    return LoadRepository(db_manager)


async def get_vehicle_repository() -> VehicleRepository:
    """Get vehicle repository instance"""
    db_manager = await get_db_manager()
    return VehicleRepository(db_manager)


async def get_timescale_repository() -> TimescaleRepository:
    """Get timescale repository instance"""
    db_manager = await get_db_manager()
    return TimescaleRepository(db_manager)


async def get_neo4j_repository() -> Neo4jRepository:
    """Get Neo4j repository instance"""
    db_manager = await get_db_manager()
    return Neo4jRepository(db_manager)
