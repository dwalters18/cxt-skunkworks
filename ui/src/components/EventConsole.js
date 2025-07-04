import React, { useState, useEffect } from 'react';
import { useWebSocket } from '../contexts/WebSocketContext';

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

    const { isConnected, events: wsEvents, addEventListener } = useWebSocket(apiBase);

    const eventTypes = [
        'LOAD_CREATED', 'LOAD_ASSIGNED', 'LOAD_PICKED_UP', 'LOAD_IN_TRANSIT', 
        'LOAD_DELIVERED', 'LOAD_CANCELLED', 'VEHICLE_LOCATION_UPDATE', 
        'VEHICLE_STATUS_CHANGE', 'DRIVER_STATUS_CHANGE', 'DRIVER_ASSIGNED',
        'ROUTE_OPTIMIZED', 'ROUTE_DEVIATION', 'AI_PREDICTION', 'SYSTEM_ALERT'
    ];

    useEffect(() => {
        fetchEventTopics();
    }, []);

    useEffect(() => {
        if (isConnected) {
            const cleanup = addEventListener((eventData) => {
                // EventData is already parsed and ready to use
                setEvents(prev => [eventData, ...prev.slice(0, 49)]); // Keep last 50 events
            });

            return cleanup;
        }
    }, [isConnected, addEventListener]);

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

    const generateUUID = () => `${Math.random().toString(36).substr(2, 9)}-${Math.random().toString(36).substr(2, 4)}-${Math.random().toString(36).substr(2, 4)}-${Math.random().toString(36).substr(2, 4)}-${Math.random().toString(36).substr(2, 12)}`;
    const generateLoadNumber = () => `LOAD-${Math.floor(Math.random() * 10000).toString().padStart(5, '0')}`;
    const generateVehicleNumber = () => `VEH-${Math.floor(Math.random() * 1000).toString().padStart(4, '0')}`;
    const generateDriverNumber = () => `DRV-${Math.floor(Math.random() * 500).toString().padStart(4, '0')}`;

    const fillSampleEventData = (eventType) => {
        const sampleData = {
            'LOAD_CREATED': {
                loadNumber: generateLoadNumber(),
                customerId: generateUUID(),
                pickupLocation: {
                    latitude: 32.7767,
                    longitude: -96.7970,
                    address: "123 Industrial Blvd, Dallas, TX 75201"
                },
                deliveryLocation: {
                    latitude: 29.7604,
                    longitude: -95.3698,
                    address: "456 Port Way, Houston, TX 77002"
                },
                pickupDate: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
                deliveryDate: new Date(Date.now() + 72 * 60 * 60 * 1000).toISOString(),
                weight: Math.floor(Math.random() * 50000) + 5000,
                volume: Math.floor(Math.random() * 500) + 100,
                commodityType: "General Freight",
                specialRequirements: ["Temperature Controlled", "Fragile"],
                rate: Math.floor(Math.random() * 5000) + 1000
            },
            'LOAD_ASSIGNED': {
                loadNumber: generateLoadNumber(),
                driverId: generateUUID(),
                vehicleId: generateUUID(),
                assignedBy: generateUUID(),
                assignmentDate: new Date().toISOString(),
                estimatedPickupTime: new Date(Date.now() + 8 * 60 * 60 * 1000).toISOString(),
                estimatedDeliveryTime: new Date(Date.now() + 32 * 60 * 60 * 1000).toISOString()
            },
            'LOAD_PICKED_UP': {
                loadNumber: generateLoadNumber(),
                actualPickupTime: new Date().toISOString(),
                location: {
                    latitude: 32.7767,
                    longitude: -96.7970,
                    address: "123 Industrial Blvd, Dallas, TX 75201"
                },
                signature: "John Smith - Warehouse Manager",
                weight: Math.floor(Math.random() * 50000) + 5000,
                pieces: Math.floor(Math.random() * 50) + 1
            },
            'LOAD_IN_TRANSIT': {
                loadNumber: generateLoadNumber(),
                currentLocation: {
                    latitude: 31.0845 + (Math.random() - 0.5) * 0.1,
                    longitude: -97.6807 + (Math.random() - 0.5) * 0.1,
                    address: "I-35, Waco, TX"
                },
                estimatedArrival: new Date(Date.now() + 4 * 60 * 60 * 1000).toISOString(),
                speed: Math.floor(Math.random() * 20) + 60,
                mileageRemaining: Math.floor(Math.random() * 200) + 50,
                status: "On Schedule"
            },
            'LOAD_DELIVERED': {
                loadNumber: generateLoadNumber(),
                actualDeliveryTime: new Date().toISOString(),
                location: {
                    latitude: 29.7604,
                    longitude: -95.3698,
                    address: "456 Port Way, Houston, TX 77002"
                },
                signature: "Maria Garcia - Receiving Manager",
                deliveryNotes: "Delivered to dock 5, all items received in good condition",
                proofOfDelivery: "POD-" + Math.floor(Math.random() * 10000)
            },
            'LOAD_CANCELLED': {
                loadNumber: generateLoadNumber(),
                cancellationReason: "Customer Request",
                cancellationDate: new Date().toISOString(),
                cancelledBy: generateUUID(),
                refundAmount: Math.floor(Math.random() * 2000) + 500,
                restockingFee: Math.floor(Math.random() * 200) + 50
            },
            'VEHICLE_LOCATION_UPDATE': {
                vehicleNumber: generateVehicleNumber(),
                location: {
                    latitude: 32.7767 + (Math.random() - 0.5) * 0.2,
                    longitude: -96.7970 + (Math.random() - 0.5) * 0.2,
                    accuracy: Math.floor(Math.random() * 10) + 3,
                    altitude: Math.floor(Math.random() * 500) + 200
                },
                speed: Math.floor(Math.random() * 80) + 35,
                heading: Math.floor(Math.random() * 360),
                odometer: Math.floor(Math.random() * 100000) + 50000,
                fuelLevel: Math.floor(Math.random() * 100),
                engineHours: Math.floor(Math.random() * 5000) + 1000,
                driverId: generateUUID(),
                loadId: generateUUID()
            },
            'VEHICLE_STATUS_CHANGE': {
                vehicleNumber: generateVehicleNumber(),
                previousStatus: "available",
                newStatus: "in_service",
                statusReason: "Load assignment",
                location: {
                    latitude: 32.7767,
                    longitude: -96.7970
                },
                changedBy: generateUUID()
            },
            'DRIVER_STATUS_CHANGE': {
                driverNumber: generateDriverNumber(),
                previousStatus: "off_duty",
                newStatus: "on_duty",
                location: {
                    latitude: 32.7767,
                    longitude: -96.7970
                },
                hoursRemaining: 11,
                nextBreakDue: new Date(Date.now() + 8 * 60 * 60 * 1000).toISOString(),
                vehicleId: generateUUID()
            },
            'DRIVER_ASSIGNED': {
                driverNumber: generateDriverNumber(),
                loadId: generateUUID(),
                vehicleId: generateUUID(),
                assignedBy: generateUUID(),
                assignmentDate: new Date().toISOString(),
                expectedDuration: "24 hours",
                specialInstructions: "Hazmat certified driver required"
            },
            'ROUTE_OPTIMIZED': {
                loadId: generateUUID(),
                driverId: generateUUID(),
                vehicleId: generateUUID(),
                originalRoute: {
                    distance: Math.floor(Math.random() * 500) + 200,
                    duration: Math.floor(Math.random() * 480) + 240,
                    waypoints: [
                        { latitude: 32.7767, longitude: -96.7970 },
                        { latitude: 29.7604, longitude: -95.3698 }
                    ]
                },
                optimizedRoute: {
                    distance: Math.floor(Math.random() * 450) + 180,
                    duration: Math.floor(Math.random() * 420) + 200,
                    waypoints: [
                        { latitude: 32.7767, longitude: -96.7970 },
                        { latitude: 31.0845, longitude: -97.6807 },
                        { latitude: 29.7604, longitude: -95.3698 }
                    ],
                    fuelEstimate: Math.floor(Math.random() * 150) + 50,
                    tollEstimate: Math.floor(Math.random() * 50) + 10
                },
                optimizationScore: Math.floor(Math.random() * 30) + 70,
                algorithmUsed: "ML_ENHANCED_ROUTING",
                fuelSavings: Math.floor(Math.random() * 25) + 5,
                timeSavings: Math.floor(Math.random() * 60) + 15
            },
            'ROUTE_DEVIATION': {
                loadId: generateUUID(),
                vehicleId: generateUUID(),
                driverId: generateUUID(),
                plannedLocation: {
                    latitude: 31.0845,
                    longitude: -97.6807
                },
                actualLocation: {
                    latitude: 31.1845,
                    longitude: -97.5807
                },
                deviationDistance: Math.floor(Math.random() * 10) + 1,
                deviationReason: "Traffic Avoidance",
                impactOnETA: Math.floor(Math.random() * 30) + 5
            },
            'AI_PREDICTION': {
                predictionType: ['demand_forecast', 'route_optimization', 'maintenance_alert', 'fuel_consumption'][Math.floor(Math.random() * 4)],
                confidence: Math.floor(Math.random() * 30) + 70,
                predictionData: {
                    region: "Dallas-Fort Worth Metroplex",
                    predictedValue: Math.floor(Math.random() * 100) + 20,
                    timeHorizon: "24 hours",
                    factors: ["weather", "traffic", "historical_patterns"]
                },
                modelVersion: "2.1.0",
                dataPoints: Math.floor(Math.random() * 1000) + 500
            },
            'SYSTEM_ALERT': {
                alertType: ['warning', 'error', 'info', 'critical'][Math.floor(Math.random() * 4)],
                message: "Sample system alert for testing purposes",
                severity: ['low', 'medium', 'high', 'critical'][Math.floor(Math.random() * 4)],
                component: "event_console",
                affectedServices: ["routing", "tracking"],
                actionRequired: "Monitor system performance",
                alertId: generateUUID(),
                escalationLevel: Math.floor(Math.random() * 3) + 1
            }
        };

        const data = sampleData[eventType] || { message: 'Sample event data for ' + eventType };
        
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
                    <div className={`stat-value connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
                        {isConnected ? '🟢' : '🔴'}
                    </div>
                    <div className="stat-label">
                        WebSocket {isConnected ? 'Connected' : 'Disconnected'}
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
