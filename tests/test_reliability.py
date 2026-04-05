"""Tests for harness.reliability – RetryWithFallback, CircuitBreaker, StepValidator."""

from __future__ import annotations

import pytest

from harness.reliability.circuit_breaker import CircuitBreaker
from harness.reliability.retry import RetryWithFallback
from harness.reliability.validator import StepValidator
from harness.schemas.base import BaseOutputSchema
from harness.schemas.invariants import InvariantValidator
from harness.utils.exceptions import (
    CircuitOpenError,
    HarnessValidationError,
    RetryExhaustedError,
)


# ── RetryWithFallback ─────────────────────────────────────────────────

class TestRetryWithFallback:
    def test_succeeds_without_retry(self) -> None:
        wrapper = RetryWithFallback(max_retries=3, base_delay=0)
        fn = wrapper.wrap(lambda: "ok")
        assert fn() == "ok"

    def test_retries_then_succeeds(self) -> None:
        call_count = 0

        def flaky() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("transient")
            return "recovered"

        wrapper = RetryWithFallback(max_retries=5, base_delay=0)
        fn = wrapper.wrap(flaky)
        assert fn() == "recovered"
        assert call_count == 3

    def test_exhausted_without_fallback(self) -> None:
        def always_fail() -> None:
            raise ValueError("always")

        wrapper = RetryWithFallback(max_retries=2, base_delay=0)
        fn = wrapper.wrap(always_fail)
        with pytest.raises(RetryExhaustedError):
            fn()

    def test_fallback_invoked_on_exhaustion(self) -> None:
        def always_fail() -> None:
            raise ValueError("always")

        def fallback() -> str:
            return "fallback_result"

        wrapper = RetryWithFallback(max_retries=2, base_delay=0, fallback=fallback)
        fn = wrapper.wrap(always_fail)
        assert fn() == "fallback_result"


# ── CircuitBreaker ────────────────────────────────────────────────────

class TestCircuitBreaker:
    def test_closed_allows_calls(self) -> None:
        cb = CircuitBreaker("test", failure_threshold=3)
        result = cb.call(lambda: "ok")
        assert result == "ok"
        assert cb.state == "closed"

    def test_opens_after_threshold(self) -> None:
        cb = CircuitBreaker("test", failure_threshold=2)
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        assert cb.state == "open"

    def test_rejects_when_open(self) -> None:
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=9999)
        with pytest.raises(ValueError):
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        with pytest.raises(CircuitOpenError):
            cb.call(lambda: "should not run")

    def test_success_resets_count(self) -> None:
        cb = CircuitBreaker("test", failure_threshold=3)
        # One failure, then a success – counter should reset
        with pytest.raises(ValueError):
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        cb.call(lambda: "ok")
        assert cb._failure_count == 0


# ── StepValidator ─────────────────────────────────────────────────────

class SampleModel(BaseOutputSchema):
    value: int


class TestStepValidator:
    def test_valid_data(self) -> None:
        sv = StepValidator()
        result = sv.validate(SampleModel, {"value": 42})
        assert result.value == 42

    def test_invalid_schema(self) -> None:
        sv = StepValidator()
        with pytest.raises(HarnessValidationError, match="Schema validation failed"):
            sv.validate(SampleModel, {"value": "not_an_int"})

    def test_invariant_checked(self) -> None:
        iv = InvariantValidator()
        iv.add_rule("must_be_positive", lambda o: o.value > 0)
        sv = StepValidator(invariant_validator=iv)
        with pytest.raises(HarnessValidationError, match="must_be_positive"):
            sv.validate(SampleModel, {"value": -1})
