"""Custom, typed exceptions for the harness.

Why this exists:
    Every failure must be classifiable.  Generic ``Exception`` makes it
    impossible to distinguish retriable errors from invariant violations
    from circuit-breaker trips.  Typed exceptions enable precise handling
    in retry logic, logging, and feedback loops.
"""

from __future__ import annotations


class HarnessError(Exception):
    """Root exception for all harness errors.

    Why this exists:
        Allows callers to catch *all* harness errors with a single
        ``except HarnessError`` while still distinguishing subtypes.
    """


class HarnessValidationError(HarnessError):
    """Raised when output validation or invariant checks fail.

    Attributes:
        violations: List of rule names that failed.
    """

    def __init__(self, message: str, *, violations: list[str] | None = None) -> None:
        super().__init__(message)
        self.violations: list[str] = violations or []


class RetryExhaustedError(HarnessError):
    """Raised when all retry attempts (including fallbacks) are exhausted.

    Attributes:
        attempts: Number of attempts made.
        last_error: The final exception that caused the last attempt to fail.
    """

    def __init__(self, message: str, *, attempts: int, last_error: Exception | None = None) -> None:
        super().__init__(message)
        self.attempts = attempts
        self.last_error = last_error


class CircuitOpenError(HarnessError):
    """Raised when a call is rejected because the circuit breaker is open.

    Attributes:
        circuit_name: Identifier of the open circuit.
    """

    def __init__(self, message: str, *, circuit_name: str) -> None:
        super().__init__(message)
        self.circuit_name = circuit_name
