# Backend Middleware

This directory contains the middleware stack for the Omni Enterprise Ultra Max backend. Middleware components process HTTP requests and responses in a specific order to provide cross-cutting concerns.

## Middleware Order

The order of middleware is critical - **first added = outermost layer**. The current stack:

```python
# From backend/main.py

# 1. Internal Prefix Stripper (if RUN_AS_INTERNAL=1)
app.add_middleware(InternalPrefixStripper, prefix="/internal")

# 2. Security Headers
app.add_middleware(SecurityHeadersMiddleware)

# 3. Metrics Collection
app.add_middleware(MetricsMiddleware)

# 4. Performance Monitor
app.add_middleware(PerformanceMonitor, slow_request_threshold=1.0)

# 5. Response Cache (if enabled and not internal)
app.add_middleware(ResponseCacheMiddleware, redis_client=redis, default_ttl=60)

# 6. Usage Tracker (if not internal)
app.add_middleware(UsageTracker)

# 7. Rate Limiter (if not internal)
app.add_middleware(RateLimiter)
```

## Middleware Components

### 1. Internal Prefix Stripper (`internal_prefix.py`)

**Purpose**: Strip `/internal` prefix from requests when running behind a gateway.

**When Applied**: Only when `RUN_AS_INTERNAL=1`

**Functionality**:
- Checks if path starts with `/internal`
- Strips prefix and continues routing
- Allows same routes to work under different namespaces

**Configuration**:
```python
RUN_AS_INTERNAL=1  # Enable internal mode
```

**Example**:
```
Request:  /internal/api/v1/health
Modified: /api/v1/health
```

**Use Case**: Gateway forwards requests to backend under `/internal/*` path.

---

### 2. Security Headers (`security_headers.py`)

**Purpose**: Add security-related HTTP headers to all responses.

**Applied**: Always (outermost after internal prefix)

**Headers Added**:
- `X-Content-Type-Options: nosniff` - Prevent MIME sniffing
- `X-Frame-Options: DENY` - Prevent clickjacking
- `X-XSS-Protection: 1; mode=block` - Enable XSS filter
- `Strict-Transport-Security` - Force HTTPS (in production)
- `Content-Security-Policy` - Control resource loading

**Configuration**:
```python
# No configuration needed - applies automatically
```

**Benefits**:
- Mitigates common web vulnerabilities
- Improves security posture
- Complies with security best practices

---

### 3. Metrics Collection (`metrics.py`)

**Purpose**: Collect Prometheus metrics for monitoring.

**Applied**: Always (for all requests)

**Metrics Collected**:
- `http_requests_total` - Total HTTP requests (by method, path, status)
- `http_request_duration_seconds` - Request duration histogram
- `http_requests_in_progress` - Current in-flight requests

**Labels**:
- `method`: HTTP method (GET, POST, etc.)
- `path`: Request path
- `status`: Response status code

**Configuration**:
```python
# Metrics exposed at /metrics endpoint
```

**Buckets**: 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0 seconds

**Usage**:
```bash
curl http://localhost:8080/metrics
```

**Integration**: Works with Prometheus, Grafana for visualization.

---

### 4. Performance Monitor (`performance_monitor.py`)

**Purpose**: Monitor and log slow requests.

**Applied**: Always

**Functionality**:
- Measures request duration
- Logs requests exceeding threshold
- Helps identify performance bottlenecks

**Configuration**:
```python
PERF_SLOW_THRESHOLD_SEC=1.0  # Log requests slower than 1 second
```

**Log Example**:
```
WARNING: Slow request: GET /api/v1/analytics took 1.523s
```

**Use Cases**:
- Performance debugging
- Identifying slow endpoints
- Capacity planning

---

### 5. Response Cache (`response_cache.py`)

**Purpose**: Cache HTTP responses in Redis to reduce backend load.

**Applied**: When `ENABLE_RESPONSE_CACHE=1` and not in internal mode

**Functionality**:
- Caches GET/HEAD requests only
- Uses Redis for distributed caching
- Respects cache headers
- TTL-based expiration

**Configuration**:
```python
ENABLE_RESPONSE_CACHE=1    # Enable caching (default)
CACHE_DEFAULT_TTL=60       # Default cache TTL in seconds
```

**Cache Key Format**:
```
cache:{method}:{path}:{query_params}
```

**Headers Respected**:
- `Cache-Control: no-cache` - Skip cache
- `Cache-Control: max-age=N` - Override TTL

**Bypass Cache**:
```bash
curl -H "Cache-Control: no-cache" http://api.example.com/endpoint
```

**Benefits**:
- Reduces database queries
- Improves response time
- Scales read-heavy endpoints

---

### 6. Usage Tracker (`usage_tracker.py`)

**Purpose**: Track API usage per user/tenant for billing and analytics.

**Applied**: When not in internal mode

**Functionality**:
- Records API calls per user
- Tracks endpoint usage
- Supports usage-based billing

**Configuration**:
```python
# Automatically enabled in public mode
# Skipped when RUN_AS_INTERNAL=1
```

**Data Tracked**:
- User ID / Tenant ID
- Endpoint called
- Timestamp
- Request count

**Storage**: Redis counters and sorted sets

**Use Cases**:
- Usage-based billing
- Rate limit enforcement
- Analytics and reporting

---

### 7. Rate Limiter (`rate_limiter.py`)

**Purpose**: Prevent abuse by limiting request rates.

**Applied**: When not in internal mode

**Functionality**:
- Limits requests per user/IP
- Sliding window algorithm
- Configurable limits per tier

**Configuration**:
```python
RATE_LIMIT_FREE=100       # Requests per minute for free tier
RATE_LIMIT_PRO=1000       # Requests per minute for pro tier
RATE_LIMIT_ENTERPRISE=-1  # Unlimited for enterprise
```

**Response Headers**:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Time when limit resets

**Error Response** (429 Too Many Requests):
```json
{
  "detail": "Rate limit exceeded. Try again in 30 seconds."
}
```

**Bypass**:
- Internal mode (`RUN_AS_INTERNAL=1`)
- Enterprise tier
- Whitelisted IPs

---

## Middleware Execution Flow

### Request Flow (Inbound)

```
1. Client Request
   ↓
2. Internal Prefix Stripper (strip /internal if present)
   ↓
3. Security Headers (prepare to add headers)
   ↓
4. Metrics (start timer, increment in-progress)
   ↓
5. Performance Monitor (start timer)
   ↓
6. Response Cache (check cache, return if hit)
   ↓
7. Usage Tracker (record usage)
   ↓
8. Rate Limiter (check limits, return 429 if exceeded)
   ↓
9. Route Handler (your endpoint code)
```

### Response Flow (Outbound)

```
1. Route Handler (return response)
   ↓
2. Rate Limiter (pass through)
   ↓
3. Usage Tracker (pass through)
   ↓
4. Response Cache (store in cache if applicable)
   ↓
5. Performance Monitor (log if slow)
   ↓
6. Metrics (record duration, status, decrement in-progress)
   ↓
7. Security Headers (add security headers)
   ↓
8. Internal Prefix Stripper (pass through)
   ↓
9. Client Response
```

## Configuration Modes

### Production Mode (Default)
All middleware enabled:
```bash
# No special configuration needed
python main.py
```

### Internal Mode (Behind Gateway)
Rate limiting and usage tracking disabled:
```bash
RUN_AS_INTERNAL=1 python main.py
```

Benefits:
- Gateway handles rate limiting
- No redundant usage tracking
- Faster internal communication

### Minimal Mode (Lightweight)
Only essential middleware:
```bash
OMNI_MINIMAL=1 python main.py
```

Benefits:
- Faster startup
- Lower memory usage
- Good for development

## Adding New Middleware

### 1. Create Middleware File

Create `backend/middleware/my_middleware.py`:

```python
"""
My Middleware
Brief description of what it does
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable
import logging

logger = logging.getLogger(__name__)


class MyMiddleware(BaseHTTPMiddleware):
    """Middleware description"""
    
    def __init__(self, app, config_param: str = "default"):
        super().__init__(app)
        self.config_param = config_param
        logger.info(f"MyMiddleware initialized with config: {config_param}")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and response"""
        
        # Before request processing
        logger.debug(f"Processing request: {request.url.path}")
        
        # Call next middleware/handler
        response = await call_next(request)
        
        # After request processing
        logger.debug(f"Response status: {response.status_code}")
        
        return response
```

### 2. Register in `main.py`

Add to the middleware stack in the appropriate order:

```python
from middleware.my_middleware import MyMiddleware

# Add to app
app.add_middleware(MyMiddleware, config_param="custom_value")
```

### 3. Consider Order

Place middleware in the correct position:
- **Outermost**: Security, metrics (need to wrap everything)
- **Middle**: Caching, performance monitoring
- **Innermost**: Rate limiting, authentication (need request context)

### 4. Write Tests

Create `backend/tests/test_my_middleware.py`:

```python
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.middleware.my_middleware import MyMiddleware


@pytest.fixture
def app():
    app = FastAPI()
    app.add_middleware(MyMiddleware, config_param="test")
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "ok"}
    
    return app


def test_my_middleware(app):
    client = TestClient(app)
    response = client.get("/test")
    assert response.status_code == 200
```

## Performance Considerations

### Middleware Overhead

Each middleware adds latency:
- Internal Prefix: ~0.1ms
- Security Headers: ~0.1ms
- Metrics: ~0.5ms
- Performance Monitor: ~0.1ms
- Response Cache: ~1-5ms (Redis lookup)
- Usage Tracker: ~1ms (Redis update)
- Rate Limiter: ~1-2ms (Redis check)

**Total Overhead**: ~3-9ms per request

### Optimization Tips

1. **Cache Aggressively**: Use response cache for read-heavy endpoints
2. **Redis Pipelining**: Batch Redis operations in custom middleware
3. **Async Operations**: Use `async/await` for all I/O
4. **Conditional Middleware**: Skip middleware when not needed (internal mode)
5. **Connection Pooling**: Reuse database/Redis connections

## Debugging Middleware

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test Middleware Order

```python
# Add print statements in each middleware
class MyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        print(f"[BEFORE] MyMiddleware: {request.url.path}")
        response = await call_next(request)
        print(f"[AFTER] MyMiddleware: {response.status_code}")
        return response
```

### Monitor Metrics

```bash
# Check request counts
curl http://localhost:8080/metrics | grep http_requests_total

# Check latency
curl http://localhost:8080/metrics | grep http_request_duration
```

## Known Issues

### Metrics Double Registration

**Issue**: Prometheus metrics may be registered twice on hot reload.

**Workaround**: Already handled with try/except blocks in metrics.py.

### Cache Invalidation

**Issue**: No automatic cache invalidation on data updates.

**Solution**: Implement cache invalidation in routes:
```python
from services.cache_service import get_cache_service

async def update_user(user_id: str, data: dict):
    # Update database
    await db.update_user(user_id, data)
    
    # Invalidate cache
    cache = get_cache_service()
    await cache.delete(f"cache:GET:/api/v1/users/{user_id}")
```

### Rate Limiting Per Tenant

**Issue**: Rate limiting is per user, not per tenant.

**Future**: Implement tenant-level rate limiting in rate_limiter.py.

## Related Documentation

- [Backend Architecture](../ARCHITECTURE.md) - Overall backend structure
- [Backend README](../README.md) - Setup and usage
- [Services Documentation](../services/README.md) - Service layer
- [Main Application](../main.py) - Middleware registration

## Support

For issues with middleware:
1. Check this documentation
2. Review middleware source code
3. Check logs for errors
4. Test middleware in isolation
5. Verify middleware order
