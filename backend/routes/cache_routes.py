"""
Enhanced Redis Caching Routes
Analytics and optimization for Redis caching layer
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime, timezone
import logging

from database import redis_client, CacheManager

router = APIRouter()
logger = logging.getLogger(__name__)


class CacheStats(BaseModel):
    total_keys: int
    memory_used_mb: float
    hit_rate: float
    miss_rate: float
    evicted_keys: int
    expired_keys: int
    connected_clients: int
    uptime_seconds: int


class CacheKeyPattern(BaseModel):
    pattern: str
    count: int
    sample_keys: List[str]
    total_size_mb: float


class CacheWarmRequest(BaseModel):
    keys: List[str]
    data_source: str  # "database", "api", "computed"
    ttl: int = 3600


@router.get("/cache/stats", response_model=CacheStats)
async def get_cache_stats():
    """Get Redis cache statistics and performance metrics"""
    
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    try:
        info = await redis_client.info()
        stats = await redis_client.info('stats')
        memory = await redis_client.info('memory')
        
        # Calculate hit rate
        keyspace_hits = stats.get('keyspace_hits', 0)
        keyspace_misses = stats.get('keyspace_misses', 0)
        total_requests = keyspace_hits + keyspace_misses
        
        hit_rate = keyspace_hits / total_requests if total_requests > 0 else 0
        miss_rate = keyspace_misses / total_requests if total_requests > 0 else 0
        
        return CacheStats(
            total_keys=await redis_client.dbsize(),
            memory_used_mb=memory.get('used_memory', 0) / (1024 * 1024),
            hit_rate=round(hit_rate * 100, 2),
            miss_rate=round(miss_rate * 100, 2),
            evicted_keys=stats.get('evicted_keys', 0),
            expired_keys=stats.get('expired_keys', 0),
            connected_clients=info.get('connected_clients', 0),
            uptime_seconds=info.get('uptime_in_seconds', 0)
        )
    
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/analyze")
async def analyze_cache_patterns():
    """Analyze cache key patterns and usage"""
    
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    try:
        # Define common patterns to analyze
        patterns = [
            "user:*",
            "session:*",
            "api:*",
            "tenant:*",
            "analytics:*",
            "ai:*",
            "cache:*"
        ]
        
        pattern_analysis = []
        
        for pattern in patterns:
            keys = await redis_client.keys(pattern)
            
            if keys:
                # Sample first 10 keys
                sample_keys = keys[:10] if len(keys) > 10 else keys
                
                # Estimate size (simplified)
                total_size = 0
                for key in sample_keys:
                    try:
                        memory_usage = await redis_client.memory_usage(key)
                        if memory_usage:
                            total_size += memory_usage
                    except:
                        pass
                
                # Extrapolate to all keys
                avg_size = total_size / len(sample_keys) if sample_keys else 0
                estimated_total_size = avg_size * len(keys)
                
                pattern_analysis.append(CacheKeyPattern(
                    pattern=pattern,
                    count=len(keys),
                    sample_keys=sample_keys,
                    total_size_mb=estimated_total_size / (1024 * 1024)
                ))
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "patterns": pattern_analysis,
            "recommendations": _generate_cache_recommendations(pattern_analysis)
        }
    
    except Exception as e:
        logger.error(f"Error analyzing cache patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _generate_cache_recommendations(patterns: List[CacheKeyPattern]) -> List[str]:
    """Generate cache optimization recommendations"""
    
    recommendations = []
    
    total_keys = sum(p.count for p in patterns)
    
    if total_keys > 100000:
        recommendations.append("Consider implementing key expiration policies - total keys exceeds 100k")
    
    for pattern in patterns:
        if pattern.total_size_mb > 100:
            recommendations.append(f"Pattern '{pattern.pattern}' uses {pattern.total_size_mb:.1f}MB - consider reducing TTL or data size")
        
        if pattern.count > 50000:
            recommendations.append(f"Pattern '{pattern.pattern}' has {pattern.count} keys - consider implementing key rotation")
    
    if not recommendations:
        recommendations.append("Cache usage is optimal")
    
    return recommendations


@router.post("/cache/warm")
async def warm_cache(request: CacheWarmRequest):
    """Warm cache with frequently accessed data"""
    
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    try:
        warmed_keys = 0
        
        for key in request.keys:
            # In production, fetch data from actual source
            # For now, store placeholder
            placeholder_data = f"warmed_data_{key}_{datetime.now(timezone.utc).isoformat()}"
            
            await CacheManager.set(key, placeholder_data, ttl=request.ttl)
            warmed_keys += 1
        
        return {
            "status": "success",
            "warmed_keys": warmed_keys,
            "ttl": request.ttl,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error warming cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/invalidate")
async def invalidate_cache_pattern(
    pattern: str = Query(..., description="Pattern to invalidate (e.g., 'user:*', 'session:123:*')")
):
    """Invalidate cache keys matching a pattern"""
    
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    try:
        deleted = await CacheManager.clear_pattern(pattern)
        
        return {
            "status": "success",
            "pattern": pattern,
            "deleted_keys": deleted,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/health")
async def check_cache_health():
    """Check Redis cache health and connectivity"""
    
    if not redis_client:
        return {
            "status": "unavailable",
            "message": "Redis client not initialized"
        }
    
    try:
        # Test connection
        await redis_client.ping()
        
        # Get basic info
        info = await redis_client.info()
        memory = await redis_client.info('memory')
        
        memory_used_mb = memory.get('used_memory', 0) / (1024 * 1024)
        memory_max_mb = memory.get('maxmemory', 0) / (1024 * 1024) if memory.get('maxmemory', 0) > 0 else None
        
        memory_usage_pct = (memory_used_mb / memory_max_mb * 100) if memory_max_mb else None
        
        health_status = "healthy"
        warnings = []
        
        if memory_usage_pct and memory_usage_pct > 90:
            health_status = "warning"
            warnings.append("Memory usage above 90%")
        
        if info.get('connected_clients', 0) > 1000:
            warnings.append("High number of connected clients")
        
        return {
            "status": health_status,
            "connected": True,
            "memory_used_mb": round(memory_used_mb, 2),
            "memory_max_mb": round(memory_max_mb, 2) if memory_max_mb else "unlimited",
            "memory_usage_pct": round(memory_usage_pct, 2) if memory_usage_pct else None,
            "connected_clients": info.get('connected_clients', 0),
            "uptime_hours": info.get('uptime_in_seconds', 0) / 3600,
            "warnings": warnings,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error checking cache health: {e}")
        return {
            "status": "error",
            "connected": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.get("/cache/optimize/suggestions")
async def get_optimization_suggestions():
    """Get cache optimization suggestions based on current usage"""
    
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    try:
        info = await redis_client.info()
        stats = await redis_client.info('stats')
        memory = await redis_client.info('memory')
        
        suggestions = []
        
        # Memory suggestions
        memory_used = memory.get('used_memory', 0)
        memory_max = memory.get('maxmemory', 0)
        
        if memory_max > 0:
            usage_pct = (memory_used / memory_max) * 100
            if usage_pct > 80:
                suggestions.append({
                    "type": "memory",
                    "priority": "high",
                    "message": "Memory usage is high. Consider increasing maxmemory or implementing aggressive TTLs",
                    "action": "Review key expiration policies"
                })
        
        # Hit rate suggestions
        hits = stats.get('keyspace_hits', 0)
        misses = stats.get('keyspace_misses', 0)
        total = hits + misses
        
        if total > 1000:  # Only if enough data
            hit_rate = (hits / total) * 100
            
            if hit_rate < 70:
                suggestions.append({
                    "type": "hit_rate",
                    "priority": "medium",
                    "message": f"Cache hit rate is {hit_rate:.1f}%. Consider implementing cache warming strategies",
                    "action": "Identify frequently accessed data and pre-cache it"
                })
            elif hit_rate > 95:
                suggestions.append({
                    "type": "hit_rate",
                    "priority": "low",
                    "message": f"Excellent cache hit rate of {hit_rate:.1f}%",
                    "action": "Current caching strategy is working well"
                })
        
        # Eviction suggestions
        evicted = stats.get('evicted_keys', 0)
        if evicted > 1000:
            suggestions.append({
                "type": "eviction",
                "priority": "high",
                "message": f"{evicted} keys evicted. Increase memory or optimize TTLs",
                "action": "Review eviction policy (LRU, LFU, etc.)"
            })
        
        # Key count suggestions
        total_keys = await redis_client.dbsize()
        if total_keys > 1000000:
            suggestions.append({
                "type": "keys",
                "priority": "medium",
                "message": f"Large number of keys ({total_keys}). Consider key cleanup strategies",
                "action": "Implement automated key expiration and cleanup"
            })
        
        if not suggestions:
            suggestions.append({
                "type": "general",
                "priority": "info",
                "message": "Cache is operating efficiently",
                "action": "Continue monitoring for optimal performance"
            })
        
        return {
            "suggestions": suggestions,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting optimization suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
