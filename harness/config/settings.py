"""HarnessSettings – global harness configuration.

Why this exists:
    Agent-level config (``AgentConfig``) handles per-agent knobs.  This
    module handles *harness*-level settings: log format, failure store
    backend, circuit-breaker defaults, etc.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings


class HarnessSettings(BaseSettings):
    """Global settings for the reliable-agent-harness.

    Why this exists:
        Separates infrastructure config from agent config.  Loaded from
        env vars prefixed with ``HARNESS_``.

    Attributes:
        log_json: Whether to emit JSON-formatted logs.
        log_level: Minimum log level.
        default_max_retries: Default retry budget for RetryWithFallback.
        default_circuit_failure_threshold: Consecutive failures to trip a circuit.
        default_circuit_recovery_timeout: Seconds before a tripped circuit
            transitions to half-open.
    """

    log_json: bool = True
    log_level: str = "INFO"
    default_max_retries: int = 3
    default_circuit_failure_threshold: int = 5
    default_circuit_recovery_timeout: float = 30.0

    model_config = {"env_prefix": "HARNESS_"}
