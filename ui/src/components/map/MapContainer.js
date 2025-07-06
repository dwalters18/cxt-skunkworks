import React, { useMemo, useState } from 'react';
import { GoogleMap, useJsApiLoader } from '@react-google-maps/api';
import MapMarker from './MapMarker';
import LoadInfoWindow from './LoadInfoWindow';
import RoutePolyline from './RoutePolyline';
import { getRouteCoordinates } from '../../utils/routeDecoder';

const GOOGLE_MAPS_LIBRARIES = ['geometry', 'drawing', 'marker'];

const MapContainer = ({
    vehicles = [],
    loads = [],
    routes = [],
    events,
    drivers,
    selectedLoad,
    selectedVehicle,
    selectedVehicleForOptimization,
    optimizedRoutes,
    activeFilters,
    visibleRoutes,
    onLoadSelect,
    onVehicleSelect,
    onVehicleSelectForOptimization,
    onOptimizeRoute,
    isOptimizing,
    onCloseInfoWindow
}) => {
    const [map, setMap] = useState(null);

    // Google Maps configuration
    const defaultCenter = useMemo(() => ({ lat: 39.8283, lng: -98.5795 }), []);
    const mapOptions = useMemo(() => ({
        disableDefaultUI: false,
        clickableIcons: true,
        scrollwheel: true,
        styles: [
            {
                featureType: "poi",
                elementType: "labels",
                stylers: [{ visibility: "off" }]
            }
        ]
    }), []);

    const { isLoaded } = useJsApiLoader({
        id: 'google-map-script',
        googleMapsApiKey: process.env.REACT_APP_GOOGLE_MAPS_API_KEY,
        libraries: GOOGLE_MAPS_LIBRARIES
    });

    const onLoad = React.useCallback(function callback(map) {
        setMap(map);
    }, []);

    const onUnmount = React.useCallback(function callback(map) {
        setMap(null);
    }, []);

    // Handle marker clicks
    const handleMarkerClick = (data, type) => {
        if (type === 'load') {
            onLoadSelect(data);
        } else if (type === 'vehicle') {
            onVehicleSelect(data);
        }
    };

    if (!isLoaded) {
        return (
            <div className="w-full h-full flex items-center justify-center bg-gray-100">
                <div className="text-center">
                    <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading map...</p>
                </div>
            </div>
        );
    }

    return (
        <GoogleMap
            mapContainerStyle={{ width: '100%', height: '100%' }}
            center={defaultCenter}
            zoom={6}
            onLoad={onLoad}
            onUnmount={onUnmount}
            options={mapOptions}
        >
            {/* Vehicle Markers */}
            {activeFilters.showVehicles && vehicles.map((vehicle) => (
                <MapMarker
                    key={`vehicle-${vehicle.id}`}
                    position={vehicle.current_location}
                    type="vehicle"
                    data={vehicle}
                    onClick={handleMarkerClick}
                    isSelected={selectedVehicle?.id === vehicle.id}
                />
            ))}

            {/* Load Markers */}
            {activeFilters.showLoads && loads.map((load) => (
                <MapMarker
                    key={`load-${load.id}`}
                    position={load.pickup_location}
                    type="load"
                    data={load}
                    onClick={handleMarkerClick}
                    isSelected={selectedLoad?.id === load.id}
                />
            ))}

            {/* Event Markers */}
            {activeFilters.eventTypes.includes('all') && events.map((event, index) => (
                <MapMarker
                    key={`event-${index}`}
                    position={event.location}
                    type="event"
                    data={event}
                    onClick={handleMarkerClick}
                />
            ))}

            {/* Regular Route Polylines */}
            {activeFilters.showRoutes && routes.map((route) => {
                const coordinates = getRouteCoordinates(route);
                if (!coordinates || coordinates.length < 2) return null;

                // Check if route should be visible
                const isActive = route.status === 'active' || route.status === 'ACTIVE';
                const shouldShow = isActive || (visibleRoutes && visibleRoutes.has(route.id));
                
                if (!shouldShow) return null;

                return (
                    <RoutePolyline
                        key={`regular-route-${route.id}`}
                        coordinates={coordinates}
                        loadId={route.load_id || route.id}
                        isOptimized={false}
                        color={isActive ? '#EF4444' : '#3B82F6'} // Red for active, blue for others
                    />
                );
            })}

            {/* Optimized Route Polylines */}
            {activeFilters.showRoutes && Array.from(optimizedRoutes.entries()).map(([loadId, routeData]) => (
                <RoutePolyline
                    key={`route-${loadId}`}
                    coordinates={routeData.coordinates}
                    loadId={loadId}
                    isOptimized={true}
                />
            ))}

            {/* Load Info Window */}
            {selectedLoad && (
                <LoadInfoWindow
                    load={selectedLoad}
                    onClose={onCloseInfoWindow}
                    vehicles={vehicles}
                    drivers={drivers}
                    selectedVehicleForOptimization={selectedVehicleForOptimization}
                    onVehicleSelect={onVehicleSelectForOptimization}
                    onOptimizeRoute={onOptimizeRoute}
                    isOptimizing={isOptimizing && isOptimizing.has(selectedLoad.id)}
                    optimizedRoute={optimizedRoutes.get(selectedLoad.id)}
                />
            )}
        </GoogleMap>
    );
};

export default MapContainer;
