"""
Redis metrics collection for monitoring.
"""
from __future__ import annotations

import logging
from typing import Optional

try:
    from prometheus_client import Gauge, Counter
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Redis connection metrics
if PROMETHEUS_AVAILABLE:
    redis_connected = Gauge(
        "redis_connected",
        "Redis connection status (1 = connected, 0 = disconnected)"
    )
    
    redis_memory_used_bytes = Gauge(
        "redis_memory_used_bytes",
        "Redis memory usage in bytes"
    )
    
    redis_memory_peak_bytes = Gauge(
        "redis_memory_peak_bytes",
        "Redis peak memory usage in bytes"
    )
    
    redis_keys_total = Gauge(
        "redis_keys_total",
        "Total number of keys in Redis"
    )
    
    redis_connected_clients = Gauge(
        "redis_connected_clients",
        "Number of client connections to Redis"
    )
    
    redis_commands_processed_total = Counter(
        "redis_commands_processed_total",
        "Total number of commands processed by Redis"
    )
    
    redis_keyspace_hits_total = Counter(
        "redis_keyspace_hits_total",
        "Total number of successful key lookups"
    )
    
    redis_keyspace_misses_total = Counter(
        "redis_keyspace_misses_total",
        "Total number of failed key lookups"
    )
else:
    redis_connected = None
    redis_memory_used_bytes = None
    redis_memory_peak_bytes = None
    redis_keys_total = None
    redis_connected_clients = None
    redis_commands_processed_total = None
    redis_keyspace_hits_total = None
    redis_keyspace_misses_total = None


async def collect_redis_metrics(redis_client) -> None:
    """
    Collect Redis metrics from INFO command and update Prometheus gauges.
    
    Args:
        redis_client: Redis async client instance
    """
    if not PROMETHEUS_AVAILABLE or not redis_client:
        return
    
    try:
        # Get Redis INFO
        info = await redis_client.info()
        
        # Connection status
        if redis_connected:
            redis_connected.set(1)
        
        # Memory metrics
        if redis_memory_used_bytes and "used_memory" in info:
            redis_memory_used_bytes.set(info["used_memory"])
        
        if redis_memory_peak_bytes and "used_memory_peak" in info:
            redis_memory_peak_bytes.set(info["used_memory_peak"])
        
        # Keyspace metrics
        if redis_keys_total:
            dbsize = await redis_client.dbsize()
            redis_keys_total.set(dbsize)
        
        # Client connections
        if redis_connected_clients and "connected_clients" in info:
            redis_connected_clients.set(info["connected_clients"])
        
        # Commands processed (cumulative counter)
        if redis_commands_processed_total and "total_commands_processed" in info:
            # Since Prometheus counters track totals, we need to set based on Redis stats
            # Note: This is a snapshot, not a rate
            total_commands = info["total_commands_processed"]
            # We can't directly set a counter, so we track the difference
            # For now, just log it - in production, use a gauge or calculate delta
            pass
        
        # Keyspace hits/misses
        if "keyspace_hits" in info:
            # Track hit rate metrics
            hits = info.get("keyspace_hits", 0)
            misses = info.get("keyspace_misses", 0)
            # Similar issue as above - these are cumulative from Redis
            # For proper tracking, we'd need to calculate deltas
            
        logger.debug(f"Redis metrics collected: {len(info)} stats")
        
    except Exception as e:
        logger.warning(f"Failed to collect Redis metrics: {e}")
        if redis_connected:
            redis_connected.set(0)


async def start_redis_metrics_collection(redis_client, interval_seconds: int = 30):
    """
    Start periodic collection of Redis metrics.
    
    Args:
        redis_client: Redis async client instance
        interval_seconds: Collection interval in seconds
    """
    import asyncio
    
    if not PROMETHEUS_AVAILABLE:
        logger.info("Prometheus not available, Redis metrics collection disabled")
        return
    
    logger.info(f"Starting Redis metrics collection (interval={interval_seconds}s)")
    
    while True:
        await collect_redis_metrics(redis_client)
        await asyncio.sleep(interval_seconds)
