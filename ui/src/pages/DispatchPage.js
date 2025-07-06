import React, { useState, useEffect } from 'react';
import DispatchMapView from '../components/DispatchMapView';

const DispatchPage = () => {
    const [dashboardData, setDashboardData] = useState(null);
    const [performance, setPerformance] = useState(null);
    const [routesOptimized, setRoutesOptimized] = useState(0);
    const [loading, setLoading] = useState(true);
    const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

    const fetchDispatchStats = async () => {
        try {
            // Fetch dashboard data for active loads
            const dashboardResponse = await fetch(`${API_BASE}/api/analytics/dashboard`);
            if (dashboardResponse.ok) {
                const data = await dashboardResponse.json();
                setDashboardData(data);
            }

            // Fetch performance data for route optimization stats
            const performanceResponse = await fetch(`${API_BASE}/api/routes/performance?time_range=24h`);
            if (performanceResponse.ok) {
                const data = await performanceResponse.json();
                setPerformance(data);
            }

            // Calculate routes optimized from routes data
            const routesResponse = await fetch(`${API_BASE}/api/routes`);
            if (routesResponse.ok) {
                const data = await routesResponse.json();
                const optimizedToday = data.routes?.filter(route => {
                    const routeDate = new Date(route.created_at);
                    const today = new Date();
                    return routeDate.toDateString() === today.toDateString() && route.status === 'ACTIVE';
                }).length || 0;
                setRoutesOptimized(optimizedToday);
            }
        } catch (error) {
            console.error('Error fetching dispatch stats:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDispatchStats();
        // Refresh stats every 30 seconds
        const interval = setInterval(fetchDispatchStats, 30000);
        return () => clearInterval(interval);
    }, []);

    // Calculate gamification score based on performance metrics
    const calculateGamificationScore = () => {
        if (!performance || !dashboardData) return 0;
        
        let score = 0;
        // Base score from route efficiency
        score += Math.round((performance.route_efficiency || 0.85) * 100);
        // Bonus for on-time delivery
        if (performance.on_time_delivery_rate > 0.9) score += 20;
        // Bonus for fuel efficiency
        if (performance.fuel_efficiency > 7) score += 15;
        // Active loads handling bonus
        score += Math.min(dashboardData.active_loads || 0, 20);
        
        return Math.min(score, 999); // Cap at 999
    };

    const gamificationScore = calculateGamificationScore();
    const activeLoads = dashboardData?.active_loads || dashboardData?.total_loads - dashboardData?.loads_delivered || 0;

    return (
        <div className="h-full flex flex-col">
            {/* Header */}
            <div className="bg-white border-b border-gray-200 px-6 py-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                            <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                            </svg>
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">Dispatch</h1>
                            <p className="text-gray-600 text-sm">Manage loads, routes, and vehicle assignments</p>
                        </div>
                    </div>
                    
                    {/* Stats */}
                    <div className="flex items-center gap-4">
                        {loading ? (
                            <div className="text-center bg-gray-100 rounded-lg px-4 py-2">
                                <div className="animate-pulse bg-gray-300 h-6 w-12 rounded mb-1"></div>
                                <div className="text-xs text-gray-500">Loading...</div>
                            </div>
                        ) : (
                            <>
                                <div className="text-center bg-gray-50 rounded-lg px-4 py-2 border border-gray-200">
                                    <div className="text-blue-600 font-bold text-lg">
                                        {Math.round((performance?.route_efficiency || 0.85) * 100)}%
                                    </div>
                                    <div className="text-xs text-gray-600">Efficiency</div>
                                </div>
                                <div className="text-center bg-gray-50 rounded-lg px-4 py-2 border border-gray-200">
                                    <div className="text-green-600 font-bold text-lg">
                                        {routesOptimized}
                                    </div>
                                    <div className="text-xs text-gray-600">Routes Today</div>
                                </div>
                                <div className="text-center bg-gray-50 rounded-lg px-4 py-2 border border-gray-200">
                                    <div className="text-purple-600 font-bold text-lg">
                                        {activeLoads}
                                    </div>
                                    <div className="text-xs text-gray-600">Active Loads</div>
                                </div>
                                {performance?.on_time_delivery_rate > 0.95 && (
                                    <div className="text-center bg-green-50 rounded-lg px-4 py-2 border border-green-200">
                                        <div className="text-green-600 font-bold text-lg">STREAK</div>
                                        <div className="text-xs text-green-600">95%+ On-Time</div>
                                    </div>
                                )}
                            </>
                        )}
                        
                        <button 
                            onClick={fetchDispatchStats}
                            className="bg-gray-100 hover:bg-gray-200 rounded-lg px-3 py-2 transition-colors duration-200"
                            disabled={loading}
                        >
                            <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                            </svg>
                            <div className="text-xs text-blue-200">Refresh</div>
                        </button>
                    </div>
                </div>
            </div>
            
            {/* Main Dispatch Map View */}
            <div className="flex-1 relative">
                <DispatchMapView />
            </div>
        </div>
    );
};

export default DispatchPage;
