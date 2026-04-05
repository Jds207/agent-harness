"""FailureLogger – persist full failure context for post-mortem analysis.

Why this exists:
    When an agent fails, you need more than a stack trace.  You need the
    input data, the config, the partial output, and the error
    classification.  This logger captures all of that in a structured
    record so debugging never starts from scratch.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from harness.observability.logging import get_logger

logger = get_logger()


class FailureRecord(BaseModel):
    """A structured record of a single failure event.

    Attributes:
        timestamp: When the failure occurred (UTC).
        error_type: The exception class name.
        error_message: The exception message.
        trace_id: The trace id of the run that failed.
        step_name: Which pipeline step failed.
        input_data: The input that caused the failure.
        config_snapshot: Agent configuration at failure time.
        partial_output: Any output produced before the failure.
    """

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    error_type: str
    error_message: str
    trace_id: str = ""
    step_name: str = ""
    input_data: dict[str, Any] = {}
    config_snapshot: dict[str, Any] = {}
    partial_output: dict[str, Any] = {}


class FailureLogger:
    """Accumulates structured failure records in memory.

    Why this exists:
        Provides a queryable log of everything that went wrong so that
        feedback loops and dashboards can surface patterns.  In v0.1 this
        is in-memory; future versions will persist to a database.
    """

    def __init__(self) -> None:
        self._records: list[FailureRecord] = []

    def log(
        self,
        *,
        error: Exception,
        trace_id: str = "",
        step_name: str = "",
        input_data: dict[str, Any] | None = None,
        config_snapshot: dict[str, Any] | None = None,
        partial_output: dict[str, Any] | None = None,
    ) -> FailureRecord:
        """Record a failure with full context.

        Args:
            error: The exception that was raised.
            trace_id: Trace identifier for the current run.
            step_name: Name of the step that failed.
            input_data: The input payload that triggered the failure.
            config_snapshot: Agent configuration at the time of failure.
            partial_output: Any output produced before the failure.

        Returns:
            The created ``FailureRecord``.
        """
        record = FailureRecord(
            error_type=type(error).__name__,
            error_message=str(error),
            trace_id=trace_id,
            step_name=step_name,
            input_data=input_data or {},
            config_snapshot=config_snapshot or {},
            partial_output=partial_output or {},
        )
        self._records.append(record)
        logger.error(
            "failure_logged",
            error_type=record.error_type,
            trace_id=trace_id,
            step_name=step_name,
        )
        return record

    @property
    def records(self) -> list[FailureRecord]:
        """All failure records logged so far."""
        return list(self._records)

    def clear(self) -> None:
        """Remove all stored records."""
        self._records.clear()
