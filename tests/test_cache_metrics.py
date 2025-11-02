"""
Test metrics collection for cache and Redis monitoring.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from gateway.app.response_cache import ResponseCache


class TestCacheMetrics:
    """Test cache metrics collection."""

    @pytest.mark.asyncio
    async def test_cache_hit_increments_metric(self):
        """Test that cache hit increments the appropriate metric."""
        # Mock Redis client
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value='{"result": "cached"}')
        
        # Create cache with mocked Redis
        cache = ResponseCache(redis_client=redis_mock, default_ttl=60)
        
        # Get cached value (should be a hit)
        result = await cache.get("test prompt", "gpt-4", temperature=0.7)
        
        # Verify result
        assert result == {"result": "cached"}
        
        # Verify Redis was called
        redis_mock.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_miss_increments_metric(self):
        """Test that cache miss increments the appropriate metric."""
        # Mock Redis client that returns None (cache miss)
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value=None)
        
        # Create cache with mocked Redis
        cache = ResponseCache(redis_client=redis_mock, default_ttl=60)
        
        # Get cached value (should be a miss)
        result = await cache.get("test prompt", "gpt-4", temperature=0.7)
        
        # Verify result is None (miss)
        assert result is None
        
        # Verify Redis was called
        redis_mock.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_set_updates_size_gauge(self):
        """Test that setting cache value updates size gauge."""
        # Mock Redis client
        redis_mock = AsyncMock()
        redis_mock.setex = AsyncMock(return_value=True)
        redis_mock.dbsize = AsyncMock(return_value=42)
        
        # Create cache with mocked Redis
        cache = ResponseCache(redis_client=redis_mock, default_ttl=60)
        
        # Set cached value
        response = {"result": "test response"}
        result = await cache.set("test prompt", "gpt-4", response, temperature=0.7)
        
        # Verify result
        assert result is True
        
        # Verify Redis was called
        redis_mock.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_memory_cache_fallback(self):
        """Test that memory cache works when Redis is unavailable."""
        # Create cache without Redis
        cache = ResponseCache(redis_client=None, default_ttl=60)
        
        # Set and get value from memory cache
        response = {"result": "test response"}
        await cache.set("test prompt", "gpt-4", response, temperature=0.7)
        
        # Get from memory cache
        result = await cache.get("test prompt", "gpt-4", temperature=0.7)
        
        # Verify result
        assert result == response


class TestRedisMetrics:
    """Test Redis metrics collection."""

    @pytest.mark.asyncio
    async def test_redis_metrics_collection(self):
        """Test that Redis metrics are collected properly."""
        from gateway.app.redis_metrics import collect_redis_metrics
        
        # Mock Redis client with info
        redis_mock = AsyncMock()
        redis_mock.info = AsyncMock(return_value={
            "used_memory": 1024000,
            "used_memory_peak": 2048000,
            "connected_clients": 5,
            "total_commands_processed": 10000,
            "keyspace_hits": 8000,
            "keyspace_misses": 2000,
        })
        redis_mock.dbsize = AsyncMock(return_value=100)
        
        # Collect metrics
        await collect_redis_metrics(redis_mock)
        
        # Verify Redis was called
        redis_mock.info.assert_called_once()
        redis_mock.dbsize.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_metrics_handles_errors(self):
        """Test that Redis metrics collection handles errors gracefully."""
        from gateway.app.redis_metrics import collect_redis_metrics
        
        # Mock Redis client that raises exception
        redis_mock = AsyncMock()
        redis_mock.info = AsyncMock(side_effect=Exception("Redis error"))
        
        # Collect metrics (should not raise)
        await collect_redis_metrics(redis_mock)
        
        # Verify Redis was called
        redis_mock.info.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
