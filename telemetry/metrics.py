"""Prometheus metrics helpers for the agent harness.

Why this exists:
    Every agent needs counters (runs, successes, failures, validation
    errors) and histograms (latency) to drive SLO dashboards.  This
    module defines those metrics once and exposes a ``/metrics`` HTTP
    endpoint via ``prometheus_client`` so Prometheus can scrape them.

Typical usage::

    from telemetry.metrics import MetricsCollector

    mc = MetricsCollector()
    mc.start_server(port=8000)         # serves /metrics

    mc.record_run(agent="summarizer", success=True, duration=1.23)
    mc.record_validation(agent="summarizer", valid=True)
"""

from __future__ import annotations

from prometheus_client import (
    Counter,
    Histogram,
    start_http_server,
)


class MetricsCollector:
    """Thin wrapper around prometheus_client instruments.

    Why this exists:
        Prevents every agent from defining its own ad-hoc counters.
        One shared set of well-named metrics = consistent dashboards.

    Attributes:
        runs_total: Counter of agent runs by agent name and outcome.
        run_duration: Histogram of run duration in seconds.
        validation_total: Counter of validation outcomes.
    """

    def __init__(self, namespace: str = "agent") -> None:
        self.runs_total = Counter(
            f"{namespace}_runs_total",
            "Total agent runs",
            ["agent", "status"],
        )
        self.run_duration = Histogram(
            f"{namespace}_run_duration_seconds",
            "Agent run duration in seconds",
            ["agent"],
            buckets=(0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60, 120),
        )
        self.validation_total = Counter(
            f"{namespace}_validation_total",
            "Output validation outcomes",
            ["agent", "valid"],
        )

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def start_server(self, port: int = 8000) -> None:
        """Start the Prometheus metrics HTTP server on ``port``.

        Args:
            port: TCP port for the ``/metrics`` endpoint.
        """
        start_http_server(port)

    def record_run(
        self,
        *,
        agent: str,
        success: bool,
        duration: float,
    ) -> None:
        """Record a completed agent run.

        Args:
            agent: Agent name label.
            success: Whether the run succeeded.
            duration: Wall-clock seconds for the run.
        """
        status = "success" if success else "failure"
        self.runs_total.labels(agent=agent, status=status).inc()
        self.run_duration.labels(agent=agent).observe(duration)

    def record_validation(self, *, agent: str, valid: bool) -> None:
        """Record a validation outcome.

        Args:
            agent: Agent name label.
            valid: Whether the output passed validation.
        """
        self.validation_total.labels(agent=agent, valid=str(valid).lower()).inc()
