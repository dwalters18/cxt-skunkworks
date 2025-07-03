"""Kafka Event Producer for TMS Events"""
import json
import asyncio
from typing import Any, Dict, Optional, Set
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError
from aiokafka.admin import AIOKafkaAdminClient, NewTopic
import logging
from datetime import datetime

from models.events import BaseEvent, EventType

logger = logging.getLogger(__name__)


class TMSEventProducer:
    """Async Kafka producer for TMS events"""
    
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer: Optional[AIOKafkaProducer] = None
        self._started = False
    
    def get_all_topics(self) -> Set[str]:
        """Get all unique topic names from the event type mapping"""
        topic_mapping = {
            # Load events
            EventType.LOAD_CREATED: "tms.loads",
            EventType.LOAD_ASSIGNED: "tms.loads",
            EventType.LOAD_PICKED_UP: "tms.loads",
            EventType.LOAD_IN_TRANSIT: "tms.loads",
            EventType.LOAD_DELIVERED: "tms.loads",
            EventType.LOAD_CANCELLED: "tms.loads",
            
            # Vehicle events
            EventType.VEHICLE_LOCATION_UPDATED: "tms.vehicles.tracking",
            EventType.VEHICLE_STATUS_CHANGED: "tms.vehicles",
            EventType.VEHICLE_MAINTENANCE_DUE: "tms.vehicles.maintenance",
            
            # Driver events
            EventType.DRIVER_STATUS_CHANGED: "tms.drivers",
            EventType.DRIVER_LOCATION_UPDATED: "tms.drivers.tracking",
            EventType.DRIVER_HOS_VIOLATION: "tms.drivers.compliance",
            
            # Route events
            EventType.ROUTE_OPTIMIZED: "tms.routes",
            EventType.ROUTE_DEVIATION: "tms.routes.alerts",
            EventType.ROUTE_COMPLETED: "tms.routes",
            
            # Carrier events
            EventType.CARRIER_PERFORMANCE_UPDATED: "tms.carriers",
            EventType.CARRIER_CAPACITY_CHANGED: "tms.carriers",
            
            # System events
            EventType.SYSTEM_ALERT: "tms.system.alerts",
            EventType.AI_PREDICTION: "tms.ai.predictions",
        }
        return set(topic_mapping.values())
    
    async def create_topics(self):
        """Create all required Kafka topics if they don't exist"""
        try:
            admin_client = AIOKafkaAdminClient(
                bootstrap_servers=self.bootstrap_servers
            )
            await admin_client.start()
            
            try:
                # Get existing topics
                metadata = await admin_client.describe_cluster()
                existing_topics = set()
                
                # List existing topics
                topic_metadata = await admin_client.list_topics()
                existing_topics = set(topic_metadata)
                
                # Get all required topics
                required_topics = self.get_all_topics()
                
                # Create missing topics
                topics_to_create = required_topics - existing_topics
                
                if topics_to_create:
                    logger.info(f"Creating {len(topics_to_create)} missing Kafka topics: {sorted(topics_to_create)}")
                    
                    new_topics = [
                        NewTopic(
                            name=topic_name,
                            num_partitions=3,
                            replication_factor=1
                        )
                        for topic_name in topics_to_create
                    ]
                    
                    await admin_client.create_topics(new_topics)
                    logger.info(f"Successfully created topics: {sorted(topics_to_create)}")
                else:
                    logger.info("All required Kafka topics already exist")
                    
            finally:
                await admin_client.close()
                
        except Exception as e:
            logger.error(f"Failed to create Kafka topics: {e}")
            # Don't raise - topics might be created by auto-creation
            logger.warning("Continuing with topic auto-creation enabled")
    
    async def start(self):
        """Start the Kafka producer"""
        if self._started:
            return
            
        try:
            # First, ensure all required topics exist
            await self.create_topics()
            
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                compression_type="gzip",
                acks='all',  # Wait for all replicas
                retry_backoff_ms=1000,
                request_timeout_ms=30000,
            )
            await self.producer.start()
            self._started = True
            logger.info("TMS Event Producer started successfully")
        except Exception as e:
            logger.error(f"Failed to start TMS Event Producer: {e}")
            raise
    
    async def stop(self):
        """Stop the Kafka producer"""
        if self.producer and self._started:
            await self.producer.stop()
            self._started = False
            logger.info("TMS Event Producer stopped")
    
    def get_topic_name(self, event_type: EventType) -> str:
        """Get topic name based on event type"""
        topic_mapping = {
            # Load events
            EventType.LOAD_CREATED: "tms.loads",
            EventType.LOAD_ASSIGNED: "tms.loads",
            EventType.LOAD_PICKED_UP: "tms.loads",
            EventType.LOAD_IN_TRANSIT: "tms.loads",
            EventType.LOAD_DELIVERED: "tms.loads",
            EventType.LOAD_CANCELLED: "tms.loads",
            
            # Vehicle events
            EventType.VEHICLE_LOCATION_UPDATED: "tms.vehicles.tracking",
            EventType.VEHICLE_STATUS_CHANGED: "tms.vehicles",
            EventType.VEHICLE_MAINTENANCE_DUE: "tms.vehicles.maintenance",
            
            # Driver events
            EventType.DRIVER_STATUS_CHANGED: "tms.drivers",
            EventType.DRIVER_LOCATION_UPDATED: "tms.drivers.tracking",
            EventType.DRIVER_HOS_VIOLATION: "tms.drivers.compliance",
            
            # Route events
            EventType.ROUTE_OPTIMIZED: "tms.routes",
            EventType.ROUTE_DEVIATION: "tms.routes.alerts",
            EventType.ROUTE_COMPLETED: "tms.routes",
            
            # Carrier events
            EventType.CARRIER_PERFORMANCE_UPDATED: "tms.carriers",
            EventType.CARRIER_CAPACITY_CHANGED: "tms.carriers",
            
            # System events
            EventType.SYSTEM_ALERT: "tms.system.alerts",
            EventType.AI_PREDICTION: "tms.ai.predictions",
        }
        return topic_mapping.get(event_type, "tms.events.default")
    
    async def send_event(self, event: BaseEvent, key: Optional[str] = None) -> bool:
        """Send an event to Kafka"""
        if not self._started or not self.producer:
            logger.error("Producer not started")
            return False
        
        try:
            topic = self.get_topic_name(event.event_type)
            event_dict = event.model_dump()
            
            # Use event_id as key if no key provided
            if key is None:
                key = event.event_id
            
            # Add headers with metadata
            headers = {
                'event_type': event.event_type.value.encode('utf-8'),
                'event_id': event.event_id.encode('utf-8'),
                'timestamp': event.timestamp.isoformat().encode('utf-8'),
                'source': event.source.encode('utf-8'),
                'version': event.version.encode('utf-8')
            }
            
            if event.correlation_id:
                headers['correlation_id'] = event.correlation_id.encode('utf-8')
            
            # Send the event
            future = await self.producer.send(
                topic=topic,
                value=event_dict,
                key=key,
                headers=list(headers.items())
            )
            
            record_metadata = await future
            logger.info(
                f"Event sent successfully: {event.event_type} to {topic} "
                f"(partition: {record_metadata.partition}, offset: {record_metadata.offset})"
            )
            return True
            
        except KafkaError as e:
            logger.error(f"Kafka error sending event {event.event_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending event {event.event_id}: {e}")
            return False
    
    async def send_bulk_events(self, events: list[BaseEvent]) -> Dict[str, bool]:
        """Send multiple events in bulk"""
        results = {}
        
        for event in events:
            success = await self.send_event(event)
            results[event.event_id] = success
        
        return results


# Global producer instance
_producer: Optional[TMSEventProducer] = None


async def get_producer() -> TMSEventProducer:
    """Get the global producer instance"""
    global _producer
    if _producer is None:
        import os
        bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        _producer = TMSEventProducer(bootstrap_servers)
        await _producer.start()
    return _producer


async def send_event(event: BaseEvent, key: Optional[str] = None) -> bool:
    """Convenience function to send an event"""
    producer = await get_producer()
    return await producer.send_event(event, key)


# Event generation helpers
async def emit_load_created(load_data: Dict[str, Any], source: str = "tms-api") -> bool:
    """Emit a load created event"""
    from models.events import LoadCreatedEvent
    
    event = LoadCreatedEvent(
        source=source,
        data=load_data
    )
    return await send_event(event, key=load_data.get('load_id'))


async def emit_vehicle_location_update(vehicle_data: Dict[str, Any], source: str = "tms-tracking") -> bool:
    """Emit a vehicle location update event"""
    from models.events import VehicleLocationEvent
    
    event = VehicleLocationEvent(
        source=source,
        data=vehicle_data
    )
    return await send_event(event, key=vehicle_data.get('vehicle_id'))


async def emit_load_status_change(load_data: Dict[str, Any], event_type: EventType, source: str = "tms-api") -> bool:
    """Emit a load status change event"""
    from models.events import LoadStatusEvent
    
    event = LoadStatusEvent(
        event_type=event_type,
        source=source,
        data=load_data
    )
    return await send_event(event, key=load_data.get('load_id'))
