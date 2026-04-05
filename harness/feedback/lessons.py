"""LessonsLearnedStore – accumulate and query failure patterns.

Why this exists:
    Individual failures are useful for debugging; *patterns* across
    failures are useful for improving the system.  This store aggregates
    lessons (human- or AI-generated summaries) and allows querying by
    tag so that agents can consult past lessons before retrying.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class Lesson(BaseModel):
    """A single lesson derived from one or more failures.

    Attributes:
        summary: Human-readable description of what was learned.
        tags: Searchable labels (e.g. ``["timeout", "openai"]``).
        source_trace_ids: Trace IDs of runs that contributed to this lesson.
        created_at: UTC timestamp.
    """

    summary: str
    tags: list[str] = []
    source_trace_ids: list[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = {}


class LessonsLearnedStore:
    """In-memory store for lessons learned from failures.

    Why this exists:
        Provides a feedback loop so that the harness (or humans reviewing
        logs) can record insights and later query them.  v0.1 is in-memory;
        a future version will back this with a vector database for
        semantic retrieval.
    """

    def __init__(self) -> None:
        self._lessons: list[Lesson] = []

    def add(
        self,
        summary: str,
        *,
        tags: list[str] | None = None,
        source_trace_ids: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Lesson:
        """Record a new lesson.

        Args:
            summary: What was learned.
            tags: Searchable labels.
            source_trace_ids: Traces that contributed to this lesson.
            metadata: Arbitrary extra context.

        Returns:
            The created ``Lesson``.
        """
        lesson = Lesson(
            summary=summary,
            tags=tags or [],
            source_trace_ids=source_trace_ids or [],
            metadata=metadata or {},
        )
        self._lessons.append(lesson)
        return lesson

    def search(self, tag: str) -> list[Lesson]:
        """Return all lessons matching a given tag.

        Args:
            tag: The tag to filter on (case-insensitive).

        Returns:
            Matching lessons, newest first.
        """
        tag_lower = tag.lower()
        results = [l for l in self._lessons if tag_lower in [t.lower() for t in l.tags]]
        return sorted(results, key=lambda l: l.created_at, reverse=True)

    @property
    def all_lessons(self) -> list[Lesson]:
        """All stored lessons."""
        return list(self._lessons)

    def clear(self) -> None:
        """Remove all stored lessons."""
        self._lessons.clear()
