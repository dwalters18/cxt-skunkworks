import React, { useState, useEffect } from 'react';

const LoadManager = ({ apiBase }) => {
    const [loads, setLoads] = useState([]);
    const [loading, setLoading] = useState(false);
    const [selectedLoad, setSelectedLoad] = useState(null);
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [filters, setFilters] = useState({
        status: '',
        carrier_id: ''
    });

    // New load form state
    const [newLoad, setNewLoad] = useState({
        load_number: '',
        pickup_address: '',
        delivery_address: '',
        pickup_datetime: '',
        delivery_datetime: '',
        weight: '',
        rate: ''
    });

    useEffect(() => {
        fetchLoads();
    }, [filters]);

    const fetchLoads = async () => {
        setLoading(true);
        try {
            const params = new URLSearchParams();
            if (filters.status) params.append('status', filters.status);
            if (filters.carrier_id) params.append('carrier_id', filters.carrier_id);
            
            const response = await fetch(`${apiBase}/api/loads?${params}`);
            if (response.ok) {
                const data = await response.json();
                setLoads(data);
            }
        } catch (error) {
            console.error('Error fetching loads:', error);
        }
        setLoading(false);
    };

    const createLoad = async () => {
        try {
            const response = await fetch(`${apiBase}/api/loads`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(newLoad),
            });
            
            if (response.ok) {
                setShowCreateForm(false);
                setNewLoad({
                    load_number: '',
                    pickup_address: '',
                    delivery_address: '',
                    pickup_datetime: '',
                    delivery_datetime: '',
                    weight: '',
                    rate: ''
                });
                fetchLoads();
            }
        } catch (error) {
            console.error('Error creating load:', error);
        }
    };

    const updateLoadStatus = async (loadId, newStatus) => {
        try {
            const response = await fetch(`${apiBase}/api/loads/${loadId}/status`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ status: newStatus }),
            });
            
            if (response.ok) {
                fetchLoads();
            }
        } catch (error) {
            console.error('Error updating load status:', error);
        }
    };

    const getStatusColor = (status) => {
        const colors = {
            'pending': '#ffa500',
            'assigned': '#2196f3',
            'picked_up': '#9c27b0',
            'in_transit': '#ff9800',
            'delivered': '#4caf50',
            'cancelled': '#f44336'
        };
        return colors[status] || '#757575';
    };

    const formatDateTime = (dateString) => {
        if (!dateString) return 'N/A';
        return new Date(dateString).toLocaleString();
    };

    return (
        <div className="p-6 bg-gray-50 min-h-screen space-y-6">
            <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold text-gray-800 dark:text-foreground">Load Management</h2>
                <button 
                    className="btn-primary"
                    onClick={() => setShowCreateForm(true)}
                >
                    + Create Load
                </button>
            </div>

            {/* Filters */}
            <div className="flex items-center space-x-4 mb-4">
                <select 
                    value={filters.status} 
                    onChange={(e) => setFilters({...filters, status: e.target.value})}
                >
                    <option value="">All Statuses</option>
                    <option value="pending">Pending</option>
                    <option value="assigned">Assigned</option>
                    <option value="picked_up">Picked Up</option>
                    <option value="in_transit">In Transit</option>
                    <option value="delivered">Delivered</option>
                    <option value="cancelled">Cancelled</option>
                </select>

                <input
                    type="text"
                    placeholder="Carrier ID"
                    value={filters.carrier_id}
                    onChange={(e) => setFilters({...filters, carrier_id: e.target.value})}
                />

                <button onClick={fetchLoads} className="btn-secondary">
                    🔄 Refresh
                </button>
            </div>

            {/* Create Load Modal */}
            {showCreateForm && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white p-6 rounded-lg shadow-lg w-11/12 md:w-1/2">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-xl font-semibold">Create New Load</h3>
                            <button onClick={() => setShowCreateForm(false)}>✕</button>
                        </div>
                        <div className="space-y-4">
                            <div className="flex flex-col space-y-1">
                                <label>Load Number:</label>
                                <input
                                    type="text"
                                    value={newLoad.load_number}
                                    onChange={(e) => setNewLoad({...newLoad, load_number: e.target.value})}
                                />
                            </div>
                            <div className="flex flex-col space-y-1">
                                <label>Pickup Address:</label>
                                <input
                                    type="text"
                                    value={newLoad.pickup_address}
                                    onChange={(e) => setNewLoad({...newLoad, pickup_address: e.target.value})}
                                />
                            </div>
                            <div className="flex flex-col space-y-1">
                                <label>Delivery Address:</label>
                                <input
                                    type="text"
                                    value={newLoad.delivery_address}
                                    onChange={(e) => setNewLoad({...newLoad, delivery_address: e.target.value})}
                                />
                            </div>
                            <div className="flex space-x-4">
                                <div className="flex flex-col space-y-1">
                                    <label>Weight (lbs):</label>
                                    <input
                                        type="number"
                                        value={newLoad.weight}
                                        onChange={(e) => setNewLoad({...newLoad, weight: e.target.value})}
                                    />
                                </div>
                                <div className="flex flex-col space-y-1">
                                    <label>Rate ($):</label>
                                    <input
                                        type="number"
                                        value={newLoad.rate}
                                        onChange={(e) => setNewLoad({...newLoad, rate: e.target.value})}
                                    />
                                </div>
                            </div>
                            <div className="flex space-x-4">
                                <div className="flex flex-col space-y-1">
                                    <label>Pickup Date/Time:</label>
                                    <input
                                        type="datetime-local"
                                        value={newLoad.pickup_datetime}
                                        onChange={(e) => setNewLoad({...newLoad, pickup_datetime: e.target.value})}
                                    />
                                </div>
                                <div className="flex flex-col space-y-1">
                                    <label>Delivery Date/Time:</label>
                                    <input
                                        type="datetime-local"
                                        value={newLoad.delivery_datetime}
                                        onChange={(e) => setNewLoad({...newLoad, delivery_datetime: e.target.value})}
                                    />
                                </div>
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button onClick={() => setShowCreateForm(false)} className="btn-secondary">
                                Cancel
                            </button>
                            <button onClick={createLoad} className="btn-primary">
                                Create Load
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Loads Table */}
            <div className="table-container">
                {loading ? (
                    <div className="loading">Loading loads...</div>
                ) : (
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Load #</th>
                                <th>Route</th>
                                <th>Status</th>
                                <th>Weight</th>
                                <th>Rate</th>
                                <th>Pickup Date</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loads.map((load) => (
                                <tr key={load.id} onClick={() => setSelectedLoad(load)}>
                                    <td>{load.load_number}</td>
                                    <td>
                                        <div className="route-info">
                                            <div>📍 {load.pickup_address}</div>
                                            <div>📍 {load.delivery_address}</div>
                                        </div>
                                    </td>
                                    <td>
                                        <span 
                                            className="status-badge"
                                            style={{ backgroundColor: getStatusColor(load.status) }}
                                        >
                                            {load.status}
                                        </span>
                                    </td>
                                    <td>{load.weight ? `${load.weight} lbs` : 'N/A'}</td>
                                    <td>{load.rate ? `$${load.rate}` : 'N/A'}</td>
                                    <td>{formatDateTime(load.pickup_datetime)}</td>
                                    <td>
                                        <div className="action-buttons">
                                            {load.status === 'pending' && (
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        updateLoadStatus(load.id, 'assigned');
                                                    }}
                                                    className="btn-small btn-primary"
                                                >
                                                    Assign
                                                </button>
                                            )}
                                            {load.status === 'assigned' && (
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        updateLoadStatus(load.id, 'picked_up');
                                                    }}
                                                    className="btn-small btn-warning"
                                                >
                                                    Pick Up
                                                </button>
                                            )}
                                            {load.status === 'picked_up' && (
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        updateLoadStatus(load.id, 'in_transit');
                                                    }}
                                                    className="btn-small btn-info"
                                                >
                                                    In Transit
                                                </button>
                                            )}
                                            {load.status === 'in_transit' && (
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        updateLoadStatus(load.id, 'delivered');
                                                    }}
                                                    className="btn-small btn-success"
                                                >
                                                    Deliver
                                                </button>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Load Details */}
            {selectedLoad && (
                <div className="load-details">
                    <h3>Load Details: {selectedLoad.load_number}</h3>
                    <div className="details-grid">
                        <div><strong>Status:</strong> {selectedLoad.status}</div>
                        <div><strong>Weight:</strong> {selectedLoad.weight} lbs</div>
                        <div><strong>Rate:</strong> ${selectedLoad.rate}</div>
                        <div><strong>Carrier:</strong> {selectedLoad.carrier_id || 'Unassigned'}</div>
                        <div><strong>Vehicle:</strong> {selectedLoad.vehicle_id || 'Unassigned'}</div>
                        <div><strong>Driver:</strong> {selectedLoad.driver_id || 'Unassigned'}</div>
                        <div><strong>Created:</strong> {formatDateTime(selectedLoad.created_at)}</div>
                        <div><strong>Updated:</strong> {formatDateTime(selectedLoad.updated_at)}</div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default LoadManager;
