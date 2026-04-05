"""Tests for harness.schemas – BaseOutputSchema and InvariantValidator."""

from __future__ import annotations

import pytest

from harness.schemas.base import BaseOutputSchema
from harness.schemas.invariants import InvariantValidator
from harness.utils.exceptions import HarnessValidationError


class InvoiceOutput(BaseOutputSchema):
    total: float
    line_items: list[float]


class TestBaseOutputSchema:
    def test_defaults_populated(self) -> None:
        out = BaseOutputSchema()
        assert out.created_at is not None
        assert out.metadata == {}

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(Exception):  # ValidationError
            BaseOutputSchema(unknown_field="bad")  # type: ignore[call-arg]


class TestInvariantValidator:
    def test_passing_invariant(self) -> None:
        v = InvariantValidator()
        v.add_rule("totals_balance", lambda o: o.total == sum(o.line_items))
        output = InvoiceOutput(total=30.0, line_items=[10.0, 20.0])
        v.check(output)  # should not raise

    def test_failing_invariant(self) -> None:
        v = InvariantValidator()
        v.add_rule("totals_balance", lambda o: o.total == sum(o.line_items))
        output = InvoiceOutput(total=99.0, line_items=[10.0, 20.0])
        with pytest.raises(HarnessValidationError, match="totals_balance"):
            v.check(output)

    def test_multiple_violations(self) -> None:
        v = InvariantValidator()
        v.add_rule("rule_a", lambda _: False)
        v.add_rule("rule_b", lambda _: False)
        with pytest.raises(HarnessValidationError) as exc_info:
            v.check(InvoiceOutput(total=0, line_items=[]))
        assert len(exc_info.value.violations) == 2

    def test_predicate_exception_captured(self) -> None:
        v = InvariantValidator()
        v.add_rule("exploder", lambda _: 1 / 0)  # type: ignore[return-value]
        with pytest.raises(HarnessValidationError, match="ZeroDivisionError"):
            v.check(InvoiceOutput(total=0, line_items=[]))
