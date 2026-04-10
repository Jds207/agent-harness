"""InvariantValidator – ensures business rules are maintained.

Why this exists:
    Schema validation catches structural errors, but business logic invariants
    (e.g. "balance can't go negative") need domain-specific checks.  This
    validator runs those checks and fails fast if they're violated.
"""

from pydantic import ValidationError
from typing import Any

from .base import AgentInput, AgentOutput


class InvariantValidator:
    """Validator for maintaining invariants in agent operations.

    Why this design: InvariantValidator centralizes all validation logic, ensuring that inputs and outputs always meet required constraints before and after processing, implementing correctness by construction.

    This validator checks both structural schemas and business logic invariants.
    """

    def validate_input(self, input_obj: AgentInput) -> None:
        """Validate agent input against schemas and invariants.

        Args:
            input_obj: The input object to validate

        Raises:
            ValueError: If validation fails
        """
        # Structural validation is handled by Pydantic BaseModel
        # Additional business logic invariants can be added here

        if not isinstance(input_obj.data, dict):
            raise ValueError("Input data must be a dictionary")

        # Example invariant: data cannot be empty for processing
        if not input_obj.data:
            raise ValueError("Input data cannot be empty")

    def validate_output(self, output_obj: AgentOutput) -> None:
        """Validate agent output against schemas and invariants.

        Args:
            output_obj: The output object to validate

        Raises:
            ValueError: If validation fails
        """
        # Structural validation is handled by Pydantic BaseModel
        # Additional business logic invariants can be added here

        # Example invariant: failed operations must have error details
        if not output_obj.success and not output_obj.result:
            raise ValueError("Failed output must contain error details in result field")