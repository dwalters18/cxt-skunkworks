"""Shared dependencies and utilities for TMS API."""
import asyncio
import logging
from typing import Optional, Set
from fastapi import WebSocket
# Import repository classes from repositories module
from database.connections import get_db_manager as get_database_manager, DatabaseManager
from repositories import (
    LoadRepository,
    VehicleRepository,
    DriverRepository,
    AuditRepository,
    Neo4jRepository,
    TimescaleRepository
)
from kafka.producer import get_producer as get_kafka_producer
from kafka.consumer import get_consumer as get_kafka_consumer, TMSEventConsumer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
consumer_task: Optional[asyncio.Task] = None
websocket_connections: Set[WebSocket] = set()

# Repository factory functions for dependency injection
async def get_load_repo():
    """Get load repository instance"""
    db_manager = await get_database_manager()
    return LoadRepository(db_manager)


async def get_vehicle_repo():
    """Get vehicle repository instance"""
    db_manager = await get_database_manager()
    return VehicleRepository(db_manager)


async def get_audit_repo():
    """Get audit repository instance"""
    db_manager = await get_database_manager()
    return AuditRepository(db_manager)


async def get_neo4j_repo():
    """Get Neo4j repository instance"""
    db_manager = await get_database_manager()
    return Neo4jRepository(db_manager)


async def get_driver_repo():
    """Get driver repository instance"""
    db_manager = await get_database_manager()
    return DriverRepository(db_manager)


async def get_timescale_repo():
    """Get TimescaleDB repository instance"""
    db_manager = await get_database_manager()
    return TimescaleRepository(db_manager)
