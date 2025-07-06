"""
Neo4j Repository for TMS API.
Handles all graph database operations for route optimization and carrier-location relationships.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from .base import Neo4jRepository as BaseNeo4jRepository


class Neo4jRepository(BaseNeo4jRepository):
    """Repository for Neo4j graph operations"""
    
    async def find_shortest_route(self, start_location_id: str, end_location_id: str):
        """Find shortest route between locations"""
        query = """
        MATCH (start:Location {id: $start_id}), (end:Location {id: $end_id})
        CALL apoc.algo.dijkstra(start, end, 'ROUTE_SEGMENT', 'distance') 
        YIELD path, weight
        RETURN path, weight as total_distance
        """
        return await self.execute_single(query, start_id=start_location_id, end_id=end_location_id)
    
    async def find_nearby_carriers(self, location_id: str, service_type: str = None):
        """Find carriers serving a location"""
        query = """
        MATCH (c:Carrier)-[s:SERVICES]->(l:Location {id: $location_id})
        """
        if service_type:
            query += " WHERE s.service_type = $service_type"
            return await self.execute_query(query, location_id=location_id, service_type=service_type)
        else:
            return await self.execute_query(query, location_id=location_id)
    
    # ==================== LOAD NODE MANAGEMENT ====================
    
    async def create_load_node(self, load_id: str, customer_id: Optional[str] = None, 
                              pickup_location: Optional[str] = None, 
                              delivery_location: Optional[str] = None,
                              weight: Optional[float] = None, status: str = 'PENDING',
                              created_at: Optional[datetime] = None) -> None:
        """Create or update Load node in Neo4j"""
        query = """
        MERGE (l:Load {id: $load_id})
        SET l.customer_id = $customer_id,
            l.pickup_location = $pickup_location,
            l.delivery_location = $delivery_location,
            l.weight = $weight,
            l.status = $status,
            l.created_at = $created_at,
            l.updated_at = datetime()
        """
        await self.execute_command(
            query,
            load_id=load_id,
            customer_id=customer_id,
            pickup_location=pickup_location,
            delivery_location=delivery_location,
            weight=weight,
            status=status,
            created_at=created_at.isoformat() if created_at else None
        )
    
    async def update_load_status(self, load_id: str, status: str, 
                                delivered_at: Optional[datetime] = None, 
                                cancelled_at: Optional[datetime] = None) -> None:
        """Update load status and timestamp"""
        query = """
        MATCH (l:Load {id: $load_id})
        SET l.status = $status,
            l.updated_at = datetime()
        """
        params = {"load_id": load_id, "status": status}
        
        if delivered_at:
            query += ", l.delivered_at = $delivered_at"
            params["delivered_at"] = delivered_at.isoformat()
        
        if cancelled_at:
            query += ", l.cancelled_at = $cancelled_at" 
            params["cancelled_at"] = cancelled_at.isoformat()
            
        await self.execute_command(query, **params)
    
    async def remove_load_assignments(self, load_id: str) -> None:
        """Remove all assignment relationships for a load"""
        query = """
        MATCH (l:Load {id: $load_id})-[r:ASSIGNED_TO|TRANSPORTS]->()
        DELETE r
        """
        await self.execute_command(query, load_id=load_id)
    
    # ==================== DRIVER NODE MANAGEMENT ====================
    
    async def create_driver_node_if_not_exists(self, driver_id: str) -> None:
        """Create Driver node if it doesn't exist"""
        query = """
        MERGE (d:Driver {id: $driver_id})
        ON CREATE SET d.created_at = datetime()
        SET d.updated_at = datetime()
        """
        await self.execute_command(query, driver_id=driver_id)
    
    async def update_driver_status(self, driver_id: str, status: str, 
                                  updated_at: Optional[datetime] = None) -> None:
        """Update driver status"""
        query = """
        MATCH (d:Driver {id: $driver_id})
        SET d.status = $status,
            d.updated_at = $updated_at
        """
        await self.execute_command(
            query, 
            driver_id=driver_id, 
            status=status,
            updated_at=updated_at.isoformat() if updated_at else datetime.utcnow().isoformat()
        )
    
    async def update_driver_location(self, driver_id: str, latitude: float, longitude: float,
                                    updated_at: Optional[datetime] = None) -> None:
        """Update driver location"""
        query = """
        MATCH (d:Driver {id: $driver_id})
        SET d.latitude = $latitude,
            d.longitude = $longitude,
            d.location_updated_at = $updated_at
        """
        await self.execute_command(
            query,
            driver_id=driver_id,
            latitude=latitude,
            longitude=longitude,
            updated_at=updated_at.isoformat() if updated_at else datetime.utcnow().isoformat()
        )
    
    # ==================== VEHICLE NODE MANAGEMENT ====================
    
    async def create_vehicle_node_if_not_exists(self, vehicle_id: str) -> None:
        """Create Vehicle node if it doesn't exist"""
        query = """
        MERGE (v:Vehicle {id: $vehicle_id})
        ON CREATE SET v.created_at = datetime()
        SET v.updated_at = datetime()
        """
        await self.execute_command(query, vehicle_id=vehicle_id)
    
    async def update_vehicle_status(self, vehicle_id: str, status: str,
                                   updated_at: Optional[datetime] = None) -> None:
        """Update vehicle status"""
        query = """
        MATCH (v:Vehicle {id: $vehicle_id})
        SET v.status = $status,
            v.updated_at = $updated_at
        """
        await self.execute_command(
            query,
            vehicle_id=vehicle_id,
            status=status,
            updated_at=updated_at.isoformat() if updated_at else datetime.utcnow().isoformat()
        )
    
    async def update_vehicle_location(self, vehicle_id: str, latitude: float, longitude: float,
                                     updated_at: Optional[datetime] = None) -> None:
        """Update vehicle location"""
        query = """
        MATCH (v:Vehicle {id: $vehicle_id})
        SET v.latitude = $latitude,
            v.longitude = $longitude,
            v.location_updated_at = $updated_at
        """
        await self.execute_command(
            query,
            vehicle_id=vehicle_id,
            latitude=latitude,
            longitude=longitude,
            updated_at=updated_at.isoformat() if updated_at else datetime.utcnow().isoformat()
        )
    
    # ==================== ROUTE NODE MANAGEMENT ====================
    
    async def create_route_node(self, route_id: str, load_id: Optional[str] = None,
                               distance: Optional[float] = None, duration: Optional[float] = None,
                               optimized_at: Optional[datetime] = None) -> None:
        """Create Route node"""
        query = """
        MERGE (r:Route {id: $route_id})
        SET r.load_id = $load_id,
            r.distance = $distance,
            r.duration = $duration,
            r.optimized_at = $optimized_at,
            r.status = 'ACTIVE',
            r.updated_at = datetime()
        """
        await self.execute_command(
            query,
            route_id=route_id,
            load_id=load_id,
            distance=distance,
            duration=duration,
            optimized_at=optimized_at.isoformat() if optimized_at else None
        )
    
    async def update_route_status(self, route_id: str, status: str,
                                 completed_at: Optional[datetime] = None) -> None:
        """Update route status"""
        query = """
        MATCH (r:Route {id: $route_id})
        SET r.status = $status,
            r.updated_at = datetime()
        """
        params = {"route_id": route_id, "status": status}
        
        if completed_at:
            query += ", r.completed_at = $completed_at"
            params["completed_at"] = completed_at.isoformat()
            
        await self.execute_command(query, **params)
    
    # ==================== RELATIONSHIP MANAGEMENT ====================
    
    async def create_customer_load_relationship(self, customer_id: str, load_id: str) -> None:
        """Create ORDERS relationship between Customer and Load"""
        query = """
        MATCH (c:Customer {id: $customer_id}), (l:Load {id: $load_id})
        MERGE (c)-[:ORDERS]->(l)
        """
        await self.execute_command(query, customer_id=customer_id, load_id=load_id)
    
    async def create_driver_load_assignment(self, driver_id: str, load_id: str,
                                           assigned_at: Optional[datetime] = None) -> None:
        """Create ASSIGNED_TO relationship between Driver and Load"""
        query = """
        MATCH (d:Driver {id: $driver_id}), (l:Load {id: $load_id})
        MERGE (d)-[r:ASSIGNED_TO]->(l)
        SET r.assigned_at = $assigned_at
        """
        await self.execute_command(
            query,
            driver_id=driver_id,
            load_id=load_id,
            assigned_at=assigned_at.isoformat() if assigned_at else datetime.utcnow().isoformat()
        )
    
    async def create_vehicle_load_assignment(self, vehicle_id: str, load_id: str,
                                            assigned_at: Optional[datetime] = None) -> None:
        """Create TRANSPORTS relationship between Vehicle and Load"""
        query = """
        MATCH (v:Vehicle {id: $vehicle_id}), (l:Load {id: $load_id})
        MERGE (v)-[r:TRANSPORTS]->(l)
        SET r.assigned_at = $assigned_at
        """
        await self.execute_command(
            query,
            vehicle_id=vehicle_id,
            load_id=load_id,
            assigned_at=assigned_at.isoformat() if assigned_at else datetime.utcnow().isoformat()
        )
    
    async def create_driver_vehicle_relationship(self, driver_id: str, vehicle_id: str,
                                                assigned_at: Optional[datetime] = None) -> None:
        """Create DRIVES relationship between Driver and Vehicle"""
        query = """
        MATCH (d:Driver {id: $driver_id}), (v:Vehicle {id: $vehicle_id})
        MERGE (d)-[r:DRIVES]->(v)
        SET r.assigned_at = $assigned_at
        """
        await self.execute_command(
            query,
            driver_id=driver_id,
            vehicle_id=vehicle_id,
            assigned_at=assigned_at.isoformat() if assigned_at else datetime.utcnow().isoformat()
        )
    
    async def create_vehicle_carrier_relationship(self, vehicle_id: str, carrier_id: str) -> None:
        """Create OWNED_BY relationship between Vehicle and Carrier"""
        query = """
        MATCH (v:Vehicle {id: $vehicle_id}), (c:Carrier {id: $carrier_id})
        MERGE (v)-[:OWNED_BY]->(c)
        """
        await self.execute_command(query, vehicle_id=vehicle_id, carrier_id=carrier_id)
    
    async def create_route_load_relationship(self, route_id: str, load_id: str) -> None:
        """Create OPTIMIZES relationship between Route and Load"""
        query = """
        MATCH (r:Route {id: $route_id}), (l:Load {id: $load_id})
        MERGE (r)-[:OPTIMIZES]->(l)
        """
        await self.execute_command(query, route_id=route_id, load_id=load_id)
    
    async def create_route_driver_relationship(self, route_id: str, driver_id: str) -> None:
        """Create EXECUTED_BY relationship between Route and Driver"""
        query = """
        MATCH (r:Route {id: $route_id}), (d:Driver {id: $driver_id})
        MERGE (r)-[:EXECUTED_BY]->(d)
        """
        await self.execute_command(query, route_id=route_id, driver_id=driver_id)
    
    async def create_route_vehicle_relationship(self, route_id: str, vehicle_id: str) -> None:
        """Create USES_VEHICLE relationship between Route and Vehicle"""
        query = """
        MATCH (r:Route {id: $route_id}), (v:Vehicle {id: $vehicle_id})
        MERGE (r)-[:USES_VEHICLE]->(v)
        """
        await self.execute_command(query, route_id=route_id, vehicle_id=vehicle_id)
    
    # ==================== ADVANCED GRAPH QUERIES ====================
    
    async def find_available_drivers_near_location(self, latitude: float, longitude: float, 
                                                  radius_km: float = 50) -> List[Dict[str, Any]]:
        """Find available drivers within radius of location"""
        query = """
        MATCH (d:Driver)
        WHERE d.status = 'AVAILABLE' 
        AND d.latitude IS NOT NULL 
        AND d.longitude IS NOT NULL
        AND distance(
            point({longitude: d.longitude, latitude: d.latitude}),
            point({longitude: $longitude, latitude: $latitude})
        ) <= $radius_meters
        RETURN d.id as driver_id, d.latitude, d.longitude,
               distance(
                   point({longitude: d.longitude, latitude: d.latitude}),
                   point({longitude: $longitude, latitude: $latitude})
               ) as distance_meters
        ORDER BY distance_meters
        """
        return await self.execute_query(
            query,
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_km * 1000
        )
    
    async def find_carrier_performance_metrics(self, carrier_id: str) -> Dict[str, Any]:
        """Get carrier performance metrics from graph relationships"""
        query = """
        MATCH (c:Carrier {id: $carrier_id})
        OPTIONAL MATCH (c)<-[:OWNED_BY]-(v:Vehicle)-[:TRANSPORTS]->(l:Load)
        OPTIONAL MATCH (l)-[:ORDERS]-(customer:Customer)
        RETURN c.id as carrier_id,
               count(DISTINCT v) as vehicle_count,
               count(DISTINCT l) as total_loads,
               count(DISTINCT CASE WHEN l.status = 'DELIVERED' THEN l END) as delivered_loads,
               count(DISTINCT customer) as unique_customers,
               avg(CASE WHEN l.status = 'DELIVERED' THEN 1.0 ELSE 0.0 END) as delivery_rate
        """
        result = await self.execute_single(query, carrier_id=carrier_id)
        return dict(result) if result else {}
    
    async def find_load_optimization_candidates(self) -> List[Dict[str, Any]]:
        """Find loads that could benefit from route optimization"""
        query = """
        MATCH (l:Load)
        WHERE l.status IN ['PENDING', 'ASSIGNED'] 
        AND NOT (l)<-[:OPTIMIZES]-(:Route)
        OPTIONAL MATCH (d:Driver)-[:ASSIGNED_TO]->(l)
        OPTIONAL MATCH (v:Vehicle)-[:TRANSPORTS]->(l)
        RETURN l.id as load_id, l.status, l.pickup_location, l.delivery_location,
               d.id as driver_id, v.id as vehicle_id,
               l.created_at, l.weight
        ORDER BY l.created_at DESC
        """
        return await self.execute_query(query)
