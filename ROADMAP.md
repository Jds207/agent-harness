# Roadmap

This document outlines the planned evolution of the `reliable-agent-harness` from MVP to full production reliability platform.

## v0.1.0 — Foundation (✅ Released 2026-04-05)
- BaseAgent + AgentConfig
- Schemas & InvariantValidator
- RetryWithFallback + CircuitBreaker
- Structured logging + FailureLogger
- In-memory LessonsLearnedStore

## v0.2.0 — Enhanced Production Features (✅ Released 2026-04-05)
- **Async Support**: AsyncBaseAgent and AsyncAgentPool for concurrent execution
- **Enhanced Metrics**: Token usage, cost tracking, model parameters, active requests
- **CLI Tools**: Testing, benchmarking, and validation commands
- **Health Checks**: HTTP health endpoints with database/API monitoring
- **Alerting System**: Email and Slack notifications for metric thresholds
- **Multi-Step Workflows**: BaseWorkflow + LangGraph integration (planned)
- **WorkflowStep**: Pre/post validation with cross-step invariants (planned)
- **State Persistence**: Workflow state management (planned)

## v0.3.0 — Self-Improving System
- Persistent LessonsLearnedStore (SQLite/vector)
- Automated lesson injection
- LLM-as-Judge evaluation
- Human-in-the-loop escalation

## v1.0.0 — Production Ready
- Multi-LLM provider support
- Built-in evaluation harness
- OpenTelemetry / LangSmith exporter
- Docker + CI/CD examples

## Portfolio Integration Plan
- Project 1 (Invoice Extractor) → uses v0.1.0
- Project 2 (Research Agent) → uses v0.2.0
- Project 3 (Lead-to-CRM) → uses v0.3.0
- Project 4 (Self-Improving) → uses v1.0.0

**Goal**: Each version must measurably increase reliability and reduce human intervention.