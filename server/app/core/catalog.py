"""Event catalog — every event type LIP knows, its payload schema, and its topic.

This registry is the single source of truth for:
  - which eventType strings are legal (the publisher rejects unregistered types)
  - what each event type's payload must look like (pydantic models, camelCase wire)
  - which topic each event type is published to

EVENT-CATALOG.md at the repo root is the human-readable mirror of this file and is
generated from it (`python -m tools.render_catalog`), so code and docs cannot drift.

Topic layout (all canonical, all envelope v1):

  lip.orders             order.* business events
  lip.stops              stop.* business events
  lip.routes             route.* business events
  lip.drivers            driver.* business events (low volume)
  lip.drivers.locations  driver.location-updated telemetry (high volume)
  lip.vehicles           vehicle.* business events
  lip.cdc                *.record-created|updated|deleted observation events (from CDC)
  lip.system             system.* platform events

Non-canonical (envelope-exempt, documented in EVENT-CATALOG.md):
  cdc.raw.*              raw Debezium change feed — source-shaped input consumed
                         only by the normalizer, never by application code.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

# ---------------------------------------------------------------------------
# Topics
# ---------------------------------------------------------------------------

TOPIC_ORDERS = "lip.orders"
TOPIC_STOPS = "lip.stops"
TOPIC_ROUTES = "lip.routes"
TOPIC_DRIVERS = "lip.drivers"
TOPIC_DRIVER_LOCATIONS = "lip.drivers.locations"
TOPIC_VEHICLES = "lip.vehicles"
TOPIC_CDC = "lip.cdc"
TOPIC_SYSTEM = "lip.system"

CANONICAL_TOPICS = [
    TOPIC_ORDERS,
    TOPIC_STOPS,
    TOPIC_ROUTES,
    TOPIC_DRIVERS,
    TOPIC_DRIVER_LOCATIONS,
    TOPIC_VEHICLES,
    TOPIC_CDC,
    TOPIC_SYSTEM,
]

# Raw Debezium output namespace (input to the normalizer, not canonical).
CDC_RAW_TOPIC_PREFIX = "cdc.raw"

# Entities that flow through CDC record-change events.
CDC_ENTITIES = [
    "order",
    "stop",
    "route",
    "driver",
    "vehicle",
    "parcel",
    "customer",
    "depot",
]


# ---------------------------------------------------------------------------
# Payload schemas (camelCase on the wire)
# ---------------------------------------------------------------------------


class PayloadModel(BaseModel):
    """Base for all payload schemas: camelCase wire names, unknown fields rejected."""

    model_config = ConfigDict(
        populate_by_name=True, alias_generator=to_camel, extra="forbid"
    )


class GeoPoint(PayloadModel):
    latitude: float
    longitude: float


class StopSnapshot(PayloadModel):
    stop_id: str
    kind: str  # PICKUP | DELIVERY
    address: str
    location: GeoPoint
    window_start: Optional[str] = None  # ISO 8601
    window_end: Optional[str] = None


class OrderCreatedPayload(PayloadModel):
    order_id: str
    order_number: str
    customer_id: str
    customer_name: str
    service_level: str  # ROUTINE | RUSH | STAT
    parcel_count: int
    pickup: StopSnapshot
    delivery: StopSnapshot
    notes: Optional[str] = None


class StopAssignment(PayloadModel):
    """Where an order's stop landed on the route — enough for a projection
    consumer (like the dispatch board) to draw the change without refetching."""

    stop_id: str
    kind: str  # PICKUP | DELIVERY
    sequence: int


class OrderAssignedPayload(PayloadModel):
    order_id: str
    order_number: str
    route_id: str
    route_number: str
    driver_id: Optional[str] = None
    vehicle_id: Optional[str] = None
    stops: List[StopAssignment] = []


class OrderCompletedPayload(PayloadModel):
    order_id: str
    order_number: str
    route_id: Optional[str] = None


class OrderCancelledPayload(PayloadModel):
    order_id: str
    order_number: str
    reason: Optional[str] = None


class StopStatusUpdatedPayload(PayloadModel):
    stop_id: str
    order_id: str
    route_id: Optional[str] = None
    kind: str  # PICKUP | DELIVERY
    previous_status: str
    status: str  # PENDING | ARRIVED | COMPLETED | FAILED


class RoutePlannedPayload(PayloadModel):
    route_id: str
    route_number: str
    service_date: str  # ISO date
    driver_id: Optional[str] = None
    vehicle_id: Optional[str] = None
    stop_count: int


class RouteStartedPayload(PayloadModel):
    route_id: str
    route_number: str
    driver_id: Optional[str] = None
    vehicle_id: Optional[str] = None


class RouteCompletedPayload(PayloadModel):
    route_id: str
    route_number: str


class DriverStatusUpdatedPayload(PayloadModel):
    driver_id: str
    driver_name: str
    previous_status: str
    status: str  # AVAILABLE | ON_ROUTE | OFF_DUTY


class DriverLocationUpdatedPayload(PayloadModel):
    driver_id: str
    vehicle_id: Optional[str] = None
    route_id: Optional[str] = None
    location: GeoPoint
    speed_mph: Optional[float] = None
    heading_deg: Optional[float] = None


class VehicleStatusUpdatedPayload(PayloadModel):
    vehicle_id: str
    vehicle_number: str
    previous_status: str
    status: str  # AVAILABLE | IN_SERVICE | MAINTENANCE


class RecordChangePayload(PayloadModel):
    """Observation event derived from the raw Debezium change feed.

    `before`/`after` are source-shaped row images (snake_case column names, as
    they exist in Postgres) — they are evidence about the system of record, not
    a business contract. Geography columns are decoded to {latitude, longitude}.
    """

    model_config = ConfigDict(
        populate_by_name=True, alias_generator=to_camel, extra="forbid"
    )

    table: str
    op: str  # created | updated | deleted (Debezium c/u/r -> created, d -> deleted)
    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None
    source_ts_ms: Optional[int] = None


class DemoResetPayload(PayloadModel):
    seed_version: str
    counts: Dict[str, int]


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EventTypeSpec:
    name: str
    topic: str
    payload_model: Type[BaseModel]
    description: str


def _business_events() -> List[EventTypeSpec]:
    return [
        EventTypeSpec(
            "order.created",
            TOPIC_ORDERS,
            OrderCreatedPayload,
            "A new order was placed; its pickup and delivery stops now exist.",
        ),
        EventTypeSpec(
            "order.assigned",
            TOPIC_ORDERS,
            OrderAssignedPayload,
            "An order's stops were attached to a route (and thereby a driver/vehicle).",
        ),
        EventTypeSpec(
            "order.completed",
            TOPIC_ORDERS,
            OrderCompletedPayload,
            "The order's delivery stop completed; the order is done.",
        ),
        EventTypeSpec(
            "order.cancelled",
            TOPIC_ORDERS,
            OrderCancelledPayload,
            "The order was cancelled; its pending stops were withdrawn.",
        ),
        EventTypeSpec(
            "stop.status-updated",
            TOPIC_STOPS,
            StopStatusUpdatedPayload,
            "A stop moved through its lifecycle: PENDING -> ARRIVED -> COMPLETED (or FAILED).",
        ),
        EventTypeSpec(
            "route.planned",
            TOPIC_ROUTES,
            RoutePlannedPayload,
            "A route was created/planned for a service date.",
        ),
        EventTypeSpec(
            "route.started",
            TOPIC_ROUTES,
            RouteStartedPayload,
            "A route went ACTIVE; its driver is now driving it.",
        ),
        EventTypeSpec(
            "route.completed",
            TOPIC_ROUTES,
            RouteCompletedPayload,
            "All stops on the route are completed (or failed); the route is done.",
        ),
        EventTypeSpec(
            "driver.status-updated",
            TOPIC_DRIVERS,
            DriverStatusUpdatedPayload,
            "A driver's duty status changed.",
        ),
        EventTypeSpec(
            "driver.location-updated",
            TOPIC_DRIVER_LOCATIONS,
            DriverLocationUpdatedPayload,
            "GPS telemetry for a driver (high volume; emitted by the simulator).",
        ),
        EventTypeSpec(
            "vehicle.status-updated",
            TOPIC_VEHICLES,
            VehicleStatusUpdatedPayload,
            "A vehicle's availability changed.",
        ),
        EventTypeSpec(
            "system.demo-reset",
            TOPIC_SYSTEM,
            DemoResetPayload,
            "The demo world was reset to its seed state.",
        ),
    ]


def _record_change_events() -> List[EventTypeSpec]:
    specs = []
    for entity in CDC_ENTITIES:
        for op in ("created", "updated", "deleted"):
            specs.append(
                EventTypeSpec(
                    f"{entity}.record-{op}",
                    TOPIC_CDC,
                    RecordChangePayload,
                    f"System-of-record observation: a {entity} row was {op} in Postgres "
                    "(captured by Debezium, normalized into the canonical envelope).",
                )
            )
    return specs


CATALOG: Dict[str, EventTypeSpec] = {
    spec.name: spec for spec in _business_events() + _record_change_events()
}


def spec_for(event_type: str) -> EventTypeSpec:
    """Look up an event type; raises KeyError for unregistered types."""
    return CATALOG[event_type]


def topic_for(event_type: str) -> str:
    return spec_for(event_type).topic
