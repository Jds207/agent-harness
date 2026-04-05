"""Observability – structured logging and tracing.

Why this exists:
    Without structured, queryable logs every debugging session turns into
    grep archaeology.  This module configures structlog once so that every
    component automatically emits JSON-friendly events with trace context.
"""

from harness.observability.logging import get_logger, setup_logging

__all__ = ["get_logger", "setup_logging"]
