/**
 * useWorldProjection — the dispatch board's state source.
 *
 * Bootstrap once from REST (a projection snapshot), then fold every canonical
 * event from the WebSocket into local state via the pure reducer in reduce.js.
 * Writes never trigger refetches: after POSTing an action, the UI waits for
 * the resulting events like any other consumer of the backbone.
 *
 * A slow background reconcile (60s) guards against drift/missed frames, and a
 * system.demo-reset event triggers a full re-bootstrap.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import api from '../api/client';
import { useWebSocket } from '../contexts/WebSocketContext';
import { applyEvent, bootstrapWorld, initialWorld } from './reduce';

export function useWorldProjection() {
  const { addEventListener, isConnected } = useWebSocket();
  const [world, setWorld] = useState(initialWorld);
  const bootstrappingRef = useRef(false);
  const bufferRef = useRef([]); // events that arrive mid-bootstrap

  const bootstrap = useCallback(async () => {
    if (bootstrappingRef.current) return;
    bootstrappingRef.current = true;
    bufferRef.current = [];
    try {
      const [ordersRes, routesRes, driversRes, vehiclesRes, depotsRes, customersRes] =
        await Promise.all([
          api.listOrders({ limit: 500 }),
          api.listRoutes(),
          api.listDrivers(),
          api.listVehicles(),
          api.listDepots(),
          api.listCustomers(),
        ]);
      setWorld((prev) => {
        let next = bootstrapWorld(prev, {
          orders: ordersRes.orders,
          routes: routesRes.routes,
          drivers: driversRes.drivers,
          vehicles: vehiclesRes.vehicles,
          depots: depotsRes.depots,
          customers: customersRes.customers,
        });
        for (const envelope of bufferRef.current) {
          next = applyEvent(next, envelope);
        }
        bufferRef.current = [];
        return next;
      });
    } catch (e) {
      console.error('world bootstrap failed', e);
    } finally {
      bootstrappingRef.current = false;
    }
  }, []);

  useEffect(() => {
    bootstrap();
  }, [bootstrap]);

  useEffect(() => {
    const unsubscribe = addEventListener((envelope) => {
      if (envelope.eventType === 'system.demo-reset') {
        bootstrap();
        return;
      }
      if (bootstrappingRef.current) {
        bufferRef.current.push(envelope);
        return;
      }
      setWorld((prev) => applyEvent(prev, envelope));
    });
    return unsubscribe;
  }, [addEventListener, bootstrap]);

  // Drift guard: quiet reconcile once a minute (invisible; events remain the
  // visible update mechanism).
  useEffect(() => {
    const t = setInterval(bootstrap, 60000);
    return () => clearInterval(t);
  }, [bootstrap]);

  return { world, isConnected, rebootstrap: bootstrap };
}
