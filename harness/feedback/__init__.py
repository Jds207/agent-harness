"""Feedback – failure logging and lessons-learned accumulation.

Why this exists:
    Failures are first-class data.  This module captures the full context
    of every failure and accumulates patterns so that future runs (and
    future developers) can learn from past mistakes.
"""

from .failure_logger import FailureLogger
from .lessons_store import LessonsLearnedStore

__all__ = ["FailureLogger", "LessonsLearnedStore"]

__all__ = ["FailureLogger", "LessonsLearnedStore"]
