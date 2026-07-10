/**
 * Dispatch map — Austin demo world.
 *
 * Renders the depot, live driver positions, route stops (numbered, colored by
 * status), route polylines through stop sequences, and unassigned order pickups.
 * Pure presentation: all data arrives via props; live movement comes from the
 * parent feeding driver positions out of the WebSocket event feed.
 */
import React, { useMemo, useCallback, useState } from 'react';
import { GoogleMap, Marker, Polyline, InfoWindow, useJsApiLoader } from '@react-google-maps/api';

const GOOGLE_MAPS_LIBRARIES = ['geometry', 'marker'];

// Austin, TX — the deterministic seed world lives here.
export const AUSTIN_CENTER = { lat: 30.2672, lng: -97.7431 };

const darkMapStyles = [
  { elementType: 'geometry', stylers: [{ color: '#242f3e' }] },
  { elementType: 'labels.text.stroke', stylers: [{ color: '#242f3e' }] },
  { elementType: 'labels.text.fill', stylers: [{ color: '#746855' }] },
  { featureType: 'administrative.locality', elementType: 'labels.text.fill', stylers: [{ color: '#d59563' }] },
  { featureType: 'poi', elementType: 'labels', stylers: [{ visibility: 'off' }] },
  { featureType: 'poi.park', elementType: 'geometry', stylers: [{ color: '#263c3f' }] },
  { featureType: 'road', elementType: 'geometry', stylers: [{ color: '#38414e' }] },
  { featureType: 'road', elementType: 'geometry.stroke', stylers: [{ color: '#212a37' }] },
  { featureType: 'road', elementType: 'labels.text.fill', stylers: [{ color: '#9ca5b3' }] },
  { featureType: 'road.highway', elementType: 'geometry', stylers: [{ color: '#746855' }] },
  { featureType: 'road.highway', elementType: 'geometry.stroke', stylers: [{ color: '#1f2835' }] },
  { featureType: 'transit', elementType: 'geometry', stylers: [{ color: '#2f3948' }] },
  { featureType: 'water', elementType: 'geometry', stylers: [{ color: '#17263c' }] },
  { featureType: 'water', elementType: 'labels.text.fill', stylers: [{ color: '#515c6d' }] },
];

const lightMapStyles = [{ featureType: 'poi', elementType: 'labels', stylers: [{ visibility: 'off' }] }];

// One color per route, stable by index.
export const ROUTE_COLORS = ['#3EFF93', '#38BDF8', '#F472B6', '#FBBF24', '#A78BFA', '#34D399', '#F87171'];

export function routeColor(index) {
  return ROUTE_COLORS[index % ROUTE_COLORS.length];
}

function stopIcon(stop, color) {
  const done = stop.status === 'COMPLETED';
  const failed = stop.status === 'FAILED';
  return {
    path: 'M 0,-1 a 1,1 0 1,1 0,2 a 1,1 0 1,1 0,-2', // circle
    scale: 7,
    fillColor: failed ? '#EF4444' : done ? '#4B5563' : color,
    fillOpacity: done ? 0.55 : 1,
    strokeColor: '#0B0F0D',
    strokeWeight: 1.5,
  };
}

function driverIcon(color) {
  return {
    path: 'M 0,-1 a 1,1 0 1,1 0,2 a 1,1 0 1,1 0,-2',
    scale: 9,
    fillColor: color,
    fillOpacity: 1,
    strokeColor: '#FFFFFF',
    strokeWeight: 2.5,
  };
}

const DEPOT_ICON_PATH =
  'M -8,3 L -8,-2 L 0,-7 L 8,-2 L 8,3 Z M -3,3 L -3,-1 L 3,-1 L 3,3'; // little warehouse

const MAPS_KEY = process.env.REACT_APP_GOOGLE_MAPS_API_KEY || '';

function MapUnavailable() {
  return (
    <div className="w-full h-full flex items-center justify-center bg-gray-100 dark:bg-background">
      <div className="max-w-md text-center px-6">
        <p className="text-lg font-semibold text-gray-800 dark:text-foreground mb-2">Map tiles unavailable</p>
        <p className="text-sm text-gray-600 dark:text-muted">
          No Google Maps API key was provided at build time. The world is still live — use the
          dispatch panel, Orders, and the Event Console. To enable the map, set{' '}
          <code className="font-mono">GOOGLE_MAPS_API_KEY</code> in your environment (or{' '}
          <code className="font-mono">ui/.env</code>) and rebuild: <code className="font-mono">make up</code>.
        </p>
      </div>
    </div>
  );
}

const MapContainer = ({
  depots = [],
  routes = [],
  unassignedOrders = [],
  driverPositions = {}, // driverId -> {latitude, longitude, name, routeNumber, color}
  visibleRouteIds = null, // null = show all ACTIVE + selected
  selectedRouteId = null,
  isDarkMode = false,
  onSelectRoute,
}) => {
  const [infoWindow, setInfoWindow] = useState(null); // {position, title, lines}

  const { isLoaded, loadError } = useJsApiLoader({
    id: 'google-map-script',
    googleMapsApiKey: MAPS_KEY || 'missing-key',
    libraries: GOOGLE_MAPS_LIBRARIES,
  });

  const mapOptions = useMemo(
    () => ({
      disableDefaultUI: true,
      zoomControl: true,
      clickableIcons: false,
      styles: isDarkMode ? darkMapStyles : lightMapStyles,
    }),
    [isDarkMode]
  );

  const routeIsVisible = useCallback(
    (route) => {
      if (visibleRouteIds) return visibleRouteIds.has(route.id);
      return route.status === 'ACTIVE' || route.id === selectedRouteId;
    },
    [visibleRouteIds, selectedRouteId]
  );

  // Nudge the renderer after mount: a map initialized while its flex container
  // is still settling can sit unpainted until it hears a resize.
  const onMapLoad = useCallback((map) => {
    setTimeout(() => {
      if (window.google?.maps?.event) {
        window.google.maps.event.trigger(map, 'resize');
        map.setCenter(AUSTIN_CENTER);
      }
    }, 400);
  }, []);

  const showInfo = (position, title, lines) => setInfoWindow({ position, title, lines });

  if (!MAPS_KEY || loadError) {
    return <MapUnavailable />;
  }

  if (!isLoaded) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-100 dark:bg-background">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-muted">Loading map…</p>
        </div>
      </div>
    );
  }

  return (
    <GoogleMap
      key={isDarkMode ? 'map-dark' : 'map-light'} // remount on theme change: in-place style swaps leave stale tiles
      mapContainerStyle={{ width: '100%', height: '100%' }}
      center={AUSTIN_CENTER}
      zoom={13}
      options={mapOptions}
      onLoad={onMapLoad}
    >
      {/* Depot */}
      {depots.map((depot) => (
        <Marker
          key={`depot-${depot.id}`}
          position={{ lat: depot.latitude, lng: depot.longitude }}
          icon={{
            path: DEPOT_ICON_PATH,
            scale: 1.6,
            fillColor: '#FBBF24',
            fillOpacity: 1,
            strokeColor: '#0B0F0D',
            strokeWeight: 1.2,
          }}
          zIndex={50}
          onClick={() => showInfo({ lat: depot.latitude, lng: depot.longitude }, depot.name, [depot.address])}
        />
      ))}

      {/* Route stops + polylines */}
      {routes.map((route, idx) => {
        if (!routeIsVisible(route)) return null;
        const color = routeColor(idx);
        const orderedStops = [...route.stops].sort((a, b) => (a.sequence ?? 0) - (b.sequence ?? 0));
        const path = orderedStops.map((s) => ({ lat: s.latitude, lng: s.longitude }));
        const isSelected = route.id === selectedRouteId;
        return (
          <React.Fragment key={route.id}>
            {path.length >= 2 && (
              <Polyline
                path={path}
                options={{
                  strokeColor: color,
                  strokeOpacity: route.status === 'ACTIVE' ? 0.9 : 0.45,
                  strokeWeight: isSelected ? 5 : 3,
                  ...(route.status !== 'ACTIVE' && {
                    strokeOpacity: 0,
                    icons: [
                      {
                        icon: { path: 'M 0,-1 0,1', strokeOpacity: 0.6, strokeColor: color, scale: 3 },
                        offset: '0',
                        repeat: '14px',
                      },
                    ],
                  }),
                }}
                onClick={() => onSelectRoute && onSelectRoute(route.id)}
              />
            )}
            {orderedStops.map((stop) => (
              <Marker
                key={stop.stopId}
                position={{ lat: stop.latitude, lng: stop.longitude }}
                icon={stopIcon(stop, color)}
                label={{
                  text: String(stop.sequence ?? '•'),
                  color: '#0B0F0D',
                  fontSize: '10px',
                  fontWeight: '700',
                }}
                zIndex={30}
                onClick={() =>
                  showInfo(
                    { lat: stop.latitude, lng: stop.longitude },
                    `${route.routeNumber} · stop ${stop.sequence} — ${stop.kind}`,
                    [
                      `${stop.orderNumber} · ${stop.status}`,
                      stop.address,
                      stop.windowStart ? `window ${fmtTime(stop.windowStart)}–${fmtTime(stop.windowEnd)}` : null,
                    ].filter(Boolean)
                  )
                }
              />
            ))}
          </React.Fragment>
        );
      })}

      {/* Unassigned order pickups */}
      {unassignedOrders.map((order) =>
        order.pickup ? (
          <Marker
            key={`unassigned-${order.id}`}
            position={{ lat: order.pickup.latitude, lng: order.pickup.longitude }}
            icon={{
              path: 'M 0,0 C -2,-6 2,-6 0,0 M 0,-4 a 1.6,1.6 0 1,1 0,-0.1', // pin-ish
              scale: 2.2,
              fillColor: '#F97316',
              fillOpacity: 1,
              strokeColor: '#0B0F0D',
              strokeWeight: 1,
            }}
            zIndex={40}
            onClick={() =>
              showInfo(
                { lat: order.pickup.latitude, lng: order.pickup.longitude },
                `${order.orderNumber} — unassigned`,
                [
                  order.customer?.name,
                  `${order.parcelCount} parcel(s)`,
                  `pickup: ${order.pickup.address}`,
                  `delivery: ${order.delivery?.address}`,
                ].filter(Boolean)
              )
            }
          />
        ) : null
      )}

      {/* Live drivers */}
      {Object.entries(driverPositions).map(([driverId, pos]) =>
        pos.latitude != null ? (
          <Marker
            key={`driver-${driverId}`}
            position={{ lat: pos.latitude, lng: pos.longitude }}
            icon={driverIcon(pos.color || '#3EFF93')}
            label={{
              text: (pos.name || '?')
                .split(' ')
                .map((p) => p[0])
                .join('')
                .slice(0, 2),
              color: '#0B0F0D',
              fontSize: '9px',
              fontWeight: '800',
            }}
            zIndex={60}
            onClick={() =>
              showInfo(
                { lat: pos.latitude, lng: pos.longitude },
                pos.name || 'Driver',
                [pos.routeNumber ? `on ${pos.routeNumber}` : 'idle', pos.speedMph != null ? `${Math.round(pos.speedMph)} mph` : null].filter(
                  Boolean
                )
              )
            }
          />
        ) : null
      )}

      {infoWindow && (
        <InfoWindow position={infoWindow.position} onCloseClick={() => setInfoWindow(null)}>
          <div style={{ color: '#111', minWidth: 180 }}>
            <div style={{ fontWeight: 700, marginBottom: 4 }}>{infoWindow.title}</div>
            {infoWindow.lines.map((l, i) => (
              <div key={i} style={{ fontSize: 12, lineHeight: 1.5 }}>
                {l}
              </div>
            ))}
          </div>
        </InfoWindow>
      )}
    </GoogleMap>
  );
};

function fmtTime(iso) {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return iso;
  }
}

export default MapContainer;
