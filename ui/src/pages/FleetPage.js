import React, { useState, useEffect } from 'react';

const FleetPage = () => {
    const [vehicles, setVehicles] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedVehicle, setSelectedVehicle] = useState(null);
    const [statusFilter, setStatusFilter] = useState('all');
    const [vehicleCounts, setVehicleCounts] = useState({
        total: 0,
        active: 0,
        inactive: 0,
        maintenance: 0,
        out_of_service: 0
    });
    const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

    const fetchVehicles = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${API_BASE}/api/vehicles`);
            if (!response.ok) throw new Error('Failed to fetch vehicles');
            
            const data = await response.json();
            let filteredVehicles = data.vehicles || [];
            
            // Apply status filter
            if (statusFilter !== 'all') {
                filteredVehicles = filteredVehicles.filter(vehicle => 
                    vehicle.status.toLowerCase() === statusFilter.toLowerCase()
                );
            }
            
            setVehicles(filteredVehicles);
            
            // Calculate counts from all vehicles
            const allVehicles = data.vehicles || [];
            const statusCounts = allVehicles.reduce((acc, vehicle) => {
                acc[vehicle.status.toLowerCase()] = (acc[vehicle.status.toLowerCase()] || 0) + 1;
                return acc;
            }, {});
            
            setVehicleCounts({
                total: allVehicles.length,
                active: statusCounts.active || 0,
                inactive: statusCounts.inactive || 0,
                maintenance: statusCounts.maintenance || 0,
                out_of_service: statusCounts.out_of_service || 0
            });
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const fetchVehicleDetails = async (vehicleId) => {
        try {
            const response = await fetch(`${API_BASE}/api/vehicles/${vehicleId}`);
            if (!response.ok) throw new Error('Failed to fetch vehicle details');
            
            const vehicle = await response.json();
            setSelectedVehicle(vehicle);
        } catch (err) {
            console.error('Error fetching vehicle details:', err);
        }
    };

    const updateVehicleStatus = async (vehicleId, newStatus) => {
        try {
            const response = await fetch(`${API_BASE}/api/vehicles/${vehicleId}/status`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: newStatus })
            });
            
            if (!response.ok) throw new Error('Failed to update vehicle status');
            await fetchVehicles(); // Refresh the vehicles
        } catch (err) {
            alert(`Error updating vehicle status: ${err.message}`);
        }
    };

    useEffect(() => {
        fetchVehicles();
    }, [statusFilter]);

    const getStatusColor = (status) => {
        const colors = {
            'ACTIVE': 'bg-green-100 text-green-800',
            'INACTIVE': 'bg-gray-100 text-gray-800',
            'MAINTENANCE': 'bg-yellow-100 text-yellow-800',
            'OUT_OF_SERVICE': 'bg-red-100 text-red-800'
        };
        return colors[status] || 'bg-gray-100 text-gray-800';
    };

    const formatLastUpdate = (timestamp) => {
        if (!timestamp) return 'Never';
        return new Date(timestamp).toLocaleString();
    };

    const formatMileage = (mileage) => {
        return new Intl.NumberFormat('en-US').format(mileage);
    };

    if (loading) {
        return (
            <div className="p-8">
                <div className="flex items-center justify-center h-64">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-gray-900">Fleet</h1>
                <p className="text-gray-600 mt-1">Monitor and manage your vehicle fleet</p>
            </div>

            {/* Fleet Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
                <div className="bg-white rounded-lg shadow p-4">
                    <div className="text-2xl font-bold text-gray-900">{vehicleCounts.total}</div>
                    <div className="text-sm text-gray-600">Total Vehicles</div>
                </div>
                <div className="bg-white rounded-lg shadow p-4">
                    <div className="text-2xl font-bold text-green-600">{vehicleCounts.active}</div>
                    <div className="text-sm text-gray-600">Active</div>
                </div>
                <div className="bg-white rounded-lg shadow p-4">
                    <div className="text-2xl font-bold text-gray-600">{vehicleCounts.inactive}</div>
                    <div className="text-sm text-gray-600">Inactive</div>
                </div>
                <div className="bg-white rounded-lg shadow p-4">
                    <div className="text-2xl font-bold text-yellow-600">{vehicleCounts.maintenance}</div>
                    <div className="text-sm text-gray-600">Maintenance</div>
                </div>
                <div className="bg-white rounded-lg shadow p-4">
                    <div className="text-2xl font-bold text-red-600">{vehicleCounts.out_of_service}</div>
                    <div className="text-sm text-gray-600">Out of Service</div>
                </div>
            </div>

            {/* Filters */}
            <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-bold text-gray-900">Fleet Filters</h2>
                    <button 
                        onClick={fetchVehicles}
                        className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors duration-200"
                    >
                        🔄 Refresh
                    </button>
                </div>
                
                <div className="flex flex-wrap gap-4">
                    <div className="flex items-center space-x-2">
                        <label className="text-sm font-medium text-gray-700">Status:</label>
                        <select 
                            value={statusFilter} 
                            onChange={(e) => setStatusFilter(e.target.value)}
                            className="border border-gray-300 rounded-md px-3 py-1 text-sm"
                        >
                            <option value="all">All Statuses</option>
                            <option value="active">Active</option>
                            <option value="inactive">Inactive</option>
                            <option value="maintenance">Maintenance</option>
                            <option value="out_of_service">Out of Service</option>
                        </select>
                    </div>
                </div>
            </div>

            {error && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
                    Error: {error}
                </div>
            )}

            {/* Vehicles Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                {vehicles.map((vehicle, index) => (
                    <div key={vehicle.vehicle_id || `vehicle-${index}`} className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow duration-200">
                        <div className="flex items-start justify-between mb-4">
                            <div>
                                <h3 className="text-lg font-bold text-gray-900">{vehicle.vehicle_number}</h3>
                                <p className="text-sm text-gray-600">{vehicle.make} {vehicle.model} ({vehicle.year})</p>
                            </div>
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(vehicle.status)}`}>
                                {vehicle.status}
                            </span>
                        </div>
                        
                        <div className="space-y-2 mb-4">
                            <div className="flex justify-between text-sm">
                                <span className="text-gray-600">VIN:</span>
                                <span className="font-medium text-xs">{vehicle.vin}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-gray-600">License:</span>
                                <span className="font-medium">{vehicle.license_plate}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-gray-600">Mileage:</span>
                                <span className="font-medium">{formatMileage(vehicle.mileage)} mi</span>
                            </div>
                        </div>
                        
                        {/* Location Info */}
                        {vehicle.current_location && vehicle.current_location.latitude && (
                            <div className="mb-4 p-2 bg-blue-50 rounded-lg">
                                <div className="text-sm font-medium text-blue-800">Current Location:</div>
                                <div className="text-xs text-blue-600">
                                    {vehicle.current_location.latitude.toFixed(4)}, {vehicle.current_location.longitude.toFixed(4)}
                                </div>
                                <div className="text-xs text-blue-500">
                                    Updated: {formatLastUpdate(vehicle.last_location_update)}
                                </div>
                            </div>
                        )}
                        
                        {/* Maintenance Info */}
                        {vehicle.next_maintenance_date && (
                            <div className="mb-4 p-2 bg-yellow-50 rounded-lg">
                                <div className="text-sm font-medium text-yellow-800">Next Maintenance:</div>
                                <div className="text-xs text-yellow-600">
                                    {new Date(vehicle.next_maintenance_date).toLocaleDateString()}
                                </div>
                            </div>
                        )}
                        
                        <div className="flex space-x-2">
                            <button 
                                onClick={() => fetchVehicleDetails(vehicle.vehicle_id)}
                                className="flex-1 bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded-lg transition-colors duration-200 text-sm"
                            >
                                View Details
                            </button>
                            <div className="relative">
                                <select 
                                    onChange={(e) => {
                                        if (e.target.value) {
                                            updateVehicleStatus(vehicle.vehicle_id, e.target.value);
                                            e.target.value = ''; // Reset select
                                        }
                                    }}
                                    className="bg-gray-100 hover:bg-gray-200 text-gray-800 py-2 px-3 rounded-lg text-sm cursor-pointer"
                                >
                                    <option value="">Update Status</option>
                                    <option value="ACTIVE">Active</option>
                                    <option value="INACTIVE">Inactive</option>
                                    <option value="MAINTENANCE">Maintenance</option>
                                    <option value="OUT_OF_SERVICE">Out of Service</option>
                                </select>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
            
            {vehicles.length === 0 && !loading && (
                <div className="bg-white rounded-xl shadow-lg p-12 text-center">
                    <div className="text-6xl mb-4">🚛</div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">No Vehicles Found</h3>
                    <p className="text-gray-600">Try adjusting your filters or check back later.</p>
                </div>
            )}

            {/* Vehicle Details Modal */}
            {selectedVehicle && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-xl shadow-xl max-w-4xl w-full max-h-96 overflow-y-auto">
                        <div className="p-6">
                            <div className="flex items-start justify-between mb-6">
                                <div>
                                    <h2 className="text-2xl font-bold text-gray-900">{selectedVehicle.vehicle_number}</h2>
                                    <p className="text-gray-600">{selectedVehicle.make} {selectedVehicle.model} ({selectedVehicle.year})</p>
                                </div>
                                <button 
                                    onClick={() => setSelectedVehicle(null)}
                                    className="text-gray-400 hover:text-gray-600 text-2xl"
                                >
                                    ×
                                </button>
                            </div>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <h3 className="text-lg font-semibold mb-3">Vehicle Information</h3>
                                    <div className="space-y-2 text-sm">
                                        <div><strong>Status:</strong> 
                                            <span className={`ml-2 px-2 py-1 rounded-full text-xs ${getStatusColor(selectedVehicle.status)}`}>
                                                {selectedVehicle.status}
                                            </span>
                                        </div>
                                        <div><strong>VIN:</strong> {selectedVehicle.vin}</div>
                                        <div><strong>License Plate:</strong> {selectedVehicle.license_plate}</div>
                                        <div><strong>Mileage:</strong> {formatMileage(selectedVehicle.mileage)} miles</div>
                                        <div><strong>Fuel Capacity:</strong> {selectedVehicle.fuel_capacity} gallons</div>
                                        <div><strong>Max Weight:</strong> {selectedVehicle.max_weight.toLocaleString()} lbs</div>
                                    </div>
                                </div>
                                
                                <div>
                                    <h3 className="text-lg font-semibold mb-3">Location & Status</h3>
                                    <div className="space-y-3 text-sm">
                                        {selectedVehicle.current_location && selectedVehicle.current_location.latitude ? (
                                            <div className="p-3 bg-blue-50 rounded-lg">
                                                <div className="font-medium text-blue-800">📍 Current Location</div>
                                                <div>Lat: {selectedVehicle.current_location.latitude.toFixed(6)}</div>
                                                <div>Lng: {selectedVehicle.current_location.longitude.toFixed(6)}</div>
                                                <div className="text-xs text-blue-600 mt-1">
                                                    Updated: {formatLastUpdate(selectedVehicle.last_location_update)}
                                                </div>
                                            </div>
                                        ) : (
                                            <div className="p-3 bg-gray-50 rounded-lg">
                                                <div className="font-medium text-gray-800">Location Unknown</div>
                                                <div className="text-xs text-gray-600">No recent location updates</div>
                                            </div>
                                        )}
                                        
                                        {selectedVehicle.next_maintenance_date && (
                                            <div className="p-3 bg-yellow-50 rounded-lg">
                                                <div className="font-medium text-yellow-800">🔧 Next Maintenance</div>
                                                <div>{new Date(selectedVehicle.next_maintenance_date).toLocaleDateString()}</div>
                                                <div className="text-xs text-yellow-600 mt-1">
                                                    Miles to maintenance: {(selectedVehicle.next_maintenance_mileage - selectedVehicle.mileage).toLocaleString()}
                                                </div>
                                            </div>
                                        )}
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

export default FleetPage;
