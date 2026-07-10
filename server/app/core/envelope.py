"""Canonical event envelope v1 — the one contract every event in LIP uses.

Every event on the canonical backbone (`lip.*` topics) is an instance of
EventEnvelope, regardless of where it came from:

  - lip-api            business intent events emitted by the API (order.created, ...)
  - lip-cdc-normalizer observation events derived from Debezium CDC (order.record-updated, ...)
  - lip-simulator      telemetry from the driver simulator (driver.location-updated)
  - lip-seeder         genesis events emitted by demo reset

Wire format is JSON with camelCase keys:

    {
      "eventId": "6f1c...",                       # unique per event (uuid4)
      "eventType": "order.created",               # dot-namespaced: <entity>.<action>
      "eventVersion": "1.0",                      # schema version of this event type
      "sourceSystem": "lip-api",                  # which producer emitted it
      "tenantId": "cxt-demo",                     # tenant scoping anchor
      "entityRefs": [{"type": "order", "id": "..."}],
      "occurredAt": "2026-07-09T14:03:22.120Z",   # when the fact happened (business time)
      "observedAt": "2026-07-09T14:03:22.140Z",   # when the backbone saw it (ingest time)
      "payload": { ... },                         # event-type-specific body (see catalog)
      "traceId": "b2c4..."                        # correlates events from one cause
    }

Publish-side validation lives in eventbus.publisher: an event that does not
validate against this envelope AND its event type's payload schema (core.catalog)
is rejected and never reaches Kafka.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator
from pydantic.alias_generators import to_camel

ENVELOPE_VERSION = "1.0"

# <entity>.<action> — lowercase, kebab-case segments, exactly one dot.
EVENT_TYPE_PATTERN = re.compile(r"^[a-z]+(?:-[a-z]+)*\.[a-z]+(?:-[a-z]+)*$")


class EntityType(str, Enum):
    """Canonical vocabulary: the only entity types an event may reference."""

    ORDER = "order"
    STOP = "stop"
    ROUTE = "route"
    DRIVER = "driver"
    VEHICLE = "vehicle"
    PARCEL = "parcel"
    CUSTOMER = "customer"
    DEPOT = "depot"
    TENANT = "tenant"


class SourceSystem(str, Enum):
    API = "lip-api"
    CDC_NORMALIZER = "lip-cdc-normalizer"
    SIMULATOR = "lip-simulator"
    SEEDER = "lip-seeder"


class EntityRef(BaseModel):
    """A typed reference to a canonical entity touched by the event."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    type: EntityType
    id: str = Field(min_length=1)


class EventEnvelope(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
        extra="forbid",
    )

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    event_version: str = ENVELOPE_VERSION
    source_system: SourceSystem
    tenant_id: str = Field(min_length=1)
    entity_refs: List[EntityRef] = Field(min_length=1)
    occurred_at: datetime
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Dict[str, Any]
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    @field_validator("event_type")
    @classmethod
    def event_type_is_dot_namespaced(cls, v: str) -> str:
        if not EVENT_TYPE_PATTERN.match(v):
            raise ValueError(
                f"eventType {v!r} must be dot-namespaced kebab-case, e.g. 'order.created'"
            )
        return v

    @field_validator("occurred_at", "observed_at")
    @classmethod
    def timestamps_are_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("timestamps must be timezone-aware (UTC)")
        return v.astimezone(timezone.utc)

    @field_serializer("occurred_at", "observed_at")
    def serialize_ts(self, v: datetime) -> str:
        return v.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    def to_wire(self) -> Dict[str, Any]:
        """The camelCase JSON-safe dict that goes on the topic."""
        return self.model_dump(by_alias=True, mode="json")

    @property
    def primary_entity(self) -> EntityRef:
        """First entity ref — used as the Kafka message key for partition ordering."""
        return self.entity_refs[0]
