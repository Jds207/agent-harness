"""AgentConfig – typed configuration for every agent.

Why this exists:
    Centralises all tuneable knobs (model name, temperature, retry budget)
    into a single validated object so that misconfiguration is caught at
    startup, not mid-run.
"""

from pydantic import BaseModel, Field
from typing import Optional


class AgentConfig(BaseModel):
    """Configuration for a harness-managed agent.

    Why this design: AgentConfig uses Pydantic to ensure all configuration is validated at creation time, preventing runtime errors from invalid config. It provides a single source of truth for agent settings with sensible defaults.
    """

    name: str = Field(default="default_agent", description="Name of the agent")
    version: str = Field(default="0.1.0", description="Version of the agent")
    max_retries: int = Field(default=3, description="Maximum number of retries")
    timeout: float = Field(default=30.0, description="Timeout in seconds")
    log_level: str = Field(default="INFO", description="Logging level")
    model_name: str = Field(default="gpt-4", description="LLM model identifier")
    temperature: float = Field(default=0.0, description="Sampling temperature for the LLM")
