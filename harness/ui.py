"""Web UI for agent harness management and testing."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from harness.health import health_checker
from harness.observability.logging import get_logger
from telemetry.enhanced_metrics import enhanced_metrics

logger = get_logger()
app = FastAPI(title="Agent Harness UI", version="0.2.0")

# Templates and static files
templates = Jinja2Templates(directory=Path(__file__).parent / "ui" / "templates")
static_path = Path(__file__).parent / "ui" / "static"

# Mount static files if they exist
if static_path.exists():
    app.mount("/static", StaticFiles(directory=static_path), name="static")


class AgentTestRequest(BaseModel):
    """Request model for agent testing."""
    agent_name: str
    input_data: Dict[str, Any]
    config: Optional[Dict[str, Any]] = None


class AgentTestResponse(BaseModel):
    """Response model for agent testing."""
    success: bool
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration: float
    trace_id: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard showing agent status and metrics."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/api/health")
async def get_health():
    """Get overall system health."""
    results = await health_checker.run_all_checks()
    return {
        "status": health_checker.get_overall_status(),
        "checks": results,
        "timestamp": asyncio.get_event_loop().time()
    }


@app.get("/api/metrics/summary")
async def get_metrics_summary():
    """Get key metrics summary."""
    # This would integrate with Prometheus, but for now return basic info
    return {
        "active_agents": 2,  # Would query actual running agents
        "total_runs": 462,   # From our load generator
        "success_rate": 89.2,
        "avg_latency": 0.95
    }


@app.get("/api/agents")
async def list_agents():
    """List available agents."""
    # Discover agents from examples directory
    agents = []
    examples_dir = Path(__file__).parent.parent / "examples"

    for agent_dir in examples_dir.iterdir():
        if agent_dir.is_dir() and (agent_dir / "__init__.py").exists():
            config_file = agent_dir / "config.json"
            schema_file = agent_dir / "schema.json"

            agent_info = {
                "name": agent_dir.name,
                "path": str(agent_dir),
                "has_config": config_file.exists(),
                "has_schema": schema_file.exists(),
            }

            # Load schema if available
            if schema_file.exists():
                try:
                    with open(schema_file) as f:
                        agent_info["schema"] = json.load(f)
                except Exception:
                    pass

            agents.append(agent_info)

    return {"agents": agents}


@app.post("/api/agents/test")
async def test_agent(request: AgentTestRequest) -> AgentTestResponse:
    """Test an agent with given input."""
    try:
        # Dynamic agent loading (simplified)
        if request.agent_name == "summarizer":
            from examples.summarizer import SummarizerAgent
            from harness.base import AgentConfig

            config = AgentConfig()  # Use defaults or merge with request.config
            agent = SummarizerAgent(config=config, metrics=enhanced_metrics)

            import time
            start_time = time.monotonic()

            result = agent.run(request.input_data)

            duration = time.monotonic() - start_time

            return AgentTestResponse(
                success=True,
                output=result.dict() if hasattr(result, 'dict') else result,
                duration=duration,
                trace_id=getattr(result, 'trace_id', None)
            )

        else:
            raise HTTPException(status_code=404, detail=f"Agent {request.agent_name} not found")

    except Exception as e:
        logger.error("agent_test_failed", agent=request.agent_name, error=str(e))
        return AgentTestResponse(
            success=False,
            error=str(e),
            duration=0.0
        )


@app.get("/playground", response_class=HTMLResponse)
async def playground(request: Request):
    """Interactive agent testing playground."""
    return templates.TemplateResponse("playground.html", {"request": request})


@app.get("/agents/{agent_name}", response_class=HTMLResponse)
async def agent_detail(request: Request, agent_name: str):
    """Agent detail and configuration page."""
    return templates.TemplateResponse("agent_detail.html", {
        "request": request,
        "agent_name": agent_name
    })


def create_ui_directories():
    """Create UI template and static directories."""
    ui_dir = Path(__file__).parent / "ui"
    templates_dir = ui_dir / "templates"
    static_dir = ui_dir / "static"

    for dir_path in [ui_dir, templates_dir, static_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)


def create_basic_templates():
    """Create basic HTML templates."""
    templates_dir = Path(__file__).parent / "ui" / "templates"

    # Dashboard template
    dashboard_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Agent Harness Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .metric { background: #f0f0f0; padding: 10px; margin: 10px; border-radius: 5px; }
        .healthy { color: green; }
        .unhealthy { color: red; }
    </style>
</head>
<body>
    <h1>Agent Harness Dashboard</h1>

    <div class="metric">
        <h3>System Health</h3>
        <div id="health-status">Loading...</div>
    </div>

    <div class="metric">
        <h3>Active Agents</h3>
        <div id="agent-count">Loading...</div>
    </div>

    <div class="metric">
        <h3>Recent Activity</h3>
        <div id="recent-activity">Loading...</div>
    </div>

    <nav>
        <a href="/playground">Agent Playground</a> |
        <a href="/api/health">Health API</a> |
        <a href="http://localhost:3000">Grafana</a>
    </nav>

    <script>
        async function updateDashboard() {
            try {
                const healthResponse = await fetch('/api/health');
                const health = await healthResponse.json();
                document.getElementById('health-status').innerHTML =
                    `<span class="${health.status === 'healthy' ? 'healthy' : 'unhealthy'}">${health.status.toUpperCase()}</span>`;

                const metricsResponse = await fetch('/api/metrics/summary');
                const metrics = await metricsResponse.json();
                document.getElementById('agent-count').innerHTML = `${metrics.active_agents} agents running`;
                document.getElementById('recent-activity').innerHTML =
                    `${metrics.total_runs} total runs, ${metrics.success_rate}% success rate`;
            } catch (e) {
                console.error('Dashboard update failed:', e);
            }
        }

        updateDashboard();
        setInterval(updateDashboard, 5000);
    </script>
</body>
</html>
    """

    # Playground template
    playground_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Agent Playground</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        textarea { width: 100%; height: 100px; }
        .result { background: #f0f0f0; padding: 10px; margin: 10px 0; border-radius: 5px; }
        .success { border-left: 5px solid green; }
        .error { border-left: 5px solid red; }
    </style>
</head>
<body>
    <h1>Agent Playground</h1>

    <form id="test-form">
        <label>Agent:</label>
        <select id="agent-select">
            <option value="summarizer">Summarizer</option>
        </select>

        <label>Input Data (JSON):</label>
        <textarea id="input-data">{"document": "This is a test document to summarize."}</textarea>

        <button type="submit">Test Agent</button>
    </form>

    <div id="results"></div>

    <script>
        document.getElementById('test-form').addEventListener('submit', async (e) => {
            e.preventDefault();

            const agentName = document.getElementById('agent-select').value;
            const inputData = JSON.parse(document.getElementById('input-data').value);

            try {
                const response = await fetch('/api/agents/test', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        agent_name: agentName,
                        input_data: inputData
                    })
                });

                const result = await response.json();

                const resultDiv = document.createElement('div');
                resultDiv.className = `result ${result.success ? 'success' : 'error'}`;
                resultDiv.innerHTML = `
                    <h4>${result.success ? 'Success' : 'Error'}</h4>
                    <p><strong>Duration:</strong> ${result.duration.toFixed(3)}s</p>
                    ${result.output ? `<pre>${JSON.stringify(result.output, null, 2)}</pre>` : ''}
                    ${result.error ? `<p><strong>Error:</strong> ${result.error}</p>` : ''}
                    ${result.trace_id ? `<p><strong>Trace ID:</strong> ${result.trace_id}</p>` : ''}
                `;

                document.getElementById('results').prepend(resultDiv);

            } catch (e) {
                alert('Test failed: ' + e.message);
            }
        });
    </script>
</body>
</html>
    """

    with open(templates_dir / "dashboard.html", "w") as f:
        f.write(dashboard_html)

    with open(templates_dir / "playground.html", "w") as f:
        f.write(playground_html)

    # Create a basic agent detail template
    agent_detail_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Agent: {{ agent_name }}</title>
</head>
<body>
    <h1>Agent: {{ agent_name }}</h1>
    <p>Agent details and configuration would go here.</p>
    <a href="/">Back to Dashboard</a>
</body>
</html>
    """

    with open(templates_dir / "agent_detail.html", "w") as f:
        f.write(agent_detail_html)


def main():
    """Run the web UI server."""
    create_ui_directories()
    create_basic_templates()

    print("🚀 Starting Agent Harness Web UI...")
    print("📊 Dashboard: http://localhost:8080")
    print("🎮 Playground: http://localhost:8080/playground")
    print("🔍 Health API: http://localhost:8080/api/health")

    uvicorn.run(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()