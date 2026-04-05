# reliable-agent-harness

A reusable, versioned Python package that turns any AI agent into a reliable, production-grade system. Instead of each agent re-implementing retry loops, validation, logging, and error handling, they inherit battle-tested infrastructure from this harness and focus purely on domain logic.

## Installation

```bash
pip install git+https://github.com/your-org/reliable-agent-harness.git@v0.1.0
```

Or add to your `pyproject.toml`:

```toml
dependencies = [
    "reliable-agent-harness @ git+https://github.com/your-org/reliable-agent-harness.git@v0.1.0",
]
```

## Quickstart

```python
from typing import Any
from harness.base import BaseAgent, AgentConfig
from harness.schemas import BaseOutputSchema

# 1. Define your output schema
class SummaryOutput(BaseOutputSchema):
    summary: str
    confidence: float

# 2. Implement your agent
class SummarizerAgent(BaseAgent[SummaryOutput]):
    def _execute(self, input_data: dict[str, Any]) -> SummaryOutput:
        # Your LLM call / business logic here
        return SummaryOutput(
            summary="Key findings from the document...",
            confidence=0.92,
        )

# 3. Run it
agent = SummarizerAgent(config=AgentConfig(model_name="gpt-4", max_retries=3))
result = agent.run({"document": "..."})
print(result.summary)
print(agent.get_trace())  # Full execution trace
```

## How This Harness Makes Agents Reliable

| Layer | What it does | Component |
|---|---|---|
| **Validation** | Every output is validated against a Pydantic schema *and* business-rule invariants | `BaseOutputSchema`, `InvariantValidator`, `StepValidator` |
| **Retry + Fallback** | Transient failures are retried with exponential back-off; persistent failures fall back to an alternative | `RetryWithFallback` |
| **Circuit Breaker** | Unhealthy downstreams are short-circuited to prevent cascading failures | `CircuitBreaker` |
| **Observability** | Structured JSON logging with trace IDs, step names, durations, and error context | `setup_logging()`, `get_logger()` |
| **Feedback Loop** | Failures are logged with full context; patterns are accumulated as lessons learned | `FailureLogger`, `LessonsLearnedStore` |
| **Typed Errors** | Every failure is a typed exception (`HarnessValidationError`, `RetryExhaustedError`, `CircuitOpenError`) so callers can react precisely | `harness.utils.exceptions` |

## Version History

| Version | Date | Highlights |
|---|---|---|
| 0.1.0 | 2026-04-05 | MVP – BaseAgent, schemas, reliability, observability, feedback |

## Development

```bash
# Clone and install
git clone https://github.com/your-org/reliable-agent-harness.git
cd reliable-agent-harness
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,test]"

# Run tests
pytest tests/ -v

# Type check
mypy harness/
```

## License

MIT
