"""Tests for harness.base – BaseAgent and AgentConfig."""

from __future__ import annotations

from typing import Any

import pytest

from harness.base.agent import BaseAgent, TraceRecord
from harness.base.config import AgentConfig
from harness.schemas.base import BaseOutputSchema


# ── Fixtures / helpers ────────────────────────────────────────────────

class SampleOutput(BaseOutputSchema):
    answer: str


class GoodAgent(BaseAgent[SampleOutput]):
    """An agent that always succeeds."""

    def _execute(self, input_data: dict[str, Any]) -> SampleOutput:
        return SampleOutput(answer=input_data.get("q", "42"))


class BadAgent(BaseAgent[SampleOutput]):
    """An agent that always raises."""

    def _execute(self, input_data: dict[str, Any]) -> SampleOutput:
        raise RuntimeError("boom")


# ── Tests ─────────────────────────────────────────────────────────────

class TestAgentConfig:
    def test_defaults(self) -> None:
        cfg = AgentConfig()
        assert cfg.model_name == "gpt-4"
        assert cfg.temperature == 0.0
        assert cfg.max_retries == 3

    def test_override(self) -> None:
        cfg = AgentConfig(model_name="claude-3", temperature=0.7, max_retries=5)
        assert cfg.model_name == "claude-3"
        assert cfg.temperature == 0.7
        assert cfg.max_retries == 5


class TestBaseAgent:
    def test_happy_path(self) -> None:
        agent = GoodAgent(config=AgentConfig())
        result = agent.run({"q": "hello"})
        assert result.answer == "hello"

    def test_trace_recorded_on_success(self) -> None:
        agent = GoodAgent(config=AgentConfig())
        agent.run({"q": "test"})
        trace = agent.get_trace()
        assert len(trace) == 2
        assert trace[0].step_name == "execute"
        assert trace[0].success is True
        assert trace[1].step_name == "validate"
        assert trace[1].success is True

    def test_trace_recorded_on_failure(self) -> None:
        agent = BadAgent(config=AgentConfig())
        with pytest.raises(RuntimeError, match="boom"):
            agent.run({})
        trace = agent.get_trace()
        assert len(trace) == 1
        assert trace[0].success is False
        assert trace[0].error == "boom"

    def test_trace_record_model(self) -> None:
        record = TraceRecord(
            trace_id="abc",
            step_name="test",
            duration_seconds=0.5,
            success=True,
        )
        assert record.trace_id == "abc"
        assert record.error is None
