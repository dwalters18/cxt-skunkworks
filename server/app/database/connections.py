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





# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


async def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        await _db_manager.initialize()
    return _db_manager


