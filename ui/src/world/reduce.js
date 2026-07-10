/**
 * World projection reducer — canonical envelopes in, UI state out.
 *
 * This is the point of the dispatch board: it does NOT refetch after writes.
 * The REST bootstrap gives it a starting snapshot; from then on the board is a
 * projection consumer, folding the same envelope v1 events every other
 * consumer sees (projector, event console) into local state.
 *
 * Only intent/telemetry events drive the board; *.record-* observation events
 * are the world model echoing and are ignored here.
 */

export const initialWorld = {
  bootstrapped: false,
  orders: {}, // id -> order JSON (REST shape)
  routes: {}, // id -> route JSON with stops[]
  drivers: {}, // id -> driver JSON
  vehicles: {}, // id -> vehicle JSON
  depots: [],
  customers: [],
  positions: {}, // driverId -> {latitude, longitude, speedMph, live}
  eventCount: 0,
  lastEventType: null,
  lastEventAt: null,
};

const byId = (list) => Object.fromEntries((list || []).map((x) => [x.id, x]));

export function bootstrapWorld(state, { orders, routes, drivers, vehicles, depots, customers }) {
  return {
    ...state,
    bootstrapped: true,
    orders: byId(orders),
    routes: byId(routes),
    drivers: byId(drivers),
    vehicles: byId(vehicles),
    depots: depots || [],
    customers: customers || [],
  };
}

// --- helpers ---------------------------------------------------------------

function snapshotToStop(orderId, snap, orderNumber) {
  return {
    stopId: snap.stopId,
    orderId,
    routeId: null,
    kind: snap.kind,
    sequence: null,
    status: 'PENDING',
    address: snap.address,
    latitude: snap.location?.latitude,
    longitude: snap.location?.longitude,
    windowStart: snap.windowStart,
    windowEnd: snap.windowEnd,
    eta: null,
    arrivedAt: null,
    completedAt: null,
    orderNumber,
  };
}

function patchOrderStop(order, stopId, patch) {
  const next = { ...order };
  for (const side of ['pickup', 'delivery']) {
    if (next[side]?.stopId === stopId) {
      next[side] = { ...next[side], ...patch };
    }
  }
  return next;
}

function recount(route) {
  const completed = route.stops.filter((s) => s.status === 'COMPLETED').length;
  return { ...route, stopsTotal: route.stops.length, stopsCompleted: completed };
}

// --- the reducer ------------------------------------------------------------

export function applyEvent(state, envelope) {
  const { eventType, payload: p, occurredAt } = envelope;
  const meta = {
    eventCount: state.eventCount + 1,
    lastEventType: eventType,
    lastEventAt: envelope.observedAt || occurredAt,
  };

  switch (eventType) {
    case 'order.created': {
      const order = {
        id: p.orderId,
        orderNumber: p.orderNumber,
        status: 'CREATED',
        serviceLevel: p.serviceLevel || 'ROUTINE',
        notes: p.notes,
        customer: { id: p.customerId, name: p.customerName },
        parcelCount: p.parcelCount,
        parcels: [],
        pickup: snapshotToStop(p.orderId, p.pickup, p.orderNumber),
        delivery: snapshotToStop(p.orderId, p.delivery, p.orderNumber),
        routeId: null,
        routeNumber: null,
        driverName: null,
        createdAt: occurredAt,
        updatedAt: occurredAt,
      };
      // Seeder genesis events replay orders that may already exist with richer
      // state from the bootstrap — never downgrade an existing order.
      if (state.orders[order.id]) return { ...state, ...meta };
      return { ...state, ...meta, orders: { ...state.orders, [order.id]: order } };
    }

    case 'order.assigned': {
      const existing = state.orders[p.orderId];
      const route = state.routes[p.routeId];
      const seqByStop = Object.fromEntries((p.stops || []).map((s) => [s.stopId, s.sequence]));
      let orders = state.orders;
      let routes = state.routes;

      if (existing) {
        let next = {
          ...existing,
          status: 'ASSIGNED',
          routeId: p.routeId,
          routeNumber: p.routeNumber,
          driverName: p.driverId ? state.drivers[p.driverId]?.name || existing.driverName : existing.driverName,
        };
        for (const side of ['pickup', 'delivery']) {
          if (next[side]) {
            next = patchOrderStop(next, next[side].stopId, {
              routeId: p.routeId,
              sequence: seqByStop[next[side].stopId] ?? next[side].sequence,
            });
          }
        }
        orders = { ...orders, [p.orderId]: next };

        if (route) {
          const newStops = ['pickup', 'delivery']
            .map((side) => next[side])
            .filter((s) => s && !route.stops.some((r) => r.stopId === s.stopId))
            .map((s) => ({ ...s, orderNumber: s.orderNumber || next.orderNumber }));
          routes = {
            ...routes,
            [p.routeId]: recount({
              ...route,
              stops: [...route.stops, ...newStops].sort(
                (a, b) => (a.sequence ?? 999) - (b.sequence ?? 999)
              ),
            }),
          };
        }
      }
      return { ...state, ...meta, orders, routes };
    }

    case 'order.completed': {
      const existing = state.orders[p.orderId];
      if (!existing) return { ...state, ...meta };
      return {
        ...state,
        ...meta,
        orders: { ...state.orders, [p.orderId]: { ...existing, status: 'COMPLETED' } },
      };
    }

    case 'order.cancelled': {
      const existing = state.orders[p.orderId];
      let routes = state.routes;
      if (existing?.routeId && routes[existing.routeId]) {
        const r = routes[existing.routeId];
        routes = {
          ...routes,
          [existing.routeId]: recount({
            ...r,
            stops: r.stops.filter((s) => s.orderId !== p.orderId),
          }),
        };
      }
      if (!existing) return { ...state, ...meta };
      return {
        ...state,
        ...meta,
        routes,
        orders: { ...state.orders, [p.orderId]: { ...existing, status: 'CANCELLED' } },
      };
    }

    case 'stop.status-updated': {
      const ts = occurredAt;
      const patch = {
        status: p.status,
        ...(p.status === 'ARRIVED' ? { arrivedAt: ts } : {}),
        ...(p.status === 'COMPLETED' ? { completedAt: ts } : {}),
      };
      let orders = state.orders;
      const order = orders[p.orderId];
      if (order) {
        let next = patchOrderStop(order, p.stopId, patch);
        // Mirror the API's cascade so the board reads truthfully between events.
        if (p.status === 'COMPLETED' && p.kind === 'PICKUP' && next.status !== 'COMPLETED') {
          next = { ...next, status: 'IN_PROGRESS' };
        }
        orders = { ...orders, [p.orderId]: next };
      }
      let routes = state.routes;
      if (p.routeId && routes[p.routeId]) {
        const r = routes[p.routeId];
        routes = {
          ...routes,
          [p.routeId]: recount({
            ...r,
            stops: r.stops.map((s) => (s.stopId === p.stopId ? { ...s, ...patch } : s)),
          }),
        };
      }
      return { ...state, ...meta, orders, routes };
    }

    case 'route.planned': {
      if (state.routes[p.routeId]) return { ...state, ...meta };
      const driver = p.driverId ? state.drivers[p.driverId] : null;
      const vehicle = p.vehicleId ? state.vehicles[p.vehicleId] : null;
      const route = {
        id: p.routeId,
        routeNumber: p.routeNumber,
        serviceDate: p.serviceDate,
        status: 'PLANNED',
        driver: driver ? { id: driver.id, name: driver.name } : null,
        vehicle: vehicle ? { id: vehicle.id, vehicleNumber: vehicle.vehicleNumber } : null,
        stops: [],
        stopsTotal: p.stopCount || 0,
        stopsCompleted: 0,
        startedAt: null,
        completedAt: null,
      };
      return { ...state, ...meta, routes: { ...state.routes, [p.routeId]: route } };
    }

    case 'route.started': {
      const route = state.routes[p.routeId];
      let drivers = state.drivers;
      let vehicles = state.vehicles;
      if (p.driverId && drivers[p.driverId]) {
        drivers = {
          ...drivers,
          [p.driverId]: {
            ...drivers[p.driverId],
            status: 'ON_ROUTE',
            activeRouteId: p.routeId,
            activeRouteNumber: p.routeNumber,
          },
        };
      }
      if (p.vehicleId && vehicles[p.vehicleId]) {
        vehicles = {
          ...vehicles,
          [p.vehicleId]: { ...vehicles[p.vehicleId], status: 'IN_SERVICE', activeRouteId: p.routeId },
        };
      }
      if (!route) return { ...state, ...meta, drivers, vehicles };
      return {
        ...state,
        ...meta,
        drivers,
        vehicles,
        routes: { ...state.routes, [p.routeId]: { ...route, status: 'ACTIVE', startedAt: occurredAt } },
      };
    }

    case 'route.completed': {
      const route = state.routes[p.routeId];
      let drivers = state.drivers;
      let vehicles = state.vehicles;
      if (route?.driver?.id && drivers[route.driver.id]) {
        drivers = {
          ...drivers,
          [route.driver.id]: {
            ...drivers[route.driver.id],
            status: 'AVAILABLE',
            activeRouteId: null,
            activeRouteNumber: null,
          },
        };
      }
      if (route?.vehicle?.id && vehicles[route.vehicle.id]) {
        vehicles = {
          ...vehicles,
          [route.vehicle.id]: { ...vehicles[route.vehicle.id], status: 'AVAILABLE', activeRouteId: null },
        };
      }
      if (!route) return { ...state, ...meta, drivers, vehicles };
      return {
        ...state,
        ...meta,
        drivers,
        vehicles,
        routes: {
          ...state.routes,
          [p.routeId]: { ...route, status: 'COMPLETED', completedAt: occurredAt },
        },
      };
    }

    case 'driver.status-updated': {
      const d = state.drivers[p.driverId];
      if (!d) return { ...state, ...meta };
      return {
        ...state,
        ...meta,
        drivers: { ...state.drivers, [p.driverId]: { ...d, status: p.status } },
      };
    }

    case 'vehicle.status-updated': {
      const v = state.vehicles[p.vehicleId];
      if (!v) return { ...state, ...meta };
      return {
        ...state,
        ...meta,
        vehicles: { ...state.vehicles, [p.vehicleId]: { ...v, status: p.status } },
      };
    }

    case 'driver.location-updated': {
      return {
        ...state,
        ...meta,
        positions: {
          ...state.positions,
          [p.driverId]: {
            latitude: p.location.latitude,
            longitude: p.location.longitude,
            speedMph: p.speedMph,
            live: true,
          },
        },
      };
    }

    default:
      // *.record-* observations, system events: acknowledged, not applied.
      return { ...state, ...meta };
  }
}

// --- selectors ----------------------------------------------------------------

export function selectUnassignedOrders(world) {
  return Object.values(world.orders)
    .filter((o) => o.status === 'CREATED' && !o.routeId)
    .sort((a, b) => {
      const wa = a.delivery?.windowEnd || '9999';
      const wb = b.delivery?.windowEnd || '9999';
      return wa < wb ? -1 : 1;
    });
}

export function selectRouteList(world) {
  return Object.values(world.routes).sort((a, b) =>
    (a.routeNumber || '').localeCompare(b.routeNumber || '')
  );
}

export function selectDriverBoard(world) {
  const routesByDriver = {};
  for (const r of Object.values(world.routes)) {
    if (r.driver?.id && r.status !== 'COMPLETED') {
      const open = r.stops.filter((s) => s.status === 'PENDING' || s.status === 'ARRIVED').length;
      const cur = routesByDriver[r.driver.id];
      // Prefer the ACTIVE route as "current"; otherwise the busiest planned one.
      if (!cur || (r.status === 'ACTIVE' && cur.status !== 'ACTIVE')) {
        routesByDriver[r.driver.id] = { ...r, openStops: open };
      }
    }
  }
  return Object.values(world.drivers)
    .sort((a, b) => (a.driverNumber || '').localeCompare(b.driverNumber || ''))
    .map((d) => ({
      ...d,
      currentRoute: routesByDriver[d.id] || null,
      position: world.positions[d.id] || (d.latitude != null ? { latitude: d.latitude, longitude: d.longitude } : null),
    }));
}
