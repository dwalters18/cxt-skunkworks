import React, { useState, useEffect } from 'react';
import './DispatchMapView.css';

const DispatchMapView = ({ onTransitionToManagement }) => {
    const [events, setEvents] = useState([]);
    const [dashboardMetrics, setDashboardMetrics] = useState({
        activeLoads: 42,
        onTimeRate: 98,
        availableDrivers: 8
    });

    const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

    useEffect(() => {
        fetchRecentEvents();
        const interval = setInterval(fetchRecentEvents, 5000);
        return () => clearInterval(interval);
    }, []);

    const fetchRecentEvents = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/events/recent?limit=10`);
            if (response.ok) {
                const data = await response.json();
                setEvents(data.events || []);
            }
        } catch (error) {
            console.error('Error fetching events:', error);
            // Fallback sample events for demonstration
            setEvents([
                { id: 1, type: 'load.in_transit', message: 'Load L-2024-001 is in transit to downtown delivery', timestamp: new Date().toISOString(), priority: 'normal' },
                { id: 2, type: 'vehicle.location_updated', message: 'Vehicle V-001 location updated: 123 Main St', timestamp: new Date().toISOString(), priority: 'normal' },
                { id: 3, type: 'route.deviation', message: 'CRITICAL: Vehicle V-003 deviated from planned route', timestamp: new Date().toISOString(), priority: 'high' },
                { id: 4, type: 'load.delivered', message: 'Load L-2024-002 successfully delivered', timestamp: new Date().toISOString(), priority: 'normal' },
                { id: 5, type: 'driver.status_changed', message: 'Driver D-007 status changed to available', timestamp: new Date().toISOString(), priority: 'normal' }
            ]);
        }
    };

    const getEventIcon = (type) => {
        if (type.includes('load')) return '📦';
        if (type.includes('vehicle')) return '🚛';
        if (type.includes('driver')) return '👤';
        if (type.includes('route')) return '🗺️';
        return '📡';
    };

    const getEventPriorityClass = (priority) => {
        switch (priority) {
            case 'high': return 'event-high';
            case 'medium': return 'event-medium';
            default: return 'event-normal';
        }
    };

    return (
        <div className="dispatch-map-view">
            {/* Map Background with Fleet Elements */}
            <div className="map-container">
                <div className="map-background"></div>
                
                {/* Fleet Trucks */}
                <div className="fleet-truck truck-green" style={{top: '25%', left: '20%'}} title="Truck T-001 - On Time">
                    🚛
                </div>
                <div className="fleet-truck truck-amber" style={{top: '45%', left: '60%'}} title="Truck T-002 - At Risk">
                    🚛
                </div>
                <div className="fleet-truck truck-red" style={{top: '70%', left: '35%'}} title="Truck T-003 - Delayed">
                    🚛
                </div>
                <div className="fleet-truck truck-green" style={{top: '55%', left: '80%'}} title="Truck T-004 - On Time">
                    🚛
                </div>

                {/* Delivery Points */}
                <div className="delivery-point delivered" style={{top: '30%', left: '75%'}} title="Delivery Completed">
                    📦<span className="checkmark">✓</span>
                </div>
                <div className="delivery-point pending" style={{top: '60%', left: '25%'}} title="Pending Delivery">
                    📦
                </div>
                <div className="delivery-point delivered" style={{top: '40%', left: '45%'}} title="Delivery Completed">
                    📦<span className="checkmark">✓</span>
                </div>
                <div className="delivery-point pending" style={{top: '75%', left: '65%'}} title="Pending Delivery">
                    📦
                </div>

                {/* Routes */}
                <svg className="route-overlay" width="100%" height="100%">
                    <path d="M 20% 25% Q 40% 35% 60% 45%" stroke="#22c55e" strokeWidth="3" fill="none" strokeDasharray="5,5">
                        <animate attributeName="stroke-dashoffset" values="0;-10" dur="1s" repeatCount="indefinite"/>
                    </path>
                    <path d="M 60% 45% Q 65% 55% 70% 65%" stroke="#f59e0b" strokeWidth="3" fill="none" strokeDasharray="5,5">
                        <animate attributeName="stroke-dashoffset" values="0;-10" dur="1s" repeatCount="indefinite"/>
                    </path>
                    <path d="M 35% 70% Q 50% 75% 65% 75%" stroke="#ef4444" strokeWidth="3" fill="none" strokeDasharray="5,5">
                        <animate attributeName="stroke-dashoffset" values="0;-10" dur="1s" repeatCount="indefinite"/>
                    </path>
                </svg>
            </div>

            {/* Real-Time Events Sidebar */}
            <div className="events-sidebar">
                <div className="sidebar-header">
                    <h3>Real-Time Events</h3>
                    <div className="live-indicator">🔴 LIVE</div>
                </div>
                <div className="events-list">
                    {events.map((event) => (
                        <div key={event.id} className={`event-item ${getEventPriorityClass(event.priority)}`}>
                            <div className="event-icon">{getEventIcon(event.type)}</div>
                            <div className="event-content">
                                <div className="event-type">{event.type.toUpperCase()}</div>
                                <div className="event-message">{event.message}</div>
                                <div className="event-time">
                                    {new Date(event.timestamp).toLocaleTimeString()}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Operations Dashboard */}
            <div className="operations-dashboard">
                <div className="dashboard-header">Operations Center</div>
                <div className="dashboard-metrics">
                    <div className="metric">
                        <span className="metric-label">Active Loads</span>
                        <span className="metric-value">{dashboardMetrics.activeLoads}</span>
                    </div>
                    <div className="metric">
                        <span className="metric-label">On-Time Rate</span>
                        <span className="metric-value">{dashboardMetrics.onTimeRate}%</span>
                    </div>
                    <div className="metric">
                        <span className="metric-label">Available Drivers</span>
                        <span className="metric-value">{dashboardMetrics.availableDrivers}</span>
                    </div>
                </div>
                <button className="management-button" onClick={onTransitionToManagement}>
                    Management View →
                </button>
            </div>
        </div>
    );
};

export default DispatchMapView;
