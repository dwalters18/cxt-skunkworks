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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
consumer_task: Optional[asyncio.Task] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global consumer_task
    logger.info("=== STARTING TMS EVENT-DRIVEN API ===")

    # Start Kafka consumer in background
    try:
        logger.info("Step 1: Initializing Kafka consumer...")
        consumer = await get_consumer()
        logger.info("Step 2: Kafka consumer instance created successfully")

        logger.info("Step 3: Starting Kafka consumer background task...")

        # Wrap the consumer start in a safe background task
        async def safe_consumer_start():
            try:
                await consumer.start()
                logger.info("Kafka consumer started successfully")
            except Exception as e:
                logger.error(f"Kafka consumer failed to start: {e}")
                logger.exception("Kafka consumer startup error:")

        consumer_task = asyncio.create_task(safe_consumer_start())
        logger.info("Step 4: Kafka consumer background task created")

        # Give it a brief moment to attempt startup, but don't wait for completion
        await asyncio.sleep(0.5)
        logger.info("Step 5: Initial startup delay completed")

        logger.info("=== KAFKA CONSUMER STARTUP COMPLETED ===")
    except Exception as e:
        logger.error(f"ERROR: Failed to initialize Kafka consumer: {e}")
        logger.exception("Full exception details:")
        # Don't fail the entire app if Kafka consumer fails
        logger.warning("Continuing without Kafka consumer...")
        consumer_task = None

    logger.info("=== API STARTUP COMPLETED - READY TO SERVE REQUESTS ===")
    yield

    # Cleanup
    logger.info("=== SHUTTING DOWN TMS EVENT-DRIVEN API ===")
    if consumer_task:
        logger.info("Cancelling Kafka consumer task...")
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            logger.info("Kafka consumer stopped gracefully")

    logger.info("=== SHUTDOWN COMPLETE ===")


# Initialize FastAPI app
logger.info("Initializing FastAPI application...")
app = FastAPI(
    title="TMS Event-Driven API",
    description="Transportation Management System with Event-Driven Architecture",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False  # Allow both /api/loads and /api/loads/ to work
)
logger.info("FastAPI application initialized")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("CORS middleware configured for localhost:3000")

# Register routers with /api prefix
logger.info("Registering API routers...")
try:
    logger.info("- Adding health router")
    app.include_router(health.router, prefix="/api")
    logger.info("- Adding loads router")
    app.include_router(loads.router, prefix="/api")
    logger.info("- Adding drivers router")
    app.include_router(drivers.router, prefix="/api")
    logger.info("- Adding vehicles router")
    app.include_router(vehicles.router, prefix="/api")
    logger.info("- Adding routes router")
    app.include_router(routes.router, prefix="/api")
    logger.info("- Adding events router")
    app.include_router(events.router, prefix="/api")
    logger.info("- Adding analytics router")
    app.include_router(analytics.router, prefix="/api")
    logger.info("- Adding websocket router")
    # WebSocket router doesn't need /api prefix
    app.include_router(websocket.router)
    logger.info("All routers registered successfully")
except Exception as e:
    logger.error(f"ERROR: Failed to register routers: {e}")
    logger.exception("Router registration error details:")
    raise


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
