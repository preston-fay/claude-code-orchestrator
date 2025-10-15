"""
Prometheus metrics for Kearney Data Platform.

Provides counters, gauges, and histograms for:
- HTTP requests (route, method, status)
- Request latency
- DuckDB query duration
- Isochrone requests by provider
- Orchestrator phase duration
- Agent retries
"""

try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        generate_latest,
        CONTENT_TYPE_LATEST,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


# HTTP Metrics
if PROMETHEUS_AVAILABLE:
    http_requests_total = Counter(
        "http_requests_total",
        "Total HTTP requests",
        ["route", "method", "status"],
    )

    http_request_latency = Histogram(
        "http_request_latency_seconds",
        "HTTP request latency in seconds",
        ["route", "method"],
        buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    )

    # Database Metrics
    duckdb_query_seconds = Histogram(
        "duckdb_query_seconds",
        "DuckDB query execution time",
        ["query_type"],
        buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    )

    duckdb_query_total = Counter(
        "duckdb_query_total",
        "Total DuckDB queries",
        ["query_type", "status"],
    )

    # Isochrone Metrics
    isochrone_requests_total = Counter(
        "isochrone_requests_total",
        "Total isochrone requests",
        ["provider"],
    )

    isochrone_request_latency = Histogram(
        "isochrone_request_latency_seconds",
        "Isochrone request latency",
        ["provider"],
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    )

    # Orchestrator Metrics
    orchestrator_phase_seconds = Histogram(
        "orchestrator_phase_seconds",
        "Orchestrator phase duration",
        ["phase"],
        buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0],
    )

    orchestrator_agent_retries_total = Counter(
        "orchestrator_agent_retries_total",
        "Total agent retries",
        ["agent", "phase"],
    )

    orchestrator_runs_total = Counter(
        "orchestrator_runs_total",
        "Total orchestrator runs",
        ["status"],
    )

    # Cache Metrics
    cache_hits_total = Counter(
        "cache_hits_total",
        "Total cache hits",
        ["cache_type"],
    )

    cache_misses_total = Counter(
        "cache_misses_total",
        "Total cache misses",
        ["cache_type"],
    )

    cache_size_bytes = Gauge(
        "cache_size_bytes",
        "Cache size in bytes",
        ["cache_type"],
    )

    # Registry Metrics
    registry_models_total = Gauge(
        "registry_models_total",
        "Total models in registry",
    )

    registry_datasets_total = Gauge(
        "registry_datasets_total",
        "Total datasets in catalog",
    )

else:
    # Dummy metrics when Prometheus is not available
    class DummyMetric:
        def labels(self, *args, **kwargs):
            return self

        def inc(self, *args, **kwargs):
            pass

        def observe(self, *args, **kwargs):
            pass

        def set(self, *args, **kwargs):
            pass

    http_requests_total = DummyMetric()
    http_request_latency = DummyMetric()
    duckdb_query_seconds = DummyMetric()
    duckdb_query_total = DummyMetric()
    isochrone_requests_total = DummyMetric()
    isochrone_request_latency = DummyMetric()
    orchestrator_phase_seconds = DummyMetric()
    orchestrator_agent_retries_total = DummyMetric()
    orchestrator_runs_total = DummyMetric()
    cache_hits_total = DummyMetric()
    cache_misses_total = DummyMetric()
    cache_size_bytes = DummyMetric()
    registry_models_total = DummyMetric()
    registry_datasets_total = DummyMetric()


def get_metrics() -> bytes:
    """
    Get Prometheus metrics in text format.

    Returns:
        Metrics in Prometheus text format
    """
    if PROMETHEUS_AVAILABLE:
        return generate_latest()
    else:
        return b"# Prometheus client not available\n"


def get_content_type() -> str:
    """
    Get Prometheus metrics content type.

    Returns:
        Content type string
    """
    if PROMETHEUS_AVAILABLE:
        return CONTENT_TYPE_LATEST
    else:
        return "text/plain"
