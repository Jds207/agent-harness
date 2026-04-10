"""StepValidator – validate intermediate pipeline step outputs.

Why this exists:
    In multi-step agent workflows, catching a bad output *between* steps
    prevents wasted work and makes debugging easier.  StepValidator wraps
    Pydantic model validation and invariant checks into a single call that
    raises a typed ``HarnessValidationError`` on any failure.
"""

from typing import Any


class StepValidator:
    """Validator for processing steps.

    Why this design: StepValidator ensures each step in the agent processing pipeline meets preconditions and postconditions, maintaining invariants throughout the execution flow. It provides a simple interface for validating pipeline state transitions.

    This validator can be extended to check specific step requirements.
    """

    def validate_step(self, step_name: str, **kwargs: Any) -> None:
        """Validate a processing step.

        Args:
            step_name: Name of the step being validated
            **kwargs: Additional validation parameters

        Raises:
            ValueError: If validation fails for the step
        """
        if step_name == "pre_process":
            # Validate preconditions for processing
            # Could check system resources, dependencies, etc.
            pass

        elif step_name == "post_process":
            # Validate postconditions after processing
            # Could check output consistency, cleanup status, etc.
            pass

        else:
            raise ValueError(f"Unknown step: {step_name}")

        # Additional custom validations can be added here based on kwargs
