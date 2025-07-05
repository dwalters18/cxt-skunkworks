import React from 'react';

const DashboardPage = () => {
    return (
        <div className="p-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">📊 Dashboard</h1>
                <p className="text-gray-600">Overview of your transportation management system</p>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-blue-500">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold text-gray-700">Active Loads</h3>
                        <span className="text-2xl">📦</span>
                    </div>
                    <div className="text-3xl font-bold text-blue-600 mb-2">24</div>
                    <div className="text-sm text-green-600">↗ +12% from yesterday</div>
                </div>

                <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-green-500">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold text-gray-700">Fleet Utilization</h3>
                        <span className="text-2xl">🚛</span>
                    </div>
                    <div className="text-3xl font-bold text-green-600 mb-2">87%</div>
                    <div className="text-sm text-green-600">↗ +5% efficiency</div>
                </div>

                <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-yellow-500">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold text-gray-700">Revenue Today</h3>
                        <span className="text-2xl">💰</span>
                    </div>
                    <div className="text-3xl font-bold text-yellow-600 mb-2">$18.2K</div>
                    <div className="text-sm text-green-600">↗ +8% vs target</div>
                </div>

                <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-purple-500">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold text-gray-700">On-Time Delivery</h3>
                        <span className="text-2xl">⏰</span>
                    </div>
                    <div className="text-3xl font-bold text-purple-600 mb-2">94%</div>
                    <div className="text-sm text-green-600">↗ +2% improvement</div>
                </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
                <h2 className="text-xl font-bold text-gray-900 mb-4">🚀 Quick Actions</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <button className="flex items-center gap-3 p-4 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors duration-200">
                        <span className="text-2xl">🎯</span>
                        <div className="text-left">
                            <div className="font-semibold text-blue-800">Start Dispatching</div>
                            <div className="text-sm text-blue-600">Go to command center</div>
                        </div>
                    </button>
                    
                    <button className="flex items-center gap-3 p-4 bg-green-50 hover:bg-green-100 rounded-lg transition-colors duration-200">
                        <span className="text-2xl">📦</span>
                        <div className="text-left">
                            <div className="font-semibold text-green-800">Add New Load</div>
                            <div className="text-sm text-green-600">Create load request</div>
                        </div>
                    </button>
                    
                    <button className="flex items-center gap-3 p-4 bg-purple-50 hover:bg-purple-100 rounded-lg transition-colors duration-200">
                        <span className="text-2xl">📈</span>
                        <div className="text-left">
                            <div className="font-semibold text-purple-800">View Analytics</div>
                            <div className="text-sm text-purple-600">Performance insights</div>
                        </div>
                    </button>
                </div>
            </div>
        </div>
    );
};

export default DashboardPage;
