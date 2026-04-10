"""LessonsLearnedStore – accumulate patterns from failures for continuous improvement.

Why this exists:
    Failures are expensive, but they're also the best teacher.  This store
    accumulates failure patterns and suggests improvements, turning
    reactive debugging into proactive hardening.
"""

from typing import Dict, List, Any
from datetime import datetime
import json
import os


class LessonsLearnedStore:
    """Store for lessons learned from failures.

    Why this design: LessonsLearnedStore creates a feedback loop by storing patterns from failures, enabling continuous improvement and preventing recurring issues. It categorizes lessons and persists them for long-term learning.

    Args:
        store_file: Path to the JSON file for storing lessons
    """

    def __init__(self, store_file: str = "lessons.json") -> None:
        """Initialize lessons store.

        Args:
            store_file: File path for storing lessons data
        """
        self.store_file = store_file
        self.lessons: Dict[str, List[Dict[str, Any]]] = self._load_lessons()

    def _load_lessons(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load lessons from storage file.

        Returns:
            Dictionary of lessons by category
        """
        if not os.path.exists(self.store_file):
            return {}

        try:
            with open(self.store_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            # If file is corrupted, start fresh
            print(f"Warning: Could not load lessons file {self.store_file}: {e}")
            return {}

    def _save_lessons(self) -> None:
        """Save lessons to storage file."""
        try:
            with open(self.store_file, "w", encoding="utf-8") as f:
                json.dump(self.lessons, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Warning: Could not save lessons file {self.store_file}: {e}")

    def store_lesson(self, error: Exception, category: str) -> None:
        """Store a lesson from a failure.

        Args:
            error: The exception that occurred
            category: Category for the lesson (e.g., "api_failure", "validation_error")
        """
        lesson = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "error_module": error.__class__.__module__,
            "category": category
        }

        if category not in self.lessons:
            self.lessons[category] = []

        self.lessons[category].append(lesson)

        # Keep only last 100 lessons per category to prevent unbounded growth
        if len(self.lessons[category]) > 100:
            self.lessons[category] = self.lessons[category][-100:]

        self._save_lessons()

    def get_lessons_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all lessons for a specific category.

        Args:
            category: The category to retrieve lessons for

        Returns:
            List of lessons for the category
        """
        return self.lessons.get(category, [])

    def get_all_categories(self) -> List[str]:
        """Get all lesson categories.

        Returns:
            List of all categories that have lessons
        """
        return list(self.lessons.keys())