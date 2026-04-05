"""Schema definitions and invariant validation.

Why this exists:
    Agents must produce structured, validated output.  These schemas and
    validators ensure every output conforms to its contract *and* to any
    business-level invariants the caller defines.
"""

from harness.schemas.base import BaseOutputSchema
from harness.schemas.invariants import InvariantValidator

__all__ = ["BaseOutputSchema", "InvariantValidator"]
