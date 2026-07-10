/**
 * Floating dispatch panel — routes with live progress, and the unassigned-order
 * queue with assign/start actions. Sits over the map.
 */
import React, { useState } from 'react';
import { cn } from '../base/utils';
import { routeColor } from '../map/MapContainer';
import { ChevronDown, ChevronUp, Play, Wifi, WifiOff, Package, RouteIcon } from 'lucide-react';

const STATUS_STYLES = {
  ACTIVE: 'bg-primary/20 text-primary',
  PLANNED: 'bg-sky-400/20 text-sky-400',
  COMPLETED: 'bg-gray-400/20 text-gray-400',
};

function RouteRow({ route, index, isSelected, onSelect, onStart }) {
  const color = routeColor(index);
  const canStart = route.status === 'PLANNED' && route.driver && route.vehicle && route.stopsTotal > 0;
  return (
    <button
      onClick={() => onSelect(route.id)}
      className={cn(
        'w-full text-left px-3 py-2 rounded-md border transition-colors',
        isSelected
          ? 'border-primary/60 bg-primary/10'
          : 'border-transparent hover:bg-gray-100 dark:hover:bg-gray-800'
      )}
    >
      <div className="flex items-center gap-2">
        <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: color }} />
        <span className="font-semibold text-sm text-gray-900 dark:text-foreground">{route.routeNumber}</span>
        <span className={cn('text-[10px] px-1.5 py-0.5 rounded-full font-semibold', STATUS_STYLES[route.status] || '')}>
          {route.status}
        </span>
        <span className="ml-auto text-xs text-gray-500 dark:text-muted">
          {route.stopsCompleted}/{route.stopsTotal} stops
        </span>
        {canStart && (
          <span
            role="button"
            title="Start route"
            onClick={(e) => {
              e.stopPropagation();
              onStart(route.id);
            }}
            className="p-1 rounded bg-primary/20 hover:bg-primary/40 text-primary"
          >
            <Play className="w-3.5 h-3.5" />
          </span>
        )}
      </div>
      <div className="mt-1 flex items-center gap-2 text-xs text-gray-500 dark:text-muted">
        <span>{route.driver ? route.driver.name : 'no driver'}</span>
        <span>·</span>
        <span>{route.vehicle ? route.vehicle.vehicleNumber : 'no vehicle'}</span>
      </div>
      {route.stopsTotal > 0 && (
        <div className="mt-1.5 h-1 rounded bg-gray-200 dark:bg-gray-800 overflow-hidden">
          <div
            className="h-full rounded"
            style={{ width: `${(100 * route.stopsCompleted) / route.stopsTotal}%`, backgroundColor: color }}
          />
        </div>
      )}
    </button>
  );
}

function UnassignedRow({ order, routes, onAssign }) {
  const [routeId, setRouteId] = useState('');
  const assignable = routes.filter((r) => r.status !== 'COMPLETED');
  return (
    <div className="px-3 py-2 rounded-md border border-transparent hover:bg-gray-100 dark:hover:bg-gray-800">
      <div className="flex items-center gap-2">
        <Package className="w-3.5 h-3.5 text-orange-400 shrink-0" />
        <span className="font-semibold text-sm text-gray-900 dark:text-foreground">{order.orderNumber}</span>
        <span className="text-xs text-gray-500 dark:text-muted truncate">{order.customer?.name}</span>
        <span className="ml-auto text-xs text-gray-500 dark:text-muted">{order.parcelCount}×</span>
      </div>
      <div className="mt-1 text-xs text-gray-500 dark:text-muted truncate">→ {order.delivery?.address}</div>
      <div className="mt-1.5 flex items-center gap-1.5">
        <select
          value={routeId}
          onChange={(e) => setRouteId(e.target.value)}
          className="flex-1 text-xs px-2 py-1 rounded border border-gray-200 dark:border-accent bg-white dark:bg-gray-900 text-gray-700 dark:text-foreground"
        >
          <option value="">assign to route…</option>
          {assignable.map((r) => (
            <option key={r.id} value={r.id}>
              {r.routeNumber} ({r.status.toLowerCase()}, {r.stopsTotal} stops)
            </option>
          ))}
        </select>
        <button
          disabled={!routeId}
          onClick={() => routeId && onAssign(order.id, routeId)}
          className={cn(
            'text-xs px-2.5 py-1 rounded font-semibold',
            routeId
              ? 'bg-primary text-background hover:bg-primary/80'
              : 'bg-gray-200 dark:bg-gray-800 text-gray-400 cursor-not-allowed'
          )}
        >
          Assign
        </button>
      </div>
    </div>
  );
}

const FloatingControlPanel = ({
  routes,
  unassignedOrders,
  drivers,
  selectedRouteId,
  onSelectRoute,
  onAssignOrder,
  onStartRoute,
  loading,
  wsConnected,
  actionError,
}) => {
  const [collapsed, setCollapsed] = useState(false);
  const [tab, setTab] = useState('routes');
  const activeCount = routes.filter((r) => r.status === 'ACTIVE').length;

  return (
    <div className="absolute top-6 right-6 z-40 w-[340px] max-h-[85vh] flex flex-col rounded-lg shadow-2xl border border-gray-200 dark:border-accent bg-white/95 dark:bg-gray-900/95 backdrop-blur">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-200 dark:border-accent">
        <RouteIcon className="w-4 h-4 text-primary" />
        <span className="font-bold text-sm text-gray-900 dark:text-foreground">Dispatch — Austin</span>
        <span title={wsConnected ? 'live event feed connected' : 'event feed disconnected'} className="ml-1">
          {wsConnected ? <Wifi className="w-3.5 h-3.5 text-primary" /> : <WifiOff className="w-3.5 h-3.5 text-red-400" />}
        </span>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="ml-auto p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-muted"
        >
          {collapsed ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
        </button>
      </div>

      {!collapsed && (
        <>
          {/* Tabs */}
          <div className="flex px-2 pt-2 gap-1">
            <button
              onClick={() => setTab('routes')}
              className={cn(
                'flex-1 text-xs font-semibold px-3 py-1.5 rounded-md',
                tab === 'routes'
                  ? 'bg-primary/15 text-primary'
                  : 'text-gray-500 dark:text-muted hover:bg-gray-100 dark:hover:bg-gray-800'
              )}
            >
              Routes ({activeCount} active)
            </button>
            <button
              onClick={() => setTab('orders')}
              className={cn(
                'flex-1 text-xs font-semibold px-3 py-1.5 rounded-md',
                tab === 'orders'
                  ? 'bg-orange-400/15 text-orange-400'
                  : 'text-gray-500 dark:text-muted hover:bg-gray-100 dark:hover:bg-gray-800'
              )}
            >
              Unassigned ({unassignedOrders.length})
            </button>
          </div>

          {actionError && (
            <div className="mx-3 mt-2 px-3 py-2 text-xs rounded bg-red-500/10 text-red-400 border border-red-500/30">
              {actionError}
            </div>
          )}

          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {loading ? (
              <div className="text-center text-xs text-gray-500 dark:text-muted py-6">Loading world…</div>
            ) : tab === 'routes' ? (
              routes.length === 0 ? (
                <div className="text-center text-xs text-gray-500 dark:text-muted py-6">No routes yet</div>
              ) : (
                routes.map((route, idx) => (
                  <RouteRow
                    key={route.id}
                    route={route}
                    index={idx}
                    isSelected={route.id === selectedRouteId}
                    onSelect={onSelectRoute}
                    onStart={onStartRoute}
                  />
                ))
              )
            ) : unassignedOrders.length === 0 ? (
              <div className="text-center text-xs text-gray-500 dark:text-muted py-6">
                Every order is on a route 🎉
              </div>
            ) : (
              unassignedOrders.map((order) => (
                <UnassignedRow key={order.id} order={order} routes={routes} onAssign={onAssignOrder} />
              ))
            )}
          </div>

          {/* Footer: driver duty summary */}
          <div className="px-4 py-2 border-t border-gray-200 dark:border-accent text-[11px] text-gray-500 dark:text-muted">
            {drivers.filter((d) => d.status === 'ON_ROUTE').length} driving ·{' '}
            {drivers.filter((d) => d.status === 'AVAILABLE').length} available ·{' '}
            {drivers.filter((d) => d.status === 'OFF_DUTY').length} off duty
          </div>
        </>
      )}
    </div>
  );
};

export default FloatingControlPanel;
