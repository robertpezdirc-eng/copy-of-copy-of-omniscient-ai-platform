"""
Redis Caching Layer for Omni Platform
Simple decorator-based caching for expensive operations
"""
import json
import hashlib
import logging
from functools import wraps
from typing import Optional, Callable, Any
import os

logger = logging.getLogger(__name__)

# Redis client (lazy initialized)
_redis_client = None


def get_redis_client():
    """Get or create Redis client"""
    global _redis_client
    if _redis_client is None:
        try:
            import redis
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            redis_password = os.getenv("REDIS_PASSWORD")
            
            _redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            # Test connection
            _redis_client.ping()
            logger.info(f"✅ Redis connected: {redis_host}:{redis_port}")
        except Exception as e:
            logger.warning(f"⚠️ Redis not available: {e}. Caching disabled.")
            _redis_client = None
    return _redis_client


def cache_response(ttl: int = 3600, key_prefix: str = ""):
    """
    Cache decorator for async functions
    
    Usage:
        @cache_response(ttl=1800)  # 30 minutes
        async def expensive_function(user_id: str):
            return {"result": "data"}
    
    Args:
        ttl: Time to live in seconds (default 1 hour)
        key_prefix: Optional prefix for cache key
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            redis = get_redis_client()
            
            # If Redis unavailable, just call function
            if redis is None:
                return await func(*args, **kwargs)
            
            # Generate cache key from function name + args + kwargs
            key_parts = [key_prefix or func.__name__]
            
            # Add args to key (skip 'self' for methods)
            for arg in args:
                if arg.__class__.__name__ not in ['Request', 'Response']:
                    key_parts.append(str(arg))
            
            # Add kwargs to key (sorted for consistency)
            for k, v in sorted(kwargs.items()):
                if k not in ['request', 'response']:
                    key_parts.append(f"{k}:{v}")
            
            # Create hash of key parts
            key_str = "|".join(key_parts)
            cache_key = f"cache:{hashlib.md5(key_str.encode()).hexdigest()}"
            
            try:
                # Try to get from cache
                cached = redis.get(cache_key)
                if cached:
                    logger.debug(f"🎯 Cache HIT: {func.__name__}")
                    return json.loads(cached)
                
                # Cache miss - execute function
                logger.debug(f"❌ Cache MISS: {func.__name__}")
                result = await func(*args, **kwargs)
                
                # Store in cache
                try:
                    redis.setex(cache_key, ttl, json.dumps(result))
                except (TypeError, ValueError) as e:
                    logger.warning(f"Cannot cache result for {func.__name__}: {e}")
                
                return result
                
            except Exception as e:
                logger.error(f"Cache error in {func.__name__}: {e}")
                # On error, just call function
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def invalidate_cache(pattern: str):
    """
    Invalidate all cache keys matching pattern
    
    Usage:
        invalidate_cache("cache:*user_123*")
    """
    redis = get_redis_client()
    if redis is None:
        return
    
    try:
        keys = redis.keys(pattern)
        if keys:
            redis.delete(*keys)
            logger.info(f"🗑️ Invalidated {len(keys)} cache keys matching {pattern}")
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")


def get_cache_stats() -> dict:
    """Get cache statistics"""
    redis = get_redis_client()
    if redis is None:
        return {"status": "unavailable"}
    
    try:
        info = redis.info("stats")
        keyspace = redis.info("keyspace")
        
        cache_keys = len(redis.keys("cache:*"))
        
        return {
            "status": "connected",
            "total_cache_keys": cache_keys,
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "hit_rate": round(
                info.get("keyspace_hits", 0) / 
                max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1) * 100,
                2
            ),
            "db_keys": keyspace.get("db0", {}).get("keys", 0) if keyspace else 0
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {"status": "error", "error": str(e)}


# Example usage in routes:
"""
from utils.cache import cache_response

@app.get("/api/v1/recommendations/{user_id}")
@cache_response(ttl=600)  # Cache for 10 minutes
async def get_recommendations(user_id: str):
    # Expensive ML operation
    recommendations = await ml_service.generate_recommendations(user_id)
    return recommendations

@app.get("/api/v1/models/search")
@cache_response(ttl=3600, key_prefix="hf_search")  # Cache for 1 hour
async def search_models(query: str):
    # Expensive HuggingFace search
    results = await huggingface_hub.search(query)
    return results
"""
