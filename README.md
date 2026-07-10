# cxt-skunkworks — Logistics Intelligence Platform (POC)

A demo-scale proof of the **LIP pattern**: a deterministic courier world
(Austin, TX) whose every change flows through **one canonical event envelope**
over Kafka — API intent events, Debezium CDC observations, and simulator
telemetry alike — projected live into Postgres, TimescaleDB, and Neo4j, with a
React dispatch UI on top.

This is a teaching/demo POC, not production: optimized for demo reliability,
code clarity, and concept fidelity. Start with [ARCHITECTURE.md](ARCHITECTURE.md)
(the system as seven planes), [EVENT-CATALOG.md](EVENT-CATALOG.md) (the
contract), and [DEMO-NOTES.md](DEMO-NOTES.md) (what to show and how).

## Quickstart

Prerequisites: Docker Desktop (or Docker Engine + Compose v2), `make`, and
~6 GB free RAM for the stack.

```bash
git clone <this-repo>
cd cxt-skunkworks
export GOOGLE_MAPS_API_KEY=...   # optional — map tiles; everything else works without it
make up          # builds images, starts everything in dependency order, waits until healthy
```

> The Maps JS key is the only optional ingredient: without it the dispatch map
> shows a fallback panel while every other surface (orders, events, analytics,
> graph) works fully. Put it in the environment (above) or in a git-ignored
> `ui/.env` as `REACT_APP_GOOGLE_MAPS_API_KEY=...`.

First run takes a few minutes (image builds + healthcheck-gated startup). When
`make up` prints the URL block, open:

| URL | What |
|---|---|
| http://localhost:3000 | **The demo UI** — dispatch map over the seeded world |
| http://localhost:8000/docs | API (OpenAPI) |
| http://localhost:8080 | Kafka UI — topics and raw envelopes |
| http://localhost:7474 | Neo4j browser (`neo4j` / `lip_graph_password`) |

You should see two routes already mid-shift with drivers moving on the map.
No `.env` files, no manual steps — if you needed a second command, that's a bug.

> Plain `docker compose up -d --build` works too; `make up` just adds the
> wait-for-healthy and the URL summary.

## The three commands that matter

```bash
make reset    # demo reset: every store, topic, and projection back to the seed
              # world (austin-v1) in under a minute — run before every demo
make audit    # prove every event on every canonical topic conforms to envelope v1
make test     # contract unit tests (envelope + catalog) inside the api container
```

All targets: `make help`.

## The world

One tenant (`cxt-demo`), one depot, 10 customers, **8 drivers, 5 vehicles,
5 routes, 30 orders** (66 parcels) across Austin. Deterministic: same IDs,
names, and coordinates every reset; stop time-windows are relative to today so
the world never looks stale. The world is defined in
[`scripts/generate_seed.py`](scripts/generate_seed.py) → committed as
[`server/database/postgres/seed.sql`](server/database/postgres/seed.sql)
(`make seed-regen` after editing the generator).

## Canonical vocabulary (load-bearing)

**Customer · Order · Stop · Route · Driver · Vehicle · Parcel · Depot** —
orders have a pickup stop and a delivery stop; stops belong to routes; parcels
belong to orders. This vocabulary is used identically in the schema, the API,
the events, and the UI.

## Canonical events (the contract)

Every event on every `lip.*` topic is an **envelope v1**:

```json
{
  "eventId": "…", "eventType": "order.created", "eventVersion": "1.0",
  "sourceSystem": "lip-api", "tenantId": "cxt-demo",
  "entityRefs": [{"type": "order", "id": "…"}],
  "occurredAt": "…", "observedAt": "…",
  "payload": { "…": "…" }, "traceId": "…"
}
```

Producers: `lip-api` (intent), `lip-cdc-normalizer` (observations from
Debezium), `lip-simulator` (telemetry), `lip-seeder` (genesis at reset).
Publish-side validation rejects malformed events — try it live on the
**Event Console** page (`/events`). Full schemas + examples:
[EVENT-CATALOG.md](EVENT-CATALOG.md).

## Repo map

```
├── docker-compose.yml       # the whole stack, healthcheck-ordered
├── Makefile                 # up / reset / audit / test / logs / nuke
├── ARCHITECTURE.md          # the system as seven planes (start here)
├── EVENT-CATALOG.md         # generated event contract reference
├── DEMO-NOTES.md            # demo scripting notes
├── scripts/generate_seed.py # the deterministic world generator
├── infra/debezium/          # CDC connector config
├── server/
│   ├── app/core/            # envelope v1 + event catalog (THE contract)
│   ├── app/eventbus/        # validated publisher, consumer helper, topic admin
│   ├── app/services/        # world model reads/mutations (all event-emitting)
│   ├── app/routers/         # REST + WebSocket
│   ├── app/workers/         # normalizer (CDC), projector (projections), simulator
│   ├── app/tools/           # demo_reset, topic_audit, create_topics, render_catalog
│   └── database/            # postgres init+seed, timescale init
└── ui/                      # React app (CRA + Tailwind + Google Maps)
```

## Local development (outside Docker)

```bash
# API (needs the datastores running: docker compose up -d postgres timescaledb neo4j kafka kafka-init)
cd server && pip install -r requirements.txt
cd app && uvicorn main:app --reload            # http://localhost:8000

# UI (CRA dev server proxies /api to :8000)
cd ui && npm install && npm start              # http://localhost:3000
```

Contract tests without any services: `cd server/app && python -m pytest tests -q`.

## License

MIT — see [LICENSE](LICENSE).
