"""
Hybrid Recommendation Engine
Combines Neo4j collaborative filtering + FAISS content-based + user behavior
"""
import logging
from typing import Dict, List, Any, Optional
import os
import numpy as np

logger = logging.getLogger(__name__)

# Optional Neo4j integration
NEO4J_ENABLED = os.getenv("NEO4J_URI") is not None
if NEO4J_ENABLED:
    try:
        from services.ai.neo4j_graph import get_neo4j_service
        logger.info("✅ Neo4j graph recommendations enabled")
    except ImportError:
        NEO4J_ENABLED = False
        logger.info("ℹ️ Neo4j not available, using standard recommendations")

# FAISS vector search for content-based filtering
try:
    from services.ai.vector_index import TenantVectorIndex
    FAISS_ENABLED = True
except ImportError:
    FAISS_ENABLED = False
    logger.warning("FAISS not available for content-based recommendations")


class RecommendationEngine:
    """
    Hybrid recommendation engine combining:
    1. Collaborative filtering (Neo4j graph patterns)
    2. Content-based filtering (FAISS vector similarity)
    3. Behavioral scoring (user engagement patterns)
    """
    
    def __init__(self):
        self.neo4j = None
        if NEO4J_ENABLED:
            try:
                self.neo4j = get_neo4j_service()
            except Exception as e:
                logger.warning(f"Neo4j initialization failed: {e}")
                self.neo4j = None
        
        self.faiss_indices: Dict[str, TenantVectorIndex] = {}
        
        # Ensemble weights
        self.weights = {
            "collaborative": 0.4,  # Neo4j graph patterns
            "content": 0.35,  # FAISS similarity
            "behavioral": 0.25  # User behavior
        }

    async def recommend_products(
        self,
        tenant_id: str,
        user_id: str,
        user_context: Dict[str, Any],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Hybrid product recommendations using ensemble scoring
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID
            user_context: User context with usage patterns
            top_k: Number of recommendations
        
        Returns:
            List of recommended products with scores
        """
        recommendations = {}
        
        # 1. Collaborative filtering (Neo4j)
        if self.neo4j:
            try:
                graph_recs = await self.neo4j.get_user_recommendations(user_id, limit=top_k * 2)
                for rec in graph_recs:
                    product_id = rec.get("product_id")
                    if product_id:
                        recommendations[product_id] = {
                            "collaborative_score": rec.get("score", 0.5),
                            "content_score": 0.0,
                            "behavioral_score": 0.0,
                            "data": rec
                        }
                logger.info(f"✅ Neo4j collaborative: {len(graph_recs)} recommendations")
            except Exception as e:
                logger.warning(f"Neo4j recommendations failed: {e}")
        
        # 2. Content-based filtering (FAISS)
        if FAISS_ENABLED and user_context.get("query"):
            try:
                faiss_index = self._get_faiss_index(tenant_id)
                query_text = user_context.get("query", "")
                similar_items = faiss_index.query(query_text, top_k=top_k * 2)
                
                for item_id, similarity_score in similar_items:
                    if item_id not in recommendations:
                        recommendations[item_id] = {
                            "collaborative_score": 0.0,
                            "content_score": 0.0,
                            "behavioral_score": 0.0,
                            "data": {"product_id": item_id}
                        }
                    recommendations[item_id]["content_score"] = similarity_score
                
                logger.info(f"✅ FAISS content-based: {len(similar_items)} recommendations")
            except Exception as e:
                logger.warning(f"FAISS recommendations failed: {e}")
        
        # 3. Behavioral scoring
        user_engagement = user_context.get("engagement_score", 0.5)
        for product_id in recommendations:
            # Boost based on user engagement patterns
            recommendations[product_id]["behavioral_score"] = self._calculate_behavioral_score(
                user_context,
                recommendations[product_id]["data"]
            )
        
        # 4. Ensemble scoring
        scored_recommendations = []
        for product_id, scores in recommendations.items():
            ensemble_score = (
                scores["collaborative_score"] * self.weights["collaborative"] +
                scores["content_score"] * self.weights["content"] +
                scores["behavioral_score"] * self.weights["behavioral"]
            )
            
            scored_recommendations.append({
                "product_id": product_id,
                "ensemble_score": ensemble_score,
                "scores": scores,
                "data": scores["data"]
            })
        
        # Sort by ensemble score
        scored_recommendations.sort(key=lambda x: x["ensemble_score"], reverse=True)
        
        # Format results
        results = []
        for rec in scored_recommendations[:top_k]:
            data = rec["data"]
            results.append({
                "product_id": rec["product_id"],
                "name": data.get("name", f"Product {rec['product_id']}"),
                "price": data.get("price", 0.0),
                "category": data.get("category", "general"),
                "confidence_score": rec["ensemble_score"],
                "recommendation_method": "hybrid_ensemble",
                "score_breakdown": {
                    "collaborative": rec["scores"]["collaborative_score"],
                    "content": rec["scores"]["content_score"],
                    "behavioral": rec["scores"]["behavioral_score"]
                },
                "reasoning": self._generate_reasoning(rec["scores"])
            })
        
        # Fallback if no recommendations
        if not results:
            logger.info("⚠️ No hybrid recommendations, using fallback")
            return await self._fallback_recommendations(top_k)
        
        return results
    
    def _get_faiss_index(self, tenant_id: str) -> TenantVectorIndex:
        """Get or create FAISS index for tenant"""
        if tenant_id not in self.faiss_indices:
            self.faiss_indices[tenant_id] = TenantVectorIndex(tenant_id)
        return self.faiss_indices[tenant_id]
    
    def _calculate_behavioral_score(
        self,
        user_context: Dict[str, Any],
        product_data: Dict[str, Any]
    ) -> float:
        """
        Calculate behavioral score based on user patterns
        
        Args:
            user_context: User context with usage patterns
            product_data: Product data
        
        Returns:
            Behavioral score (0-1)
        """
        score = 0.5  # Base score
        
        # Boost for high engagement users
        engagement = user_context.get("engagement_score", 0.5)
        score += engagement * 0.2
        
        # Boost for matching category
        user_category = user_context.get("preferred_category")
        product_category = product_data.get("category")
        if user_category and user_category == product_category:
            score += 0.2
        
        # Boost for usage patterns
        if user_context.get("high_api_usage") and "api" in str(product_data).lower():
            score += 0.15
        
        return min(1.0, score)
    
    def _generate_reasoning(self, scores: Dict[str, float]) -> str:
        """Generate human-readable reasoning for recommendation"""
        reasons = []
        
        if scores["collaborative_score"] > 0.6:
            reasons.append("users like you chose this")
        if scores["content_score"] > 0.6:
            reasons.append("matches your interests")
        if scores["behavioral_score"] > 0.6:
            reasons.append("fits your usage patterns")
        
        if not reasons:
            return "recommended for you"
        
        return ", ".join(reasons)
    
    async def _fallback_recommendations(self, top_k: int) -> List[Dict[str, Any]]:
        """Fallback recommendations when hybrid fails"""
        candidate_products = [
            {
                "product_id": "api_marketplace_pro",
                "name": "API Marketplace Pro",
                "price": 299.00,
                "category": "marketplace",
                "confidence_score": 0.85,
                "recommendation_method": "fallback",
                "reasoning": "Popular choice"
            },
            {
                "product_id": "ai_credits_1000",
                "name": "AI Credits Package (1000)",
                "price": 49.00,
                "category": "credits",
                "confidence_score": 0.78,
                "recommendation_method": "fallback",
                "reasoning": "Frequently purchased"
            }
        ]
        return candidate_products[:top_k]

    async def recommend_features(self, tenant_id: str, user_id: str, current_usage: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
        return [
            {
                "feature_id": "api_rate_monitoring",
                "name": "API Rate Monitoring",
                "category": "analytics",
                "benefit": "Prevent API throttling",
                "value_score": 0.92,
                "setup_time": "5 minutes",
                "relevance_score": 0.88,
                "tutorial_link": "/tutorials/api_rate_monitoring"
            }
        ][:top_k]
