"""
OpenTelemetry Tracing for Omni Platform
Distributed tracing across services
"""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Global tracer
_tracer = None
_tracer_provider = None


def setup_telemetry(service_name: str = "omni-backend"):
    """
    Setup OpenTelemetry tracing
    
    Call this once at application startup:
        from middleware.telemetry import setup_telemetry
        setup_telemetry("omni-backend")
    """
    global _tracer, _tracer_provider
    
    # Check if telemetry is enabled
    if not os.getenv("ENABLE_TELEMETRY", "false").lower() in ("1", "true", "yes"):
        logger.info("⏭️ Telemetry disabled (set ENABLE_TELEMETRY=true to enable)")
        return
    
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        
        # Optional exporters
        exporter = None
        exporter_type = os.getenv("OTEL_EXPORTER", "console")  # console, jaeger, otlp
        
        if exporter_type == "console":
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter
            exporter = ConsoleSpanExporter()
            logger.info("📊 Using Console exporter for traces")
            
        elif exporter_type == "jaeger":
            from opentelemetry.exporter.jaeger.thrift import JaegerExporter
            jaeger_host = os.getenv("JAEGER_HOST", "localhost")
            jaeger_port = int(os.getenv("JAEGER_PORT", "6831"))
            exporter = JaegerExporter(
                agent_host_name=jaeger_host,
                agent_port=jaeger_port,
            )
            logger.info(f"📊 Using Jaeger exporter: {jaeger_host}:{jaeger_port}")
            
        elif exporter_type == "otlp":
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            logger.info(f"📊 Using OTLP exporter: {otlp_endpoint}")
        
        # Create resource with service name
        resource = Resource(attributes={
            SERVICE_NAME: service_name
        })
        
        # Create tracer provider
        _tracer_provider = TracerProvider(resource=resource)
        
        # Add span processor with exporter
        if exporter:
            _tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
        
        # Set as global tracer provider
        trace.set_tracer_provider(_tracer_provider)
        
        # Get tracer
        _tracer = trace.get_tracer(__name__)
        
        logger.info(f"✅ OpenTelemetry initialized for {service_name}")
        
    except ImportError as e:
        logger.warning(f"⚠️ OpenTelemetry not available: {e}")
    except Exception as e:
        logger.error(f"❌ Failed to setup telemetry: {e}")


def get_tracer():
    """Get the global tracer"""
    return _tracer


def instrument_fastapi(app):
    """
    Instrument FastAPI app with OpenTelemetry
    
    Usage:
        from fastapi import FastAPI
        from middleware.telemetry import setup_telemetry, instrument_fastapi
        
        app = FastAPI()
        setup_telemetry("omni-backend")
        instrument_fastapi(app)
    """
    if _tracer is None:
        logger.debug("Telemetry not initialized, skipping FastAPI instrumentation")
        return
    
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(app)
        logger.info("✅ FastAPI instrumented with OpenTelemetry")
    except Exception as e:
        logger.error(f"Failed to instrument FastAPI: {e}")


def trace_function(name: Optional[str] = None):
    """
    Decorator to trace a function
    
    Usage:
        from middleware.telemetry import trace_function
        
        @trace_function("ml.predict")
        async def predict_revenue(data):
            # Your code here
            return result
    """
    def decorator(func):
        from functools import wraps
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if _tracer is None:
                return await func(*args, **kwargs)
            
            span_name = name or f"{func.__module__}.{func.__name__}"
            
            with _tracer.start_as_current_span(span_name):
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# Middleware for request tracing
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class TelemetryMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add tracing context to requests
    
    Usage:
        app.add_middleware(TelemetryMiddleware)
    """
    
    async def dispatch(self, request: Request, call_next):
        if _tracer is None:
            return await call_next(request)
        
        # Create span for this request
        with _tracer.start_as_current_span(
            f"{request.method} {request.url.path}",
            attributes={
                "http.method": request.method,
                "http.url": str(request.url),
                "http.route": request.url.path,
            }
        ) as span:
            try:
                response: Response = await call_next(request)
                
                # Add response status to span
                span.set_attribute("http.status_code", response.status_code)
                
                return response
            except Exception as e:
                # Record exception in span
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise


# Example usage:
"""
# In main.py:

from middleware.telemetry import setup_telemetry, instrument_fastapi, TelemetryMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_telemetry("omni-backend")
    yield
    # Shutdown

app = FastAPI(lifespan=lifespan)

# Instrument FastAPI
instrument_fastapi(app)

# Add telemetry middleware
app.add_middleware(TelemetryMiddleware)


# In your routes:

from middleware.telemetry import trace_function

@app.post("/api/v1/predict")
@trace_function("ml.predict_revenue")
async def predict_revenue(payload: dict):
    result = await ml_service.predict(payload)
    return result
"""
