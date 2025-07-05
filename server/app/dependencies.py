"""Shared dependencies and utilities for TMS API."""
import asyncio
import logging
from typing import Optional, Set
from fastapi import WebSocket
from database.connections import (
    get_db_manager, get_load_repository, get_vehicle_repository,
    get_audit_repository, get_neo4j_repository, get_timescale_repository,
    DatabaseManager
)
from kafka.producer import get_producer
from kafka.consumer import get_consumer, TMSEventConsumer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
consumer_task: Optional[asyncio.Task] = None
websocket_connections: Set[WebSocket] = set()


async def get_database_manager() -> DatabaseManager:
    """Get database manager dependency."""
    return get_db_manager()


async def get_kafka_producer():
    """Get Kafka producer dependency."""
    return get_producer()


async def get_kafka_consumer():
    """Get Kafka consumer dependency."""
    return get_consumer()


async def get_load_repo():
    """Get load repository dependency."""
    return get_load_repository()


async def get_vehicle_repo():
    """Get vehicle repository dependency."""
    return get_vehicle_repository()


async def get_audit_repo():
    """Get audit repository dependency."""
    return get_audit_repository()


async def get_neo4j_repo():
    """Get Neo4j repository dependency."""
    return get_neo4j_repository()


async def get_timescale_repo():
    """Get TimescaleDB repository dependency."""
    return get_timescale_repository()
