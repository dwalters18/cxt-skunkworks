/**
 * Projection reducer tests — the dispatch board's event-folding logic.
 * Run: npm test -- --watchAll=false
 */
import { applyEvent, bootstrapWorld, initialWorld, selectUnassignedOrders } from './reduce';

const T0 = '2026-07-09T14:00:00Z';

function env(eventType, payload, occurredAt = T0) {
  return {
    eventId: `e-${Math.random()}`,
    eventType,
    eventVersion: '1.0',
    sourceSystem: 'lip-api',
    tenantId: 'cxt-demo',
    entityRefs: [{ type: 'order', id: payload.orderId || 'x' }],
    occurredAt,
    observedAt: occurredAt,
    payload,
  };
}

function baseWorld() {
  return bootstrapWorld(initialWorld, {
    orders: [],
    routes: [
      {
        id: 'r1',
        routeNumber: 'RT-900',
        serviceDate: '2026-07-09',
        status: 'PLANNED',
        driver: { id: 'd1', name: 'Aisha Johnson' },
        vehicle: { id: 'v1', vehicleNumber: 'VAN-103' },
        stops: [],
        stopsTotal: 0,
        stopsCompleted: 0,
      },
    ],
    drivers: [
      { id: 'd1', name: 'Aisha Johnson', driverNumber: 'DRV-003', status: 'AVAILABLE' },
    ],
    vehicles: [{ id: 'v1', vehicleNumber: 'VAN-103', status: 'AVAILABLE' }],
    depots: [],
    customers: [],
  });
}

const CREATED = env('order.created', {
  orderId: 'o1',
  orderNumber: 'ORD-2001',
  customerId: 'c1',
  customerName: 'Capital Diagnostics Lab',
  serviceLevel: 'STAT',
  parcelCount: 2,
  pickup: {
    stopId: 's-p', kind: 'PICKUP', address: 'Depot',
    location: { latitude: 30.26, longitude: -97.72 },
    windowStart: T0, windowEnd: '2026-07-09T15:30:00Z',
  },
  delivery: {
    stopId: 's-d', kind: 'DELIVERY', address: '600 Congress Ave',
    location: { latitude: 30.268, longitude: -97.743 },
    windowStart: T0, windowEnd: '2026-07-09T15:30:00Z',
  },
  notes: null,
});

test('order.created materializes an unassigned order from the payload alone', () => {
  const world = applyEvent(baseWorld(), CREATED);
  const order = world.orders['o1'];
  expect(order.status).toBe('CREATED');
  expect(order.serviceLevel).toBe('STAT');
  expect(order.pickup.latitude).toBe(30.26);
  expect(selectUnassignedOrders(world).map((o) => o.id)).toEqual(['o1']);
  expect(world.eventCount).toBe(1);
});

test('order.assigned moves the order onto the route with sequenced stops', () => {
  let world = applyEvent(baseWorld(), CREATED);
  world = applyEvent(
    world,
    env('order.assigned', {
      orderId: 'o1',
      orderNumber: 'ORD-2001',
      routeId: 'r1',
      routeNumber: 'RT-900',
      driverId: 'd1',
      vehicleId: 'v1',
      stops: [
        { stopId: 's-p', kind: 'PICKUP', sequence: 1 },
        { stopId: 's-d', kind: 'DELIVERY', sequence: 2 },
      ],
    })
  );
  const order = world.orders['o1'];
  expect(order.status).toBe('ASSIGNED');
  expect(order.routeNumber).toBe('RT-900');
  expect(order.driverName).toBe('Aisha Johnson');
  expect(order.pickup.sequence).toBe(1);
  const route = world.routes['r1'];
  expect(route.stops.map((s) => s.stopId)).toEqual(['s-p', 's-d']);
  expect(route.stops[0].latitude).toBe(30.26); // coords carried over for the map
  expect(route.stopsTotal).toBe(2);
  expect(selectUnassignedOrders(world)).toHaveLength(0);
});

test('stop lifecycle cascades: pickup completion → IN_PROGRESS, delivery + order.completed → done', () => {
  let world = applyEvent(baseWorld(), CREATED);
  world = applyEvent(
    world,
    env('order.assigned', {
      orderId: 'o1', orderNumber: 'ORD-2001', routeId: 'r1', routeNumber: 'RT-900',
      driverId: 'd1', vehicleId: 'v1',
      stops: [
        { stopId: 's-p', kind: 'PICKUP', sequence: 1 },
        { stopId: 's-d', kind: 'DELIVERY', sequence: 2 },
      ],
    })
  );
  world = applyEvent(
    world,
    env('stop.status-updated', {
      stopId: 's-p', orderId: 'o1', routeId: 'r1', kind: 'PICKUP',
      previousStatus: 'PENDING', status: 'COMPLETED',
    }, '2026-07-09T14:10:00Z')
  );
  expect(world.orders['o1'].status).toBe('IN_PROGRESS');
  expect(world.orders['o1'].pickup.status).toBe('COMPLETED');
  expect(world.routes['r1'].stopsCompleted).toBe(1);

  world = applyEvent(
    world,
    env('stop.status-updated', {
      stopId: 's-d', orderId: 'o1', routeId: 'r1', kind: 'DELIVERY',
      previousStatus: 'ARRIVED', status: 'COMPLETED',
    }, '2026-07-09T14:30:00Z')
  );
  world = applyEvent(world, env('order.completed', { orderId: 'o1', orderNumber: 'ORD-2001', routeId: 'r1' }));
  expect(world.orders['o1'].status).toBe('COMPLETED');
  expect(world.routes['r1'].stopsCompleted).toBe(2);
  expect(world.orders['o1'].delivery.completedAt).toBe('2026-07-09T14:30:00Z');
});

test('route.planned + route.started/completed manage driver duty state', () => {
  let world = baseWorld();
  world = applyEvent(
    world,
    env('route.planned', {
      routeId: 'r2', routeNumber: 'RT-901', serviceDate: '2026-07-09',
      driverId: 'd1', vehicleId: 'v1', stopCount: 0,
    })
  );
  expect(world.routes['r2'].driver.name).toBe('Aisha Johnson');
  world = applyEvent(
    world,
    env('route.started', { routeId: 'r2', routeNumber: 'RT-901', driverId: 'd1', vehicleId: 'v1' })
  );
  expect(world.drivers['d1'].status).toBe('ON_ROUTE');
  expect(world.routes['r2'].status).toBe('ACTIVE');
  world = applyEvent(world, env('route.completed', { routeId: 'r2', routeNumber: 'RT-901' }));
  expect(world.drivers['d1'].status).toBe('AVAILABLE');
  expect(world.vehicles['v1'].status).toBe('AVAILABLE');
});

test('observation (*.record-*) events tick the counter without touching state', () => {
  const world = baseWorld();
  const next = applyEvent(
    world,
    env('order.record-updated', { table: 'orders', op: 'updated', before: {}, after: { id: 'o9' } })
  );
  expect(next.orders).toEqual(world.orders);
  expect(next.eventCount).toBe(1);
});

test('driver.location-updated feeds positions', () => {
  const world = applyEvent(
    baseWorld(),
    env('driver.location-updated', {
      driverId: 'd1', vehicleId: 'v1', routeId: 'r1',
      location: { latitude: 30.3, longitude: -97.7 }, speedMph: 34, headingDeg: 90,
    })
  );
  expect(world.positions['d1'].latitude).toBe(30.3);
  expect(world.positions['d1'].live).toBe(true);
});
