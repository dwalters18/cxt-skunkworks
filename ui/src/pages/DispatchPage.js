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
        <div className="h-screen flex flex-col">
            {/* Gamified Header */}
            <div className="bg-gradient-to-r from-blue-900 to-blue-700 text-white px-8 py-4 shadow-lg">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className="text-3xl animate-bounce">🎯</div>
                        <div>
                            <h1 className="text-2xl font-bold">Dispatch Command Center</h1>
                            <p className="text-blue-200 text-sm">Your mission: Optimize routes and dispatch loads efficiently</p>
                        </div>
                    </div>
                    
                    {/* Gamification Stats */}
                    <div className="flex items-center gap-6">
                        {loading ? (
                            <div className="text-center bg-white/10 rounded-lg px-4 py-2">
                                <div className="animate-pulse bg-white/20 h-6 w-12 rounded mb-1"></div>
                                <div className="text-xs text-blue-200">Loading...</div>
                            </div>
                        ) : (
                            <>
                                <div className="text-center bg-white/10 rounded-lg px-4 py-2 hover:bg-white/20 transition-colors duration-200">
                                    <div className="text-yellow-400 font-bold text-lg">
                                        🏆 {gamificationScore}
                                    </div>
                                    <div className="text-xs text-blue-200">Efficiency Score</div>
                                </div>
                                <div className="text-center bg-white/10 rounded-lg px-4 py-2 hover:bg-white/20 transition-colors duration-200">
                                    <div className="text-green-400 font-bold text-lg">
                                        ⚡ {routesOptimized}
                                    </div>
                                    <div className="text-xs text-blue-200">Routes Today</div>
                                </div>
                                <div className="text-center bg-white/10 rounded-lg px-4 py-2 hover:bg-white/20 transition-colors duration-200">
                                    <div className="text-purple-400 font-bold text-lg">
                                        🚛 {activeLoads}
                                    </div>
                                    <div className="text-xs text-blue-200">Active Loads</div>
                                </div>
                                {performance?.on_time_delivery_rate > 0.95 && (
                                    <div className="text-center bg-green-500/20 rounded-lg px-4 py-2 border border-green-400">
                                        <div className="text-green-300 font-bold text-lg">🎆 STREAK</div>
                                        <div className="text-xs text-green-200">95%+ On-Time</div>
                                    </div>
                                )}
                            </>
                        )}
                        
                        <button 
                            onClick={fetchDispatchStats}
                            className="bg-white/10 hover:bg-white/20 rounded-lg px-3 py-2 transition-colors duration-200"
                            disabled={loading}
                        >
                            <div className="text-lg">🔄</div>
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
