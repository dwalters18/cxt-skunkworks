# Route Optimization System Setup

This document explains how to configure and use the street-level route optimization feature in the TMS dispatch interface.

## Overview
The Route Optimization Service calculates the most efficient routes for **Load + Vehicle** combinations using Google Maps API, with optional driver assignment for maximum operational flexibility.

## Architecture Philosophy

### Core Optimization: Load ↔ Vehicle
- **Primary Focus**: Optimize routes based on load requirements and vehicle capabilities
- **Independence**: Route optimization works without driver assignment
- **Flexibility**: Driver assignment is optional and can change during execution

### Driver Assignment: Optional & Flexible
- **Industry Reality**: Drivers have high turnover and shift changes
- **Operational Flexibility**: Routes can be executed by different drivers
- **Future Ready**: Supports autonomous vehicle integration

## 🔧 Setup Requirements

### 1. Google Maps API Key

You'll need a Google Maps API key with the following APIs enabled:

1. **Directions API** (Required) - For route calculations
2. **Maps JavaScript API** (Required) - For frontend map display
3. **Places API** (Optional) - For enhanced location search

#### Getting Your API Key:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing project
3. Enable the required APIs listed above
4. Go to "Credentials" → "Create Credentials" → "API Key"
5. Restrict the API key to specific APIs for security
6. Copy your API key

### 2. Environment Configuration

#### Backend Configuration:
Update your `server/app/.env` file:
```bash
# Google Maps API Key for route optimization
MAPS_API_KEY=your_actual_google_maps_api_key_here
```

#### Frontend Configuration:
Update your `ui/.env` file (copy from `ui/.env.example`):
```bash
# Google Maps API Key for frontend maps
REACT_APP_GOOGLE_MAPS_API_KEY=your_actual_google_maps_api_key_here
```

### 3. Docker Environment

The Docker Compose configuration will automatically pick up environment variables from your `.env` files:

- Backend uses `server/app/.env` for `MAPS_API_KEY`  
- Frontend uses `ui/.env` for `REACT_APP_GOOGLE_MAPS_API_KEY`

Simply run:
```bash
docker-compose up --build
```

## 🚀 How to Use

### 1. Accessing Route Optimization

1. Open the dispatch map interface
2. Enable the "Routes" filter to show route lines
3. Look for loads with pickup and delivery locations

### 2. Optimizing a Route

**Option A: From Map**
- Find a load with a dashed route line (non-optimized)
- Click the "🗺️ Optimize Route" button that appears

**Option B: From Info Window**
- Click on a load marker to open the info window
- Click "🗺️ Optimize Route" button in the load details

### 3. Visual Indicators

The map legend shows different route types:

- **Solid thick lines**: Optimized routes with street-level accuracy
- **Dashed thin lines**: Straight-line routes (non-optimized)
- **Green routes**: High optimization scores
- **Yellow/Amber routes**: Moderate optimization scores

### 4. Route Information

Optimized routes display:
- **Distance**: Actual driving distance in miles
- **Duration**: Estimated travel time considering traffic
- **Optimization Score**: Efficiency rating (0-100)
- **Fuel Estimate**: Projected fuel consumption
- **Turn-by-turn directions**: Available via API

## 🚀 API Endpoints

### Route Optimization Endpoint
**POST** `/api/routes/optimize-load`

Optimizes a route for a specific load and vehicle combination.

#### Request Body:
```json
{
  "load_id": "uuid",
  "vehicle_id": "uuid", 
  "driver_id": "uuid (optional)",
  "priority": "normal|urgent|eco (optional, default: normal)"
}
```

#### Response:
```json
{
  "success": true,
  "message": "Route optimization completed",
  "route_id": "uuid",
  "distance_miles": 42.3,
  "duration_minutes": 65,
  "optimization_score": 87.5,
  "route_geometry": "LINESTRING(...)"
}
```

### Route Details Endpoint
**GET** `/api/routes/{route_id}`

Returns detailed route information including coordinates and turn-by-turn directions.

#### Response:
```json
{
  "route_id": "uuid",
  "load_number": "L123456",
  "driver_name": "John Smith (optional)",
  "vehicle": "2023 Freightliner Cascadia",
  "distance_miles": 42.3,
  "duration_minutes": 65,
  "optimization_score": 87.5,
  "status": "PLANNED",
  "route_coordinates": [[lat, lng], [lat, lng], ...],
  "fuel_estimate": 8.2,
  "toll_estimate": 15.50
}
```

## 📡 Event Schema

### ROUTE_OPTIMIZED Event
Published to Kafka topic `tms.routes` when route optimization completes:

```json
{
  "eventType": "ROUTE_OPTIMIZED",
  "eventVersion": "1.0", 
  "entityType": "ROUTE",
  "entityId": "route-uuid",
  "data": {
    "route_id": "uuid",
    "load_ids": ["uuid"],
    "vehicle_id": "uuid",
    "driver_id": "uuid (optional)",
    "original_distance": 45.2,
    "optimized_distance": 42.3,
    "time_saved": 8.5,
    "fuel_saved": 1.2,
    "algorithm_used": "google_maps_api",
    "optimization_score": 87.5,
    "traffic_considered": true,
    "steps_count": 12,
    "encoded_polyline": "google_maps_encoded_polyline_string"
  }
}
```

## 🗄️ Database Schema

### Routes Table Structure
The routes table supports our flexible driver assignment architecture:

```sql
CREATE TABLE routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    load_id UUID NOT NULL REFERENCES loads(id),
    driver_id UUID REFERENCES drivers(id),  -- NULLABLE for flexibility
    vehicle_id UUID NOT NULL REFERENCES vehicles(id),
    origin_location GEOGRAPHY(POINT, 4326),
    destination_location GEOGRAPHY(POINT, 4326),
    route_geometry GEOMETRY(LINESTRING, 4326),  -- PostGIS route coordinates
    planned_distance_miles DECIMAL(10,2),
    planned_duration_minutes INTEGER,
    optimization_score DECIMAL(5,2),
    fuel_estimate DECIMAL(8,2),
    toll_estimate DECIMAL(8,2),
    status route_status_enum DEFAULT 'PLANNED',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Key Design Decisions:
- **driver_id is NULLABLE**: Routes can exist without driver assignment
- **PostGIS LINESTRING**: Stores actual route coordinates for map display
- **route_status_enum**: PLANNED, IN_PROGRESS, COMPLETED, CANCELLED
- **optimization_score**: 0-100 rating of route efficiency

## 🔔 Real-Time Events

The system publishes `ROUTE_OPTIMIZED` events when routes are calculated:

```json
{
  "event_type": "ROUTE_OPTIMIZED",
  "route_id": "uuid",
  "load_id": "uuid", 
  "vehicle_id": "uuid",
  "driver_id": "uuid",  # May be null
  "optimization_data": {
    "distance_miles": 162.35,
    "duration_minutes": 152,
    "fuel_saved": 3.2,
    "time_saved": 18,
    "algorithm_used": "google_maps_directions"
  }
}
```

## 🚨 Troubleshooting

### Common Issues:

1. **Google Maps API quota exceeded**
   - Check your API usage in Google Cloud Console
   - Consider implementing rate limiting
   - Monitor daily quotas and billing

2. **Route optimization returns straight-line routes**
   - Verify MAPS_API_KEY is set correctly
   - Check API key has Directions API enabled
   - Review API key restrictions (HTTP referrers, IP addresses)

3. **Database errors with route geometry**
   - Ensure PostGIS extension is installed
   - Verify TimescaleDB image includes PostGIS (`timescale/timescaledb-ha:pg16`)

4. **Event publishing fails**
   - Check Kafka connectivity
   - Verify event schema matches PRD Events Schema
   - Monitor Kafka topic `tms.routes` for messages

### API Key Security:

- Never commit API keys to version control
- Use environment variables for all deployments
- Restrict API keys to specific APIs and domains
- Monitor API usage in Google Cloud Console

## 🎯 Best Practices

1. **Route Planning**: Optimize routes during load assignment for best results
2. **Batch Operations**: Consider optimizing multiple routes simultaneously
3. **Traffic Timing**: Routes calculated during peak hours include traffic delays
4. **Monitoring**: Track optimization scores to measure system efficiency
5. **Fallbacks**: System gracefully falls back to straight-line routes if Google Maps is unavailable

## 🔮 Future Enhancements

Potential improvements include:

- **Multi-stop optimization**: Optimize routes with multiple waypoints
- **Driver preferences**: Consider driver-specific routing preferences
- **Vehicle constraints**: Factor in vehicle size/weight restrictions
- **Cost optimization**: Balance distance vs. fuel costs vs. tolls
- **Historical analysis**: Learn from past route performance
