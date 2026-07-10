# Architecture — the LIP proof-of-concept as seven planes

This repo is a demo-scale proof of the **Logistics Intelligence Platform (LIP)**
pattern: one canonical event backbone feeding a live, multi-projection world
model, with every mutation flowing through an API that narrates what it does as
events. It is deliberately small — every plane below exists in miniature so the
*concepts* can be walked through in code.

The plane vocabulary comes from the LIP vision ("Seven Planes"); each section
says what the plane means at maturity and what stands in for it here.

```
                 ┌─────────────────────────────────────────────────────────┐
                 │                  EXPERIENCE  (React UI)                  │
                 │   dispatch map · orders · event console · analytics     │
                 └──────────────▲────────────────────▲─────────────────────┘
                        REST /api│              WS /ws│ (envelopes, verbatim)
                 ┌──────────────┴────────────────────┴─────────────────────┐
   ACTION        │                 FastAPI  (server/app)                   │
   (governed     │   mutations write Postgres + emit canonical events      │
    mutations)   └───────▲──────────────────────────────────┬──────────────┘
                         │ SQL                              │ publish (validated)
                 ┌───────┴────────┐                ┌────────▼─────────────────────┐
   WORLD MODEL   │ Postgres       │   Debezium     │ Kafka — canonical backbone   │
   (system of    │ (PostGIS)      ├───────────────►│  lip.orders lip.stops        │
    record +     │ orders stops   │  cdc.raw.*     │  lip.routes lip.drivers      │
    projections) │ routes drivers │  (raw inbox)   │  lip.drivers.locations       │
                 │ vehicles ...   │       │        │  lip.vehicles lip.cdc        │
                 └───────▲────────┘       │        │  lip.system                  │
                         │                ▼        └───────┬──────────┬───────────┘
                         │       ┌──────────────┐          │          │
   INTEGRATION           │       │ normalizer   ├──────────┘          │
   (CDC → canonical)     │       │ (worker)     │  *.record-* events  │
                         │       └──────────────┘                     │
                 ┌───────┴──────────────────────────────┐    ┌────────▼──────────┐
   PERCEPTION    │ simulator (worker)                   │    │ projector (worker)│
   (telemetry)   │ drives ACTIVE routes, emits          │    │ event_stream +    │
                 │ driver.location-updated, walks stops │    │ driver_locations  │
                 │ through the API like a driver app    │    │ (TimescaleDB) and │
                 └──────────────────────────────────────┘    │ the Neo4j graph   │
                                                             └───────────────────┘
```

## 1. Integration & Data Plane — "every event once, in order, forever replayable"

**The idea.** One canonical event contract carries every operational fact over a
streaming backbone; the event log is the platform's memory, and any projection
can be rebuilt from replay.

**Here.** Kafka in KRaft mode (no ZooKeeper) with **auto-topic-creation
disabled** — the eight `lip.*` topics are created deliberately by `kafka-init`
([server/app/tools/create_topics.py](server/app/tools/create_topics.py)) and
nothing else may appear. The contract is **envelope v1**
([server/app/core/envelope.py](server/app/core/envelope.py)); the registry of
event types, payload schemas, and topic routing is
[server/app/core/catalog.py](server/app/core/catalog.py), mirrored 1:1 in
[EVENT-CATALOG.md](EVENT-CATALOG.md). Publish-side validation
([server/app/eventbus/publisher.py](server/app/eventbus/publisher.py)) rejects
anything malformed before it reaches a topic, and `make audit` replays every
topic to prove the guarantee held.

Change data capture is the second ingestion mode: Debezium streams every
Postgres row change to the `cdc.raw.public.*` topics (source-shaped, documented
as the *inbox*, never consumed by application code), and the **normalizer**
worker ([server/app/workers/normalizer.py](server/app/workers/normalizer.py))
republishes each change as a canonical `<entity>.record-created|updated|deleted`
event on `lip.cdc`. Edit a row in psql and watch it surface on the backbone —
that is the integration plane's whole pitch in one trick.

## 2. World Model Plane — the ontology made live

**The idea.** A canonical ontology (objects, identities, relationships,
lifecycle) continuously projected into fit-for-purpose read models; the twin
answers *what is happening and what does it affect*, seconds fresh.

**Here.** The canonical vocabulary is load-bearing and used everywhere — code,
schema, topics, UI: **Customer, Order, Stop, Route, Driver, Vehicle, Parcel,
Depot**. The invariants are enforced by the Postgres schema
([server/database/postgres/init.sql](server/database/postgres/init.sql)):

- an **order** has exactly two **stops** — one `PICKUP`, one `DELIVERY`
  (`UNIQUE (order_id, kind)`)
- **stops belong to routes**: assigning an order sets `route_id` + `sequence`
  on its stops; unrouted orders have stops with `route_id NULL`
- **parcels belong to orders**

Postgres is the system of record. Two further projections are maintained *from
events* by the projector: **TimescaleDB** (`event_stream` — every envelope,
queryable; `driver_locations` — telemetry hypertable) and **Neo4j** — the world
model as a graph (`(:Customer)-[:PLACED]->(:Order)`,
`(:Route)-[:HAS_STOP]->(:Stop)-[:FOR_ORDER]->(:Order)`,
`(:Route)-[:ASSIGNED_TO]->(:Driver)` …). The graph earns its keep at
`GET /api/graph/impact/driver/{id}`: "if this driver goes down, which routes,
stops, orders, and customers are affected" is one traversal (surfaced in the UI
as the **Impact** button on the Drivers page).

## 3. Perception Plane — the platform's senses

**The idea.** Everything the physical world emits (GPS, scans, photos, sensor
series) becomes typed events on the same contract.

**Here.** The **simulator**
([server/app/workers/simulator.py](server/app/workers/simulator.py)) stands in
for the driver app + telematics: it moves drivers along their ACTIVE routes at
city speeds (time-scaled), emits `driver.location-updated` telemetry through
the same validated publisher as every other producer, and on arrival walks each
stop through `ARRIVED → COMPLETED` **via the API** — so business events, CDC
observations, and projections all fire exactly as they would for a real driver.
Reading its itinerary straight from Postgres is the one documented shortcut.

## 4. Intelligence Plane — models, inference, projection

**The idea.** Forecasting, ETA prediction, optimization, and simulation served
against the twin, with every model output an event with lineage.

**Here.** Deliberately thin — this POC stabilizes the substrate intelligence
will stand on. What exists: seed routes are sequenced by a nearest-neighbor
heuristic ([scripts/generate_seed.py](scripts/generate_seed.py)), and the
analytics endpoints compute honest aggregates over the event log and world
model. The pattern to note: anything the intelligence plane will ever produce
(an ETA, a recommendation) is just another envelope on the backbone.

## 5. Action Plane — governed verbs

**The idea.** Every business mutation is a governed verb: preconditions,
validation, and a durable, explainable trail.

**Here.** The FastAPI service ([server/app/main.py](server/app/main.py)) is the
only writer of the world model. Each mutation in
[server/app/services/world.py](server/app/services/world.py) follows one
discipline — *check preconditions → write Postgres → emit the intent event* —
and state machines are enforced (`PENDING → ARRIVED → COMPLETED` for stops;
only `CREATED` orders can be assigned; a route needs a driver, vehicle, and
stops to start). Completing a delivery stop cascades: parcels delivered → order
completed → route completed → driver and vehicle released — each step narrated
as an event. `POST /api/events/publish` demonstrates the boundary: malformed
events get a 422 and never reach Kafka.

## 6. Trust Plane — chain of custody, evidence, transparency

**The idea.** The platform shows its work — physical custody, decision custody,
evidence integrity.

**Here.** The seeds of it: every envelope carries `occurredAt` vs `observedAt`
(honest time semantics), a `traceId` correlating everything one action caused,
and `entityRefs` tying events to the objects they touched. The `event_stream`
projection is the queryable audit trail (the Event Console reads it), and
`make audit` is a trust operation: prove the entire backbone conforms to the
published contract. Parcel-level custody objects (scans, photos, signatures)
are future series material.

## 7. Experience Plane — surfaces that carry decisions

**The idea.** Intelligence appears inside the workflows people already live in.

**Here.** The React UI ([ui/](ui/)): the **Dispatch Board** — three panels
(unassigned queue with time-window urgency, live Austin map, drivers & routes)
whose state is a **client-side projection**: a REST snapshot folded forward by
canonical events via a pure reducer ([ui/src/world/reduce.js](ui/src/world/reduce.js)).
Actions POST to the API and then *wait for their own events* — no
write-then-refetch, which is the experience-plane version of the platform's
core claim. Plus **Order entry** (service levels ROUTINE/RUSH/STAT, address-book
"geocoding" against the seeded city), **Order detail** (lifecycle, stops with
manual dev controls, parcels, and the per-order **event tail** — the embryo of
the evidence timeline), **Drivers** (graph-powered Impact view), **Fleet**,
**Dashboard**, **Analytics**, and the **Event Console** — the contract made
visible: filter the live backbone, expand any envelope, and publish test events
(valid and invalid) to see validation work. The UI receives events over `/ws`
verbatim in wire form; what you see is byte-for-byte what consumers see.

## The services (docker-compose.yml)

| service | plane | what it does |
|---|---|---|
| `postgres` | world model | system of record (PostGIS), seeded deterministic Austin world |
| `timescaledb` | world model | `event_stream` + `driver_locations` projections |
| `neo4j` | world model | graph projection (relationships, blast radius) |
| `kafka` | integration | the canonical backbone (KRaft, no auto-create) |
| `kafka-init` | integration | one-shot: creates the eight `lip.*` topics |
| `debezium` + `debezium-init` | integration | CDC from Postgres to `cdc.raw.*` |
| `api` | action + experience | REST + WebSocket gateway; the only world-model writer |
| `normalizer` | integration | `cdc.raw.*` → canonical `*.record-*` events |
| `projector` | world model | events → Timescale + Neo4j (+ current locations) |
| `simulator` | perception | drives routes, emits telemetry, works stops via the API |
| `ui` | experience | React app behind nginx (same-origin `/api` + `/ws`) |
| `kafka-ui` | operator tool | inspect topics/messages at :8080 |
| `pgadmin` | operator tool (profile `tools`) | poke the databases at :5050 |

## Design decisions worth knowing

- **Intent vs observation.** The API emits *intent* (`order.created`); CDC emits
  *observation* (`order.record-created`). Both are canonical, distinguishable by
  `sourceSystem` and name. Consumers choose their stream; the Event Console
  shows both.
- **`cdc.raw.*` is not canonical, on purpose.** Debezium's own format is treated
  as source material (like the WAL itself). The audit script classifies it as
  the documented inbox and fails on any *other* non-canonical topic. Demo reset
  recreates the `lip.*` namespace but leaves the inbox alone — deleting a live
  connector's topics wedges its producer, and source material isn't state.
- **Projections replay.** The projector runs without a consumer group and
  re-reads the whole backbone on every start; its writes are idempotent
  (unique `(time, event_id)` + Cypher `MERGE`). Kill it, wipe its stores,
  restart it — everything rebuilds from the log. Demo reset leans on exactly
  this property.
- **No Flink.** The previous Flink cluster ran zero jobs. Stream processing is
  the projector worker — a plain Python consumer you can read in one sitting,
  which is the point of a teaching POC. Swapping it for Flink/Kafka Streams
  later changes the *how*, not the contract.
- **Location writes are rate-limited.** Telemetry flows at full rate into
  TimescaleDB; the world model's `current_location` is refreshed every ~10s per
  driver so the CDC echo stays readable.
- **Determinism over realism.** Fixed UUIDs, fixed names, windows relative to
  `CURRENT_DATE`. `make reset` lands on the identical world every time, in
  under a minute.
