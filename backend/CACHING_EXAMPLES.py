"""
EXAMPLE: How to add caching to existing routes

This shows before/after comparison for adding Redis caching
to expensive AI/ML operations.
"""

# ============================================================
# BEFORE (NO CACHING) - Slow and expensive
# ============================================================

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class RecommendationRequest(BaseModel):
    user_id: str
    context: dict = {}


@router.post("/api/v1/recommendations")
async def get_recommendations(request: RecommendationRequest):
    """
    Get AI recommendations
    
    PROBLEM: This calls expensive ML model EVERY TIME
    - Slow: 2-3 seconds per request
    - Expensive: Uses GPU/CPU resources
    - Same user = same result for hours
    """
    # Expensive ML operation
    recommendations = await recommendation_engine.generate(
        user_id=request.user_id,
        context=request.context
    )
    
    return {
        "user_id": request.user_id,
        "recommendations": recommendations
    }


# ============================================================
# AFTER (WITH CACHING) - Fast and cheap!
# ============================================================

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.cache import cache_response  # ← ADD THIS IMPORT

router = APIRouter()

class RecommendationRequest(BaseModel):
    user_id: str
    context: dict = {}


@router.post("/api/v1/recommendations")
@cache_response(ttl=600)  # ← ADD THIS DECORATOR (10 min cache)
async def get_recommendations(request: RecommendationRequest):
    """
    Get AI recommendations
    
    IMPROVEMENT: Now caches results for 10 minutes
    - First request: 2-3 seconds (cache MISS)
    - Next requests: <50ms (cache HIT)
    - 50-70% cost reduction!
    """
    # Same code - cache decorator handles everything
    recommendations = await recommendation_engine.generate(
        user_id=request.user_id,
        context=request.context
    )
    
    return {
        "user_id": request.user_id,
        "recommendations": recommendations
    }


# ============================================================
# MORE EXAMPLES
# ============================================================

# Example 1: HuggingFace model search (very slow without cache)
@router.get("/api/v1/models/search")
@cache_response(ttl=3600, key_prefix="hf_search")  # 1 hour
async def search_models(query: str):
    """Cache expensive HuggingFace API calls"""
    results = await huggingface_hub.search(query)
    return results


# Example 2: ML predictions (expensive GPU computation)
@router.post("/api/v1/predict/churn")
@cache_response(ttl=1800)  # 30 minutes
async def predict_churn(user_id: str):
    """Cache ML model predictions"""
    prediction = await churn_model.predict(user_id)
    return prediction


# Example 3: Sentiment analysis (NLP is slow)
@router.post("/api/v1/sentiment/analyze")
@cache_response(ttl=900)  # 15 minutes
async def analyze_sentiment(text: str):
    """Cache sentiment analysis results"""
    sentiment = await sentiment_analyzer.analyze(text)
    return sentiment


# ============================================================
# WHEN NOT TO CACHE
# ============================================================

# DON'T cache real-time data
@router.get("/api/v1/realtime/stock-price")
# NO @cache_response - data changes constantly
async def get_stock_price(symbol: str):
    return await stock_api.get_price(symbol)


# DON'T cache user mutations
@router.post("/api/v1/users/{user_id}/update")
# NO @cache_response - writes should not be cached
async def update_user(user_id: str, data: dict):
    return await db.update_user(user_id, data)


# ============================================================
# CACHE INVALIDATION
# ============================================================

from utils.cache import invalidate_cache

@router.post("/api/v1/users/{user_id}/preferences")
async def update_preferences(user_id: str, preferences: dict):
    """When user changes preferences, clear their recommendation cache"""
    
    # Update preferences
    await db.update_preferences(user_id, preferences)
    
    # Invalidate recommendation cache for this user
    invalidate_cache(f"cache:*{user_id}*recommendations*")
    
    return {"status": "updated"}


# ============================================================
# MONITORING CACHE PERFORMANCE
# ============================================================

from utils.cache import get_cache_stats

@router.get("/api/v1/cache/stats")
async def cache_statistics():
    """
    Get cache performance metrics
    
    Returns:
        {
            "status": "connected",
            "total_cache_keys": 1234,
            "keyspace_hits": 5000,
            "keyspace_misses": 1000,
            "hit_rate": 83.33,
            "db_keys": 1234
        }
    """
    return get_cache_stats()


# ============================================================
# QUICK WINS: Add caching to these endpoints first
# ============================================================

"""
HIGHEST IMPACT (add caching here first):

1. /api/v1/predict/* - ML predictions (slow GPU operations)
   @cache_response(ttl=1800)  # 30 min

2. /huggingface/* - External API calls (slow network)
   @cache_response(ttl=3600)  # 1 hour

3. /api/v1/recommendations/* - Recommendation engine (expensive)
   @cache_response(ttl=600)   # 10 min

4. /api/v1/sentiment/* - NLP analysis (CPU intensive)
   @cache_response(ttl=900)   # 15 min

5. /api/v1/anomaly/* - Anomaly detection (complex computation)
   @cache_response(ttl=300)   # 5 min

Expected results:
- 50-70% reduction in response time
- 50-70% reduction in compute costs
- Better user experience
- Can handle 10x more traffic
"""
