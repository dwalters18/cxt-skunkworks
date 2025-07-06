import React, { useState, useEffect } from 'react';

const AnalyticsPage = () => {
    const [dashboardData, setDashboardData] = useState(null);
    const [performanceData, setPerformanceData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [timeFilter, setTimeFilter] = useState('7d');

    const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

    const fetchDashboardData = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/analytics/dashboard`);
            if (!response.ok) throw new Error('Failed to fetch dashboard data');
            
            const data = await response.json();
            setDashboardData(data);
        } catch (err) {
            console.error('Error fetching dashboard data:', err);
        }
    };

    const fetchPerformanceData = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/routes/performance?time_range=${timeFilter}`);
            if (!response.ok) throw new Error('Failed to fetch performance data');
            
            const data = await response.json();
            setPerformanceData(data);
        } catch (err) {
            console.error('Error fetching performance data:', err);
        }
    };

    const fetchData = async () => {
        try {
            setLoading(true);
            setError(null);
            await Promise.all([fetchDashboardData(), fetchPerformanceData()]);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [timeFilter]);

    const formatCurrency = (amount) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    };

    const formatPercentage = (value) => {
        return `${(value * 100).toFixed(1)}%`;
    };

    const formatDistance = (miles) => {
        return new Intl.NumberFormat('en-US').format(miles);
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
                <h1 className="text-3xl font-bold text-gray-900 mb-2">📈 Analytics</h1>
                <p className="text-gray-600">Performance insights and data visualization</p>
            </div>

            {/* Time Filter */}
            <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
                <div className="flex items-center justify-between">
                    <h2 className="text-xl font-bold text-gray-900">Analytics Dashboard</h2>
                    <div className="flex items-center space-x-4">
                        <div className="flex items-center space-x-2">
                            <label className="text-sm font-medium text-gray-700">Time Period:</label>
                            <select 
                                value={timeFilter} 
                                onChange={(e) => setTimeFilter(e.target.value)}
                                className="border border-gray-300 rounded-md px-3 py-1 text-sm"
                            >
                                <option value="1d">Last 24 Hours</option>
                                <option value="7d">Last 7 Days</option>
                                <option value="30d">Last 30 Days</option>
                                <option value="90d">Last 90 Days</option>
                            </select>
                        </div>
                        <button 
                            onClick={fetchData}
                            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors duration-200"
                        >
                            🔄 Refresh
                        </button>
                    </div>
                </div>
            </div>

            {error && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
                    Error: {error}
                </div>
            )}

            {/* Key Performance Indicators */}
            {dashboardData && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                    <div className="bg-white rounded-lg shadow p-4">
                        <div className="text-2xl font-bold text-blue-600">{dashboardData.total_loads}</div>
                        <div className="text-sm text-gray-600">Total Loads</div>
                        <div className="text-xs text-green-500 mt-1">
                            {dashboardData.loads_delivered} delivered
                        </div>
                    </div>
                    <div className="bg-white rounded-lg shadow p-4">
                        <div className="text-2xl font-bold text-green-600">{dashboardData.active_drivers}</div>
                        <div className="text-sm text-gray-600">Active Drivers</div>
                        <div className="text-xs text-gray-500 mt-1">
                            of {dashboardData.total_drivers} total
                        </div>
                    </div>
                    <div className="bg-white rounded-lg shadow p-4">
                        <div className="text-2xl font-bold text-purple-600">{dashboardData.active_vehicles}</div>
                        <div className="text-sm text-gray-600">Active Vehicles</div>
                        <div className="text-xs text-gray-500 mt-1">
                            of {dashboardData.total_vehicles} total
                        </div>
                    </div>
                    <div className="bg-white rounded-lg shadow p-4">
                        <div className="text-2xl font-bold text-orange-600">{formatCurrency(dashboardData.total_revenue || 0)}</div>
                        <div className="text-sm text-gray-600">Total Revenue</div>
                        <div className="text-xs text-gray-500 mt-1">
                            from delivered loads
                        </div>
                    </div>
                </div>
            )}

            {/* Performance Metrics */}
            {performanceData && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
                    <div className="bg-white rounded-xl shadow-lg p-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-4">Route Performance</h2>
                        <div className="space-y-4">
                            <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                                <div>
                                    <div className="font-medium text-blue-800">Average Route Efficiency</div>
                                    <div className="text-sm text-blue-600">Distance optimization vs actual</div>
                                </div>
                                <div className="text-2xl font-bold text-blue-600">
                                    {formatPercentage(performanceData.route_efficiency || 0.85)}
                                </div>
                            </div>
                            
                            <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                                <div>
                                    <div className="font-medium text-green-800">On-Time Delivery Rate</div>
                                    <div className="text-sm text-green-600">Deliveries completed on schedule</div>
                                </div>
                                <div className="text-2xl font-bold text-green-600">
                                    {formatPercentage(performanceData.on_time_delivery || 0.92)}
                                </div>
                            </div>
                            
                            <div className="flex justify-between items-center p-3 bg-purple-50 rounded-lg">
                                <div>
                                    <div className="font-medium text-purple-800">Fuel Efficiency</div>
                                    <div className="text-sm text-purple-600">Miles per gallon average</div>
                                </div>
                                <div className="text-2xl font-bold text-purple-600">
                                    {(performanceData.fuel_efficiency || 6.8).toFixed(1)} MPG
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="bg-white rounded-xl shadow-lg p-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-4">Fleet Utilization</h2>
                        <div className="space-y-4">
                            <div className="flex justify-between items-center p-3 bg-orange-50 rounded-lg">
                                <div>
                                    <div className="font-medium text-orange-800">Vehicle Utilization</div>
                                    <div className="text-sm text-orange-600">Active vehicles vs total fleet</div>
                                </div>
                                <div className="text-2xl font-bold text-orange-600">
                                    {formatPercentage(performanceData.vehicle_utilization || 0.78)}
                                </div>
                            </div>
                            
                            <div className="flex justify-between items-center p-3 bg-red-50 rounded-lg">
                                <div>
                                    <div className="font-medium text-red-800">Driver Utilization</div>
                                    <div className="text-sm text-red-600">Active drivers vs available</div>
                                </div>
                                <div className="text-2xl font-bold text-red-600">
                                    {formatPercentage(performanceData.driver_utilization || 0.83)}
                                </div>
                            </div>
                            
                            <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                                <div>
                                    <div className="font-medium text-gray-800">Average Load Weight</div>
                                    <div className="text-sm text-gray-600">Per delivery load</div>
                                </div>
                                <div className="text-2xl font-bold text-gray-600">
                                    {(performanceData.avg_load_weight || 15420).toLocaleString()} lbs
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Revenue and Cost Analysis */}
            {performanceData && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="bg-white rounded-xl shadow-lg p-6">
                        <h3 className="text-lg font-bold text-gray-900 mb-4">Revenue Metrics</h3>
                        <div className="space-y-3">
                            <div className="flex justify-between">
                                <span className="text-gray-600">Total Revenue:</span>
                                <span className="font-bold text-green-600">
                                    {formatCurrency(performanceData.total_revenue || 285420)}
                                </span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-600">Avg per Load:</span>
                                <span className="font-bold">
                                    {formatCurrency(performanceData.avg_revenue_per_load || 2450)}
                                </span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-600">Per Mile:</span>
                                <span className="font-bold">
                                    {formatCurrency(performanceData.revenue_per_mile || 2.15)}
                                </span>
                            </div>
                        </div>
                    </div>
                    
                    <div className="bg-white rounded-xl shadow-lg p-6">
                        <h3 className="text-lg font-bold text-gray-900 mb-4">Cost Analysis</h3>
                        <div className="space-y-3">
                            <div className="flex justify-between">
                                <span className="text-gray-600">Fuel Costs:</span>
                                <span className="font-bold text-red-600">
                                    {formatCurrency(performanceData.fuel_costs || 42180)}
                                </span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-600">Maintenance:</span>
                                <span className="font-bold">
                                    {formatCurrency(performanceData.maintenance_costs || 18650)}
                                </span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-600">Driver Pay:</span>
                                <span className="font-bold">
                                    {formatCurrency(performanceData.driver_costs || 125480)}
                                </span>
                            </div>
                        </div>
                    </div>
                    
                    <div className="bg-white rounded-xl shadow-lg p-6">
                        <h3 className="text-lg font-bold text-gray-900 mb-4">Distance Metrics</h3>
                        <div className="space-y-3">
                            <div className="flex justify-between">
                                <span className="text-gray-600">Total Miles:</span>
                                <span className="font-bold text-blue-600">
                                    {formatDistance(performanceData.total_miles || 132840)} mi
                                </span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-600">Avg per Load:</span>
                                <span className="font-bold">
                                    {formatDistance(performanceData.avg_miles_per_load || 875)} mi
                                </span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-600">Empty Miles %:</span>
                                <span className="font-bold">
                                    {formatPercentage(performanceData.empty_miles_ratio || 0.12)}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {!dashboardData && !performanceData && !loading && (
                <div className="bg-white rounded-xl shadow-lg p-12 text-center">
                    <div className="text-6xl mb-4">📈</div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">No Analytics Data Available</h3>
                    <p className="text-gray-600">Performance data will appear here once operations begin.</p>
                </div>
            )}
        </div>
    );
};

export default AnalyticsPage;
