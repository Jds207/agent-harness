"""Feedback – failure logging and lessons-learned accumulation.

Why this exists:
    Failures are first-class data.  This module captures the full context
    of every failure and accumulates patterns so that future runs (and
    future developers) can learn from past mistakes.
"""

from harness.feedback.failure_logger import FailureLogger
from harness.feedback.lessons import LessonsLearnedStore

__all__ = ["FailureLogger", "LessonsLearnedStore"]
