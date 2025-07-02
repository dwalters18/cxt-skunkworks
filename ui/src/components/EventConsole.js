import React, { useState, useEffect } from 'react';

const EventConsole = ({ apiBase }) => {
    const [events, setEvents] = useState([]);
    const [eventTopics, setEventTopics] = useState([]);
    const [selectedTopic, setSelectedTopic] = useState('');
    const [showPublishForm, setShowPublishForm] = useState(false);
    const [isAutoRefresh, setIsAutoRefresh] = useState(true);
    const [newEvent, setNewEvent] = useState({
        event_type: '',
        source: 'manual',
        data: '{}',
        correlation_id: ''
    });

    const [websocket, setWebsocket] = useState(null);
    const [connectionStatus, setConnectionStatus] = useState('disconnected');

    const eventTypes = [
        'LOAD_CREATED', 'LOAD_ASSIGNED', 'LOAD_PICKED_UP', 'LOAD_IN_TRANSIT', 
        'LOAD_DELIVERED', 'LOAD_CANCELLED', 'VEHICLE_LOCATION_UPDATE', 
        'VEHICLE_STATUS_CHANGE', 'DRIVER_STATUS_CHANGE', 'DRIVER_ASSIGNED',
        'ROUTE_OPTIMIZED', 'ROUTE_DEVIATION', 'AI_PREDICTION', 'SYSTEM_ALERT'
    ];

    useEffect(() => {
        fetchEventTopics();
        if (isAutoRefresh) {
            connectWebSocket();
        } else {
            disconnectWebSocket();
        }
        
        return () => {
            disconnectWebSocket();
        };
    }, [isAutoRefresh]);

    const connectWebSocket = () => {
        if (websocket) {
            return; // Already connected
        }
        
        const wsUrl = apiBase.replace('http', 'ws') + '/ws/events';
        const ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
            console.log('WebSocket connected');
            setConnectionStatus('connected');
            setWebsocket(ws);
        };
        
        ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                if (message.type === 'event' && message.data) {
                    setEvents(prev => [message.data, ...prev.slice(0, 49)]); // Keep last 50 events
                }
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        ws.onclose = () => {
            console.log('WebSocket disconnected');
            setConnectionStatus('disconnected');
            setWebsocket(null);
            
            // Attempt to reconnect after 5 seconds if auto-refresh is still enabled
            if (isAutoRefresh) {
                setTimeout(() => {
                    if (isAutoRefresh) {
                        connectWebSocket();
                    }
                }, 5000);
            }
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            setConnectionStatus('error');
        };
    };
    
    const disconnectWebSocket = () => {
        if (websocket) {
            websocket.close();
            setWebsocket(null);
            setConnectionStatus('disconnected');
        }
    };

    const fetchEventTopics = async () => {
        try {
            const response = await fetch(`${apiBase}/api/events/topics`);
            if (response.ok) {
                const data = await response.json();
                setEventTopics(data.topics || []);
            }
        } catch (error) {
            console.error('Error fetching event topics:', error);
        }
    };



    const publishEvent = async () => {
        try {
            let parsedData;
            try {
                parsedData = JSON.parse(newEvent.data);
            } catch (e) {
                alert('Invalid JSON in event data');
                return;
            }

            const eventPayload = {
                event_type: newEvent.event_type,
                source: newEvent.source,
                data: parsedData,
                correlation_id: newEvent.correlation_id || undefined
            };

            const response = await fetch(`${apiBase}/api/events/publish`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(eventPayload),
            });

            if (response.ok) {
                setShowPublishForm(false);
                setNewEvent({
                    event_type: '',
                    source: 'manual',
                    data: '{}',
                    correlation_id: ''
                });
                // Add to local events for immediate feedback
                const publishedEvent = {
                    ...eventPayload,
                    event_id: `manual-${Date.now()}`,
                    timestamp: new Date().toISOString()
                };
                setEvents(prev => [publishedEvent, ...prev]);
            }
        } catch (error) {
            console.error('Error publishing event:', error);
        }
    };

    const getEventTypeColor = (eventType) => {
        const colors = {
            'LOAD_CREATED': '#4caf50',
            'LOAD_ASSIGNED': '#2196f3',
            'LOAD_PICKED_UP': '#ff9800',
            'LOAD_IN_TRANSIT': '#9c27b0',
            'LOAD_DELIVERED': '#4caf50',
            'LOAD_CANCELLED': '#f44336',
            'VEHICLE_LOCATION_UPDATE': '#00bcd4',
            'VEHICLE_STATUS_CHANGE': '#607d8b',
            'DRIVER_STATUS_CHANGE': '#795548',
            'AI_PREDICTION': '#e91e63',
            'SYSTEM_ALERT': '#ff5722'
        };
        return colors[eventType] || '#757575';
    };

    const formatTimestamp = (timestamp) => {
        return new Date(timestamp).toLocaleString();
    };

    const formatEventData = (data) => {
        return JSON.stringify(data, null, 2);
    };

    const fillSampleEventData = (eventType) => {
        const sampleData = {
            'load.created': {
                load_id: `LOAD-${Math.floor(Math.random() * 10000).toString().padStart(5, '0')}`,
                pickup_address: '123 Main St, Dallas, TX',
                delivery_address: '456 Oak Ave, Houston, TX',
                weight: Math.floor(Math.random() * 50000) + 1000,
                rate: Math.floor(Math.random() * 5000) + 500
            },
            'load.assigned': {
                load_id: `LOAD-${Math.floor(Math.random() * 10000).toString().padStart(5, '0')}`,
                vehicle_id: `VEH-${Math.floor(Math.random() * 1000).toString().padStart(4, '0')}`,
                driver_id: `DRV-${Math.floor(Math.random() * 500).toString().padStart(4, '0')}`
            },
            'load.picked_up': {
                load_id: `LOAD-${Math.floor(Math.random() * 10000).toString().padStart(5, '0')}`,
                pickup_time: new Date().toISOString(),
                location: { lat: 32.7767, lon: -96.7970 }
            },
            'load.in_transit': {
                load_id: `LOAD-${Math.floor(Math.random() * 10000).toString().padStart(5, '0')}`,
                current_location: { lat: 31.7619, lon: -96.7661 },
                estimated_arrival: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString()
            },
            'load.delivered': {
                load_id: `LOAD-${Math.floor(Math.random() * 10000).toString().padStart(5, '0')}`,
                delivery_time: new Date().toISOString(),
                signature: 'John Doe'
            },
            'vehicle.location.updated': {
                vehicle_id: `VEH-${Math.floor(Math.random() * 1000).toString().padStart(4, '0')}`,
                location: { 
                    latitude: 32.7767 + (Math.random() - 0.5) * 0.1, 
                    longitude: -96.7970 + (Math.random() - 0.5) * 0.1 
                },
                speed: Math.floor(Math.random() * 80) + 35,
                heading: Math.floor(Math.random() * 360)
            },
            'driver.status.changed': {
                driver_id: `DRV-${Math.floor(Math.random() * 500).toString().padStart(4, '0')}`,
                old_status: 'available',
                new_status: 'on_duty',
                reason: 'Manual status change'
            },
            'system.alert': {
                alert_type: 'warning',
                message: 'Sample system alert for testing',
                severity: 'medium',
                component: 'event_console'
            },
            'ai.prediction': {
                prediction_type: 'demand_forecast',
                confidence: 0.85,
                prediction_data: {
                    region: 'Dallas-Fort Worth',
                    predicted_demand: 42,
                    time_horizon: '24h'
                }
            },
            'route.optimized': {
                route_id: `ROUTE-${Math.floor(Math.random() * 1000).toString().padStart(4, '0')}`,
                optimized_distance: Math.floor(Math.random() * 500) + 100,
                estimated_duration: Math.floor(Math.random() * 480) + 60,
                fuel_savings: Math.floor(Math.random() * 50) + 10
            }
        };

        const data = sampleData[eventType] || { message: 'Sample event data' };
        
        setNewEvent({
            ...newEvent,
            data: JSON.stringify(data, null, 2),
            source: 'manual_test',
            correlation_id: `test-${Date.now()}`
        });
    };

    return (
        <div className="event-console">
            <div className="section-header">
                <h2>Event Console</h2>
                <div className="console-controls">
                    <label className="auto-refresh-toggle">
                        <input
                            type="checkbox"
                            checked={isAutoRefresh}
                            onChange={(e) => setIsAutoRefresh(e.target.checked)}
                        />
                        Auto Refresh
                    </label>
                    <button
                        onClick={() => setShowPublishForm(true)}
                        className="btn-primary"
                    >
                        📤 Publish Event
                    </button>
                </div>
            </div>

            {/* Event Statistics */}
            <div className="event-stats">
                <div className="stat-card">
                    <div className="stat-value">{events.length}</div>
                    <div className="stat-label">Total Events</div>
                </div>
                <div className="stat-card">
                    <div className="stat-value">{eventTopics.length}</div>
                    <div className="stat-label">Active Topics</div>
                </div>
                <div className="stat-card">
                    <div className="stat-value">
                        {events.filter(e => new Date(e.timestamp) > new Date(Date.now() - 300000)).length}
                    </div>
                    <div className="stat-label">Last 5 Minutes</div>
                </div>
                <div className="stat-card">
                    <div className={`stat-value connection-status ${connectionStatus}`}>
                        {connectionStatus === 'connected' ? '🟢' : 
                         connectionStatus === 'error' ? '🔴' : '🟡'}
                    </div>
                    <div className="stat-label">
                        WebSocket {connectionStatus.charAt(0).toUpperCase() + connectionStatus.slice(1)}
                    </div>
                </div>
            </div>

            {/* Event Filters */}
            <div className="event-filters">
                <select
                    value={selectedTopic}
                    onChange={(e) => setSelectedTopic(e.target.value)}
                >
                    <option value="">All Event Types</option>
                    {eventTypes.map(type => (
                        <option key={type} value={type}>{type}</option>
                    ))}
                </select>
                <button onClick={() => setEvents([])} className="btn-secondary">
                    🗑️ Clear Console
                </button>
            </div>

            {/* Event Stream */}
            <div className="event-stream">
                <h3>Live Event Stream</h3>
                <div className="events-container">
                    {events
                        .filter(event => !selectedTopic || event.event_type === selectedTopic)
                        .map((event, index) => (
                        <div key={`${event.event_id}-${index}`} className="event-item">
                            <div className="event-header">
                                <span 
                                    className="event-type"
                                    style={{ color: getEventTypeColor(event.event_type) }}
                                >
                                    ● {event.event_type}
                                </span>
                                <span className="event-source">{event.source}</span>
                                <span className="event-timestamp">
                                    {formatTimestamp(event.timestamp)}
                                </span>
                            </div>
                            <div className="event-id">ID: {event.event_id}</div>
                            <div className="event-data">
                                <details>
                                    <summary>Event Data</summary>
                                    <pre>{formatEventData(event.data)}</pre>
                                </details>
                            </div>
                        </div>
                    ))}
                    
                    {events.length === 0 && (
                        <div className="no-events">
                            <p>No events to display. Events will appear here in real-time.</p>
                            {!isAutoRefresh && (
                                <p>Enable auto-refresh to see simulated events.</p>
                            )}
                        </div>
                    )}
                </div>
            </div>

            {/* Publish Event Modal */}
            {showPublishForm && (
                <div className="modal-overlay">
                    <div className="modal large">
                        <div className="modal-header">
                            <h3>Publish Event</h3>
                            <button onClick={() => setShowPublishForm(false)}>✕</button>
                        </div>
                        <div className="modal-body">
                            <div className="form-group">
                                <label>Event Type:</label>
                                <select
                                    value={newEvent.event_type}
                                    onChange={(e) => setNewEvent({...newEvent, event_type: e.target.value})}
                                >
                                    <option value="">Select Event Type</option>
                                    {eventTypes.map(type => (
                                        <option key={type} value={type}>{type}</option>
                                    ))}
                                </select>
                                {newEvent.event_type && (
                                    <button
                                        onClick={() => fillSampleEventData(newEvent.event_type)}
                                        className="btn-small btn-secondary"
                                        style={{ marginTop: '5px' }}
                                    >
                                        Fill Sample Data
                                    </button>
                                )}
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label>Source:</label>
                                    <input
                                        type="text"
                                        value={newEvent.source}
                                        onChange={(e) => setNewEvent({...newEvent, source: e.target.value})}
                                        placeholder="manual, api, telematics, etc."
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Correlation ID (optional):</label>
                                    <input
                                        type="text"
                                        value={newEvent.correlation_id}
                                        onChange={(e) => setNewEvent({...newEvent, correlation_id: e.target.value})}
                                        placeholder="Optional correlation ID"
                                    />
                                </div>
                            </div>
                            <div className="form-group">
                                <label>Event Data (JSON):</label>
                                <textarea
                                    value={newEvent.data}
                                    onChange={(e) => setNewEvent({...newEvent, data: e.target.value})}
                                    rows={10}
                                    placeholder='{"key": "value"}'
                                    className="json-editor"
                                />
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button onClick={() => setShowPublishForm(false)} className="btn-secondary">
                                Cancel
                            </button>
                            <button onClick={publishEvent} className="btn-primary">
                                Publish Event
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Available Topics */}
            <div className="available-topics">
                <h3>Available Event Topics</h3>
                <div className="topics-grid">
                    {eventTopics.map(topic => (
                        <div key={topic} className="topic-card">
                            <div className="topic-name">{topic}</div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default EventConsole;
