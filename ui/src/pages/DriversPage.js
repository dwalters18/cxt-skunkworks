import React, { useState, useEffect } from 'react';

const DriversPage = () => {
    const [drivers, setDrivers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedDriver, setSelectedDriver] = useState(null);
    const [filterStatus, setFilterStatus] = useState('all');
    const [showAvailableOnly, setShowAvailableOnly] = useState(false);

    const fetchDrivers = async () => {
        try {
            setLoading(true);
            const params = new URLSearchParams();
            if (filterStatus !== 'all') {
                params.append('status', filterStatus.toUpperCase());
            }
            if (showAvailableOnly) {
                params.append('available_only', 'true');
            }
            
            const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/drivers?${params}`);
            if (!response.ok) throw new Error('Failed to fetch drivers');
            
            const data = await response.json();
            setDrivers(data.drivers || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const fetchDriverDetails = async (driverId) => {
        try {
            const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/drivers/${driverId}`);
            if (!response.ok) throw new Error('Failed to fetch driver details');
            
            const driver = await response.json();
            setSelectedDriver(driver);
        } catch (err) {
            console.error('Error fetching driver details:', err);
        }
    };

    useEffect(() => {
        fetchDrivers();
    }, [filterStatus, showAvailableOnly]);

    const getStatusColor = (status) => {
        const colors = {
            'AVAILABLE': 'bg-green-100 text-green-800',
            'ON_DUTY': 'bg-blue-100 text-blue-800',
            'OFF_DUTY': 'bg-gray-100 text-gray-800',
            'DRIVING': 'bg-yellow-100 text-yellow-800',
            'INACTIVE': 'bg-red-100 text-red-800'
        };
        return colors[status] || 'bg-gray-100 text-gray-800';
    };

    const formatLastUpdate = (timestamp) => {
        if (!timestamp) return 'Never';
        return new Date(timestamp).toLocaleString();
    };

    if (loading) {
        return (
            <div className="p-8">
                <div className="flex items-center justify-center h-64">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="p-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">👥 Driver Management</h1>
                <p className="text-gray-600">Manage your driver workforce and schedules</p>
            </div>

            {/* Filters */}
            <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-bold text-gray-900">Driver Filters</h2>
                    <button 
                        onClick={fetchDrivers}
                        className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors duration-200"
                    >
                        🔄 Refresh
                    </button>
                </div>
                
                <div className="flex flex-wrap gap-4">
                    <div className="flex items-center space-x-2">
                        <label className="text-sm font-medium text-gray-700">Status:</label>
                        <select 
                            value={filterStatus} 
                            onChange={(e) => setFilterStatus(e.target.value)}
                            className="border border-gray-300 rounded-md px-3 py-1 text-sm"
                        >
                            <option value="all">All Statuses</option>
                            <option value="available">Available</option>
                            <option value="on_duty">On Duty</option>
                            <option value="off_duty">Off Duty</option>
                            <option value="driving">Driving</option>
                            <option value="inactive">Inactive</option>
                        </select>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                        <input 
                            type="checkbox" 
                            id="availableOnly" 
                            checked={showAvailableOnly}
                            onChange={(e) => setShowAvailableOnly(e.target.checked)}
                            className="rounded border-gray-300"
                        />
                        <label htmlFor="availableOnly" className="text-sm font-medium text-gray-700">
                            Available Only
                        </label>
                    </div>
                </div>
            </div>

            {error && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
                    Error: {error}
                </div>
            )}

            {/* Drivers Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                {drivers.map((driver) => (
                    <div key={driver.driver_id} className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow duration-200">
                        <div className="flex items-start justify-between mb-4">
                            <div>
                                <h3 className="text-lg font-bold text-gray-900">{driver.name}</h3>
                                <p className="text-sm text-gray-600">{driver.carrier_name || 'Independent'}</p>
                            </div>
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(driver.status)}`}>
                                {driver.status}
                            </span>
                        </div>
                        
                        <div className="space-y-2 mb-4">
                            <div className="flex justify-between text-sm">
                                <span className="text-gray-600">License:</span>
                                <span className="font-medium">{driver.license_number}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-gray-600">Phone:</span>
                                <span className="font-medium">{driver.phone}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-gray-600">Active Loads:</span>
                                <span className="font-medium">{driver.active_loads}</span>
                            </div>
                        </div>
                        
                        {/* Hours of Service */}
                        <div className="mb-4">
                            <div className="text-sm text-gray-600 mb-1">Hours of Service</div>
                            <div className="flex justify-between text-xs">
                                <span>Driven: {driver.hours_driven_today.toFixed(1)}h</span>
                                <span>Remaining: {driver.hours_remaining_today.toFixed(1)}h</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                                <div 
                                    className="bg-blue-600 h-2 rounded-full" 
                                    style={{ width: `${(driver.hours_driven_today / 11) * 100}%` }}
                                ></div>
                            </div>
                        </div>
                        
                        {/* Location Info */}
                        {driver.current_location.latitude && (
                            <div className="text-xs text-gray-500 mb-4">
                                Location: {driver.current_location.latitude.toFixed(4)}, {driver.current_location.longitude.toFixed(4)}<br/>
                                Updated: {formatLastUpdate(driver.last_location_update)}
                            </div>
                        )}
                        
                        <button 
                            onClick={() => fetchDriverDetails(driver.driver_id)}
                            className="w-full bg-purple-600 hover:bg-purple-700 text-white py-2 px-4 rounded-lg transition-colors duration-200 text-sm"
                        >
                            View Details
                        </button>
                    </div>
                ))}
            </div>
            
            {drivers.length === 0 && !loading && (
                <div className="bg-white rounded-xl shadow-lg p-12 text-center">
                    <div className="text-6xl mb-4">👥</div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">No Drivers Found</h3>
                    <p className="text-gray-600">Try adjusting your filters or check back later.</p>
                </div>
            )}

            {/* Driver Details Modal */}
            {selectedDriver && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-96 overflow-y-auto">
                        <div className="p-6">
                            <div className="flex items-start justify-between mb-6">
                                <div>
                                    <h2 className="text-2xl font-bold text-gray-900">{selectedDriver.name}</h2>
                                    <p className="text-gray-600">{selectedDriver.carrier_name || 'Independent Driver'}</p>
                                </div>
                                <button 
                                    onClick={() => setSelectedDriver(null)}
                                    className="text-gray-400 hover:text-gray-600 text-2xl"
                                >
                                    ×
                                </button>
                            </div>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <h3 className="text-lg font-semibold mb-3">Contact Information</h3>
                                    <div className="space-y-2 text-sm">
                                        <div><strong>Email:</strong> {selectedDriver.email}</div>
                                        <div><strong>Phone:</strong> {selectedDriver.phone}</div>
                                        <div><strong>License:</strong> {selectedDriver.license_number}</div>
                                        <div><strong>Status:</strong> 
                                            <span className={`ml-2 px-2 py-1 rounded-full text-xs ${getStatusColor(selectedDriver.status)}`}>
                                                {selectedDriver.status}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                                
                                <div>
                                    <h3 className="text-lg font-semibold mb-3">Performance Metrics</h3>
                                    <div className="space-y-2 text-sm">
                                        <div><strong>Total Loads:</strong> {selectedDriver.performance.total_loads}</div>
                                        <div><strong>Completed:</strong> {selectedDriver.performance.completed_loads}</div>
                                        <div><strong>Completion Rate:</strong> {(selectedDriver.performance.completion_rate * 100).toFixed(1)}%</div>
                                        <div><strong>Avg Delivery Time:</strong> {selectedDriver.performance.avg_delivery_hours.toFixed(1)}h</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default DriversPage;
