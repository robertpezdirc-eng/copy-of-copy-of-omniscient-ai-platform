"""
Redis Caching Service with Tenant Isolation
Provides high-performance caching for speed and stability
"""

from typing import Optional, Any, Dict, List
import json
import hashlib
import logging
from datetime import timedelta
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class CacheService:
    """Enhanced Redis caching service with tenant isolation"""
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.default_ttl = 300  # 5 minutes default TTL
        
    def _make_key(self, tenant_id: str, key: str) -> str:
        """Create tenant-isolated cache key"""
        return f"cache:{tenant_id}:{key}"
    
    def _hash_key(self, data: Any) -> str:
        """Create a hash for complex data structures"""
        if isinstance(data, dict):
            data = json.dumps(data, sort_keys=True)
        return hashlib.md5(str(data).encode()).hexdigest()
    
    async def get(
        self,
        tenant_id: str,
        key: str,
        default: Any = None
    ) -> Any:
        """Get value from cache"""
        cache_key = self._make_key(tenant_id, key)
        
        try:
            value = await self.redis.get(cache_key)
            if value is None:
                logger.debug(f"Cache miss: {cache_key}")
                return default
            
            logger.debug(f"Cache hit: {cache_key}")
            return json.loads(value)
        except Exception as e:
            logger.error(f"Cache get error for {cache_key}: {e}")
            return default
    
    async def set(
        self,
        tenant_id: str,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with TTL"""
        cache_key = self._make_key(tenant_id, key)
        ttl = ttl or self.default_ttl
        
        try:
            serialized = json.dumps(value)
            await self.redis.setex(cache_key, ttl, serialized)
            logger.debug(f"Cache set: {cache_key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set error for {cache_key}: {e}")
            return False
    
    async def delete(self, tenant_id: str, key: str) -> bool:
        """Delete key from cache"""
        cache_key = self._make_key(tenant_id, key)
        
        try:
            await self.redis.delete(cache_key)
            logger.debug(f"Cache delete: {cache_key}")
            return True
        except Exception as e:
            logger.error(f"Cache delete error for {cache_key}: {e}")
            return False
    
    async def delete_pattern(self, tenant_id: str, pattern: str) -> int:
        """Delete all keys matching a pattern for a tenant"""
        cache_pattern = self._make_key(tenant_id, pattern)
        
        try:
            keys = []
            async for key in self.redis.scan_iter(match=cache_pattern):
                keys.append(key)
            
            if keys:
                deleted = await self.redis.delete(*keys)
                logger.info(f"Cache deleted {deleted} keys matching {cache_pattern}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error for {cache_pattern}: {e}")
            return 0
    
    async def exists(self, tenant_id: str, key: str) -> bool:
        """Check if key exists in cache"""
        cache_key = self._make_key(tenant_id, key)
        
        try:
            return await self.redis.exists(cache_key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for {cache_key}: {e}")
            return False
    
    async def increment(
        self,
        tenant_id: str,
        key: str,
        amount: int = 1
    ) -> Optional[int]:
        """Increment a counter"""
        cache_key = self._make_key(tenant_id, key)
        
        try:
            value = await self.redis.incrby(cache_key, amount)
            logger.debug(f"Cache increment: {cache_key} -> {value}")
            return value
        except Exception as e:
            logger.error(f"Cache increment error for {cache_key}: {e}")
            return None
    
    async def get_or_set(
        self,
        tenant_id: str,
        key: str,
        factory_func,
        ttl: Optional[int] = None
    ) -> Any:
        """Get value from cache or set it using factory function"""
        # Try to get from cache first
        value = await self.get(tenant_id, key)
        if value is not None:
            return value
        
        # Generate value using factory function
        try:
            if callable(factory_func):
                value = factory_func()
            else:
                value = factory_func
            
            # Store in cache
            await self.set(tenant_id, key, value, ttl)
            return value
        except Exception as e:
            logger.error(f"Cache get_or_set error for {key}: {e}")
            return None
    
    async def get_many(
        self,
        tenant_id: str,
        keys: List[str]
    ) -> Dict[str, Any]:
        """Get multiple values from cache"""
        cache_keys = [self._make_key(tenant_id, k) for k in keys]
        results = {}
        
        try:
            values = await self.redis.mget(cache_keys)
            for key, value in zip(keys, values):
                if value is not None:
                    results[key] = json.loads(value)
            
            logger.debug(f"Cache get_many: {len(results)}/{len(keys)} hits")
            return results
        except Exception as e:
            logger.error(f"Cache get_many error: {e}")
            return {}
    
    async def set_many(
        self,
        tenant_id: str,
        mapping: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Set multiple values in cache"""
        ttl = ttl or self.default_ttl
        
        try:
            pipe = self.redis.pipeline()
            for key, value in mapping.items():
                cache_key = self._make_key(tenant_id, key)
                serialized = json.dumps(value)
                pipe.setex(cache_key, ttl, serialized)
            
            await pipe.execute()
            logger.debug(f"Cache set_many: {len(mapping)} keys")
            return True
        except Exception as e:
            logger.error(f"Cache set_many error: {e}")
            return False
    
    async def flush_tenant(self, tenant_id: str) -> int:
        """Flush all cache for a tenant"""
        return await self.delete_pattern(tenant_id, "*")
    
    async def get_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get cache statistics for a tenant"""
        pattern = self._make_key(tenant_id, "*")
        
        try:
            keys_count = 0
            async for _ in self.redis.scan_iter(match=pattern):
                keys_count += 1
            
            info = await self.redis.info("stats")
            
            return {
                "tenant_keys": keys_count,
                "total_connections": info.get("total_connections_received", 0),
                "total_commands": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                )
            }
        except Exception as e:
            logger.error(f"Cache stats error for tenant {tenant_id}: {e}")
            return {}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)
    
    async def warm_cache(
        self,
        tenant_id: str,
        data_loader_func,
        keys: List[str],
        ttl: Optional[int] = None
    ) -> int:
        """Warm up cache with preloaded data"""
        warmed = 0
        
        try:
            for key in keys:
                if not await self.exists(tenant_id, key):
                    value = data_loader_func(key)
                    if value is not None:
                        await self.set(tenant_id, key, value, ttl)
                        warmed += 1
            
            logger.info(f"Cache warmed: {warmed}/{len(keys)} keys for tenant {tenant_id}")
            return warmed
        except Exception as e:
            logger.error(f"Cache warm error for tenant {tenant_id}: {e}")
            return warmed


class ResponseCacheService(CacheService):
    """Specialized cache service for HTTP responses"""
    
    def make_response_key(
        self,
        tenant_id: str,
        method: str,
        path: str,
        query_params: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create cache key for HTTP response"""
        key_parts = [method, path]
        
        if query_params:
            params_hash = self._hash_key(query_params)
            key_parts.append(params_hash)
        
        return ":".join(key_parts)
    
    async def cache_response(
        self,
        tenant_id: str,
        method: str,
        path: str,
        response_data: Any,
        query_params: Optional[Dict[str, Any]] = None,
        ttl: int = 60
    ) -> bool:
        """Cache an HTTP response"""
        key = self.make_response_key(tenant_id, method, path, query_params)
        return await self.set(tenant_id, key, response_data, ttl)
    
    async def get_cached_response(
        self,
        tenant_id: str,
        method: str,
        path: str,
        query_params: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """Get cached HTTP response"""
        key = self.make_response_key(tenant_id, method, path, query_params)
        return await self.get(tenant_id, key)


# Global cache service instance
_cache_service: Optional[CacheService] = None
_response_cache_service: Optional[ResponseCacheService] = None


def get_cache_service(redis_client: aioredis.Redis) -> CacheService:
    """Get or create cache service instance"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService(redis_client)
    return _cache_service


def get_response_cache_service(redis_client: aioredis.Redis) -> ResponseCacheService:
    """Get or create response cache service instance"""
    global _response_cache_service
    if _response_cache_service is None:
        _response_cache_service = ResponseCacheService(redis_client)
    return _response_cache_service
