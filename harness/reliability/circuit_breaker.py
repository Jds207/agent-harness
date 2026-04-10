"""CircuitBreaker – fail fast when a downstream is unhealthy.

Why this exists:
    When an external service is down, continuing to hammer it wastes
    latency budget and may trigger rate-limits.  A circuit breaker
    short-circuits calls after a threshold of consecutive failures,
    then periodically probes to see if the service has recovered.
"""

from typing import Any, Callable
import time


class CircuitBreaker:
    """Circuit breaker pattern implementation.

    Why this design: CircuitBreaker prevents cascading failures by temporarily stopping calls to failing services, allowing them time to recover and maintaining system stability. It implements the classic closed/open/half-open state machine.

    Args:
        failure_threshold: Number of consecutive failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0) -> None:
        """Initialize circuit breaker.

        Args:
            failure_threshold: Consecutive failures needed to open circuit
            recovery_timeout: Time to wait before recovery attempt
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self._state = "closed"  # closed, open, half-open

    def call(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator to wrap function with circuit breaker logic.

        Args:
            func: Function to protect with circuit breaker

        Returns:
            Wrapped function
        """
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if self._state == "open":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self._state = "half-open"
                else:
                    raise Exception("Circuit breaker is open")

            try:
                result = func(*args, **kwargs)
                if self._state == "half-open":
                    self._state = "closed"
                    self.failure_count = 0
                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                if self.failure_count >= self.failure_threshold:
                    self._state = "open"
                raise e

        return wrapper

    @property
    def state(self) -> str:
        """Current circuit state: ``closed``, ``open``, or ``half-open``."""
        if self._state == "open":
            elapsed = time.monotonic() - self._last_failure_time
            if elapsed >= self.recovery_timeout:
                self._state = "half-open"
        return self._state

    def call(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute ``fn`` through the circuit breaker.

        Args:
            fn: The callable to protect.
            *args: Positional arguments forwarded to ``fn``.
            **kwargs: Keyword arguments forwarded to ``fn``.

        Returns:
            The return value of ``fn``.

        Raises:
            CircuitOpenError: If the circuit is open and not yet
                ready for a probe.
        """
        current = self.state
        if current == "open":
            raise CircuitOpenError(
                f"Circuit '{self.name}' is open – call rejected",
                circuit_name=self.name,
            )

        try:
            result = fn(*args, **kwargs)
        except Exception as exc:
            self._on_failure()
            raise exc

        self._on_success()
        return result

    def _on_success(self) -> None:
        self._failure_count = 0
        if self._state != "closed":
            logger.info("circuit_closed", circuit=self.name)
        self._state = "closed"

    def _on_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self.failure_threshold:
            self._state = "open"
            logger.warning(
                "circuit_opened",
                circuit=self.name,
                failures=self._failure_count,
            )
