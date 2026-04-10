"""RetryWithFallback – tenacity-based retry with optional fallback callable.

Why this exists:
    A single retry decorator cannot handle the real world: you need
    exponential back-off, jitter, a budget cap, *and* the ability to
    fall back to a cheaper/simpler model or tool when the primary is
    persistently failing.  This class composes all of that.
"""

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Callable, Any

from pydantic import BaseModel, Field


class RetryConfig(BaseModel):
    """Configuration for retry behavior.

    Why this design: RetryConfig centralizes retry parameters in a validated structure,
    ensuring consistent and safe retry behavior across the system.
    """
    max_attempts: int = Field(default=3, description="Maximum number of retry attempts")
    wait_multiplier: float = Field(default=1.0, description="Base multiplier for exponential backoff")
    wait_max: float = Field(default=60.0, description="Maximum wait time between retries")


class RetryWithFallback:
    """Retry mechanism with fallback strategies.

    Why this design: RetryWithFallback uses tenacity for robust retry logic with exponential backoff,
    ensuring transient failures don't break agent operations while providing configurable fallback behavior.

    Args:
        config: Retry configuration parameters
    """

    def __init__(self, config: RetryConfig) -> None:
        """Initialize retry handler with configuration.

        Args:
            config: Retry configuration object
        """
        self.config = config

    def retry(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator to add retry logic to a function.

        Args:
            func: The function to decorate with retry logic

        Returns:
            Decorated function with retry behavior
        """
        return retry(
            stop=stop_after_attempt(self.config.max_attempts),
            wait=wait_exponential(multiplier=self.config.wait_multiplier, max=self.config.wait_max),
            retry=retry_if_exception_type(Exception),
            reraise=True
        )(func)
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
