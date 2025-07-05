import React from 'react';

const DriversPage = () => {
    return (
        <div className="p-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">👥 Driver Management</h1>
                <p className="text-gray-600">Manage your driver workforce and schedules</p>
            </div>

            <div className="bg-white rounded-xl shadow-lg p-6">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold text-gray-900">Active Drivers</h2>
                    <button className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors duration-200">
                        + Add Driver
                    </button>
                </div>
                
                <div className="h-96 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg flex items-center justify-center">
                    <div className="text-center text-gray-500">
                        <div className="text-6xl mb-4">👥</div>
                        <div className="text-xl font-semibold mb-2">Driver Management Interface</div>
                        <div>Driver profiles, schedules, and performance tracking will be implemented here</div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DriversPage;
