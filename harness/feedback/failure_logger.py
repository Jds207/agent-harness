"""FailureLogger – persist full failure context for post-mortem analysis.

Why this exists:
    When an agent fails, you need more than a stack trace.  You need the
    input data, the config, the partial output, and the error
    classification.  This logger captures all of that in a structured
    record so debugging never starts from scratch.
"""

from typing import Any
from datetime import datetime
import json


class FailureLogger:
    """Logger for capturing and classifying failures.

    Why this design: FailureLogger treats failures as first-class data, capturing detailed information about errors to enable analysis and improvement of agent reliability. It stores failures in a structured format for later analysis and pattern detection.

    Args:
        log_file: Path to the file where failures will be logged
    """

    def __init__(self, log_file: str = "failures.log") -> None:
        """Initialize failure logger.

        Args:
            log_file: File path for storing failure records
        """
        self.log_file = log_file

    def log_failure(self, error: Exception, context: Any) -> None:
        """Log a failure with full context.

        Args:
            error: The exception that occurred
            context: Context information about the failure (e.g., input data)
        """
        failure_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "error_module": error.__class__.__module__,
            "context": str(context)
        }

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(failure_record, ensure_ascii=False) + "\n")
        except Exception as log_error:
            # If logging fails, print to stderr as fallback
            print(f"Failed to log failure: {log_error}", file=__import__("sys").stderr)
