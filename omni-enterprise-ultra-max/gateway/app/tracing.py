"""
Distributed tracing with OpenTelemetry and Jaeger.
Traces requests across gateway -> backend.
"""
from __future__ import annotations

import logging
from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from .settings import settings

logger = logging.getLogger(__name__)

tracer_provider: Optional[TracerProvider] = None


def init_tracing(app) -> Optional[trace.Tracer]:
    """
    Initialize OpenTelemetry tracing with Jaeger exporter.
    
    Args:
        app: FastAPI application instance
        
    Returns:
        Tracer instance if tracing is enabled, None otherwise
    """
    global tracer_provider
    
    if not settings.enable_tracing or not settings.jaeger_host:
        logger.info("Distributed tracing disabled (ENABLE_TRACING=false or JAEGER_HOST not set)")
        return None
    
    try:
        # Create resource with service name
        resource = Resource(attributes={
            SERVICE_NAME: settings.service_name,
            "environment": settings.environment,
        })
        
        # Create tracer provider
        tracer_provider = TracerProvider(resource=resource)
        
        # Configure Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name=settings.jaeger_host,
            agent_port=settings.jaeger_port,
        )
        
        # Add span processor
        span_processor = BatchSpanProcessor(jaeger_exporter)
        tracer_provider.add_span_processor(span_processor)
        
        # Set as global tracer provider
        trace.set_tracer_provider(tracer_provider)
        
        # Instrument FastAPI automatically
        FastAPIInstrumentor.instrument_app(app)
        
        logger.info(
            f"OpenTelemetry tracing initialized. "
            f"Exporting to Jaeger at {settings.jaeger_host}:{settings.jaeger_port}"
        )
        
        # Return tracer for manual instrumentation
        return trace.get_tracer(__name__)
        
    except Exception as e:
        logger.error(f"Failed to initialize tracing: {e}")
        return None


def get_tracer() -> trace.Tracer:
    """Get the global tracer instance."""
    return trace.get_tracer(__name__)


def add_trace_context_to_headers(headers: dict) -> dict:
    """
    Add trace context to outgoing HTTP headers for distributed tracing.
    
    Args:
        headers: Existing headers dict
        
    Returns:
        Headers with trace context added
    """
    from opentelemetry.propagate import inject
    
    # Create a copy to avoid mutating the original
    headers_with_trace = headers.copy()
    
    # Inject trace context
    inject(headers_with_trace)
    
    return headers_with_trace
