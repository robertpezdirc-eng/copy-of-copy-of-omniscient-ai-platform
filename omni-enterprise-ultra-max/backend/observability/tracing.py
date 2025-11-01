import os
import logging
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

try:
    # Jaeger exporters
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter as _JaegerThriftExporter
except Exception:  # pragma: no cover
    _JaegerThriftExporter = None  # type: ignore

logger = logging.getLogger(__name__)


def _jaeger_exporter() -> Optional[object]:
    host = os.getenv("JAEGER_HOST", "localhost")
    port = int(os.getenv("JAEGER_PORT", "6831"))
    if _JaegerThriftExporter is None:
        logger.warning("Jaeger exporter not installed; tracing disabled")
        return None
    try:
        return _JaegerThriftExporter(agent_host_name=host, agent_port=port)  # type: ignore
    except Exception as e:  # pragma: no cover
        logger.error(f"Failed to create Jaeger exporter: {e}")
        return None


def init_tracing(app) -> bool:
    """Initialize OpenTelemetry tracing for the FastAPI app.

    Controlled by env ENABLE_TRACING (1/true). Uses Jaeger exporter by default.
    Returns True if tracing initialized, False otherwise.
    """
    enabled = os.getenv("ENABLE_TRACING", "0").lower() in ("1", "true", "yes")
    if not enabled:
        logger.info("Tracing disabled (ENABLE_TRACING not set)")
        return False

    service_name = os.getenv("OTEL_SERVICE_NAME", "omni-backend")
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    exporter = _jaeger_exporter()
    if exporter:
        provider.add_span_processor(BatchSpanProcessor(exporter))
    else:
        logger.warning("No exporter configured; tracing provider set without exporter")

    trace.set_tracer_provider(provider)

    try:
        FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
    except Exception as e:  # pragma: no cover
        logger.error(f"Failed to instrument FastAPI for tracing: {e}")
        return False

    logger.info("OpenTelemetry tracing initialized")
    return True
