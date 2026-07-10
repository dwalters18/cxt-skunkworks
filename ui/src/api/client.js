/**
 * API client — the single place the UI talks to the backend.
 *
 * All endpoints return camelCase JSON (the same wire dialect as the canonical
 * event envelope). Base URL is same-origin by default: nginx proxies /api in
 * Docker, the CRA dev proxy handles local dev.
 */

const BASE = process.env.REACT_APP_BACKEND_URL || '';

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    let detail;
    try {
      const body = await res.json();
      detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
    } catch {
      detail = res.statusText;
    }
    const err = new Error(detail || `HTTP ${res.status}`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

const get = (path) => request(path);
const post = (path, body) => request(path, { method: 'POST', body: JSON.stringify(body ?? {}) });
const patch = (path, body) => request(path, { method: 'PATCH', body: JSON.stringify(body ?? {}) });

export const api = {
  // orders
  listOrders: (params = {}) => get(`/api/orders?${new URLSearchParams(params)}`),
  unassignedOrders: () => get('/api/orders/unassigned'),
  getOrder: (id) => get(`/api/orders/${id}`),
  orderEvents: (id, limit = 200) => get(`/api/orders/${id}/events?limit=${limit}`),
  createOrder: (body) => post('/api/orders', body),
  assignOrder: (id, routeId) => post(`/api/orders/${id}/assign`, { routeId }),
  assignOrderToDriver: (id, driverId) => post(`/api/orders/${id}/assign`, { driverId }),
  cancelOrder: (id, reason) => post(`/api/orders/${id}/cancel`, { reason }),

  // routes
  listRoutes: (status) => get(`/api/routes${status ? `?status=${status}` : ''}`),
  getRoute: (id) => get(`/api/routes/${id}`),
  createRoute: (body) => post('/api/routes', body),
  startRoute: (id) => post(`/api/routes/${id}/start`),

  // stops
  updateStopStatus: (id, status) => post(`/api/stops/${id}/status`, { status }),

  // fleet & people
  listDrivers: () => get('/api/drivers'),
  updateDriverStatus: (id, status) => patch(`/api/drivers/${id}/status`, { status }),
  listVehicles: () => get('/api/vehicles'),
  updateVehicleStatus: (id, status) => patch(`/api/vehicles/${id}/status`, { status }),
  listCustomers: () => get('/api/customers'),
  listDepots: () => get('/api/depots'),

  // events & analytics
  recentEvents: (params = {}) => get(`/api/events/recent?${new URLSearchParams(params)}`),
  eventCatalog: () => get('/api/events/catalog'),
  publishEvent: (body) => post('/api/events/publish', body),
  analyticsSummary: () => get('/api/analytics/summary'),
  eventsByType: (hours = 24) => get(`/api/analytics/events-by-type?hours=${hours}`),
  eventVolume: (minutes = 60) => get(`/api/analytics/event-volume?minutes=${minutes}`),

  // graph
  driverImpact: (id) => get(`/api/graph/impact/driver/${id}`),
  graphOverview: () => get('/api/graph/overview'),

  // health
  health: () => get('/api/health'),
};

export default api;
