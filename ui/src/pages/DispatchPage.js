import React, { useState, useEffect, useCallback } from 'react';
import DispatchMapView from '../components/DispatchMapView';
import FloatingControlPanel from '../components/dispatch/FloatingControlPanel';
import { useMapData } from '../hooks/useMapData';
import { useDarkMode } from '../contexts/DarkModeContext';
// Icons now handled by FloatingControlPanel component

const DispatchPage = () => {
    const { isDarkMode } = useDarkMode();
    const [selectedLoad, setSelectedLoad] = useState(null);
    const [selectedVehicle, setSelectedVehicle] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');
    const [visibleRoutes, setVisibleRoutes] = useState(new Set());
    const [mapRef, setMapRef] = useState(null);

    // Use the existing useMapData hook to get real data
    const {
        loads,
        vehicles,
        routes,
        isLoading: dataLoading,
        // Fetch functions
        fetchLoads,
        fetchVehicles,
        fetchRoutes
    } = useMapData();

    // Combined fetch function
    const fetchMapData = useCallback(async () => {
        await Promise.all([
            fetchLoads(),
            fetchVehicles(),
            fetchRoutes()
        ]);
    }, [fetchLoads, fetchVehicles, fetchRoutes]);

    // Initialize data on component mount
    useEffect(() => {
        fetchMapData();
        const interval = setInterval(fetchMapData, 5000);
        return () => clearInterval(interval);
    }, [fetchMapData]);

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

    // Map pan and zoom functionality
    const panToLocation = (lat, lng, zoom = 15) => {
        if (mapRef && lat && lng) {
            mapRef.panTo({ lat, lng });
            mapRef.setZoom(zoom);
        }
    };

    // Helper function to get coordinates from entity
    const getEntityCoordinates = (entity, type) => {
        if (type === 'load') {
            // Try pickup location first, then delivery location
            const pickup = entity.pickup_location || entity.pickupLocation;
            const delivery = entity.delivery_location || entity.deliveryLocation;
            
            if (pickup && pickup.lat && pickup.lng) {
                return { lat: pickup.lat, lng: pickup.lng };
            } else if (delivery && delivery.lat && delivery.lng) {
                return { lat: delivery.lat, lng: delivery.lng };
            }
        } else if (type === 'vehicle') {
            const location = entity.current_location || entity.currentLocation || entity.location;
            if (location && location.lat && location.lng) {
                return { lat: location.lat, lng: location.lng };
            }
        }
        return null;
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
                <DispatchMapView 
                    visibleRoutes={visibleRoutes} 
                    onMapLoad={setMapRef}
                    isDarkMode={isDarkMode} 
                />

                {/* Floating Control Panel */}
                <FloatingControlPanel 
                    isDarkMode={isDarkMode}
                    loads={loads}
                    vehicles={vehicles}
                    routes={routes}
                    visibleRoutes={visibleRoutes}
                    selectedLoad={selectedLoad}
                    selectedVehicle={selectedVehicle}
                    searchTerm={searchTerm}
                    setSearchTerm={setSearchTerm}
                    statusFilter={statusFilter}
                    setStatusFilter={setStatusFilter}
                    setSelectedLoad={setSelectedLoad}
                    setSelectedVehicle={setSelectedVehicle}
                    panToLocation={panToLocation}
                    toggleRouteVisibility={toggleRouteVisibility}
                    handleAssignLoad={handleAssignLoad}
                    dataLoading={dataLoading}
                    getEntityCoordinates={getEntityCoordinates}
                />
            </div>
        </div>
    );
};

export default DispatchPage;
