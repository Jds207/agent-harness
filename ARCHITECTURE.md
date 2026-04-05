# What Was Built & How It Works

This document explains the architecture, design decisions, and component breakdown of the **reliable-agent-harness** v0.1.0.

---

## Purpose

The harness is a reusable Python package that provides production-grade infrastructure for AI agents. Rather than every agent project re-implementing retry logic, validation, logging, and error handling from scratch, they depend on this package and inherit all of it for free.

The core philosophy is **systems engineering over prompt engineering**: correctness is enforced by schemas and invariants at every step, failures are treated as first-class data, and every component is observable.

---

## Project Structure

```
reliable-agent-harness/
├── harness/
│   ├── __init__.py              # Package root, exposes __version__
│   ├── base/                    # BaseAgent + AgentConfig
│   │   ├── agent.py             # Abstract agent with run → validate → trace contract
│   │   └── config.py            # Pydantic-settings for agent configuration
│   ├── schemas/                 # Output validation
│   │   ├── base.py              # BaseOutputSchema (trace_id, timestamp, metadata)
│   │   └── invariants.py        # InvariantValidator for business-rule checks
│   ├── reliability/             # Failure handling
│   │   ├── retry.py             # RetryWithFallback (tenacity + fallback callable)
│   │   ├── circuit_breaker.py   # CircuitBreaker (closed → open → half-open)
│   │   └── validator.py         # StepValidator (schema + invariant in one call)
│   ├── observability/           # Logging & tracing
│   │   └── logging.py           # Structured logging via structlog
│   ├── feedback/                # Learning from failures
│   │   ├── failure_logger.py    # FailureLogger (full-context failure records)
│   │   └── lessons.py           # LessonsLearnedStore (tag-based lessons)
│   ├── config/                  # Harness-wide settings
│   │   └── settings.py          # HarnessSettings (log format, defaults)
│   ├── utils/                   # Shared utilities
│   │   └── exceptions.py        # Typed exception hierarchy
│   └── workflow/                # Reserved for v0.2 (multi-step pipelines)
├── tests/                       # 30 tests (happy-path + failure-path)
│   ├── test_base.py
│   ├── test_schemas.py
│   ├── test_reliability.py
│   └── test_feedback.py
├── pyproject.toml               # Package metadata, deps, tool config
├── README.md
├── CHANGELOG.md
└── LICENSE
```

---

## Component Deep-Dive

### 1. Base Layer (`harness/base/`)

**BaseAgent** is the abstract class that every agent must subclass. It enforces a strict contract:

1. `run(input_data)` → calls `_execute()` (your logic), then `validate()` (checks).
2. Every step is timed and recorded as a `TraceRecord` with trace_id, duration, success/error.
3. The full trace is retrievable via `get_trace()`.

Subclasses only implement `_execute()`. The harness handles everything around it.

**AgentConfig** uses pydantic-settings to load configuration from environment variables (prefixed `AGENT_`), `.env` files, or constructor kwargs. Fields include model name, temperature, retry budget, and timeout.

### 2. Schema Layer (`harness/schemas/`)

**BaseOutputSchema** is the Pydantic model that all agent outputs extend. It enforces:
- A `trace_id` linking the output to its execution trace.
- A `created_at` UTC timestamp for auditability.
- `extra = "forbid"` to prevent silent field typos.

**InvariantValidator** handles semantic validation that Pydantic can't express — business rules like "line items must sum to the total". You register named predicates, then call `check(output)`. Any failures raise `HarnessValidationError` with the list of violated rule names.

### 3. Reliability Layer (`harness/reliability/`)

**RetryWithFallback** wraps any callable with:
- Tenacity-based retry with exponential back-off + jitter.
- A configurable attempt budget.
- An optional fallback callable invoked when all retries are exhausted (e.g., switch to a cheaper model).
- Raises `RetryExhaustedError` (typed) if everything fails.

**CircuitBreaker** implements the classic closed → open → half-open pattern:
- Tracks consecutive failures against a threshold.
- When open, immediately rejects calls with `CircuitOpenError` (no wasted latency).
- After a recovery timeout, transitions to half-open and allows a probe call.
- A single success resets the circuit to closed.

**StepValidator** combines Pydantic schema validation and invariant checking into one call, useful for validating intermediate outputs between pipeline steps.

### 4. Observability Layer (`harness/observability/`)

Built on **structlog**, configured once via `setup_logging()`:
- Every log event is machine-parseable JSON (or console-formatted for dev).
- Automatic fields: timestamp (ISO), log level.
- Agent steps automatically log: trace_id, step_name, duration, success, error.

### 5. Feedback Layer (`harness/feedback/`)

**FailureLogger** captures the full context of every failure:
- Error type and message.
- Trace ID, step name, input data, config snapshot, partial output.
- All stored as queryable `FailureRecord` Pydantic models.

**LessonsLearnedStore** accumulates human- or AI-generated lessons derived from failures:
- Each lesson has a summary, tags, source trace IDs, and metadata.
- Searchable by tag (case-insensitive).
- v0.1 is in-memory; future versions will back this with a vector database.

### 6. Error Hierarchy (`harness/utils/exceptions.py`)

All errors are typed and subclass `HarnessError`:

| Exception | When it's raised |
|---|---|
| `HarnessValidationError` | Schema or invariant check fails |
| `RetryExhaustedError` | All retry attempts (+ fallback) exhausted |
| `CircuitOpenError` | Call rejected by an open circuit breaker |

This lets callers write precise exception handling instead of catching bare `Exception`.

---

## Design Decisions

| Decision | Rationale |
|---|---|
| Pydantic v2 for all models | Runtime validation + JSON schema generation + excellent error messages |
| pydantic-settings for config | Env-var loading with type safety; no manual parsing |
| structlog for logging | Structured, machine-parseable events; composable processors |
| tenacity for retry | Battle-tested, highly configurable retry library |
| Composition over inheritance | After `BaseAgent`, everything is pluggable and composable — no deep class trees |
| Typed exceptions | Every failure path is distinguishable; enables precise retry/fallback logic |
| `from __future__ import annotations` | Enables modern type syntax on Python 3.11+ without runtime evaluation |

---

## Test Coverage

30 tests covering every public component with both happy-path and failure-path scenarios:

- **test_base.py** (6 tests): AgentConfig defaults/overrides, BaseAgent run/trace on success and failure.
- **test_schemas.py** (5 tests): BaseOutputSchema defaults, extra-field rejection, InvariantValidator pass/fail/multi-violation/exception.
- **test_reliability.py** (8 tests): RetryWithFallback success/retry/exhaustion/fallback, CircuitBreaker states, StepValidator schema/invariant.
- **test_feedback.py** (7 tests): FailureLogger context capture/accumulation/clear, LessonsLearnedStore add/search/case-insensitive/clear.

---

## What's Next (v0.2 Roadmap)

- **Workflow module**: LangGraph-style composable step pipelines.
- **Persistent feedback store**: Swap in-memory stores for SQLite/vector DB.
- **Async support**: `async run()` and async retry for async agents.
- **Metrics export**: OpenTelemetry spans and counters.
- **Pre-built validators**: Common invariant checks (JSON structure, token limits, format compliance).
