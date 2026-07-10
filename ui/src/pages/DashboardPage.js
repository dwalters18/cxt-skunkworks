/**
 * Dashboard — KPI tiles over the analytics summary plus a live tail of the
 * canonical event feed. Location telemetry is deliberately excluded from the
 * activity panel to keep the signal readable.
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { cn } from '../components/base/utils';
import { useWebSocket } from '../contexts/WebSocketContext';
import api from '../api/client';
import { Package, Route as RouteIcon, Users, Truck, Boxes, Timer, Activity, Radio } from 'lucide-react';

export function eventTone(eventType) {
  if (eventType.includes('.record-')) return 'text-gray-500 dark:text-gray-400';
  if (eventType.startsWith('system.')) return 'text-red-500 dark:text-red-400';
  if (eventType.startsWith('order.')) return 'text-emerald-600 dark:text-primary';
  if (eventType.startsWith('stop.')) return 'text-sky-600 dark:text-sky-400';
  if (eventType.startsWith('driver.')) return 'text-violet-600 dark:text-violet-400';
  if (eventType.startsWith('route.')) return 'text-amber-600 dark:text-amber-400';
  if (eventType.startsWith('vehicle.')) return 'text-pink-600 dark:text-pink-400';
  return 'text-gray-500 dark:text-gray-400';
}

export function summarizeEvent({ eventType, payload = {} }) {
  switch (eventType) {
    case 'order.created':
      return `${payload.orderNumber} · ${payload.customerName}`;
    case 'order.assigned':
      return `${payload.orderNumber} → ${payload.routeNumber}`;
    case 'order.completed':
      return `${payload.orderNumber} delivered`;
    case 'order.cancelled':
      return `${payload.orderNumber} — ${payload.reason || 'no reason given'}`;
    case 'stop.status-updated':
      return `${payload.kind} ${payload.previousStatus} → ${payload.status}`;
    case 'route.planned':
      return `${payload.routeNumber} · ${payload.stopCount} stops`;
    case 'route.started':
      return `${payload.routeNumber} under way`;
    case 'route.completed':
      return `${payload.routeNumber} finished`;
    case 'driver.status-updated':
      return `${payload.driverName}: ${payload.previousStatus} → ${payload.status}`;
    case 'driver.location-updated':
      return payload.speedMph != null ? `${Math.round(payload.speedMph)} mph` : 'position update';
    case 'vehicle.status-updated':
      return `${payload.vehicleNumber}: ${payload.previousStatus} → ${payload.status}`;
    case 'system.demo-reset':
      return `world reseeded (${payload.seedVersion})`;
    default: {
      if (eventType.includes('.record-')) {
        const row = payload.after || payload.before || {};
        const label =
          row.order_number || row.route_number || row.driver_number || row.vehicle_number ||
          row.barcode || row.code || row.name || (row.id ? String(row.id).slice(0, 8) : '');
        return [payload.table, payload.op, label && `· ${label}`].filter(Boolean).join(' ');
      }
      return '';
    }
  }
}

const fmtClock = (iso) =>
  iso ? new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }) : '';

function KpiTile({ icon: Icon, label, value, sub }) {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-accent p-4">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-muted">
        <Icon className="w-4 h-4 text-primary" /> {label}
      </div>
      <div className="mt-2 text-2xl font-bold text-gray-900 dark:text-foreground">{value}</div>
      {sub && <div className="mt-1 text-xs text-gray-500 dark:text-muted">{sub}</div>}
    </div>
  );
}

const DashboardPage = () => {
  const { events, isConnected, addEventListener } = useWebSocket();
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);
  const refreshTimer = useRef(null);

  const fetchSummary = useCallback(async () => {
    try {
      setSummary(await api.analyticsSummary());
      setError(null);
    } catch (e) {
      setError(e.message);
    }
  }, []);

  const scheduleRefresh = useCallback(() => {
    if (refreshTimer.current) return;
    refreshTimer.current = setTimeout(() => {
      refreshTimer.current = null;
      fetchSummary();
    }, 1000);
  }, [fetchSummary]);

  useEffect(() => {
    fetchSummary();
    const poll = setInterval(fetchSummary, 10000);
    return () => {
      clearInterval(poll);
      if (refreshTimer.current) clearTimeout(refreshTimer.current);
    };
  }, [fetchSummary]);

  useEffect(() => {
    const unsubscribe = addEventListener(({ eventType }) => {
      if (eventType !== 'driver.location-updated') scheduleRefresh();
    });
    return unsubscribe;
  }, [addEventListener, scheduleRefresh]);

  const activity = events.filter((e) => e.eventType !== 'driver.location-updated').slice(0, 12);

  const onTime =
    summary?.stops?.onTimePercentage == null ? '—' : `${Math.round(summary.stops.onTimePercentage)}%`;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-foreground">Dashboard</h1>
        <p className="text-gray-600 dark:text-muted mt-1">Operational state of the Austin demo world, rebuilt from the event backbone</p>
      </div>

      {error && (
        <div className="px-3 py-2 text-xs rounded bg-red-500/10 text-red-500 dark:text-red-400 border border-red-500/30">{error}</div>
      )}

      {!summary ? (
        <div className="text-center text-gray-500 dark:text-muted py-16">Loading summary…</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <KpiTile
            icon={Package}
            label="Orders"
            value={summary.orders.total}
            sub={`${summary.orders.created} created · ${summary.orders.assigned} assigned · ${summary.orders.in_progress} in progress · ${summary.orders.completed} completed`}
          />
          <KpiTile
            icon={RouteIcon}
            label="Active routes"
            value={`${summary.routes.active} of ${summary.routes.total}`}
            sub={`${summary.routes.planned} planned · ${summary.routes.completed} completed`}
          />
          <KpiTile
            icon={Users}
            label="Drivers on route"
            value={summary.drivers.on_route}
            sub={`${summary.drivers.available} available · ${summary.drivers.off_duty} off duty`}
          />
          <KpiTile
            icon={Truck}
            label="Vehicles in service"
            value={summary.vehicles.in_service}
            sub={`${summary.vehicles.available} available · ${summary.vehicles.maintenance} in maintenance`}
          />
          <KpiTile
            icon={Boxes}
            label="Parcels delivered"
            value={`${summary.parcels.delivered} / ${summary.parcels.total}`}
          />
          <KpiTile
            icon={Timer}
            label="On-time stops"
            value={onTime}
            sub={`${summary.stops.completed_in_window} of ${summary.stops.completed} completed in window`}
          />
          <KpiTile icon={Activity} label="Events last hour" value={summary.eventsLastHour} sub="across the backbone" />
        </div>
      )}

      <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-accent">
        <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-200 dark:border-accent">
          <Radio className="w-4 h-4 text-primary" />
          <h2 className="text-sm font-semibold text-gray-900 dark:text-foreground">Live activity</h2>
          <span className={cn('w-2 h-2 rounded-full ml-1', isConnected ? 'bg-primary animate-pulse' : 'bg-red-500')} />
          <span className="ml-auto text-xs text-gray-500 dark:text-muted">location telemetry hidden</span>
        </div>
        <div className="divide-y divide-gray-100 dark:divide-gray-800">
          {activity.length === 0 ? (
            <div className="px-4 py-8 text-center text-sm text-gray-500 dark:text-muted">
              Waiting for events… drive the world from the Dispatch Board
            </div>
          ) : (
            activity.map((envelope) => (
              <div key={envelope.eventId} className="flex items-center gap-3 px-4 py-2 text-xs">
                <span className="font-mono text-gray-400 dark:text-muted w-16 shrink-0">{fmtClock(envelope.observedAt)}</span>
                <span className={cn('font-mono font-semibold w-48 shrink-0 truncate', eventTone(envelope.eventType))}>
                  {envelope.eventType}
                </span>
                <span className="text-gray-600 dark:text-muted truncate">{summarizeEvent(envelope)}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
