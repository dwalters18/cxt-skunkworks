import React, { useState, useEffect } from 'react';
import { useWebSocket } from '../contexts/WebSocketContext';
import { useMapData } from '../hooks/useMapData';
import { useRouteOptimization } from '../hooks/useRouteOptimization';
import MapContainer from './map/MapContainer';

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

const DispatchMapView = ({ onTransitionToManagement }) => {
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
                {/* Map Container with all markers and routes */}
                <div className="flex-1 relative" style={{ marginTop: realTimeAlerts.length > 0 ? '120px' : '64px' }}>
                    <MapContainer
                        vehicles={vehicles}
                        loads={loads}
                        events={events}
                        optimizedRoutes={optimizedRoutes}
                        selectedVehicle={selectedVehicle}
                        selectedLoad={selectedLoad}
                        selectedVehicleForOptimization={selectedVehicleForOptimization}
                        activeFilters={activeFilters}
                        onVehicleSelect={handleVehicleClick}
                        onLoadSelect={handleLoadClick}
                        onVehicleSelectionChange={setSelectedVehicleForOptimization}
                        onRouteOptimization={optimizeLoadRoute}
                        isOptimizing={isOptimizing}
                    />
                </div>
            </div>
        </div>
    );
};

export default DispatchMapView;
