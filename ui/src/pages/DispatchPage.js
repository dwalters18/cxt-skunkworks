/**
 * Dispatch Board — the live map over the seeded Austin world.
 *
 * Data flow (the demo story in one page):
 *   - initial world state via REST (/api/routes, /api/orders/unassigned, ...)
 *   - live movement from the canonical event feed: driver.location-updated
 *     moves the dots; stop/order/route events trigger a world refresh
 *   - actions (assign order, start route) POST to the API, which emits events
 *     the map then reacts to — the full loop in one screen
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import MapContainer, { routeColor } from '../components/map/MapContainer';
import FloatingControlPanel from '../components/dispatch/FloatingControlPanel';
import { useDarkMode } from '../contexts/DarkModeContext';
import { useWebSocket } from '../contexts/WebSocketContext';
import api from '../api/client';

const REFRESH_EVENTS = new Set([
  'order.created',
  'order.assigned',
  'order.completed',
  'order.cancelled',
  'stop.status-updated',
  'route.planned',
  'route.started',
  'route.completed',
  'driver.status-updated',
  'system.demo-reset',
]);

const DispatchPage = () => {
  const { isDarkMode } = useDarkMode();
  const { addEventListener, isConnected } = useWebSocket();

  const [routes, setRoutes] = useState([]);
  const [unassignedOrders, setUnassignedOrders] = useState([]);
  const [depots, setDepots] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [driverPositions, setDriverPositions] = useState({});
  const [selectedRouteId, setSelectedRouteId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionError, setActionError] = useState(null);
  const refreshTimer = useRef(null);

  const fetchWorld = useCallback(async () => {
    try {
      const [routesRes, unassignedRes, depotsRes, driversRes] = await Promise.all([
        api.listRoutes(),
        api.unassignedOrders(),
        api.listDepots(),
        api.listDrivers(),
      ]);
      const routeList = routesRes.routes || [];
      setRoutes(routeList);
      setUnassignedOrders(unassignedRes.orders || []);
      setDepots(depotsRes.depots || []);
      setDrivers(driversRes.drivers || []);

      // Seed driver dots from the world model; live events take over from here.
      const colorByDriver = {};
      routeList.forEach((r, idx) => {
        if (r.driver?.id) colorByDriver[r.driver.id] = routeColor(idx);
      });
      setDriverPositions((prev) => {
        const next = { ...prev };
        (driversRes.drivers || []).forEach((d) => {
          if (d.status === 'OFF_DUTY') {
            delete next[d.id];
            return;
          }
          const existing = next[d.id];
          next[d.id] = {
            latitude: existing?.live ? existing.latitude : d.latitude,
            longitude: existing?.live ? existing.longitude : d.longitude,
            live: existing?.live || false,
            name: d.name,
            routeNumber: d.activeRouteNumber,
            color: colorByDriver[d.id] || '#9CA3AF',
            speedMph: existing?.speedMph,
          };
        });
        return next;
      });
      setLoading(false);
    } catch (e) {
      console.error('world fetch failed', e);
      setLoading(false);
    }
  }, []);

  // Debounced refresh so a burst of events causes one refetch.
  const scheduleRefresh = useCallback(() => {
    if (refreshTimer.current) return;
    refreshTimer.current = setTimeout(() => {
      refreshTimer.current = null;
      fetchWorld();
    }, 400);
  }, [fetchWorld]);

  useEffect(() => {
    fetchWorld();
    const poll = setInterval(fetchWorld, 30000); // safety net if WS drops
    return () => {
      clearInterval(poll);
      if (refreshTimer.current) clearTimeout(refreshTimer.current);
    };
  }, [fetchWorld]);

  useEffect(() => {
    const unsubscribe = addEventListener((envelope) => {
      if (envelope.eventType === 'driver.location-updated') {
        const p = envelope.payload;
        setDriverPositions((prev) => {
          const existing = prev[p.driverId] || {};
          return {
            ...prev,
            [p.driverId]: {
              ...existing,
              latitude: p.location.latitude,
              longitude: p.location.longitude,
              speedMph: p.speedMph,
              live: true,
            },
          };
        });
      } else if (REFRESH_EVENTS.has(envelope.eventType)) {
        scheduleRefresh();
      }
    });
    return unsubscribe;
  }, [addEventListener, scheduleRefresh]);

  const handleAssignOrder = async (orderId, routeId) => {
    setActionError(null);
    try {
      await api.assignOrder(orderId, routeId);
    } catch (e) {
      setActionError(e.message);
    }
  };

  const handleStartRoute = async (routeId) => {
    setActionError(null);
    try {
      await api.startRoute(routeId);
    } catch (e) {
      setActionError(e.message);
    }
  };

  return (
    <div className="h-screen flex bg-gray-50 dark:bg-background relative">
      <div className="flex-1 relative">
        <MapContainer
          depots={depots}
          routes={routes}
          unassignedOrders={unassignedOrders}
          driverPositions={driverPositions}
          selectedRouteId={selectedRouteId}
          isDarkMode={isDarkMode}
          onSelectRoute={setSelectedRouteId}
        />
        <FloatingControlPanel
          routes={routes}
          unassignedOrders={unassignedOrders}
          drivers={drivers}
          selectedRouteId={selectedRouteId}
          onSelectRoute={setSelectedRouteId}
          onAssignOrder={handleAssignOrder}
          onStartRoute={handleStartRoute}
          loading={loading}
          wsConnected={isConnected}
          actionError={actionError}
        />
      </div>
    </div>
  );
};

export default DispatchPage;
