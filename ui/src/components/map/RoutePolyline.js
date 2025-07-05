import React from 'react';
import { Polyline } from '@react-google-maps/api';

const RoutePolyline = ({ 
    coordinates, 
    loadId, 
    isOptimized = false,
    color = '#3B82F6',
    opacity = 0.8 
}) => {
    if (!coordinates || coordinates.length < 2) {
        return null;
    }

    // Enhanced styling for optimized routes
    const polylineOptions = {
        path: coordinates,
        geodesic: true,
        strokeColor: isOptimized ? '#10B981' : color, // Green for optimized, blue for regular
        strokeOpacity: opacity,
        strokeWeight: isOptimized ? 4 : 3,
        icons: isOptimized ? [
            {
                icon: {
                    path: 'M 0,-1 0,1',
                    strokeOpacity: 1,
                    strokeColor: '#10B981',
                    scale: 3,
                },
                offset: '0%',
                repeat: '20px',
            },
        ] : undefined,
    };

    return (
        <Polyline
            options={polylineOptions}
            onClick={() => {
                // Could add click handler for route details
                console.log(`Route clicked for load ${loadId}`);
            }}
        />
    );
};

export default RoutePolyline;
