import React, { useState, useEffect } from 'react';
import LoadManager from './LoadManager';
import VehicleTracker from './VehicleTracker';
import EventConsole from './EventConsole';
import AnalyticsDashboard from './AnalyticsDashboard';
import './TMSDashboard.css';

const TMSDashboard = () => {
    const [activeTab, setActiveTab] = useState('loads');
    const [dashboardData, setDashboardData] = useState({
        totalLoads: 0,
        activeLoads: 0,
        totalVehicles: 0,
        activeVehicles: 0
    });

    const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

    useEffect(() => {
        fetchDashboardData();
        const interval = setInterval(fetchDashboardData, 30000); // Update every 30 seconds
        return () => clearInterval(interval);
    }, []);

    const fetchDashboardData = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/analytics/dashboard`);
            if (response.ok) {
                const data = await response.json();
                setDashboardData(data);
            }
        } catch (error) {
            console.error('Error fetching dashboard data:', error);
        }
    };

    const tabs = [
        { id: 'loads', label: 'Load Management', icon: '📦' },
        { id: 'vehicles', label: 'Vehicle Tracking', icon: '🚛' },
        { id: 'events', label: 'Event Console', icon: '⚡' },
        { id: 'analytics', label: 'Analytics', icon: '📊' }
    ];

    const renderTabContent = () => {
        switch (activeTab) {
            case 'loads':
                return <LoadManager apiBase={API_BASE} />;
            case 'vehicles':
                return <VehicleTracker apiBase={API_BASE} />;
            case 'events':
                return <EventConsole apiBase={API_BASE} />;
            case 'analytics':
                return <AnalyticsDashboard apiBase={API_BASE} />;
            default:
                return <LoadManager apiBase={API_BASE} />;
        }
    };

    return (
        <div className="tms-dashboard">
            {/* Dashboard Overview Cards */}
            <div className="dashboard-overview">
                <div className="overview-card">
                    <div className="card-icon">📦</div>
                    <div className="card-content">
                        <h3>Total Loads</h3>
                        <div className="card-value">{dashboardData.totalLoads}</div>
                    </div>
                </div>
                <div className="overview-card">
                    <div className="card-icon">🚀</div>
                    <div className="card-content">
                        <h3>Active Loads</h3>
                        <div className="card-value">{dashboardData.activeLoads}</div>
                    </div>
                </div>
                <div className="overview-card">
                    <div className="card-icon">🚛</div>
                    <div className="card-content">
                        <h3>Total Vehicles</h3>
                        <div className="card-value">{dashboardData.totalVehicles}</div>
                    </div>
                </div>
                <div className="overview-card">
                    <div className="card-icon">📡</div>
                    <div className="card-content">
                        <h3>System Status</h3>
                        <div className="card-value status-online">Online</div>
                    </div>
                </div>
            </div>

            {/* Navigation Tabs */}
            <div className="dashboard-tabs">
                {tabs.map(tab => (
                    <button
                        key={tab.id}
                        className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
                        onClick={() => setActiveTab(tab.id)}
                    >
                        <span className="tab-icon">{tab.icon}</span>
                        <span className="tab-label">{tab.label}</span>
                    </button>
                ))}
            </div>

            {/* Tab Content */}
            <div className="dashboard-content">
                {renderTabContent()}
            </div>
        </div>
    );
};

export default TMSDashboard;
