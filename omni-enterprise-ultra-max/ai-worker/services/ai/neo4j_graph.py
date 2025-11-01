"""
Neo4j Graph Service - Advanced Recommendation Engine
Implements graph-based recommendations using Neo4j
"""

import os
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Neo4j connection settings
NEO4J_ENABLED = os.getenv("NEO4J_URI") is not None
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

if NEO4J_ENABLED:
    try:
        from neo4j import GraphDatabase
        
        class Neo4jGraphService:
            """Neo4j graph database service for advanced recommendations"""
            
            def __init__(self):
                self.driver = None
                if NEO4J_URI and NEO4J_PASSWORD:
                    try:
                        self.driver = GraphDatabase.driver(
                            NEO4J_URI,
                            auth=(NEO4J_USER, NEO4J_PASSWORD)
                        )
                        logger.info("✅ Neo4j connected successfully")
                    except Exception as e:
                        logger.warning(f"Neo4j connection failed: {e}")
                        self.driver = None
            
            def close(self):
                if self.driver:
                    self.driver.close()
            
            async def get_user_recommendations(
                self, 
                user_id: str, 
                limit: int = 10
            ) -> List[Dict[str, Any]]:
                """
                Get personalized recommendations based on user's graph connections
                Uses collaborative filtering + content similarity
                """
                if not self.driver:
                    return self._fallback_recommendations(user_id, limit)
                
                try:
                    with self.driver.session() as session:
                        # Cypher query for collaborative filtering
                        query = """
                        MATCH (u:User {id: $user_id})-[:PURCHASED|VIEWED]->(p:Product)
                        MATCH (p)<-[:PURCHASED|VIEWED]-(other:User)
                        MATCH (other)-[:PURCHASED|VIEWED]->(rec:Product)
                        WHERE NOT (u)-[:PURCHASED|VIEWED]->(rec)
                        WITH rec, COUNT(DISTINCT other) as score,
                             COLLECT(DISTINCT other.id)[0..3] as similar_users
                        RETURN rec.id as product_id,
                               rec.name as product_name,
                               rec.category as category,
                               score,
                               similar_users
                        ORDER BY score DESC
                        LIMIT $limit
                        """
                        
                        result = session.run(query, user_id=user_id, limit=limit)
                        
                        recommendations = []
                        for record in result:
                            recommendations.append({
                                "product_id": record["product_id"],
                                "product_name": record["product_name"],
                                "category": record["category"],
                                "score": record["score"],
                                "reason": f"Users similar to you also purchased this",
                                "similar_users": record["similar_users"]
                            })
                        
                        return recommendations
                
                except Exception as e:
                    logger.error(f"Neo4j recommendation query failed: {e}")
                    return self._fallback_recommendations(user_id, limit)
            
            async def get_product_similarities(
                self, 
                product_id: str, 
                limit: int = 5
            ) -> List[Dict[str, Any]]:
                """
                Find similar products based on graph structure
                Uses pattern matching on user behavior
                """
                if not self.driver:
                    return []
                
                try:
                    with self.driver.session() as session:
                        query = """
                        MATCH (p:Product {id: $product_id})<-[:PURCHASED|VIEWED]-(u:User)
                        MATCH (u)-[:PURCHASED|VIEWED]->(similar:Product)
                        WHERE similar.id <> $product_id
                        WITH similar, COUNT(DISTINCT u) as common_users,
                             COLLECT(DISTINCT u.id)[0..3] as users
                        RETURN similar.id as product_id,
                               similar.name as product_name,
                               similar.category as category,
                               common_users as similarity_score,
                               users
                        ORDER BY common_users DESC
                        LIMIT $limit
                        """
                        
                        result = session.run(query, product_id=product_id, limit=limit)
                        
                        similarities = []
                        for record in result:
                            similarities.append({
                                "product_id": record["product_id"],
                                "product_name": record["product_name"],
                                "category": record["category"],
                                "similarity_score": record["similarity_score"],
                                "common_users": record["users"]
                            })
                        
                        return similarities
                
                except Exception as e:
                    logger.error(f"Neo4j similarity query failed: {e}")
                    return []
            
            async def track_user_interaction(
                self,
                user_id: str,
                product_id: str,
                interaction_type: str = "VIEWED"
            ) -> bool:
                """
                Track user-product interactions in the graph
                Creates/updates relationships
                """
                if not self.driver:
                    return False
                
                try:
                    with self.driver.session() as session:
                        query = """
                        MERGE (u:User {id: $user_id})
                        MERGE (p:Product {id: $product_id})
                        MERGE (u)-[r:%s]->(p)
                        ON CREATE SET r.first_interaction = timestamp(),
                                     r.count = 1
                        ON MATCH SET r.last_interaction = timestamp(),
                                    r.count = r.count + 1
                        RETURN r
                        """ % interaction_type
                        
                        session.run(query, user_id=user_id, product_id=product_id)
                        return True
                
                except Exception as e:
                    logger.error(f"Failed to track interaction: {e}")
                    return False
            
            async def get_trending_products(
                self,
                category: Optional[str] = None,
                time_window_hours: int = 24,
                limit: int = 10
            ) -> List[Dict[str, Any]]:
                """
                Get trending products based on recent interactions
                """
                if not self.driver:
                    return []
                
                try:
                    with self.driver.session() as session:
                        category_filter = ""
                        if category:
                            category_filter = "AND p.category = $category"
                        
                        query = f"""
                        MATCH (u:User)-[r:PURCHASED|VIEWED]->(p:Product)
                        WHERE r.last_interaction > timestamp() - ($hours * 3600 * 1000)
                        {category_filter}
                        WITH p, COUNT(DISTINCT u) as user_count,
                             SUM(r.count) as total_interactions
                        RETURN p.id as product_id,
                               p.name as product_name,
                               p.category as category,
                               user_count,
                               total_interactions,
                               (user_count * 2 + total_interactions) as trending_score
                        ORDER BY trending_score DESC
                        LIMIT $limit
                        """
                        
                        params = {
                            "hours": time_window_hours,
                            "limit": limit
                        }
                        if category:
                            params["category"] = category
                        
                        result = session.run(query, **params)
                        
                        trending = []
                        for record in result:
                            trending.append({
                                "product_id": record["product_id"],
                                "product_name": record["product_name"],
                                "category": record["category"],
                                "unique_users": record["user_count"],
                                "total_interactions": record["total_interactions"],
                                "trending_score": record["trending_score"]
                            })
                        
                        return trending
                
                except Exception as e:
                    logger.error(f"Failed to get trending products: {e}")
                    return []
            
            async def find_user_communities(
                self,
                min_community_size: int = 5
            ) -> List[Dict[str, Any]]:
                """
                Identify user communities/clusters based on behavior
                Uses graph algorithms (if available)
                """
                if not self.driver:
                    return []
                
                try:
                    with self.driver.session() as session:
                        # Simple community detection via common products
                        query = """
                        MATCH (u1:User)-[:PURCHASED]->(p:Product)<-[:PURCHASED]-(u2:User)
                        WHERE u1.id < u2.id
                        WITH u1, u2, COUNT(DISTINCT p) as common_products
                        WHERE common_products >= 3
                        RETURN u1.id as user1, u2.id as user2, common_products
                        LIMIT 100
                        """
                        
                        result = session.run(query)
                        
                        # Build community clusters
                        clusters = []
                        for record in result:
                            clusters.append({
                                "user1": record["user1"],
                                "user2": record["user2"],
                                "strength": record["common_products"]
                            })
                        
                        return clusters
                
                except Exception as e:
                    logger.error(f"Failed to find communities: {e}")
                    return []
            
            def _fallback_recommendations(
                self, 
                user_id: str, 
                limit: int
            ) -> List[Dict[str, Any]]:
                """Fallback recommendations when Neo4j is unavailable"""
                return [
                    {
                        "product_id": f"prod_{i}",
                        "product_name": f"Recommended Product {i}",
                        "category": "general",
                        "score": 10 - i,
                        "reason": "Popular item"
                    }
                    for i in range(1, min(limit + 1, 6))
                ]
        
        # Singleton instance
        _neo4j_service = Neo4jGraphService()
        
        def get_neo4j_service() -> Neo4jGraphService:
            return _neo4j_service
    
    except ImportError:
        logger.warning("Neo4j driver not installed. Graph features disabled.")
        NEO4J_ENABLED = False

if not NEO4J_ENABLED:
    # Dummy service when Neo4j is disabled
    class Neo4jGraphService:
        async def get_user_recommendations(self, user_id: str, limit: int = 10):
            return []
        
        async def get_product_similarities(self, product_id: str, limit: int = 5):
            return []
        
        async def track_user_interaction(self, user_id: str, product_id: str, interaction_type: str = "VIEWED"):
            return False
        
        async def get_trending_products(self, category=None, time_window_hours=24, limit=10):
            return []
        
        async def find_user_communities(self, min_community_size=5):
            return []
    
    def get_neo4j_service() -> Neo4jGraphService:
        return Neo4jGraphService()
