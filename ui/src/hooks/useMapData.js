import { useState, useEffect, useCallback } from 'react';

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

export const useMapData = () => {
    const [events, setEvents] = useState([]);
    const [vehicles, setVehicles] = useState([]);
    const [loads, setLoads] = useState([]);
    const [drivers, setDrivers] = useState([]);
    const [routes, setRoutes] = useState([]);
    const [dashboardData, setDashboardData] = useState({});
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    // Fetch all map data
    const fetchMapData = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        
        try {
            // Updated API endpoints to match backend
            const [eventsRes, vehiclesRes, loadsRes, routesRes, driversRes, dashboardRes] = await Promise.all([
                fetch(`${API_BASE}/api/events/recent`),
                fetch(`${API_BASE}/api/vehicles`),
                fetch(`${API_BASE}/api/loads`),
                fetch(`${API_BASE}/api/routes`),
                fetch(`${API_BASE}/api/drivers`),
                fetch(`${API_BASE}/api/dashboard`)
            ]);

            // Handle different response formats and check for successful responses
            const eventsData = eventsRes.ok ? await eventsRes.json() : [];
            const vehiclesData = vehiclesRes.ok ? await vehiclesRes.json() : [];
            const loadsData = loadsRes.ok ? await loadsRes.json() : [];
            const routesData = routesRes.ok ? await routesRes.json() : [];
            const driversData = driversRes.ok ? await driversRes.json() : [];
            const dashboardDataRes = dashboardRes.ok ? await dashboardRes.json() : {};

            // Set state with proper data extraction
            setEvents(eventsData?.events || eventsData || []);
            setVehicles(vehiclesData?.vehicles || vehiclesData || []);
            setLoads(loadsData?.loads || loadsData || []);
            setRoutes(routesData?.routes || routesData || []);
            setDrivers(driversData?.drivers || driversData || []);
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

    // Fetch routes
    const fetchRoutes = useCallback(async () => {
        try {
            const response = await fetch(`${API_BASE}/api/routes`);
            if (response.ok) {
                const data = await response.json();
                setRoutes(data?.routes || data || []);
            }
        } catch (err) {
            console.error('Error fetching routes:', err);
        }
    }, []);

    return {
        // Data
        events,
        vehicles,
        loads,
        drivers,
        routes,
        dashboardData,
        
        // State
        isLoading,
        error,
        
        // Methods
        fetchMapData,
        fetchEvents,
        fetchVehicles,
        fetchLoads,
        fetchRoutes,
        setEvents,
        setVehicles,
        setLoads,
        setDrivers,
        setRoutes
    };
};
