"""
Redis-based rate limiting middleware for API Gateway.
Tier-based limits with sliding window algorithm.
"""
from __future__ import annotations

import logging
import time
from typing import Callable, Optional

import redis.asyncio as redis
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from .settings import settings

logger = logging.getLogger(__name__)


class RedisRateLimiter(BaseHTTPMiddleware):
    """
    Redis-backed rate limiter with sliding window.
    
    Rate limits by API key tier:
    - free: 10 req/min
    - basic: 100 req/min
    - premium: 1000 req/min
    - master: unlimited
    """
    
    def __init__(self, app, redis_client: Optional[redis.Redis] = None, redis_getter: Optional[Callable[[], Optional[redis.Redis]]] = None):
        super().__init__(app)
        self.redis_client = redis_client
        self.redis_getter = redis_getter
        self.enabled = settings.redis_url is not None
        
        # Tier limits (requests per minute)
        self.tier_limits = {
            "free": 10,
            "basic": 100,
            "premium": 1000,
            "master": None,  # unlimited
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Resolve redis client (supports late-binding via getter)
        client = self.redis_getter() if self.redis_getter else self.redis_client

        # Skip rate limiting if Redis not configured
        if not self.enabled or not client:
            return await call_next(request)
        
        # Skip rate limiting for health/metrics endpoints
        if request.url.path in ["/health", "/metrics", "/"]:
            return await call_next(request)
        
        # Extract API key and tier from header (will be set by auth middleware)
        api_key = request.headers.get("x-api-key")
        if not api_key:
            # No API key = default to free tier
            tier = "free"
            identifier = request.client.host if request.client else "unknown"
        else:
            # Use tier from request state if available (set by auth.py)
            tier = getattr(request.state, "tier", "free")
            identifier = api_key
        
        # Check if unlimited
        limit = self.tier_limits.get(tier)
        if limit is None:
            return await call_next(request)
        
        # Check rate limit
        allowed, remaining, reset_time = await self._check_rate_limit(
            client, identifier, tier, limit
        )
        
        # Add rate limit headers
        response = await call_next(request) if allowed else Response(
            content='{"detail":"Rate limit exceeded"}',
            status_code=HTTP_429_TOO_MANY_REQUESTS,
            media_type="application/json"
        )
        
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response
    
    def _get_tier_for_key(self, api_key: str) -> str:
        """Map API key to tier. In production, query from database."""
        # For now, simple mapping based on key prefix
        if api_key.startswith("master-"):
            return "master"
        elif api_key.startswith("premium-"):
            return "premium"
        elif api_key.startswith("basic-"):
            return "basic"
        elif api_key == "prod-key-omni-2025":
            return "premium"  # Our current production key
        else:
            return "free"
    
    async def _check_rate_limit(
        self, client: redis.Redis, identifier: str, tier: str, limit: int
    ) -> tuple[bool, int, int]:
        """
        Check rate limit using sliding window in Redis.
        
        Returns:
            (allowed, remaining, reset_time)
        """
        now = int(time.time())
        window = 60  # 1 minute window
        key = f"ratelimit:{tier}:{identifier}"
        
        try:
            async with client.pipeline(transaction=True) as pipe:
                # Remove expired entries
                await pipe.zremrangebyscore(key, 0, now - window)
                # Count requests in current window
                await pipe.zcard(key)
                # Add current request
                await pipe.zadd(key, {str(now): now})
                # Set expiry
                await pipe.expire(key, window)
                results = await pipe.execute()
            
            count = results[1]  # zcard result
            
            if count >= limit:
                # Rate limit exceeded
                remaining = 0
                reset_time = now + window
                return False, remaining, reset_time
            else:
                # Request allowed
                remaining = limit - count - 1
                reset_time = now + window
                return True, remaining, reset_time
                
        except Exception as e:
            logger.warning(f"Redis rate limit check failed: {e}. Allowing request.")
            # Fail open - allow request if Redis unavailable
            return True, limit, now + window


async def get_redis_client() -> Optional[redis.Redis]:
    """Create async Redis client if URL configured."""
    if not settings.redis_url:
        return None
    
    try:
        client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=10,
            socket_connect_timeout=5,
            socket_keepalive=True,
        )
        # Test connection
        await client.ping()
        logger.info("Redis connection established for rate limiting")
        return client
    except Exception as e:
        logger.warning(f"Failed to connect to Redis: {e}. Rate limiting disabled.")
        return None
