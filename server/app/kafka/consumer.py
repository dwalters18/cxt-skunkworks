"""Kafka Event Consumer for TMS Events"""
import json
import asyncio
from typing import Any, Dict, List, Optional, Callable, Awaitable
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
import logging
from datetime import datetime

from models.events import BaseEvent, EventType, EVENT_TYPE_MAPPING
from services.graph_sync_service import GraphSyncService
from database.connections import DatabaseManager

logger = logging.getLogger(__name__)

# Type alias for event handlers
EventHandler = Callable[[BaseEvent], Awaitable[None]]


class TMSEventConsumer:
    """Async Kafka consumer for TMS events"""
    
    def __init__(self, 
                 bootstrap_servers: str,
                 group_id: str,
                 topics: List[str] = None,
                 db_manager: Optional[DatabaseManager] = None):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.topics = topics or self._get_default_topics()
        self.consumer: Optional[AIOKafkaConsumer] = None
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._running = False
        
        # Initialize graph sync service if database manager is provided
        self.graph_sync_service = None
        if db_manager:
            self.graph_sync_service = GraphSyncService(db_manager)
            logger.info("Graph sync service initialized for Neo4j event-driven updates")
    
    def _get_default_topics(self) -> List[str]:
        """Get default topics to subscribe to"""
        return [
            "tms.loads",
            "tms.vehicles",
            "tms.vehicles.tracking",
            "tms.drivers",
            "tms.drivers.tracking",
            "tms.routes",
            "tms.routes.alerts",
            "tms.carriers",
            "tms.system.alerts",
            "tms.ai.predictions"
        ]
    
    async def start(self):
        """Start the Kafka consumer"""
        logger.info("=== TMSEventConsumer.start() BEGIN ===")
        
        if self._running:
            logger.info("Consumer already running, skipping start")
            return
        
        try:
            logger.info(f"Creating AIOKafkaConsumer with:")
            logger.info(f"  - bootstrap_servers: {self.bootstrap_servers}")
            logger.info(f"  - group_id: {self.group_id}")
            logger.info(f"  - topics: {self.topics}")
            
            self.consumer = AIOKafkaConsumer(
                *self.topics,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                auto_commit_interval_ms=1000,
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000,
            )
            logger.info("AIOKafkaConsumer instance created successfully")
            
            logger.info("Attempting to connect to Kafka (this may take a moment)...")
            await self.consumer.start()
            logger.info("Successfully connected to Kafka broker!")
            
            self._running = True
            logger.info(f"=== TMS Event Consumer FULLY STARTED for topics: {self.topics} ===")
            
        except Exception as e:
            logger.error(f"ERROR: Failed to start TMS Event Consumer: {e}")
            logger.exception("Full exception details:")
            raise
    
    async def stop(self):
        """Stop the Kafka consumer"""
        if self.consumer and self._running:
            self._running = False
            await self.consumer.stop()
            logger.info("TMS Event Consumer stopped")
    
    def register_handler(self, event_type: EventType, handler: EventHandler):
        """Register an event handler for a specific event type"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.info(f"Registered handler for {event_type}")
    
    async def _process_message(self, message):
        """Process a single Kafka message"""
        try:
            # Parse message
            message_data = json.loads(message.value.decode('utf-8'))
            event_type = EventType(message_data.get('event_type'))
            
            # Create event object
            event_class = EVENT_TYPE_MAPPING.get(event_type, BaseEvent)
            event = event_class(**message_data)
            
            logger.debug(f"Processing {event_type} event: {event.event_id}")
            
            # Process with registered handlers
            handlers = self._handlers.get(event_type, [])
            for handler in handlers:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Handler error for {event_type}: {e}")
            
            # **NEW: Process with graph sync service if available**
            if self.graph_sync_service:
                try:
                    await self.graph_sync_service.handle_event(event)
                except Exception as e:
                    logger.error(f"Graph sync error for {event_type}: {e}")
            
            logger.debug(f"Successfully processed {event_type} event")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            logger.error(f"Message content: {message.value}")
    
    async def consume_events(self):
        """Main event consumption loop"""
        if not self._running or not self.consumer:
            logger.error("Consumer not started")
            return
        
        logger.info("Starting event consumption loop")
        
        try:
            async for message in self.consumer:
                if not self._running:
                    break
                
                logger.debug(
                    f"Received message from {message.topic}:{message.partition} "
                    f"at offset {message.offset}"
                )
                
                # Process the message
                await self._process_message(message)
                
        except Exception as e:
            logger.error(f"Error in event consumption loop: {e}")
            raise
    
    async def run(self):
        """Start consuming events (blocking)"""
        await self.start()
        try:
            await self.consume_events()
        finally:
            await self.stop()


class TMSEventHandlers:
    """Collection of TMS event handlers"""
    
    @staticmethod
    async def handle_load_created(event: BaseEvent):
        """Handle load created events"""
        logger.info(f"Load created: {event.data.get('id', 'unknown')}")
        # Additional business logic can be added here
    
    @staticmethod
    async def handle_load_assigned(event: BaseEvent):
        """Handle load assignment events"""
        logger.info(f"Load assigned: {event.data.get('load_id', 'unknown')} to driver {event.data.get('driver_id', 'unknown')}")
        # Additional business logic can be added here
    
    @staticmethod 
    async def handle_vehicle_location_update(event: BaseEvent):
        """Handle vehicle location updates"""
        vehicle_id = event.data.get('vehicle_id', 'unknown')
        location = event.location
        if location:
            logger.debug(f"Vehicle {vehicle_id} location updated: {location.latitude}, {location.longitude}")
        # Additional business logic can be added here
    
    @staticmethod
    async def handle_route_deviation(event: BaseEvent):
        """Handle route deviation alerts"""
        logger.warning(f"Route deviation detected: {event.data}")
        # Additional alerting logic can be added here
    
    @staticmethod
    async def handle_ai_prediction(event: BaseEvent):
        """Handle AI predictions"""
        prediction_type = event.data.get('prediction_type', 'unknown')
        logger.info(f"AI Prediction received: {prediction_type}")
        # Additional AI processing logic can be added here


# Default consumer instance
_consumer: Optional[TMSEventConsumer] = None

async def get_consumer(group_id: str = "tms-api-group", 
                      db_manager: Optional[DatabaseManager] = None) -> TMSEventConsumer:
    """Get the global consumer instance with graph sync capabilities"""
    global _consumer
    
    if _consumer is None:
        import os
        bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        _consumer = TMSEventConsumer(
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            db_manager=db_manager  # Enable graph sync if db_manager provided
        )
        
        # Register default event handlers
        handlers = TMSEventHandlers()
        _consumer.register_handler(EventType.LOAD_CREATED, handlers.handle_load_created)
        _consumer.register_handler(EventType.LOAD_ASSIGNED, handlers.handle_load_assigned)
        _consumer.register_handler(EventType.VEHICLE_LOCATION_UPDATED, handlers.handle_vehicle_location_update)
        _consumer.register_handler(EventType.ROUTE_DEVIATION, handlers.handle_route_deviation)
        _consumer.register_handler(EventType.AI_PREDICTION, handlers.handle_ai_prediction)
        
        logger.info("TMSEventConsumer initialized with graph sync capabilities")
    
    return _consumer
