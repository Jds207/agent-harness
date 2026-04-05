"""InvariantValidator – enforce business rules on agent outputs.

Why this exists:
    Pydantic validates *structure*; invariants validate *semantics*.
    For example, "line-item totals must sum to the invoice total" is an
    invariant, not a schema constraint.  This class lets callers register
    arbitrary predicates that are checked after schema validation.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from harness.utils.exceptions import HarnessValidationError


class InvariantValidator:
    """Runs a set of named business-rule checks against an output.

    Why this exists:
        Schema validation alone is insufficient.  Business invariants
        (balances, cross-field constraints, domain rules) need a
        composable, inspectable mechanism.

    Example::

        validator = InvariantValidator()
        validator.add_rule("totals_balance", lambda out: out.total == sum(out.items))
        validator.check(output)  # raises HarnessValidationError on failure
    """

    def __init__(self) -> None:
        self._rules: list[tuple[str, Callable[[Any], bool]]] = []

    def add_rule(self, name: str, predicate: Callable[[Any], bool]) -> None:
        """Register a named invariant predicate.

        Args:
            name: Human-readable rule name (used in error messages).
            predicate: A callable that returns ``True`` if the invariant holds.
        """
        self._rules.append((name, predicate))

    def check(self, output: Any) -> None:
        """Run all registered rules against ``output``.

        Args:
            output: The value to validate.

        Raises:
            HarnessValidationError: If any rule returns ``False``.
        """
        violations: list[str] = []
        for name, predicate in self._rules:
            try:
                if not predicate(output):
                    violations.append(name)
            except Exception as exc:
                violations.append(f"{name} (raised {type(exc).__name__}: {exc})")

        if violations:
            raise HarnessValidationError(
                f"Invariant violations: {', '.join(violations)}",
                violations=violations,
            )
