/**
 * Order detail — one order's lifecycle, stops, parcels and event tail.
 * The evidence view: the header state is a projection, the tail at the bottom
 * is every canonical event that produced it. Live over the websocket.
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { cn } from '../components/base/utils';
import { useWebSocket } from '../contexts/WebSocketContext';
import api from '../api/client';
import { SERVICE_CHIP } from '../components/dispatch/urgency';
import { eventTone, summarizeEvent } from './DashboardPage';
import { ArrowLeft, MapPin, Package, Radio, FlaskConical, Check, Ban, SearchX } from 'lucide-react';

const LIFECYCLE = ['CREATED', 'ASSIGNED', 'IN_PROGRESS', 'COMPLETED'];

const ORDER_STATUS_CHIP = {
  CREATED: 'bg-warn/15 text-warn border border-warn/30',
  ASSIGNED: 'bg-info/15 text-info border border-info/30',
  IN_PROGRESS: 'bg-primary/15 text-primary border border-primary/30',
  COMPLETED: 'bg-foreground/5 text-muted border border-accent',
  CANCELLED: 'bg-danger/15 text-danger border border-danger/40',
};

const STOP_CHIP = {
  PENDING: 'bg-foreground/5 text-muted border border-accent',
  ARRIVED: 'bg-info/15 text-info border border-info/30',
  COMPLETED: 'bg-primary/15 text-primary border border-primary/30',
  FAILED: 'bg-danger/15 text-danger border border-danger/30',
};

const PARCEL_CHIP = {
  PENDING: 'bg-foreground/5 text-muted border border-accent',
  PICKED_UP: 'bg-info/15 text-info border border-info/30',
  DELIVERED: 'bg-primary/15 text-primary border border-primary/30',
};

const fmtTime = (iso) =>
  iso ? new Date(iso).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }) : '—';

const fmtClock = (iso) =>
  iso ? new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }) : '';

const fmtDateTime = (iso) =>
  iso ? new Date(iso).toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) : '—';

function LifecycleStepper({ status }) {
  if (status === 'CANCELLED') {
    return (
      <div className="bg-surface border border-danger/40 rounded-card shadow-card px-5 py-4 flex items-center gap-3">
        <Ban className="w-5 h-5 text-danger shrink-0" />
        <div>
          <div className="font-heading text-sm font-semibold text-danger">Order cancelled</div>
          <div className="text-xs text-muted">
            Terminal state — an order.cancelled event closed this order's lifecycle.
          </div>
        </div>
      </div>
    );
  }
  const currentIdx = LIFECYCLE.indexOf(status);
  return (
    <div className="bg-surface border border-accent rounded-card shadow-card px-5 py-4">
      <div className="flex items-center">
        {LIFECYCLE.map((step, i) => {
          const reached = i <= currentIdx;
          const current = i === currentIdx;
          return (
            <React.Fragment key={step}>
              {i > 0 && <div className={cn('flex-1 h-0.5 mx-2', reached ? 'bg-primary' : 'bg-accent')} />}
              <div className="flex items-center gap-2 shrink-0">
                <span
                  className={cn(
                    'w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold border',
                    reached ? 'bg-primary text-background border-primary' : 'bg-surface-raised text-muted border-accent',
                    current && 'ring-2 ring-primary/30'
                  )}
                >
                  {i < currentIdx ? <Check className="w-3.5 h-3.5" /> : i + 1}
                </span>
                <span className={cn('text-xs font-semibold hidden sm:inline', reached ? 'text-foreground' : 'text-muted')}>
                  {step.replace('_', ' ')}
                </span>
              </div>
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}

function StopRow({ stop, routeNumber, showControls, busy, onAdvance }) {
  return (
    <div className="rounded-xl border border-accent bg-surface-raised p-3">
      <div className="flex items-center gap-2 min-w-0">
        <span
          className={cn(
            'text-[10px] font-semibold px-1.5 py-0.5 rounded shrink-0',
            stop.kind === 'PICKUP' ? 'bg-primary/10 text-primary' : 'bg-info/10 text-info'
          )}
        >
          {stop.kind}
        </span>
        <span className="text-xs text-foreground truncate flex items-center gap-1 min-w-0" title={stop.address}>
          <MapPin className="w-3 h-3 text-muted shrink-0" /> {stop.address}
        </span>
        <span className={cn('ml-auto text-[10px] font-semibold px-2 py-0.5 rounded-full shrink-0', STOP_CHIP[stop.status])}>
          {stop.status}
        </span>
      </div>
      <div className="mt-1.5 pl-1 text-[11px] text-muted flex flex-wrap gap-x-3 gap-y-0.5">
        <span>
          window {fmtTime(stop.windowStart)}–{fmtTime(stop.windowEnd)}
        </span>
        {stop.routeId && (
          <span>
            {routeNumber || 'routed'} · stop {stop.sequence}
          </span>
        )}
        {stop.arrivedAt && <span>arrived {fmtTime(stop.arrivedAt)}</span>}
        {stop.completedAt && <span>completed {fmtTime(stop.completedAt)}</span>}
      </div>
      {showControls && (
        <div className="mt-2 pl-1 flex gap-1.5">
          {stop.status === 'PENDING' && (
            <button
              disabled={busy}
              onClick={() => onAdvance(stop.stopId, 'ARRIVED')}
              className="text-[11px] font-semibold px-2.5 py-1 rounded-lg bg-info/15 text-info border border-info/30 hover:bg-info/25 disabled:opacity-50"
            >
              Arrive
            </button>
          )}
          {stop.status === 'ARRIVED' && (
            <button
              disabled={busy}
              onClick={() => onAdvance(stop.stopId, 'COMPLETED')}
              className="text-[11px] font-semibold px-2.5 py-1 rounded-lg bg-primary text-background hover:bg-primary/85 disabled:opacity-50"
            >
              Complete
            </button>
          )}
          {(stop.status === 'PENDING' || stop.status === 'ARRIVED') && (
            <button
              disabled={busy}
              onClick={() => onAdvance(stop.stopId, 'FAILED')}
              className="text-[11px] font-semibold px-2.5 py-1 rounded-lg bg-danger/10 text-danger border border-danger/30 hover:bg-danger/20 disabled:opacity-50"
            >
              Fail
            </button>
          )}
        </div>
      )}
    </div>
  );
}

const OrderDetailPage = () => {
  const { orderId } = useParams();
  const navigate = useNavigate();
  const { addEventListener } = useWebSocket();

  const [order, setOrder] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [loadError, setLoadError] = useState(null);
  const [actionError, setActionError] = useState(null);
  const [drivers, setDrivers] = useState([]);
  const [busy, setBusy] = useState(false);
  const [devMode, setDevMode] = useState(true);
  const [expandedEventId, setExpandedEventId] = useState(null);
  const [liveIds, setLiveIds] = useState(() => new Set());
  const highlightTimersRef = useRef([]);
  const refetchTimerRef = useRef(null);

  // Initial load: order + its event tail in parallel.
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setNotFound(false);
    setLoadError(null);
    Promise.all([api.getOrder(orderId), api.orderEvents(orderId)])
      .then(([o, ev]) => {
        if (cancelled) return;
        setOrder(o);
        setEvents(ev.events || []);
      })
      .catch((e) => {
        if (cancelled) return;
        if (e.status === 404) setNotFound(true);
        else setLoadError(e.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [orderId]);

  const refetchOrder = useCallback(async () => {
    try {
      setOrder(await api.getOrder(orderId));
    } catch (e) {
      if (e.status === 404) setNotFound(true);
    }
  }, [orderId]);

  const refetchAll = useCallback(async () => {
    try {
      const [o, ev] = await Promise.all([api.getOrder(orderId), api.orderEvents(orderId)]);
      setOrder(o);
      setEvents((prev) => {
        const server = ev.events || [];
        const seen = new Set(server.map((e) => e.eventId));
        const extras = prev.filter((e) => !seen.has(e.eventId));
        return [...extras, ...server].sort((a, b) => new Date(b.observedAt) - new Date(a.observedAt));
      });
    } catch (e) {
      if (e.status === 404) setNotFound(true);
      else setActionError(e.message);
    }
  }, [orderId]);

  // Coalesce websocket-triggered refetches into one call per burst.
  const scheduleOrderRefetch = useCallback(() => {
    if (refetchTimerRef.current) return;
    refetchTimerRef.current = setTimeout(() => {
      refetchTimerRef.current = null;
      refetchOrder();
    }, 400);
  }, [refetchOrder]);

  // Live tail: any envelope referencing this order lands here first.
  useEffect(() => {
    const unsubscribe = addEventListener((envelope) => {
      const refs = envelope.entityRefs || [];
      if (!refs.some((r) => r.type === 'order' && r.id === orderId)) return;
      setEvents((prev) =>
        prev.some((e) => e.eventId === envelope.eventId) ? prev : [envelope, ...prev]
      );
      setLiveIds((prev) => new Set(prev).add(envelope.eventId));
      const timer = setTimeout(() => {
        setLiveIds((prev) => {
          const next = new Set(prev);
          next.delete(envelope.eventId);
          return next;
        });
      }, 4000);
      highlightTimersRef.current.push(timer);
      scheduleOrderRefetch();
    });
    return unsubscribe;
  }, [addEventListener, orderId, scheduleOrderRefetch]);

  useEffect(() => {
    const highlightTimers = highlightTimersRef.current;
    const refetchTimer = refetchTimerRef;
    return () => {
      highlightTimers.forEach(clearTimeout);
      if (refetchTimer.current) clearTimeout(refetchTimer.current);
    };
  }, []);

  // Drivers are only needed for the CREATED-state assign control.
  useEffect(() => {
    if (order?.status !== 'CREATED') return;
    api
      .listDrivers()
      .then((res) => setDrivers((res.drivers || []).filter((d) => d.status !== 'OFF_DUTY')))
      .catch(() => {});
  }, [order?.status]);

  const advanceStop = async (stopId, status) => {
    setBusy(true);
    setActionError(null);
    try {
      await api.updateStopStatus(stopId, status);
      await refetchAll();
    } catch (e) {
      setActionError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const assignDriver = async (driverId) => {
    if (!driverId) return;
    setBusy(true);
    setActionError(null);
    try {
      await api.assignOrderToDriver(orderId, driverId);
      await refetchAll();
    } catch (e) {
      setActionError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const cancelOrder = async () => {
    if (!window.confirm(`Cancel ${order.orderNumber}? This emits order.cancelled.`)) return;
    setBusy(true);
    setActionError(null);
    try {
      await api.cancelOrder(orderId, 'Cancelled from order detail');
      await refetchAll();
    } catch (e) {
      setActionError(e.message);
    } finally {
      setBusy(false);
    }
  };

  if (notFound) {
    return (
      <div className="max-w-lg mx-auto mt-16 bg-surface border border-accent rounded-card shadow-card p-8 text-center">
        <SearchX className="w-8 h-8 text-muted mx-auto" />
        <h1 className="mt-3 font-heading text-lg font-semibold text-foreground">Order not found</h1>
        <p className="mt-1 text-sm text-muted">
          This order isn't in the world model — it may have been swept away by a demo reset.
        </p>
        <button
          onClick={() => navigate('/orders')}
          className="mt-5 inline-flex items-center gap-1.5 px-4 py-2 text-sm font-semibold rounded-xl bg-primary text-background hover:bg-primary/85"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Orders
        </button>
      </div>
    );
  }

  if (loading) {
    return <div className="text-center text-muted py-16">Loading order…</div>;
  }

  if (loadError || !order) {
    return (
      <div className="space-y-4">
        <div className="px-3 py-2 text-xs rounded-lg bg-danger/10 text-danger border border-danger/30">
          {loadError || 'Failed to load order'}
        </div>
        <button
          onClick={() => navigate('/orders')}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-muted hover:text-primary"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Orders
        </button>
      </div>
    );
  }

  const stops = [order.pickup, order.delivery].filter(Boolean);
  const nextOpenIdx = stops.findIndex((s) => s.status === 'PENDING' || s.status === 'ARRIVED');

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start gap-4">
        <div className="min-w-0">
          <button
            onClick={() => navigate('/orders')}
            className="flex items-center gap-1 text-xs font-semibold text-muted hover:text-primary"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Orders
          </button>
          <div className="mt-1 flex flex-wrap items-center gap-2.5">
            <h1 className="font-heading text-2xl font-bold text-foreground">{order.orderNumber}</h1>
            <span
              className={cn(
                'text-[10px] font-semibold px-2 py-0.5 rounded-full',
                SERVICE_CHIP[order.serviceLevel] || SERVICE_CHIP.ROUTINE
              )}
            >
              {order.serviceLevel}
            </span>
            <span
              className={cn(
                'text-[10px] font-semibold px-2 py-0.5 rounded-full',
                ORDER_STATUS_CHIP[order.status] || ORDER_STATUS_CHIP.COMPLETED
              )}
            >
              {(order.status || '').replace('_', ' ')}
            </span>
          </div>
          <div className="mt-1 text-xs text-muted">
            {order.customer?.name} · {order.parcelCount} parcel{order.parcelCount === 1 ? '' : 's'} · created{' '}
            {fmtDateTime(order.createdAt)}
          </div>
          {order.notes && <div className="mt-1 text-xs text-muted italic">“{order.notes}”</div>}
        </div>

        <div className="ml-auto flex items-center gap-2">
          {order.status === 'CREATED' && (
            <select
              value=""
              disabled={busy}
              onChange={(e) => assignDriver(e.target.value)}
              className="text-xs font-semibold px-2.5 py-2 rounded-xl border border-accent bg-surface-raised text-foreground focus:outline-none focus:ring-2 focus:ring-primary/60 disabled:opacity-50"
            >
              <option value="">Assign to driver…</option>
              {drivers.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({(d.status || '').replace('_', ' ').toLowerCase()})
                </option>
              ))}
            </select>
          )}
          {(order.status === 'CREATED' || order.status === 'ASSIGNED') && (
            <button
              onClick={cancelOrder}
              disabled={busy}
              className="flex items-center gap-1.5 text-xs font-semibold px-3 py-2 rounded-xl bg-danger/10 text-danger border border-danger/30 hover:bg-danger/20 disabled:opacity-50"
            >
              <Ban className="w-3.5 h-3.5" /> Cancel order
            </button>
          )}
        </div>
      </div>

      {actionError && (
        <div className="px-3 py-2 text-xs rounded-lg bg-danger/10 text-danger border border-danger/30">
          {actionError}
        </div>
      )}

      <LifecycleStepper status={order.status} />

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 items-start">
        <section className="bg-surface border border-accent rounded-card shadow-card p-5">
          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4 text-primary" />
            <h2 className="font-heading text-sm font-semibold text-foreground">Stops</h2>
            {order.routeNumber && (
              <span className="text-[11px] text-muted">
                {order.routeNumber}
                {order.driverName ? ` · ${order.driverName}` : ''}
              </span>
            )}
            <button
              onClick={() => setDevMode((v) => !v)}
              className={cn(
                'ml-auto flex items-center gap-1.5 text-[11px] font-semibold px-2.5 py-1 rounded-full border transition-colors',
                devMode
                  ? 'bg-warn/15 text-warn border-warn/30'
                  : 'bg-foreground/5 text-muted border-accent hover:text-foreground'
              )}
              title="Manual stop progress — the dev stand-in for the driver app"
            >
              <FlaskConical className="w-3.5 h-3.5" /> Manual progress (dev)
            </button>
          </div>
          <div className="mt-3 space-y-2">
            {stops.length === 0 ? (
              <div className="text-center text-xs text-muted py-6">No stops recorded for this order.</div>
            ) : (
              stops.map((stop, i) => (
                <StopRow
                  key={stop.stopId}
                  stop={stop}
                  routeNumber={order.routeNumber}
                  showControls={devMode && i === nextOpenIdx}
                  busy={busy}
                  onAdvance={advanceStop}
                />
              ))
            )}
          </div>
        </section>

        <section className="bg-surface border border-accent rounded-card shadow-card p-5">
          <div className="flex items-center gap-2">
            <Package className="w-4 h-4 text-primary" />
            <h2 className="font-heading text-sm font-semibold text-foreground">Parcels</h2>
            <span className="text-[11px] text-muted">({order.parcels?.length || 0})</span>
          </div>
          <div className="mt-3 space-y-1.5">
            {(order.parcels || []).length === 0 ? (
              <div className="text-center text-xs text-muted py-6">No parcels recorded.</div>
            ) : (
              order.parcels.map((p) => (
                <div
                  key={p.id}
                  className="flex items-center gap-3 rounded-xl border border-accent bg-surface-raised px-3 py-2 text-xs"
                >
                  <span className="font-mono text-foreground shrink-0">{p.barcode}</span>
                  <span className="text-muted flex-1 truncate" title={p.description}>
                    {p.description}
                  </span>
                  <span className="text-muted shrink-0">{p.weightKg != null ? `${p.weightKg} kg` : '—'}</span>
                  <span
                    className={cn(
                      'text-[10px] font-semibold px-2 py-0.5 rounded-full shrink-0',
                      PARCEL_CHIP[p.status] || PARCEL_CHIP.PENDING
                    )}
                  >
                    {(p.status || '').replace('_', ' ')}
                  </span>
                </div>
              ))
            )}
          </div>
        </section>
      </div>

      <section className="bg-surface border border-accent rounded-card shadow-card">
        <div className="px-5 py-4 border-b border-accent">
          <div className="flex items-center gap-2">
            <Radio className="w-4 h-4 text-primary" />
            <h2 className="font-heading text-sm font-semibold text-foreground">Event tail</h2>
            <span className="ml-auto text-[11px] text-muted">{events.length} events</span>
          </div>
          <p className="mt-0.5 text-[11px] text-muted">
            every canonical event referencing this order — the evidence timeline
          </p>
        </div>
        <div className="max-h-[480px] overflow-y-auto divide-y divide-accent/50">
          {events.length === 0 ? (
            <div className="px-5 py-8 text-center text-xs text-muted">No events yet for this order.</div>
          ) : (
            events.map((envelope) => (
              <div
                key={envelope.eventId}
                className={cn('transition-colors', liveIds.has(envelope.eventId) && 'bg-primary/5')}
              >
                <button
                  onClick={() =>
                    setExpandedEventId(expandedEventId === envelope.eventId ? null : envelope.eventId)
                  }
                  className="w-full text-left px-5 py-2 hover:bg-white/[0.03]"
                >
                  <div className="flex items-center gap-3 text-xs min-w-0">
                    <span className="font-mono text-muted w-16 shrink-0">{fmtClock(envelope.observedAt)}</span>
                    <span className={cn('font-mono font-semibold w-52 shrink-0 truncate', eventTone(envelope.eventType))}>
                      {envelope.eventType}
                    </span>
                    <span className="shrink-0 rounded text-[10px] px-1.5 py-0.5 bg-foreground/5 text-muted">
                      {envelope.sourceSystem}
                    </span>
                    <span className="text-muted truncate">{summarizeEvent(envelope)}</span>
                  </div>
                </button>
                {expandedEventId === envelope.eventId && (
                  <pre className="mx-5 mb-3 p-3 rounded-xl bg-background border border-accent text-[11px] leading-relaxed font-mono text-foreground overflow-x-auto">
                    {JSON.stringify(envelope, null, 2)}
                  </pre>
                )}
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );
};

export default OrderDetailPage;
