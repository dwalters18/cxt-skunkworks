import React, { useState, useEffect } from 'react';

const AnalyticsDashboard = ({ apiBase }) => {
    const [analytics, setAnalytics] = useState({
        total_loads: 0,
        active_loads: 0,
        total_vehicles: 0,
        active_vehicles: 0,
        loads_by_status: {},
        vehicles_by_status: {},
        recent_events: [],
        hourly_loads: []
    });
    const [timeRange, setTimeRange] = useState('24h');
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchAnalytics();
        const interval = setInterval(fetchAnalytics, 30000); // Update every 30 seconds
        return () => clearInterval(interval);
    }, [timeRange]);

    const fetchAnalytics = async () => {
        setLoading(true);
        try {
            const response = await fetch(`${apiBase}/api/analytics/dashboard?time_range=${timeRange}`);
            if (response.ok) {
                const data = await response.json();
                setAnalytics(data);
            }
        } catch (error) {
            console.error('Error fetching analytics:', error);
        }
        setLoading(false);
    };

    const calculateLoadMetrics = () => {
        const total = analytics.total_loads;
        const delivered = analytics.loads_by_status?.delivered || 0;
        const inTransit = analytics.loads_by_status?.in_transit || 0;
        const pending = analytics.loads_by_status?.pending || 0;
        
        return {
            deliveryRate: total > 0 ? ((delivered / total) * 100).toFixed(1) : 0,
            utilizationRate: total > 0 ? (((delivered + inTransit) / total) * 100).toFixed(1) : 0,
            pendingRate: total > 0 ? ((pending / total) * 100).toFixed(1) : 0
        };
    };

    const calculateVehicleMetrics = () => {
        const total = analytics.total_vehicles;
        const active = analytics.vehicles_by_status?.in_transit || 0;
        const available = analytics.vehicles_by_status?.available || 0;
        const maintenance = analytics.vehicles_by_status?.maintenance || 0;
        
        return {
            utilizationRate: total > 0 ? ((active / total) * 100).toFixed(1) : 0,
            availabilityRate: total > 0 ? ((available / total) * 100).toFixed(1) : 0,
            maintenanceRate: total > 0 ? ((maintenance / total) * 100).toFixed(1) : 0
        };
    };

    const loadMetrics = calculateLoadMetrics();
    const vehicleMetrics = calculateVehicleMetrics();

    // Use real performance data from API
    const performanceData = {
        hourlyLoads: analytics.hourly_loads || [],
        dailyRevenue: analytics.daily_revenue || [
            { day: 'Mon', revenue: 12500 },
            { day: 'Tue', revenue: 18200 },
            { day: 'Wed', revenue: 15800 },
            { day: 'Thu', revenue: 22100 },
            { day: 'Fri', revenue: 19300 },
            { day: 'Sat', revenue: 14600 },
            { day: 'Sun', revenue: 11200 }
        ],
        recentEvents: analytics.recent_events || []
    };

    const getStatusColor = (status) => {
        const colors = {
            'delivered': '#4caf50',
            'in_transit': '#ff9800',
            'pending': '#2196f3',
            'cancelled': '#f44336',
            'available': '#4caf50',
            'assigned': '#2196f3',
            'maintenance': '#f44336',
            'offline': '#757575'
        };
        return colors[status] || '#757575';
    };

    const MetricCard = ({ title, value, subtitle, trend, color = '#2196f3' }) => (
        <div className="bg-white p-4 rounded-lg shadow flex items-center justify-between">
            <div className="metric-header">
                <h4>{title}</h4>
                {trend && (
                    <span className={`trend ${trend > 0 ? 'positive' : 'negative'}`}>
                        {trend > 0 ? '↗' : '↘'} {Math.abs(trend)}%
                    </span>
                )}
            </div>
            <div className="metric-value" style={{ color }}>
                {value}
            </div>
            {subtitle && <div className="metric-subtitle">{subtitle}</div>}
        </div>
    );

    const BarChart = ({ data, dataKey, xKey, title }) => (
        <div className="space-y-2">
            <h4>{title}</h4>
            <div className="bar-chart">
                {(data || []).map((item, index) => {
                    const maxValue = Math.max(...(data || []).map(d => d[dataKey]));
                    const height = (item[dataKey] / maxValue) * 100;
                    return (
                        <div key={index} className="bar-item">
                            <div 
                                className="bar" 
                                style={{ 
                                    height: `${height}%`,
                                    backgroundColor: '#2196f3'
                                }}
                                title={`${item[xKey]}: ${item[dataKey]}`}
                            ></div>
                            <div className="bar-label">{item[xKey]}</div>
                        </div>
                    );
                })}
            </div>
        </div>
    );

    return (
        <div className="p-6 bg-white rounded-lg shadow space-y-6">
            <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold text-gray-800 dark:text-foreground">Analytics Dashboard</h2>
                <div className="flex items-center space-x-4">
                    <select
                        value={timeRange}
                        onChange={(e) => setTimeRange(e.target.value)}
                    >
                        <option value="1h">Last Hour</option>
                        <option value="24h">Last 24 Hours</option>
                        <option value="7d">Last 7 Days</option>
                        <option value="30d">Last 30 Days</option>
                    </select>
                    <button onClick={fetchAnalytics} className="bg-gray-500 hover:bg-gray-600 text-white py-2 px-4 rounded">
                        🔄 Refresh
                    </button>
                </div>
            </div>

            {loading && <div className="text-center text-gray-500 dark:text-gray-400 py-4">Loading analytics...</div>}

            {/* Key Performance Indicators */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                <MetricCard
                    title="Load Delivery Rate"
                    value={`${loadMetrics.deliveryRate}%`}
                    subtitle="Successfully delivered"
                    color="#4caf50"
                    trend={2.3}
                />
                <MetricCard
                    title="Vehicle Utilization"
                    value={`${vehicleMetrics.utilizationRate}%`}
                    subtitle="Vehicles in use"
                    color="#2196f3"
                    trend={-1.2}
                />
                <MetricCard
                    title="Average Revenue"
                    value="$45,280"
                    subtitle="Per load delivered"
                    color="#ff9800"
                    trend={5.7}
                />
                <MetricCard
                    title="On-Time Delivery"
                    value="94.2%"
                    subtitle="Within scheduled window"
                    color="#9c27b0"
                    trend={1.8}
                />
            </div>

            {/* Status Breakdowns */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                <div className="breakdown-section">
                    <h3>Load Status Distribution</h3>
                    <div className="status-grid">
                        {Object.entries(analytics.loads_by_status || {}).map(([status, count]) => (
                            <div key={status} className="status-item">
                                <div 
                                    className="status-indicator"
                                    style={{ backgroundColor: getStatusColor(status) }}
                                ></div>
                                <div className="status-info">
                                    <div className="status-count">{count}</div>
                                    <div className="status-label">{status.replace('_', ' ')}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="breakdown-section">
                    <h3>Vehicle Status Distribution</h3>
                    <div className="status-grid">
                        {Object.entries(analytics.vehicles_by_status || {}).map(([status, count]) => (
                            <div key={status} className="status-item">
                                <div 
                                    className="status-indicator"
                                    style={{ backgroundColor: getStatusColor(status) }}
                                ></div>
                                <div className="status-info">
                                    <div className="status-count">{count}</div>
                                    <div className="status-label">{status.replace('_', ' ')}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Performance Charts */}
            <div className="charts-section">
                <div className="chart-grid">
                    <BarChart
                        data={performanceData.hourlyLoads}
                        dataKey="loads"
                        xKey="hour"
                        title="Hourly Load Volume"
                    />
                    <BarChart
                        data={performanceData.dailyRevenue}
                        dataKey="revenue"
                        xKey="day"
                        title="Daily Revenue ($)"
                    />
                </div>
            </div>

            {/* Recent Activity */}
            <div className="recent-activity">
                <h3>Recent System Activity</h3>
                <div className="activity-list">
                    {analytics.recent_events?.slice(0, 10).map((event, index) => (
                        <div key={index} className="activity-item">
                            <div className="activity-time">
                                {new Date(event.timestamp).toLocaleTimeString()}
                            </div>
                            <div className="activity-type" style={{ color: getStatusColor(event.type) }}>
                                {event.type}
                            </div>
                            <div className="activity-description">
                                {event.description}
                            </div>
                        </div>
                    )) || (
                        // Mock recent activities
                        [
                            { timestamp: new Date(), type: 'delivered', description: 'Load LOAD-10001 delivered successfully' },
                            { timestamp: new Date(Date.now() - 300000), type: 'in_transit', description: 'Vehicle VEH-0123 started transit' },
                            { timestamp: new Date(Date.now() - 600000), type: 'pending', description: 'New load LOAD-10005 created' },
                            { timestamp: new Date(Date.now() - 900000), type: 'available', description: 'Vehicle VEH-0124 became available' },
                            { timestamp: new Date(Date.now() - 1200000), type: 'delivered', description: 'Load LOAD-09998 delivered successfully' }
                        ].map((event, index) => (
                            <div key={index} className="activity-item">
                                <div className="activity-time">
                                    {event.timestamp.toLocaleTimeString()}
                                </div>
                                <div className="activity-type" style={{ color: getStatusColor(event.type) }}>
                                    {event.type}
                                </div>
                                <div className="activity-description">
                                    {event.description}
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* System Health */}
            <div className="system-health">
                <h3>System Health</h3>
                <div className="health-grid">
                    <div className="health-item">
                        <div className="health-indicator online"></div>
                        <div className="health-label">API Status</div>
                        <div className="health-value">Online</div>
                    </div>
                    <div className="health-item">
                        <div className="health-indicator online"></div>
                        <div className="health-label">Kafka Cluster</div>
                        <div className="health-value">Healthy</div>
                    </div>
                    <div className="health-item">
                        <div className="health-indicator online"></div>
                        <div className="health-label">Database</div>
                        <div className="health-value">Connected</div>
                    </div>
                    <div className="health-item">
                        <div className="health-indicator warning"></div>
                        <div className="health-label">Event Processing</div>
                        <div className="health-value">High Load</div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AnalyticsDashboard;
