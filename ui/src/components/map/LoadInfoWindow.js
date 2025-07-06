import React from 'react';
import { InfoWindow } from '@react-google-maps/api';
import { normalizePosition } from '../../utils/wkbDecoder';

const LoadInfoWindow = ({
    load,
    onClose,
    vehicles,
    drivers,
    selectedVehicleForOptimization,
    onVehicleSelect,
    onOptimizeRoute,
    isOptimizing,
    optimizedRoute
}) => {
    if (!load) return null;

    // Convert position data to Google Maps LatLngLiteral format
    const getValidPosition = (pos) => {
        if (!pos) return null;

        // Use the new normalizePosition utility that handles WKB, {latitude, longitude}, and {lat, lng} formats
        const validPos = normalizePosition(pos);

        if (!validPos) {
            console.warn('Invalid position data for InfoWindow:', pos);
            return null;
        }

        return validPos;
    };
    
    const validPosition = getValidPosition(load.pickup_location);
    
    // Don't render InfoWindow if position is invalid
    if (!validPosition) {
        return null;
    }

    const handleOptimize = () => {
        if (selectedVehicleForOptimization && onOptimizeRoute) {
            onOptimizeRoute(load.id, selectedVehicleForOptimization);
        }
    };

    return (
        <InfoWindow
            position={validPosition}
            onCloseClick={onClose}
        >
            <div className="p-4 max-w-sm">
                {/* Load Header */}
                <div className="flex items-center gap-2 mb-3">
                    <span className="text-2xl">📦</span>
                    <div>
                        <h3 className="font-bold text-lg text-gray-900">Load #{load.id}</h3>
                        <p className="text-sm text-gray-600">{load.load_type || 'Standard Load'}</p>
                    </div>
                </div>

                {/* Load Details */}
                <div className="space-y-2 mb-4">
                    <div className="flex justify-between">
                        <span className="text-sm font-medium text-gray-700">Weight:</span>
                        <span className="text-sm text-gray-900">{load.weight || 'N/A'} lbs</span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-sm font-medium text-gray-700">Distance:</span>
                        <span className="text-sm text-gray-900">{load.distance || 'N/A'} miles</span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-sm font-medium text-gray-700">Status:</span>
                        <span className={`text-sm font-medium px-2 py-1 rounded ${
                            load.status === 'available' ? 'bg-green-100 text-green-800' :
                            load.status === 'assigned' ? 'bg-blue-100 text-blue-800' :
                            load.status === 'in_transit' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-gray-100 text-gray-800'
                        }`}>
                            {load.status || 'Unknown'}
                        </span>
                    </div>
                </div>

                {/* Route Information */}
                <div className="space-y-2 mb-4">
                    <div>
                        <span className="text-sm font-medium text-gray-700">📍 Pickup:</span>
                        <p className="text-xs text-gray-600 mt-1">{load.pickup_address || 'Address not available'}</p>
                    </div>
                    <div>
                        <span className="text-sm font-medium text-gray-700">📍 Delivery:</span>
                        <p className="text-xs text-gray-600 mt-1">{load.delivery_address || 'Address not available'}</p>
                    </div>
                </div>

                {/* Route Optimization Section */}
                <div className="border-t pt-4">
                    <h4 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                        ⚡ Route Optimization
                    </h4>
                    
                    {/* Vehicle Selection */}
                    <div className="mb-3">
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Select Vehicle:
                        </label>
                        <select
                            value={selectedVehicleForOptimization || ''}
                            onChange={(e) => onVehicleSelect && onVehicleSelect(e.target.value)}
                            className="w-full p-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        >
                            <option value="">Choose a vehicle...</option>
                            {vehicles.map((vehicle) => (
                                <option key={vehicle.id} value={vehicle.id}>
                                    {vehicle.license_plate} - {vehicle.vehicle_type}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Optimization Results */}
                    {optimizedRoute && (
                        <div className="mb-3 p-3 bg-green-50 rounded-lg">
                            <div className="flex items-center gap-2 mb-2">
                                <span className="text-green-600">✅</span>
                                <span className="text-sm font-medium text-green-800">Route Optimized!</span>
                            </div>
                            <div className="text-xs text-green-700 space-y-1">
                                {optimizedRoute.total_distance && (
                                    <div>Distance: {Math.round(optimizedRoute.total_distance)} miles</div>
                                )}
                                {optimizedRoute.total_duration && (
                                    <div>Duration: {Math.round(optimizedRoute.total_duration / 60)} mins</div>
                                )}
                                {optimizedRoute.driver_name && (
                                    <div>Driver: {optimizedRoute.driver_name}</div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Optimization Button */}
                    <button
                        onClick={handleOptimize}
                        disabled={!selectedVehicleForOptimization || isOptimizing}
                        className={`w-full py-2 px-4 rounded-md text-sm font-medium transition-colors duration-200 ${
                            !selectedVehicleForOptimization || isOptimizing
                                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                : 'bg-blue-600 hover:bg-blue-700 text-white'
                        }`}
                    >
                        {isOptimizing ? (
                            <div className="flex items-center justify-center gap-2">
                                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                                Optimizing...
                            </div>
                        ) : (
                            '⚡ Optimize Route'
                        )}
                    </button>
                </div>
            </div>
        </InfoWindow>
    );
};

export default LoadInfoWindow;
