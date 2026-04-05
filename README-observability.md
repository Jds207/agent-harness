# Observability Guide

How to run the full metrics → traces → dashboards stack locally for agent-harness development.

---

## Architecture

```
┌──────────────────┐      OTLP (gRPC :4317)      ┌──────────────────┐
│  Agent Process   │ ──────────────────────────▶  │  OTel Collector  │
│                  │                              └────────┬─────────┘
│  /metrics :8000  │                                       │
└────────┬─────────┘                                       │ OTLP
         │ scrape                                          ▼
         │                                        ┌──────────────────┐
         ▼                                        │      Tempo       │
┌──────────────────┐                              │  (trace store)   │
│   Prometheus     │                              └────────┬─────────┘
│   :9090          │                                       │
└────────┬─────────┘                                       │
         │                                                 │
         └──────────────────┐     ┌────────────────────────┘
                            ▼     ▼
                     ┌──────────────────┐
                     │     Grafana      │
                     │     :3000        │
                     └──────────────────┘
```

**Data flow:**
1. Your agent exposes Prometheus metrics on `:8000/metrics` via `prometheus_client`.
2. Your agent sends OTLP traces to the OTel Collector on `:4317`.
3. Prometheus scrapes `:8000` every 15s.
4. OTel Collector batches and forwards traces to Tempo.
5. Grafana queries both Prometheus (metrics) and Tempo (traces).

---

## Prerequisites

- Docker & Docker Compose
- Python 3.11+
- The harness installed in dev mode: `pip install -e ".[dev,test]"`

---

## Quick Start

### 1. Start the observability stack

```bash
cd observability
docker compose up -d
```

This starts:
| Service | URL | Purpose |
|---|---|---|
| Prometheus | http://localhost:9090 | Metric storage & queries |
| Grafana | http://localhost:3000 | Dashboards (admin/admin) |
| OTel Collector | localhost:4317 (gRPC) | Receives OTLP traces |
| Tempo | http://localhost:3200 | Trace storage |

### 2. Run the example agent

```bash
# From the repo root
python -m examples.summarizer
```

This will:
- Start a `/metrics` server on port 8000
- Send OTLP traces to localhost:4317
- Run 5 demo summarizations
- Stay alive for Prometheus scraping (Ctrl+C to stop)

### 3. Verify everything works

```bash
# Metrics endpoint
curl http://localhost:8000/metrics

# Prometheus targets (should show agent-harness as UP)
open http://localhost:9090/targets

# Grafana dashboard (pre-provisioned)
open http://localhost:3000
```

---

## Verification Checklist

| Check | How |
|---|---|
| Metrics exposed | `curl http://localhost:8000/metrics` returns `agent_runs_total`, `agent_run_duration_seconds`, `agent_validation_total` |
| Prometheus scraping | http://localhost:9090/targets shows `agent-harness` as **UP** |
| Grafana dashboard | http://localhost:3000 → "Agent Harness – Overview" shows panels with data |
| Traces in Tempo | In Grafana, go to Explore → Tempo → search by `service.name = summarizer-agent` |

---

## What Each File Does

### `telemetry/` (Python package – part of your agent code)

| File | Purpose |
|---|---|
| `metrics.py` | `MetricsCollector` – wraps `prometheus_client` counters & histograms; starts `/metrics` server |
| `tracing.py` | `TracingProvider` – configures OTel SDK, OTLP exporter, and provides `start_span()` context manager |

### `observability/` (Infrastructure configs – not part of the Python package)

| File | Purpose |
|---|---|
| `docker-compose.yml` | Defines Prometheus, Grafana, OTel Collector, Tempo |
| `prometheus.yml` | Scrape config targeting `host.docker.internal:8000` |
| `otel/config.yaml` | OTel Collector pipeline: OTLP receiver → batch processor → Tempo exporter |
| `tempo/config.yaml` | Tempo local storage config |
| `grafana/provisioning/datasources/` | Auto-configures Prometheus + Tempo as Grafana data sources |
| `grafana/provisioning/dashboards/` | Points Grafana at the dashboards directory |
| `grafana/dashboards/` | Pre-built "Agent Harness – Overview" dashboard JSON |

---

## Using Telemetry in Your Own Agents

```python
from telemetry.metrics import MetricsCollector
from telemetry.tracing import TracingProvider

# Setup (once at startup)
metrics = MetricsCollector()
metrics.start_server(port=8000)

tracing = TracingProvider(service_name="my-agent")
tracing.configure(otlp_endpoint="http://localhost:4317")

# In your agent's run loop
with tracing.start_span("my_step", attributes={"key": "value"}):
    result = do_work()

metrics.record_run(agent="my-agent", success=True, duration=1.5)
metrics.record_validation(agent="my-agent", valid=True)
```

---

## Metrics Reference

| Metric | Type | Labels | Description |
|---|---|---|---|
| `agent_runs_total` | Counter | `agent`, `status` | Total runs by agent and outcome (success/failure) |
| `agent_run_duration_seconds` | Histogram | `agent` | Run duration with p50/p95/p99 buckets |
| `agent_validation_total` | Counter | `agent`, `valid` | Validation outcomes (true/false) |

---

## Grafana Dashboard Panels

The pre-provisioned **"Agent Harness – Overview"** dashboard includes:

1. **Agent Runs (rate/min)** – time series of run rate by agent and status
2. **Run Duration p50/p95/p99** – latency percentiles over time
3. **Validation Outcomes (rate/min)** – valid vs. invalid outputs
4. **Success Rate (%)** – gauge with red/yellow/green thresholds (0/90/99%)

---

## Linux Networking Note

`host.docker.internal` works on macOS and Windows. On Linux, choose one of:

1. Run the agent inside a container on the same Docker Compose network
2. Set `network_mode: host` for Prometheus
3. Replace `host.docker.internal` with your host IP in `prometheus.yml`

---

## Tear Down

```bash
cd observability
docker compose down -v   # -v removes volumes (Grafana/Tempo data)
```

---

## Roadmap (next increments)

| Priority | Component | Purpose |
|---|---|---|
| Next | Loki + Promtail | Structured log aggregation correlated via `trace_id` |
| Later | Alertmanager | SLO-based alerts (e.g. success rate < 99%) |
| Later | Grafana dashboards | Per-agent detail dashboards, error breakdown |
