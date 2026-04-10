"""StructuredLogger – consistent, queryable logging for all components.

Why this exists:
    Without structured logs, debugging production issues requires grep
    archaeology.  StructuredLogger wraps structlog to ensure every log
    entry carries trace context, timestamps, and machine-readable fields.
"""

import structlog
from typing import Any, Dict

from ..schemas.base import AgentInput, AgentOutput


class StructuredLogger:
    """Structured logging for agent operations.

    Why this design: StructuredLogger uses structlog to provide consistent, machine-readable logs with context, enabling effective monitoring and debugging of agent behavior. It provides dedicated methods for logging agent successes and failures with full context.

    Args:
        agent_name: Name of the agent for log context
    """

    def __init__(self, agent_name: str) -> None:
        """Initialize logger with agent context.

        Args:
            agent_name: Name of the agent for log identification
        """
        self.logger = structlog.get_logger(agent_name)
        self.agent_name = agent_name

    def log_success(self, input_obj: AgentInput, output_obj: AgentOutput) -> None:
        """Log successful operation with full context.

        Args:
            input_obj: The input that was processed
            output_obj: The output that was produced
        """
        self.logger.info(
            "agent_success",
            agent_name=self.agent_name,
            input_data=input_obj.data,
            input_metadata=input_obj.metadata,
            output_result=output_obj.result,
            output_metadata=output_obj.metadata,
            success=output_obj.success
        )

    def log_failure(self, input_obj: AgentInput, error: Exception) -> None:
        """Log failed operation with error details.

        Args:
            input_obj: The input that failed to process
            error: The exception that occurred
        """
        self.logger.error(
            "agent_failure",
            agent_name=self.agent_name,
            input_data=input_obj.data,
            input_metadata=input_obj.metadata,
            error_type=type(error).__name__,
            error_message=str(error),
            error_module=error.__class__.__module__
        )