"""Render EVENT-CATALOG.md from the code registry (core.catalog).

    python3 -m tools.render_catalog > ../../EVENT-CATALOG.md   (from server/app)

Run whenever the catalog changes so docs can't drift from code.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from core import catalog
from core.envelope import ENVELOPE_VERSION

EXAMPLES = {
    "order.created": {
        "orderId": "b1000000-0000-4000-8000-000000000005",
        "orderNumber": "ORD-1005",
        "customerId": "c1000000-0000-4000-8000-000000000009",
        "customerName": "Clarksville Floral Studio",
        "serviceLevel": "RUSH",
        "parcelCount": 1,
        "pickup": {
            "stopId": "b2000000-0000-4000-8000-000000000051",
            "kind": "PICKUP",
            "address": "2401 E 6th St, Austin, TX 78702",
            "location": {"latitude": 30.2601, "longitude": -97.7185},
            "windowStart": "2026-07-09T08:20:00Z",
            "windowEnd": "2026-07-09T10:20:00Z",
        },
        "delivery": {
            "stopId": "b2000000-0000-4000-8000-000000000052",
            "kind": "DELIVERY",
            "address": "600 Congress Ave, Austin, TX 78701",
            "location": {"latitude": 30.268, "longitude": -97.7431},
            "windowStart": "2026-07-09T09:20:00Z",
            "windowEnd": "2026-07-09T13:20:00Z",
        },
        "notes": "Deliver to loading dock",
    },
    "order.assigned": {
        "orderId": "b1000000-0000-4000-8000-000000000024",
        "orderNumber": "ORD-1024",
        "routeId": "a1000000-0000-4000-8000-000000000003",
        "routeNumber": "RT-103",
        "driverId": "d2000000-0000-4000-8000-000000000003",
        "vehicleId": "e1000000-0000-4000-8000-000000000003",
        "stops": [
            {"stopId": "b2000000-0000-4000-8000-000000000241", "kind": "PICKUP", "sequence": 11},
            {"stopId": "b2000000-0000-4000-8000-000000000242", "kind": "DELIVERY", "sequence": 12},
        ],
    },
    "order.completed": {
        "orderId": "b1000000-0000-4000-8000-000000000006",
        "orderNumber": "ORD-1006",
        "routeId": "a1000000-0000-4000-8000-000000000002",
    },
    "order.cancelled": {
        "orderId": "b1000000-0000-4000-8000-000000000028",
        "orderNumber": "ORD-1028",
        "reason": "Customer withdrew the order",
    },
    "stop.status-updated": {
        "stopId": "b2000000-0000-4000-8000-000000000061",
        "orderId": "b1000000-0000-4000-8000-000000000006",
        "routeId": "a1000000-0000-4000-8000-000000000002",
        "kind": "DELIVERY",
        "previousStatus": "ARRIVED",
        "status": "COMPLETED",
    },
    "route.planned": {
        "routeId": "a1000000-0000-4000-8000-000000000006",
        "routeNumber": "RT-106",
        "serviceDate": "2026-07-09",
        "driverId": "d2000000-0000-4000-8000-000000000006",
        "vehicleId": "e1000000-0000-4000-8000-000000000004",
        "stopCount": 0,
    },
    "route.started": {
        "routeId": "a1000000-0000-4000-8000-000000000003",
        "routeNumber": "RT-103",
        "driverId": "d2000000-0000-4000-8000-000000000003",
        "vehicleId": "e1000000-0000-4000-8000-000000000003",
    },
    "route.completed": {
        "routeId": "a1000000-0000-4000-8000-000000000001",
        "routeNumber": "RT-101",
    },
    "driver.status-updated": {
        "driverId": "d2000000-0000-4000-8000-000000000003",
        "driverName": "Aisha Johnson",
        "previousStatus": "AVAILABLE",
        "status": "ON_ROUTE",
    },
    "driver.location-updated": {
        "driverId": "d2000000-0000-4000-8000-000000000001",
        "vehicleId": "e1000000-0000-4000-8000-000000000001",
        "routeId": "a1000000-0000-4000-8000-000000000001",
        "location": {"latitude": 30.2712, "longitude": -97.7426},
        "speedMph": 35.0,
        "headingDeg": 312.5,
    },
    "vehicle.status-updated": {
        "vehicleId": "e1000000-0000-4000-8000-000000000005",
        "vehicleNumber": "BOX-105",
        "previousStatus": "AVAILABLE",
        "status": "MAINTENANCE",
    },
    "system.demo-reset": {
        "seedVersion": "austin-v1",
        "counts": {"orders": 30, "routes": 5, "drivers": 8, "vehicles": 5, "customers": 10, "parcels": 66, "stops": 60},
    },
}

RECORD_CHANGE_EXAMPLE = {
    "table": "orders",
    "op": "updated",
    "before": {"id": "b1000000-0000-4000-8000-000000000007", "status": "ASSIGNED", "order_number": "ORD-1007"},
    "after": {"id": "b1000000-0000-4000-8000-000000000007", "status": "IN_PROGRESS", "order_number": "ORD-1007"},
    "sourceTsMs": 1783000000000,
}


def envelope_wrap(event_type: str, payload: dict, source: str) -> dict:
    entity = event_type.split(".")[0]
    if entity == "system":
        refs = [{"type": "tenant", "id": "cxt-demo"}]
    else:
        refs = [{"type": entity, "id": payload.get(f"{entity}Id", f"{entity}-id-here")}]
    return {
        "eventId": "6f1c8e0a-9a1b-4c2d-8e3f-5a6b7c8d9e0f",
        "eventType": event_type,
        "eventVersion": ENVELOPE_VERSION,
        "sourceSystem": source,
        "tenantId": "cxt-demo",
        "entityRefs": refs,
        "occurredAt": "2026-07-09T14:03:22.120Z",
        "observedAt": "2026-07-09T14:03:22.140Z",
        "payload": payload,
        "traceId": "b2c4e6a8-1d3f-4a5b-9c8d-7e6f5a4b3c2d",
    }


def schema_table(model) -> str:
    schema = model.model_json_schema(by_alias=True)
    props = schema.get("properties", {})
    required = set(schema.get("required", []))
    defs = schema.get("$defs", {})

    def type_of(p: dict) -> str:
        if "$ref" in p:
            name = p["$ref"].split("/")[-1]
            return name
        if "anyOf" in p:
            parts = []
            for a in p["anyOf"]:
                if a.get("type") == "null":
                    continue
                parts.append(type_of(a))
            return " \\| ".join(parts) + " \\| null"
        t = p.get("type", "object")
        if t == "array":
            return f"array<{type_of(p.get('items', {}))}>"
        return t

    lines = ["| field | type | required |", "|---|---|---|"]
    for name, p in props.items():
        lines.append(f"| `{name}` | {type_of(p)} | {'yes' if name in required else 'no'} |")
    _ = defs
    return "\n".join(lines)


def main() -> None:
    business = [s for s in catalog.CATALOG.values() if not s.name.split(".", 1)[1].startswith("record-")]
    now = datetime.now(timezone.utc).date().isoformat()

    out = []
    w = out.append
    w("# Event Catalog — canonical envelope v1")
    w("")
    w("> Generated from `server/app/core/catalog.py` by `python -m tools.render_catalog`.")
    w(f"> Envelope version: **{ENVELOPE_VERSION}** · Last rendered: {now}")
    w("")
    w("Every event on every `lip.*` topic is wrapped in the same envelope. The publisher")
    w("(`server/app/eventbus/publisher.py`) validates both the envelope and the per-type")
    w("payload schema before anything reaches Kafka — malformed events are rejected at")
    w("publish time, never shipped.")
    w("")
    w("## The envelope")
    w("")
    w("```json")
    w(json.dumps(envelope_wrap("order.created", {"…": "event-type-specific payload, schemas below"}, "lip-api"), indent=2, ensure_ascii=False))
    w("```")
    w("")
    w("| field | meaning |")
    w("|---|---|")
    w("| `eventId` | unique id for this event (uuid4) |")
    w("| `eventType` | dot-namespaced `<entity>.<action>`, kebab-case (e.g. `stop.status-updated`) |")
    w("| `eventVersion` | schema version of this event type |")
    w("| `sourceSystem` | producer: `lip-api`, `lip-cdc-normalizer`, `lip-simulator`, `lip-seeder` |")
    w("| `tenantId` | tenant scoping anchor (demo world: `cxt-demo`) |")
    w("| `entityRefs` | typed refs to every canonical entity the event touches; first ref is the Kafka message key |")
    w("| `occurredAt` | when the fact happened (business time) |")
    w("| `observedAt` | when the backbone saw it (ingest time) |")
    w("| `payload` | event-type-specific body, schema below |")
    w("| `traceId` | correlates events caused by one action |")
    w("")
    w("## Topics")
    w("")
    w("| topic | carries |")
    w("|---|---|")
    for t in catalog.CANONICAL_TOPICS:
        carried = sorted({s.name for s in catalog.CATALOG.values() if s.topic == t})
        shown = ", ".join(f"`{c}`" for c in carried[:6])
        if len(carried) > 6:
            shown += f", … ({len(carried)} types)"
        w(f"| `{t}` | {shown} |")
    w("| `cdc.raw.public.*` | **envelope-exempt** raw Debezium change feed — the integration plane's inbox. Consumed only by the normalizer, which re-publishes everything as canonical `*.record-*` events on `lip.cdc`. |")
    w("")
    w("## Business + telemetry + system events")
    w("")
    for spec in business:
        w(f"### `{spec.name}`")
        w("")
        w(f"*Topic:* `{spec.topic}` · *Emitted by:* "
          + ("`lip-simulator`" if spec.name == "driver.location-updated"
             else "`lip-seeder`" if spec.name == "system.demo-reset"
             else "`lip-api` (and `lip-seeder` at reset)" if spec.name in ("order.created", "route.planned")
             else "`lip-api`"))
        w("")
        w(spec.description)
        w("")
        w("**Payload schema**")
        w("")
        w(schema_table(spec.payload_model))
        w("")
        if spec.name in EXAMPLES:
            w("**Example**")
            w("")
            w("```json")
            source = ("lip-simulator" if spec.name == "driver.location-updated"
                      else "lip-seeder" if spec.name == "system.demo-reset" else "lip-api")
            w(json.dumps(envelope_wrap(spec.name, EXAMPLES[spec.name], source), indent=2, ensure_ascii=False))
            w("```")
            w("")
    w("## Observation events (CDC record changes)")
    w("")
    w("One family, three actions per entity, all on `lip.cdc`, all emitted by")
    w("`lip-cdc-normalizer` from the raw Debezium feed:")
    w("")
    entities = ", ".join(f"`{e}`" for e in catalog.CDC_ENTITIES)
    w(f"- entities: {entities}")
    w("- actions: `record-created` (insert or snapshot read), `record-updated`, `record-deleted`")
    w("- i.e. `order.record-created`, `order.record-updated`, … `depot.record-deleted`"
      f" ({len(catalog.CDC_ENTITIES) * 3} registered types)")
    w("")
    w("These are *observations of the system of record*, distinct from the business")
    w("*intent* events above. `before`/`after` are source-shaped row images (snake_case")
    w("column names as they exist in Postgres); geography columns are decoded to")
    w("`{latitude, longitude}`.")
    w("")
    w("**Payload schema**")
    w("")
    w(schema_table(catalog.RecordChangePayload))
    w("")
    w("**Example** (`order.record-updated`)")
    w("")
    w("```json")
    w(json.dumps(envelope_wrap("order.record-updated", RECORD_CHANGE_EXAMPLE, "lip-cdc-normalizer"), indent=2, ensure_ascii=False))
    w("```")
    w("")
    w("## Validation guarantees")
    w("")
    w("- `eventType` must match `^[a-z-]+\\.[a-z-]+$` and be registered in the catalog")
    w("- payload must validate against the registered schema (unknown fields rejected)")
    w("- `entityRefs` must contain at least one typed ref; types are the closed set: "
      "order, stop, route, driver, vehicle, parcel, customer, depot, tenant")
    w("- timestamps must be timezone-aware UTC")
    w("- violations raise at publish time (`POST /api/events/publish` returns **422** — try it)")
    w("- `make audit` replays every canonical topic and re-validates every message")
    w("")
    print("\n".join(out))


if __name__ == "__main__":
    main()
