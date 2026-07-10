"""Validated canonical event publisher.

The ONLY way events reach the `lip.*` topics. publish() validates twice before
anything is sent:

  1. the envelope itself (core.envelope.EventEnvelope — field types, eventType
     grammar, timezone-aware timestamps, at least one entityRef)
  2. the payload against the event type's registered schema (core.catalog)

A malformed event raises EventValidationError and is never produced. This is the
publish-side enforcement the demo relies on: bad shapes die at the door, so every
consumer can trust that anything on a canonical topic parses as envelope v1.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from aiokafka import AIOKafkaProducer
from pydantic import ValidationError

from core import catalog
from core.config import KAFKA_BOOTSTRAP_SERVERS, TENANT_ID
from core.envelope import EntityRef, EventEnvelope, SourceSystem

logger = logging.getLogger(__name__)


class EventValidationError(Exception):
    """Raised when an event fails envelope or payload validation. Not published."""

    def __init__(self, message: str, details: Any = None):
        super().__init__(message)
        self.details = details


def build_envelope(
    event_type: str,
    source_system: SourceSystem,
    entity_refs: List[EntityRef],
    payload: Dict[str, Any],
    occurred_at: Optional[datetime] = None,
    trace_id: Optional[str] = None,
    tenant_id: str = TENANT_ID,
) -> EventEnvelope:
    """Construct and fully validate a canonical event; raises EventValidationError."""
    try:
        spec = catalog.spec_for(event_type)
    except KeyError:
        raise EventValidationError(
            f"eventType {event_type!r} is not in the event catalog; "
            "register it in core/catalog.py before publishing"
        )

    # Validate the payload against the registered schema, then serialize it in
    # wire form so the topic always carries the canonical camelCase shape.
    try:
        payload_wire = spec.payload_model.model_validate(payload).model_dump(
            by_alias=True, mode="json"
        )
    except ValidationError as e:
        raise EventValidationError(
            f"payload for {event_type} failed schema validation", details=e.errors()
        )

    try:
        kwargs: Dict[str, Any] = dict(
            event_type=event_type,
            source_system=source_system,
            tenant_id=tenant_id,
            entity_refs=entity_refs,
            occurred_at=occurred_at or datetime.now(timezone.utc),
            payload=payload_wire,
        )
        if trace_id is not None:
            kwargs["trace_id"] = trace_id
        return EventEnvelope(**kwargs)
    except ValidationError as e:
        raise EventValidationError(
            f"envelope for {event_type} failed validation", details=e.errors()
        )


class EventPublisher:
    """Async Kafka producer that only speaks envelope v1."""

    def __init__(self, bootstrap_servers: str = KAFKA_BOOTSTRAP_SERVERS):
        self.bootstrap_servers = bootstrap_servers
        self._producer: Optional[AIOKafkaProducer] = None

    async def start(self) -> None:
        if self._producer is not None:
            return
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            acks="all",
            linger_ms=5,
        )
        await self._producer.start()
        logger.info("EventPublisher connected to %s", self.bootstrap_servers)

    async def stop(self) -> None:
        if self._producer is not None:
            await self._producer.stop()
            self._producer = None

    async def publish(self, envelope: EventEnvelope) -> None:
        """Publish a validated envelope to its catalog topic.

        Keyed by the primary entity id so all events about one entity stay
        ordered within a partition.
        """
        if self._producer is None:
            raise RuntimeError("EventPublisher not started")

        topic = catalog.topic_for(envelope.event_type)
        headers = [
            ("eventType", envelope.event_type.encode()),
            ("eventId", envelope.event_id.encode()),
            ("traceId", envelope.trace_id.encode()),
            ("tenantId", envelope.tenant_id.encode()),
        ]
        await self._producer.send_and_wait(
            topic,
            value=envelope.to_wire(),
            key=envelope.primary_entity.id,
            headers=headers,
        )
        logger.debug("published %s -> %s", envelope.event_type, topic)

    async def emit(
        self,
        event_type: str,
        source_system: SourceSystem,
        entity_refs: List[EntityRef],
        payload: Dict[str, Any],
        occurred_at: Optional[datetime] = None,
        trace_id: Optional[str] = None,
    ) -> EventEnvelope:
        """build_envelope + publish in one call. Returns the envelope that was sent."""
        envelope = build_envelope(
            event_type=event_type,
            source_system=source_system,
            entity_refs=entity_refs,
            payload=payload,
            occurred_at=occurred_at,
            trace_id=trace_id,
        )
        await self.publish(envelope)
        return envelope


_publisher: Optional[EventPublisher] = None


async def get_publisher() -> EventPublisher:
    """Process-wide publisher singleton."""
    global _publisher
    if _publisher is None:
        _publisher = EventPublisher()
        await _publisher.start()
    return _publisher
