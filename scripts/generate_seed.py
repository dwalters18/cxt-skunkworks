#!/usr/bin/env python3
"""Generate the deterministic demo seed world (Austin, TX).

Writes server/database/postgres/seed.sql — the single source of truth for the
demo world. The SQL file is committed; regenerate it only when you change the
world:

    python3 scripts/generate_seed.py

Everything is fixed (IDs, names, coordinates, parcel counts). The only moving
part is time: stop windows are SQL expressions relative to CURRENT_DATE so the
world always looks like "today" no matter when it is seeded.

World shape:
  1 tenant, 1 depot, 10 customers, 8 drivers, 5 vehicles,
  5 routes (2 ACTIVE mid-shift, 3 PLANNED), 30 orders (23 routed, 7 unassigned),
  ~66 parcels. Orders each have a PICKUP and a DELIVERY stop; routed stops carry
  route_id + sequence (pickups first, then deliveries nearest-neighbor).
"""
from __future__ import annotations

import math
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "server" / "database" / "postgres" / "seed.sql"

SEED_VERSION = "austin-v1"
TENANT = "cxt-demo"

# ---------------------------------------------------------------------------
# Fixed world data — Austin, TX
# ---------------------------------------------------------------------------

DEPOT = {
    "id": "d1000000-0000-4000-8000-000000000001",
    "name": "Eastside Depot",
    "address": "2401 E 6th St, Austin, TX 78702",
    "lat": 30.2601,
    "lng": -97.7185,
}

# id suffix, code, name, contact, area, address, lat, lng
CUSTOMERS = [
    (1, "CAPLAB", "Capital Diagnostics Lab", "Dr. Renee Alvarez", "3115 Red River St, Austin, TX 78705", 30.2900, -97.7305),
    (2, "ZILKER", "Zilker Botanical Supply", "Tom Herrera", "2220 Barton Springs Rd, Austin, TX 78746", 30.2646, -97.7688),
    (3, "SOCOOP", "South Congress Optics", "Priya Patel", "1601 S Congress Ave, Austin, TX 78704", 30.2470, -97.7514),
    (4, "MUELPH", "Mueller Community Pharmacy", "Grace Kim", "1910 Aldrich St, Austin, TX 78723", 30.2996, -97.7052),
    (5, "HPPRNT", "Hyde Park Print Works", "Marcus Bell", "4315 Guadalupe St, Austin, TX 78751", 30.3095, -97.7387),
    (6, "DOMTEC", "Domain Tech Components", "Ellen Zhao", "11410 Century Oaks Ter, Austin, TX 78758", 30.4014, -97.7256),
    (7, "BSCOFF", "Barton Springs Coffee Roasters", "Luis Romero", "2201 S Lamar Blvd, Austin, TX 78704", 30.2493, -97.7676),
    (8, "RIVAUT", "Riverside Auto Parts", "Hank Dawson", "2404 E Riverside Dr, Austin, TX 78741", 30.2333, -97.7202),
    (9, "CLKFLR", "Clarksville Floral Studio", "Amelie Fontaine", "1211 W 6th St, Austin, TX 78703", 30.2725, -97.7565),
    (10, "WPDENT", "Windsor Park Dental Group", "Dr. Sam Osei", "5811 Berkman Dr, Austin, TX 78723", 30.3159, -97.6927),
]

# id suffix, number, first, last, phone, status
DRIVERS = [
    (1, "DRV-001", "Maria", "Garcia", "512-555-0101", "ON_ROUTE"),
    (2, "DRV-002", "Carlos", "Rodriguez", "512-555-0102", "ON_ROUTE"),
    (3, "DRV-003", "Aisha", "Johnson", "512-555-0103", "AVAILABLE"),
    (4, "DRV-004", "Robert", "Wilson", "512-555-0104", "AVAILABLE"),
    (5, "DRV-005", "Emily", "Chen", "512-555-0105", "AVAILABLE"),
    (6, "DRV-006", "David", "Okafor", "512-555-0106", "AVAILABLE"),
    (7, "DRV-007", "Sarah", "Nguyen", "512-555-0107", "AVAILABLE"),
    (8, "DRV-008", "James", "Miller", "512-555-0108", "OFF_DUTY"),
]

# id suffix, number, kind, make, model, capacity, status
VEHICLES = [
    (1, "VAN-101", "VAN", "Ford", "Transit 350", 60, "IN_SERVICE"),
    (2, "VAN-102", "VAN", "Mercedes-Benz", "Sprinter 2500", 55, "IN_SERVICE"),
    (3, "VAN-103", "VAN", "RAM", "ProMaster 2500", 50, "AVAILABLE"),
    (4, "VAN-104", "VAN", "Ford", "Transit 250", 45, "AVAILABLE"),
    (5, "BOX-105", "BOX_TRUCK", "Isuzu", "NPR-HD", 120, "AVAILABLE"),
]

# Delivery address pool: (label address, lat, lng) — coordinates are authoritative
# for the map; addresses are human-readable labels in the right neighborhoods.
DELIVERY_POINTS = [
    ("904 West Ave, Austin, TX 78701", 30.2734, -97.7484),
    ("1804 E Cesar Chavez St, Austin, TX 78702", 30.2560, -97.7228),
    ("3809 Duval St, Austin, TX 78751", 30.3037, -97.7288),
    ("2604 S 5th St, Austin, TX 78704", 30.2372, -97.7644),
    ("1401 Rosewood Ave, Austin, TX 78702", 30.2683, -97.7229),
    ("5300 Airport Blvd, Austin, TX 78751", 30.3131, -97.7126),
    ("807 W Mary St, Austin, TX 78704", 30.2489, -97.7583),
    ("3401 Cherrywood Rd, Austin, TX 78722", 30.2926, -97.7146),
    ("1200 Barton Hills Dr, Austin, TX 78704", 30.2547, -97.7789),
    ("6800 Burnet Rd, Austin, TX 78757", 30.3437, -97.7405),
    ("2002 Manor Rd, Austin, TX 78722", 30.2841, -97.7186),
    ("400 E Riverside Dr, Austin, TX 78704", 30.2447, -97.7401),
    ("4700 Grover Ave, Austin, TX 78756", 30.3178, -97.7419),
    ("1913 E 12th St, Austin, TX 78702", 30.2735, -97.7176),
    ("2525 W Anderson Ln, Austin, TX 78757", 30.3593, -97.7317),
    ("1100 S Lamar Blvd, Austin, TX 78704", 30.2559, -97.7635),
    ("5400 Manchaca Rd, Austin, TX 78745", 30.2172, -97.7965),
    ("3300 Bee Caves Rd, Austin, TX 78746", 30.2731, -97.8018),
    ("7301 Woodrow Ave, Austin, TX 78757", 30.3474, -97.7326),
    ("2200 E 7th St, Austin, TX 78702", 30.2593, -97.7157),
    ("600 Congress Ave, Austin, TX 78701", 30.2680, -97.7431),
    ("4200 Red River St, Austin, TX 78751", 30.3013, -97.7245),
    ("1717 Toomey Rd, Austin, TX 78704", 30.2617, -97.7615),
    ("5555 N Lamar Blvd, Austin, TX 78751", 30.3221, -97.7267),
    ("1304 E 51st St, Austin, TX 78723", 30.3054, -97.7099),
    ("901 W Ben White Blvd, Austin, TX 78704", 30.2278, -97.7756),
    ("3663 Bee Caves Rd, Austin, TX 78746", 30.2705, -97.8090),
    ("1601 E 38th 1/2 St, Austin, TX 78722", 30.2969, -97.7194),
    ("500 E Anderson Ln, Austin, TX 78752", 30.3541, -97.7043),
    ("2901 Montopolis Dr, Austin, TX 78741", 30.2287, -97.7040),
]

PARCEL_DESCRIPTIONS = [
    "Lab specimen kit", "Document envelope", "Small electronics", "Pharmacy tote",
    "Print job — boxed", "Auto part", "Floral arrangement", "Coffee sample case",
    "Optical frames", "Dental supplies", "Marketing materials", "Spare cables",
]

NOTES = {
    1: "Refrigerated — keep cold",
    4: "Signature required",
    7: "Fragile",
    9: "Deliver to loading dock",
    13: "Signature required",
    17: "Fragile — glass",
    22: "Call recipient on arrival",
    26: "Refrigerated — keep cold",
}

# Orders 1..30. (customer#, pickup: "depot" or "site", delivery point index 0-based,
# parcel_count, pickup window start offset minutes from 08:00, window length min)
ORDERS = [
    # RT-101 (ACTIVE, Maria, VAN-101): orders 1-5, depot pickups, mid-shift
    (1, 1, "depot", 0, 2, 0, 120),
    (2, 3, "depot", 6, 1, 0, 120),
    (3, 5, "depot", 2, 3, 10, 120),
    (4, 7, "depot", 8, 2, 10, 120),
    (5, 9, "depot", 20, 1, 20, 120),
    # RT-102 (ACTIVE, Carlos, VAN-102): orders 6-10, mixed pickups, first delivery done
    (6, 2, "site", 3, 2, 20, 120),
    (7, 4, "depot", 4, 3, 30, 120),
    (8, 4, "depot", 24, 2, 30, 120),
    (9, 8, "site", 11, 4, 40, 120),
    (10, 8, "depot", 19, 1, 40, 120),
    # RT-103 (PLANNED, Aisha, VAN-103): orders 11-15
    (11, 1, "depot", 5, 2, 120, 150),
    (12, 1, "site", 21, 3, 120, 150),
    (13, 6, "depot", 14, 2, 130, 150),
    (14, 6, "site", 28, 3, 130, 150),
    (15, 10, "depot", 27, 1, 140, 150),
    # RT-104 (PLANNED, Robert, BOX-105): orders 16-20
    (16, 5, "site", 10, 4, 150, 150),
    (17, 9, "depot", 1, 2, 150, 150),
    (18, 7, "site", 16, 3, 160, 150),
    (19, 3, "depot", 12, 1, 160, 150),
    (20, 2, "depot", 17, 2, 170, 150),
    # RT-105 (PLANNED, Emily, VAN-104): orders 21-23
    (21, 10, "site", 25, 3, 180, 150),
    (22, 4, "depot", 9, 2, 180, 150),
    (23, 1, "depot", 13, 2, 190, 150),
    # Unassigned (CREATED): orders 24-30 — dispatch board material
    (24, 2, "site", 7, 1, 240, 180),
    (25, 6, "depot", 15, 2, 240, 180),
    (26, 1, "depot", 18, 3, 250, 180),
    (27, 8, "site", 22, 2, 250, 180),
    (28, 5, "depot", 23, 1, 260, 180),
    (29, 9, "site", 26, 2, 260, 180),
    (30, 3, "depot", 29, 4, 270, 180),
]

# route# -> (route_number, driver#, vehicle#, status, [order#s])
ROUTES = {
    1: ("RT-101", 1, 1, "ACTIVE", [1, 2, 3, 4, 5]),
    2: ("RT-102", 2, 2, "ACTIVE", [6, 7, 8, 9, 10]),
    3: ("RT-103", 3, 3, "PLANNED", [11, 12, 13, 14, 15]),
    4: ("RT-104", 4, 5, "PLANNED", [16, 17, 18, 19, 20]),
    5: ("RT-105", 5, 4, "PLANNED", [21, 22, 23]),
}

# Mid-shift state for ACTIVE routes: which stop sequences are already done.
# RT-101: all 5 pickups completed (driver has the parcels, heading to deliveries).
# RT-102: pickups completed AND first delivery completed (order 6 fully delivered).
COMPLETED_SEQUENCES = {1: 5, 2: 6}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def order_id(n: int) -> str:
    return f"b1000000-0000-4000-8000-{n:012d}"

def stop_id(n: int, kind: str) -> str:
    k = 1 if kind == "PICKUP" else 2
    return f"b2000000-0000-4000-8000-{n * 10 + k:012d}"

def parcel_id(n: int, k: int) -> str:
    return f"b3000000-0000-4000-8000-{n * 100 + k:012d}"

def customer_id(n: int) -> str:
    return f"c1000000-0000-4000-8000-{n:012d}"

def driver_id(n: int) -> str:
    return f"d2000000-0000-4000-8000-{n:012d}"

def vehicle_id(n: int) -> str:
    return f"e1000000-0000-4000-8000-{n:012d}"

def route_id(n: int) -> str:
    return f"a1000000-0000-4000-8000-{n:012d}"

def geo(lat: float, lng: float) -> str:
    return f"ST_GeogFromText('POINT({lng} {lat})')"

def ts(minutes_from_8am: int) -> str:
    """A timestamptz expression relative to today, so the seed is always fresh."""
    return f"(CURRENT_DATE + TIME '08:00' + INTERVAL '{minutes_from_8am} minutes')"

def sql_str(s):
    if s is None:
        return "NULL"
    return "'" + str(s).replace("'", "''") + "'"

def haversine_miles(a, b):
    lat1, lng1, lat2, lng2 = map(math.radians, [a[0], a[1], b[0], b[1]])
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lng2 - lng1) / 2) ** 2
    return 3958.8 * 2 * math.asin(math.sqrt(h))


def order_pickup(o):
    """(address, lat, lng) of the order's pickup stop."""
    n, cust, mode, _, _, _, _ = o
    if mode == "depot":
        return (DEPOT["address"], DEPOT["lat"], DEPOT["lng"])
    c = CUSTOMERS[cust - 1]
    return (c[4], c[5], c[6])


def order_delivery(o):
    addr, lat, lng = DELIVERY_POINTS[o[3]][0], DELIVERY_POINTS[o[3]][1], DELIVERY_POINTS[o[3]][2]
    return (addr, lat, lng)


def sequence_route(order_nums):
    """Pickups first (in order-number order), then deliveries nearest-neighbor
    starting from the depot. Returns [(order_num, kind), ...] in sequence."""
    seq = [(n, "PICKUP") for n in order_nums]
    remaining = list(order_nums)
    pos = (DEPOT["lat"], DEPOT["lng"])
    while remaining:
        nxt = min(
            remaining,
            key=lambda n: haversine_miles(pos, order_delivery(ORDERS[n - 1])[1:]),
        )
        seq.append((nxt, "DELIVERY"))
        d = order_delivery(ORDERS[nxt - 1])
        pos = (d[1], d[2])
        remaining.remove(nxt)
    return seq


# ---------------------------------------------------------------------------
# Emit SQL
# ---------------------------------------------------------------------------

def main() -> None:
    lines: list[str] = []
    w = lines.append

    w(f"-- Deterministic demo seed world: {SEED_VERSION} (Austin, TX)")
    w("-- GENERATED by scripts/generate_seed.py — edit the generator, not this file.")
    w("-- Idempotent: truncates and reloads the whole world. Stop windows are")
    w("-- relative to CURRENT_DATE so the world always reads as 'today'.")
    w("")
    w("BEGIN;")
    w("")
    w("TRUNCATE TABLE parcels, stops, orders, routes, vehicles, drivers, depots, customers, tenants CASCADE;")
    w("")

    w(f"INSERT INTO tenants (id, name) VALUES ({sql_str(TENANT)}, 'CXT Demo Courier — Austin');")
    w("")

    w("INSERT INTO depots (id, tenant_id, name, address, location) VALUES")
    w(f"  ('{DEPOT['id']}', '{TENANT}', {sql_str(DEPOT['name'])}, {sql_str(DEPOT['address'])}, {geo(DEPOT['lat'], DEPOT['lng'])});")
    w("")

    w("INSERT INTO customers (id, tenant_id, code, name, contact_name, email, phone, address, location) VALUES")
    rows = []
    for n, code, name, contact, address, lat, lng in CUSTOMERS:
        email = f"dispatch@{code.lower()}.example.com"
        phone = f"512-555-02{n:02d}"
        rows.append(
            f"  ('{customer_id(n)}', '{TENANT}', {sql_str(code)}, {sql_str(name)}, {sql_str(contact)}, "
            f"{sql_str(email)}, {sql_str(phone)}, {sql_str(address)}, {geo(lat, lng)})"
        )
    w(",\n".join(rows) + ";")
    w("")

    # Drivers: ON_ROUTE drivers start at meaningful mid-shift positions.
    driver_pos = {n: (DEPOT["lat"], DEPOT["lng"]) for n, *_ in DRIVERS}
    # Maria finished pickups at the depot. Carlos just completed his first delivery.
    carlos_first_delivery = None
    seq2 = sequence_route(ROUTES[2][4])
    for order_num, kind in seq2:
        if kind == "DELIVERY":
            carlos_first_delivery = order_delivery(ORDERS[order_num - 1])
            break
    if carlos_first_delivery:
        driver_pos[2] = (carlos_first_delivery[1], carlos_first_delivery[2])

    w("INSERT INTO drivers (id, tenant_id, driver_number, first_name, last_name, phone, email, status, home_depot_id, current_location, location_updated_at) VALUES")
    rows = []
    for n, number, first, last, phone, status in DRIVERS:
        email = f"{first.lower()}.{last.lower()}@cxtdemo.example.com"
        lat, lng = driver_pos[n]
        rows.append(
            f"  ('{driver_id(n)}', '{TENANT}', {sql_str(number)}, {sql_str(first)}, {sql_str(last)}, "
            f"{sql_str(phone)}, {sql_str(email)}, '{status}', '{DEPOT['id']}', {geo(lat, lng)}, NOW())"
        )
    w(",\n".join(rows) + ";")
    w("")

    w("INSERT INTO vehicles (id, tenant_id, vehicle_number, kind, make, model, capacity_parcels, status, home_depot_id, current_location) VALUES")
    rows = []
    for n, number, kind, make, model, cap, status in VEHICLES:
        # In-service vehicles ride with their route's driver.
        pos = driver_pos.get({1: 1, 2: 2}.get(n), (DEPOT["lat"], DEPOT["lng"]))
        rows.append(
            f"  ('{vehicle_id(n)}', '{TENANT}', {sql_str(number)}, {sql_str(kind)}, {sql_str(make)}, "
            f"{sql_str(model)}, {cap}, '{status}', '{DEPOT['id']}', {geo(pos[0], pos[1])})"
        )
    w(",\n".join(rows) + ";")
    w("")

    w("INSERT INTO routes (id, tenant_id, route_number, service_date, status, driver_id, vehicle_id, started_at) VALUES")
    rows = []
    for rn, (number, drv, veh, status, _orders) in ROUTES.items():
        started = ts(0) if status == "ACTIVE" else "NULL"
        rows.append(
            f"  ('{route_id(rn)}', '{TENANT}', {sql_str(number)}, CURRENT_DATE, '{status}', "
            f"'{driver_id(drv)}', '{vehicle_id(veh)}', {started})"
        )
    w(",\n".join(rows) + ";")
    w("")

    # Orders + stops + parcels
    order_to_route = {}
    order_seq = {}   # (order_num, kind) -> sequence
    for rn, (_, _, _, _, order_nums) in ROUTES.items():
        for i, (order_num, kind) in enumerate(sequence_route(order_nums), start=1):
            order_to_route[order_num] = rn
            order_seq[(order_num, kind)] = i

    def stop_state(order_num, kind):
        """(status, arrived_expr, completed_expr) for mid-shift ACTIVE routes."""
        rn = order_to_route.get(order_num)
        if rn not in COMPLETED_SEQUENCES:
            return ("PENDING", "NULL", "NULL")
        seq = order_seq[(order_num, kind)]
        if seq <= COMPLETED_SEQUENCES[rn]:
            done_min = 5 * seq  # finished stops, minutes after 08:00
            return ("COMPLETED", ts(done_min - 2), ts(done_min))
        return ("PENDING", "NULL", "NULL")

    w("INSERT INTO orders (id, tenant_id, order_number, customer_id, status, notes) VALUES")
    rows = []
    for o in ORDERS:
        n, cust, *_ = o
        rn = order_to_route.get(n)
        if rn is None:
            status = "CREATED"
        else:
            pickup_done = stop_state(n, "PICKUP")[0] == "COMPLETED"
            delivery_done = stop_state(n, "DELIVERY")[0] == "COMPLETED"
            if delivery_done:
                status = "COMPLETED"
            elif pickup_done:
                status = "IN_PROGRESS"
            else:
                status = "ASSIGNED"
        rows.append(
            f"  ('{order_id(n)}', '{TENANT}', 'ORD-{1000 + n}', '{customer_id(cust)}', '{status}', {sql_str(NOTES.get(n))})"
        )
    w(",\n".join(rows) + ";")
    w("")

    w("INSERT INTO stops (id, tenant_id, order_id, route_id, kind, sequence, status, address, location, window_start, window_end, arrived_at, completed_at) VALUES")
    rows = []
    for o in ORDERS:
        n, cust, mode, dp, parcels, win_start, win_len = o
        rn = order_to_route.get(n)
        rid = f"'{route_id(rn)}'" if rn else "NULL"
        for kind, (addr, lat, lng) in (("PICKUP", order_pickup(o)), ("DELIVERY", order_delivery(o))):
            seq = order_seq.get((n, kind))
            seq_sql = seq if seq is not None else "NULL"
            status, arrived, completed = stop_state(n, kind)
            if kind == "PICKUP":
                ws, we = win_start, win_start + win_len
            else:
                ws, we = win_start + 60, win_start + win_len + 180
            rows.append(
                f"  ('{stop_id(n, kind)}', '{TENANT}', '{order_id(n)}', {rid}, '{kind}', {seq_sql}, '{status}', "
                f"{sql_str(addr)}, {geo(lat, lng)}, {ts(ws)}, {ts(we)}, {arrived}, {completed})"
            )
    w(",\n".join(rows) + ";")
    w("")

    w("INSERT INTO parcels (id, tenant_id, order_id, barcode, description, weight_kg, status) VALUES")
    rows = []
    parcel_total = 0
    for o in ORDERS:
        n, cust, mode, dp, count, *_ = o
        pickup_done = stop_state(n, "PICKUP")[0] == "COMPLETED"
        delivery_done = stop_state(n, "DELIVERY")[0] == "COMPLETED"
        pstatus = "DELIVERED" if delivery_done else ("PICKED_UP" if pickup_done else "PENDING")
        for k in range(1, count + 1):
            desc = PARCEL_DESCRIPTIONS[(n + k) % len(PARCEL_DESCRIPTIONS)]
            weight = round(0.5 + ((n * 7 + k * 3) % 28) * 0.5, 2)
            rows.append(
                f"  ('{parcel_id(n, k)}', '{TENANT}', '{order_id(n)}', 'PCL-{1000 + n}-{k}', "
                f"{sql_str(desc)}, {weight}, '{pstatus}')"
            )
            parcel_total += 1
    w(",\n".join(rows) + ";")
    w("")
    w("COMMIT;")
    w("")

    OUT.write_text("\n".join(lines))
    print(f"wrote {OUT}")
    print(
        f"world: 1 tenant, 1 depot, {len(CUSTOMERS)} customers, {len(DRIVERS)} drivers, "
        f"{len(VEHICLES)} vehicles, {len(ROUTES)} routes, {len(ORDERS)} orders, "
        f"{len(ORDERS) * 2} stops, {parcel_total} parcels"
    )


if __name__ == "__main__":
    main()
