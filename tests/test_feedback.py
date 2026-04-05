"""Tests for harness.feedback – FailureLogger and LessonsLearnedStore."""

from __future__ import annotations

from harness.feedback.failure_logger import FailureLogger
from harness.feedback.lessons import LessonsLearnedStore


class TestFailureLogger:
    def test_log_captures_context(self) -> None:
        fl = FailureLogger()
        err = ValueError("test error")
        record = fl.log(
            error=err,
            trace_id="t1",
            step_name="parse",
            input_data={"raw": "bad"},
        )
        assert record.error_type == "ValueError"
        assert record.error_message == "test error"
        assert record.trace_id == "t1"
        assert record.step_name == "parse"
        assert record.input_data == {"raw": "bad"}

    def test_records_accumulate(self) -> None:
        fl = FailureLogger()
        fl.log(error=RuntimeError("a"))
        fl.log(error=RuntimeError("b"))
        assert len(fl.records) == 2

    def test_clear(self) -> None:
        fl = FailureLogger()
        fl.log(error=RuntimeError("a"))
        fl.clear()
        assert len(fl.records) == 0


class TestLessonsLearnedStore:
    def test_add_and_retrieve(self) -> None:
        store = LessonsLearnedStore()
        store.add("Rate limits need exponential back-off", tags=["rate-limit", "openai"])
        assert len(store.all_lessons) == 1

    def test_search_by_tag(self) -> None:
        store = LessonsLearnedStore()
        store.add("Lesson A", tags=["timeout"])
        store.add("Lesson B", tags=["rate-limit"])
        store.add("Lesson C", tags=["timeout", "openai"])
        results = store.search("timeout")
        assert len(results) == 2
        assert all("timeout" in [t.lower() for t in l.tags] for l in results)

    def test_search_case_insensitive(self) -> None:
        store = LessonsLearnedStore()
        store.add("Lesson", tags=["Timeout"])
        assert len(store.search("timeout")) == 1

    def test_clear(self) -> None:
        store = LessonsLearnedStore()
        store.add("Lesson", tags=["test"])
        store.clear()
        assert len(store.all_lessons) == 0
