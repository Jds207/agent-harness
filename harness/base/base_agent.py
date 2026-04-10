"""BaseAgent – the abstract contract every agent must implement.

Why this exists:
    A uniform interface lets the harness wrap *any* agent with retry logic,
    validation, observability, and feedback without knowing the agent's
    internal details.  Subclasses only need to implement ``_execute``.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from pydantic import BaseModel

from ..schemas.base import AgentInput, AgentOutput
from ..schemas.validator import InvariantValidator
from ..reliability.retry import RetryWithFallback, RetryConfig
from ..reliability.circuit_breaker import CircuitBreaker
from ..reliability.validator import StepValidator
from ..observability.logger import StructuredLogger
from ..feedback.failure_logger import FailureLogger
from ..feedback.lessons_store import LessonsLearnedStore
from .config import AgentConfig


class BaseAgent(ABC):
    """Abstract base class for all reliable agents.

    Why this design: BaseAgent enforces correctness by construction through schema validation at every step, implements reliability patterns (retry, circuit breaker), comprehensive observability, and feedback loops for continuous improvement. Composition over inheritance allows flexible layering of reliability features.

    Attributes:
        config: Agent configuration
        logger: Structured logger for observability
        validator: Input/output validator
        retry_handler: Retry mechanism with fallback
        circuit_breaker: Circuit breaker for fault tolerance
        step_validator: Step-by-step validation
        failure_logger: Failure logging for analysis
        lessons_store: Storage for lessons learned
    """

    def __init__(self, config: AgentConfig) -> None:
        """Initialize the agent with configuration and reliability layers.

        Args:
            config: Agent configuration object
        """
        self.config = config
        self.logger = StructuredLogger(config.name)
        self.validator = InvariantValidator()
        self.retry_handler = RetryWithFallback(RetryConfig(max_attempts=config.max_retries))
        self.circuit_breaker = CircuitBreaker()
        self.step_validator = StepValidator()
        self.failure_logger = FailureLogger()
        self.lessons_store = LessonsLearnedStore()

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data and return output with full reliability guarantees.

        This method implements the complete harness pipeline:
        validation → retry → circuit breaker → logging → feedback

        Args:
            input_data: Input data as dictionary

        Returns:
            Output data as dictionary

        Raises:
            ValidationError: If input/output validation fails
            Exception: If processing fails after all retries
        """
        # Validate input schema
        input_obj = AgentInput(**input_data)
        self.validator.validate_input(input_obj)

        try:
            # Process with reliability layers
            result = self._process_with_reliability(input_obj)

            # Validate output schema
            output_obj = AgentOutput(**result)
            self.validator.validate_output(output_obj)

            # Log successful operation
            self.logger.log_success(input_obj, output_obj)

            return result

        except Exception as e:
            # Log failure with full context
            self.logger.log_failure(input_obj, e)

            # Record failure for analysis
            self.failure_logger.log_failure(e, input_obj)

            # Store lesson for continuous improvement
            self.lessons_store.store_lesson(e, "process_failure")

            # Re-raise to maintain error propagation
            raise

    def _process_with_reliability(self, input_obj: AgentInput) -> Dict[str, Any]:
        """Internal processing method with reliability layers applied.

        Args:
            input_obj: Validated input object

        Returns:
            Processing result
        """
        @self.retry_handler.retry
        @self.circuit_breaker.call
        def _inner_process() -> Dict[str, Any]:
            # Validate pre-processing state
            self.step_validator.validate_step("pre_process")

            # Execute agent-specific logic
            result = self._execute(input_obj)

            # Validate post-processing state
            self.step_validator.validate_step("post_process")

            return result

        return _inner_process()

    @abstractmethod
    def _execute(self, input_obj: AgentInput) -> Dict[str, Any]:
        """Execute the agent-specific logic.

        Subclasses must implement this method to provide their domain logic.

        Args:
            input_obj: Validated input object

        Returns:
            Result dictionary that will be validated as AgentOutput
        """
        pass