"""Example summarizer agent with full telemetry integration.

Run with:
    python -m examples.summarizer

This starts a Prometheus /metrics server on port 8000 and sends
OTLP traces to localhost:4317 (the OTel Collector).
"""

from __future__ import annotations

import time
from typing import Any

from harness.base import AgentConfig, BaseAgent
from harness.observability.logging import get_logger, setup_logging
from harness.schemas.base import BaseOutputSchema
from telemetry.metrics import MetricsCollector
from telemetry.tracing import TracingProvider

logger = get_logger()


# ── Output schema ────────────────────────────────────────────────────

class SummaryOutput(BaseOutputSchema):
    """Output produced by the summarizer agent."""

    summary: str
    confidence: float


# ── Agent ─────────────────────────────────────────────────────────────

class SummarizerAgent(BaseAgent[SummaryOutput]):
    """A toy summarizer agent that demonstrates harness + telemetry.

    In a real agent this would call an LLM; here it returns a
    hard-coded summary to exercise the full instrumentation pipeline.
    """

    def __init__(
        self,
        config: AgentConfig,
        metrics: MetricsCollector,
        tracing: TracingProvider,
    ) -> None:
        super().__init__(config)
        self._metrics = metrics
        self._tracing = tracing

    def _execute(self, input_data: dict[str, Any]) -> SummaryOutput:
        with self._tracing.start_span(
            "summarizer.execute",
            attributes={"agent": "summarizer", "input_length": len(str(input_data))},
        ):
            # Simulate LLM latency
            time.sleep(0.05)
            return SummaryOutput(
                summary=f"Summary of: {input_data.get('document', '')[:80]}",
                confidence=0.95,
                trace_id=self._trace_id,
            )

    def run(self, input_data: dict[str, Any]) -> SummaryOutput:
        """Override run to add metrics around the base implementation."""
        start = time.monotonic()
        success = False
        try:
            result = super().run(input_data)
            success = True
            self._metrics.record_validation(agent="summarizer", valid=True)
            return result
        except Exception:
            self._metrics.record_validation(agent="summarizer", valid=False)
            raise
        finally:
            duration = time.monotonic() - start
            self._metrics.record_run(
                agent="summarizer",
                success=success,
                duration=duration,
            )


# ── Entrypoint ────────────────────────────────────────────────────────

def main() -> None:
    setup_logging(json=True, level="INFO")

    # Telemetry
    metrics = MetricsCollector()
    metrics.start_server(port=8000)
    logger.info("metrics_server_started", port=8000)

    tracing = TracingProvider(service_name="summarizer-agent")
    tracing.configure(otlp_endpoint="http://localhost:4317")
    logger.info("tracing_configured", endpoint="http://localhost:4317")

    # Agent
    config = AgentConfig(model_name="gpt-4", temperature=0.0, max_retries=3)
    agent = SummarizerAgent(config=config, metrics=metrics, tracing=tracing)

    # Run a few demo invocations
    for i in range(5):
        result = agent.run({"document": f"Document #{i}: Lorem ipsum dolor sit amet..."})
        logger.info(
            "run_complete",
            run=i,
            summary=result.summary,
            confidence=result.confidence,
            trace_id=result.trace_id,
        )

    logger.info("demo_finished", total_runs=5)
    logger.info(
        "metrics_available",
        url="http://localhost:8000/metrics",
        hint="curl http://localhost:8000/metrics",
    )

    # Keep the process alive so Prometheus can scrape
    logger.info("keeping_alive", hint="Press Ctrl+C to stop")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        tracing.shutdown()
        logger.info("shutdown")


if __name__ == "__main__":
    main()
