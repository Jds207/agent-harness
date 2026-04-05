"""RetryWithFallback – tenacity-based retry with optional fallback callable.

Why this exists:
    A single retry decorator cannot handle the real world: you need
    exponential back-off, jitter, a budget cap, *and* the ability to
    fall back to a cheaper/simpler model or tool when the primary is
    persistently failing.  This class composes all of that.
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any, TypeVar

from tenacity import (
    RetryError,
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    wait_none,
)

from harness.observability.logging import get_logger
from harness.utils.exceptions import RetryExhaustedError

F = TypeVar("F", bound=Callable[..., Any])

logger = get_logger()


class RetryWithFallback:
    """Wraps a callable with retry logic and an optional fallback.

    Why this exists:
        Agents often call external services that can transiently fail.
        This class retries with exponential back-off, then – if all
        attempts are exhausted – invokes an optional fallback callable
        before raising ``RetryExhaustedError``.

    Args:
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds for exponential back-off.
        fallback: An optional callable to invoke when retries are exhausted.
    """

    def __init__(
        self,
        *,
        max_retries: int = 3,
        base_delay: float = 1.0,
        fallback: Callable[..., Any] | None = None,
    ) -> None:
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.fallback = fallback

    def wrap(self, fn: F) -> F:
        """Decorate ``fn`` with retry + fallback logic.

        Args:
            fn: The callable to protect.

        Returns:
            A wrapped callable with the same signature.
        """
        retry_decorator = retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_none() if self.base_delay == 0 else wait_exponential_jitter(initial=self.base_delay, max=60),
            reraise=False,
        )
        retried_fn = retry_decorator(fn)

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return retried_fn(*args, **kwargs)
            except RetryError as exc:
                logger.warning(
                    "retry_exhausted",
                    function=fn.__name__,
                    attempts=self.max_retries,
                )
                if self.fallback is not None:
                    logger.info("using_fallback", function=fn.__name__)
                    return self.fallback(*args, **kwargs)
                raise RetryExhaustedError(
                    f"All {self.max_retries} attempts failed for {fn.__name__}",
                    attempts=self.max_retries,
                    last_error=exc.last_attempt.exception() if exc.last_attempt else None,
                ) from exc

        return wrapper  # type: ignore[return-value]
