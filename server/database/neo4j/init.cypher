// Neo4j initialization for TMS graph data
// Create constraints for unique identifiers
CREATE CONSTRAINT carrier_id IF NOT EXISTS FOR (c:Carrier) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT driver_id IF NOT EXISTS FOR (d:Driver) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT vehicle_id IF NOT EXISTS FOR (v:Vehicle) REQUIRE v.id IS UNIQUE;
CREATE CONSTRAINT customer_id IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT load_id IF NOT EXISTS FOR (l:Load) REQUIRE l.id IS UNIQUE;
CREATE CONSTRAINT route_id IF NOT EXISTS FOR (r:Route) REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT location_id IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE;
CREATE CONSTRAINT hub_id IF NOT EXISTS FOR (h:Hub) REQUIRE h.id IS UNIQUE;
CREATE CONSTRAINT driver_id IF NOT EXISTS FOR (d:Driver) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT vehicle_id IF NOT EXISTS FOR (v:Vehicle) REQUIRE v.id IS UNIQUE;
CREATE CONSTRAINT customer_id IF NOT EXISTS FOR (cu:Customer) REQUIRE cu.id IS UNIQUE;

// Create indexes for performance
CREATE INDEX location_coordinates IF NOT EXISTS FOR (l:Location) ON (l.latitude, l.longitude);
CREATE INDEX driver_status IF NOT EXISTS FOR (d:Driver) ON (d.status);
CREATE INDEX vehicle_status IF NOT EXISTS FOR (v:Vehicle) ON (v.status);
CREATE INDEX load_status IF NOT EXISTS FOR (l:Load) ON (l.status);
CREATE INDEX route_distance IF NOT EXISTS FOR ()-[r:ROUTE_SEGMENT]->() ON (r.distance);

// Create sample carriers (matching PostgreSQL data)
CREATE
  (carrier1:Carrier {
    id: 'f47ac10b-58cc-4372-a567-0e02b2c3d479',
    name: 'Austin Logistics LLC',
    mc_number: 'MC-123456',
    dot_number: 'DOT-789012',
    status: 'active',
    contact_info: {
      phone: '512-555-0100',
      email: 'dispatch@austinlogistics.com',
      address: '123 Industrial Blvd, Austin, TX 78748'
    }
  }),
  (carrier2:Carrier {
    id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    name: 'Texas Freight Solutions',
    mc_number: 'MC-654321',
    dot_number: 'DOT-210987',
    status: 'active',
    contact_info: {
      phone: '512-555-0200',
      email: 'operations@texasfreight.com',
      address: '456 Commerce St, Austin, TX 78701'
    }
  });

// Create sample customers (matching PostgreSQL schema)
CREATE
  (customer1:Customer {
    id: 'c1a2b3c4-d5e6-f789-0123-456789abcdef',
    customer_code: 'CUST001',
    company_name: 'Austin Manufacturing Co',
    contact_name: 'John Smith',
    email: 'john.smith@austinmfg.com',
    phone: '512-555-1000',
    address: '789 Factory Rd, Austin, TX 78744',
    city: 'Austin',
    state: 'TX',
    zipcode: '78744',
    country: 'USA'
  }),
  (customer2:Customer {
    id: 'd2b3c4d5-e6f7-8901-2345-6789abcdef01',
    customer_code: 'CUST002',
    company_name: 'Dallas Distribution Center',
    contact_name: 'Sarah Johnson',
    email: 'sarah.johnson@dallasdc.com',
    phone: '214-555-2000',
    address: '321 Warehouse Ave, Dallas, TX 75201',
    city: 'Dallas',
    state: 'TX',
    zipcode: '75201',
    country: 'USA'
  });

// Create locations (major cities and Austin area)
CREATE 
  (austin:Location {
    id: 'LOC_AUSTIN',
    name: 'Austin, TX',
    city: 'Austin',
    state: 'TX',
    zipcode: '78701',
    latitude: 30.2672,
    longitude: -97.7431,
    type: 'city'
  }),
  (houston:Location {
    id: 'LOC_HOUSTON',
    name: 'Houston, TX',
    city: 'Houston',
    state: 'TX',
    zipcode: '77002',
    latitude: 29.7604,
    longitude: -95.3698,
    type: 'city'
  }),
  (dallas:Location {
    id: 'LOC_DALLAS',
    name: 'Dallas, TX',
    city: 'Dallas',
    state: 'TX',
    zipcode: '75201',
    latitude: 32.7767,
    longitude: -96.7970,
    type: 'city'
  }),
  (sanantonio:Location {
    id: 'LOC_SAN_ANTONIO',
    name: 'San Antonio, TX',
    city: 'San Antonio',
    state: 'TX',
    zipcode: '78205',
    latitude: 29.4241,
    longitude: -98.4936,
    type: 'city'
  }),
  (roundrock:Location {
    id: 'LOC_ROUND_ROCK',
    name: 'Round Rock, TX',
    city: 'Round Rock',
    state: 'TX',
    zipcode: '78664',
    latitude: 30.5082,
    longitude: -97.6789,
    type: 'city'
  }),
  (cedarpark:Location {
    id: 'LOC_CEDAR_PARK',
    name: 'Cedar Park, TX',
    city: 'Cedar Park',
    state: 'TX',
    zipcode: '78613',
    latitude: 30.5052,
    longitude: -97.8203,
    type: 'city'
  }),
  (newyork:Location {
    id: 'LOC_NEW_YORK',
    name: 'New York, NY',
    city: 'New York',
    state: 'NY',
    zipcode: '10001',
    latitude: 40.7128,
    longitude: -74.0060,
    type: 'city'
  }),
  (austin:Location {
    id: 'LOC_AUSTIN',
    name: 'Austin, TX',
    city: 'Austin',
    state: 'TX',
    zipcode: '78701',
    latitude: 30.2672,
    longitude: -97.7431,
    type: 'city'
  }),
  (roundrock:Location {
    id: 'LOC_ROUND_ROCK',
    name: 'Round Rock, TX',
    city: 'Round Rock',
    state: 'TX',
    zipcode: '78664',
    latitude: 30.5077,
    longitude: -97.6890,
    type: 'city'
  }),
  (pflugerville:Location {
    id: 'LOC_PFLUGERVILLE',
    name: 'Pflugerville, TX',
    city: 'Pflugerville',
    state: 'TX',
    zipcode: '78660',
    latitude: 30.3872,
    longitude: -97.6231,
    type: 'city'
  }),
  (buda:Location {
    id: 'LOC_BUDA',
    name: 'Buda, TX',
    city: 'Buda',
    state: 'TX',
    zipcode: '78610',
    latitude: 30.1272,
    longitude: -97.6631,
    type: 'city'
  }),
  (georgetown:Location {
    id: 'LOC_GEORGETOWN',
    name: 'Georgetown, TX',
    city: 'Georgetown',
    state: 'TX',
    zipcode: '78626',
    latitude: 30.5172,
    longitude: -97.6831,
    type: 'city'
  });

// Create sample loads (matching PostgreSQL data)
CREATE
  (load1:Load {
    id: 'l1010101-2020-3030-4040-505050505050',
    load_number: 'LD001',
    customer_id: 'c1a2b3c4-d5e6-f789-0123-456789abcdef',
    origin_location: 'LOC_AUSTIN',
    destination_location: 'LOC_HOUSTON',
    pickup_date: datetime('2024-01-15T08:00:00Z'),
    delivery_date: datetime('2024-01-15T15:00:00Z'),
    weight: 25000,
    commodity: 'Electronics',
    value: 150000.00,
    rate: 850.00,
    status: 'assigned',
    assigned_driver_id: 'd1234567-89ab-cdef-0123-456789abcdef',
    assigned_vehicle_id: 'v1111111-2222-3333-4444-555555555555'
  }),
  (load2:Load {
    id: 'l2020202-3030-4040-5050-606060606060',
    load_number: 'LD002',
    customer_id: 'd2b3c4d5-e6f7-8901-2345-6789abcdef01',
    origin_location: 'LOC_DALLAS',
    destination_location: 'LOC_SAN_ANTONIO',
    pickup_date: datetime('2024-01-16T09:00:00Z'),
    delivery_date: datetime('2024-01-16T16:00:00Z'),
    weight: 18500,
    commodity: 'Building Materials',
    value: 45000.00,
    rate: 625.00,
    status: 'in_transit',
    assigned_driver_id: 'd2345678-9abc-def0-1234-56789abcdef0',
    assigned_vehicle_id: 'v2222222-3333-4444-5555-666666666666'
  });

// Create sample routes
CREATE
  (route1:Route {
    id: 'r1a1a1a1-b2b2-c3c3-d4d4-e5e5e5e5e5e5',
    route_name: 'Austin-Houston Express',
    route_type: 'REGULAR',
    load_id: 'l1010101-2020-3030-4040-505050505050',
    driver_id: 'd1234567-89ab-cdef-0123-456789abcdef',
    vehicle_id: 'v1111111-2222-3333-4444-555555555555',
    origin_location: 'LOC_AUSTIN',
    destination_location: 'LOC_HOUSTON',
    total_distance: 165.0,
    estimated_duration: 180,
    fuel_cost_estimate: 45.50,
    status: 'active'
  }),
  (route2:Route {
    id: 'r2b2b2b2-c3c3-d4d4-e5e5-f6f6f6f6f6f6',
    route_name: 'Dallas-San Antonio Direct',
    route_type: 'SPOT',
    load_id: 'l2020202-3030-4040-5050-606060606060',
    driver_id: 'd2345678-9abc-def0-1234-56789abcdef0',
    vehicle_id: 'v2222222-3333-4444-5555-666666666666',
    origin_location: 'LOC_DALLAS',
    destination_location: 'LOC_SAN_ANTONIO',
    total_distance: 275.0,
    estimated_duration: 300,
    fuel_cost_estimate: 72.25,
    status: 'in_progress'
  });

// Create carriers aligned with PostgreSQL IDs
CREATE
  (swift:Carrier {
    id: '00000000-0000-0000-0000-000000000001',
    name: 'Swift Transportation',
    mc_number: 'MC-123456',
    dot_number: 'DOT-987654'
  }),
  (schneider:Carrier {
    id: '00000000-0000-0000-0000-000000000002',
    name: 'Schneider National',
    mc_number: 'MC-234567',
    dot_number: 'DOT-876543'
  }),
  (jbhunt:Carrier {
    id: '00000000-0000-0000-0000-000000000003',
    name: 'J.B. Hunt Transport',
    mc_number: 'MC-345678',
    dot_number: 'DOT-765432'
  });

// Create customers
CREATE
  (acme:Customer {
    id: '10000000-0000-0000-0000-000000000001',
    customer_code: 'CUST001',
    company_name: 'Acme Logistics'
  }),
  (global:Customer {
    id: '10000000-0000-0000-0000-000000000002',
    customer_code: 'CUST002',
    company_name: 'Global Freight Solutions'
  }),
  (premier:Customer {
    id: '10000000-0000-0000-0000-000000000003',
    customer_code: 'CUST003',
    company_name: 'Premier Shipping Co'
  });

// Create vehicles
CREATE
  (:Vehicle {
    id: '20000000-0000-0000-0000-000000000001',
    vehicle_number: 'SWIFT001',
    carrier_id: '00000000-0000-0000-0000-000000000001'
  }),
  (:Vehicle {
    id: '20000000-0000-0000-0000-000000000002',
    vehicle_number: 'SCH001',
    carrier_id: '00000000-0000-0000-0000-000000000002'
  }),
  (:Vehicle {
    id: '20000000-0000-0000-0000-000000000003',
    vehicle_number: 'JBH001',
    carrier_id: '00000000-0000-0000-0000-000000000003'
  });

// Create drivers
CREATE
  (:Driver {
    id: 'd1f8b2c4-5e6f-4a7b-8c9d-0e1f2a3b4c5d',
    name: 'Robert Wilson',
    carrier_id: '00000000-0000-0000-0000-000000000001'
  }),
  (:Driver {
    id: 'a4c1e5f7-8b9c-7d0e-1f2a-3b4c5d6e7f8a',
    name: 'Maria Garcia',
    carrier_id: '00000000-0000-0000-0000-000000000001'
  }),
  (:Driver {
    id: 'c6e3a9b1-0d2f-9e4c-5d6e-7f8a9b0c1d2e',
    name: 'Carlos Rodriguez',
    carrier_id: '00000000-0000-0000-0000-000000000001'
  });

// Route relationships
CREATE
  (route1)-[:INCLUDES_STOP {
    stop_sequence: 1,
    stop_type: 'PICKUP',
    estimated_arrival: datetime('2024-01-15T08:00:00Z'),
    service_time_minutes: 60
  }]->(austin),
  (route1)-[:INCLUDES_STOP {
    stop_sequence: 2,
    stop_type: 'DELIVERY',
    estimated_arrival: datetime('2024-01-15T15:00:00Z'),
    service_time_minutes: 45
  }]->(houston),
  (route2)-[:INCLUDES_STOP {
    stop_sequence: 1,
    stop_type: 'PICKUP',
    estimated_arrival: datetime('2024-01-16T09:00:00Z'),
    service_time_minutes: 75
  }]->(dallas),
  (route2)-[:INCLUDES_STOP {
    stop_sequence: 2,
    stop_type: 'DELIVERY',
    estimated_arrival: datetime('2024-01-16T16:00:00Z'),
    service_time_minutes: 60
  }]->(sanantonio);

// Vehicle-Route assignments
CREATE
  (vehicle1)-[:FOLLOWS_ROUTE {
    route_start: datetime('2024-01-15T06:30:00Z'),
    route_end: datetime('2024-01-15T16:30:00Z')
  }]->(route1),
  (vehicle2)-[:FOLLOWS_ROUTE {
    route_start: datetime('2024-01-16T07:30:00Z'),
    route_end: datetime('2024-01-16T17:30:00Z')
  }]->(route2);

// Hub relationships
CREATE
  (hub_austin)-[:LOCATED_AT]->(austin),
  (hub_houston)-[:LOCATED_AT]->(houston),
  (hub_dallas)-[:LOCATED_AT]->(dallas);

// Create basic route connections between locations
CREATE
  (austin)-[:ROUTE_SEGMENT {
    distance: 165.0,
    travel_time: 180,
    highway: 'I-10',
    toll_cost: 0.0,
    fuel_cost_estimate: 45.50,
    road_type: 'HIGHWAY',
    traffic_patterns: {morning_rush: 1.2, evening_rush: 1.3, normal: 1.0}
  }]->(houston),
  (houston)-[:ROUTE_SEGMENT {
    distance: 165.0,
    travel_time: 180,
    highway: 'I-10',
    toll_cost: 0.0,
    fuel_cost_estimate: 45.50,
    road_type: 'HIGHWAY',
    traffic_patterns: {morning_rush: 1.2, evening_rush: 1.3, normal: 1.0}
  }]->(austin),
  (austin)-[:ROUTE_SEGMENT {
    distance: 195.0,
    travel_time: 210,
    highway: 'I-35',
    toll_cost: 0.0,
    fuel_cost_estimate: 52.75,
    road_type: 'HIGHWAY',
    traffic_patterns: {morning_rush: 1.4, evening_rush: 1.5, normal: 1.0}
  }]->(dallas),
  (dallas)-[:ROUTE_SEGMENT {
    distance: 195.0,
    travel_time: 210,
    highway: 'I-35',
    toll_cost: 0.0,
    fuel_cost_estimate: 52.75,
    road_type: 'HIGHWAY',
    traffic_patterns: {morning_rush: 1.4, evening_rush: 1.5, normal: 1.0}
  }]->(austin),
  (dallas)-[:ROUTE_SEGMENT {
    distance: 275.0,
    travel_time: 300,
    highway: 'I-35',
    toll_cost: 0.0,
    fuel_cost_estimate: 72.25,
    road_type: 'HIGHWAY',
    traffic_patterns: {morning_rush: 1.1, evening_rush: 1.2, normal: 1.0}
  }]->(sanantonio),
  (sanantonio)-[:ROUTE_SEGMENT {
    distance: 275.0,
    travel_time: 300,
    highway: 'I-35',
    toll_cost: 0.0,
    fuel_cost_estimate: 72.25,
    road_type: 'HIGHWAY',
    traffic_patterns: {morning_rush: 1.1, evening_rush: 1.2, normal: 1.0}
  }]->(dallas),
  (houston)-[:ROUTE_SEGMENT {
    distance: 240.0,
    travel_time: 265,
    highway: 'I-45',
    toll_cost: 0.0,
    fuel_cost_estimate: 65.00,
    road_type: 'HIGHWAY',
    traffic_patterns: {morning_rush: 1.3, evening_rush: 1.4, normal: 1.0}
  }]->(dallas),
  (dallas)-[:ROUTE_SEGMENT {
    distance: 240.0,
    travel_time: 265,
    highway: 'I-45',
    toll_cost: 0.0,
    fuel_cost_estimate: 65.00,
    road_type: 'HIGHWAY',
    traffic_patterns: {morning_rush: 1.3, evening_rush: 1.4, normal: 1.0}
  }]->(houston);

// Add Austin area local connections
CREATE
  (austin)-[:ROUTE_SEGMENT {
    distance: 20.0,
    travel_time: 25,
    highway: 'I-35',
    toll_cost: 0.0,
    fuel_cost_estimate: 5.50,
    road_type: 'ARTERIAL'
  }]->(roundrock),
  (roundrock)-[:ROUTE_SEGMENT {
    distance: 20.0,
    travel_time: 25,
    highway: 'I-35',
    toll_cost: 0.0,
    fuel_cost_estimate: 5.50,
    road_type: 'ARTERIAL'
  }]->(austin),
  (austin)-[:ROUTE_SEGMENT {
    distance: 18.0,
    travel_time: 22,
    highway: 'US-183',
    toll_cost: 0.0,
    fuel_cost_estimate: 4.90,
    road_type: 'ARTERIAL'
  }]->(cedarpark),
  (cedarpark)-[:ROUTE_SEGMENT {
    distance: 18.0,
    travel_time: 22,
    highway: 'US-183',
    toll_cost: 0.0,
    fuel_cost_estimate: 4.90,
    road_type: 'ARTERIAL'
  }]->(austin);

// Performance and historical relationships
CREATE
  (driver1)-[:HAS_SERVED {
    service_date: date('2024-01-10'),
    load_id: 'previous_load_001',
    on_time_pickup: true,
    on_time_delivery: true,
    customer_rating: 4.8,
    fuel_efficiency: 7.2,
    distance_driven: 165.0
  }]->(houston),
  (driver2)-[:HAS_SERVED {
    service_date: date('2024-01-12'),
    load_id: 'previous_load_002',
    on_time_pickup: true,
    on_time_delivery: false,
    customer_rating: 4.2,
    fuel_efficiency: 6.8,
    distance_driven: 275.0
  }]->(sanantonio);

// Nearby location relationships for optimization
CREATE
  (austin)-[:NEARBY_LOCATION {
    distance: 20.0,
    travel_time: 25,
    accessibility_score: 0.9
  }]->(roundrock),
  (austin)-[:NEARBY_LOCATION {
    distance: 18.0,
    travel_time: 22,
    accessibility_score: 0.85
  }]->(cedarpark),
  (roundrock)-[:NEARBY_LOCATION {
    distance: 12.0,
    travel_time: 15,
    accessibility_score: 0.75
  }]->(cedarpark);

MATCH (houston:Location {id: 'LOC_HOUSTON'}), (atlanta:Location {id: 'LOC_ATLANTA'})
CREATE (houston)-[:ROUTE_SEGMENT {
  distance: 790.2,
  estimated_time: 720,
  highway: 'I-10 E to I-65 N',
  toll_cost: 45.75,
  traffic_level: 'high'
}]->(atlanta);

MATCH (dallas:Location {id: 'LOC_DALLAS'}), (chicago:Location {id: 'LOC_CHICAGO'})
CREATE (dallas)-[:ROUTE_SEGMENT {
  distance: 921.8,
  estimated_time: 840,
  highway: 'I-35 N to I-44 E',
  toll_cost: 35.25,
  traffic_level: 'moderate'
}]->(chicago);

MATCH (atlanta:Location {id: 'LOC_ATLANTA'}), (chicago:Location {id: 'LOC_CHICAGO'})
CREATE (atlanta)-[:ROUTE_SEGMENT {
  distance: 716.4,
  estimated_time: 660,
  highway: 'I-75 N to I-65 N',
  toll_cost: 28.50,
  traffic_level: 'high'
}]->(chicago);

MATCH (chicago:Location {id: 'LOC_CHICAGO'}), (newyork:Location {id: 'LOC_NEW_YORK'})
CREATE (chicago)-[:ROUTE_SEGMENT {
  distance: 790.1,
  estimated_time: 720,
  highway: 'I-80 E to I-280 E',
  toll_cost: 65.25,
  traffic_level: 'very_high'
}]->(newyork);

MATCH (losangeles:Location {id: 'LOC_LOS_ANGELES'}), (houston:Location {id: 'LOC_HOUSTON'})
CREATE (losangeles)-[:ROUTE_SEGMENT {
  distance: 1547.1,
  estimated_time: 1380,
  highway: 'I-10 E',
  toll_cost: 25.00,
  traffic_level: 'moderate'
}]->(houston);

// Create bidirectional routes (return trips)
MATCH (a:Location)-[r:ROUTE_SEGMENT]->(b:Location)
WHERE NOT exists((b)-[:ROUTE_SEGMENT]->(a))
CREATE (b)-[:ROUTE_SEGMENT {
  distance: r.distance,
  estimated_time: r.estimated_time,
  highway: r.highway,
  toll_cost: r.toll_cost,
  traffic_level: r.traffic_level
}]->(a);

// Create carrier service relationships
MATCH (abc:Carrier {id: 'CARRIER_ABC'}), (houston:Location {id: 'LOC_HOUSTON'})
CREATE (abc)-[:SERVICES {
  frequency: 'daily',
  capacity: 10,
  service_type: 'LTL'
}]->(houston);

MATCH (abc:Carrier {id: 'CARRIER_ABC'}), (dallas:Location {id: 'LOC_DALLAS'})
CREATE (abc)-[:SERVICES {
  frequency: 'daily',
  capacity: 8,
  service_type: 'FTL'
}]->(dallas);

MATCH (xyz:Carrier {id: 'CARRIER_XYZ'}), (houston:Location {id: 'LOC_HOUSTON'})
CREATE (xyz)-[:SERVICES {
  frequency: 'twice_daily',
  capacity: 15,
  service_type: 'LTL'
}]->(houston);

MATCH (xyz:Carrier {id: 'CARRIER_XYZ'}), (atlanta:Location {id: 'LOC_ATLANTA'})
CREATE (xyz)-[:SERVICES {
  frequency: 'daily',
  capacity: 12,
  service_type: 'FTL'
}]->(atlanta);

// Create sample routes
CREATE (route1:Route {
  id: 'ROUTE_HOU_ATL_001',
  name: 'Houston to Atlanta Express',
  total_distance: 790.2,
  estimated_total_time: 720,
  route_type: 'long_haul',
  active: true
});

MATCH (route1:Route {id: 'ROUTE_HOU_ATL_001'}), 
      (houston:Location {id: 'LOC_HOUSTON'}), 
      (atlanta:Location {id: 'LOC_ATLANTA'})
CREATE (route1)-[:STARTS_AT]->(houston),
       (route1)-[:ENDS_AT]->(atlanta);

// Add some network analysis functions
// This creates a simple procedure to find shortest path between locations
CALL apoc.custom.asProcedure(
  'findShortestRoute',
  'MATCH (start:Location {id: $startId}), (end:Location {id: $endId})
   CALL apoc.algo.dijkstra(start, end, "ROUTE_SEGMENT", "distance") YIELD path, weight
   RETURN path, weight as total_distance',
  'read',
  [['path', 'PATH'], ['total_distance', 'FLOAT']],
  [['startId', 'STRING'], ['endId', 'STRING']]
);

// Create indexes for common queries
CREATE INDEX location_state IF NOT EXISTS FOR (l:Location) ON (l.state);
CREATE INDEX carrier_service_area IF NOT EXISTS FOR (c:Carrier) ON (c.service_areas);
CREATE INDEX route_active IF NOT EXISTS FOR (r:Route) ON (r.active);
