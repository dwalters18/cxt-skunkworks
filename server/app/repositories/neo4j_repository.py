"""
Neo4j Repository for TMS API.
Handles all graph database operations for route optimization and carrier-location relationships.
"""

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
