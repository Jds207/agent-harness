"""AgentConfig – typed configuration for every agent.

Why this exists:
    Centralises all tuneable knobs (model name, temperature, retry budget)
    into a single validated object so that misconfiguration is caught at
    startup, not mid-run.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings


class AgentConfig(BaseSettings):
    """Configuration for a harness-managed agent.

    Why this exists:
        A single source of truth for agent settings, loadable from env vars,
        .env files, or constructor kwargs.  Pydantic validates everything
        at instantiation time.

    Attributes:
        model_name: The LLM model identifier (e.g. ``"gpt-4"``).
        temperature: Sampling temperature for the LLM.
        max_retries: How many times the harness may retry on failure.
        retry_delay_seconds: Base delay between retries (used with back-off).
        timeout_seconds: Maximum wall-clock time for a single execution.
    """

    model_name: str = "gpt-4"
    temperature: float = 0.0
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    timeout_seconds: float = 120.0

    model_config = {"env_prefix": "AGENT_"}
