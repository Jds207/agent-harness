"""Telemetry – Prometheus metrics and OpenTelemetry tracing helpers.

Why this exists:
    Separates instrumentation (metric counters, span creation) from the
    observability *infrastructure* (Prometheus server, OTel Collector,
    Grafana).  Agents import ``telemetry`` to emit signals; the
    ``observability/`` directory runs the backends that receive them.
"""

from telemetry.metrics import MetricsCollector
from telemetry.tracing import TracingProvider

__all__ = ["MetricsCollector", "TracingProvider"]
