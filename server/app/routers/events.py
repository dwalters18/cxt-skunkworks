"""Event management endpoints for TMS API."""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional
import logging
import json

from models.events import EventType, BaseEvent, create_event
from dependencies import get_timescale_repo, get_kafka_producer
from kafka.producer import get_producer
from websocket_manager import broadcast_event_to_websockets

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["events"])


class EventSubscription(BaseModel):
    """Event subscription model."""
    topics: List[str]
    webhook_url: Optional[str] = None


@router.get("/recent")
async def get_recent_events(
    limit: int = 10,
    timescale_repo=Depends(get_timescale_repo)
):
    """Get recent events from TimescaleDB."""
    try:
        # Get recent events from load_events table (our main event table)
        query = """
            SELECT 
                event_id, event_type, event_data, created_at,
                load_id, vehicle_id, driver_id
            FROM load_events 
            ORDER BY created_at DESC 
            LIMIT $1
        """
        
        events = await timescale_repo.execute_query(query, limit)
        
        # Format events for API response
        formatted_events = []
        for event in events:
            formatted_event = {
                "event_id": event["event_id"],
                "event_type": event["event_type"],
                "timestamp": event["created_at"].isoformat(),
                "data": event["event_data"] if isinstance(event["event_data"], dict) else json.loads(event["event_data"]) if event["event_data"] else {},
                "source": "TMS_API"
            }
            
            # Add entity references if available
            if event.get("load_id"):
                formatted_event["data"]["load_id"] = event["load_id"]
            if event.get("vehicle_id"):
                formatted_event["data"]["vehicle_id"] = event["vehicle_id"]
            if event.get("driver_id"):
                formatted_event["data"]["driver_id"] = event["driver_id"]
                
            formatted_events.append(formatted_event)
        
        return {
            "events": formatted_events,
            "count": len(formatted_events),
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error retrieving recent events: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve recent events: {str(e)}")


@router.get("/topics")
async def get_event_topics():
    """Get available event topics."""
    try:
        # Return all available event types from our EventType enum
        topics = []
        for event_type in EventType:
            topic = f"tms.{event_type.value.lower().replace('_', '.')}"
            topics.append({
                "event_type": event_type.value,
                "topic": topic,
                "description": f"Events related to {event_type.value.replace('_', ' ').lower()}"
            })
        
        # Group topics by domain
        load_topics = [t for t in topics if "load" in t["topic"]]
        vehicle_topics = [t for t in topics if "vehicle" in t["topic"]]
        driver_topics = [t for t in topics if "driver" in t["topic"]]
        route_topics = [t for t in topics if "route" in t["topic"]]
        system_topics = [t for t in topics if "system" in t["topic"] or "ai" in t["topic"]]
        
        return {
            "topics": topics,
            "grouped_topics": {
                "loads": load_topics,
                "vehicles": vehicle_topics,
                "drivers": driver_topics,
                "routes": route_topics,
                "system": system_topics
            },
            "total_topics": len(topics)
        }
    except Exception as e:
        logger.error(f"Error retrieving event topics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve event topics: {str(e)}")


@router.post("/publish")
async def publish_event(
    event_data: Dict, 
    background_tasks: BackgroundTasks,
    producer=Depends(get_kafka_producer)
):
    """Manually publish an event (for testing)."""
    try:
        # Validate event structure
        if "event_type" not in event_data:
            raise HTTPException(status_code=400, detail="event_type is required")
        
        event_type_str = event_data["event_type"]
        
        # Validate event type
        try:
            event_type = EventType(event_type_str)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid event_type: {event_type_str}")
        
        # Create event using our event factory
        event = create_event(
            event_type=event_type,
            data=event_data.get("data", {}),
            source=event_data.get("source", "MANUAL_API"),
            correlation_id=event_data.get("correlation_id")
        )
        
        # Determine Kafka topic based on event type
        topic_mapping = {
            EventType.LOAD_CREATED: "tms.loads",
            EventType.LOAD_ASSIGNED: "tms.loads",
            EventType.LOAD_PICKED_UP: "tms.loads",
            EventType.LOAD_IN_TRANSIT: "tms.loads",
            EventType.LOAD_DELIVERED: "tms.loads",
            EventType.LOAD_CANCELLED: "tms.loads",
            EventType.VEHICLE_LOCATION_UPDATED: "tms.vehicles.tracking",
            EventType.VEHICLE_STATUS_CHANGED: "tms.vehicles",
            EventType.DRIVER_STATUS_CHANGED: "tms.drivers",
            EventType.DRIVER_LOCATION_UPDATED: "tms.drivers.tracking",
            EventType.ROUTE_OPTIMIZED: "tms.routes",
            EventType.ROUTE_DEVIATION: "tms.routes.alerts",
            EventType.AI_PREDICTION: "tms.ai.predictions",
            EventType.SYSTEM_ALERT: "tms.system.alerts"
        }
        
        topic = topic_mapping.get(event_type, "tms.events")
        
        # Publish to Kafka
        await producer.send(topic, event.dict())
        
        # Broadcast to WebSocket clients
        background_tasks.add_task(broadcast_event_to_websockets, {
            "event_type": event.event_type.value,
            "data": event.data,
            "timestamp": event.timestamp.isoformat(),
            "event_id": event.event_id
        })
        
        return {
            "message": "Event published successfully",
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "topic": topic
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error publishing event: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to publish event: {str(e)}")


@router.get("/filter")
async def get_events_by_filter(
    event_type: Optional[str] = None,
    load_id: Optional[str] = None,
    vehicle_id: Optional[str] = None,
    driver_id: Optional[str] = None,
    hours: int = 24,
    limit: int = 50,
    timescale_repo=Depends(get_timescale_repo)
):
    """Get events filtered by various criteria."""
    try:
        # Build query conditions
        conditions = []
        params = []
        param_count = 0
        
        if event_type:
            param_count += 1
            conditions.append(f"event_type = ${param_count}")
            params.append(event_type)
            
        if load_id:
            param_count += 1
            conditions.append(f"load_id = ${param_count}")
            params.append(load_id)
            
        if vehicle_id:
            param_count += 1
            conditions.append(f"vehicle_id = ${param_count}")
            params.append(vehicle_id)
            
        if driver_id:
            param_count += 1
            conditions.append(f"driver_id = ${param_count}")
            params.append(driver_id)
        
        # Add time filter
        param_count += 1
        conditions.append(f"created_at >= NOW() - INTERVAL '${param_count} hours'")
        params.append(hours)
        
        where_clause = f"WHERE {' AND '.join(conditions)}"
        
        # Add limit parameter
        param_count += 1
        limit_param = param_count
        query = f"""
            SELECT 
                event_id, event_type, event_data, created_at,
                load_id, vehicle_id, driver_id
            FROM load_events 
            {where_clause}
            ORDER BY created_at DESC 
            LIMIT ${limit_param}
        """
        params.append(limit)
        
        events = await timescale_repo.execute_query(query, params)
        
        # Format events for API response
        formatted_events = []
        for event in events:
            formatted_event = {
                "event_id": event["event_id"],
                "event_type": event["event_type"],
                "timestamp": event["created_at"].isoformat(),
                "data": event["event_data"] if isinstance(event["event_data"], dict) else json.loads(event["event_data"]) if event["event_data"] else {},
                "source": "TMS_API"
            }
            
            # Add entity references if available
            if event.get("load_id"):
                formatted_event["data"]["load_id"] = event["load_id"]
            if event.get("vehicle_id"):
                formatted_event["data"]["vehicle_id"] = event["vehicle_id"]
            if event.get("driver_id"):
                formatted_event["data"]["driver_id"] = event["driver_id"]
                
            formatted_events.append(formatted_event)
        
        return {
            "events": formatted_events,
            "count": len(formatted_events),
            "filters": {
                "event_type": event_type,
                "load_id": load_id,
                "vehicle_id": vehicle_id,
                "driver_id": driver_id,
                "hours": hours
            },
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error filtering events: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to filter events: {str(e)}")
