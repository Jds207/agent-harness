"""Base abstractions for agents and their configuration.

Why this exists:
    Provides the contract that every agent must fulfil – run, validate,
    and expose a trace – so the rest of the harness (retry, logging,
    feedback) can operate generically over any agent implementation.
"""

from harness.base.agent import BaseAgent
from harness.base.config import AgentConfig

__all__ = ["BaseAgent", "AgentConfig"]
