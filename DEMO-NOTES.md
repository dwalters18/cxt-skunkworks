# Demo Notes — what each piece demonstrates

Running log for demo scripting. Each entry: the surface, what it proves, and
the money moment. Keep appending as the series grows.

## Pre-demo checklist

1. `make up` (fresh machine: ~3-5 min for image builds, then healthchecks gate startup)
2. `make reset` — returns the world to seed state in well under a minute; do this right before presenting
3. Open http://localhost:3000 → splash → Dispatch Board; two routes (RT-101, RT-102) are already mid-shift and moving
4. Keep http://localhost:8080 (Kafka UI) and a psql window handy for the CDC trick

## The seed world (austin-v1)

One tenant (`cxt-demo`) in Austin, TX: **Eastside Depot** (2401 E 6th St),
**10 customers** (labs, pharmacies, print shops — courier-flavored), **8
drivers**, **5 vehicles**, **5 routes** (RT-101/102 ACTIVE mid-shift,
RT-103/104/105 PLANNED and staffed), **30 orders** (23 routed, 7 unassigned),
**66 parcels**. Deterministic IDs (`ORD-1001`…, `DRV-001`…); stop windows are
relative to today so the world never looks stale. Regenerate only via
`make seed-regen` (edits go in `scripts/generate_seed.py`, never in seed.sql).

## The one-take demo (order entry → dispatch → delivered, no terminal)

1. **Dispatch Board (/)** — three panels: unassigned queue (urgency-sorted,
   STAT pulses red), live map, drivers & routes. Status bar reads
   "projected from N events" — call out that the board is a projection
   consumer: it never refetches after a write; it folds the same envelopes
   every other consumer sees.
2. **New Order** (button on the queue) — pick a customer (choose Capital
   Diagnostics Lab for the medical story), pickup "Depot", delivery from the
   address book, service level **STAT** (watch the deliver-by tighten), 2
   parcels → Create. You land on the order detail; its event tail already
   shows `order.created` (lip-api) and the CDC `*.record-created` echoes.
3. Back to the board — the order is already in the queue (it arrived as an
   event, not a refetch), sorted by urgency.
4. **Assign:** drag the order onto a driver (or click order → click driver).
   If the driver has no route, one is planned automatically (`route.planned`)
   then `order.assigned` lands and the card moves to their row; the stops
   appear on the map in route colors.
5. **Advance:** click the driver → slide-over → Start route (if planned), then
   Arrive → Complete the pickup, then the delivery. Each press is an API call
   whose `stop.status-updated` event moves the board; completing the delivery
   fires `order.completed` (and `route.completed` when the route drains).
6. Split-screen with **Event Console** (/events) during all of the above: every
   transition shows up as canonical envelopes with shared traceIds.

### Dispatch Board (/) — extra beats
**Proves:** the world model is alive — one screen shows state + events + action.
- Driver dots move every 2s while routes are ACTIVE (simulator telemetry →
  backbone → WebSocket → map); manual stop advancement works even while the
  simulator runs (it drives only ACTIVE routes).
- Click a stop: numbered by route sequence, colored by status; completed stops dim.

### Event Console (/events)
**Proves:** the canonical contract exists and is enforced.
- Every producer on one screen; filter by namespace or sourceSystem
  (lip-api / lip-cdc-normalizer / lip-simulator / lip-seeder).
- Expand any row: the raw envelope — eventId, eventType, entityRefs, occurredAt
  vs observedAt, traceId.
- **Money moment #1 (validation):** "Try an invalid event" → Publish → 422 with
  field-level errors, "rejected at publish time". Then publish the valid one → 202
  and it appears in the stream a beat later.
- **Money moment #2 (CDC):** in psql
  (`docker compose exec postgres psql -U lip_user lip_world`) run
  `UPDATE drivers SET phone = '512-555-9999' WHERE driver_number = 'DRV-008';`
  → a `driver.record-updated` envelope appears in the console with before/after.
  Nothing called an API — the integration plane observed the world change.

### Orders (/orders)
**Proves:** canonical vocabulary end to end — an order is created *with* its
pickup and delivery stops and its parcels, atomically.
- Create an order (New Order → pick a customer → depot pickup) and flip to the
  Event Console: one `order.created` intent event + a cluster of `*.record-created`
  observations (order, 2 stops, N parcels) sharing the moment. Intent vs
  observation in one gesture.

### Drivers (/drivers) — "Impact"
**Proves:** the graph projection answers blast-radius questions in one hop.
- Pick an ON_ROUTE driver → Impact → routes, stop count, open orders, customers
  affected — served by Neo4j, which was itself built purely from events.

### Dashboard + Analytics
**Proves:** projections are queryable and honest. Events-last-hour ticks up as
the simulator works; on-time % is computed from stop windows vs completions.

### `make audit` (terminal)
**Proves:** the done-criterion — every message on every canonical topic
validates against envelope v1 + its payload schema; the raw CDC namespace is
explicitly classified; any rogue topic fails the audit.

### `make reset` (terminal)
**Proves:** the event-sourced posture — wipe topics, projections, and graph;
reseed Postgres; Debezium re-narrates the world; the projector rebuilds
Timescale and Neo4j from events alone. Run it twice to show repeatability.

## Talking points / gotchas

- `driver.location-updated` is hidden by default in the console (telemetry
  noise); the toggle exists precisely to show *why* envelopes make filtering
  trivial.
- After the two ACTIVE routes finish (~15-20 min), start RT-103/104/105 for more
  movement, or just `make reset`. Auto-start is off by default
  (`SIM_AUTO_START_ROUTES=false`) so presenters control the pace.
- The Google Maps key is NOT committed (git-ignored by design). It reaches the
  build via `GOOGLE_MAPS_API_KEY` in the host env or a local `ui/.env`; without
  it everything works except map tiles (fallback panel explains itself). Keep a
  key exported on the demo machine.
- Windows/timing: seed stop windows assume the demo runs the same day as the
  reset (they're `CURRENT_DATE`-relative — another reason to reset before
  presenting).

## Series backlog (where the next episodes plug in)

- **Intelligence:** ETA prediction per stop → `stop.eta-updated` events (the
  catalog + envelope are ready; add the type, emit, project).
- **Trust:** parcel scan/photo custody events; assemble a per-parcel timeline
  from `event_stream` filtered by entityRef.
- **Action:** exception verbs (driver-down → replan) using the Impact query as
  the blast-radius input.
