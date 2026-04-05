"""Enhanced metrics collection with AI-specific measurements."""

from __future__ import annotations

from typing import Optional

from prometheus_client import Counter, Gauge, Histogram

from telemetry.metrics import MetricsCollector


class EnhancedMetricsCollector(MetricsCollector):
    """Extended metrics with AI-specific measurements."""

    def __init__(self, namespace: str = "agent") -> None:
        super().__init__(namespace)

        # AI-specific metrics
        self.tokens_total = Counter(
            f"{namespace}_tokens_total",
            "Total tokens used by agent",
            ["agent", "model", "type"],  # type: prompt, completion, total
        )

        self.cost_dollars = Counter(
            f"{namespace}_cost_dollars",
            "Total cost in dollars for agent runs",
            ["agent", "model"],
        )

        self.model_temperature = Gauge(
            f"{namespace}_model_temperature",
            "Current temperature setting for model",
            ["agent", "model"],
        )

        self.active_requests = Gauge(
            f"{namespace}_active_requests",
            "Number of currently active agent requests",
            ["agent"],
        )

        self.prompt_length_chars = Histogram(
            f"{namespace}_prompt_length_chars",
            "Input prompt length in characters",
            ["agent"],
            buckets=(100, 500, 1000, 2000, 5000, 10000, 25000, 50000),
        )

    def record_run(
        self,
        *,
        agent: str,
        success: bool,
        duration: float,
        model: Optional[str] = None,
        tokens_used: Optional[dict[str, int]] = None,
        cost: Optional[float] = None,
        temperature: Optional[float] = None,
        prompt_length: Optional[int] = None,
    ) -> None:
        """Record a completed agent run with enhanced metrics."""
        super().record_run(agent=agent, success=success, duration=duration)

        model = model or "unknown"

        if tokens_used:
            for token_type, count in tokens_used.items():
                self.tokens_total.labels(
                    agent=agent, model=model, type=token_type
                ).inc(count)

        if cost is not None:
            self.cost_dollars.labels(agent=agent, model=model).inc(cost)

        if temperature is not None:
            self.model_temperature.labels(agent=agent, model=model).set(temperature)

        if prompt_length is not None:
            self.prompt_length_chars.labels(agent=agent).observe(prompt_length)

    def increment_active_requests(self, *, agent: str) -> None:
        """Increment active request counter."""
        self.active_requests.labels(agent=agent).inc()

    def decrement_active_requests(self, *, agent: str) -> None:
        """Decrement active request counter."""
        self.active_requests.labels(agent=agent).dec()


# Global enhanced instance
enhanced_metrics = EnhancedMetricsCollector()