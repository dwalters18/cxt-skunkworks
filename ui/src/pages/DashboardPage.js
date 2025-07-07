import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const DashboardPage = () => {
    const [dashboardData, setDashboardData] = useState(null);
    const [recentLoads, setRecentLoads] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const navigate = useNavigate();

    const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

    const fetchDashboardData = async () => {
        try {
            setLoading(true);
            setError(null);
            
            // Fetch dashboard summary
            const dashboardResponse = await fetch(`${API_BASE}/api/analytics/dashboard`);
            if (!dashboardResponse.ok) throw new Error('Failed to fetch dashboard data');
            const dashboardData = await dashboardResponse.json();
            setDashboardData(dashboardData);
            
            // Fetch recent loads for activity feed
            const loadsResponse = await fetch(`${API_BASE}/api/loads?limit=50&offset=0`);
            if (loadsResponse.ok) {
                const loadsData = await loadsResponse.json();
                setRecentLoads(loadsData.loads || []);
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDashboardData();
        // Refresh data every 30 seconds
        const interval = setInterval(fetchDashboardData, 30000);
        return () => clearInterval(interval);
    }, []);

    const formatCurrency = (amount) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0
        }).format(amount);
    };

    const formatPercentage = (value) => {
        if (value == null || isNaN(value)) return '0%';
        return `${Math.round(value * 100)}%`;
    };

    const getLoadStatusColor = (status) => {
        const colors = {
            'PENDING': 'bg-yellow-100 text-yellow-800',
            'ASSIGNED': 'bg-blue-100 text-blue-800',
            'IN_TRANSIT': 'bg-green-100 text-green-800',
            'DELIVERED': 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200',
            'CANCELLED': 'bg-red-100 text-red-800'
        };
        return colors[status] || 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200';
    };

    if (loading) {
        return (
            <div className="space-y-6">
                <div className="flex items-center justify-center h-64">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-foreground">Dashboard</h1>
                    <p className="text-gray-600 dark:text-muted mt-1">Overview of your transportation management system</p>
                </div>
                <button 
                    onClick={fetchDashboardData}
                    className="bg-primary hover:bg-primary/80 text-background px-4 py-2 rounded-lg transition-colors duration-200 flex items-center gap-2"
                    disabled={loading}
                >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Refresh
                </button>
            </div>

            {error && (
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-600 text-red-800 dark:text-red-400 px-4 py-3 rounded-lg">
                    <div className="flex items-center gap-2">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Error: {error}
                    </div>
                </div>
            )}

            {/* KPI Cards */}
            {dashboardData && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-accent p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-sm font-medium text-gray-500 dark:text-muted">Active Loads</h3>
                            <div className="w-8 h-8 bg-blue-100 dark:bg-primary/10 rounded-lg flex items-center justify-center">
                                <svg className="w-5 h-5 text-blue-600 dark:text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                                </svg>
                            </div>
                        </div>
                        <div className="text-2xl font-bold text-gray-900 dark:text-foreground mb-1">
                            {dashboardData.active_loads || (dashboardData.total_loads || 0) - (dashboardData.loads_delivered || 0) || 0}
                        </div>
                        <div className="text-sm text-gray-600 dark:text-muted">
                            {dashboardData.loads_in_transit || 0} in transit
                        </div>
                    </div>

                    <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-accent p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-sm font-medium text-gray-500 dark:text-muted">Fleet Utilization</h3>
                            <div className="w-8 h-8 bg-green-100 dark:bg-primary/10 rounded-lg flex items-center justify-center">
                                <svg className="w-5 h-5 text-green-600 dark:text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </div>
                        </div>
                        <div className="text-2xl font-bold text-gray-900 dark:text-foreground mb-1">
                            {formatPercentage(
                                (dashboardData.total_vehicles && dashboardData.total_vehicles > 0) 
                                    ? (dashboardData.active_vehicles || 0) / dashboardData.total_vehicles 
                                    : 0.85
                            )}
                        </div>
                        <div className="text-sm text-gray-600 dark:text-muted">
                            {dashboardData.active_vehicles || 0} of {dashboardData.total_vehicles || 0} active
                        </div>
                    </div>

                    <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-accent p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-sm font-medium text-gray-500 dark:text-muted">Total Revenue</h3>
                            <div className="w-8 h-8 bg-yellow-100 dark:bg-primary/10 rounded-lg flex items-center justify-center">
                                <svg className="w-5 h-5 text-yellow-600 dark:text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                                </svg>
                            </div>
                        </div>
                        <div className="text-2xl font-bold text-gray-900 dark:text-foreground mb-1">
                            {formatCurrency(dashboardData.total_revenue || 0)}
                        </div>
                        <div className="text-sm text-gray-600 dark:text-muted">
                            from {dashboardData.loads_delivered || 0} deliveries
                        </div>
                    </div>

                    <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-accent p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-sm font-medium text-gray-500 dark:text-muted">Driver Utilization</h3>
                            <div className="w-8 h-8 bg-purple-100 dark:bg-primary/10 rounded-lg flex items-center justify-center">
                                <svg className="w-5 h-5 text-purple-600 dark:text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                </svg>
                            </div>
                        </div>
                        <div className="text-2xl font-bold text-gray-900 dark:text-foreground mb-1">
                            {formatPercentage(
                                (dashboardData.total_drivers && dashboardData.total_drivers > 0) 
                                    ? (dashboardData.active_drivers || 0) / dashboardData.total_drivers 
                                    : 0.78
                            )}
                        </div>
                        <div className="text-sm text-gray-600 dark:text-muted">
                            {dashboardData.active_drivers || 0} of {dashboardData.total_drivers || 0} active
                        </div>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Quick Actions */}
                <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-accent p-6">
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-foreground mb-4">Quick Actions</h2>
                    <div className="space-y-3">
                        <button 
                            onClick={() => navigate('/dispatch')}
                            className="w-full flex items-center gap-3 p-4 bg-blue-50 dark:bg-primary/10 hover:bg-blue-100 dark:hover:bg-primary/20 rounded-lg transition-colors duration-200"
                        >
                            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                                </svg>
                            </div>
                            <div className="text-left">
                                <div className="font-semibold text-gray-900 dark:text-foreground">Start Dispatching</div>
                                <div className="text-sm text-gray-600 dark:text-muted">Go to command center</div>
                            </div>
                        </button>
                        
                        <button 
                            onClick={() => navigate('/loads')}
                            className="w-full flex items-center gap-3 p-4 bg-green-50 dark:bg-primary/10 hover:bg-green-100 dark:hover:bg-primary/20 rounded-lg transition-colors duration-200"
                        >
                            <span className="text-2xl">📦</span>
                            <div className="text-left">
                                <div className="font-semibold text-green-800 dark:text-primary">Manage Loads</div>
                                <div className="text-sm text-green-600 dark:text-primary/80">View and manage shipments</div>
                            </div>
                        </button>
                        
                        <button 
                            onClick={() => navigate('/analytics')}
                            className="w-full flex items-center gap-3 p-4 bg-purple-50 dark:bg-primary/10 hover:bg-purple-100 dark:hover:bg-primary/20 rounded-lg transition-colors duration-200"
                        >
                            <span className="text-2xl">📈</span>
                            <div className="text-left">
                                <div className="font-semibold text-purple-800 dark:text-primary">View Analytics</div>
                                <div className="text-sm text-purple-600 dark:text-primary/80">Performance insights</div>
                            </div>
                        </button>
                        
                        <button 
                            onClick={() => navigate('/fleet')}
                            className="w-full flex items-center gap-3 p-4 bg-orange-50 dark:bg-primary/10 hover:bg-orange-100 dark:hover:bg-primary/20 rounded-lg transition-colors duration-200"
                        >
                            <span className="text-2xl">🚛</span>
                            <div className="text-left">
                                <div className="font-semibold text-orange-800 dark:text-primary">Fleet Management</div>
                                <div className="text-sm text-orange-600 dark:text-primary/80">Monitor vehicles and drivers</div>
                            </div>
                        </button>
                    </div>
                </div>

                {/* Recent Activity */}
                <div className="bg-white dark:bg-gray-900 rounded-xl shadow-lg border border-gray-200 dark:border-accent p-6">
                    <h2 className="text-xl font-bold text-gray-900 dark:text-foreground mb-4">📋 Recent Activity</h2>
                    <div className="space-y-3">
                        {recentLoads.length > 0 ? (
                            recentLoads.map((load) => (
                                <div key={load.load_id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                                    <div className="flex-1">
                                        <div className="font-medium text-gray-900 dark:text-foreground">{load.load_number}</div>
                                        <div className="text-sm text-gray-600 dark:text-muted">
                                            {load.pickup_address?.split(',')[0]} → {load.delivery_address?.split(',')[0]}
                                        </div>
                                        <div className="text-xs text-gray-500 dark:text-muted/80 mt-1">
                                            {load.customer} • {formatCurrency(load.rate)}
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getLoadStatusColor(load.status)}`}>
                                            {load.status}
                                        </span>
                                        <div className="text-xs text-gray-500 dark:text-muted/80 mt-1">
                                            {new Date(load.created_at).toLocaleDateString()}
                                        </div>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="text-center py-8 text-gray-500 dark:text-muted">
                                <div className="text-4xl mb-2">📦</div>
                                <div>No recent activity</div>
                            </div>
                        )}
                    </div>
                    
                    {recentLoads.length > 0 && (
                        <div className="mt-4 text-center">
                            <button 
                                onClick={() => navigate('/loads')}
                                className="text-primary hover:text-primary/80 text-sm font-medium"
                            >
                                View All Loads →
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default DashboardPage;
