"""Contract tests for envelope v1 and the catalog — the load-bearing guarantees.

Run locally (no services needed):  cd server && pip install -r requirements.txt
                                   cd app && python -m pytest tests -q
"""
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from core import catalog
from core.envelope import EntityRef, EntityType, EventEnvelope, SourceSystem
from eventbus.publisher import EventValidationError, build_envelope

NOW = datetime(2026, 7, 9, 14, 0, 0, tzinfo=timezone.utc)


def valid_location_payload():
    return {
        "driverId": "d2000000-0000-4000-8000-000000000001",
        "vehicleId": None,
        "routeId": None,
        "location": {"latitude": 30.26, "longitude": -97.74},
        "speedMph": 30.0,
        "headingDeg": 90.0,
    }


def test_build_envelope_happy_path():
    env = build_envelope(
        "driver.location-updated",
        SourceSystem.SIMULATOR,
        [EntityRef(type=EntityType.DRIVER, id="d1")],
        valid_location_payload(),
        occurred_at=NOW,
    )
    wire = env.to_wire()
    assert wire["eventType"] == "driver.location-updated"
    assert wire["sourceSystem"] == "lip-simulator"
    assert wire["tenantId"] == "cxt-demo"
    assert wire["entityRefs"] == [{"type": "driver", "id": "d1"}]
    assert wire["occurredAt"] == "2026-07-09T14:00:00Z"
    assert wire["payload"]["location"]["latitude"] == 30.26
    assert set(wire) == {
        "eventId", "eventType", "eventVersion", "sourceSystem", "tenantId",
        "entityRefs", "occurredAt", "observedAt", "payload", "traceId",
    }


def test_unregistered_event_type_rejected():
    with pytest.raises(EventValidationError, match="not in the event catalog"):
        build_envelope(
            "order.teleported",
            SourceSystem.API,
            [EntityRef(type=EntityType.ORDER, id="o1")],
            {},
        )


def test_malformed_payload_rejected():
    with pytest.raises(EventValidationError, match="payload"):
        build_envelope(
            "driver.location-updated",
            SourceSystem.SIMULATOR,
            [EntityRef(type=EntityType.DRIVER, id="d1")],
            {"driverId": "d1"},  # missing location
        )


def test_unknown_payload_fields_rejected():
    payload = valid_location_payload()
    payload["surpriseField"] = 42
    with pytest.raises(EventValidationError):
        build_envelope(
            "driver.location-updated",
            SourceSystem.SIMULATOR,
            [EntityRef(type=EntityType.DRIVER, id="d1")],
            payload,
        )


def test_envelope_requires_entity_refs():
    with pytest.raises(ValidationError):
        EventEnvelope(
            event_type="system.demo-reset",
            source_system=SourceSystem.SEEDER,
            tenant_id="cxt-demo",
            entity_refs=[],
            occurred_at=NOW,
            payload={},
        )


def test_event_type_grammar_enforced():
    for bad in ("ORDER.CREATED", "order", "order.created.now", "order_created", "Order.created"):
        with pytest.raises(ValidationError):
            EventEnvelope(
                event_type=bad,
                source_system=SourceSystem.API,
                tenant_id="cxt-demo",
                entity_refs=[EntityRef(type=EntityType.ORDER, id="x")],
                occurred_at=NOW,
                payload={},
            )


def test_naive_timestamps_rejected():
    with pytest.raises(ValidationError, match="timezone-aware"):
        EventEnvelope(
            event_type="order.created",
            source_system=SourceSystem.API,
            tenant_id="cxt-demo",
            entity_refs=[EntityRef(type=EntityType.ORDER, id="x")],
            occurred_at=datetime(2026, 7, 9, 14, 0, 0),  # naive
            payload={},
        )


def test_wire_roundtrip():
    env = build_envelope(
        "driver.location-updated",
        SourceSystem.SIMULATOR,
        [EntityRef(type=EntityType.DRIVER, id="d1")],
        valid_location_payload(),
        occurred_at=NOW,
    )
    parsed = EventEnvelope.model_validate(env.to_wire())
    assert parsed.event_id == env.event_id
    assert parsed.event_type == env.event_type
    assert parsed.occurred_at == env.occurred_at


def test_every_catalog_topic_is_canonical():
    for spec in catalog.CATALOG.values():
        assert spec.topic in catalog.CANONICAL_TOPICS, spec.name


def test_catalog_covers_cdc_family():
    for entity in catalog.CDC_ENTITIES:
        for op in ("created", "updated", "deleted"):
            assert f"{entity}.record-{op}" in catalog.CATALOG


def test_record_change_payload_validates():
    build_envelope(
        "order.record-updated",
        SourceSystem.CDC_NORMALIZER,
        [EntityRef(type=EntityType.ORDER, id="o1")],
        {
            "table": "orders",
            "op": "updated",
            "before": {"id": "o1", "status": "ASSIGNED"},
            "after": {"id": "o1", "status": "IN_PROGRESS"},
            "sourceTsMs": 1234567890,
        },
        occurred_at=NOW,
    )
