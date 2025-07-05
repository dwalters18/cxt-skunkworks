import React from 'react';

const LoadsPage = () => {
    return (
        <div className="p-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">📦 Load Management</h1>
                <p className="text-gray-600">Manage and track all transportation loads</p>
            </div>

            {/* Load Management Content */}
            <div className="bg-white rounded-xl shadow-lg p-6">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold text-gray-900">Active Loads</h2>
                    <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors duration-200">
                        + Add New Load
                    </button>
                </div>
                
                <div className="h-96 bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg flex items-center justify-center">
                    <div className="text-center text-gray-500">
                        <div className="text-6xl mb-4">📦</div>
                        <div className="text-xl font-semibold mb-2">Load Management Interface</div>
                        <div>Load listing and management features will be implemented here</div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default LoadsPage;
