# Event Catalog — canonical envelope v1

> Generated from `server/app/core/catalog.py` by `python -m tools.render_catalog`.
> Envelope version: **1.0** · Last rendered: 2026-07-10

Every event on every `lip.*` topic is wrapped in the same envelope. The publisher
(`server/app/eventbus/publisher.py`) validates both the envelope and the per-type
payload schema before anything reaches Kafka — malformed events are rejected at
publish time, never shipped.

## The envelope

```json
{
  "eventId": "6f1c8e0a-9a1b-4c2d-8e3f-5a6b7c8d9e0f",
  "eventType": "order.created",
  "eventVersion": "1.0",
  "sourceSystem": "lip-api",
  "tenantId": "cxt-demo",
  "entityRefs": [
    {
      "type": "order",
      "id": "order-id-here"
    }
  ],
  "occurredAt": "2026-07-09T14:03:22.120Z",
  "observedAt": "2026-07-09T14:03:22.140Z",
  "payload": {
    "…": "event-type-specific payload, schemas below"
  },
  "traceId": "b2c4e6a8-1d3f-4a5b-9c8d-7e6f5a4b3c2d"
}
```

| field | meaning |
|---|---|
| `eventId` | unique id for this event (uuid4) |
| `eventType` | dot-namespaced `<entity>.<action>`, kebab-case (e.g. `stop.status-updated`) |
| `eventVersion` | schema version of this event type |
| `sourceSystem` | producer: `lip-api`, `lip-cdc-normalizer`, `lip-simulator`, `lip-seeder` |
| `tenantId` | tenant scoping anchor (demo world: `cxt-demo`) |
| `entityRefs` | typed refs to every canonical entity the event touches; first ref is the Kafka message key |
| `occurredAt` | when the fact happened (business time) |
| `observedAt` | when the backbone saw it (ingest time) |
| `payload` | event-type-specific body, schema below |
| `traceId` | correlates events caused by one action |

## Topics

| topic | carries |
|---|---|
| `lip.orders` | `order.assigned`, `order.cancelled`, `order.completed`, `order.created` |
| `lip.stops` | `stop.status-updated` |
| `lip.routes` | `route.completed`, `route.planned`, `route.started` |
| `lip.drivers` | `driver.status-updated` |
| `lip.drivers.locations` | `driver.location-updated` |
| `lip.vehicles` | `vehicle.status-updated` |
| `lip.cdc` | `customer.record-created`, `customer.record-deleted`, `customer.record-updated`, `depot.record-created`, `depot.record-deleted`, `depot.record-updated`, … (24 types) |
| `lip.system` | `system.demo-reset` |
| `cdc.raw.public.*` | **envelope-exempt** raw Debezium change feed — the integration plane's inbox. Consumed only by the normalizer, which re-publishes everything as canonical `*.record-*` events on `lip.cdc`. |

## Business + telemetry + system events

### `order.created`

*Topic:* `lip.orders` · *Emitted by:* `lip-api` (and `lip-seeder` at reset)

A new order was placed; its pickup and delivery stops now exist.

**Payload schema**

| field | type | required |
|---|---|---|
| `orderId` | string | yes |
| `orderNumber` | string | yes |
| `customerId` | string | yes |
| `customerName` | string | yes |
| `parcelCount` | integer | yes |
| `pickup` | StopSnapshot | yes |
| `delivery` | StopSnapshot | yes |
| `notes` | string \| null | no |

**Example**

```json
{
  "eventId": "6f1c8e0a-9a1b-4c2d-8e3f-5a6b7c8d9e0f",
  "eventType": "order.created",
  "eventVersion": "1.0",
  "sourceSystem": "lip-api",
  "tenantId": "cxt-demo",
  "entityRefs": [
    {
      "type": "order",
      "id": "b1000000-0000-4000-8000-000000000005"
    }
  ],
  "occurredAt": "2026-07-09T14:03:22.120Z",
  "observedAt": "2026-07-09T14:03:22.140Z",
  "payload": {
    "orderId": "b1000000-0000-4000-8000-000000000005",
    "orderNumber": "ORD-1005",
    "customerId": "c1000000-0000-4000-8000-000000000009",
    "customerName": "Clarksville Floral Studio",
    "parcelCount": 1,
    "pickup": {
      "stopId": "b2000000-0000-4000-8000-000000000051",
      "kind": "PICKUP",
      "address": "2401 E 6th St, Austin, TX 78702",
      "location": {
        "latitude": 30.2601,
        "longitude": -97.7185
      },
      "windowStart": "2026-07-09T08:20:00Z",
      "windowEnd": "2026-07-09T10:20:00Z"
    },
    "delivery": {
      "stopId": "b2000000-0000-4000-8000-000000000052",
      "kind": "DELIVERY",
      "address": "600 Congress Ave, Austin, TX 78701",
      "location": {
        "latitude": 30.268,
        "longitude": -97.7431
      },
      "windowStart": "2026-07-09T09:20:00Z",
      "windowEnd": "2026-07-09T13:20:00Z"
    },
    "notes": "Deliver to loading dock"
  },
  "traceId": "b2c4e6a8-1d3f-4a5b-9c8d-7e6f5a4b3c2d"
}
```

### `order.assigned`

*Topic:* `lip.orders` · *Emitted by:* `lip-api`

An order's stops were attached to a route (and thereby a driver/vehicle).

**Payload schema**

| field | type | required |
|---|---|---|
| `orderId` | string | yes |
| `orderNumber` | string | yes |
| `routeId` | string | yes |
| `routeNumber` | string | yes |
| `driverId` | string \| null | no |
| `vehicleId` | string \| null | no |

**Example**

```json
{
  "eventId": "6f1c8e0a-9a1b-4c2d-8e3f-5a6b7c8d9e0f",
  "eventType": "order.assigned",
  "eventVersion": "1.0",
  "sourceSystem": "lip-api",
  "tenantId": "cxt-demo",
  "entityRefs": [
    {
      "type": "order",
      "id": "b1000000-0000-4000-8000-000000000024"
    }
  ],
  "occurredAt": "2026-07-09T14:03:22.120Z",
  "observedAt": "2026-07-09T14:03:22.140Z",
  "payload": {
    "orderId": "b1000000-0000-4000-8000-000000000024",
    "orderNumber": "ORD-1024",
    "routeId": "a1000000-0000-4000-8000-000000000003",
    "routeNumber": "RT-103",
    "driverId": "d2000000-0000-4000-8000-000000000003",
    "vehicleId": "e1000000-0000-4000-8000-000000000003"
  },
  "traceId": "b2c4e6a8-1d3f-4a5b-9c8d-7e6f5a4b3c2d"
}
```

### `order.completed`

*Topic:* `lip.orders` · *Emitted by:* `lip-api`

The order's delivery stop completed; the order is done.

**Payload schema**

| field | type | required |
|---|---|---|
| `orderId` | string | yes |
| `orderNumber` | string | yes |
| `routeId` | string \| null | no |

**Example**

```json
{
  "eventId": "6f1c8e0a-9a1b-4c2d-8e3f-5a6b7c8d9e0f",
  "eventType": "order.completed",
  "eventVersion": "1.0",
  "sourceSystem": "lip-api",
  "tenantId": "cxt-demo",
  "entityRefs": [
    {
      "type": "order",
      "id": "b1000000-0000-4000-8000-000000000006"
    }
  ],
  "occurredAt": "2026-07-09T14:03:22.120Z",
  "observedAt": "2026-07-09T14:03:22.140Z",
  "payload": {
    "orderId": "b1000000-0000-4000-8000-000000000006",
    "orderNumber": "ORD-1006",
    "routeId": "a1000000-0000-4000-8000-000000000002"
  },
  "traceId": "b2c4e6a8-1d3f-4a5b-9c8d-7e6f5a4b3c2d"
}
```

### `order.cancelled`

*Topic:* `lip.orders` · *Emitted by:* `lip-api`

The order was cancelled; its pending stops were withdrawn.

**Payload schema**

| field | type | required |
|---|---|---|
| `orderId` | string | yes |
| `orderNumber` | string | yes |
| `reason` | string \| null | no |

**Example**

```json
{
  "eventId": "6f1c8e0a-9a1b-4c2d-8e3f-5a6b7c8d9e0f",
  "eventType": "order.cancelled",
  "eventVersion": "1.0",
  "sourceSystem": "lip-api",
  "tenantId": "cxt-demo",
  "entityRefs": [
    {
      "type": "order",
      "id": "b1000000-0000-4000-8000-000000000028"
    }
  ],
  "occurredAt": "2026-07-09T14:03:22.120Z",
  "observedAt": "2026-07-09T14:03:22.140Z",
  "payload": {
    "orderId": "b1000000-0000-4000-8000-000000000028",
    "orderNumber": "ORD-1028",
    "reason": "Customer withdrew the order"
  },
  "traceId": "b2c4e6a8-1d3f-4a5b-9c8d-7e6f5a4b3c2d"
}
```

### `stop.status-updated`

*Topic:* `lip.stops` · *Emitted by:* `lip-api`

A stop moved through its lifecycle: PENDING -> ARRIVED -> COMPLETED (or FAILED).

**Payload schema**

| field | type | required |
|---|---|---|
| `stopId` | string | yes |
| `orderId` | string | yes |
| `routeId` | string \| null | no |
| `kind` | string | yes |
| `previousStatus` | string | yes |
| `status` | string | yes |

**Example**

```json
{
  "eventId": "6f1c8e0a-9a1b-4c2d-8e3f-5a6b7c8d9e0f",
  "eventType": "stop.status-updated",
  "eventVersion": "1.0",
  "sourceSystem": "lip-api",
  "tenantId": "cxt-demo",
  "entityRefs": [
    {
      "type": "stop",
      "id": "b2000000-0000-4000-8000-000000000061"
    }
  ],
  "occurredAt": "2026-07-09T14:03:22.120Z",
  "observedAt": "2026-07-09T14:03:22.140Z",
  "payload": {
    "stopId": "b2000000-0000-4000-8000-000000000061",
    "orderId": "b1000000-0000-4000-8000-000000000006",
    "routeId": "a1000000-0000-4000-8000-000000000002",
    "kind": "DELIVERY",
    "previousStatus": "ARRIVED",
    "status": "COMPLETED"
  },
  "traceId": "b2c4e6a8-1d3f-4a5b-9c8d-7e6f5a4b3c2d"
}
```

### `route.planned`

*Topic:* `lip.routes` · *Emitted by:* `lip-api` (and `lip-seeder` at reset)

A route was created/planned for a service date.

**Payload schema**

| field | type | required |
|---|---|---|
| `routeId` | string | yes |
| `routeNumber` | string | yes |
| `serviceDate` | string | yes |
| `driverId` | string \| null | no |
| `vehicleId` | string \| null | no |
| `stopCount` | integer | yes |

**Example**

```json
{
  "eventId": "6f1c8e0a-9a1b-4c2d-8e3f-5a6b7c8d9e0f",
  "eventType": "route.planned",
  "eventVersion": "1.0",
  "sourceSystem": "lip-api",
  "tenantId": "cxt-demo",
  "entityRefs": [
    {
      "type": "route",
      "id": "a1000000-0000-4000-8000-000000000006"
    }
  ],
  "occurredAt": "2026-07-09T14:03:22.120Z",
  "observedAt": "2026-07-09T14:03:22.140Z",
  "payload": {
    "routeId": "a1000000-0000-4000-8000-000000000006",
    "routeNumber": "RT-106",
    "serviceDate": "2026-07-09",
    "driverId": "d2000000-0000-4000-8000-000000000006",
    "vehicleId": "e1000000-0000-4000-8000-000000000004",
    "stopCount": 0
  },
  "traceId": "b2c4e6a8-1d3f-4a5b-9c8d-7e6f5a4b3c2d"
}
```

### `route.started`

*Topic:* `lip.routes` · *Emitted by:* `lip-api`

A route went ACTIVE; its driver is now driving it.

**Payload schema**

| field | type | required |
|---|---|---|
| `routeId` | string | yes |
| `routeNumber` | string | yes |
| `driverId` | string \| null | no |
| `vehicleId` | string \| null | no |

**Example**

```json
{
  "eventId": "6f1c8e0a-9a1b-4c2d-8e3f-5a6b7c8d9e0f",
  "eventType": "route.started",
  "eventVersion": "1.0",
  "sourceSystem": "lip-api",
  "tenantId": "cxt-demo",
  "entityRefs": [
    {
      "type": "route",
      "id": "a1000000-0000-4000-8000-000000000003"
    }
  ],
  "occurredAt": "2026-07-09T14:03:22.120Z",
  "observedAt": "2026-07-09T14:03:22.140Z",
  "payload": {
    "routeId": "a1000000-0000-4000-8000-000000000003",
    "routeNumber": "RT-103",
    "driverId": "d2000000-0000-4000-8000-000000000003",
    "vehicleId": "e1000000-0000-4000-8000-000000000003"
  },
  "traceId": "b2c4e6a8-1d3f-4a5b-9c8d-7e6f5a4b3c2d"
}
```

### `route.completed`

*Topic:* `lip.routes` · *Emitted by:* `lip-api`

All stops on the route are completed (or failed); the route is done.

**Payload schema**

| field | type | required |
|---|---|---|
| `routeId` | string | yes |
| `routeNumber` | string | yes |

**Example**

```json
{
  "eventId": "6f1c8e0a-9a1b-4c2d-8e3f-5a6b7c8d9e0f",
  "eventType": "route.completed",
  "eventVersion": "1.0",
  "sourceSystem": "lip-api",
  "tenantId": "cxt-demo",
  "entityRefs": [
    {
      "type": "route",
      "id": "a1000000-0000-4000-8000-000000000001"
    }
  ],
  "occurredAt": "2026-07-09T14:03:22.120Z",
  "observedAt": "2026-07-09T14:03:22.140Z",
  "payload": {
    "routeId": "a1000000-0000-4000-8000-000000000001",
    "routeNumber": "RT-101"
  },
  "traceId": "b2c4e6a8-1d3f-4a5b-9c8d-7e6f5a4b3c2d"
}
```

### `driver.status-updated`

*Topic:* `lip.drivers` · *Emitted by:* `lip-api`

A driver's duty status changed.

**Payload schema**

| field | type | required |
|---|---|---|
| `driverId` | string | yes |
| `driverName` | string | yes |
| `previousStatus` | string | yes |
| `status` | string | yes |

**Example**

```json
{
  "eventId": "6f1c8e0a-9a1b-4c2d-8e3f-5a6b7c8d9e0f",
  "eventType": "driver.status-updated",
  "eventVersion": "1.0",
  "sourceSystem": "lip-api",
  "tenantId": "cxt-demo",
  "entityRefs": [
    {
      "type": "driver",
      "id": "d2000000-0000-4000-8000-000000000003"
    }
  ],
  "occurredAt": "2026-07-09T14:03:22.120Z",
  "observedAt": "2026-07-09T14:03:22.140Z",
  "payload": {
    "driverId": "d2000000-0000-4000-8000-000000000003",
    "driverName": "Aisha Johnson",
    "previousStatus": "AVAILABLE",
    "status": "ON_ROUTE"
  },
  "traceId": "b2c4e6a8-1d3f-4a5b-9c8d-7e6f5a4b3c2d"
}
```

### `driver.location-updated`

*Topic:* `lip.drivers.locations` · *Emitted by:* `lip-simulator`

GPS telemetry for a driver (high volume; emitted by the simulator).

**Payload schema**

| field | type | required |
|---|---|---|
| `driverId` | string | yes |
| `vehicleId` | string \| null | no |
| `routeId` | string \| null | no |
| `location` | GeoPoint | yes |
| `speedMph` | number \| null | no |
| `headingDeg` | number \| null | no |

**Example**

```json
{
  "eventId": "6f1c8e0a-9a1b-4c2d-8e3f-5a6b7c8d9e0f",
  "eventType": "driver.location-updated",
  "eventVersion": "1.0",
  "sourceSystem": "lip-simulator",
  "tenantId": "cxt-demo",
  "entityRefs": [
    {
      "type": "driver",
      "id": "d2000000-0000-4000-8000-000000000001"
    }
  ],
  "occurredAt": "2026-07-09T14:03:22.120Z",
  "observedAt": "2026-07-09T14:03:22.140Z",
  "payload": {
    "driverId": "d2000000-0000-4000-8000-000000000001",
    "vehicleId": "e1000000-0000-4000-8000-000000000001",
    "routeId": "a1000000-0000-4000-8000-000000000001",
    "location": {
      "latitude": 30.2712,
      "longitude": -97.7426
    },
    "speedMph": 35.0,
    "headingDeg": 312.5
  },
  "traceId": "b2c4e6a8-1d3f-4a5b-9c8d-7e6f5a4b3c2d"
}
```

### `vehicle.status-updated`

*Topic:* `lip.vehicles` · *Emitted by:* `lip-api`

A vehicle's availability changed.

**Payload schema**

| field | type | required |
|---|---|---|
| `vehicleId` | string | yes |
| `vehicleNumber` | string | yes |
| `previousStatus` | string | yes |
| `status` | string | yes |

**Example**

```json
{
  "eventId": "6f1c8e0a-9a1b-4c2d-8e3f-5a6b7c8d9e0f",
  "eventType": "vehicle.status-updated",
  "eventVersion": "1.0",
  "sourceSystem": "lip-api",
  "tenantId": "cxt-demo",
  "entityRefs": [
    {
      "type": "vehicle",
      "id": "e1000000-0000-4000-8000-000000000005"
    }
  ],
  "occurredAt": "2026-07-09T14:03:22.120Z",
  "observedAt": "2026-07-09T14:03:22.140Z",
  "payload": {
    "vehicleId": "e1000000-0000-4000-8000-000000000005",
    "vehicleNumber": "BOX-105",
    "previousStatus": "AVAILABLE",
    "status": "MAINTENANCE"
  },
  "traceId": "b2c4e6a8-1d3f-4a5b-9c8d-7e6f5a4b3c2d"
}
```

### `system.demo-reset`

*Topic:* `lip.system` · *Emitted by:* `lip-seeder`

The demo world was reset to its seed state.

**Payload schema**

| field | type | required |
|---|---|---|
| `seedVersion` | string | yes |
| `counts` | object | yes |

**Example**

```json
{
  "eventId": "6f1c8e0a-9a1b-4c2d-8e3f-5a6b7c8d9e0f",
  "eventType": "system.demo-reset",
  "eventVersion": "1.0",
  "sourceSystem": "lip-seeder",
  "tenantId": "cxt-demo",
  "entityRefs": [
    {
      "type": "tenant",
      "id": "cxt-demo"
    }
  ],
  "occurredAt": "2026-07-09T14:03:22.120Z",
  "observedAt": "2026-07-09T14:03:22.140Z",
  "payload": {
    "seedVersion": "austin-v1",
    "counts": {
      "orders": 30,
      "routes": 5,
      "drivers": 8,
      "vehicles": 5,
      "customers": 10,
      "parcels": 66,
      "stops": 60
    }
  },
  "traceId": "b2c4e6a8-1d3f-4a5b-9c8d-7e6f5a4b3c2d"
}
```

## Observation events (CDC record changes)

One family, three actions per entity, all on `lip.cdc`, all emitted by
`lip-cdc-normalizer` from the raw Debezium feed:

- entities: `order`, `stop`, `route`, `driver`, `vehicle`, `parcel`, `customer`, `depot`
- actions: `record-created` (insert or snapshot read), `record-updated`, `record-deleted`
- i.e. `order.record-created`, `order.record-updated`, … `depot.record-deleted` (24 registered types)

These are *observations of the system of record*, distinct from the business
*intent* events above. `before`/`after` are source-shaped row images (snake_case
column names as they exist in Postgres); geography columns are decoded to
`{latitude, longitude}`.

**Payload schema**

| field | type | required |
|---|---|---|
| `table` | string | yes |
| `op` | string | yes |
| `before` | object \| null | no |
| `after` | object \| null | no |
| `sourceTsMs` | integer \| null | no |

**Example** (`order.record-updated`)

```json
{
  "eventId": "6f1c8e0a-9a1b-4c2d-8e3f-5a6b7c8d9e0f",
  "eventType": "order.record-updated",
  "eventVersion": "1.0",
  "sourceSystem": "lip-cdc-normalizer",
  "tenantId": "cxt-demo",
  "entityRefs": [
    {
      "type": "order",
      "id": "order-id-here"
    }
  ],
  "occurredAt": "2026-07-09T14:03:22.120Z",
  "observedAt": "2026-07-09T14:03:22.140Z",
  "payload": {
    "table": "orders",
    "op": "updated",
    "before": {
      "id": "b1000000-0000-4000-8000-000000000007",
      "status": "ASSIGNED",
      "order_number": "ORD-1007"
    },
    "after": {
      "id": "b1000000-0000-4000-8000-000000000007",
      "status": "IN_PROGRESS",
      "order_number": "ORD-1007"
    },
    "sourceTsMs": 1783000000000
  },
  "traceId": "b2c4e6a8-1d3f-4a5b-9c8d-7e6f5a4b3c2d"
}
```

## Validation guarantees

- `eventType` must match `^[a-z-]+\.[a-z-]+$` and be registered in the catalog
- payload must validate against the registered schema (unknown fields rejected)
- `entityRefs` must contain at least one typed ref; types are the closed set: order, stop, route, driver, vehicle, parcel, customer, depot, tenant
- timestamps must be timezone-aware UTC
- violations raise at publish time (`POST /api/events/publish` returns **422** — try it)
- `make audit` replays every canonical topic and re-validates every message

