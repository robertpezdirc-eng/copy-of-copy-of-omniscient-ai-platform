import time
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Configure tracer provider with service name
resource = Resource.create({"service.name": "omni-loadgen"})
provider = TracerProvider(resource=resource)
trace.set_tracer_provider(provider)

# Export to local Tempo via OTLP gRPC (mapped to localhost:4317)
exporter = OTLPSpanExporter(endpoint="localhost:4317", insecure=True)
processor = BatchSpanProcessor(exporter)
provider.add_span_processor(processor)

tracer = trace.get_tracer(__name__)

def generate_spans(n: int = 20):
    for i in range(n):
        with tracer.start_as_current_span("demo-operation") as span:
            span.set_attribute("iteration", i)
            span.set_attribute("component", "demo")
            span.set_attribute("env", "dev")
            time.sleep(0.05)

if __name__ == "__main__":
    generate_spans(50)
    # Give exporter a moment to flush
    time.sleep(1)