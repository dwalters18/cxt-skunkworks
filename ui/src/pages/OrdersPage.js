/**
 * Orders — every order in the world model, with assign/cancel actions and
 * a simple order-entry form. Live: refetches on order.* / stop.status-updated.
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { cn } from '../components/base/utils';
import { useWebSocket } from '../contexts/WebSocketContext';
import api from '../api/client';
import { ChevronRight, ChevronDown, Package, Plus, X } from 'lucide-react';

const DEPOT = { address: '2401 E 6th St, Austin, TX 78702', latitude: 30.2601, longitude: -97.7185 };

const STATUSES = ['CREATED', 'ASSIGNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'];

const STATUS_STYLES = {
  CREATED: 'bg-orange-400/15 text-orange-600 dark:text-orange-400',
  ASSIGNED: 'bg-sky-400/15 text-sky-600 dark:text-sky-400',
  IN_PROGRESS: 'bg-primary/15 text-emerald-600 dark:text-primary',
  COMPLETED: 'bg-gray-400/20 text-gray-600 dark:text-gray-400',
  CANCELLED: 'bg-red-400/15 text-red-600 dark:text-red-400',
};

const StatusChip = ({ status }) => (
  <span className={cn('rounded-full text-xs px-2 py-0.5 font-semibold whitespace-nowrap', STATUS_STYLES[status] || STATUS_STYLES.COMPLETED)}>
    {(status || '').replace('_', ' ')}
  </span>
);

const fmtTime = (iso) =>
  iso ? new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '—';

function StopCell({ stop }) {
  if (!stop) return <span className="text-gray-400 dark:text-muted">—</span>;
  return (
    <div className="min-w-0">
      <div className="truncate max-w-[220px] text-gray-900 dark:text-foreground" title={stop.address}>
        {stop.address}
      </div>
      <div className="text-xs text-gray-500 dark:text-muted">
        {fmtTime(stop.windowStart)}–{fmtTime(stop.windowEnd)}
        <span className="ml-1.5 text-[10px] uppercase tracking-wide">{stop.status?.toLowerCase()}</span>
      </div>
    </div>
  );
}

function NewOrderModal({ customers, onClose, onCreated }) {
  const [form, setForm] = useState({
    customerId: customers[0]?.id || '',
    pickupAtDepot: true,
    deliveryAddress: '600 Congress Ave, Austin, TX 78701',
    deliveryLat: 30.2672,
    deliveryLng: -97.7431,
    parcelCount: 1,
    notes: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const set = (key, value) => setForm((f) => ({ ...f, [key]: value }));
  const customer = customers.find((c) => c.id === form.customerId);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!customer) return;
    setSubmitting(true);
    setError(null);
    try {
      const pickup = form.pickupAtDepot
        ? { ...DEPOT }
        : { address: customer.address, latitude: customer.latitude, longitude: customer.longitude };
      await api.createOrder({
        customerId: customer.id,
        pickup,
        delivery: {
          address: form.deliveryAddress,
          latitude: Number(form.deliveryLat),
          longitude: Number(form.deliveryLng),
        },
        parcelCount: Math.min(10, Math.max(1, Number(form.parcelCount) || 1)),
        notes: form.notes || undefined,
      });
      onCreated();
    } catch (err) {
      setError(err.message);
      setSubmitting(false);
    }
  };

  const inputClass =
    'w-full px-3 py-2 text-sm rounded-md border border-gray-200 dark:border-accent bg-white dark:bg-gray-800 text-gray-900 dark:text-foreground focus:outline-none focus:ring-2 focus:ring-primary';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <form
        onSubmit={handleSubmit}
        className="relative w-full max-w-lg bg-white dark:bg-gray-900 rounded-lg shadow-2xl border border-gray-200 dark:border-accent p-6 space-y-4"
      >
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-foreground">New Order</h2>
          <button type="button" onClick={onClose} className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-muted">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-500 dark:text-muted mb-1">Customer</label>
          <select value={form.customerId} onChange={(e) => set('customerId', e.target.value)} className={inputClass}>
            {customers.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.code})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-foreground">
            <input
              type="checkbox"
              checked={form.pickupAtDepot}
              onChange={(e) => set('pickupAtDepot', e.target.checked)}
              className="accent-emerald-500"
            />
            Pickup at depot
          </label>
          <p className="mt-1 text-xs text-gray-500 dark:text-muted">
            {form.pickupAtDepot ? DEPOT.address : `Pickup at customer: ${customer?.address || '—'}`}
          </p>
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-500 dark:text-muted mb-1">Delivery address</label>
          <input value={form.deliveryAddress} onChange={(e) => set('deliveryAddress', e.target.value)} className={inputClass} required />
          <div className="mt-2 grid grid-cols-2 gap-2">
            <div>
              <label className="block text-xs font-semibold text-gray-500 dark:text-muted mb-1">Latitude</label>
              <input type="number" step="0.0001" value={form.deliveryLat} onChange={(e) => set('deliveryLat', e.target.value)} className={inputClass} />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-500 dark:text-muted mb-1">Longitude</label>
              <input type="number" step="0.0001" value={form.deliveryLng} onChange={(e) => set('deliveryLng', e.target.value)} className={inputClass} />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="block text-xs font-semibold text-gray-500 dark:text-muted mb-1">Parcels (1–10)</label>
            <input type="number" min="1" max="10" value={form.parcelCount} onChange={(e) => set('parcelCount', e.target.value)} className={inputClass} />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-500 dark:text-muted mb-1">Notes</label>
            <input value={form.notes} onChange={(e) => set('notes', e.target.value)} placeholder="optional" className={inputClass} />
          </div>
        </div>

        {error && (
          <div className="px-3 py-2 text-xs rounded bg-red-500/10 text-red-500 dark:text-red-400 border border-red-500/30">{error}</div>
        )}

        <div className="flex justify-end gap-2 pt-1">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-semibold rounded-md text-gray-600 dark:text-muted hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting || !form.customerId}
            className="px-4 py-2 text-sm font-semibold rounded-md bg-primary text-background hover:bg-primary/80 disabled:opacity-50"
          >
            {submitting ? 'Creating…' : 'Create order'}
          </button>
        </div>
      </form>
    </div>
  );
}

const OrdersPage = () => {
  const { addEventListener } = useWebSocket();
  const [orders, setOrders] = useState([]);
  const [routes, setRoutes] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('ALL');
  const [expandedId, setExpandedId] = useState(null);
  const [showNewOrder, setShowNewOrder] = useState(false);
  const [actionError, setActionError] = useState(null);
  const refreshTimer = useRef(null);

  const fetchAll = useCallback(async () => {
    try {
      const [ordersRes, routesRes, customersRes] = await Promise.all([
        api.listOrders({ limit: 200 }),
        api.listRoutes(),
        api.listCustomers(),
      ]);
      setOrders(ordersRes.orders || []);
      setRoutes(routesRes.routes || []);
      setCustomers(customersRes.customers || []);
    } catch (e) {
      setActionError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const scheduleRefresh = useCallback(() => {
    if (refreshTimer.current) return;
    refreshTimer.current = setTimeout(() => {
      refreshTimer.current = null;
      fetchAll();
    }, 500);
  }, [fetchAll]);

  useEffect(() => {
    fetchAll();
    return () => refreshTimer.current && clearTimeout(refreshTimer.current);
  }, [fetchAll]);

  useEffect(() => {
    const unsubscribe = addEventListener(({ eventType }) => {
      if (eventType.startsWith('order.') || eventType === 'stop.status-updated' || eventType === 'system.demo-reset') {
        scheduleRefresh();
      }
    });
    return unsubscribe;
  }, [addEventListener, scheduleRefresh]);

  const handleAssign = async (orderId, routeId) => {
    setActionError(null);
    try {
      await api.assignOrder(orderId, routeId);
      fetchAll();
    } catch (e) {
      setActionError(e.message);
    }
  };

  const handleCancel = async (orderId) => {
    setActionError(null);
    try {
      await api.cancelOrder(orderId, 'Cancelled from Orders page');
      fetchAll();
    } catch (e) {
      setActionError(e.message);
    }
  };

  const counts = orders.reduce((acc, o) => ({ ...acc, [o.status]: (acc[o.status] || 0) + 1 }), {});
  const visible = filter === 'ALL' ? orders : orders.filter((o) => o.status === filter);
  const assignableRoutes = routes.filter((r) => r.status !== 'COMPLETED');

  const filterChip = (id, label, count) => (
    <button
      key={id}
      onClick={() => setFilter(id)}
      className={cn(
        'rounded-full text-xs px-3 py-1 font-semibold transition-colors',
        filter === id
          ? 'bg-primary text-background'
          : 'bg-white dark:bg-gray-900 border border-gray-200 dark:border-accent text-gray-600 dark:text-muted hover:bg-gray-100 dark:hover:bg-gray-800'
      )}
    >
      {label} · {count}
    </button>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-foreground">Orders</h1>
          <p className="text-gray-600 dark:text-muted mt-1">Pickup → delivery, each order carried by two stops on a route</p>
        </div>
        <button
          onClick={() => setShowNewOrder(true)}
          className="flex items-center gap-1.5 px-4 py-2 text-sm font-semibold rounded-md bg-primary text-background hover:bg-primary/80"
        >
          <Plus className="w-4 h-4" /> New Order
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        {filterChip('ALL', 'All', orders.length)}
        {STATUSES.map((s) => filterChip(s, s.replace('_', ' '), counts[s] || 0))}
      </div>

      {actionError && (
        <div className="px-3 py-2 text-xs rounded bg-red-500/10 text-red-500 dark:text-red-400 border border-red-500/30">{actionError}</div>
      )}

      <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-accent overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs uppercase tracking-wide text-gray-500 dark:text-muted border-b border-gray-200 dark:border-accent">
              <th className="px-3 py-3 w-8" />
              <th className="px-3 py-3">Order #</th>
              <th className="px-3 py-3">Customer</th>
              <th className="px-3 py-3">Status</th>
              <th className="px-3 py-3">Parcels</th>
              <th className="px-3 py-3">Pickup</th>
              <th className="px-3 py-3">Delivery</th>
              <th className="px-3 py-3">Route</th>
              <th className="px-3 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={9} className="px-3 py-10 text-center text-gray-500 dark:text-muted">Loading orders…</td>
              </tr>
            ) : visible.length === 0 ? (
              <tr>
                <td colSpan={9} className="px-3 py-10 text-center text-gray-500 dark:text-muted">No orders match this filter</td>
              </tr>
            ) : (
              visible.map((order) => {
                const expanded = expandedId === order.id;
                return (
                  <React.Fragment key={order.id}>
                    <tr className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                      <td className="px-3 py-2.5">
                        <button
                          onClick={() => setExpandedId(expanded ? null : order.id)}
                          className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-muted"
                          title="Show parcels"
                        >
                          {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                        </button>
                      </td>
                      <td className="px-3 py-2.5 font-semibold text-gray-900 dark:text-foreground whitespace-nowrap">{order.orderNumber}</td>
                      <td className="px-3 py-2.5 text-gray-700 dark:text-foreground">
                        <span className="truncate block max-w-[180px]" title={order.customer?.name}>{order.customer?.name || '—'}</span>
                      </td>
                      <td className="px-3 py-2.5"><StatusChip status={order.status} /></td>
                      <td className="px-3 py-2.5 text-gray-700 dark:text-foreground">{order.parcelCount}</td>
                      <td className="px-3 py-2.5"><StopCell stop={order.pickup} /></td>
                      <td className="px-3 py-2.5"><StopCell stop={order.delivery} /></td>
                      <td className="px-3 py-2.5 whitespace-nowrap">
                        {order.routeNumber ? (
                          <div>
                            <div className="text-gray-900 dark:text-foreground font-medium">{order.routeNumber}</div>
                            <div className="text-xs text-gray-500 dark:text-muted">{order.driverName || 'no driver'}</div>
                          </div>
                        ) : (
                          <span className="text-gray-400 dark:text-muted">—</span>
                        )}
                      </td>
                      <td className="px-3 py-2.5">
                        <div className="flex items-center gap-1.5">
                          {order.status === 'CREATED' && (
                            <select
                              value=""
                              onChange={(e) => e.target.value && handleAssign(order.id, e.target.value)}
                              className="text-xs px-2 py-1 rounded border border-gray-200 dark:border-accent bg-white dark:bg-gray-800 text-gray-700 dark:text-foreground"
                            >
                              <option value="">Assign…</option>
                              {assignableRoutes.map((r) => (
                                <option key={r.id} value={r.id}>
                                  {r.routeNumber} ({r.status.toLowerCase()}, {r.stopsTotal} stops)
                                </option>
                              ))}
                            </select>
                          )}
                          {(order.status === 'CREATED' || order.status === 'ASSIGNED') && (
                            <button
                              onClick={() => handleCancel(order.id)}
                              className="text-xs px-2 py-1 rounded font-semibold text-red-500 dark:text-red-400 hover:bg-red-500/10"
                            >
                              Cancel
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                    {expanded && (
                      <tr className="border-b border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-800/40">
                        <td colSpan={9} className="px-6 py-3">
                          <div className="flex items-center gap-1.5 text-xs font-semibold text-gray-500 dark:text-muted mb-2">
                            <Package className="w-3.5 h-3.5" /> Parcels ({order.parcels?.length || 0})
                          </div>
                          {(order.parcels || []).length === 0 ? (
                            <div className="text-xs text-gray-500 dark:text-muted">No parcels recorded</div>
                          ) : (
                            <div className="space-y-1">
                              {order.parcels.map((p) => (
                                <div key={p.id} className="flex items-center gap-3 text-xs">
                                  <span className="font-mono text-gray-900 dark:text-foreground">{p.barcode}</span>
                                  <span className="text-gray-600 dark:text-muted flex-1 truncate">{p.description}</span>
                                  <span className="text-gray-600 dark:text-muted">{p.weightKg} kg</span>
                                  <span
                                    className={cn(
                                      'rounded-full px-2 py-0.5 font-semibold',
                                      p.status === 'DELIVERED'
                                        ? 'bg-primary/15 text-emerald-600 dark:text-primary'
                                        : 'bg-gray-400/20 text-gray-600 dark:text-gray-400'
                                    )}
                                  >
                                    {p.status}
                                  </span>
                                </div>
                              ))}
                            </div>
                          )}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {showNewOrder && (
        <NewOrderModal
          customers={customers}
          onClose={() => setShowNewOrder(false)}
          onCreated={() => {
            setShowNewOrder(false);
            fetchAll();
          }}
        />
      )}
    </div>
  );
};

export default OrdersPage;
