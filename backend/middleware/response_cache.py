"""
Response Cache Middleware
Provides automatic caching of HTTP responses using Redis
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import Headers
from typing import Callable
import json
import logging

logger = logging.getLogger(__name__)


class ResponseCacheMiddleware(BaseHTTPMiddleware):
    """Middleware for caching HTTP responses"""
    
    def __init__(self, app, redis_client=None, default_ttl: int = 60):
        super().__init__(app)
        self.redis = redis_client
        self.default_ttl = default_ttl
        self.cacheable_methods = {"GET", "HEAD"}
        self.cache_enabled = redis_client is not None
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with caching"""
        
        # Only cache GET/HEAD requests
        if request.method not in self.cacheable_methods or not self.cache_enabled:
            return await call_next(request)
        
        # Skip caching for certain paths
        if self._should_skip_cache(request.url.path):
            return await call_next(request)
        
        # Get tenant ID from headers or default
        tenant_id = request.headers.get("x-tenant-id", "default")
        
        # Generate cache key
        cache_key = self._make_cache_key(
            tenant_id=tenant_id,
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params)
        )
        
        # Try to get from cache
        try:
            cached_response = await self._get_cached_response(cache_key)
            if cached_response:
                logger.debug(f"Cache hit: {cache_key}")
                return Response(
                    content=cached_response["body"],
                    status_code=cached_response["status_code"],
                    headers=Headers(cached_response["headers"]),
                    media_type=cached_response.get("media_type")
                )
        except Exception as e:
            logger.error(f"Cache read error: {e}")
        
        # Call next middleware/route
        response = await call_next(request)
        
        # Cache successful responses
        if response.status_code == 200:
            try:
                # Read response body
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk
                
                # Cache the response
                await self._cache_response(
                    cache_key=cache_key,
                    body=body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )
                
                logger.debug(f"Cache set: {cache_key}")
                
                # Return response with body
                return Response(
                    content=body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )
            except Exception as e:
                logger.error(f"Cache write error: {e}")
        
        return response
    
    def _should_skip_cache(self, path: str) -> bool:
        """Check if path should skip caching"""
        skip_patterns = [
            "/metrics",
            "/health",
            "/api/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/ws",  # WebSocket
        ]
        
        for pattern in skip_patterns:
            if path.startswith(pattern):
                return True
        
        return False
    
    def _make_cache_key(
        self,
        tenant_id: str,
        method: str,
        path: str,
        query_params: dict
    ) -> str:
        """Generate cache key"""
        import hashlib
        
        # Create consistent key from query params
        if query_params:
            params_str = json.dumps(query_params, sort_keys=True)
            params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        else:
            params_hash = "noparams"
        
        return f"response_cache:{tenant_id}:{method}:{path}:{params_hash}"
    
    async def _get_cached_response(self, cache_key: str) -> dict:
        """Get cached response"""
        if not self.redis:
            return None
        
        try:
            cached = await self.redis.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Failed to get cached response: {e}")
        
        return None
    
    async def _cache_response(
        self,
        cache_key: str,
        body: bytes,
        status_code: int,
        headers: dict,
        media_type: str
    ):
        """Cache response"""
        if not self.redis:
            return
        
        try:
            # Don't cache large responses (> 1MB)
            if len(body) > 1024 * 1024:
                return
            
            response_data = {
                "body": body.decode("utf-8") if isinstance(body, bytes) else body,
                "status_code": status_code,
                "headers": {k: v for k, v in headers.items() if k.lower() not in ["set-cookie", "authorization"]},
                "media_type": media_type
            }
            
            await self.redis.setex(
                cache_key,
                self.default_ttl,
                json.dumps(response_data)
            )
        except Exception as e:
            logger.error(f"Failed to cache response: {e}")
