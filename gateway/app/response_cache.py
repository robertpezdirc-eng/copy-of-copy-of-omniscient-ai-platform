"""
Response caching for AI chat completions with Redis backend and in-memory fallback.
"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, Optional

from cachetools import TTLCache

try:
    from prometheus_client import Counter, Gauge
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Cache metrics (Prometheus)
if PROMETHEUS_AVAILABLE:
    cache_hits_total = Counter(
        "cache_hits_total",
        "Total number of cache hits",
        ["cache_type"]  # redis or memory
    )
    cache_misses_total = Counter(
        "cache_misses_total",
        "Total number of cache misses"
    )
    cache_size_gauge = Gauge(
        "cache_size_items",
        "Current number of items in cache",
        ["cache_type"]
    )
else:
    cache_hits_total = None
    cache_misses_total = None
    cache_size_gauge = None


class ResponseCache:
    """
    Cache for AI responses with Redis primary and in-memory fallback.
    """

    def __init__(self, redis_client=None, default_ttl: int = 60, max_memory_size: int = 1000):
        """
        Args:
            redis_client: Optional Redis async client
            default_ttl: TTL in seconds for cached responses (default 60s)
            max_memory_size: Max items in in-memory cache if Redis unavailable
        """
        self.redis = redis_client
        self.default_ttl = default_ttl
        # In-memory fallback cache with TTL
        self.memory_cache: TTLCache = TTLCache(maxsize=max_memory_size, ttl=default_ttl)
        logger.info(
            f"ResponseCache initialized (redis={'yes' if redis_client else 'no'}, "
            f"ttl={default_ttl}s, memory_max={max_memory_size})"
        )

    def _make_key(self, prompt: str, model: str, temperature: float = 0.7) -> str:
        """Generate cache key from request parameters."""
        # Use hash for compact key while preserving uniqueness
        key_data = f"{prompt}|{model}|{temperature:.2f}"
        key_hash = hashlib.sha256(key_data.encode()).hexdigest()[:16]
        return f"ai:resp:{key_hash}"

    async def get(self, prompt: str, model: str, temperature: float = 0.7) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached response if available.

        Returns:
            Cached response dict or None if cache miss
        """
        key = self._make_key(prompt, model, temperature)

        # Try Redis first
        if self.redis:
            try:
                cached = await self.redis.get(key)
                if cached:
                    logger.debug(f"Cache HIT (Redis): {key}")
                    if cache_hits_total:
                        cache_hits_total.labels(cache_type="redis").inc()
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Redis get error: {e}")

        # Fallback to memory cache
        if key in self.memory_cache:
            logger.debug(f"Cache HIT (memory): {key}")
            if cache_hits_total:
                cache_hits_total.labels(cache_type="memory").inc()
            return self.memory_cache[key]

        logger.debug(f"Cache MISS: {key}")
        if cache_misses_total:
            cache_misses_total.inc()
        return None

    async def set(
        self,
        prompt: str,
        model: str,
        response: Dict[str, Any],
        temperature: float = 0.7,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Store response in cache.

        Args:
            prompt: User prompt
            model: Model name
            response: Response dict to cache
            temperature: Model temperature
            ttl: Optional custom TTL; uses default if not specified

        Returns:
            True if cached successfully
        """
        key = self._make_key(prompt, model, temperature)
        ttl = ttl or self.default_ttl

        # Try Redis first
        if self.redis:
            try:
                await self.redis.setex(key, ttl, json.dumps(response))
                logger.debug(f"Cached to Redis: {key} (ttl={ttl}s)")
                if cache_size_gauge:
                    # Update cache size gauge (approximate)
                    try:
                        dbsize = await self.redis.dbsize()
                        cache_size_gauge.labels(cache_type="redis").set(dbsize)
                    except Exception:
                        pass
                return True
            except Exception as e:
                logger.warning(f"Redis set error: {e}")

        # Fallback to memory cache
        self.memory_cache[key] = response
        logger.debug(f"Cached to memory: {key} (ttl={ttl}s)")
        if cache_size_gauge:
            cache_size_gauge.labels(cache_type="memory").set(len(self.memory_cache))
        return True

    async def clear(self) -> int:
        """Clear all cached responses. Returns count of cleared items."""
        count = 0

        if self.redis:
            try:
                # Clear all keys matching pattern
                cursor = 0
                while True:
                    cursor, keys = await self.redis.scan(cursor, match="ai:resp:*", count=100)
                    if keys:
                        count += await self.redis.delete(*keys)
                    if cursor == 0:
                        break
                logger.info(f"Cleared {count} items from Redis cache")
            except Exception as e:
                logger.warning(f"Redis clear error: {e}")

        # Clear memory cache
        mem_count = len(self.memory_cache)
        self.memory_cache.clear()
        logger.info(f"Cleared {mem_count} items from memory cache")

        return count + mem_count
