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

        // Parse WKB structure:
        // Byte 0: Byte order (01 = little endian, 00 = big endian)
        const byteOrder = hex.substring(0, 2);
        const isLittleEndian = byteOrder === '01';
        
        // Bytes 1-4: Geometry type (with potential SRID flag)
        const geometryTypeHex = hex.substring(2, 10);
        const geometryType = parseInt(reverseHexIfNeeded(geometryTypeHex, isLittleEndian), 16);
        
        let offset = 10; // After byte order + geometry type
        
        // Check if SRID is present (0x20000000 flag in geometry type)
        if (geometryType & 0x20000000) {
            offset += 8; // skip SRID (4 bytes = 8 hex chars)
        }
        
        // Extract coordinates (8 bytes each = 16 hex chars)
        const xHex = hex.substring(offset, offset + 16);
        const yHex = hex.substring(offset + 16, offset + 32);
        
        // Convert hex to double precision floating point
        const longitude = hexToDouble(xHex, isLittleEndian);
        const latitude = hexToDouble(yHex, isLittleEndian);
        
        // Debug logging
        // console.log('WKB Debug:', {
        //     hex: hex.substring(0, 50) + '...',
        //     byteOrder,
        //     geometryType: geometryType.toString(16),
        //     longitude,
        //     latitude
        // });
        
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
