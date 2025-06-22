"""TMS Event Consumer Service with Business Logic"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from models.events import EventType, BaseEvent
from database.connections import (
    get_load_repository, get_vehicle_repository, 
    get_timescale_repository, get_neo4j_repository
)
from kafka.consumer import TMSEventConsumer, get_consumer

logger = logging.getLogger(__name__)


class TMSEventProcessorService:
    """Processes TMS events and implements business logic"""
    
    def __init__(self):
        self.consumer = None
        self.running = False
        
        # Statistics tracking
        self.events_processed = 0
        self.events_by_type = {}
        self.last_activity = datetime.utcnow()
    
    async def start(self):
        """Start the event consumer service"""
        self.consumer = await get_consumer("tms-processor-group")
        
        # Register event handlers
        await self._register_handlers()
        
        # Start consumer
        await self.consumer.start()
        self.running = True
        
        logger.info("TMS Event Processor Service started")
        
        # Start processing events
        await self.consumer.consume_events()
    
    async def stop(self):
        """Stop the event consumer service"""
        self.running = False
        if self.consumer:
            await self.consumer.stop()
        logger.info("TMS Event Processor Service stopped")
    
    async def _register_handlers(self):
        """Register business logic event handlers"""
        # Load event handlers
        await self.consumer.register_handler(EventType.LOAD_CREATED, self._handle_load_created)
        await self.consumer.register_handler(EventType.LOAD_ASSIGNED, self._handle_load_assigned)
        await self.consumer.register_handler(EventType.LOAD_PICKED_UP, self._handle_load_picked_up)
        await self.consumer.register_handler(EventType.LOAD_IN_TRANSIT, self._handle_load_in_transit)
        await self.consumer.register_handler(EventType.LOAD_DELIVERED, self._handle_load_delivered)
        await self.consumer.register_handler(EventType.LOAD_CANCELLED, self._handle_load_cancelled)
        
        # Vehicle event handlers
        await self.consumer.register_handler(EventType.VEHICLE_LOCATION_UPDATE, self._handle_vehicle_location_update)
        await self.consumer.register_handler(EventType.VEHICLE_STATUS_CHANGE, self._handle_vehicle_status_change)
        
        # Driver event handlers
        await self.consumer.register_handler(EventType.DRIVER_STATUS_CHANGE, self._handle_driver_status_change)
        await self.consumer.register_handler(EventType.DRIVER_ASSIGNED, self._handle_driver_assigned)
        
        # Route event handlers
        await self.consumer.register_handler(EventType.ROUTE_OPTIMIZED, self._handle_route_optimized)
        await self.consumer.register_handler(EventType.ROUTE_DEVIATION, self._handle_route_deviation)
        
        # AI event handlers
        await self.consumer.register_handler(EventType.AI_PREDICTION, self._handle_ai_prediction)
        
        logger.info("Event handlers registered")
    
    def _track_event(self, event_type: EventType):
        """Track event processing statistics"""
        self.events_processed += 1
        self.events_by_type[event_type.value] = self.events_by_type.get(event_type.value, 0) + 1
        self.last_activity = datetime.utcnow()
    
    # Load Event Handlers
    async def _handle_load_created(self, event: BaseEvent):
        """Handle load creation - send notifications, validate data"""
        try:
            self._track_event(EventType.LOAD_CREATED)
            load_data = event.data
            
            logger.info(f"Processing load created: {load_data.get('load_id')}")
            
            # Business logic for load creation
            load_id = load_data.get('load_id')
            if not load_id:
                logger.warning("Load created event missing load_id")
                return
            
            # Example: Auto-assign high-priority loads
            weight = load_data.get('weight', 0)
            if weight > 40000:  # Heavy loads get priority
                logger.info(f"High-priority load detected: {load_id} ({weight} lbs)")
                # Could trigger automatic carrier matching here
                
            # Example: Validate pickup/delivery locations
            pickup_addr = load_data.get('pickup_address')
            delivery_addr = load_data.get('delivery_address')
            if pickup_addr and delivery_addr:
                # Could integrate with geocoding service for validation
                logger.info(f"Load route: {pickup_addr} -> {delivery_addr}")
            
            # Store event for analytics
            await self._store_event_analytics(event)
            
        except Exception as e:
            logger.error(f"Error handling load created event: {e}")
    
    async def _handle_load_assigned(self, event: BaseEvent):
        """Handle load assignment - update capacity, notify stakeholders"""
        try:
            self._track_event(EventType.LOAD_ASSIGNED)
            assignment_data = event.data
            
            load_id = assignment_data.get('load_id')
            carrier_id = assignment_data.get('carrier_id')
            vehicle_id = assignment_data.get('vehicle_id')
            driver_id = assignment_data.get('driver_id')
            
            logger.info(f"Processing load assignment: {load_id} -> Carrier: {carrier_id}, Vehicle: {vehicle_id}, Driver: {driver_id}")
            
            # Update vehicle status to 'assigned'
            if vehicle_id:
                vehicle_repo = await get_vehicle_repository()
                try:
                    await vehicle_repo.execute_command(
                        "UPDATE vehicles SET status = 'assigned', updated_at = CURRENT_TIMESTAMP WHERE id = $1",
                        vehicle_id
                    )
                    logger.info(f"Vehicle {vehicle_id} status updated to assigned")
                except Exception as e:
                    logger.error(f"Failed to update vehicle status: {e}")
            
            # Update driver status
            if driver_id:
                try:
                    # Using vehicle_repo connection for now (could create driver_repo)
                    await vehicle_repo.execute_command(
                        "UPDATE drivers SET status = 'assigned', current_load_id = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2",
                        load_id, driver_id
                    )
                    logger.info(f"Driver {driver_id} assigned to load {load_id}")
                except Exception as e:
                    logger.error(f"Failed to update driver status: {e}")
            
            # Store event for analytics
            await self._store_event_analytics(event)
            
        except Exception as e:
            logger.error(f"Error handling load assigned event: {e}")
    
    async def _handle_load_picked_up(self, event: BaseEvent):
        """Handle load pickup - start tracking, update ETA"""
        try:
            self._track_event(EventType.LOAD_PICKED_UP)
            pickup_data = event.data
            
            load_id = pickup_data.get('load_id')
            logger.info(f"Processing load pickup: {load_id}")
            
            # Update load status and pickup timestamp
            load_repo = await get_load_repository()
            await load_repo.execute_command(
                "UPDATE loads SET status = 'picked_up', actual_pickup_datetime = CURRENT_TIMESTAMP WHERE id = $1",
                load_id
            )
            
            # Start active tracking for this load
            # In a real system, this might enable GPS tracking, set up geofences, etc.
            logger.info(f"Active tracking enabled for load {load_id}")
            
            await self._store_event_analytics(event)
            
        except Exception as e:
            logger.error(f"Error handling load pickup event: {e}")
    
    async def _handle_load_in_transit(self, event: BaseEvent):
        """Handle load in transit - monitor progress, predict ETA"""
        try:
            self._track_event(EventType.LOAD_IN_TRANSIT)
            transit_data = event.data
            
            load_id = transit_data.get('load_id')
            logger.info(f"Processing load in transit: {load_id}")
            
            # Could trigger ETA calculations, route monitoring, etc.
            # For now, just log the progress
            current_location = transit_data.get('current_location')
            if current_location:
                logger.info(f"Load {load_id} current location: {current_location}")
            
            await self._store_event_analytics(event)
            
        except Exception as e:
            logger.error(f"Error handling load in transit event: {e}")
    
    async def _handle_load_delivered(self, event: BaseEvent):
        """Handle load delivery - complete transaction, free resources"""
        try:
            self._track_event(EventType.LOAD_DELIVERED)
            delivery_data = event.data
            
            load_id = delivery_data.get('load_id')
            logger.info(f"Processing load delivery: {load_id}")
            
            # Update load completion
            load_repo = await get_load_repository()
            await load_repo.execute_command(
                "UPDATE loads SET status = 'delivered', actual_delivery_datetime = CURRENT_TIMESTAMP WHERE id = $1",
                load_id
            )
            
            # Free up vehicle and driver
            load = await load_repo.get_load(load_id)
            if load:
                vehicle_id = load.get('vehicle_id')
                driver_id = load.get('driver_id')
                
                if vehicle_id:
                    vehicle_repo = await get_vehicle_repository()
                    await vehicle_repo.execute_command(
                        "UPDATE vehicles SET status = 'available', updated_at = CURRENT_TIMESTAMP WHERE id = $1",
                        vehicle_id
                    )
                    logger.info(f"Vehicle {vehicle_id} now available")
                
                if driver_id:
                    await vehicle_repo.execute_command(
                        "UPDATE drivers SET status = 'available', current_load_id = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = $1",
                        driver_id
                    )
                    logger.info(f"Driver {driver_id} now available")
            
            await self._store_event_analytics(event)
            
        except Exception as e:
            logger.error(f"Error handling load delivery event: {e}")
    
    async def _handle_load_cancelled(self, event: BaseEvent):
        """Handle load cancellation - free resources, handle refunds"""
        try:
            self._track_event(EventType.LOAD_CANCELLED)
            cancellation_data = event.data
            
            load_id = cancellation_data.get('load_id')
            reason = cancellation_data.get('reason', 'Not specified')
            logger.info(f"Processing load cancellation: {load_id}, Reason: {reason}")
            
            # Similar resource cleanup as delivery
            load_repo = await get_load_repository()
            load = await load_repo.get_load(load_id)
            if load:
                vehicle_id = load.get('vehicle_id')
                driver_id = load.get('driver_id')
                
                if vehicle_id:
                    vehicle_repo = await get_vehicle_repository()
                    await vehicle_repo.execute_command(
                        "UPDATE vehicles SET status = 'available', updated_at = CURRENT_TIMESTAMP WHERE id = $1",
                        vehicle_id
                    )
                
                if driver_id:
                    await vehicle_repo.execute_command(
                        "UPDATE drivers SET status = 'available', current_load_id = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = $1",
                        driver_id
                    )
            
            await self._store_event_analytics(event)
            
        except Exception as e:
            logger.error(f"Error handling load cancellation event: {e}")
    
    # Vehicle Event Handlers
    async def _handle_vehicle_location_update(self, event: BaseEvent):
        """Handle vehicle location updates - store tracking data, check geofences"""
        try:
            self._track_event(EventType.VEHICLE_LOCATION_UPDATE)
            location_data = event.data
            
            vehicle_id = location_data.get('vehicle_id')
            location = location_data.get('location', {})
            
            # Store in TimescaleDB
            timescale_repo = await get_timescale_repository()
            
            tracking_record = {
                'vehicle_id': vehicle_id,
                'latitude': location.get('latitude'),
                'longitude': location.get('longitude'),
                'speed': location_data.get('speed'),
                'heading': location_data.get('heading'),
                'fuel_level': location_data.get('fuel_level'),
                'is_moving': location_data.get('is_moving', False),
                'driver_id': location_data.get('driver_id'),
                'timestamp': datetime.utcnow()
            }
            
            await timescale_repo.insert_vehicle_tracking(tracking_record)
            
            # Check for interesting conditions
            speed = location_data.get('speed', 0)
            if speed > 80:  # Speed monitoring
                logger.warning(f"Vehicle {vehicle_id} exceeding speed limit: {speed} mph")
            
            if location_data.get('fuel_level', 100) < 20:  # Low fuel warning
                logger.warning(f"Vehicle {vehicle_id} low fuel: {location_data.get('fuel_level')}%")
            
        except Exception as e:
            logger.error(f"Error handling vehicle location update: {e}")
    
    async def _handle_vehicle_status_change(self, event: BaseEvent):
        """Handle vehicle status changes"""
        try:
            self._track_event(EventType.VEHICLE_STATUS_CHANGE)
            status_data = event.data
            
            vehicle_id = status_data.get('vehicle_id')
            old_status = status_data.get('old_status')
            new_status = status_data.get('new_status')
            
            logger.info(f"Vehicle {vehicle_id} status change: {old_status} -> {new_status}")
            
            await self._store_event_analytics(event)
            
        except Exception as e:
            logger.error(f"Error handling vehicle status change: {e}")
    
    # Driver Event Handlers
    async def _handle_driver_status_change(self, event: BaseEvent):
        """Handle driver status changes - manage HOS compliance"""
        try:
            self._track_event(EventType.DRIVER_STATUS_CHANGE)
            status_data = event.data
            
            driver_id = status_data.get('driver_id')
            old_status = status_data.get('old_status')
            new_status = status_data.get('new_status')
            
            logger.info(f"Driver {driver_id} status change: {old_status} -> {new_status}")
            
            # HOS (Hours of Service) compliance checks could go here
            if new_status == 'off_duty':
                logger.info(f"Driver {driver_id} went off duty - checking HOS compliance")
            
            await self._store_event_analytics(event)
            
        except Exception as e:
            logger.error(f"Error handling driver status change: {e}")
    
    async def _handle_driver_assigned(self, event: BaseEvent):
        """Handle driver assignment to loads"""
        try:
            self._track_event(EventType.DRIVER_ASSIGNED)
            assignment_data = event.data
            
            driver_id = assignment_data.get('driver_id')
            load_id = assignment_data.get('load_id')
            
            logger.info(f"Driver {driver_id} assigned to load {load_id}")
            
            await self._store_event_analytics(event)
            
        except Exception as e:
            logger.error(f"Error handling driver assignment: {e}")
    
    # Route Event Handlers
    async def _handle_route_optimized(self, event: BaseEvent):
        """Handle route optimization results"""
        try:
            self._track_event(EventType.ROUTE_OPTIMIZED)
            route_data = event.data
            
            route_id = route_data.get('route_id')
            vehicle_id = route_data.get('vehicle_id')
            estimated_duration = route_data.get('estimated_duration')
            
            logger.info(f"Route optimized: {route_id} for vehicle {vehicle_id}, ETA: {estimated_duration} minutes")
            
            await self._store_event_analytics(event)
            
        except Exception as e:
            logger.error(f"Error handling route optimization: {e}")
    
    async def _handle_route_deviation(self, event: BaseEvent):
        """Handle route deviation alerts"""
        try:
            self._track_event(EventType.ROUTE_DEVIATION)
            deviation_data = event.data
            
            vehicle_id = deviation_data.get('vehicle_id')
            deviation_distance = deviation_data.get('deviation_distance')
            
            logger.warning(f"Route deviation detected for vehicle {vehicle_id}: {deviation_distance} miles off route")
            
            await self._store_event_analytics(event)
            
        except Exception as e:
            logger.error(f"Error handling route deviation: {e}")
    
    # AI Event Handlers
    async def _handle_ai_prediction(self, event: BaseEvent):
        """Handle AI predictions and insights"""
        try:
            self._track_event(EventType.AI_PREDICTION)
            prediction_data = event.data
            
            prediction_type = prediction_data.get('prediction_type')
            confidence = prediction_data.get('confidence', 0)
            
            logger.info(f"AI Prediction: {prediction_type}, Confidence: {confidence:.2%}")
            
            # Act on high-confidence predictions
            if confidence > 0.9:
                if prediction_type == 'maintenance_alert':
                    urgency = prediction_data.get('urgency', 'low')
                    vehicle_id = prediction_data.get('vehicle_id')
                    logger.warning(f"High-confidence maintenance alert for vehicle {vehicle_id}: {urgency} urgency")
                elif prediction_type == 'delivery_delay':
                    load_id = prediction_data.get('load_id')
                    delay_minutes = prediction_data.get('predicted_delay', 0)
                    logger.warning(f"Predicted delivery delay for load {load_id}: {delay_minutes} minutes")
            
            await self._store_event_analytics(event)
            
        except Exception as e:
            logger.error(f"Error handling AI prediction: {e}")
    
    async def _store_event_analytics(self, event: BaseEvent):
        """Store event data for analytics"""
        try:
            timescale_repo = await get_timescale_repository()
            
            # Store event in analytics table
            await timescale_repo.db_manager.timescale_pool.execute(
                """
                INSERT INTO event_analytics (time, event_type, event_id, source, data)
                VALUES ($1, $2, $3, $4, $5)
                """,
                event.timestamp,
                event.event_type.value,
                event.event_id,
                event.source,
                event.model_dump_json()
            )
            
        except Exception as e:
            logger.error(f"Error storing event analytics: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            "events_processed": self.events_processed,
            "events_by_type": self.events_by_type,
            "last_activity": self.last_activity.isoformat(),
            "running": self.running
        }


# Service instance
event_processor_service = TMSEventProcessorService()


async def start_event_processor():
    """Start the event processor service"""
    await event_processor_service.start()


async def stop_event_processor():
    """Stop the event processor service"""
    await event_processor_service.stop()


if __name__ == "__main__":
    # Run as standalone service
    import signal
    import sys
    
    def signal_handler(sig, frame):
        print("\nShutting down event processor...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    async def main():
        await start_event_processor()
    
    asyncio.run(main())
