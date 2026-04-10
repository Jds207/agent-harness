"""Base schemas for agent inputs and outputs.

Why this exists:
    Agents must produce structured, validated input and output. These base schemas
    ensure every input and output conforms to expected contracts, implementing
    correctness by construction.
"""

from pydantic import BaseModel, Field
from typing import Any, Dict


class AgentInput(BaseModel):
    """Base input schema for agents.

    Why this design: AgentInput provides a standardized, validated input structure that ensures all agent inputs conform to expected schemas, preventing runtime errors from malformed data.

    Attributes:
        data: Core input data payload
        metadata: Additional context and metadata
    """
    data: Dict[str, Any] = Field(default_factory=dict, description="Core input data payload")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context and metadata")


class AgentOutput(BaseModel):
    """Base output schema for agents.

    Why this design: AgentOutput ensures all agent outputs are properly structured and validated, maintaining consistency across different agent implementations and enabling reliable downstream processing.

    Attributes:
        result: The main output result
        metadata: Additional context and metadata
        success: Whether the operation succeeded
    """
    result: Any = Field(..., description="The main output result")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context and metadata")
    success: bool = Field(default=True, description="Whether the operation succeeded")
