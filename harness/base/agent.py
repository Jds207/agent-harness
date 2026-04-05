"""BaseAgent – the abstract contract every agent must implement.

Why this exists:
    A uniform interface lets the harness wrap *any* agent with retry logic,
    validation, observability, and feedback without knowing the agent's
    internal details.  Subclasses only need to implement ``_execute``.
"""

from __future__ import annotations

import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from harness.base.config import AgentConfig
from harness.observability.logging import get_logger
from harness.schemas.base import BaseOutputSchema

T = TypeVar("T", bound=BaseOutputSchema)

logger = get_logger()


class TraceRecord(BaseModel):
    """A single step in the agent's execution trace.

    Why this exists:
        Traces are first-class data.  Every step records its name, duration,
        success status, and any error so that post-run analysis is trivial.
    """

    trace_id: str
    step_name: str
    duration_seconds: float
    success: bool
    error: str | None = None
    metadata: dict[str, Any] = {}


class BaseAgent(ABC, Generic[T]):
    """Abstract base for all harness-managed agents.

    Why this exists:
        Enforces the run → validate → trace contract.  Concrete agents only
        implement ``_execute``; the harness handles everything else.

    Args:
        config: Agent configuration (model, temperature, retries, etc.).
    """

    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self._trace: list[TraceRecord] = []
        self._trace_id: str = uuid.uuid4().hex

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, input_data: dict[str, Any]) -> T:
        """Execute the agent and validate the result.

        Args:
            input_data: Arbitrary input payload for the agent.

        Returns:
            A validated output conforming to the agent's output schema.

        Raises:
            HarnessValidationError: When validation of the output fails.
        """
        step = "execute"
        start = time.monotonic()
        try:
            result = self._execute(input_data)
            self._record(step, time.monotonic() - start, success=True)
        except Exception as exc:
            self._record(step, time.monotonic() - start, success=False, error=str(exc))
            raise

        step = "validate"
        start = time.monotonic()
        try:
            self.validate(result)
            self._record(step, time.monotonic() - start, success=True)
        except Exception as exc:
            self._record(step, time.monotonic() - start, success=False, error=str(exc))
            raise

        return result

    def validate(self, output: T) -> None:
        """Run output validation.  Override to add business-rule checks.

        Args:
            output: The output to validate.

        Raises:
            HarnessValidationError: On validation failure.
        """
        # Default: Pydantic already validated at construction time.
        # Subclasses should call super().validate(output) then add checks.

    def get_trace(self) -> list[TraceRecord]:
        """Return the full execution trace for this run."""
        return list(self._trace)

    # ------------------------------------------------------------------
    # Abstract
    # ------------------------------------------------------------------

    @abstractmethod
    def _execute(self, input_data: dict[str, Any]) -> T:
        """Core agent logic.  Subclasses must implement this.

        Args:
            input_data: The input payload.

        Returns:
            The agent's raw (but schema-valid) output.
        """

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _record(
        self,
        step_name: str,
        duration: float,
        *,
        success: bool,
        error: str | None = None,
    ) -> None:
        record = TraceRecord(
            trace_id=self._trace_id,
            step_name=step_name,
            duration_seconds=round(duration, 6),
            success=success,
            error=error,
        )
        self._trace.append(record)
        logger.info(
            "agent_step",
            trace_id=self._trace_id,
            step_name=step_name,
            success=success,
            duration=round(duration, 6),
            error=error,
        )
