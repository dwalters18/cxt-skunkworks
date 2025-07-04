import React, { useState, useEffect } from 'react';
import LoadManager from './LoadManager';
import VehicleTracker from './VehicleTracker';
import EventConsole from './EventConsole';
import AnalyticsDashboard from './AnalyticsDashboard';


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
        <div className="p-6 bg-gray-50 min-h-screen font-sans">
            {/* Dashboard Overview Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
                <div className="bg-white p-6 rounded-lg shadow flex items-center space-x-4">
                    <div className="text-3xl text-gray-500">📦</div>
                    <div className="flex flex-col">
                        <h3 className="text-gray-600 text-sm font-medium mb-1">Total Loads</h3>
                        <div className="text-2xl font-bold text-gray-800">{dashboardData.totalLoads}</div>
                    </div>
                </div>
                <div className="bg-white p-6 rounded-lg shadow flex items-center space-x-4">
                    <div className="text-3xl text-gray-500">🚀</div>
                    <div className="flex flex-col">
                        <h3 className="text-gray-600 text-sm font-medium mb-1">Active Loads</h3>
                        <div className="text-2xl font-bold text-gray-800">{dashboardData.activeLoads}</div>
                    </div>
                </div>
                <div className="bg-white p-6 rounded-lg shadow flex items-center space-x-4">
                    <div className="text-3xl text-gray-500">🚛</div>
                    <div className="flex flex-col">
                        <h3 className="text-gray-600 text-sm font-medium mb-1">Total Vehicles</h3>
                        <div className="text-2xl font-bold text-gray-800">{dashboardData.totalVehicles}</div>
                    </div>
                </div>
                <div className="bg-white p-6 rounded-lg shadow flex items-center space-x-4">
                    <div className="text-3xl text-gray-500">📡</div>
                    <div className="flex flex-col">
                        <h3 className="text-gray-600 text-sm font-medium mb-1">System Status</h3>
                        <div className="text-green-500 font-bold">Online</div>
                    </div>
                </div>
            </div>

            {/* Navigation Tabs */}
            <div className="flex space-x-2 bg-white rounded-lg p-1 mb-6 shadow">
                {tabs.map(tab => (
                    <button
                        key={tab.id}
                        className={`${activeTab === tab.id ? 'bg-blue-500 text-white' : 'text-gray-700 hover:bg-gray-100'} flex items-center space-x-2 px-4 py-2 rounded cursor-pointer transition`}
                        onClick={() => setActiveTab(tab.id)}
                    >
                        <span className="text-xl">{tab.icon}</span>
                        <span className="font-medium">{tab.label}</span>
                    </button>
                ))}
            </div>

            {/* Tab Content */}
            <div className="bg-white p-6 rounded-lg shadow min-h-[600px]">
                {renderTabContent()}
            </div>
        </div>
    );
};

export default TMSDashboard;
