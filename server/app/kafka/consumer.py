"""Kafka Event Consumer for TMS Events"""
import json
import asyncio
from typing import Any, Dict, List, Optional, Callable, Awaitable
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
import logging
from datetime import datetime

from models.events import BaseEvent, EventType, EVENT_TYPE_MAPPING

logger = logging.getLogger(__name__)

# Type alias for event handlers
EventHandler = Callable[[BaseEvent], Awaitable[None]]


class TMSEventConsumer:
    """Async Kafka consumer for TMS events"""
    
    def __init__(self, 
                 bootstrap_servers: str,
                 group_id: str,
                 topics: List[str] = None):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.topics = topics or self._get_default_topics()
        self.consumer: Optional[AIOKafkaConsumer] = None
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._running = False
    
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
    
    def unregister_handler(self, event_type: EventType, handler: EventHandler):
        """Unregister an event handler"""
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            if not self._handlers[event_type]:
                del self._handlers[event_type]
            logger.info(f"Unregistered handler for {event_type}")
    
    async def _parse_event(self, message) -> Optional[BaseEvent]:
        """Parse a Kafka message into a TMS event"""
        try:
            # Get event type from headers
            event_type_header = None
            if message.headers:
                for key, value in message.headers:
                    if key == 'event_type':
                        event_type_header = value.decode('utf-8')
                        break
            
            if not event_type_header:
                logger.warning("Message missing event_type header")
                return None
            
            # Map to EventType enum
            try:
                event_type = EventType(event_type_header)
            except ValueError:
                logger.warning(f"Unknown event type: {event_type_header}")
                return None
            
            # Get the appropriate event class
            event_class = EVENT_TYPE_MAPPING.get(event_type, BaseEvent)
            
            # Parse the message value
            event_data = message.value
            if not isinstance(event_data, dict):
                logger.warning("Message value is not a dictionary")
                return None
            
            # Create the event object
            event = event_class(**event_data)
            return event
            
        except Exception as e:
            logger.error(f"Failed to parse event from message: {e}")
            return None
    
    async def _handle_event(self, event: BaseEvent):
        """Handle an event by calling registered handlers"""
        handlers = self._handlers.get(event.event_type, [])
        
        if not handlers:
            logger.debug(f"No handlers registered for {event.event_type}")
            return
        
        # Execute all handlers for this event type
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Error in event handler for {event.event_type}: {e}")
    
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
                
                # Parse the event
                event = await self._parse_event(message)
                if event:
                    # Handle the event
                    await self._handle_event(event)
                
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


# Event Handlers
class TMSEventHandlers:
    """Collection of TMS event handlers"""
    
    @staticmethod
    async def handle_load_created(event: BaseEvent):
        """Handle load created events"""
        logger.info(f"Processing load created: {event.data}")
        
        # Here you would typically:
        # 1. Validate the load data
        # 2. Store in database
        # 3. Trigger load matching algorithms
        # 4. Send notifications
        
    @staticmethod
    async def handle_load_assigned(event: BaseEvent):
        """Handle load assignment events"""
        logger.info(f"Processing load assignment: {event.data}")
        
        # Here you would typically:
        # 1. Update load status in database
        # 2. Notify carrier/driver
        # 3. Create route optimization task
        # 4. Update capacity planning
    
    @staticmethod
    async def handle_vehicle_location_update(event: BaseEvent):
        """Handle vehicle location updates"""
        logger.debug(f"Processing vehicle location update: {event.data}")
        
        # Here you would typically:
        # 1. Store in TimescaleDB
        # 2. Check for route deviations
        # 3. Update ETAs
        # 4. Trigger geofence alerts
    
    @staticmethod
    async def handle_route_deviation(event: BaseEvent):
        """Handle route deviation alerts"""
        logger.warning(f"Route deviation detected: {event.data}")
        
        # Here you would typically:
        # 1. Alert dispatchers
        # 2. Recalculate routes
        # 3. Update customer notifications
        # 4. Log for analytics
    
    @staticmethod
    async def handle_ai_prediction(event: BaseEvent):
        """Handle AI predictions"""
        logger.info(f"AI prediction received: {event.data}")
        
        # Here you would typically:
        # 1. Store prediction results
        # 2. Trigger preventive actions
        # 3. Update dashboards
        # 4. Feed back to ML models


# Default consumer instance
_consumer: Optional[TMSEventConsumer] = None


async def get_consumer(group_id: str = "tms-api-group") -> TMSEventConsumer:
    """Get the global consumer instance"""
    global _consumer
    logger.info(f"=== KAFKA CONSUMER INITIALIZATION START ===")
    
    if _consumer is None:
        import os
        bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        logger.info(f"Consumer Config: bootstrap_servers={bootstrap_servers}, group_id={group_id}")
        
        logger.info("Creating TMSEventConsumer instance...")
        _consumer = TMSEventConsumer(bootstrap_servers, group_id)
        logger.info("TMSEventConsumer instance created successfully")
        
        # Register default handlers
        logger.info("Registering default event handlers...")
        handlers = TMSEventHandlers()
        logger.info("- Registering LOAD_CREATED handler")
        _consumer.register_handler(EventType.LOAD_CREATED, handlers.handle_load_created)
        logger.info("- Registering LOAD_ASSIGNED handler")
        _consumer.register_handler(EventType.LOAD_ASSIGNED, handlers.handle_load_assigned)
        logger.info("- Registering VEHICLE_LOCATION_UPDATED handler")
        _consumer.register_handler(EventType.VEHICLE_LOCATION_UPDATED, handlers.handle_vehicle_location_update)
        logger.info("- Registering ROUTE_DEVIATION handler")
        _consumer.register_handler(EventType.ROUTE_DEVIATION, handlers.handle_route_deviation)
        logger.info("- Registering AI_PREDICTION handler")
        _consumer.register_handler(EventType.AI_PREDICTION, handlers.handle_ai_prediction)
        logger.info("All event handlers registered successfully")
        
    else:
        logger.info("Using existing consumer instance")
    
    logger.info(f"=== KAFKA CONSUMER INITIALIZATION COMPLETE ===")
    return _consumer
