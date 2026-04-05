"""Config – application-level settings management.

Why this exists:
    Provides a single entry-point for loading and validating harness-wide
    configuration from environment variables, .env files, or constructor
    kwargs via pydantic-settings.
"""

from harness.config.settings import HarnessSettings

__all__ = ["HarnessSettings"]
