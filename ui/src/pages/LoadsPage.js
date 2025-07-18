import React, { useState, useEffect } from 'react';

const LoadsPage = () => {
    const [loads, setLoads] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedLoad, setSelectedLoad] = useState(null);
    const [statusFilter, setStatusFilter] = useState('all');
    const [showUnassignedOnly, setShowUnassignedOnly] = useState(false);
    const [loadCounts, setLoadCounts] = useState({
        total: 0,
        pending: 0,
        assigned: 0,
        in_transit: 0,
        delivered: 0,
        unassigned: 0
    });

    const fetchLoads = async () => {
        try {
            setLoading(true);
            let url = `${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/loads`;
            
            if (showUnassignedOnly) {
                url = `${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/loads/unassigned`;
            } else if (statusFilter !== 'all') {
                url = `${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/loads/by-status/${statusFilter.toUpperCase()}`;
            }
            
            const response = await fetch(url);
            if (!response.ok) throw new Error('Failed to fetch loads');
            
            const data = await response.json();
            setLoads(data.loads || data || []);
            
            // Update counts
            await fetchLoadCounts();
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const fetchLoadCounts = async () => {
        try {
            const [unassignedResponse, allResponse] = await Promise.all([
                fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/loads/unassigned`),
                fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/loads`)
            ]);
            
            const unassignedData = await unassignedResponse.json();
            const allData = await allResponse.json();
            
            const allLoads = allData.loads || [];
            const statusCounts = allLoads.reduce((acc, load) => {
                acc[load.status.toLowerCase()] = (acc[load.status.toLowerCase()] || 0) + 1;
                return acc;
            }, {});
            
            setLoadCounts({
                total: allLoads.length,
                pending: statusCounts.pending || 0,
                assigned: statusCounts.assigned || 0,
                in_transit: statusCounts.in_transit || 0,
                delivered: statusCounts.delivered || 0,
                unassigned: (unassignedData.loads || unassignedData || []).length
            });
        } catch (err) {
            console.error('Error fetching load counts:', err);
        }
    };

    const assignDriver = async (loadId, driverId) => {
        try {
            const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/loads/${loadId}/assign`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ driver_id: driverId })
            });
            
            if (!response.ok) throw new Error('Failed to assign driver');
            await fetchLoads(); // Refresh the loads
        } catch (err) {
            alert(`Error assigning driver: ${err.message}`);
        }
    };

    useEffect(() => {
        fetchLoads();
    }, [statusFilter, showUnassignedOnly]);

    const getStatusColor = (status) => {
        const colors = {
            'PENDING': 'bg-yellow-100 text-yellow-800',
            'ASSIGNED': 'bg-blue-100 text-blue-800',
            'PICKED_UP': 'bg-purple-100 text-purple-800',
            'IN_TRANSIT': 'bg-indigo-100 text-indigo-800',
            'DELIVERED': 'bg-green-100 text-green-800',
            'CANCELLED': 'bg-red-100 text-red-800'
        };
        return colors[status] || 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200';
    };

    const formatCurrency = (amount) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    };

    if (loading) {
        return (
            <div className="space-y-6">
                <div className="flex items-center justify-center h-64">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-blue-100 dark:bg-primary/20 rounded-lg flex items-center justify-center">
                        <svg className="w-5 h-5 text-blue-600 dark:text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                        </svg>
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900 dark:text-foreground">Loads</h1>
                        <p className="text-gray-600 dark:text-muted mt-1">Manage and track all transportation loads</p>
                    </div>
                </div>
                <button 
                    onClick={fetchLoads}
                    className="bg-primary hover:bg-primary/80 text-background px-4 py-2 rounded-lg transition-colors duration-200 flex items-center gap-2"
                >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Refresh
                </button>
            </div>

            {/* Load Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                {[
                    { key: 'total', count: loadCounts.total, label: 'Total Loads', color: 'text-gray-900 dark:text-foreground' },
                    { key: 'pending', count: loadCounts.pending, label: 'Pending', color: 'text-yellow-600' },
                    { key: 'assigned', count: loadCounts.assigned, label: 'Assigned', color: 'text-blue-600' },
                    { key: 'in_transit', count: loadCounts.in_transit, label: 'In Transit', color: 'text-indigo-600' },
                    { key: 'delivered', count: loadCounts.delivered, label: 'Delivered', color: 'text-green-600' },
                    { key: 'unassigned', count: loadCounts.unassigned, label: 'Unassigned', color: 'text-red-600' }
                ].map((card) => (
                    <div key={card.key} className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-accent p-4">
                        <div className={`text-2xl font-bold ${card.color}`}>{card.count}</div>
                        <div className="text-sm text-gray-600 dark:text-muted">{card.label}</div>
                    </div>
                ))}
            </div>

            {/* Filters */}
            <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-accent p-6">
                <div className="flex items-center gap-2 mb-4">
                    <div className="w-6 h-6 bg-gray-100 dark:bg-accent rounded-lg flex items-center justify-center">
                        <svg className="w-4 h-4 text-gray-600 dark:text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.207A1 1 0 013 6.5V4z" />
                        </svg>
                    </div>
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-foreground">Filters</h2>
                </div>
                
                <div className="flex flex-wrap gap-4">
                    <div className="flex items-center space-x-2">
                        <label className="text-sm font-medium text-gray-700 dark:text-muted">Status:</label>
                        <select 
                            value={statusFilter} 
                            onChange={(e) => setStatusFilter(e.target.value)}
                            className="border border-gray-300 dark:border-accent rounded-md px-3 py-1 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-foreground"
                        >
                            <option value="all">All Statuses</option>
                            <option value="pending">Pending</option>
                            <option value="assigned">Assigned</option>
                            <option value="picked_up">Picked Up</option>
                            <option value="in_transit">In Transit</option>
                            <option value="delivered">Delivered</option>
                            <option value="cancelled">Cancelled</option>
                        </select>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                        <input 
                            type="checkbox" 
                            id="unassignedOnly" 
                            checked={showUnassignedOnly}
                            onChange={(e) => setShowUnassignedOnly(e.target.checked)}
                            className="rounded border-gray-300 dark:border-accent bg-white dark:bg-gray-800"
                        />
                        <label htmlFor="unassignedOnly" className="text-sm font-medium text-gray-700 dark:text-muted">
                            Unassigned Only
                        </label>
                    </div>
                </div>
            </div>

            {error && (
                <div className="bg-red-100 dark:bg-red-900/20 border border-red-400 dark:border-red-600 text-red-700 dark:text-red-400 px-4 py-3 rounded mb-6">
                    Error: {error}
                </div>
            )}

            {/* Loads Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                {loads.map((load, index) => (
                    <div key={load.load_id || `load-${index}`} className="bg-white dark:bg-gray-900 rounded-xl shadow-lg border border-gray-200 dark:border-accent p-6 hover:shadow-xl transition-shadow duration-200">
                        <div className="flex items-start justify-between mb-4">
                            <div>
                                <h3 className="text-lg font-bold text-gray-900 dark:text-foreground">{load.load_number || `Load #${load.load_id.slice(-8)}`}</h3>
                                <p className="text-sm text-gray-600 dark:text-muted">{load.customer_name}</p>
                            </div>
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(load.status)}`}>
                                {load.status}
                            </span>
                        </div>
                        
                        <div className="space-y-2 mb-4">
                            <div className="flex justify-between text-sm">
                                <span className="text-gray-600 dark:text-muted">Rate:</span>
                                <span className="font-medium text-green-600">{formatCurrency(load.rate)}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-gray-600 dark:text-muted">Distance:</span>
                                <span className="font-medium">{load.distance} mi</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-gray-600 dark:text-muted">Weight:</span>
                                <span className="font-medium">{load.weight ? `${load.weight} lbs` : 'N/A'}</span>
                            </div>
                        </div>
                        
                        {/* Route Info */}
                        <div className="mb-4">
                            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-muted mb-2">
                                <span>📍</span>
                                <span>{load.pickup_address?.split(',')[0] || 'N/A'}</span>
                            </div>
                            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-muted">
                                <span>🎯</span>
                                <span>{load.delivery_address?.split(',')[0] || 'N/A'}</span>
                            </div>
                        </div>
                        
                        {/* Dates */}
                        <div className="mb-4 text-xs text-gray-500 dark:text-gray-400">
                            <div>Pickup: {formatDate(load.pickup_date)}</div>
                            <div>Delivery: {formatDate(load.delivery_date)}</div>
                        </div>
                        
                        {/* Driver Assignment */}
                        {load.assigned_driver_name ? (
                            <div className="mb-4 p-2 bg-blue-50 rounded-lg">
                                <div className="text-sm font-medium text-blue-800">Assigned Driver:</div>
                                <div className="text-sm text-blue-600">{load.assigned_driver_name}</div>
                            </div>
                        ) : (
                            <div className="mb-4 p-2 bg-yellow-50 rounded-lg">
                                <div className="text-sm font-medium text-yellow-800">⚠️ Unassigned</div>
                                <div className="text-xs text-yellow-600">Needs driver assignment</div>
                            </div>
                        )}
                        
                        <button 
                            onClick={() => setSelectedLoad(load)}
                            className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg transition-colors duration-200 text-sm"
                        >
                            View Details
                        </button>
                    </div>
                ))}
            </div>
            
            {loads.length === 0 && !loading && (
                <div className="bg-white dark:bg-gray-900 rounded-xl shadow-lg border border-gray-200 dark:border-accent p-12 text-center">
                    <div className="text-6xl mb-4">📦</div>
                    <h3 className="text-xl font-semibold text-gray-900 dark:text-foreground mb-2">No loads found</h3>
                    <p className="text-gray-600 dark:text-muted">Try adjusting your filters or check back later.</p>
                </div>
            )}

            {/* Load Details Modal */}
            {selectedLoad && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white dark:bg-gray-900 rounded-xl shadow-xl border border-gray-200 dark:border-accent max-w-4xl w-full max-h-96 overflow-y-auto">
                        <div className="p-6">
                            <div className="flex items-start justify-between mb-6">
                                <div>
                                    <h2 className="text-2xl font-bold text-gray-900 dark:text-foreground">
                                        {selectedLoad.load_number || `Load #${selectedLoad.load_id.slice(-8)}`}
                                    </h2>
                                    <p className="text-gray-600 dark:text-muted">{selectedLoad.customer_name}</p>
                                </div>
                                <button 
                                    onClick={() => setSelectedLoad(null)}
                                    className="text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 text-2xl"
                                >
                                    ×
                                </button>
                            </div>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <h3 className="text-lg font-semibold mb-3">Load Details</h3>
                                    <div className="space-y-2 text-sm">
                                        <div><strong>Status:</strong> 
                                            <span className={`ml-2 px-2 py-1 rounded-full text-xs ${getStatusColor(selectedLoad.status)}`}>
                                                {selectedLoad.status}
                                            </span>
                                        </div>
                                        <div><strong>Rate:</strong> {formatCurrency(selectedLoad.rate)}</div>
                                        <div><strong>Distance:</strong> {selectedLoad.distance} miles</div>
                                        <div><strong>Weight:</strong> {selectedLoad.weight ? `${selectedLoad.weight} lbs` : 'Not specified'}</div>
                                        <div><strong>Commodity:</strong> {selectedLoad.commodity_type || 'Not specified'}</div>
                                    </div>
                                </div>
                                
                                <div>
                                    <h3 className="text-lg font-semibold mb-3">Route Information</h3>
                                    <div className="space-y-3 text-sm">
                                        <div className="p-3 bg-blue-50 rounded-lg">
                                            <div className="font-medium text-blue-800">📍 Pickup Location</div>
                                            <div>{selectedLoad.pickup_address}</div>
                                            <div>{selectedLoad.pickup_city}, {selectedLoad.pickup_state} {selectedLoad.pickup_zip}</div>
                                            <div className="text-xs text-blue-600 mt-1">Date: {formatDate(selectedLoad.pickup_date)}</div>
                                        </div>
                                        
                                        <div className="p-3 bg-red-50 rounded-lg">
                                            <div className="font-medium text-red-800">🎯 Delivery Location</div>
                                            <div>{selectedLoad.delivery_address}</div>
                                            <div>{selectedLoad.delivery_city}, {selectedLoad.delivery_state} {selectedLoad.delivery_zip}</div>
                                            <div className="text-xs text-red-600 mt-1">Date: {formatDate(selectedLoad.delivery_date)}</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            {selectedLoad.assigned_driver_name && (
                                <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                                    <h3 className="text-lg font-semibold mb-2">Assigned Driver</h3>
                                    <div className="text-sm">
                                        <strong>{selectedLoad.assigned_driver_name}</strong>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default LoadsPage;
