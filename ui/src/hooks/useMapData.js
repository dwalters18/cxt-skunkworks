import { useState, useEffect, useCallback } from 'react';

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

export const useMapData = () => {
    const [events, setEvents] = useState([]);
    const [vehicles, setVehicles] = useState([]);
    const [loads, setLoads] = useState([]);
    const [drivers, setDrivers] = useState([]);
    const [dashboardData, setDashboardData] = useState({});
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    // Fetch all map data
    const fetchMapData = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        
        try {
            // Updated API endpoints to match backend
            const [eventsRes, vehiclesRes, loadsRes, dashboardRes] = await Promise.all([
                fetch(`${API_BASE}/api/events/recent`),
                fetch(`${API_BASE}/api/vehicles`),
                fetch(`${API_BASE}/api/loads`),
                fetch(`${API_BASE}/api/analytics/dashboard`)
            ]);

            // Check for failed requests
            if (!eventsRes.ok) throw new Error(`Events API failed: ${eventsRes.status}`);
            if (!vehiclesRes.ok) throw new Error(`Vehicles API failed: ${vehiclesRes.status}`);
            if (!loadsRes.ok) throw new Error(`Loads API failed: ${loadsRes.status}`);
            if (!dashboardRes.ok) throw new Error(`Dashboard API failed: ${dashboardRes.status}`);

            const [eventsData, vehiclesData, loadsData, dashboardDataRes] = await Promise.all([
                eventsRes.json(),
                vehiclesRes.json(),
                loadsRes.json(),
                dashboardRes.json()
            ]);

            // Handle different response formats
            setEvents(eventsData?.events || eventsData || []);
            setVehicles(vehiclesData || []);
            setLoads(loadsData || []);
            setDrivers([]); // No drivers endpoint available yet
            setDashboardData(dashboardDataRes || {});
        } catch (err) {
            console.error('Error fetching map data:', err);
            setError('Failed to load map data');
        } finally {
            setIsLoading(false);
        }
    }, []);

    // Fetch individual data types
    const fetchEvents = useCallback(async () => {
        try {
            const response = await fetch(`${API_BASE}/api/events/recent`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            setEvents(data?.events || data || []);
        } catch (err) {
            console.error('Error fetching events:', err);
            setError(`Failed to fetch events: ${err.message}`);
        }
    }, []);

    const fetchVehicles = useCallback(async () => {
        try {
            const response = await fetch(`${API_BASE}/api/vehicles`);
            const data = await response.json();
            setVehicles(data || []);
        } catch (err) {
            console.error('Error fetching vehicles:', err);
        }
    }, []);

    const fetchLoads = useCallback(async () => {
        try {
            const response = await fetch(`${API_BASE}/api/loads`);
            const data = await response.json();
            setLoads(data || []);
        } catch (err) {
            console.error('Error fetching loads:', err);
        }
    }, []);

    // Initialize data on mount
    useEffect(() => {
        fetchMapData();
    }, [fetchMapData]);

    return {
        // Data
        events,
        vehicles,
        loads,
        drivers,
        dashboardData,
        
        // State
        isLoading,
        error,
        
        // Methods
        fetchMapData,
        fetchEvents,
        fetchVehicles,
        fetchLoads,
        setEvents,
        setVehicles,
        setLoads,
        setDrivers
    };
};
