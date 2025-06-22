import React, { useState, useEffect } from 'react';

const VehicleTracker = ({ apiBase }) => {
    const [vehicles, setVehicles] = useState([]);
    const [selectedVehicle, setSelectedVehicle] = useState(null);
    const [trackingHistory, setTrackingHistory] = useState([]);
    const [loading, setLoading] = useState(false);
    const [showLocationUpdate, setShowLocationUpdate] = useState(false);
    const [locationUpdate, setLocationUpdate] = useState({
        latitude: '',
        longitude: '',
        speed: '',
        heading: ''
    });

    useEffect(() => {
        fetchVehicles();
        const interval = setInterval(fetchVehicles, 15000); // Update every 15 seconds
        return () => clearInterval(interval);
    }, []);

    const fetchVehicles = async () => {
        setLoading(true);
        try {
            const response = await fetch(`${apiBase}/api/vehicles`);
            if (response.ok) {
                const data = await response.json();
                setVehicles(data);
            }
        } catch (error) {
            console.error('Error fetching vehicles:', error);
        }
        setLoading(false);
    };

    const fetchTrackingHistory = async (vehicleId) => {
        try {
            const response = await fetch(`${apiBase}/api/vehicles/${vehicleId}/tracking?hours=24`);
            if (response.ok) {
                const data = await response.json();
                setTrackingHistory(data);
            }
        } catch (error) {
            console.error('Error fetching tracking history:', error);
        }
    };

    const updateVehicleLocation = async () => {
        if (!selectedVehicle) return;
        
        try {
            const response = await fetch(`${apiBase}/api/vehicles/${selectedVehicle.id}/location`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    latitude: parseFloat(locationUpdate.latitude),
                    longitude: parseFloat(locationUpdate.longitude),
                    speed: parseFloat(locationUpdate.speed) || null,
                    heading: parseFloat(locationUpdate.heading) || null,
                }),
            });
            
            if (response.ok) {
                setShowLocationUpdate(false);
                setLocationUpdate({ latitude: '', longitude: '', speed: '', heading: '' });
                fetchVehicles();
                fetchTrackingHistory(selectedVehicle.id);
            }
        } catch (error) {
            console.error('Error updating vehicle location:', error);
        }
    };

    const selectVehicle = (vehicle) => {
        setSelectedVehicle(vehicle);
        fetchTrackingHistory(vehicle.id);
    };

    const getStatusColor = (status) => {
        const colors = {
            'available': '#4caf50',
            'assigned': '#2196f3',
            'in_transit': '#ff9800',
            'maintenance': '#f44336',
            'offline': '#757575'
        };
        return colors[status] || '#757575';
    };

    const formatDateTime = (dateString) => {
        return new Date(dateString).toLocaleString();
    };

    const generateSampleLocation = () => {
        // Sample locations around Dallas, TX area
        const baseLatitude = 32.7767;
        const baseLongitude = -96.7970;
        const variation = 0.5; // Roughly 35 mile radius
        
        setLocationUpdate({
            latitude: (baseLatitude + (Math.random() - 0.5) * variation).toFixed(6),
            longitude: (baseLongitude + (Math.random() - 0.5) * variation).toFixed(6),
            speed: Math.floor(Math.random() * 75).toString(),
            heading: Math.floor(Math.random() * 360).toString()
        });
    };

    return (
        <div className="vehicle-tracker">
            <div className="section-header">
                <h2>Vehicle Tracking</h2>
                <button onClick={fetchVehicles} className="btn-secondary">
                    🔄 Refresh
                </button>
            </div>

            <div className="tracker-layout">
                {/* Vehicle List */}
                <div className="vehicle-list">
                    <h3>Active Vehicles ({vehicles.length})</h3>
                    {loading ? (
                        <div className="loading">Loading vehicles...</div>
                    ) : (
                        <div className="vehicles-grid">
                            {vehicles.map((vehicle) => (
                                <div
                                    key={vehicle.id}
                                    className={`vehicle-card ${selectedVehicle?.id === vehicle.id ? 'selected' : ''}`}
                                    onClick={() => selectVehicle(vehicle)}
                                >
                                    <div className="vehicle-header">
                                        <div className="vehicle-icon">🚛</div>
                                        <div className="vehicle-info">
                                            <div className="vehicle-id">{vehicle.vehicle_number || vehicle.id}</div>
                                            <div 
                                                className="vehicle-status"
                                                style={{ color: getStatusColor(vehicle.status) }}
                                            >
                                                ● {vehicle.status}
                                            </div>
                                        </div>
                                    </div>
                                    <div className="vehicle-details">
                                        <div>Type: {vehicle.vehicle_type}</div>
                                        <div>Carrier: {vehicle.carrier_id}</div>
                                        <div>Driver: {vehicle.current_driver_id || 'None'}</div>
                                        <div>Updated: {formatDateTime(vehicle.updated_at)}</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Vehicle Details & Map */}
                <div className="vehicle-details-panel">
                    {selectedVehicle ? (
                        <div>
                            <div className="vehicle-detail-header">
                                <h3>Vehicle {selectedVehicle.vehicle_number || selectedVehicle.id}</h3>
                                <button
                                    onClick={() => setShowLocationUpdate(true)}
                                    className="btn-primary"
                                >
                                    📍 Update Location
                                </button>
                            </div>

                            {/* Vehicle Info */}
                            <div className="vehicle-info-grid">
                                <div className="info-card">
                                    <h4>Vehicle Information</h4>
                                    <div><strong>Status:</strong> {selectedVehicle.status}</div>
                                    <div><strong>Type:</strong> {selectedVehicle.vehicle_type}</div>
                                    <div><strong>Capacity:</strong> {selectedVehicle.capacity} lbs</div>
                                    <div><strong>License:</strong> {selectedVehicle.license_plate}</div>
                                    <div><strong>VIN:</strong> {selectedVehicle.vin}</div>
                                </div>

                                <div className="info-card">
                                    <h4>Current Assignment</h4>
                                    <div><strong>Carrier:</strong> {selectedVehicle.carrier_id}</div>
                                    <div><strong>Driver:</strong> {selectedVehicle.current_driver_id || 'None'}</div>
                                    <div><strong>Load:</strong> {selectedVehicle.current_load_id || 'None'}</div>
                                </div>
                            </div>

                            {/* Tracking History */}
                            <div className="tracking-history">
                                <h4>Recent Tracking Data ({trackingHistory.length} records)</h4>
                                <div className="tracking-table">
                                    <table className="data-table">
                                        <thead>
                                            <tr>
                                                <th>Time</th>
                                                <th>Location</th>
                                                <th>Speed</th>
                                                <th>Heading</th>
                                                <th>Status</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {trackingHistory.slice(0, 10).map((track, index) => (
                                                <tr key={index}>
                                                    <td>{formatDateTime(track.time)}</td>
                                                    <td>
                                                        {track.latitude?.toFixed(4)}, {track.longitude?.toFixed(4)}
                                                    </td>
                                                    <td>{track.speed ? `${track.speed} mph` : 'N/A'}</td>
                                                    <td>{track.heading ? `${track.heading}°` : 'N/A'}</td>
                                                    <td>
                                                        <span className={`status-indicator ${track.is_moving ? 'moving' : 'stopped'}`}>
                                                            {track.is_moving ? '🟢 Moving' : '🔴 Stopped'}
                                                        </span>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            {/* Simple Map Placeholder */}
                            <div className="map-container">
                                <h4>Location Map</h4>
                                <div className="map-placeholder">
                                    <div className="map-info">
                                        {trackingHistory.length > 0 ? (
                                            <div>
                                                <div>📍 Latest Position:</div>
                                                <div>Lat: {trackingHistory[0]?.latitude?.toFixed(6)}</div>
                                                <div>Lng: {trackingHistory[0]?.longitude?.toFixed(6)}</div>
                                                <div>Last Update: {formatDateTime(trackingHistory[0]?.time)}</div>
                                            </div>
                                        ) : (
                                            <div>No tracking data available</div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="no-selection">
                            <h3>Select a vehicle to view details</h3>
                            <p>Click on a vehicle from the list to see tracking information, location history, and current status.</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Location Update Modal */}
            {showLocationUpdate && selectedVehicle && (
                <div className="modal-overlay">
                    <div className="modal">
                        <div className="modal-header">
                            <h3>Update Vehicle Location</h3>
                            <button onClick={() => setShowLocationUpdate(false)}>✕</button>
                        </div>
                        <div className="modal-body">
                            <div className="form-group">
                                <label>Latitude:</label>
                                <input
                                    type="number"
                                    step="0.000001"
                                    value={locationUpdate.latitude}
                                    onChange={(e) => setLocationUpdate({...locationUpdate, latitude: e.target.value})}
                                    placeholder="32.776664"
                                />
                            </div>
                            <div className="form-group">
                                <label>Longitude:</label>
                                <input
                                    type="number"
                                    step="0.000001"
                                    value={locationUpdate.longitude}
                                    onChange={(e) => setLocationUpdate({...locationUpdate, longitude: e.target.value})}
                                    placeholder="-96.796988"
                                />
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label>Speed (mph):</label>
                                    <input
                                        type="number"
                                        value={locationUpdate.speed}
                                        onChange={(e) => setLocationUpdate({...locationUpdate, speed: e.target.value})}
                                        placeholder="65"
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Heading (degrees):</label>
                                    <input
                                        type="number"
                                        min="0"
                                        max="359"
                                        value={locationUpdate.heading}
                                        onChange={(e) => setLocationUpdate({...locationUpdate, heading: e.target.value})}
                                        placeholder="180"
                                    />
                                </div>
                            </div>
                            <button 
                                onClick={generateSampleLocation}
                                className="btn-secondary"
                                style={{ marginTop: '10px' }}
                            >
                                🎲 Generate Sample Location
                            </button>
                        </div>
                        <div className="modal-footer">
                            <button onClick={() => setShowLocationUpdate(false)} className="btn-secondary">
                                Cancel
                            </button>
                            <button onClick={updateVehicleLocation} className="btn-primary">
                                Update Location
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default VehicleTracker;
