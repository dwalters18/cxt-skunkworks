/**
 * Fleet — vehicles with availability toggles. IN_SERVICE is system-set when a
 * route starts; dispatchers only flip AVAILABLE ↔ MAINTENANCE here.
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { cn } from '../components/base/utils';
import { useWebSocket } from '../contexts/WebSocketContext';
import api from '../api/client';
import { Truck, Package, Route as RouteIcon, Wrench } from 'lucide-react';

const STATUS_STYLES = {
  AVAILABLE: 'bg-green-400/15 text-green-600 dark:text-green-400',
  IN_SERVICE: 'bg-sky-400/15 text-sky-600 dark:text-sky-400',
  MAINTENANCE: 'bg-amber-400/15 text-amber-600 dark:text-amber-400',
};

const KIND_LABELS = { VAN: 'Van', BOX_TRUCK: 'Box truck' };

const FleetPage = () => {
  const { addEventListener } = useWebSocket();
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionError, setActionError] = useState(null);
  const refreshTimer = useRef(null);

  const fetchVehicles = useCallback(async () => {
    try {
      const res = await api.listVehicles();
      setVehicles(res.vehicles || []);
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
      fetchVehicles();
    }, 500);
  }, [fetchVehicles]);

  useEffect(() => {
    fetchVehicles();
    return () => refreshTimer.current && clearTimeout(refreshTimer.current);
  }, [fetchVehicles]);

  useEffect(() => {
    const unsubscribe = addEventListener(({ eventType }) => {
      if (eventType === 'vehicle.status-updated' || eventType === 'system.demo-reset') {
        scheduleRefresh();
      }
    });
    return unsubscribe;
  }, [addEventListener, scheduleRefresh]);

  const toggleMaintenance = async (vehicle) => {
    setActionError(null);
    const next = vehicle.status === 'AVAILABLE' ? 'MAINTENANCE' : 'AVAILABLE';
    try {
      await api.updateVehicleStatus(vehicle.id, next);
      fetchVehicles();
    } catch (e) {
      setActionError(e.message);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-foreground">Fleet</h1>
        <p className="text-gray-600 dark:text-muted mt-1">Vehicles, capacity, and service status</p>
      </div>

      {actionError && (
        <div className="px-3 py-2 text-xs rounded bg-red-500/10 text-red-500 dark:text-red-400 border border-red-500/30">{actionError}</div>
      )}

      {loading ? (
        <div className="text-center text-gray-500 dark:text-muted py-16">Loading fleet…</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {vehicles.map((vehicle) => (
            <div key={vehicle.id} className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-accent p-4 flex flex-col gap-3">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-lg bg-gray-100 dark:bg-gray-800 flex items-center justify-center shrink-0">
                  <Truck className="w-5 h-5 text-gray-500 dark:text-muted" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-gray-900 dark:text-foreground">{vehicle.vehicleNumber}</span>
                    <span className="rounded text-[10px] px-1.5 py-0.5 font-semibold bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-muted uppercase tracking-wide">
                      {KIND_LABELS[vehicle.kind] || vehicle.kind}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 dark:text-muted truncate">
                    {vehicle.make} {vehicle.model}
                  </div>
                </div>
                <span className={cn('rounded-full text-xs px-2 py-0.5 font-semibold whitespace-nowrap', STATUS_STYLES[vehicle.status] || '')}>
                  {(vehicle.status || '').replace('_', ' ')}
                </span>
              </div>

              <div className="space-y-1 text-xs text-gray-600 dark:text-muted">
                <div className="flex items-center gap-1.5">
                  <Package className="w-3.5 h-3.5" /> capacity {vehicle.capacityParcels} parcels
                </div>
                {vehicle.activeRouteNumber && (
                  <div className="flex items-center gap-1.5 text-sky-600 dark:text-sky-400">
                    <RouteIcon className="w-3.5 h-3.5" /> on {vehicle.activeRouteNumber}
                  </div>
                )}
              </div>

              {vehicle.status !== 'IN_SERVICE' && (
                <button
                  onClick={() => toggleMaintenance(vehicle)}
                  className={cn(
                    'mt-auto flex items-center justify-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-md',
                    vehicle.status === 'AVAILABLE'
                      ? 'bg-amber-400/15 text-amber-600 dark:text-amber-400 hover:bg-amber-400/25'
                      : 'bg-primary/15 text-emerald-600 dark:text-primary hover:bg-primary/25'
                  )}
                >
                  <Wrench className="w-3.5 h-3.5" />
                  {vehicle.status === 'AVAILABLE' ? 'Send to maintenance' : 'Mark available'}
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default FleetPage;
