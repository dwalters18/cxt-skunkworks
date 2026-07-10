/**
 * Drivers — duty roster with live "last seen" telemetry and the graph-powered
 * blast-radius panel (what breaks if this driver goes dark).
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { cn } from '../components/base/utils';
import { useWebSocket } from '../contexts/WebSocketContext';
import api from '../api/client';
import { Phone, Clock, Route as RouteIcon, Network, X, User } from 'lucide-react';

const STATUS_STYLES = {
  AVAILABLE: 'bg-green-400/15 text-green-600 dark:text-green-400',
  ON_ROUTE: 'bg-sky-400/15 text-sky-600 dark:text-sky-400',
  OFF_DUTY: 'bg-gray-400/20 text-gray-600 dark:text-gray-400',
};

const ROUTE_STATUS_STYLES = {
  ACTIVE: 'bg-primary/15 text-emerald-600 dark:text-primary',
  PLANNED: 'bg-sky-400/15 text-sky-600 dark:text-sky-400',
  COMPLETED: 'bg-gray-400/20 text-gray-600 dark:text-gray-400',
};

function timeAgo(iso) {
  if (!iso) return 'never';
  const s = Math.max(0, Math.floor((Date.now() - new Date(iso).getTime()) / 1000));
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}

function ImpactPanel({ impact, onClose }) {
  const openOrders = impact.openOrdersAffected || [];
  const customerName = (c) => (typeof c === 'string' ? c : c?.name);
  return (
    <div className="fixed inset-0 z-50">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="absolute inset-y-0 right-0 w-full max-w-md bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-accent shadow-2xl overflow-y-auto">
        <div className="sticky top-0 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-accent px-6 py-4 flex items-start gap-2">
          <Network className="w-5 h-5 text-primary mt-0.5" />
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-foreground">Blast radius</h2>
            <p className="text-xs text-gray-500 dark:text-muted">from the world-model graph · {impact.driverName}</p>
          </div>
          <button onClick={onClose} className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-muted">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="px-6 py-4 space-y-5">
          {impact.summary && (
            <p className="text-sm text-gray-700 dark:text-foreground bg-gray-50 dark:bg-gray-800 rounded-lg p-3">{impact.summary}</p>
          )}

          <div className="grid grid-cols-3 gap-2 text-center">
            {[
              [impact.routes?.length || 0, 'routes'],
              [impact.stopCount ?? 0, 'stops'],
              [impact.ordersAffected?.length || 0, 'orders'],
            ].map(([value, label]) => (
              <div key={label} className="rounded-lg border border-gray-200 dark:border-accent p-2">
                <div className="text-xl font-bold text-gray-900 dark:text-foreground">{value}</div>
                <div className="text-xs text-gray-500 dark:text-muted">{label}</div>
              </div>
            ))}
          </div>

          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-muted mb-2">Affected routes</h3>
            {(impact.routes || []).length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-muted">None</p>
            ) : (
              <div className="space-y-1.5">
                {impact.routes.map((r) => (
                  <div key={r.id} className="flex items-center gap-2 text-sm">
                    <span className="font-semibold text-gray-900 dark:text-foreground">{r.routeNumber}</span>
                    <span className={cn('rounded-full text-xs px-2 py-0.5 font-semibold', ROUTE_STATUS_STYLES[r.status] || '')}>{r.status}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-muted mb-2">
              Open orders at risk ({openOrders.length})
            </h3>
            {openOrders.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-muted">No open orders would be affected</p>
            ) : (
              <div className="space-y-1.5">
                {openOrders.map((o) => (
                  <div key={o.id} className="flex items-center gap-2 text-sm">
                    <span className="font-semibold text-gray-900 dark:text-foreground">{o.orderNumber}</span>
                    <span className="rounded-full text-xs px-2 py-0.5 font-semibold bg-orange-400/15 text-orange-600 dark:text-orange-400">
                      {(o.status || '').replace('_', ' ')}
                    </span>
                    <span className="text-xs text-gray-500 dark:text-muted truncate">{customerName(o.customer)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

const DriversPage = () => {
  const { addEventListener } = useWebSocket();
  const [drivers, setDrivers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionError, setActionError] = useState(null);
  const [impact, setImpact] = useState(null);
  const [impactLoadingId, setImpactLoadingId] = useState(null);
  const refreshTimer = useRef(null);

  const fetchDrivers = useCallback(async () => {
    try {
      const res = await api.listDrivers();
      setDrivers(res.drivers || []);
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
      fetchDrivers();
    }, 500);
  }, [fetchDrivers]);

  useEffect(() => {
    fetchDrivers();
    // Keep the relative "last seen" labels fresh even when telemetry pauses.
    const tick = setInterval(() => setDrivers((prev) => [...prev]), 30000);
    return () => {
      clearInterval(tick);
      if (refreshTimer.current) clearTimeout(refreshTimer.current);
    };
  }, [fetchDrivers]);

  useEffect(() => {
    const unsubscribe = addEventListener((envelope) => {
      if (envelope.eventType === 'driver.location-updated') {
        const { driverId } = envelope.payload;
        setDrivers((prev) =>
          prev.map((d) => (d.id === driverId ? { ...d, locationUpdatedAt: envelope.occurredAt } : d))
        );
      } else if (envelope.eventType === 'driver.status-updated' || envelope.eventType === 'system.demo-reset') {
        scheduleRefresh();
      }
    });
    return unsubscribe;
  }, [addEventListener, scheduleRefresh]);

  const toggleDuty = async (driver) => {
    setActionError(null);
    const next = driver.status === 'AVAILABLE' ? 'OFF_DUTY' : 'AVAILABLE';
    try {
      await api.updateDriverStatus(driver.id, next);
      fetchDrivers();
    } catch (e) {
      setActionError(e.message);
    }
  };

  const showImpact = async (driver) => {
    setActionError(null);
    setImpactLoadingId(driver.id);
    try {
      setImpact(await api.driverImpact(driver.id));
    } catch (e) {
      setActionError(e.message);
    } finally {
      setImpactLoadingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-foreground">Drivers</h1>
        <p className="text-gray-600 dark:text-muted mt-1">Duty status, live telemetry, and graph-derived impact</p>
      </div>

      {actionError && (
        <div className="px-3 py-2 text-xs rounded bg-red-500/10 text-red-500 dark:text-red-400 border border-red-500/30">{actionError}</div>
      )}

      {loading ? (
        <div className="text-center text-gray-500 dark:text-muted py-16">Loading drivers…</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {drivers.map((driver) => (
            <div key={driver.id} className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-accent p-4 flex flex-col gap-3">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center shrink-0">
                  <User className="w-5 h-5 text-gray-500 dark:text-muted" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="font-semibold text-gray-900 dark:text-foreground truncate">{driver.name}</div>
                  <div className="text-xs font-mono text-gray-500 dark:text-muted">{driver.driverNumber}</div>
                </div>
                <span className={cn('rounded-full text-xs px-2 py-0.5 font-semibold whitespace-nowrap', STATUS_STYLES[driver.status] || '')}>
                  {(driver.status || '').replace('_', ' ')}
                </span>
              </div>

              <div className="space-y-1 text-xs text-gray-600 dark:text-muted">
                <div className="flex items-center gap-1.5">
                  <Phone className="w-3.5 h-3.5" /> {driver.phone || '—'}
                </div>
                {driver.activeRouteNumber && (
                  <div className="flex items-center gap-1.5 text-sky-600 dark:text-sky-400">
                    <RouteIcon className="w-3.5 h-3.5" /> on {driver.activeRouteNumber}
                  </div>
                )}
                <div className="flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5" /> last seen {timeAgo(driver.locationUpdatedAt)}
                </div>
              </div>

              <div className="mt-auto flex items-center gap-2 pt-1">
                {driver.status !== 'ON_ROUTE' && (
                  <button
                    onClick={() => toggleDuty(driver)}
                    className={cn(
                      'flex-1 text-xs font-semibold px-3 py-1.5 rounded-md',
                      driver.status === 'AVAILABLE'
                        ? 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-muted hover:bg-gray-200 dark:hover:bg-gray-700'
                        : 'bg-primary/15 text-emerald-600 dark:text-primary hover:bg-primary/25'
                    )}
                  >
                    {driver.status === 'AVAILABLE' ? 'Go off duty' : 'Go available'}
                  </button>
                )}
                <button
                  onClick={() => showImpact(driver)}
                  disabled={impactLoadingId === driver.id}
                  className="flex-1 flex items-center justify-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-md border border-gray-200 dark:border-accent text-gray-700 dark:text-foreground hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-50"
                >
                  <Network className="w-3.5 h-3.5 text-primary" />
                  {impactLoadingId === driver.id ? 'Tracing…' : 'Impact'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {impact && <ImpactPanel impact={impact} onClose={() => setImpact(null)} />}
    </div>
  );
};

export default DriversPage;
