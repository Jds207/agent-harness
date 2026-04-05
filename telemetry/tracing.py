"""OpenTelemetry tracing helpers for the agent harness.

Why this exists:
    Every agent run should produce a trace that can be viewed in Tempo
    or Jaeger.  This module configures the OTel SDK once and provides
    a simple ``start_span`` helper so agent code doesn't deal with
    boilerplate.

Typical usage::

    from telemetry.tracing import TracingProvider

    tp = TracingProvider(service_name="summarizer-agent")
    tp.configure(otlp_endpoint="http://localhost:4317")

    with tp.start_span("execute") as span:
        span.set_attribute("agent", "summarizer")
        result = do_work()
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Generator

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


class TracingProvider:
    """Configures and exposes an OpenTelemetry tracer.

    Why this exists:
        Centralises OTel SDK setup so each agent only calls
        ``configure()`` once at startup and then uses ``start_span()``
        for zero-boilerplate tracing.

    Args:
        service_name: The ``service.name`` resource attribute reported
            to the OTel Collector / Tempo.
    """

    def __init__(self, service_name: str = "agent-harness") -> None:
        self.service_name = service_name
        self._provider: TracerProvider | None = None
        self._tracer: trace.Tracer | None = None

    def configure(
        self,
        *,
        otlp_endpoint: str = "http://localhost:4317",
        insecure: bool = True,
    ) -> None:
        """Initialise the OTel TracerProvider and OTLP exporter.

        Args:
            otlp_endpoint: gRPC endpoint of the OTel Collector.
            insecure: Use insecure (non-TLS) connection.
        """
        resource = Resource.create({"service.name": self.service_name})
        self._provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=insecure)
        self._provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(self._provider)
        self._tracer = trace.get_tracer(self.service_name)

    @contextmanager
    def start_span(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> Generator[trace.Span, None, None]:
        """Context manager that creates and yields an OTel span.

        Args:
            name: Span operation name (e.g. ``"execute"``, ``"validate"``).
            attributes: Optional key-value pairs to attach to the span.

        Yields:
            The active ``Span``.  Automatically ended on context exit.
        """
        tracer = self._tracer or trace.get_tracer(self.service_name)
        with tracer.start_as_current_span(name) as span:
            if attributes:
                for k, v in attributes.items():
                    span.set_attribute(k, v)
            yield span

    def shutdown(self) -> None:
        """Flush pending spans and shut down the provider."""
        if self._provider is not None:
            self._provider.shutdown()
