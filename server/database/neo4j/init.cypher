// Neo4j initialization for TMS graph data
// Create constraints and indexes
CREATE CONSTRAINT carrier_id IF NOT EXISTS FOR (c:Carrier) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT location_id IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE;
CREATE CONSTRAINT route_id IF NOT EXISTS FOR (r:Route) REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT hub_id IF NOT EXISTS FOR (h:Hub) REQUIRE h.id IS UNIQUE;

// Create indexes for performance
CREATE INDEX location_coordinates IF NOT EXISTS FOR (l:Location) ON (l.latitude, l.longitude);
CREATE INDEX route_distance IF NOT EXISTS FOR ()-[r:ROUTE_SEGMENT]->() ON (r.distance);

// Create sample locations (major cities and hubs)
CREATE 
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
  (atlanta:Location {
    id: 'LOC_ATLANTA',
    name: 'Atlanta, GA',
    city: 'Atlanta',
    state: 'GA',
    zipcode: '30309',
    latitude: 33.7490,
    longitude: -84.3880,
    type: 'city'
  }),
  (chicago:Location {
    id: 'LOC_CHICAGO',
    name: 'Chicago, IL',
    city: 'Chicago',
    state: 'IL',
    zipcode: '60601',
    latitude: 41.8781,
    longitude: -87.6298,
    type: 'city'
  }),
  (losangeles:Location {
    id: 'LOC_LOS_ANGELES',
    name: 'Los Angeles, CA',
    city: 'Los Angeles',
    state: 'CA',
    zipcode: '90012',
    latitude: 34.0522,
    longitude: -118.2437,
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
  });

// Create transportation hubs
CREATE 
  (houston_hub:Hub {
    id: 'HUB_HOUSTON_001',
    name: 'Houston Distribution Hub',
    location_id: 'LOC_HOUSTON',
    capacity: 1000,
    hub_type: 'distribution',
    operating_hours: '24/7'
  }),
  (atlanta_hub:Hub {
    id: 'HUB_ATLANTA_001',
    name: 'Atlanta Logistics Center',
    location_id: 'LOC_ATLANTA',
    capacity: 1500,
    hub_type: 'cross_dock',
    operating_hours: '5AM-11PM'
  }),
  (chicago_hub:Hub {
    id: 'HUB_CHICAGO_001',
    name: 'Chicago Regional Hub',
    location_id: 'LOC_CHICAGO',
    capacity: 2000,
    hub_type: 'regional',
    operating_hours: '24/7'
  });

// Create carriers
CREATE 
  (abc_transport:Carrier {
    id: 'CARRIER_ABC',
    name: 'ABC Transportation',
    mc_number: 'MC123456',
    dot_number: 'DOT789012',
    fleet_size: 50,
    service_areas: ['TX', 'LA', 'AR', 'OK']
  }),
  (xyz_logistics:Carrier {
    id: 'CARRIER_XYZ',
    name: 'XYZ Logistics',
    mc_number: 'MC234567',
    dot_number: 'DOT890123',
    fleet_size: 75,
    service_areas: ['TX', 'GA', 'FL', 'AL', 'MS']
  });

// Link hubs to their locations
MATCH (h:Hub), (l:Location)
WHERE h.location_id = l.id
CREATE (h)-[:LOCATED_AT]->(l);

// Create route segments between major locations
MATCH (houston:Location {id: 'LOC_HOUSTON'}), (dallas:Location {id: 'LOC_DALLAS'})
CREATE (houston)-[:ROUTE_SEGMENT {
  distance: 239.1,
  estimated_time: 240,
  highway: 'I-45',
  toll_cost: 15.50,
  traffic_level: 'moderate'
}]->(dallas);

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
