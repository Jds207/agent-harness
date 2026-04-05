"""BaseOutputSchema – the root model for all agent outputs.

Why this exists:
    Every agent output goes through Pydantic validation.  This base class
    provides shared fields (trace_id, created_at) so downstream consumers
    always have provenance metadata.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class BaseOutputSchema(BaseModel):
    """Root schema for agent outputs.

    Why this exists:
        Guarantees that every agent output carries a trace_id and timestamp,
        making it trivially auditable.

    Attributes:
        trace_id: Opaque identifier linking this output to its execution trace.
        created_at: UTC timestamp of when the output was produced.
        metadata: Arbitrary key-value pairs for domain-specific context.
    """

    trace_id: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = {}

    model_config = {"extra": "forbid"}
