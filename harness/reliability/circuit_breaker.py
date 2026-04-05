"""CircuitBreaker – fail fast when a downstream is unhealthy.

Why this exists:
    When an external service is down, continuing to hammer it wastes
    latency budget and may trigger rate-limits.  A circuit breaker
    short-circuits calls after a threshold of consecutive failures,
    then periodically probes to see if the service has recovered.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from harness.observability.logging import get_logger
from harness.utils.exceptions import CircuitOpenError

logger = get_logger()


class CircuitBreaker:
    """Simple circuit breaker with closed → open → half-open states.

    Why this exists:
        Prevents cascading failures by stopping calls to a downstream
        service that is known to be unhealthy, and automatically
        recovering once it begins responding again.

    Args:
        name: A human-readable name for this circuit (used in logs/errors).
        failure_threshold: Consecutive failures needed to open the circuit.
        recovery_timeout: Seconds to wait before allowing a probe call.
    """

    def __init__(
        self,
        name: str,
        *,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self._failure_count: int = 0
        self._state: str = "closed"
        self._last_failure_time: float = 0.0

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
