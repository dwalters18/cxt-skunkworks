/**
 * Utility to decode WKB (Well-Known Binary) format to latitude/longitude coordinates
 * WKB format is commonly used in PostGIS and other spatial databases
 */

/**
 * Decodes a WKB hex string to extract latitude and longitude coordinates
 * @param {string} wkbHex - The WKB hex string
 * @returns {Object|null} - {lat, lng} object or null if invalid
 */
export const decodeWKB = (wkbHex) => {
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

        // For POINT geometry, the structure is:
        // - Byte order (1 byte)
        // - Geometry type (4 bytes)
        // - SRID (4 bytes, if present)
        // - X coordinate (8 bytes - longitude)
        // - Y coordinate (8 bytes - latitude)

        // Skip byte order (2 chars), geometry type (8 chars), and SRID if present
        let offset = 2; // byte order
        offset += 8; // geometry type

        // Check if SRID is present (geometry type will have 0x20000000 flag)
        const geometryType = parseInt(hex.substring(2, 10), 16);
        if (geometryType & 0x20000000) {
            offset += 8; // skip SRID
        }

        // Extract X (longitude) and Y (latitude) coordinates
        const xHex = hex.substring(offset, offset + 16);
        const yHex = hex.substring(offset + 16, offset + 32);

        // Convert hex to double precision floating point
        const longitude = hexToDouble(xHex);
        const latitude = hexToDouble(yHex);

        // Validate coordinates are within valid ranges
        if (latitude < -90 || latitude > 90 || longitude < -180 || longitude > 180) {
            console.warn('Decoded coordinates out of valid range:', { latitude, longitude });
            return null;
        }

        return {
            lat: latitude,
            lng: longitude
        };
    } catch (error) {
        console.error('Error decoding WKB:', error, wkbHex);
        return null;
    }
};

/**
 * Converts a hex string to a double precision floating point number
 * @param {string} hex - 16-character hex string representing a double
 * @returns {number} - The decoded double value
 */
function hexToDouble(hex) {
    // Convert hex string to byte array
    const bytes = [];
    for (let i = 0; i < hex.length; i += 2) {
        bytes.push(parseInt(hex.substr(i, 2), 16));
    }

    // Create ArrayBuffer and DataView for IEEE 754 double conversion
    const buffer = new ArrayBuffer(8);
    const view = new DataView(buffer);

    // Set bytes in little-endian order (typical for WKB)
    for (let i = 0; i < 8; i++) {
        view.setUint8(i, bytes[i]);
    }

    // Read as double in little-endian format
    return view.getFloat64(0, true);
}

/**
 * Helper function to convert various position formats to {lat, lng}
 * Handles WKB strings, {latitude, longitude}, and {lat, lng} formats
 * @param {string|Object} position - Position data in various formats
 * @returns {Object|null} - {lat, lng} object or null if invalid
 */
export const normalizePosition = (position) => {
    if (!position) return null;

    // Handle WKB string format
    if (typeof position === 'string') {
        return decodeWKB(position);
    }

    // Handle {latitude, longitude} format
    if (position.latitude !== undefined && position.longitude !== undefined) {
        return {
            lat: parseFloat(position.latitude),
            lng: parseFloat(position.longitude)
        };
    }

    // Handle {lat, lng} format
    if (position.lat !== undefined && position.lng !== undefined) {
        return {
            lat: parseFloat(position.lat),
            lng: parseFloat(position.lng)
        };
    }

    return null;
};
