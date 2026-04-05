"""StepValidator – validate intermediate pipeline step outputs.

Why this exists:
    In multi-step agent workflows, catching a bad output *between* steps
    prevents wasted work and makes debugging easier.  StepValidator wraps
    Pydantic model validation and invariant checks into a single call that
    raises a typed ``HarnessValidationError`` on any failure.
"""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from harness.observability.logging import get_logger
from harness.schemas.invariants import InvariantValidator
from harness.utils.exceptions import HarnessValidationError

T = TypeVar("T", bound=BaseModel)

logger = get_logger()


class StepValidator:
    """Validates step output against a Pydantic model and optional invariants.

    Why this exists:
        Combines schema validation (Pydantic) and business-rule validation
        (InvariantValidator) into a single method so pipeline steps can
        validate with one call.

    Args:
        invariant_validator: Optional invariant validator to run after
            schema validation succeeds.
    """

    def __init__(self, invariant_validator: InvariantValidator | None = None) -> None:
        self._invariant_validator = invariant_validator

    def validate(self, model_class: type[T], data: dict[str, Any]) -> T:
        """Parse ``data`` into ``model_class`` and run invariant checks.

        Args:
            model_class: The Pydantic model to validate against.
            data: Raw data dict to validate.

        Returns:
            A validated model instance.

        Raises:
            HarnessValidationError: On schema or invariant failure.
        """
        try:
            instance = model_class.model_validate(data)
        except ValidationError as exc:
            logger.error("step_validation_failed", errors=exc.error_count())
            raise HarnessValidationError(
                f"Schema validation failed: {exc}",
                violations=[str(e["type"]) for e in exc.errors()],
            ) from exc

        if self._invariant_validator is not None:
            self._invariant_validator.check(instance)

        return instance
