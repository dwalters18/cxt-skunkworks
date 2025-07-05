import { useState, useCallback } from 'react';

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

export const useRouteOptimization = () => {
    const [optimizedRoutes, setOptimizedRoutes] = useState(new Map());
    const [isOptimizing, setIsOptimizing] = useState(new Set());
    const [optimizationError, setOptimizationError] = useState(null);

    // Helper function to parse WKT LINESTRING to Google Maps coordinates
    const parseWKTLineString = useCallback((wktString) => {
        if (!wktString || typeof wktString !== 'string') {
            return [];
        }

        const match = wktString.match(/LINESTRING\s*\(\s*([^)]+)\s*\)/i);
        if (!match) {
            return [];
        }

        const coordinatesString = match[1];
        const coordinatePairs = coordinatesString.split(',');
        
        return coordinatePairs.map(pair => {
            const [lng, lat] = pair.trim().split(/\s+/).map(Number);
            return { lat, lng };
        }).filter(coord => !isNaN(coord.lat) && !isNaN(coord.lng));
    }, []);

    // Get route coordinates from various formats
    const getRouteCoordinates = useCallback((routeDetails) => {
        if (!routeDetails) return [];

        // Try WKT LINESTRING format first
        if (routeDetails.geometry && typeof routeDetails.geometry === 'string') {
            const wktCoords = parseWKTLineString(routeDetails.geometry);
            if (wktCoords.length > 0) {
                return wktCoords;
            }
        }

        // Try coordinate array format
        if (Array.isArray(routeDetails.coordinates) && routeDetails.coordinates.length > 0) {
            return routeDetails.coordinates;
        }

        // Fallback to straight line between pickup and delivery
        if (routeDetails.pickup_location && routeDetails.delivery_location) {
            return [
                routeDetails.pickup_location,
                routeDetails.delivery_location
            ];
        }

        return [];
    }, [parseWKTLineString]);

    // Optimize route for a specific load
    const optimizeLoadRoute = useCallback(async (loadId, vehicleId, driverId = null) => {
        if (!loadId || !vehicleId) {
            setOptimizationError('Load ID and Vehicle ID are required for route optimization');
            return null;
        }

        // Add load to optimizing set
        setIsOptimizing(prev => new Set([...prev, loadId]));
        setOptimizationError(null);

        try {
            // Call route optimization API
            const optimizeResponse = await fetch(`${API_BASE}/api/routes/optimize-load`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    load_id: loadId,
                    vehicle_id: vehicleId,
                    driver_id: driverId
                }),
            });

            if (!optimizeResponse.ok) {
                throw new Error(`Optimization failed: ${optimizeResponse.status}`);
            }

            const optimizationResult = await optimizeResponse.json();
            
            if (!optimizationResult.route_id) {
                throw new Error('No route ID returned from optimization');
            }

            // Fetch detailed route information
            const routeResponse = await fetch(`${API_BASE}/api/routes/${optimizationResult.route_id}`);
            
            if (!routeResponse.ok) {
                throw new Error(`Failed to fetch route details: ${routeResponse.status}`);
            }

            const routeDetails = await routeResponse.json();
            
            // Store optimized route
            setOptimizedRoutes(prev => {
                const newMap = new Map(prev);
                newMap.set(loadId, {
                    ...routeDetails,
                    coordinates: getRouteCoordinates(routeDetails),
                    optimizationResult
                });
                return newMap;
            });

            return {
                success: true,
                routeDetails,
                optimizationResult
            };

        } catch (error) {
            console.error('Route optimization error:', error);
            setOptimizationError(error.message);
            return {
                success: false,
                error: error.message
            };
        } finally {
            // Remove load from optimizing set
            setIsOptimizing(prev => {
                const newSet = new Set(prev);
                newSet.delete(loadId);
                return newSet;
            });
        }
    }, [getRouteCoordinates]);

    // Clear optimization for a load
    const clearOptimization = useCallback((loadId) => {
        setOptimizedRoutes(prev => {
            const newMap = new Map(prev);
            newMap.delete(loadId);
            return newMap;
        });
    }, []);

    // Clear all optimizations
    const clearAllOptimizations = useCallback(() => {
        setOptimizedRoutes(new Map());
        setIsOptimizing(new Set());
        setOptimizationError(null);
    }, []);

    // Check if a load is being optimized
    const isLoadOptimizing = useCallback((loadId) => {
        return isOptimizing.has(loadId);
    }, [isOptimizing]);

    // Get optimization for a load
    const getOptimization = useCallback((loadId) => {
        return optimizedRoutes.get(loadId);
    }, [optimizedRoutes]);

    return {
        // State
        optimizedRoutes,
        isOptimizing,
        optimizationError,
        
        // Methods
        optimizeLoadRoute,
        clearOptimization,
        clearAllOptimizations,
        isLoadOptimizing,
        getOptimization,
        getRouteCoordinates,
        parseWKTLineString
    };
};
