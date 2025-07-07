import React, { useState, useEffect } from 'react';
import { useWebSocket } from '../contexts/WebSocketContext';
import { useMapData } from '../hooks/useMapData';
import { useRouteOptimization } from '../hooks/useRouteOptimization';
import MapContainer from './map/MapContainer';

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

const DispatchMapView = ({ onTransitionToManagement, visibleRoutes, onRouteVisibilityChange, onMapLoad, isDarkMode }) => {
    // Use custom hooks for data management
    const { 
        events, 
        vehicles, 
        loads, 
        routes,
        drivers, 
        dashboardData,
        isLoading: dataLoading,
        error: dataError,
        fetchMapData 
    } = useMapData();
    
    const {
        optimizedRoutes,
        isOptimizing,
        optimizationError,
        optimizeLoadRoute,
        clearOptimization,
        isLoadOptimizing,
        getOptimization
    } = useRouteOptimization();
    
    // Local UI state
    const [selectedVehicle, setSelectedVehicle] = useState(null);
    const [selectedLoad, setSelectedLoad] = useState(null);
    const [selectedVehicleForOptimization, setSelectedVehicleForOptimization] = useState(null);
    const [activeFilters, setActiveFilters] = useState({
        showVehicles: true,
        showLoads: true,
        showRoutes: true,
        eventTypes: ['all']
    });
    const [gamificationScore, setGamificationScore] = useState(0);
    const [achievements, setAchievements] = useState([]);
    const [realTimeAlerts, setRealTimeAlerts] = useState([]);
    
    // WebSocket connection
    const { isConnected, events: wsEvents, addEventListener } = useWebSocket();

    // WebSocket event handler
    const handleRealTimeEvent = (eventData) => {
        // Process events for alerts and gamification
        if (eventData.type === 'LOAD_DELIVERED' && eventData.data?.on_time) {
            setAchievements(prev => [...prev, {
                id: Date.now(),
                title: 'On-Time Delivery! 🎯',
                points: 50,
                timestamp: new Date()
            }]);
        }
        
        // Filter high priority events for alerts
        if (eventData.priority === 'high' || eventData.type?.includes('deviation')) {
            setRealTimeAlerts(prev => [{
                id: eventData.id,
                message: eventData.message,
                type: eventData.type,
                priority: eventData.priority,
                timestamp: eventData.timestamp
            }, ...prev.slice(0, 4)]);
        }
    };

    // Update gamification score based on dashboard data
    const updateGamificationScore = (data) => {
        const score = Math.round(
            (data.on_time_percentage || 0) * 10 +
            (data.fuel_efficiency || 0) * 5 +
            (data.driver_satisfaction || 0) * 8
        );
        setGamificationScore(score);
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

    const formatEventTime = (timestamp) => {
        return new Date(timestamp).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    // WebSocket connection for real-time updates
    useEffect(() => {
        if (isConnected) {
            const cleanup = addEventListener(handleRealTimeEvent);
            return cleanup;
        }
    }, [isConnected, addEventListener]);

    // Update gamification score when dashboard data changes
    useEffect(() => {
        if (dashboardData) {
            updateGamificationScore(dashboardData);
        }
    }, [dashboardData]);

    return (
        <div className="relative w-screen h-screen overflow-hidden bg-gradient-to-br from-slate-900 to-slate-800 font-sans text-white">
            {/* Enhanced Analytics Header */}
            <div className="absolute top-0 left-0 right-0 h-20 bg-gradient-to-r from-slate-800 to-slate-700 border-b border-slate-600 px-8 z-30">
                <div className="flex items-center justify-between h-full">
                    {/* Left Section - Key Metrics */}
                    <div className="flex items-center space-x-8">
                        <div className="text-center">
                            <div className="text-2xl font-bold text-blue-400">{loads?.filter(l => l.status === 'assigned' || l.status === 'in_transit').length || 0}</div>
                            <div className="text-xs text-slate-300 uppercase tracking-wide">Active Loads</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold text-green-400">{vehicles?.filter(v => v.status === 'available').length || 0}</div>
                            <div className="text-xs text-slate-300 uppercase tracking-wide">Available Trucks</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold text-purple-400">{drivers?.filter(d => d.status === 'available').length || 0}</div>
                            <div className="text-xs text-slate-300 uppercase tracking-wide">Available Drivers</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold text-emerald-400">{dashboardData?.on_time_percentage ? `${Math.round(dashboardData.on_time_percentage)}%` : 'N/A'}</div>
                            <div className="text-xs text-slate-300 uppercase tracking-wide">On-Time Rate</div>
                        </div>
                    </div>
                    
                    {/* Center Section - Achievements */}
                    <div className="flex items-center space-x-2">
                        {achievements.slice(-2).map(achievement => (
                            <div key={achievement.id} className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-3 py-1 rounded-full text-xs font-medium animate-pulse">
                                {achievement.title}
                            </div>
                        ))}
                    </div>
                    
                    {/* Right Section - Connection & Revenue */}
                    <div className="flex items-center space-x-6">
                        <div className="text-center">
                            <div className="text-2xl font-bold text-yellow-400">
                                ${dashboardData?.total_revenue ? (dashboardData.total_revenue / 1000).toFixed(0) + 'K' : '0'}
                            </div>
                            <div className="text-xs text-slate-300 uppercase tracking-wide">Total Revenue</div>
                        </div>
                        <div className="flex items-center space-x-2">
                            <div className={`w-3 h-3 rounded-full animate-pulse ${
                                isConnected ? 'bg-green-400 shadow-lg shadow-green-400/50' : 'bg-red-400 shadow-lg shadow-red-400/50'
                            }`}></div>
                            <span className={`font-medium text-sm ${
                                isConnected ? 'text-green-400' : 'text-red-400'
                            }`}>{isConnected ? 'LIVE' : 'OFFLINE'}</span>
                        </div>
                    </div>
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
                {/* Map Container with all markers and routes */}
                <div className="flex-1 relative" style={{ marginTop: realTimeAlerts.length > 0 ? '140px' : '80px' }}>
                    <MapContainer
                        vehicles={vehicles}
                        loads={loads}
                        events={events}
                        routes={routes}
                        optimizedRoutes={optimizedRoutes}
                        selectedVehicle={selectedVehicle}
                        selectedLoad={selectedLoad}
                        selectedVehicleForOptimization={selectedVehicleForOptimization}
                        activeFilters={activeFilters}
                        visibleRoutes={visibleRoutes}
                        onVehicleSelect={handleVehicleClick}
                        onLoadSelect={handleLoadClick}
                        onVehicleSelectionChange={setSelectedVehicleForOptimization}
                        onOptimizeRoute={optimizeLoadRoute}
                        isOptimizing={isOptimizing}
                        onMapLoad={onMapLoad}
                        isDarkMode={isDarkMode}
                    />
                </div>
            </div>
        </div>
    );
};

export default DispatchMapView;
