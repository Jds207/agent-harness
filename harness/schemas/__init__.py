"""Schema definitions and invariant validation.

Why this exists:
    Agents must produce structured, validated output.  These schemas and
    validators ensure every output conforms to its contract *and* to any
    business-level invariants the caller defines.
"""

from .base import AgentInput, AgentOutput
from .validator import InvariantValidator

__all__ = ["AgentInput", "AgentOutput", "InvariantValidator"]

__all__ = ["BaseOutputSchema", "InvariantValidator"]
