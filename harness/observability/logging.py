"""Structured logging configuration via structlog.

Why this exists:
    A single ``setup_logging()`` call at process start ensures every log
    event is machine-parseable JSON with consistent fields (trace_id,
    step_name, etc.).  ``get_logger()`` returns a bound logger that
    components use without worrying about configuration.
"""

from __future__ import annotations

import structlog


def setup_logging(*, json: bool = True, level: str = "INFO") -> None:
    """Configure structlog for the process.

    Args:
        json: If ``True``, render events as JSON; otherwise use console format.
        level: Minimum log level (``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``).
    """
    processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    if json:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            structlog._log_levels.NAME_TO_LEVEL[level.lower()],
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(**initial_bindings: object) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger.

    Args:
        **initial_bindings: Key-value pairs to bind into every event from
            this logger instance.

    Returns:
        A structlog bound logger.
    """
    return structlog.get_logger(**initial_bindings)  # type: ignore[return-value]
