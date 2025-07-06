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
                return {
                    path: 'M 0,-24 C -8,-24 -12,-16 -12,-8 L -12,8 C -12,16 -8,24 0,24 C 8,24 12,16 12,8 L 12,-8 C 12,-16 8,-24 0,-24 Z M 0,-16 C 4,-16 8,-12 8,-8 L 8,8 C 8,12 4,16 0,16 C -4,16 -8,12 -8,8 L -8,-8 C -8,-12 -4,-16 0,-16 Z',
                    fillColor: data?.status === 'available' ? '#10B981' : data?.status === 'busy' ? '#F59E0B' : '#EF4444',
                    fillOpacity: 1,
                    strokeColor: '#FFFFFF',
                    strokeWeight: 2,
                    scale: 1,
                    anchor: { x: 0, y: 24 }
                };
            case 'load':
                return {
                    path: 'M -12,-12 L 12,-12 L 12,12 L -12,12 Z M -8,-8 L 8,-8 L 8,8 L -8,8 Z',
                    fillColor: data?.status === 'available' ? '#3B82F6' : data?.status === 'assigned' ? '#8B5CF6' : '#6B7280',
                    fillOpacity: 1,
                    strokeColor: '#FFFFFF',
                    strokeWeight: 2,
                    scale: 1.2,
                    anchor: { x: 0, y: 0 }
                };
            case 'event':
                return {
                    path: 'M 0,-20 C -11,-20 -20,-11 -20,0 C -20,11 -11,20 0,20 C 11,20 20,11 20,0 C 20,-11 11,-20 0,-20 Z',
                    fillColor: getEventColor(data?.event_type),
                    fillOpacity: 0.8,
                    strokeColor: '#FFFFFF',
                    strokeWeight: 2,
                    scale: 0.8,
                    anchor: { x: 0, y: 0 }
                };
            default:
                return {
                    path: 'M 0,-20 C -11,-20 -20,-11 -20,0 C -20,11 -11,20 0,20 C 11,20 20,11 20,0 C 20,-11 11,-20 0,-20 Z',
                    fillColor: '#6B7280',
                    fillOpacity: 1,
                    strokeColor: '#FFFFFF',
                    strokeWeight: 2,
                    scale: 1,
                    anchor: { x: 0, y: 0 }
                };
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

    // Add selection highlight
    const markerOptions = getMarkerOptions();
    if (isSelected) {
        markerOptions.strokeColor = '#FBBF24';
        markerOptions.strokeWeight = 4;
        markerOptions.scale = markerOptions.scale * 1.2;
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
