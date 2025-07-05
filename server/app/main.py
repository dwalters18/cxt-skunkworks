# server/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

# Import routers
from routers import (
    health,
    loads,
    drivers,
    vehicles,
    routes,
    events,
    analytics,
    websocket
)

# Import background services
from kafka.consumer import get_consumer, TMSEventConsumer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
consumer_task: Optional[asyncio.Task] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global consumer_task
    logger.info("Starting TMS Event-Driven API...")
    
    # Start Kafka consumer in background
    try:
        consumer = get_consumer()
        event_consumer = TMSEventConsumer(consumer)
        consumer_task = asyncio.create_task(event_consumer.start_consuming())
        logger.info("Kafka consumer started")
    except Exception as e:
        logger.error(f"Failed to start Kafka consumer: {e}")
    
    yield
    
    # Cleanup
    logger.info("Shutting down TMS Event-Driven API...")
    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            logger.info("Kafka consumer stopped")
    
    logger.info("Shutdown complete")


# Initialize FastAPI app
app = FastAPI(
    title="TMS Event-Driven API",
    description="Transportation Management System with Event-Driven Architecture",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(loads.router)
app.include_router(drivers.router)
app.include_router(vehicles.router)
app.include_router(routes.router)
app.include_router(events.router)
app.include_router(analytics.router)
app.include_router(websocket.router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
