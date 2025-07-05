"""
Base repository classes for TMS API.
Provides common database operation patterns.
"""

from database.connections import DatabaseManager


class BaseRepository:
    """Base repository for common database operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager


class PostgresRepository(BaseRepository):
    """Base repository for PostgreSQL operations"""
    
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


class TimescaleRepository(BaseRepository):
    """Base repository for TimescaleDB operations"""
    
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


class Neo4jRepository(BaseRepository):
    """Base repository for Neo4j operations"""
    
    async def execute_query(self, query: str, **params):
        """Execute a Cypher query and return results"""
        async with await self.db_manager.get_neo4j_session() as session:
            result = await session.run(query, **params)
            return await result.data()
    
    async def execute_single(self, query: str, **params):
        """Execute a Cypher query and return single result"""
        async with await self.db_manager.get_neo4j_session() as session:
            result = await session.run(query, **params)
            return await result.single()
    
    async def execute_command(self, query: str, **params):
        """Execute a Cypher command (CREATE/UPDATE/DELETE)"""
        async with await self.db_manager.get_neo4j_session() as session:
            result = await session.run(query, **params)
            await result.consume()
            return result.summary()
