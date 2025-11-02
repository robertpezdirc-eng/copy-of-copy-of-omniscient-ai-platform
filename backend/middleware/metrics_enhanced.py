"""
Enhanced Prometheus Metrics for Omni Platform
Business metrics + ML model tracking
"""
import logging
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import time

logger = logging.getLogger(__name__)

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("⚠️ Prometheus client not available")


# HTTP Metrics (already exist in current metrics.py, enhancing them)
if PROMETHEUS_AVAILABLE:
    # Request metrics
    HTTP_REQUESTS_TOTAL = Counter(
        'http_requests_total',
        'Total HTTP requests',
        ['method', 'endpoint', 'status']
    )
    
    HTTP_REQUEST_DURATION = Histogram(
        'http_request_duration_seconds',
        'HTTP request latency',
        ['method', 'endpoint'],
        buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0)
    )
    
    # Active requests gauge
    HTTP_REQUESTS_ACTIVE = Gauge(
        'http_requests_active',
        'Number of active HTTP requests'
    )
    
    # Business Metrics
    ML_PREDICTIONS_TOTAL = Counter(
        'ml_predictions_total',
        'Total ML predictions',
        ['model_type', 'tenant_id']
    )
    
    ML_PREDICTION_DURATION = Histogram(
        'ml_prediction_duration_seconds',
        'ML prediction latency',
        ['model_type'],
        buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0)
    )
    
    CACHE_OPERATIONS = Counter(
        'cache_operations_total',
        'Cache operations',
        ['operation', 'result']  # operation: get/set, result: hit/miss/error
    )
    
    API_KEY_USAGE = Counter(
        'api_key_usage_total',
        'API key usage',
        ['tenant_id', 'endpoint']
    )
    
    REVENUE_EVENTS = Counter(
        'revenue_events_total',
        'Billable events',
        ['tenant_id', 'event_type']  # event_type: api_call, ml_inference, storage
    )


class EnhancedMetricsMiddleware(BaseHTTPMiddleware):
    """
    Enhanced metrics middleware with business tracking
    
    Usage:
        app.add_middleware(EnhancedMetricsMiddleware)
    """
    
    async def dispatch(self, request: Request, call_next):
        if not PROMETHEUS_AVAILABLE:
            return await call_next(request)
        
        # Track active requests
        HTTP_REQUESTS_ACTIVE.inc()
        
        start_time = time.time()
        
        try:
            response: Response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            endpoint = request.url.path
            method = request.method
            status = response.status_code
            
            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).inc()
            
            HTTP_REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            # Track API key usage if present
            if hasattr(request.state, 'tenant_id'):
                API_KEY_USAGE.labels(
                    tenant_id=request.state.tenant_id,
                    endpoint=endpoint
                ).inc()
            
            return response
            
        except Exception as e:
            # Record error
            HTTP_REQUESTS_TOTAL.labels(
                method=request.method,
                endpoint=request.url.path,
                status=500
            ).inc()
            raise
        finally:
            HTTP_REQUESTS_ACTIVE.dec()


# Helper functions for business metrics
def track_ml_prediction(model_type: str, tenant_id: str, duration: float):
    """Track ML prediction"""
    if not PROMETHEUS_AVAILABLE:
        return
    
    ML_PREDICTIONS_TOTAL.labels(
        model_type=model_type,
        tenant_id=tenant_id
    ).inc()
    
    ML_PREDICTION_DURATION.labels(
        model_type=model_type
    ).observe(duration)


def track_cache_operation(operation: str, result: str):
    """Track cache hit/miss"""
    if not PROMETHEUS_AVAILABLE:
        return
    
    CACHE_OPERATIONS.labels(
        operation=operation,
        result=result
    ).inc()


def track_revenue_event(tenant_id: str, event_type: str, quantity: float = 1.0):
    """Track billable event"""
    if not PROMETHEUS_AVAILABLE:
        return
    
    REVENUE_EVENTS.labels(
        tenant_id=tenant_id,
        event_type=event_type
    ).inc(quantity)


# Metrics endpoint
def get_metrics():
    """Return Prometheus metrics"""
    if not PROMETHEUS_AVAILABLE:
        return "# Prometheus not available\n"
    
    return generate_latest()


# Example usage in routes:
"""
from middleware.metrics_enhanced import track_ml_prediction, track_revenue_event
import time

@app.post("/api/v1/predict/revenue-lstm")
async def predict_revenue(request: Request, payload: dict):
    tenant_id = request.state.tenant_id
    
    # Track start time
    start_time = time.time()
    
    # Do prediction
    result = await lstm_service.predict(payload)
    
    # Track metrics
    duration = time.time() - start_time
    track_ml_prediction("lstm", tenant_id, duration)
    track_revenue_event(tenant_id, "ml_inference")
    
    return result
"""
