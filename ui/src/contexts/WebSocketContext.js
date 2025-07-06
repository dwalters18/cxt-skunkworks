// ui/src/contexts/WebSocketContext.js

import React, { createContext, useContext, useRef, useCallback, useEffect, useState } from 'react';

const WebSocketContext = createContext(null);

export const useWebSocket = () => {
    const context = useContext(WebSocketContext);
    if (!context) {
        throw new Error('useWebSocket must be used within a WebSocketProvider');
    }
    return context;
};

export const WebSocketProvider = ({ children }) => {
    const wsRef = useRef(null);
    const [isConnected, setIsConnected] = useState(false);
    const [events, setEvents] = useState([]);
    const [lastReconnectAttempt, setLastReconnectAttempt] = useState(0);
    const reconnectTimeoutRef = useRef(null);
    const eventListenersRef = useRef(new Map());
    const isConnectingRef = useRef(false); // Prevent multiple connection attempts
    const mountedRef = useRef(true); // Track if component is mounted

    const connectWebSocket = useCallback(() => {
        // Prevent multiple connection attempts
        if (!mountedRef.current || isConnectingRef.current) {
            return;
        }
        
        if (wsRef.current && (wsRef.current.readyState === WebSocket.CONNECTING || wsRef.current.readyState === WebSocket.OPEN)) {
            return;
        }

        const wsUrl = `${process.env.REACT_APP_WEBSOCKET_URL || 'ws://localhost:8000/ws'}/events`;
        console.log('Attempting WebSocket connection...');
        isConnectingRef.current = true;
        
        try {
            wsRef.current = new WebSocket(wsUrl);
            
            wsRef.current.onopen = () => {
                if (!mountedRef.current) return;
                
                console.log('WebSocket connected');
                setIsConnected(true);
                setLastReconnectAttempt(0);
                isConnectingRef.current = false;
                
                // Clear any pending reconnection attempts
                if (reconnectTimeoutRef.current) {
                    clearTimeout(reconnectTimeoutRef.current);
                    reconnectTimeoutRef.current = null;
                }
            };
            
            wsRef.current.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    setEvents(prev => [data, ...prev.slice(0, 99)]); // Keep last 100 events
                    
                    // Notify all registered listeners
                    eventListenersRef.current.forEach((listener, id) => {
                        listener(data);
                    });
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };
            
            wsRef.current.onclose = (event) => {
                if (!mountedRef.current) return;
                
                console.log('WebSocket disconnected:', {
                    code: event.code,
                    reason: event.reason || 'No reason provided',
                    wasClean: event.wasClean,
                    url: wsUrl
                });
                setIsConnected(false);
                isConnectingRef.current = false;
                
                // Only attempt reconnection if not manually closed
                if (event.code !== 1000) {
                    scheduleReconnection();
                }
            };
            
            wsRef.current.onerror = (error) => {
                if (!mountedRef.current) return;
                
                console.error('WebSocket error details:', {
                    type: error.type,
                    target: error.target?.readyState,
                    url: error.target?.url,
                    isTrusted: error.isTrusted,
                    message: error.message || 'Connection failed'
                });
                setIsConnected(false);
                isConnectingRef.current = false;
            };
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            isConnectingRef.current = false;
            if (mountedRef.current) {
                scheduleReconnection();
            }
        }
    }, []); // Remove dependencies to prevent recreation

    const scheduleReconnection = useCallback(() => {
        if (!mountedRef.current || isConnectingRef.current) {
            return;
        }
        
        // Clear any existing timeout
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
        }

        // Exponential backoff with max delay of 30 seconds
        const now = Date.now();
        const timeSinceLastAttempt = now - lastReconnectAttempt;
        const minDelay = Math.min(3000 * Math.pow(2, Math.floor(timeSinceLastAttempt / 10000)), 30000);
        
        console.log(`Scheduling WebSocket reconnection in ${minDelay}ms`);
        setLastReconnectAttempt(now);
        
        reconnectTimeoutRef.current = setTimeout(() => {
            if (mountedRef.current) {
                connectWebSocket();
            }
        }, minDelay);
    }, [lastReconnectAttempt]); // Remove connectWebSocket dependency

    const addEventListener = useCallback((listener) => {
        const id = Math.random().toString(36).substr(2, 9);
        eventListenersRef.current.set(id, listener);
        
        // Return cleanup function
        return () => {
            eventListenersRef.current.delete(id);
        };
    }, []);

    const disconnect = useCallback(() => {
        isConnectingRef.current = false;
        
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
        }
        
        if (wsRef.current) {
            wsRef.current.close(1000, 'Manual disconnect');
            wsRef.current = null;
        }
        
        setIsConnected(false);
    }, []);

    // Initialize WebSocket connection on mount
    useEffect(() => {
        mountedRef.current = true;
        
        // Small delay to prevent React StrictMode double execution
        const timer = setTimeout(() => {
            if (mountedRef.current) {
                connectWebSocket();
            }
        }, 100);
        
        // Cleanup on unmount
        return () => {
            mountedRef.current = false;
            clearTimeout(timer);
            disconnect();
        };
    }, []); // Remove dependencies to prevent re-execution

    // Add visibility change handler to reconnect when tab becomes visible
    useEffect(() => {
        const handleVisibilityChange = () => {
            if (mountedRef.current && document.visibilityState === 'visible' && !isConnected && !isConnectingRef.current) {
                console.log('Tab became visible, attempting WebSocket reconnection...');
                connectWebSocket();
            }
        };

        document.addEventListener('visibilitychange', handleVisibilityChange);
        return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
    }, [isConnected]); // Remove connectWebSocket dependency

    const value = {
        isConnected,
        events,
        addEventListener,
        disconnect,
        reconnect: connectWebSocket
    };

    return (
        <WebSocketContext.Provider value={value}>
            {children}
        </WebSocketContext.Provider>
    );
};
