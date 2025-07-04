import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { GoogleMap, useJsApiLoader, Marker, InfoWindow, Polyline, Circle, DirectionsService, DirectionsRenderer } from '@react-google-maps/api';
import { useWebSocket } from '../contexts/WebSocketContext';
import './DispatchMapView.css';

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
            <div className="dispatch-loading">
                <div className="loading-spinner"></div>
                <p>Loading Google Maps...</p>
            </div>
        );
    }

    return (
        <div className="dispatch-map-view">
            {/* Gamification Header */}
            <div className="gamification-header">
                <div className="score-display">
                    <span className="score-label">Dispatch Score</span>
                    <span className="score-value">{gamificationScore}</span>
                </div>
                <div className="achievements-ticker">
                    {achievements.slice(-3).map(achievement => (
                        <div key={achievement.id} className="achievement-badge">
                            {achievement.title}
                        </div>
                    ))}
                </div>
                <div className="live-status">
                    <div className={`pulse ${isConnected ? '' : 'disconnected'}`}></div>
                    <span>{isConnected ? 'LIVE' : 'OFFLINE'}</span>
                </div>
            </div>

            {/* Critical Alerts Bar */}
            {realTimeAlerts.length > 0 && (
                <div className="critical-alerts">
                    {realTimeAlerts.slice(0, 2).map(alert => (
                        <div key={alert.id} className="alert-item critical">
                            <span className="alert-icon">⚠️</span>
                            <span className="alert-text">{alert.message}</span>
                            <span className="alert-time">{formatEventTime(alert.timestamp)}</span>
                        </div>
                    ))}
                </div>
            )}

            <div className="main-content">
                {/* Interactive Map */}
                <div className="map-container">
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
                                                 <div 
                                                     className="route-optimize-btn"
                                                     style={{
                                                         position: 'absolute',
                                                         top: '10px',
                                                         left: '10px',
                                                         zIndex: 1000
                                                     }}
                                                 >
                                                     <button
                                                         onClick={() => optimizeLoadRoute(load)}
                                                         disabled={isOptimizing.has(load.id)}
                                                         className="btn btn-sm btn-primary"
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
                                <div className="info-window vehicle-info">
                                    <h4>🚛 {selectedVehicle.vehicle_number}</h4>
                                    <p><strong>Status:</strong> {selectedVehicle.status}</p>
                                    <p><strong>Type:</strong> {selectedVehicle.vehicle_type}</p>
                                    {selectedVehicle.driver && (
                                        <p><strong>Driver:</strong> {selectedVehicle.driver}</p>
                                    )}
                                    <p><strong>Last Update:</strong> {formatEventTime(selectedVehicle.updated_at)}</p>
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
                                <div className="info-window load-info">
                                    <h4>📦 Load {selectedLoad.load_number}</h4>
                                    <p><strong>Status:</strong> {selectedLoad.status}</p>
                                    <p><strong>Weight:</strong> {selectedLoad.weight || 'N/A'} lbs</p>
                                    <div className="load-locations">
                                        <p><strong>● Pickup:</strong> {new Date(selectedLoad.pickup_date).toLocaleDateString() ? new Date(selectedLoad.pickup_date).toLocaleDateString() : 'Not scheduled'}</p>
                                        {selectedLoad.delivery_date && (
                                            <p><strong>■ Delivery:</strong> {new Date(selectedLoad.delivery_date).toLocaleDateString()}</p>
                                        )}
                                    </div>
                                    {selectedLoad.distance && (
                                        <p><strong>Distance:</strong> {selectedLoad.distance} miles</p>
                                    )}
                                    
                                    {/* Show optimized route info */}
                                    {optimizedRoutes.has(selectedLoad.id) && (
                                        <div className="optimized-route-info">
                                            <hr />
                                            <h5>🗺️ Optimized Route</h5>
                                            <p><strong>Distance:</strong> {optimizedRoutes.get(selectedLoad.id).distance_miles} miles</p>
                                            <p><strong>Duration:</strong> {optimizedRoutes.get(selectedLoad.id).duration_minutes} minutes</p>
                                            <p><strong>Score:</strong> {optimizedRoutes.get(selectedLoad.id).optimization_score}/100</p>
                                        </div>
                                    )}
                                    
                                    {/* Route optimization button in info window */}
                                    {!optimizedRoutes.has(selectedLoad.id) && (
                                        <div className="route-actions">
                                            <button
                                                onClick={() => optimizeLoadRoute(selectedLoad)}
                                                disabled={isOptimizing.has(selectedLoad.id)}
                                                className="btn btn-sm btn-success mt-2"
                                            >
                                                {isOptimizing.has(selectedLoad.id) ? '🔄 Optimizing...' : '🗺️ Optimize Route'}
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </InfoWindow>
                        )}
                    </GoogleMap>

                    {/* Map Legend */}
                    <div className="map-legend">
                        <h4>📍 Map Legend</h4>
                        <div className="legend-item">
                            <span className="legend-symbol">→</span>
                            <span style={{ color: '#28a745' }}>Vehicles ({vehicles.length})</span>
                        </div>
                        <div className="legend-item">
                            <span className="legend-symbol">●</span>
                            <span style={{ color: '#007bff' }}>Pickup Locations</span>
                        </div>
                        <div className="legend-item">
                            <span className="legend-symbol">■</span>
                            <span style={{ color: '#f59e0b' }}>Delivery Locations</span>
                        </div>
                        {activeFilters.showRoutes && (
                            <>
                                <div className="legend-item">
                                    <div className="legend-line optimized"></div>
                                    <span style={{ color: '#28a745' }}>Optimized Routes</span>
                                </div>
                                <div className="legend-item">
                                    <div className="legend-line straight"></div>
                                    <span style={{ color: '#ffc107' }}>Straight-Line Routes</span>
                                </div>
                            </>
                        )}
                    </div>

                    {/* Map Controls */}
                    <div className="map-controls">
                        <div className="filter-controls">
                            <button
                                className={`filter-btn vehicles ${activeFilters.showVehicles ? 'active' : ''}`}
                                onClick={() => setActiveFilters(prev => ({...prev, showVehicles: !prev.showVehicles}))}
                                title="Toggle vehicle markers (arrows)"
                            >
                                🚛 Vehicles ({vehicles.length})
                            </button>
                            <button
                                className={`filter-btn loads ${activeFilters.showLoads ? 'active' : ''}`}
                                onClick={() => setActiveFilters(prev => ({...prev, showLoads: !prev.showLoads}))}
                                title="Toggle load markers (circles/squares)"
                            >
                                📦 Loads ({loads.length})
                            </button>
                            <button
                                className={`filter-btn routes ${activeFilters.showRoutes ? 'active' : ''}`}
                                onClick={() => setActiveFilters(prev => ({...prev, showRoutes: !prev.showRoutes}))}
                                title="Toggle route lines between pickup and delivery"
                            >
                                🗺️ Routes
                            </button>
                        </div>
                        <div className="legend">
                            <div className="legend-title">Map Legend</div>
                            <div className="legend-items">
                                <div className="legend-item">
                                    <span className="legend-symbol vehicle-arrow">→</span>
                                    <span>Vehicles</span>
                                </div>
                                <div className="legend-item">
                                    <span className="legend-symbol pickup-circle">●</span>
                                    <span>Pickup</span>
                                </div>
                                <div className="legend-item">
                                    <span className="legend-symbol delivery-square">■</span>
                                    <span>Delivery</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Real-Time Events Sidebar */}
                <div className="events-sidebar">
                    <div className="sidebar-header">
                        <h3>🔴 Live Events</h3>
                        <div className="event-count">{events.length}</div>
                    </div>
                    <div className="events-list">
                        {events.map((event, index) => (
                            <div key={event.id || index} className={`event-item priority-${event.priority || 'normal'}`}>
                                <div className="event-icon">
                                    {event.type?.includes('load') ? '📦' :
                                     event.type?.includes('vehicle') ? '🚛' :
                                     event.type?.includes('driver') ? '👤' :
                                     event.type?.includes('route') ? '🗺️' : '📡'}
                                </div>
                                <div className="event-content">
                                    <div className="event-type">{event.type}</div>
                                    <div className="event-message">{event.message}</div>
                                    <div className="event-time">{formatEventTime(event.timestamp)}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Operations Dashboard */}
            <div className="operations-dashboard">
                <div className="dashboard-header">
                    <h3>Operations Center</h3>
                    <button className="management-button" onClick={onTransitionToManagement}>
                        Management View →
                    </button>
                </div>
                <div className="dashboard-metrics">
                    <div className="metric-card">
                        <div className="metric-icon">📦</div>
                        <div className="metric-content">
                            <div className="metric-value">{dashboardData.active_loads || 0}</div>
                            <div className="metric-label">Active Loads</div>
                        </div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-icon">🎯</div>
                        <div className="metric-content">
                            <div className="metric-value">{dashboardData.on_time_percentage || 0}%</div>
                            <div className="metric-label">On-Time Rate</div>
                        </div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-icon">🚛</div>
                        <div className="metric-content">
                            <div className="metric-value">{dashboardData.available_vehicles || 0}</div>
                            <div className="metric-label">Available Vehicles</div>
                        </div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-icon">👤</div>
                        <div className="metric-content">
                            <div className="metric-value">{dashboardData.available_drivers || 0}</div>
                            <div className="metric-label">Available Drivers</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DispatchMapView;
