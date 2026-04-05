# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-04-05

### Added
- `BaseAgent` abstract class with `run()`, `validate()`, and `get_trace()` methods.
- `AgentConfig` pydantic-settings model for agent configuration.
- `BaseOutputSchema` generic Pydantic output model.
- `InvariantValidator` for enforcing business rules on outputs.
- `RetryWithFallback` reliability wrapper using tenacity.
- `CircuitBreaker` for protecting downstream calls.
- `StepValidator` with typed `ValidationError` on failure.
- Structured logging via structlog with trace_id, step_name, success, duration.
- `FailureLogger` for capturing full failure context.
- `LessonsLearnedStore` (in-memory) for accumulating failure patterns.
- Full test suite covering happy-path and failure-path scenarios.
