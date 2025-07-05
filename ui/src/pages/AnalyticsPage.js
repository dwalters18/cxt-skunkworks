import React from 'react';

const AnalyticsPage = () => {
    return (
        <div className="p-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">📈 Analytics</h1>
                <p className="text-gray-600">Performance insights and data visualization</p>
            </div>

            {/* Analytics Content Placeholder */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="bg-white rounded-xl shadow-lg p-6">
                    <h2 className="text-xl font-bold text-gray-900 mb-4">Route Efficiency Trends</h2>
                    <div className="h-64 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg flex items-center justify-center">
                        <div className="text-center text-gray-500">
                            <div className="text-4xl mb-2">📊</div>
                            <div>Chart visualization will go here</div>
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-xl shadow-lg p-6">
                    <h2 className="text-xl font-bold text-gray-900 mb-4">Fleet Performance</h2>
                    <div className="h-64 bg-gradient-to-br from-green-50 to-green-100 rounded-lg flex items-center justify-center">
                        <div className="text-center text-gray-500">
                            <div className="text-4xl mb-2">🚛</div>
                            <div>Performance metrics will go here</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AnalyticsPage;
