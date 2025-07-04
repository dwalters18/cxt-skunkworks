import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { GoogleMap, useJsApiLoader, Marker, InfoWindow, Polyline, Circle, DirectionsService, DirectionsRenderer } from '@react-google-maps/api';
import { useWebSocket } from '../contexts/WebSocketContext';

// Constants - moved outside component to prevent re-creation
const GOOGLE_MAPS_LIBRARIES = ['geometry', 'drawing'];
const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

const DispatchMapView = ({ onTransitionToManagement }) => {
    // Core state
    const [events, setEvents] = useState([]);
    const [vehicles, setVehicles] = useState([]);
    const [loads, setLoads] = useState([]);
    const [drivers, setDrivers] = useState([]);
    const [selectedVehicle, setSelectedVehicle] = useState(null);
    const [selectedLoad, setSelectedLoad] = useState(null);
    const [dashboardData, setDashboardData] = useState({});
    
    // UI state
    const [activeFilters, setActiveFilters] = useState({
        showVehicles: true,
        showLoads: true,
        showRoutes: true,
        eventTypes: ['all']
    });
    const [gamificationScore, setGamificationScore] = useState(0);
    const [achievements, setAchievements] = useState([]);
    const [realTimeAlerts, setRealTimeAlerts] = useState([]);
    const [optimizedRoutes, setOptimizedRoutes] = useState(new Map()); // Store optimized route data
    const [isOptimizing, setIsOptimizing] = useState(new Set()); // Track which loads are being optimized
    
    // WebSocket connection
    const { isConnected, events: wsEvents, addEventListener } = useWebSocket();
    
    // Google Maps configuration
    const defaultCenter = useMemo(() => ({ lat: 39.8283, lng: -98.5795 }), []);
    const mapOptions = useMemo(() => ({
        disableDefaultUI: false,
        clickableIcons: true,
        scrollwheel: true,
        styles: [
            {
                featureType: "poi",
                elementType: "labels",
                stylers: [{ visibility: "off" }]
            }
        ]
    }), []);

    const { isLoaded } = useJsApiLoader({
        id: 'google-map-script',
        googleMapsApiKey: process.env.REACT_APP_GOOGLE_MAPS_API_KEY || '',
        libraries: GOOGLE_MAPS_LIBRARIES
    });

    // Fetch functions
    const fetchDashboardData = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/analytics/dashboard`);
            if (response.ok) {
                const data = await response.json();
                setDashboardData(data);
                updateGamificationScore(data);
            }
        } catch (error) {
            console.error('Error fetching dashboard data:', error);
        }
    };

    const fetchVehicles = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/vehicles`);
            if (response.ok) {
                const data = await response.json();
                setVehicles(data);
            }
        } catch (error) {
            console.error('Error fetching vehicles:', error);
        }
    };

    const fetchLoads = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/loads?limit=100`);
            if (response.ok) {
                const data = await response.json();
                setLoads(data);
            }
        } catch (error) {
            console.error('Error fetching loads:', error);
        }
    };

    const fetchRecentEvents = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/events/recent?limit=20`);
            if (response.ok) {
                const data = await response.json();
                setEvents(data.events || []);
                processEventsForAlerts(data.events || []);
            }
        } catch (error) {
            console.error('Error fetching events:', error);
        }
    };

    // WebSocket connection for real-time updates
    useEffect(() => {
        if (isConnected) {
            const cleanup = addEventListener((eventData) => {
                handleRealTimeEvent(eventData);
            });
            
            return cleanup;
        }
    }, [isConnected, addEventListener]);

    const handleRealTimeEvent = (eventData) => {
        setEvents(prev => [eventData, ...prev.slice(0, 19)]);
        
        // Update relevant state based on event type
        if (eventData.type?.includes('vehicle')) {
            fetchVehicles();
        } else if (eventData.type?.includes('load')) {
            fetchLoads();
        }
        
        // Process for alerts and gamification
        processEventForGamification(eventData);
    };

    const updateGamificationScore = (data) => {
        const score = Math.round(
            (data.on_time_percentage || 0) * 10 +
            (data.fuel_efficiency || 0) * 5 +
            (data.driver_satisfaction || 0) * 8
        );
        setGamificationScore(score);
    };

    const processEventForGamification = (event) => {
        if (event.type === 'LOAD_DELIVERED' && event.data?.on_time) {
            setAchievements(prev => [...prev, {
                id: Date.now(),
                title: 'On-Time Delivery! 🎯',
                points: 50,
                timestamp: new Date()
            }]);
        }
    };

    const processEventsForAlerts = (events) => {
        const alerts = events
            .filter(e => e.priority === 'high' || e.type?.includes('deviation'))
            .map(e => ({
                id: e.id,
                message: e.message,
                type: e.type,
                priority: e.priority,
                timestamp: e.timestamp
            }));
        setRealTimeAlerts(alerts);
    };

    // Event handlers
    const handleVehicleClick = (vehicle) => {
        setSelectedVehicle(vehicle);
        setSelectedLoad(null);
    };

    const handleLoadClick = (load) => {
        setSelectedLoad(load);
        setSelectedVehicle(null);
    };

    const getVehicleColor = (vehicle) => {
        if (!vehicle.status) return '#6B7280';
        switch (vehicle.status) {
            case 'AVAILABLE': return '#10B981';
            case 'IN_USE': return '#F59E0B';
            case 'MAINTENANCE': return '#EF4444';
            default: return '#6B7280';
        }
    };

    const getLoadStatusColor = (status) => {
        switch (status) {
            case 'PENDING': return '#6B7280';
            case 'ASSIGNED': return '#3B82F6';
            case 'PICKED_UP': return '#F59E0B';
            case 'IN_TRANSIT': return '#8B5CF6';
            case 'DELIVERED': return '#10B981';
            default: return '#6B7280';
        }
    };

    const formatEventTime = (timestamp) => {
        return new Date(timestamp).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    // Optimize route for a specific load
    const optimizeLoadRoute = async (load, driver_id, vehicle_id) => {
        setIsOptimizing(prev => new Set([...prev, load.id]));
        
        try {
            const response = await fetch('/api/routes/optimize-load', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
        body: JSON.stringify({
                    load_id: load.id,
                    driver_id: driver_id || 'placeholder-driver-id', // In real app, would be selected
                    vehicle_id: vehicle_id || 'placeholder-vehicle-id' // In real app, would be selected
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                
                // Fetch detailed route information
                const routeResponse = await fetch(`/api/routes/${result.route_id}`);
                if (routeResponse.ok) {
                    const routeDetails = await routeResponse.json();
                    
                    // Store optimized route
                    setOptimizedRoutes(prev => new Map(prev.set(load.id, {
                        ...routeDetails,
                        coordinates: routeDetails.route_coordinates
                    })));
                    
                    // Show success notification
                    console.log(`Route optimized for load ${load.load_number}: ${routeDetails.distance_miles} miles, ${routeDetails.duration_minutes} minutes`);
                }
            } else {
                console.error('Route optimization failed:', await response.text());
            }
        } catch (error) {
            console.error('Error optimizing route:', error);
        } finally {
            setIsOptimizing(prev => {
                const newSet = new Set(prev);
                newSet.delete(load.id);
                return newSet;
            });
        }
    };

    // Get route coordinates for display
    const getRouteCoordinates = (load) => {
        const optimizedRoute = optimizedRoutes.get(load.id);
        
        if (optimizedRoute && optimizedRoute.coordinates && optimizedRoute.coordinates.length > 0) {
            // Convert route coordinates to Google Maps format
            return optimizedRoute.coordinates.map(coord => ({
                lat: coord[1], // PostGIS stores as [lng, lat]
                lng: coord[0]
            }));
        }
        
        // Fallback to straight line if no optimized route
        return [
            { lat: load.pickup_latitude, lng: load.pickup_longitude },
            { lat: load.delivery_latitude, lng: load.delivery_longitude }
        ];
    };

    // Effects
    useEffect(() => {
        fetchDashboardData();
        fetchVehicles();
        fetchLoads();
        fetchRecentEvents();

        const dashboardInterval = setInterval(fetchDashboardData, 30000);
        const eventsInterval = setInterval(fetchRecentEvents, 10000);
        const vehiclesInterval = setInterval(fetchVehicles, 15000);
        const loadsInterval = setInterval(fetchLoads, 20000);

        return () => {
            clearInterval(dashboardInterval);
            clearInterval(eventsInterval);
            clearInterval(vehiclesInterval);
            clearInterval(loadsInterval);
        };
    }, []);

    if (!isLoaded) {
        return (
            <div className="flex flex-col items-center justify-center h-screen bg-slate-900 text-white">
                <div className="w-10 h-10 border-4 border-slate-700 border-t-blue-500 rounded-full animate-spin mb-4"></div>
                <p className="text-lg">Loading Google Maps...</p>
            </div>
        );
    }

    return (
        <div className="relative w-screen h-screen overflow-hidden bg-gradient-to-br from-slate-900 to-slate-800 font-sans text-white">
            {/* Gamification Header */}
            <div className="absolute top-0 left-0 right-0 h-16 bg-gradient-to-r from-slate-800 to-slate-700 border-b border-slate-600 flex items-center justify-between px-8 z-30">
                <div className="flex items-center space-x-4">
                    <span className="text-sm font-medium text-slate-300">Dispatch Score</span>
                    <span className="text-2xl font-bold text-emerald-400">{gamificationScore}</span>
                </div>
                <div className="flex items-center space-x-2">
                    {achievements.slice(-3).map(achievement => (
                        <div key={achievement.id} className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-3 py-1 rounded-full text-xs font-medium animate-pulse">
                            {achievement.title}
                        </div>
                    ))}
                </div>
                <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full animate-pulse ${
                        isConnected ? 'bg-green-400 shadow-lg shadow-green-400/50' : 'bg-red-400 shadow-lg shadow-red-400/50'
                    }`}></div>
                    <span className={`font-medium ${
                        isConnected ? 'text-green-400' : 'text-red-400'
                    }`}>{isConnected ? 'LIVE' : 'OFFLINE'}</span>
                </div>
            </div>

            {/* Critical Alerts Bar */}
            {realTimeAlerts.length > 0 && (
                <div className="absolute top-16 left-0 right-0 bg-gradient-to-r from-red-600 to-orange-600 border-b border-red-700 p-2 z-20">
                    {realTimeAlerts.slice(0, 2).map(alert => (
                        <div key={alert.id} className="flex items-center space-x-3 bg-red-800/30 backdrop-blur-sm rounded-lg p-2 mb-1 last:mb-0">
                            <span className="text-yellow-300 text-lg">⚠️</span>
                            <span className="text-white font-medium flex-1">{alert.message}</span>
                            <span className="text-red-200 text-xs">{formatEventTime(alert.timestamp)}</span>
                        </div>
                    ))}
                </div>
            )}

            <div className="flex h-full">
                {/* Interactive Map */}
                <div className="flex-1 relative" style={{ marginTop: realTimeAlerts.length > 0 ? '120px' : '64px' }}>
                    <GoogleMap
                        mapContainerStyle={{ width: '100%', height: '100%' }}
                        center={defaultCenter}
                        zoom={4}
                        options={mapOptions}
                    >
                        {/* Vehicle Markers */}
                        {activeFilters.showVehicles && vehicles.map(vehicle => (
                            vehicle.latitude && vehicle.longitude && (
                                <Marker
                                    key={`vehicle-${vehicle.vehicle_number}`}
                                    position={{
                                        lat: vehicle.latitude,
                                        lng: vehicle.longitude
                                    }}
                                    onClick={() => handleVehicleClick(vehicle)}
                                    icon={{
                                        path: window.google?.maps?.SymbolPath?.FORWARD_CLOSED_ARROW,
                                        scale: 8,
                                        fillColor: getVehicleColor(vehicle),
                                        fillOpacity: 0.9,
                                        strokeWeight: 2,
                                        strokeColor: '#FFFFFF',
                                        rotation: vehicle.heading || 0
                                    }}
                                    title={`Vehicle: ${vehicle.vehicle_number} - ${vehicle.status}`}
                                />
                            )
                        ))}

                        {/* Load Markers */}
                        {activeFilters.showLoads && loads.map(load => (
                            load.pickup_latitude && load.pickup_longitude && (
                                <React.Fragment key={`load-${load.load_number}`}>
                                    {/* Pickup Location - Circle */}
                                    <Marker
                                        position={{
                                            lat: load.pickup_latitude,
                                            lng: load.pickup_longitude
                                        }}
                                        onClick={() => handleLoadClick(load)}
                                        icon={{
                                            path: window.google?.maps?.SymbolPath?.CIRCLE,
                                            scale: 10,
                                            fillColor: getLoadStatusColor(load.status),
                                            fillOpacity: 0.8,
                                            strokeWeight: 3,
                                            strokeColor: '#FFFFFF'
                                        }}
                                        title={`Pickup: ${load.load_number} - ${load.status}`}
                                    />
                                    {/* Delivery Location - Square */}
                                    {load.delivery_latitude && load.delivery_longitude && (
                                        <Marker
                                            position={{
                                                lat: load.delivery_latitude,
                                                lng: load.delivery_longitude
                                            }}
                                            onClick={() => handleLoadClick(load)}
                                            icon={{
                                                path: 'M -8,-8 L 8,-8 L 8,8 L -8,8 Z', // Square path
                                                scale: 1,
                                                fillColor: getLoadStatusColor(load.status),
                                                fillOpacity: 0.8,
                                                strokeWeight: 3,
                                                strokeColor: '#FFFFFF'
                                            }}
                                            title={`Delivery: ${load.load_number} - ${load.status}`}
                                        />
                                    )}
                                    {/* Route Line - Show optimized route or straight line */}
                                    {activeFilters.showRoutes && activeFilters.showLoads && 
                                     load.delivery_latitude && load.delivery_longitude && (
                                         <>
                                             <Polyline
                                                 path={getRouteCoordinates(load)}
                                                 options={{
                                                     strokeColor: getLoadStatusColor(load.status),
                                                     strokeOpacity: optimizedRoutes.has(load.id) ? 0.8 : 0.6,
                                                     strokeWeight: optimizedRoutes.has(load.id) ? 3 : 2,
                                                     strokeDashArray: optimizedRoutes.has(load.id) ? null : [5, 5], // Dashed for non-optimized
                                                     icons: [{
                                                         icon: {
                                                             path: window.google?.maps?.SymbolPath?.FORWARD_OPEN_ARROW,
                                                             scale: optimizedRoutes.has(load.id) ? 3 : 2,
                                                             strokeColor: getLoadStatusColor(load.status)
                                                         },
                                                         offset: '50%'
                                                     }]
                                                 }}
                                             />
                                             {/* Route optimization button */}
                                             {!optimizedRoutes.has(load.id) && (
                                                  <div className="absolute top-2 left-2 z-[1000]">
                                                      <button
                                                          onClick={() => optimizeLoadRoute(load)}
                                                          disabled={isOptimizing.has(load.id)}
                                                          className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-3 py-1 rounded-md text-sm font-medium transition-colors duration-200 shadow-lg"
                                                          title="Optimize route with Google Maps"
                                                      >
                                                          {isOptimizing.has(load.id) ? '🔄 Optimizing...' : '🗺️ Optimize Route'}
                                                      </button>
                                                  </div>
                                              )}
                                         </>
                                     )}
                                </React.Fragment>
                            )
                        ))}

                        {/* Vehicle Info Window */}
                        {selectedVehicle && (
                            <InfoWindow
                                position={{
                                    lat: selectedVehicle.latitude,
                                    lng: selectedVehicle.longitude
                                }}
                                onCloseClick={() => setSelectedVehicle(null)}
                            >
                                <div className="bg-white rounded-lg p-4 shadow-lg border border-slate-200 min-w-64">
                                    <h4 className="text-slate-800 font-semibold mb-3 flex items-center gap-2">🚛 {selectedVehicle.vehicle_number}</h4>
                                    <div className="space-y-2 text-sm">
                                        <p className="text-slate-700"><span className="font-medium">Status:</span> <span className="text-green-600">{selectedVehicle.status}</span></p>
                                        {selectedVehicle.driver && (
                                            <p className="text-slate-700"><span className="font-medium">Driver:</span> {selectedVehicle.driver}</p>
                                        )}
                                        <p className="text-slate-700"><span className="font-medium">Last Update:</span> {formatEventTime(selectedVehicle.updated_at)}</p>
                                    </div>
                                </div>
                            </InfoWindow>
                        )}

                        {/* Load Info Window */}
                        {selectedLoad && (
                            <InfoWindow
                                position={{
                                    lat: selectedLoad.pickup_latitude,
                                    lng: selectedLoad.pickup_longitude
                                }}
                                onCloseClick={() => setSelectedLoad(null)}
                            >
                                <div className="bg-white rounded-lg p-4 shadow-lg border border-slate-200 min-w-72">
                                    <h4 className="text-slate-800 font-semibold mb-3 flex items-center gap-2">📦 Load {selectedLoad.load_number}</h4>
                                    <div className="space-y-2 text-sm">
                                        <p className="text-slate-700"><span className="font-medium">Status:</span> <span className="text-blue-600">{selectedLoad.status}</span></p>
                                        <p className="text-slate-700"><span className="font-medium">Weight:</span> {selectedLoad.weight || 'N/A'} lbs</p>
                                        <div className="bg-slate-50 rounded-md p-2 space-y-1">
                                            <p className="text-slate-700"><span className="font-medium text-blue-600">● Pickup:</span> {new Date(selectedLoad.pickup_date).toLocaleDateString() ? new Date(selectedLoad.pickup_date).toLocaleDateString() : 'Not scheduled'}</p>
                                            {selectedLoad.delivery_date && (
                                                <p className="text-slate-700"><span className="font-medium text-amber-500">■ Delivery:</span> {new Date(selectedLoad.delivery_date).toLocaleDateString()}</p>
                                            )}
                                        </div>
                                        {selectedLoad.distance && (
                                            <p className="text-slate-700"><span className="font-medium">Distance:</span> {selectedLoad.distance} miles</p>
                                        )}
                                        
                                        {/* Show optimized route info */}
                                        {optimizedRoutes.has(selectedLoad.id) && (
                                            <div className="border-t border-slate-200 pt-3 mt-3">
                                                <h5 className="text-slate-800 font-medium mb-2 flex items-center gap-1">🗺️ Optimized Route</h5>
                                                <div className="bg-green-50 rounded-md p-2 space-y-1">
                                                    <p className="text-slate-700 text-xs"><span className="font-medium">Distance:</span> {optimizedRoutes.get(selectedLoad.id).distance_miles} miles</p>
                                                    <p className="text-slate-700 text-xs"><span className="font-medium">Duration:</span> {optimizedRoutes.get(selectedLoad.id).duration_minutes} minutes</p>
                                                    <p className="text-slate-700 text-xs"><span className="font-medium">Score:</span> <span className="text-green-600 font-semibold">{optimizedRoutes.get(selectedLoad.id).optimization_score}/100</span></p>
                                                </div>
                                            </div>
                                        )}
                                        
                                        {/* Route optimization button in info window */}
                                        {!optimizedRoutes.has(selectedLoad.id) && (
                                            <div className="pt-2">
                                                <button
                                                    onClick={() => optimizeLoadRoute(selectedLoad)}
                                                    disabled={isOptimizing.has(selectedLoad.id)}
                                                    className="bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white px-3 py-1 rounded-md text-sm font-medium transition-colors duration-200 w-full"
                                                >
                                                    {isOptimizing.has(selectedLoad.id) ? '🔄 Optimizing...' : '🗺️ Optimize Route'}
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </InfoWindow>
                        )}
                    </GoogleMap>

                    {/* Map Legend */}
                    <div className="absolute top-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg p-4 shadow-lg border border-slate-200 z-10 min-w-48">
                        <h4 className="text-slate-800 font-semibold mb-3 flex items-center gap-2">📍 Map Legend</h4>
                        <div className="space-y-2">
                            <div className="flex items-center gap-2">
                                <span className="text-green-600 font-bold text-lg">→</span>
                                <span className="text-green-600 text-sm font-medium">Vehicles ({vehicles.length})</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-blue-600 font-bold text-lg">●</span>
                                <span className="text-blue-600 text-sm font-medium">Pickup Locations</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-amber-500 font-bold text-lg">■</span>
                                <span className="text-amber-500 text-sm font-medium">Delivery Locations</span>
                            </div>
                            {activeFilters.showRoutes && (
                                <>
                                    <div className="flex items-center gap-2">
                                        <div className="w-6 h-1 bg-green-500 rounded-full"></div>
                                        <span className="text-green-600 text-sm font-medium">Optimized Routes</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <div className="w-6 h-1 border-b-2 border-dashed border-yellow-500"></div>
                                        <span className="text-yellow-600 text-sm font-medium">Straight-Line Routes</span>
                                    </div>
                                </>
                            )}
                        </div>
                    </div>

                    {/* Map Controls */}
                    <div className="absolute top-4 right-4 bg-white/90 backdrop-blur-sm rounded-lg p-4 shadow-lg border border-slate-200 z-10">
                        <div className="flex flex-col space-y-2">
                            <button
                                className={`px-4 py-2 rounded-lg font-medium text-sm transition-all duration-200 transform hover:scale-105 ${
                                    activeFilters.showVehicles 
                                        ? 'bg-gradient-to-r from-green-500 to-green-600 text-white shadow-lg shadow-green-500/30' 
                                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                                }`}
                                onClick={() => setActiveFilters(prev => ({...prev, showVehicles: !prev.showVehicles}))}
                                title="Toggle vehicle markers (arrows)"
                            >
                                🚛 Vehicles ({vehicles.length})
                            </button>
                            <button
                                className={`px-4 py-2 rounded-lg font-medium text-sm transition-all duration-200 transform hover:scale-105 ${
                                    activeFilters.showLoads 
                                        ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-lg shadow-blue-500/30' 
                                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                                }`}
                                onClick={() => setActiveFilters(prev => ({...prev, showLoads: !prev.showLoads}))}
                                title="Toggle load markers (circles/squares)"
                            >
                                📦 Loads ({loads.length})
                            </button>
                            <button
                                className={`px-4 py-2 rounded-lg font-medium text-sm transition-all duration-200 transform hover:scale-105 ${
                                    activeFilters.showRoutes 
                                        ? 'bg-gradient-to-r from-purple-500 to-purple-600 text-white shadow-lg shadow-purple-500/30' 
                                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                                }`}
                                onClick={() => setActiveFilters(prev => ({...prev, showRoutes: !prev.showRoutes}))}
                                title="Toggle route lines between pickup and delivery"
                            >
                                🗺️ Routes
                            </button>
                        </div>
                    </div>
                </div>

                {/* Real-Time Events Sidebar */}
                <div className="w-80 bg-slate-800/95 backdrop-blur-sm border-l border-slate-700 flex flex-col">
                    <div className="flex items-center justify-between p-4 border-b border-slate-700">
                        <h3 className="text-white font-semibold flex items-center gap-2">
                            <span className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></span>
                            Live Events
                        </h3>
                        <div className="bg-slate-700 text-white px-2 py-1 rounded-full text-xs font-medium">
                            {events.length}
                        </div>
                    </div>
                    <div className="flex-1 overflow-y-auto p-4 space-y-3">
                        {events.map((event, index) => {
                            const priorityColors = {
                                high: 'border-red-500 bg-red-500/10',
                                medium: 'border-yellow-500 bg-yellow-500/10',
                                normal: 'border-slate-600 bg-slate-700/30'
                            };
                            const priority = event.priority || 'normal';
                            
                            return (
                                <div key={event.id || index} className={`border-l-4 rounded-lg p-3 transition-all duration-200 hover:scale-105 ${priorityColors[priority]}`}>
                                    <div className="flex items-start gap-3">
                                        <div className="text-2xl flex-shrink-0">
                                            {event.type?.includes('load') ? '📦' :
                                             event.type?.includes('vehicle') ? '🚛' :
                                             event.type?.includes('driver') ? '👤' :
                                             event.type?.includes('route') ? '🗺️' : '📡'}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="text-white font-medium text-sm mb-1">{event.type}</div>
                                            <div className="text-slate-300 text-sm mb-2 leading-relaxed">{event.message}</div>
                                            <div className="text-slate-400 text-xs">{formatEventTime(event.timestamp)}</div>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>

            {/* Operations Dashboard */}
            <div className="bg-slate-900/95 backdrop-blur-sm border-t border-slate-700 p-6">
                <div className="flex items-center justify-between mb-6">
                    <h3 className="text-white text-xl font-semibold">Operations Center</h3>
                    <button 
                        className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-4 py-2 rounded-lg font-medium transition-all duration-200 hover:scale-105 shadow-lg"
                        onClick={onTransitionToManagement}
                    >
                        Management View →
                    </button>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="bg-slate-800/80 rounded-xl p-4 border border-slate-700 hover:border-slate-600 transition-all duration-200 hover:scale-105">
                        <div className="flex items-center gap-3">
                            <div className="text-3xl">📦</div>
                            <div className="flex-1">
                                <div className="text-2xl font-bold text-white mb-1">{dashboardData.active_loads || 0}</div>
                                <div className="text-slate-400 text-sm">Active Loads</div>
                            </div>
                        </div>
                    </div>
                    <div className="bg-slate-800/80 rounded-xl p-4 border border-slate-700 hover:border-slate-600 transition-all duration-200 hover:scale-105">
                        <div className="flex items-center gap-3">
                            <div className="text-3xl">🎯</div>
                            <div className="flex-1">
                                <div className="text-2xl font-bold text-white mb-1">{dashboardData.on_time_percentage || 0}%</div>
                                <div className="text-slate-400 text-sm">On-Time Rate</div>
                            </div>
                        </div>
                    </div>
                    <div className="bg-slate-800/80 rounded-xl p-4 border border-slate-700 hover:border-slate-600 transition-all duration-200 hover:scale-105">
                        <div className="flex items-center gap-3">
                            <div className="text-3xl">🚛</div>
                            <div className="flex-1">
                                <div className="text-2xl font-bold text-white mb-1">{dashboardData.available_vehicles || 0}</div>
                                <div className="text-slate-400 text-sm">Available Vehicles</div>
                            </div>
                        </div>
                    </div>
                    <div className="bg-slate-800/80 rounded-xl p-4 border border-slate-700 hover:border-slate-600 transition-all duration-200 hover:scale-105">
                        <div className="flex items-center gap-3">
                            <div className="text-3xl">👤</div>
                            <div className="flex-1">
                                <div className="text-2xl font-bold text-white mb-1">{dashboardData.available_drivers || 0}</div>
                                <div className="text-slate-400 text-sm">Available Drivers</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DispatchMapView;
