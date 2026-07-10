/**
 * Dispatch Board — three panels over one projection.
 *
 *   [ Unassigned queue ]  [ Live map ]  [ Drivers & routes ]
 *
 * All state comes from useWorldProjection: a REST snapshot folded forward by
 * canonical events. Actions (assign, start, advance) POST to the API and then
 * WAIT — the board changes only when the resulting events arrive on the bus,
 * which is the whole demonstration.
 */
import React, { useMemo, useState, useEffect, useCallback } from 'react';
import MapContainer, { routeColor } from '../components/map/MapContainer';
import UnassignedPanel from '../components/dispatch/UnassignedPanel';
import DriversPanel from '../components/dispatch/DriversPanel';
import DriverSlideOver from '../components/dispatch/DriverSlideOver';
import { useDarkMode } from '../contexts/DarkModeContext';
import { useWorldProjection } from '../world/useWorldProjection';
import { selectDriverBoard, selectRouteList, selectUnassignedOrders } from '../world/reduce';
import api from '../api/client';
import { Activity, Wifi, WifiOff } from 'lucide-react';

const DispatchPage = () => {
  const { isDarkMode } = useDarkMode();
  const { world, isConnected } = useWorldProjection();

  const [selectedOrderId, setSelectedOrderId] = useState(null);
  const [selectedRouteId, setSelectedRouteId] = useState(null);
  const [openDriverId, setOpenDriverId] = useState(null);
  const [assigningOrderIds, setAssigningOrderIds] = useState(new Set());
  const [banner, setBanner] = useState(null);
  const [now, setNow] = useState(Date.now());

  // Urgency countdowns tick twice a minute.
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 30000);
    return () => clearInterval(t);
  }, []);

  const unassigned = useMemo(() => selectUnassignedOrders(world), [world]);
  const routeList = useMemo(() => selectRouteList(world), [world]);
  const driverBoard = useMemo(() => selectDriverBoard(world), [world]);

  const routeIndexById = useMemo(
    () => Object.fromEntries(routeList.map((r, i) => [r.id, i])),
    [routeList]
  );

  // The selected order stops being "assigning" the moment its events landed.
  useEffect(() => {
    setAssigningOrderIds((prev) => {
      if (prev.size === 0) return prev;
      const next = new Set([...prev].filter((id) => world.orders[id]?.status === 'CREATED'));
      return next.size === prev.size ? prev : next;
    });
  }, [world]);

  const driverPositions = useMemo(() => {
    const out = {};
    for (const d of driverBoard) {
      if (d.status === 'OFF_DUTY' || !d.position) continue;
      out[d.id] = {
        latitude: d.position.latitude,
        longitude: d.position.longitude,
        speedMph: d.position.speedMph,
        name: d.name,
        routeNumber: d.currentRoute?.routeNumber,
        color: d.currentRoute ? routeColor(routeIndexById[d.currentRoute.id] ?? 0) : '#96A19B',
      };
    }
    return out;
  }, [driverBoard, routeIndexById]);

  const handleAssign = useCallback(
    async (orderId, driverId) => {
      if (!orderId || !driverId) return;
      setBanner(null);
      setAssigningOrderIds((prev) => new Set(prev).add(orderId));
      setSelectedOrderId(null);
      try {
        await api.assignOrderToDriver(orderId, driverId);
        // Done. order.assigned (and possibly route.planned) will move the card.
      } catch (e) {
        setAssigningOrderIds((prev) => {
          const next = new Set(prev);
          next.delete(orderId);
          return next;
        });
        setBanner(e.message);
      }
    },
    []
  );

  const openDriver = openDriverId ? driverBoard.find((d) => d.id === openDriverId) : null;
  const openDriverRoute = openDriver?.currentRoute ? world.routes[openDriver.currentRoute.id] : null;

  return (
    <div className="h-screen flex bg-background overflow-hidden">
      <UnassignedPanel
        orders={unassigned}
        selectedOrderId={selectedOrderId}
        assigningOrderIds={assigningOrderIds}
        onSelect={setSelectedOrderId}
        now={now}
      />

      <div className="flex-1 relative min-w-0">
        {/* Board status bar */}
        <div className="absolute top-0 inset-x-0 z-40 flex items-center gap-3 px-4 py-2.5 bg-surface/90 backdrop-blur border-b border-accent">
          <h1 className="font-heading font-semibold text-sm text-foreground">Dispatch — Austin</h1>
          <span className="flex items-center gap-1.5 text-[11px] text-muted">
            {isConnected ? (
              <><Wifi className="w-3.5 h-3.5 text-primary" /> live</>
            ) : (
              <><WifiOff className="w-3.5 h-3.5 text-danger" /> reconnecting…</>
            )}
          </span>
          <span className="ml-auto flex items-center gap-1.5 text-[11px] text-muted font-mono">
            <Activity className="w-3.5 h-3.5 text-primary" />
            projected from {world.eventCount.toLocaleString()} events
            {world.lastEventType && <span className="text-primary/80">· {world.lastEventType}</span>}
          </span>
        </div>

        {banner && (
          <div className="absolute top-12 inset-x-4 z-40 px-3 py-2 text-xs rounded-xl bg-danger/15 text-danger border border-danger/40 backdrop-blur">
            {banner}
            <button className="ml-2 underline" onClick={() => setBanner(null)}>dismiss</button>
          </div>
        )}

        <MapContainer
          depots={world.depots}
          routes={routeList}
          unassignedOrders={unassigned}
          driverPositions={driverPositions}
          selectedRouteId={selectedRouteId || (openDriverRoute ? openDriverRoute.id : null)}
          isDarkMode={isDarkMode}
          onSelectRoute={setSelectedRouteId}
        />

        {openDriver && (
          <DriverSlideOver
            driver={openDriver}
            route={openDriverRoute}
            onClose={() => setOpenDriverId(null)}
          />
        )}
      </div>

      <DriversPanel
        drivers={driverBoard}
        routeIndexById={routeIndexById}
        selectedOrderId={selectedOrderId}
        onAssign={handleAssign}
        onOpenDriver={setOpenDriverId}
      />
    </div>
  );
};

export default DispatchPage;
