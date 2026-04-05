"""Load generator – continuously runs the summarizer agent to populate dashboards.

Run with:
    python -m examples.load_generator

Sends a steady stream of agent runs (with occasional simulated failures)
so that Prometheus, Grafana, and Tempo have real data to display.
"""

from __future__ import annotations

import random
import time
from typing import Any

from harness.base import AgentConfig, BaseAgent
from harness.observability.logging import get_logger, setup_logging
from harness.schemas.base import BaseOutputSchema
from telemetry.metrics import MetricsCollector
from telemetry.tracing import TracingProvider


logger = get_logger()


class SummaryOutput(BaseOutputSchema):
    summary: str
    confidence: float


class LoadGenAgent(BaseAgent[SummaryOutput]):
    """Agent that sometimes fails to generate realistic metrics."""

    def __init__(
        self,
        config: AgentConfig,
        metrics: MetricsCollector,
        tracing: TracingProvider,
        failure_rate: float = 0.1,
    ) -> None:
        super().__init__(config)
        self._metrics = metrics
        self._tracing = tracing
        self._failure_rate = failure_rate

    def _execute(self, input_data: dict[str, Any]) -> SummaryOutput:
        with self._tracing.start_span(
            "summarizer.execute",
            attributes={"agent": "summarizer", "input_length": len(str(input_data))},
        ):
            # Simulate variable latency (50ms – 2s)
            latency = random.uniform(0.05, 2.0)
            time.sleep(latency)

            # Simulate occasional failures
            if random.random() < self._failure_rate:
                raise RuntimeError("Simulated LLM timeout")

            confidence = random.uniform(0.6, 0.99)
            return SummaryOutput(
                summary=f"Summary of: {input_data.get('document', '')[:60]}",
                confidence=round(confidence, 3),
                trace_id=self._trace_id,
            )

    def run(self, input_data: dict[str, Any]) -> SummaryOutput:
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


SAMPLE_DOCS = [
    "Quarterly earnings report showing 15% revenue growth across all segments",
    "Technical design document for the new microservices architecture",
    "Customer support ticket analysis revealing common pain points",
    "Research paper on transformer attention mechanisms and efficiency",
    "Product roadmap for Q3 2026 with key milestones and dependencies",
    "Security audit findings and remediation recommendations",
    "Marketing campaign performance metrics and ROI analysis",
    "Infrastructure cost optimization report for cloud services",
]


def main() -> None:
    setup_logging(json=True, level="INFO")

    # Reuse the already-running metrics server if port 8000 is taken
    metrics = MetricsCollector()
    try:
        metrics.start_server(port=8001)
        logger.info("metrics_server_started", port=8001, note="load generator metrics on 8001")
    except OSError:
        logger.info("metrics_server_skipped", note="port 8001 in use, using existing")

    tracing = TracingProvider(service_name="summarizer-agent")
    tracing.configure(otlp_endpoint="http://localhost:4317")

    config = AgentConfig(model_name="gpt-4", temperature=0.0, max_retries=3)
    agent = LoadGenAgent(config=config, metrics=metrics, tracing=tracing, failure_rate=0.1)

    run_count = 0
    success_count = 0
    failure_count = 0

    logger.info("load_generator_started", failure_rate=0.1, hint="Ctrl+C to stop")

    try:
        while True:
            doc = random.choice(SAMPLE_DOCS)
            run_count += 1
            try:
                result = agent.run({"document": doc})
                success_count += 1
                logger.info(
                    "run_ok",
                    run=run_count,
                    confidence=result.confidence,
                    trace_id=result.trace_id,
                )
            except Exception as exc:
                failure_count += 1
                logger.warning("run_failed", run=run_count, error=str(exc))

            # Reset trace for next run
            agent._trace = []
            import uuid
            agent._trace_id = uuid.uuid4().hex

            # Brief pause between runs (0.5s – 3s)
            time.sleep(random.uniform(0.5, 3.0))

            # Progress update every 10 runs
            if run_count % 10 == 0:
                logger.info(
                    "progress",
                    total=run_count,
                    successes=success_count,
                    failures=failure_count,
                    rate=f"{success_count/run_count*100:.1f}%",
                )

    except KeyboardInterrupt:
        logger.info(
            "load_generator_stopped",
            total=run_count,
            successes=success_count,
            failures=failure_count,
        )
        tracing.shutdown()


if __name__ == "__main__":
    main()
