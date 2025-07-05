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
            const dashboardResponse = await fetch(`${API_BASE}/api/dashboard`);
            if (!dashboardResponse.ok) throw new Error('Failed to fetch dashboard data');
            const dashboardData = await dashboardResponse.json();
            setDashboardData(dashboardData);
            
            // Fetch recent loads for activity feed
            const loadsResponse = await fetch(`${API_BASE}/api/loads?limit=5`);
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
        return `${Math.round(value * 100)}%`;
    };

    const getLoadStatusColor = (status) => {
        const colors = {
            'PENDING': 'bg-yellow-100 text-yellow-800',
            'ASSIGNED': 'bg-blue-100 text-blue-800',
            'IN_TRANSIT': 'bg-green-100 text-green-800',
            'DELIVERED': 'bg-gray-100 text-gray-800',
            'CANCELLED': 'bg-red-100 text-red-800'
        };
        return colors[status] || 'bg-gray-100 text-gray-800';
    };

    if (loading) {
        return (
            <div className="p-8">
                <div className="flex items-center justify-center h-64">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="p-8">
            <div className="mb-8">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900 mb-2">📊 Dashboard</h1>
                        <p className="text-gray-600">Overview of your transportation management system</p>
                    </div>
                    <button 
                        onClick={fetchDashboardData}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors duration-200"
                        disabled={loading}
                    >
                        🔄 Refresh
                    </button>
                </div>
            </div>

            {error && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
                    Error: {error}
                </div>
            )}

            {/* KPI Cards */}
            {dashboardData && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-blue-500">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold text-gray-700">Active Loads</h3>
                            <span className="text-2xl">📦</span>
                        </div>
                        <div className="text-3xl font-bold text-blue-600 mb-2">
                            {dashboardData.active_loads || dashboardData.total_loads - dashboardData.loads_delivered}
                        </div>
                        <div className="text-sm text-blue-600">
                            {dashboardData.loads_in_transit || 0} in transit
                        </div>
                    </div>

                    <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-green-500">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold text-gray-700">Fleet Utilization</h3>
                            <span className="text-2xl">🚛</span>
                        </div>
                        <div className="text-3xl font-bold text-green-600 mb-2">
                            {formatPercentage((dashboardData.active_vehicles / dashboardData.total_vehicles) || 0.85)}
                        </div>
                        <div className="text-sm text-green-600">
                            {dashboardData.active_vehicles} of {dashboardData.total_vehicles} active
                        </div>
                    </div>

                    <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-yellow-500">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold text-gray-700">Total Revenue</h3>
                            <span className="text-2xl">💰</span>
                        </div>
                        <div className="text-3xl font-bold text-yellow-600 mb-2">
                            {formatCurrency(dashboardData.total_revenue || 0)}
                        </div>
                        <div className="text-sm text-yellow-600">
                            from {dashboardData.loads_delivered || 0} deliveries
                        </div>
                    </div>

                    <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-purple-500">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold text-gray-700">Driver Utilization</h3>
                            <span className="text-2xl">👨‍💼</span>
                        </div>
                        <div className="text-3xl font-bold text-purple-600 mb-2">
                            {formatPercentage((dashboardData.active_drivers / dashboardData.total_drivers) || 0.78)}
                        </div>
                        <div className="text-sm text-purple-600">
                            {dashboardData.active_drivers} of {dashboardData.total_drivers} active
                        </div>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Quick Actions */}
                <div className="bg-white rounded-xl shadow-lg p-6">
                    <h2 className="text-xl font-bold text-gray-900 mb-4">🚀 Quick Actions</h2>
                    <div className="space-y-3">
                        <button 
                            onClick={() => navigate('/dispatch')}
                            className="w-full flex items-center gap-3 p-4 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors duration-200"
                        >
                            <span className="text-2xl">🎯</span>
                            <div className="text-left">
                                <div className="font-semibold text-blue-800">Start Dispatching</div>
                                <div className="text-sm text-blue-600">Go to command center</div>
                            </div>
                        </button>
                        
                        <button 
                            onClick={() => navigate('/loads')}
                            className="w-full flex items-center gap-3 p-4 bg-green-50 hover:bg-green-100 rounded-lg transition-colors duration-200"
                        >
                            <span className="text-2xl">📦</span>
                            <div className="text-left">
                                <div className="font-semibold text-green-800">Manage Loads</div>
                                <div className="text-sm text-green-600">View and manage shipments</div>
                            </div>
                        </button>
                        
                        <button 
                            onClick={() => navigate('/analytics')}
                            className="w-full flex items-center gap-3 p-4 bg-purple-50 hover:bg-purple-100 rounded-lg transition-colors duration-200"
                        >
                            <span className="text-2xl">📈</span>
                            <div className="text-left">
                                <div className="font-semibold text-purple-800">View Analytics</div>
                                <div className="text-sm text-purple-600">Performance insights</div>
                            </div>
                        </button>
                        
                        <button 
                            onClick={() => navigate('/fleet')}
                            className="w-full flex items-center gap-3 p-4 bg-orange-50 hover:bg-orange-100 rounded-lg transition-colors duration-200"
                        >
                            <span className="text-2xl">🚛</span>
                            <div className="text-left">
                                <div className="font-semibold text-orange-800">Fleet Management</div>
                                <div className="text-sm text-orange-600">Monitor vehicles and drivers</div>
                            </div>
                        </button>
                    </div>
                </div>

                {/* Recent Activity */}
                <div className="bg-white rounded-xl shadow-lg p-6">
                    <h2 className="text-xl font-bold text-gray-900 mb-4">📋 Recent Activity</h2>
                    <div className="space-y-3">
                        {recentLoads.length > 0 ? (
                            recentLoads.map((load) => (
                                <div key={load.load_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                    <div className="flex-1">
                                        <div className="font-medium text-gray-900">{load.load_number}</div>
                                        <div className="text-sm text-gray-600">
                                            {load.pickup_address?.split(',')[0]} → {load.delivery_address?.split(',')[0]}
                                        </div>
                                        <div className="text-xs text-gray-500 mt-1">
                                            {load.customer} • {formatCurrency(load.rate)}
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getLoadStatusColor(load.status)}`}>
                                            {load.status}
                                        </span>
                                        <div className="text-xs text-gray-500 mt-1">
                                            {new Date(load.created_at).toLocaleDateString()}
                                        </div>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="text-center py-8 text-gray-500">
                                <div className="text-4xl mb-2">📦</div>
                                <div>No recent activity</div>
                            </div>
                        )}
                    </div>
                    
                    {recentLoads.length > 0 && (
                        <div className="mt-4 text-center">
                            <button 
                                onClick={() => navigate('/loads')}
                                className="text-blue-600 hover:text-blue-800 text-sm font-medium"
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
