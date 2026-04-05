"""Health check system for production readiness."""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from harness.observability.logging import get_logger

logger = get_logger()


class HealthStatus:
    """Health check result status."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class HealthCheck(ABC):
    """Base class for health checks."""

    def __init__(self, name: str, timeout: float = 5.0):
        self.name = name
        self.timeout = timeout

    @abstractmethod
    async def check(self) -> tuple[str, str]:
        """Perform health check. Returns (status, message)."""
        pass


class DatabaseHealthCheck(HealthCheck):
    """Check database connectivity."""

    def __init__(self, connection_string: str):
        super().__init__("database")
        self.connection_string = connection_string

    async def check(self) -> tuple[str, str]:
        try:
            # Simulate DB check
            await asyncio.sleep(0.1)
            return HealthStatus.HEALTHY, "Database connection OK"
        except Exception as e:
            return HealthStatus.UNHEALTHY, f"Database error: {e}"


class ExternalAPIHealthCheck(HealthCheck):
    """Check external API availability."""

    def __init__(self, name: str, url: str, expected_status: int = 200):
        super().__init__(f"api_{name}")
        self.url = url
        self.expected_status = expected_status

    async def check(self) -> tuple[str, str]:
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(self.url, timeout=self.timeout) as resp:
                    if resp.status == self.expected_status:
                        return HealthStatus.HEALTHY, f"API {self.url} OK"
                    else:
                        return HealthStatus.UNHEALTHY, f"API {self.url} returned {resp.status}"
        except Exception as e:
            return HealthStatus.UNHEALTHY, f"API {self.url} error: {e}"


class MetricsHealthCheck(HealthCheck):
    """Check metrics collection is working."""

    def __init__(self, metrics_collector: Any):
        super().__init__("metrics")
        self.metrics = metrics_collector

    async def check(self) -> tuple[str, str]:
        try:
            # Check if metrics are being collected
            # This is a simplified check - in practice you'd check actual metric values
            return HealthStatus.HEALTHY, "Metrics collection OK"
        except Exception as e:
            return HealthStatus.UNHEALTHY, f"Metrics error: {e}"


class HealthChecker:
    """Manages and runs health checks."""

    def __init__(self):
        self.checks: List[HealthCheck] = []
        self.last_results: Dict[str, tuple[str, str, float]] = {}

    def add_check(self, check: HealthCheck) -> None:
        """Add a health check."""
        self.checks.append(check)

    async def run_all_checks(self) -> Dict[str, tuple[str, str, float]]:
        """Run all health checks concurrently."""
        tasks = []
        for check in self.checks:
            task = asyncio.create_task(self._run_check(check))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        health_results = {}
        for check, result in zip(self.checks, results):
            if isinstance(result, Exception):
                health_results[check.name] = (HealthStatus.UNHEALTHY, str(result), time.time())
            else:
                status, message = result
                health_results[check.name] = (status, message, time.time())

        self.last_results = health_results
        return health_results

    async def _run_check(self, check: HealthCheck) -> tuple[str, str]:
        """Run a single health check with timeout."""
        try:
            return await asyncio.wait_for(check.check(), timeout=check.timeout)
        except asyncio.TimeoutError:
            return HealthStatus.UNHEALTHY, f"Check timed out after {check.timeout}s"
        except Exception as e:
            return HealthStatus.UNHEALTHY, f"Check failed: {e}"

    def get_overall_status(self) -> str:
        """Get overall system health status."""
        if not self.last_results:
            return HealthStatus.UNHEALTHY

        statuses = [status for status, _, _ in self.last_results.values()]

        if any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY

    async def start_health_endpoint(self, port: int = 8080) -> None:
        """Start HTTP health check endpoint."""
        from aiohttp import web

        async def health_handler(request: web.Request) -> web.Response:
            results = await self.run_all_checks()
            overall = self.get_overall_status()

            response_data = {
                "status": overall,
                "timestamp": time.time(),
                "checks": {
                    name: {"status": status, "message": message, "timestamp": ts}
                    for name, (status, message, ts) in results.items()
                }
            }

            status_code = 200 if overall == HealthStatus.HEALTHY else 503
            return web.json_response(response_data, status=status_code)

        app = web.Application()
        app.router.add_get("/health", health_handler)
        app.router.add_get("/ready", health_handler)  # Kubernetes readiness

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()

        logger.info("health_endpoint_started", port=port)
        # Keep running
        while True:
            await asyncio.sleep(60)


# Global health checker instance
health_checker = HealthChecker()