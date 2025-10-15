"""
Distributed tracing for Kearney Data Platform.

Uses OpenTelemetry for:
- Request tracing (FastAPI middleware)
- Span context propagation
- OTLP export (configurable endpoint)
"""

from typing import Optional
import os

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False


_tracer: Optional[trace.Tracer] = None


def init_tracer(
    service_name: str = "kearney-platform",
    otlp_endpoint: Optional[str] = None,
) -> Optional[trace.Tracer]:
    """
    Initialize OpenTelemetry tracer.

    Reads from environment:
    - OTEL_EXPORTER_OTLP_ENDPOINT (default: http://localhost:4318)
    - OTEL_SERVICE_NAME (overrides service_name)

    Args:
        service_name: Service name for traces
        otlp_endpoint: OTLP endpoint URL (overrides env var)

    Returns:
        Tracer instance or None if not available
    """
    global _tracer

    if not OTEL_AVAILABLE:
        return None

    # Get endpoint from env or param
    endpoint = otlp_endpoint or os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "http://localhost:4318",
    )

    # Get service name from env or param
    service = os.getenv("OTEL_SERVICE_NAME", service_name)

    # Create resource
    resource = Resource.create({SERVICE_NAME: service})

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Add OTLP exporter
    try:
        otlp_exporter = OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces")
        span_processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(span_processor)
    except Exception:
        # If OTLP endpoint is not available, continue without export
        pass

    # Set global tracer provider
    trace.set_tracer_provider(provider)

    # Get tracer
    _tracer = trace.get_tracer(service)

    return _tracer


def get_tracer() -> Optional[trace.Tracer]:
    """
    Get current tracer.

    Returns:
        Tracer instance or None
    """
    return _tracer


def instrument_fastapi(app) -> None:
    """
    Instrument FastAPI app with OpenTelemetry.

    Adds middleware to:
    - Create spans for each request
    - Attach trace IDs to logs
    - Propagate context

    Args:
        app: FastAPI application
    """
    if not OTEL_AVAILABLE:
        return

    try:
        FastAPIInstrumentor.instrument_app(app)
    except Exception:
        # If instrumentation fails, continue without tracing
        pass


def get_current_trace_id() -> Optional[str]:
    """
    Get current trace ID.

    Returns:
        Trace ID hex string or None
    """
    if not OTEL_AVAILABLE:
        return None

    try:
        span = trace.get_current_span()
        if span and span.get_span_context().is_valid:
            return format(span.get_span_context().trace_id, "032x")
    except Exception:
        pass

    return None


def create_span(name: str, **attributes):
    """
    Create a span with attributes.

    Example:
        with create_span("query_execution", query_type="SELECT") as span:
            # Do work
            span.set_attribute("rows_returned", 100)

    Args:
        name: Span name
        **attributes: Span attributes
    """
    if not OTEL_AVAILABLE or _tracer is None:
        # Return dummy context manager
        class DummySpan:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def set_attribute(self, key, value):
                pass
        return DummySpan()

    span = _tracer.start_as_current_span(name)
    for key, value in attributes.items():
        span.set_attribute(key, value)

    return span
