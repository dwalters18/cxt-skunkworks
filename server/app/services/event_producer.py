"""TMS Event Producer Service"""
import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List

from models.events import EventType, create_event
from kafka.producer import get_producer

logger = logging.getLogger(__name__)


class TMSEventProducerService:
    """Generates synthetic TMS events for testing and demonstration"""
    
    def __init__(self):
        self.producer = None
        self.running = False
        
        # Sample data for generating events
        self.load_ids = [f"LOAD-{i:05d}" for i in range(1000, 1100)]
        self.vehicle_ids = [f"VEH-{i:04d}" for i in range(100, 200)]
        self.driver_ids = [f"DRV-{i:04d}" for i in range(50, 150)]
        self.carrier_ids = [f"CAR-{i:03d}" for i in range(10, 30)]
        
        # Sample locations (lat, lon)
        self.locations = [
            {"name": "Dallas, TX", "lat": 32.7767, "lon": -96.7970},
            {"name": "Houston, TX", "lat": 29.7604, "lon": -95.3698},
            {"name": "Austin, TX", "lat": 30.2672, "lon": -97.7431},
            {"name": "San Antonio, TX", "lat": 29.4241, "lon": -98.4936},
            {"name": "Fort Worth, TX", "lat": 32.7555, "lon": -97.3308},
            {"name": "Phoenix, AZ", "lat": 33.4484, "lon": -112.0740},
            {"name": "Los Angeles, CA", "lat": 34.0522, "lon": -118.2437},
            {"name": "Chicago, IL", "lat": 41.8781, "lon": -87.6298},
            {"name": "Atlanta, GA", "lat": 33.7490, "lon": -84.3880},
            {"name": "Miami, FL", "lat": 25.7617, "lon": -80.1918}
        ]
    
    async def start(self):
        """Start the event producer service"""
        self.producer = await get_producer()
        self.running = True
        logger.info("TMS Event Producer Service started")
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self._generate_load_events()),
            asyncio.create_task(self._generate_vehicle_tracking()),
            asyncio.create_task(self._generate_driver_events()),
            asyncio.create_task(self._generate_route_events()),
            asyncio.create_task(self._generate_ai_predictions())
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def stop(self):
        """Stop the event producer service"""
        self.running = False
        logger.info("TMS Event Producer Service stopped")
    
    async def _generate_load_events(self):
        """Generate load lifecycle events"""
        while self.running:
            try:
                load_id = random.choice(self.load_ids)
                pickup_location = random.choice(self.locations)
                delivery_location = random.choice(self.locations)
                
                # Generate load created event
                load_data = {
                    "load_id": load_id,
                    "load_number": f"LN-{random.randint(10000, 99999)}",
                    "pickup_address": pickup_location["name"],
                    "delivery_address": delivery_location["name"],
                    "pickup_location": {
                        "latitude": pickup_location["lat"],
                        "longitude": pickup_location["lon"]
                    },
                    "delivery_location": {
                        "latitude": delivery_location["lat"],
                        "longitude": delivery_location["lon"]
                    },
                    "weight": random.randint(1000, 50000),
                    "rate": random.randint(500, 5000),
                    "pickup_datetime": (datetime.utcnow() + timedelta(hours=random.randint(1, 72))).isoformat(),
                    "delivery_datetime": (datetime.utcnow() + timedelta(hours=random.randint(24, 168))).isoformat()
                }
                
                event = create_event(EventType.LOAD_CREATED, load_data, "event_producer")
                await self.producer.send_event(event)
                
                # Sometimes generate follow-up events for the same load
                if random.random() < 0.3:
                    await asyncio.sleep(random.randint(5, 30))
                    
                    # Load assigned event
                    assignment_data = {
                        "load_id": load_id,
                        "carrier_id": random.choice(self.carrier_ids),
                        "vehicle_id": random.choice(self.vehicle_ids),
                        "driver_id": random.choice(self.driver_ids),
                        "old_status": "pending",
                        "new_status": "assigned"
                    }
                    
                    assign_event = create_event(EventType.LOAD_ASSIGNED, assignment_data, "event_producer")
                    await self.producer.send_event(assign_event)
                
                await asyncio.sleep(random.randint(30, 180))  # 30 seconds to 3 minutes
                
            except Exception as e:
                logger.error(f"Error generating load event: {e}")
                await asyncio.sleep(60)
    
    async def _generate_vehicle_tracking(self):
        """Generate vehicle tracking events"""
        # Track vehicle positions and movements
        vehicle_positions = {}
        
        # Initialize random positions for vehicles
        for vehicle_id in self.vehicle_ids:
            location = random.choice(self.locations)
            vehicle_positions[vehicle_id] = {
                "lat": location["lat"] + random.uniform(-0.5, 0.5),
                "lon": location["lon"] + random.uniform(-0.5, 0.5),
                "speed": random.randint(0, 75),
                "heading": random.randint(0, 359),
                "is_moving": random.choice([True, False])
            }
        
        while self.running:
            try:
                vehicle_id = random.choice(self.vehicle_ids)
                position = vehicle_positions[vehicle_id]
                
                # Simulate movement
                if position["is_moving"]:
                    # Small movement based on speed and heading
                    lat_change = random.uniform(-0.01, 0.01)
                    lon_change = random.uniform(-0.01, 0.01)
                    position["lat"] += lat_change
                    position["lon"] += lon_change
                    position["speed"] = max(0, position["speed"] + random.randint(-10, 10))
                    position["heading"] = (position["heading"] + random.randint(-30, 30)) % 360
                
                # Sometimes change movement status
                if random.random() < 0.1:
                    position["is_moving"] = not position["is_moving"]
                    if not position["is_moving"]:
                        position["speed"] = 0
                
                tracking_data = {
                    "vehicle_id": vehicle_id,
                    "location": {
                        "latitude": position["lat"],
                        "longitude": position["lon"]
                    },
                    "speed": position["speed"],
                    "heading": position["heading"],
                    "fuel_level": random.randint(10, 100),
                    "is_moving": position["is_moving"],
                    "driver_id": random.choice(self.driver_ids) if random.random() > 0.3 else None
                }
                
                event = create_event(EventType.VEHICLE_LOCATION_UPDATE, tracking_data, "event_producer")
                await self.producer.send_event(event)
                
                await asyncio.sleep(random.randint(10, 60))  # 10 seconds to 1 minute
                
            except Exception as e:
                logger.error(f"Error generating vehicle tracking event: {e}")
                await asyncio.sleep(30)
    
    async def _generate_driver_events(self):
        """Generate driver-related events"""
        while self.running:
            try:
                driver_id = random.choice(self.driver_ids)
                
                # Random driver events
                event_types = [
                    (EventType.DRIVER_STATUS_CHANGE, {
                        "driver_id": driver_id,
                        "old_status": random.choice(["available", "on_duty", "off_duty"]),
                        "new_status": random.choice(["available", "on_duty", "off_duty", "break"])
                    }),
                    (EventType.DRIVER_ASSIGNED, {
                        "driver_id": driver_id,
                        "load_id": random.choice(self.load_ids),
                        "vehicle_id": random.choice(self.vehicle_ids)
                    })
                ]
                
                event_type, data = random.choice(event_types)
                event = create_event(event_type, data, "event_producer")
                await self.producer.send_event(event)
                
                await asyncio.sleep(random.randint(120, 600))  # 2 to 10 minutes
                
            except Exception as e:
                logger.error(f"Error generating driver event: {e}")
                await asyncio.sleep(60)
    
    async def _generate_route_events(self):
        """Generate route optimization and navigation events"""
        while self.running:
            try:
                route_data = {
                    "route_id": f"ROUTE-{random.randint(1000, 9999)}",
                    "vehicle_id": random.choice(self.vehicle_ids),
                    "start_location": random.choice(self.locations),
                    "end_location": random.choice(self.locations),
                    "waypoints": random.sample(self.locations, random.randint(1, 3)),
                    "estimated_duration": random.randint(60, 720),  # minutes
                    "estimated_distance": random.randint(50, 1500),  # miles
                    "traffic_conditions": random.choice(["light", "moderate", "heavy"]),
                    "weather_conditions": random.choice(["clear", "rain", "fog", "snow"])
                }
                
                event = create_event(EventType.ROUTE_OPTIMIZED, route_data, "event_producer")
                await self.producer.send_event(event)
                
                await asyncio.sleep(random.randint(300, 900))  # 5 to 15 minutes
                
            except Exception as e:
                logger.error(f"Error generating route event: {e}")
                await asyncio.sleep(60)
    
    async def _generate_ai_predictions(self):
        """Generate AI prediction events"""
        while self.running:
            try:
                prediction_types = [
                    {
                        "prediction_type": "delivery_time",
                        "load_id": random.choice(self.load_ids),
                        "predicted_delivery": (datetime.utcnow() + timedelta(hours=random.randint(1, 48))).isoformat(),
                        "confidence": random.uniform(0.7, 0.95),
                        "factors": ["traffic", "weather", "driver_performance"]
                    },
                    {
                        "prediction_type": "fuel_consumption",
                        "vehicle_id": random.choice(self.vehicle_ids),
                        "predicted_consumption": random.uniform(15, 45),
                        "confidence": random.uniform(0.8, 0.99),
                        "factors": ["route_distance", "traffic", "vehicle_efficiency"]
                    },
                    {
                        "prediction_type": "maintenance_alert",
                        "vehicle_id": random.choice(self.vehicle_ids),
                        "maintenance_type": random.choice(["oil_change", "brake_service", "tire_rotation"]),
                        "predicted_date": (datetime.utcnow() + timedelta(days=random.randint(1, 30))).isoformat(),
                        "urgency": random.choice(["low", "medium", "high"])
                    }
                ]
                
                prediction_data = random.choice(prediction_types)
                event = create_event(EventType.AI_PREDICTION, prediction_data, "ai_service")
                await self.producer.send_event(event)
                
                await asyncio.sleep(random.randint(180, 600))  # 3 to 10 minutes
                
            except Exception as e:
                logger.error(f"Error generating AI prediction event: {e}")
                await asyncio.sleep(60)


# Service instance
event_producer_service = TMSEventProducerService()


async def start_event_producer():
    """Start the event producer service"""
    await event_producer_service.start()


async def stop_event_producer():
    """Stop the event producer service"""
    await event_producer_service.stop()


if __name__ == "__main__":
    # Run as standalone service
    import signal
    import sys
    
    def signal_handler(sig, frame):
        print("\nShutting down event producer...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    async def main():
        await start_event_producer()
    
    asyncio.run(main())
