/**
 * WebSocket context — live feed of canonical events.
 *
 * Connects to /ws and receives every event on the backbone verbatim in
 * envelope v1 wire form (camelCase):
 *   { eventId, eventType, eventVersion, sourceSystem, tenantId,
 *     entityRefs, occurredAt, observedAt, payload, traceId }
 *
 * Consumers filter by envelope.eventType (e.g. 'driver.location-updated').
 */
import React, { createContext, useContext, useRef, useCallback, useEffect, useState } from 'react';

const WebSocketContext = createContext(null);

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

function defaultWsUrl() {
  if (process.env.REACT_APP_WEBSOCKET_URL) return process.env.REACT_APP_WEBSOCKET_URL;
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
  // In dev (CRA on :3000) the dev server doesn't proxy websockets reliably,
  // so fall back to the API port directly.
  const host =
    window.location.port === '3000' && process.env.NODE_ENV === 'development'
      ? `${window.location.hostname}:8000`
      : window.location.host;
  return `${proto}://${host}/ws`;
}

export const WebSocketProvider = ({ children }) => {
  const wsRef = useRef(null);
  const [isConnected, setIsConnected] = useState(false);
  const [events, setEvents] = useState([]);
  const reconnectRef = useRef(null);
  const reconnectDelayRef = useRef(2000);
  const listenersRef = useRef(new Map());
  const mountedRef = useRef(true);

  const connect = useCallback(() => {
    if (!mountedRef.current) return;
    if (wsRef.current && (wsRef.current.readyState === WebSocket.CONNECTING || wsRef.current.readyState === WebSocket.OPEN)) {
      return;
    }
    const url = defaultWsUrl();
    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!mountedRef.current) return;
        setIsConnected(true);
        reconnectDelayRef.current = 2000;
      };

      ws.onmessage = (msg) => {
        try {
          const envelope = JSON.parse(msg.data);
          if (!envelope.eventType) return;
          setEvents((prev) => [envelope, ...prev.slice(0, 199)]);
          listenersRef.current.forEach((listener) => listener(envelope));
        } catch {
          // non-JSON frame; ignore
        }
      };

      ws.onclose = () => {
        if (!mountedRef.current) return;
        setIsConnected(false);
        scheduleReconnect();
      };

      ws.onerror = () => {
        setIsConnected(false);
      };
    } catch {
      scheduleReconnect();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const scheduleReconnect = useCallback(() => {
    if (!mountedRef.current || reconnectRef.current) return;
    const delay = reconnectDelayRef.current;
    reconnectDelayRef.current = Math.min(delay * 2, 30000);
    reconnectRef.current = setTimeout(() => {
      reconnectRef.current = null;
      connect();
    }, delay);
  }, [connect]);

  const addEventListener = useCallback((listener) => {
    const id = Math.random().toString(36).slice(2, 11);
    listenersRef.current.set(id, listener);
    return () => listenersRef.current.delete(id);
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    const timer = setTimeout(connect, 100);
    return () => {
      mountedRef.current = false;
      clearTimeout(timer);
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      if (wsRef.current) wsRef.current.close(1000, 'unmount');
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const onVisible = () => {
      if (document.visibilityState === 'visible' && !isConnected) connect();
    };
    document.addEventListener('visibilitychange', onVisible);
    return () => document.removeEventListener('visibilitychange', onVisible);
  }, [isConnected, connect]);

  return (
    <WebSocketContext.Provider value={{ isConnected, events, addEventListener }}>
      {children}
    </WebSocketContext.Provider>
  );
};
