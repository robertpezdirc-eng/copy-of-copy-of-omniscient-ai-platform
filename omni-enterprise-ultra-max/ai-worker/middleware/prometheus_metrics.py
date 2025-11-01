"""
Prometheus Metrics Middleware
Tracks API performance, requests, and model inference times
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
from typing import Callable

# Define metrics
request_count = Counter(
    'api_requests_total',
    'Total API requests',
    ['endpoint', 'method', 'status']
)

request_duration = Histogram(
    'api_request_duration_seconds',
    'Request duration in seconds',
    ['endpoint', 'method'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

active_requests = Gauge(
    'api_active_requests',
    'Number of active requests'
)

model_inference_time = Histogram(
    'model_inference_duration_seconds',
    'Model inference time in seconds',
    ['model_type', 'tenant_id'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

error_count = Counter(
    'api_errors_total',
    'Total errors',
    ['endpoint', 'error_type', 'status_code']
)

model_requests = Counter(
    'model_requests_total',
    'Total model inference requests',
    ['model_type', 'tenant_id']
)

# Cache statistics
cache_hits = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

# System metrics
memory_usage_bytes = Gauge(
    'process_memory_bytes',
    'Process memory usage in bytes'
)

cpu_usage_percent = Gauge(
    'process_cpu_percent',
    'Process CPU usage percentage'
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to track metrics for all requests"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response | None:
        # Skip metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)
        
        # Track active requests
        active_requests.inc()
        start_time = time.time()
        
        response: Response | None = None
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Record successful request
            request_count.labels(
                endpoint=request.url.path,
                method=request.method,
                status=response.status_code
            ).inc()
            
            request_duration.labels(
                endpoint=request.url.path,
                method=request.method
            ).observe(duration)
            
            # Track errors
            if response.status_code >= 400:
                error_count.labels(
                    endpoint=request.url.path,
                    error_type="http_error",
                    status_code=response.status_code
                ).inc()
            
        except Exception as e: # pragma: no cover
            duration = time.time() - start_time # pragma: no cover
            status_code = 500 # pragma: no cover
            response = Response(status_code=status_code) # pragma: no cover
            
            # Record exception
            error_count.labels(
                endpoint=request.url.path,
                error_type=type(e).__name__,
                status_code=500
            ).inc()
            
            request_duration.labels(
                endpoint=request.url.path,
                method=request.method
            ).observe(duration)

            # Re-raise the exception to be handled by other exception handlers
            # or to result in a 500 Internal Server Error if not caught.
            # This ensures that the original error propagation is maintained.
            raise
        
        finally:
            active_requests.dec()


def track_model_inference(model_type: str, tenant_id: str = "default"):
    """Context manager to track model inference time"""
    class ModelInferenceTracker:
        def __init__(self, model_type: str, tenant_id: str):
            self.model_type = model_type
            self.tenant_id = tenant_id
            self.start_time = None
        
        def __enter__(self):
            self.start_time = time.time()
            model_requests.labels(
                model_type=self.model_type,
                tenant_id=self.tenant_id
            ).inc()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = time.time() - self.start_time
            model_inference_time.labels(
                model_type=self.model_type,
                tenant_id=self.tenant_id
            ).observe(duration)
    
    return ModelInferenceTracker(model_type, tenant_id)


def track_cache_hit(cache_type: str):
    """Record cache hit"""
    cache_hits.labels(cache_type=cache_type).inc()


def track_cache_miss(cache_type: str):
    """Record cache miss"""
    cache_misses.labels(cache_type=cache_type).inc()


def update_system_metrics():
    """Update system resource metrics"""
    try:
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_usage_bytes.set(process.memory_info().rss)
        cpu_usage_percent.set(process.cpu_percent())
    except ImportError:
        # psutil not available
        pass


def get_metrics() -> bytes:
    """Generate Prometheus metrics output"""
    update_system_metrics()
    return generate_latest()
