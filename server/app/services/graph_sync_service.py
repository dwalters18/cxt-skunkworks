"""
Neo4j Graph Synchronization Service
Handles event-driven population of Neo4j graph from Kafka events
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from models.events import BaseEvent, EventType
from repositories.neo4j_repository import Neo4jRepository
from database.connections import DatabaseManager

logger = logging.getLogger(__name__)


class GraphSyncService:
    """Service for synchronizing PostgreSQL data to Neo4j graph based on Kafka events"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.neo4j_repo = Neo4jRepository(db_manager)
    
    async def handle_event(self, event: BaseEvent) -> None:
        """Route events to appropriate graph update handlers"""
        try:
            event_handlers = {
                # Load Events
                EventType.LOAD_CREATED: self._handle_load_created,
                EventType.LOAD_ASSIGNED: self._handle_load_assigned,
                EventType.LOAD_DELIVERED: self._handle_load_delivered,
                EventType.LOAD_CANCELLED: self._handle_load_cancelled,
                
                # Vehicle Events  
                EventType.VEHICLE_LOCATION_UPDATED: self._handle_vehicle_location_updated,
                EventType.VEHICLE_ASSIGNED: self._handle_vehicle_assigned,
                EventType.VEHICLE_STATUS_CHANGED: self._handle_vehicle_status_changed,
                
                # Driver Events
                EventType.DRIVER_STATUS_CHANGED: self._handle_driver_status_changed,
                EventType.DRIVER_ASSIGNED: self._handle_driver_assigned,
                EventType.DRIVER_LOCATION_UPDATED: self._handle_driver_location_updated,
                
                # Route Events
                EventType.ROUTE_OPTIMIZED: self._handle_route_optimized,
                EventType.ROUTE_COMPLETED: self._handle_route_completed,
            }
            
            handler = event_handlers.get(event.event_type)
            if handler:
                await handler(event)
                logger.info(f"Successfully processed {event.event_type} event for Neo4j graph sync")
            else:
                logger.debug(f"No graph sync handler for event type: {event.event_type}")
                
        except Exception as e:
            logger.error(f"Error processing event {event.event_type} for graph sync: {e}")
    
    async def _handle_load_created(self, event: BaseEvent) -> None:
        """Create Load node and relationships when load is created"""
        data = event.data
        load_id = data.get('id') or data.get('load_id')
        
        if not load_id:
            logger.warning("Load created event missing load ID")
            return
            
        # Create Load node
        await self.neo4j_repo.create_load_node(
            load_id=str(load_id),
            customer_id=data.get('customer_id'),
            pickup_location=data.get('pickup_location'),
            delivery_location=data.get('delivery_location'),
            weight=data.get('weight'),
            status=data.get('status', 'PENDING'),
            created_at=event.timestamp
        )
        
        # Create relationships to Customer and Locations if available
        if data.get('customer_id'):
            await self.neo4j_repo.create_customer_load_relationship(
                customer_id=str(data.get('customer_id')),
                load_id=str(load_id)
            )
    
    async def _handle_load_assigned(self, event: BaseEvent) -> None:
        """Create assignment relationships when load is assigned"""
        data = event.data
        load_id = data.get('load_id')
        driver_id = data.get('driver_id')
        vehicle_id = data.get('vehicle_id')
        
        if not load_id:
            logger.warning("Load assigned event missing load ID")
            return
            
        # Create Driver node if not exists and create ASSIGNED_TO relationship
        if driver_id:
            await self.neo4j_repo.create_driver_node_if_not_exists(str(driver_id))
            await self.neo4j_repo.create_driver_load_assignment(
                driver_id=str(driver_id),
                load_id=str(load_id),
                assigned_at=event.timestamp
            )
        
        # Create Vehicle node if not exists and create TRANSPORTS relationship
        if vehicle_id:
            await self.neo4j_repo.create_vehicle_node_if_not_exists(str(vehicle_id))
            await self.neo4j_repo.create_vehicle_load_assignment(
                vehicle_id=str(vehicle_id),
                load_id=str(load_id),
                assigned_at=event.timestamp
            )
    
    async def _handle_load_delivered(self, event: BaseEvent) -> None:
        """Update load status and create delivery relationships"""
        data = event.data
        load_id = data.get('load_id')
        
        if load_id:
            await self.neo4j_repo.update_load_status(
                load_id=str(load_id),
                status='DELIVERED',
                delivered_at=event.timestamp
            )
    
    async def _handle_load_cancelled(self, event: BaseEvent) -> None:
        """Update load status and remove active assignments"""
        data = event.data
        load_id = data.get('load_id')
        
        if load_id:
            await self.neo4j_repo.update_load_status(
                load_id=str(load_id),
                status='CANCELLED',
                cancelled_at=event.timestamp
            )
            # Remove active assignment relationships
            await self.neo4j_repo.remove_load_assignments(str(load_id))
    
    async def _handle_vehicle_location_updated(self, event: BaseEvent) -> None:
        """Update vehicle location in graph"""
        data = event.data
        vehicle_id = data.get('vehicle_id')
        location = event.location
        
        if vehicle_id and location:
            await self.neo4j_repo.update_vehicle_location(
                vehicle_id=str(vehicle_id),
                latitude=location.latitude,
                longitude=location.longitude,
                updated_at=event.timestamp
            )
    
    async def _handle_vehicle_assigned(self, event: BaseEvent) -> None:
        """Handle vehicle assignment to carrier/driver"""
        data = event.data
        vehicle_id = data.get('vehicle_id')
        carrier_id = data.get('carrier_id')
        driver_id = data.get('driver_id')
        
        if vehicle_id:
            await self.neo4j_repo.create_vehicle_node_if_not_exists(str(vehicle_id))
            
            if carrier_id:
                await self.neo4j_repo.create_vehicle_carrier_relationship(
                    vehicle_id=str(vehicle_id),
                    carrier_id=str(carrier_id)
                )
            
            if driver_id:
                await self.neo4j_repo.create_driver_node_if_not_exists(str(driver_id))
                await self.neo4j_repo.create_driver_vehicle_relationship(
                    driver_id=str(driver_id),
                    vehicle_id=str(vehicle_id),
                    assigned_at=event.timestamp
                )
    
    async def _handle_vehicle_status_changed(self, event: BaseEvent) -> None:
        """Update vehicle status in graph"""
        data = event.data
        vehicle_id = data.get('vehicle_id')
        status = data.get('status')
        
        if vehicle_id and status:
            await self.neo4j_repo.update_vehicle_status(
                vehicle_id=str(vehicle_id),
                status=status,
                updated_at=event.timestamp
            )
    
    async def _handle_driver_status_changed(self, event: BaseEvent) -> None:
        """Update driver status in graph"""
        data = event.data
        driver_id = data.get('driver_id')
        status = data.get('status')
        
        if driver_id and status:
            await self.neo4j_repo.create_driver_node_if_not_exists(str(driver_id))
            await self.neo4j_repo.update_driver_status(
                driver_id=str(driver_id),
                status=status,
                updated_at=event.timestamp
            )
    
    async def _handle_driver_assigned(self, event: BaseEvent) -> None:
        """Handle driver assignment events"""
        data = event.data
        driver_id = data.get('driver_id')
        load_id = data.get('load_id')
        vehicle_id = data.get('vehicle_id')
        
        if driver_id:
            await self.neo4j_repo.create_driver_node_if_not_exists(str(driver_id))
            
            if load_id:
                await self.neo4j_repo.create_driver_load_assignment(
                    driver_id=str(driver_id),
                    load_id=str(load_id),
                    assigned_at=event.timestamp
                )
            
            if vehicle_id:
                await self.neo4j_repo.create_driver_vehicle_relationship(
                    driver_id=str(driver_id),
                    vehicle_id=str(vehicle_id),
                    assigned_at=event.timestamp
                )
    
    async def _handle_driver_location_updated(self, event: BaseEvent) -> None:
        """Update driver location in graph"""
        data = event.data
        driver_id = data.get('driver_id')
        location = event.location
        
        if driver_id and location:
            await self.neo4j_repo.create_driver_node_if_not_exists(str(driver_id))
            await self.neo4j_repo.update_driver_location(
                driver_id=str(driver_id),
                latitude=location.latitude,
                longitude=location.longitude,
                updated_at=event.timestamp
            )
    
    async def _handle_route_optimized(self, event: BaseEvent) -> None:
        """Create route relationships when route is optimized"""
        data = event.data
        route_id = data.get('route_id')
        load_id = data.get('load_id')
        driver_id = data.get('driver_id')
        vehicle_id = data.get('vehicle_id')
        
        if route_id:
            await self.neo4j_repo.create_route_node(
                route_id=str(route_id),
                load_id=str(load_id) if load_id else None,
                distance=data.get('distance'),
                duration=data.get('duration'),
                optimized_at=event.timestamp
            )
            
            # Create relationships to involved entities
            if load_id:
                await self.neo4j_repo.create_route_load_relationship(
                    route_id=str(route_id),
                    load_id=str(load_id)
                )
            
            if driver_id:
                await self.neo4j_repo.create_route_driver_relationship(
                    route_id=str(route_id),
                    driver_id=str(driver_id)
                )
            
            if vehicle_id:
                await self.neo4j_repo.create_route_vehicle_relationship(
                    route_id=str(route_id),
                    vehicle_id=str(vehicle_id)
                )
    
    async def _handle_route_completed(self, event: BaseEvent) -> None:
        """Update route status when completed"""
        data = event.data
        route_id = data.get('route_id')
        
        if route_id:
            await self.neo4j_repo.update_route_status(
                route_id=str(route_id),
                status='COMPLETED',
                completed_at=event.timestamp
            )
