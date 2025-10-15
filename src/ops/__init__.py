"""Ops layer for Kearney Data Platform: secrets, logging, tracing, metrics, caching."""

from .secrets import get_secret, SecretSource
from .logging import configure_logging, get_logger
from .metrics import (
    http_requests_total,
    http_request_latency,
    duckdb_query_seconds,
    isochrone_requests_total,
    orchestrator_phase_seconds,
    orchestrator_agent_retries_total,
)

__all__ = [
    "get_secret",
    "SecretSource",
    "configure_logging",
    "get_logger",
    "http_requests_total",
    "http_request_latency",
    "duckdb_query_seconds",
    "isochrone_requests_total",
    "orchestrator_phase_seconds",
    "orchestrator_agent_retries_total",
]
