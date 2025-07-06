/**
 * Utility to decode WKB LINESTRING format for route geometry
 */

/**
 * Reverses hex byte order if needed based on endianness
 * @param {string} hex - Hex string to potentially reverse
 * @param {boolean} isLittleEndian - Whether the data is little endian
 * @returns {string} - Potentially reversed hex string
 */
function reverseHexIfNeeded(hex, isLittleEndian) {
    if (!isLittleEndian) return hex;

    // Reverse byte order for little endian
    let reversed = '';
    for (let i = hex.length - 2; i >= 0; i -= 2) {
        reversed += hex.substring(i, i + 2);
    }
    return reversed;
}

/**
 * Converts a hex string to a double precision floating point number
 * @param {string} hex - 16-character hex string representing a double
 * @param {boolean} isLittleEndian - Whether the bytes are in little endian order
 * @returns {number} - The decoded double value
 */
function hexToDouble(hex, isLittleEndian) {
    // Create ArrayBuffer and DataView for IEEE 754 double conversion
    const buffer = new ArrayBuffer(8);
    const view = new DataView(buffer);

    // Convert hex string to bytes and set them in the buffer
    for (let i = 0; i < 8; i++) {
        const byteIndex = isLittleEndian ? i : (7 - i);
        const hexIndex = i * 2;
        const byte = parseInt(hex.substring(hexIndex, hexIndex + 2), 16);
        view.setUint8(byteIndex, byte);
    }

    // Read as double in the correct endian format
    return view.getFloat64(0, isLittleEndian);
}

/**
 * Decodes a WKB LINESTRING hex string to extract array of coordinates
 * @param {string} wkbHex - The WKB hex string representing a LINESTRING
 * @returns {Array|null} - Array of {lat, lng} objects or null if invalid
 */
export const decodeWKBLineString = (wkbHex) => {
    try {
        if (!wkbHex || typeof wkbHex !== 'string') {
            return null;
        }

        // Remove any whitespace and convert to uppercase
        const hex = wkbHex.replace(/\s/g, '').toUpperCase();

        // Basic validation - WKB should be hex string
        if (!/^[0-9A-F]+$/.test(hex)) {
            return null;
        }

        // Parse WKB LINESTRING structure:
        // Byte 0: Byte order (01 = little endian, 00 = big endian)
        const byteOrder = hex.substring(0, 2);
        const isLittleEndian = byteOrder === '01';

        // Bytes 1-4: Geometry type (should be 2 for LINESTRING, with potential SRID flag)
        const geometryTypeHex = hex.substring(2, 10);
        const geometryType = parseInt(reverseHexIfNeeded(geometryTypeHex, isLittleEndian), 16);

        let offset = 10; // After byte order + geometry type

        // Check if SRID is present (0x20000000 flag in geometry type)
        if (geometryType & 0x20000000) {
            offset += 8; // skip SRID (4 bytes = 8 hex chars)
        }

        // Read number of points in the linestring (4 bytes = 8 hex chars)
        const numPointsHex = hex.substring(offset, offset + 8);
        const numPoints = parseInt(reverseHexIfNeeded(numPointsHex, isLittleEndian), 16);
        offset += 8;

        // Extract coordinate pairs
        const coordinates = [];
        for (let i = 0; i < numPoints; i++) {
            // Each point is 16 bytes (32 hex chars) - 8 bytes X, 8 bytes Y
            const xHex = hex.substring(offset, offset + 16);
            const yHex = hex.substring(offset + 16, offset + 32);
            offset += 32;

            const longitude = hexToDouble(xHex, isLittleEndian);
            const latitude = hexToDouble(yHex, isLittleEndian);

            // Validate coordinates are within valid ranges
            if (latitude >= -90 && latitude <= 90 && longitude >= -180 && longitude <= 180) {
                coordinates.push({
                    lat: latitude,
                    lng: longitude
                });
            }
        }

        return coordinates.length > 0 ? coordinates : null;
    } catch (error) {
        console.error('Error decoding WKB LINESTRING:', error, wkbHex);
        return null;
    }
};

/**
 * Converts route data with WKB geometry to coordinates for map rendering
 * @param {Object} route - Route object with route_geometry property
 * @returns {Array|null} - Array of {lat, lng} objects or null if invalid
 */
export const getRouteCoordinates = (route) => {
    if (!route || !route.route_geometry) {
        return null;
    }

    return decodeWKBLineString(route.route_geometry);
};
