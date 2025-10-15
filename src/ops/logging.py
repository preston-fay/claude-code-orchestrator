"""
Structured logging for Kearney Data Platform.

Uses structlog for JSON-formatted logs with:
- ISO8601 timestamps
- run_id (orchestrator)
- phase (orchestrator)
- request_id (FastAPI)
- client (multi-tenant)
- trace_id (OpenTelemetry)
"""

import logging
import sys
from typing import Optional

try:
    import structlog
    from structlog.processors import (
        JSONRenderer,
        TimeStamper,
        add_log_level,
        format_exc_info,
    )
    from structlog.stdlib import (
        add_logger_name,
        ProcessorFormatter,
    )
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False


def configure_logging(
    json: bool = True,
    level: str = "INFO",
    service_name: str = "kearney-platform",
) -> None:
    """
    Configure structured logging with structlog.

    Processors:
    - TimeStamper (ISO8601)
    - add_log_level
    - add_logger_name
    - format_exc_info (traceback)
    - JSONRenderer (if json=True)

    Context fields:
    - timestamp (ISO8601)
    - level (INFO, WARNING, ERROR)
    - logger (module name)
    - run_id (orchestrator)
    - phase (orchestrator)
    - request_id (FastAPI)
    - client (tenant)
    - trace_id (OpenTelemetry)

    Args:
        json: Use JSON format (True) or console format (False)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        service_name: Service name for logs
    """
    if not STRUCTLOG_AVAILABLE:
        # Fallback to standard logging
        logging.basicConfig(
            level=getattr(logging, level),
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
        return

    # Processors for structlog
    processors = [
        # Add log level
        add_log_level,
        # Add logger name
        add_logger_name,
        # Add timestamp (ISO8601)
        TimeStamper(fmt="iso", utc=True),
        # Format exceptions
        format_exc_info,
    ]

    if json:
        # JSON output for production
        processors.append(JSONRenderer())
    else:
        # Console output for development
        processors.append(structlog.dev.ConsoleRenderer())

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level),
    )

    # Add service name to context
    structlog.contextvars.bind_contextvars(
        service=service_name,
    )


def get_logger(name: str) -> "structlog.BoundLogger":
    """
    Get a structured logger.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Structured logger with context
    """
    if STRUCTLOG_AVAILABLE:
        return structlog.get_logger(name)
    else:
        return logging.getLogger(name)


def bind_context(**kwargs) -> None:
    """
    Bind context variables to logger.

    Example:
        bind_context(run_id="abc123", phase="planning", client="acme-corp")

    Args:
        **kwargs: Context key-value pairs
    """
    if STRUCTLOG_AVAILABLE:
        structlog.contextvars.bind_contextvars(**kwargs)


def unbind_context(*keys: str) -> None:
    """
    Unbind context variables.

    Args:
        *keys: Context keys to remove
    """
    if STRUCTLOG_AVAILABLE:
        structlog.contextvars.unbind_contextvars(*keys)


def clear_context() -> None:
    """Clear all context variables."""
    if STRUCTLOG_AVAILABLE:
        structlog.contextvars.clear_contextvars()
