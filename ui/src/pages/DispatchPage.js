import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import DispatchMapView from '../components/DispatchMapView';
import { useMapData } from '../hooks/useMapData';
import { useDarkMode } from '../contexts/DarkModeContext';
import { 
  Menu, 
  X, 
  MapPin, 
  Truck, 
  Package, 
  Route,
  Search,
  RefreshCw,
  Filter,
  Phone,
  Clock,
  Navigation,
  Circle,
  CheckCircle,
  AlertTriangle,
  Play
} from 'lucide-react';

const DispatchPage = () => {
    const navigate = useNavigate();
    const { isDarkMode } = useDarkMode();
    const [isImmersiveMode, setIsImmersiveMode] = useState(true);
    const [selectedTab, setSelectedTab] = useState('loads');
    const [selectedVehicle, setSelectedVehicle] = useState(null);
    const [selectedLoad, setSelectedLoad] = useState(null);
    const [autoRefresh, setAutoRefresh] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');
    const [visibleRoutes, setVisibleRoutes] = useState(new Set());

    // Use the existing useMapData hook to get real data
    const { 
        events, 
        vehicles, 
        loads, 
        routes,
        drivers, 
        dashboardData,
        isLoading: dataLoading,
        error: dataError,
        fetchMapData 
    } = useMapData();

    // Initialize data on component mount
    useEffect(() => {
        fetchMapData();
        const interval = autoRefresh ? setInterval(fetchMapData, 5000) : null;
        return () => interval && clearInterval(interval);
    }, [autoRefresh, fetchMapData]);

    // Initialize visible routes when routes data changes
    useEffect(() => {
        if (routes && routes.length > 0) {
            const initialVisible = new Set();
            routes.forEach(route => {
                // ACTIVE routes are always visible by default
                if (route.status === 'active' || route.status === 'ACTIVE') {
                    initialVisible.add(route.id);
                }
            });
            setVisibleRoutes(initialVisible);
        }
    }, [routes]);

    // Toggle between immersive and management modes
    const toggleMode = () => {
        if (isImmersiveMode) {
            navigate('/');
        } else {
            setIsImmersiveMode(true);
        }
    };

    // Utility functions
    const getStatusColor = (status) => {
        switch (status?.toUpperCase()) {
            case 'DELIVERED':
                return 'bg-green-100 text-green-800';
            case 'IN_TRANSIT':
                return 'bg-blue-100 text-blue-800';
            case 'ASSIGNED':
                return 'bg-yellow-100 text-yellow-800';
            case 'UNASSIGNED':
                return 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200';
            case 'CANCELLED':
                return 'bg-red-100 text-red-800';
            case 'ACTIVE':
                return 'bg-green-100 text-green-800';
            case 'COMPLETED':
                return 'bg-blue-100 text-blue-800';
            case 'PENDING':
                return 'bg-yellow-100 text-yellow-800';
            default:
                return 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200';
        }
    };

    const getPriorityColor = (priority) => {
        const colors = {
            'High': 'bg-red-100 text-red-800',
            'high': 'bg-red-100 text-red-800',
            'Medium': 'bg-yellow-100 text-yellow-800',
            'medium': 'bg-yellow-100 text-yellow-800',
            'Low': 'bg-green-100 text-green-800',
            'low': 'bg-green-100 text-green-800'
        };
        return colors[priority] || 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200';
    };

    const toggleRouteVisibility = (routeId, routeStatus) => {
        // ACTIVE routes cannot be hidden
        if (routeStatus === 'active' || routeStatus === 'ACTIVE') {
            return;
        }

        setVisibleRoutes(prev => {
            const newVisible = new Set(prev);
            if (newVisible.has(routeId)) {
                newVisible.delete(routeId);
            } else {
                newVisible.add(routeId);
            }
            return newVisible;
        });
    };

    const filteredLoads = loads ? loads.filter(load => {
        const matchesSearch = (load.number || load.id || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
                             (load.customer || '').toLowerCase().includes(searchTerm.toLowerCase());
        const matchesStatus = statusFilter === 'all' || (load.status || '').toLowerCase() === statusFilter.toLowerCase();
        return matchesSearch && matchesStatus;
    }) : [];

    // Handle load assignment
    const handleAssignLoad = (loadId, vehicleId) => {
        // This would typically make an API call to assign the load
        console.log(`Assigning load ${loadId} to vehicle ${vehicleId}`);
        // Refresh data after assignment
        fetchMapData();
    };

    return (
        <div className="h-screen flex bg-gray-50 relative">
            {/* Full Screen Map with Custom DispatchMapView */}
            <div className="flex-1 relative">
                <DispatchMapView visibleRoutes={visibleRoutes} isDarkMode={isDarkMode} />

                {/* Floating Control Panel */}
                <div className="absolute top-24 right-16 w-96 z-50">
                    <div className={`${
                        isDarkMode 
                            ? 'bg-gray-900/20 border-gray-700/30' 
                            : 'bg-white/10 border-white/20'
                    } backdrop-blur-xl rounded-2xl shadow-2xl overflow-hidden`}>
                        {/* Glass effect overlay */}
                        <div className={`absolute inset-0 ${
                            isDarkMode 
                                ? 'bg-gradient-to-br from-gray-800/30 via-gray-900/10 to-transparent' 
                                : 'bg-gradient-to-br from-white/20 via-white/5 to-transparent'
                        } pointer-events-none`}></div>
                        
                        {/* Panel Content */}
                        <div className="relative z-10">
                            {/* Panel Header */}
                            <div className={`p-6 border-b ${
                                isDarkMode ? 'border-gray-700/30' : 'border-white/10'
                            }`}>
                                <h2 className={`text-lg font-semibold mb-4 drop-shadow-sm ${
                                    isDarkMode ? 'text-white' : 'text-gray-700 dark:text-white'
                                }`}>Dispatch Control</h2>
                                
                                {/* Search and Filter */}
                                <div className="space-y-3">
                                    <div className="relative">
                                        <Search className={`absolute left-4 top-1/2 transform -translate-y-1/2 w-4 h-4 ${
                                            isDarkMode ? 'text-gray-400' : 'text-white/70'
                                        }`} />
                                        <input
                                            type="text"
                                            placeholder="Search loads..."
                                            value={searchTerm}
                                            onChange={(e) => setSearchTerm(e.target.value)}
                                            className={`w-full pl-12 pr-4 py-3 backdrop-blur-sm border rounded-xl transition-all duration-200 ${
                                                isDarkMode 
                                                    ? 'bg-gray-800/40 border-gray-600/50 text-white placeholder-gray-400 focus:ring-2 focus:ring-primary/50 focus:border-primary/50'
                                                    : 'bg-white/10 border-white/20 text-white placeholder-white/60 focus:ring-2 focus:ring-primary/50 focus:border-primary/50'
                                            }`}
                                        />
                                    </div>
                                    
                                    <select
                                        value={statusFilter}
                                        onChange={(e) => setStatusFilter(e.target.value)}
                                        className={`w-full px-4 py-3 backdrop-blur-sm border rounded-xl transition-all duration-200 ${
                                            isDarkMode 
                                                ? 'bg-gray-800/40 border-gray-600/50 text-white focus:ring-2 focus:ring-primary/50 focus:border-primary/50'
                                                : 'bg-white/10 border-white/20 text-white focus:ring-2 focus:ring-primary/50 focus:border-primary/50'
                                        }`}
                                    >
                                        <option value="all" className="bg-gray-800 text-white">All Statuses</option>
                                        <option value="unassigned" className="bg-gray-800 text-white">Unassigned</option>
                                        <option value="assigned" className="bg-gray-800 text-white">Assigned</option>
                                        <option value="pending" className="bg-gray-800 text-white">Pending</option>
                                        <option value="active" className="bg-gray-800 text-white">Active</option>
                                        <option value="completed" className="bg-gray-800 text-white">Completed</option>
                                    </select>
                                </div>
                            </div>

                            {/* Tab Navigation */}
                            <div className={`flex border-b ${
                                isDarkMode ? 'border-gray-700/30' : 'border-white/10'
                            }`}>
                                {[
                                    { id: 'loads', label: 'Loads', icon: Package },
                                    { id: 'vehicles', label: 'Vehicles', icon: Truck },
                                    { id: 'routes', label: 'Routes', icon: Route }
                                ].map(tab => (
                                    <button
                                        key={tab.id}
                                        onClick={() => setSelectedTab(tab.id)}
                                        className={`flex-1 flex items-center justify-center gap-2 py-4 px-4 text-sm font-medium transition-all duration-200 ${
                                            selectedTab === tab.id
                                                ? `text-primary border-b-2 border-primary ${
                                                    isDarkMode ? 'bg-primary/10' : 'bg-primary/10'
                                                } backdrop-blur-sm`
                                                : `${
                                                    isDarkMode ? 'text-gray-300 hover:text-white hover:bg-gray-800/20' : 'text-white/70 hover:text-white hover:bg-white/5'
                                                }`
                                        }`}
                                    >
                                        <tab.icon className="w-4 h-4" />
                                        {tab.label}
                                    </button>
                                ))}
                            </div>

                            {/* Tab Content */}
                            <div className="max-h-96 overflow-auto p-6">
                                {dataLoading ? (
                                    <div className="flex items-center justify-center h-32">
                                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                                        <span className={`ml-2 ${
                                            isDarkMode ? 'text-gray-300' : 'text-white/80'
                                        }`}>Loading...</span>
                                    </div>
                                ) : (
                                    <>
                                        {selectedTab === 'loads' && (
                                            <div className="space-y-3">
                                                {filteredLoads.length === 0 ? (
                                                    <div className={`text-center py-8 ${
                                                        isDarkMode ? 'text-gray-400' : 'text-white/60'
                                                    }`}>
                                                        <Package className="w-12 h-12 mx-auto mb-2 opacity-50" />
                                                        <p>No loads found</p>
                                                    </div>
                                                ) : (
                                                    filteredLoads.map((load) => (
                                                        <div 
                                                            key={load.id} 
                                                            className={`border rounded-lg p-4 cursor-pointer transition-all hover:shadow-md ${
                                                                selectedLoad === load.id 
                                                                    ? 'ring-2 ring-primary bg-primary/10' 
                                                                    : isDarkMode 
                                                                        ? 'bg-gray-800/40 border-gray-600/50 hover:bg-gray-700/40' 
                                                                        : 'bg-white/10 border-white/20 hover:bg-white/20'
                                                            }`}
                                                            onClick={() => setSelectedLoad(load.id)}
                                                        >
                                                            <div className="flex items-start justify-between mb-2">
                                                                <div className="flex items-center gap-2">
                                                                    <Package className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                                                                    <span className={`font-medium ${
                                                                        isDarkMode ? 'text-gray-200' : 'text-gray-700 dark:text-white'
                                                                    }`}>{load.number || load.id}</span>
                                                                </div>
                                                                <div className="flex gap-1">
                                                                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(load.status)}`}>
                                                                        {load.status || 'Unknown'}
                                                                    </span>
                                                                    {load.priority && (
                                                                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(load.priority)}`}>
                                                                            {load.priority}
                                                                        </span>
                                                                    )}
                                                                </div>
                                                            </div>
                                                            
                                                            <div className="space-y-2 text-sm">
                                                                <div className="flex items-center gap-2">
                                                                    <MapPin className="w-3 h-3 text-green-500" />
                                                                    <span className={`text-gray-600 dark:text-muted ${
                                                                        isDarkMode ? 'text-gray-400' : 'text-gray-600 dark:text-muted'
                                                                    }`}>{load.pickup_address || load.origin || 'N/A'}</span>
                                                                </div>
                                                                <div className="flex items-center gap-2">
                                                                    <MapPin className="w-3 h-3 text-red-500" />
                                                                    <span className={`text-gray-600 dark:text-muted ${
                                                                        isDarkMode ? 'text-gray-400' : 'text-gray-600 dark:text-muted'
                                                                    }`}>{load.delivery_address || load.destination || 'N/A'}</span>
                                                                </div>
                                                                <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400">
                                                                    <span>{load.customer || 'N/A'}</span>
                                                                    <span>{load.rate ? `$${load.rate.toLocaleString()}` : 'N/A'}</span>
                                                                </div>
                                                            </div>

                                                            {((load.status || '').toLowerCase() === 'unassigned' || (load.status || '').toLowerCase() === 'pending') && vehicles && (
                                                                <div className="mt-3 pt-3 border-t">
                                                                    <select 
                                                                        className={`w-full px-3 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 ${
                                                                            isDarkMode ? 'bg-gray-800/40 text-white' : 'bg-white/10 text-gray-700 dark:text-white'
                                                                        }`}
                                                                        onChange={(e) => e.target.value && handleAssignLoad(load.id, e.target.value)}
                                                                    >
                                                                        <option value="">Assign vehicle...</option>
                                                                        {vehicles.filter(v => (v.status || '').toLowerCase() === 'available').map(vehicle => (
                                                                            <option key={vehicle.id} value={vehicle.id}>
                                                                                {vehicle.number || vehicle.id} - {vehicle.driver || 'Unknown Driver'}
                                                                            </option>
                                                                        ))}
                                                                    </select>
                                                                </div>
                                                            )}
                                                        </div>
                                                    ))
                                                )}
                                            </div>
                                        )}

                                        {selectedTab === 'vehicles' && (
                                            <div className="space-y-3">
                                                {!vehicles || vehicles.length === 0 ? (
                                                    <div className={`text-center py-8 ${
                                                        isDarkMode ? 'text-gray-400' : 'text-white/60'
                                                    }`}>
                                                        <Truck className="w-12 h-12 mx-auto mb-2 opacity-50" />
                                                        <p>No vehicles found</p>
                                                    </div>
                                                ) : (
                                                    vehicles.map((vehicle) => (
                                                        <div 
                                                            key={vehicle.id}
                                                            className={`border rounded-lg p-4 cursor-pointer transition-all hover:shadow-md ${
                                                                selectedVehicle === vehicle.id 
                                                                    ? 'ring-2 ring-primary bg-primary/10' 
                                                                    : isDarkMode 
                                                                        ? 'bg-gray-800/40 border-gray-600/50 hover:bg-gray-700/40' 
                                                                        : 'bg-white/10 border-white/20 hover:bg-white/20'
                                                            }`}
                                                            onClick={() => setSelectedVehicle(vehicle.id)}
                                                        >
                                                            <div className="flex items-start justify-between mb-2">
                                                                <div className="flex items-center gap-2">
                                                                    <Truck className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                                                                    <span className={`font-medium ${
                                                                        isDarkMode ? 'text-gray-200' : 'text-gray-700 dark:text-white'
                                                                    }`}>{vehicle.number || vehicle.id}</span>
                                                                </div>
                                                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(vehicle.status)}`}>
                                                                    {vehicle.status || 'Unknown'}
                                                                </span>
                                                            </div>
                                                            
                                                            <div className="space-y-2 text-sm">
                                                                <div className="flex items-center gap-2">
                                                                    <span className={`text-gray-600 dark:text-muted ${
                                                                        isDarkMode ? 'text-gray-400' : 'text-gray-600 dark:text-muted'
                                                                    }`}>{vehicle.driver || 'Unassigned'}</span>
                                                                </div>
                                                                <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400">
                                                                    <span>{vehicle.type || 'Unknown Type'}</span>
                                                                    <span>{vehicle.speed || 0} mph</span>
                                                                </div>
                                                                <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400">
                                                                    <span>Updated: {vehicle.lastUpdate || vehicle.last_update || 'N/A'}</span>
                                                                    <span className="flex items-center gap-1">
                                                                        <Navigation className="w-3 h-3" />
                                                                        {vehicle.heading || 0}°
                                                                    </span>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    ))
                                                )}
                                            </div>
                                        )}

                                        {selectedTab === 'routes' && (
                                            <div className="space-y-3">
                                                {!routes || routes.length === 0 ? (
                                                    <div className={`text-center py-8 ${
                                                        isDarkMode ? 'text-gray-400' : 'text-white/60'
                                                    }`}>
                                                        <Route className="w-12 h-12 mx-auto mb-2 opacity-50" />
                                                        <p>No routes found</p>
                                                    </div>
                                                ) : (
                                                    routes.map((route) => {
                                                        const isVisible = visibleRoutes.has(route.id);
                                                        const isActive = route.status === 'active' || route.status === 'ACTIVE';
                                                        const canToggle = !isActive;
                                                        
                                                        return (
                                                            <div 
                                                                key={route.id} 
                                                                className={`border rounded-lg p-4 transition-all ${
                                                                    canToggle ? 'cursor-pointer hover:shadow-md' : 'cursor-default'
                                                                } ${
                                                                    isVisible ? 'bg-white border-blue-200' : 'bg-gray-50 border-gray-200'
                                                                } ${
                                                                    isActive ? 'ring-2 ring-green-200' : ''
                                                                } ${
                                                                    isDarkMode 
                                                                        ? 'bg-gray-800/40 border-gray-600/50' 
                                                                        : 'bg-white/10 border-white/20'
                                                                }`}
                                                                onClick={() => toggleRouteVisibility(route.id, route.status)}
                                                            >
                                                                <div className="flex items-start justify-between mb-2">
                                                                    <div className="flex items-center gap-2">
                                                                        <div className="flex items-center gap-1">
                                                                            <Route className={`w-4 h-4 ${
                                                                                isVisible ? 'text-blue-500' : 'text-gray-400'
                                                                            }`} />
                                                                            <div className={`w-2 h-2 rounded-full ${
                                                                                isVisible ? 'bg-blue-500' : 'bg-gray-400'
                                                                            }`}></div>
                                                                        </div>
                                                                        <span className={`font-medium ${
                                                                            isVisible ? 'text-gray-900 dark:text-foreground' : 'text-gray-500 dark:text-gray-400'
                                                                        }`}>{route.name || route.id}</span>
                                                                        {isActive && (
                                                                            <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full font-medium">
                                                                                ALWAYS VISIBLE
                                                                            </span>
                                                                        )}
                                                                    </div>
                                                                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(route.status)}`}>
                                                                        {route.status || 'Unknown'}
                                                                    </span>
                                                                </div>
                                                                
                                                                <div className="space-y-2 text-sm">
                                                                    <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400">
                                                                        <span>Waypoints: {route.waypoints?.length || 0}</span>
                                                                        <span>Distance: {route.distance ? `${route.distance} km` : 'N/A'}</span>
                                                                    </div>
                                                                    <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400">
                                                                        <span>Efficiency: {route.efficiency || 'N/A'}%</span>
                                                                        <span>ETA: {route.estimated_time || route.estimatedTime || 'N/A'}</span>
                                                                    </div>
                                                                </div>
                                                                
                                                                {canToggle && (
                                                                    <div className="mt-2 pt-2 border-t">
                                                                        <span className="text-xs text-gray-400">
                                                                            Click to {isVisible ? 'hide' : 'show'} on map
                                                                        </span>
                                                                    </div>
                                                                )}
                                                            </div>
                                                        );
                                                    })
                                                )}
                                            </div>
                                        )}
                                    </>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DispatchPage;
