"""Event endpoints — the demo surface for the canonical contract.

  GET  /api/events/recent   recent envelopes from the event_stream projection
  GET  /api/events/catalog  the machine-readable event catalog (types + schemas)
  POST /api/events/publish  manual publish; malformed events are REJECTED with 422,
                            demonstrating publish-side validation live
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core import catalog
from core.envelope import EntityRef, SourceSystem
from routers.deps import get_events, get_trace_id, get_ts

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/recent")
async def recent_events(
    limit: int = 50,
    event_type: Optional[str] = None,
    source_system: Optional[str] = None,
    ts=Depends(get_ts),
):
    conditions, params = [], []
    if event_type:
        params.append(event_type)
        conditions.append(f"event_type = ${len(params)}")
    if source_system:
        params.append(source_system)
        conditions.append(f"source_system = ${len(params)}")
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.append(min(limit, 500))
    rows = await ts.fetch(
        f"""
        SELECT time, event_id, event_type, event_version, source_system, tenant_id,
               trace_id, entity_refs, occurred_at, payload
        FROM event_stream {where}
        ORDER BY time DESC LIMIT ${len(params)}
        """,
        *params,
    )
    events = [
        {
            "eventId": str(r["event_id"]),
            "eventType": r["event_type"],
            "eventVersion": r["event_version"],
            "sourceSystem": r["source_system"],
            "tenantId": r["tenant_id"],
            "traceId": str(r["trace_id"]) if r["trace_id"] else None,
            "entityRefs": json.loads(r["entity_refs"]),
            "occurredAt": r["occurred_at"].isoformat().replace("+00:00", "Z"),
            "observedAt": r["time"].isoformat().replace("+00:00", "Z"),
            "payload": json.loads(r["payload"]),
        }
        for r in rows
    ]
    return {"events": events, "count": len(events)}


@router.get("/catalog")
async def event_catalog():
    types = []
    for spec in catalog.CATALOG.values():
        types.append(
            {
                "eventType": spec.name,
                "topic": spec.topic,
                "description": spec.description,
                "payloadSchema": spec.payload_model.model_json_schema(by_alias=True),
            }
        )
    return {
        "envelopeVersion": "1.0",
        "topics": catalog.CANONICAL_TOPICS,
        "eventTypes": types,
        "count": len(types),
    }


class PublishRequest(BaseModel):
    eventType: str
    entityRefs: List[Dict[str, str]]
    payload: Dict[str, Any]


@router.post("/publish", status_code=202)
async def publish_event(
    body: PublishRequest,
    events=Depends(get_events),
    trace_id=Depends(get_trace_id),
):
    """Manually publish a canonical event. Malformed events never reach Kafka."""
    from eventbus.publisher import EventValidationError

    try:
        refs = [EntityRef(**r) for r in body.entityRefs]
    except Exception as e:
        raise HTTPException(422, detail=f"invalid entityRefs: {e}")
    try:
        envelope = await events.emit(
            body.eventType,
            SourceSystem.API,
            entity_refs=refs,
            payload=body.payload,
            trace_id=trace_id,
        )
    except EventValidationError as e:
        raise HTTPException(
            422,
            detail={"message": str(e), "errors": e.details, "rejected": True},
        )
    return {"published": True, "eventId": envelope.event_id, "topic": catalog.topic_for(envelope.event_type)}
