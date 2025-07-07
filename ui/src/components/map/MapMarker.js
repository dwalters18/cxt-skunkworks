import React from 'react';
import { Marker } from '@react-google-maps/api';
import { normalizePosition } from '../../utils/wkbDecoder';

const MapMarker = ({
    position,
    type,
    data,
    onClick,
    isSelected = false
}) => {
    // Convert position data to Google Maps LatLngLiteral format
    const getValidPosition = (pos) => {
        if (!pos) return null;

        // Use the new normalizePosition utility that handles WKB, {latitude, longitude}, and {lat, lng} formats
        const validPos = normalizePosition(pos);

        if (!validPos) {
            console.warn('Invalid position data for marker:', pos);
            return null;
        }

        return validPos;
    };
    
    const validPosition = getValidPosition(position);
    
    // Don't render marker if position is invalid
    if (!validPosition) {
        return null;
    }
    // Define marker icons and colors based on type
    const getMarkerOptions = () => {
        switch (type) {
            case 'vehicle':
                // Enhanced truck icon with cab and trailer
                return {
                    path: 'M -20,-8 L -16,-8 L -16,-12 L -4,-12 L -4,-8 L 8,-8 L 8,-4 L 20,-4 L 20,8 L 16,8 L 16,12 L 12,12 L 12,8 L 4,8 L 4,12 L 0,12 L 0,8 L -12,8 L -12,12 L -16,12 L -16,8 L -20,8 Z M -12,-8 L -8,-8 L -8,-4 L -12,-4 Z M 2,8 C 2,10 0,12 -2,12 C -4,12 -6,10 -6,8 C -6,6 -4,4 -2,4 C 0,4 2,6 2,8 Z M 18,8 C 18,10 16,12 14,12 C 12,12 10,10 10,8 C 10,6 12,4 14,4 C 16,4 18,6 18,8 Z',
                    fillColor: getVehicleColor(data?.status),
                    fillOpacity: 1,
                    strokeColor: '#FFFFFF',
                    strokeWeight: 2,
                    scale: 1.2,
                    anchor: { x: 0, y: 0 }
                };
            case 'load':
                // Enhanced package/cargo icon
                return {
                    path: 'M -12,-12 L 12,-12 L 12,-8 L 8,-8 L 8,-4 L 12,-4 L 12,12 L -12,12 L -12,-4 L -8,-4 L -8,-8 L -12,-8 Z M -8,-8 L 8,-8 L 8,-4 L -8,-4 Z M -6,2 L 6,2 M -6,6 L 6,6',
                    fillColor: getLoadColor(data?.status),
                    fillOpacity: 1,
                    strokeColor: '#FFFFFF',
                    strokeWeight: 2,
                    scale: 1.3,
                    anchor: { x: 0, y: 0 }
                };
            case 'driver':
                // Driver/person icon
                return {
                    path: 'M 0,-16 C 3,-16 6,-13 6,-10 C 6,-7 3,-4 0,-4 C -3,-4 -6,-7 -6,-10 C -6,-13 -3,-16 0,-16 Z M -8,0 C -8,0 -6,2 0,2 C 6,2 8,0 8,0 L 8,16 L 4,16 L 4,8 L -4,8 L -4,16 L -8,16 Z',
                    fillColor: getDriverColor(data?.status),
                    fillOpacity: 1,
                    strokeColor: '#FFFFFF',
                    strokeWeight: 2,
                    scale: 1.1,
                    anchor: { x: 0, y: 16 }
                };
            case 'event':
                return {
                    path: 'M 0,-16 C -9,-16 -16,-9 -16,0 C -16,9 -9,16 0,16 C 9,16 16,9 16,0 C 16,-9 9,-16 0,-16 Z M 0,-8 L 0,0 L 6,6',
                    fillColor: getEventColor(data?.event_type),
                    fillOpacity: 0.9,
                    strokeColor: '#FFFFFF',
                    strokeWeight: 2,
                    scale: 0.9,
                    anchor: { x: 0, y: 0 }
                };
            default:
                return {
                    path: 'M 0,-16 C -9,-16 -16,-9 -16,0 C -16,9 -9,16 0,16 C 9,16 16,9 16,0 C 16,-9 9,-16 0,-16 Z',
                    fillColor: '#6B7280',
                    fillOpacity: 1,
                    strokeColor: '#FFFFFF',
                    strokeWeight: 2,
                    scale: 1,
                    anchor: { x: 0, y: 0 }
                };
        }
    };

    // Enhanced vehicle status colors
    const getVehicleColor = (status) => {
        switch (status) {
            case 'available':
                return '#10B981'; // Bright green
            case 'busy':
            case 'in_transit':
                return '#F59E0B'; // Orange
            case 'maintenance':
                return '#EF4444'; // Red
            case 'offline':
                return '#6B7280'; // Gray
            default:
                return '#8B5CF6'; // Purple
        }
    };

    // Enhanced load status colors
    const getLoadColor = (status) => {
        switch (status) {
            case 'available':
            case 'pending':
                return '#3B82F6'; // Blue
            case 'assigned':
                return '#8B5CF6'; // Purple
            case 'picked_up':
            case 'in_transit':
                return '#F59E0B'; // Orange
            case 'delivered':
                return '#10B981'; // Green
            case 'cancelled':
                return '#EF4444'; // Red
            default:
                return '#6B7280'; // Gray
        }
    };

    // Driver status colors
    const getDriverColor = (status) => {
        switch (status) {
            case 'available':
                return '#10B981'; // Green
            case 'driving':
            case 'on_duty':
                return '#3B82F6'; // Blue
            case 'off_duty':
                return '#F59E0B'; // Orange
            case 'sleeper_berth':
                return '#8B5CF6'; // Purple
            default:
                return '#6B7280'; // Gray
        }
    };

    // Get event type colors
    const getEventColor = (eventType) => {
        switch (eventType) {
            case 'delivery':
                return '#10B981'; // Green
            case 'pickup':
                return '#3B82F6'; // Blue  
            case 'delay':
                return '#F59E0B'; // Yellow
            case 'breakdown':
                return '#EF4444'; // Red
            case 'traffic':
                return '#F97316'; // Orange
            default:
                return '#6B7280'; // Gray
        }
    };

    // Enhanced selection highlight with animation and glow
    const markerOptions = getMarkerOptions();
    if (isSelected) {
        markerOptions.strokeColor = '#FBBF24'; // Bright yellow
        markerOptions.strokeWeight = 4;
        markerOptions.scale = markerOptions.scale * 1.3; // Make selected markers larger
        // Add a pulsing shadow effect
        markerOptions.shadowColor = '#FBBF24';
        markerOptions.shadowOpacity = 0.6;
        markerOptions.shadowBlur = 10;
    }

    const handleClick = () => {
        if (onClick) {
            onClick(data, type);
        }
    };

    return (
        <Marker
            position={validPosition}
            icon={markerOptions}
            onClick={handleClick}
            title={getMarkerTitle()}
            animation={isSelected ? window.google?.maps?.Animation?.BOUNCE : null}
        />
    );

    function getMarkerTitle() {
        switch (type) {
            case 'vehicle':
                return `Vehicle: ${data?.license_plate || 'Unknown'} (${data?.status || 'Unknown'})`;
            case 'load':
                return `Load #${data?.id || 'Unknown'} (${data?.status || 'Unknown'})`;
            case 'event':
                return `Event: ${data?.event_type || 'Unknown'} - ${data?.description || ''}`;
            default:
                return 'Map Marker';
        }
    }
};

export default MapMarker;
