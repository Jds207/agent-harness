"""Base abstractions for agents and their configuration.

Why this exists:
    Provides the contract that every agent must fulfil – run, validate,
    and expose a trace – so the rest of the harness (retry, logging,
    feedback) can operate generically over any agent implementation.
"""

from .base_agent import BaseAgent
from .config import AgentConfig

__all__ = ["BaseAgent", "AgentConfig"]

__all__ = ["BaseAgent", "AgentConfig"]
