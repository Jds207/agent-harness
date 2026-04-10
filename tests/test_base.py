"""Tests for harness.base – BaseAgent and AgentConfig."""

from __future__ import annotations

from typing import Any

import pytest

from harness.base.agent import BaseAgent
from harness.base.config import AgentConfig
from harness.schemas.base import AgentInput, AgentOutput


# ── Fixtures / helpers ────────────────────────────────────────────────

class SampleOutput(AgentOutput):
    answer: str


class GoodAgent(BaseAgent):
    """An agent that always succeeds."""

    def _execute(self, input_obj: AgentInput) -> dict[str, Any]:
        return {"result": input_obj.data.get("q", "42"), "answer": input_obj.data.get("q", "42")}


class BadAgent(BaseAgent):
    """An agent that always raises."""

    def _execute(self, input_obj: AgentInput) -> dict[str, Any]:
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
        agent = GoodAgent(config=AgentConfig(name="test_agent"))
        result = agent.process({"q": "hello"})
        assert result["result"] == "hello"
        assert result["answer"] == "hello"

    def test_failure_propagation(self) -> None:
        agent = BadAgent(config=AgentConfig(name="test_agent"))
        with pytest.raises(RuntimeError, match="boom"):
            agent.process({"dummy": "data"})