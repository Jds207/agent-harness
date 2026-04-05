"""Async agent execution support for better performance and concurrency."""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Generic, TypeVar

from harness.base import AgentConfig, BaseAgent
from harness.schemas.base import BaseOutputSchema

T = TypeVar("T", bound=BaseOutputSchema)


class AsyncBaseAgent(BaseAgent[T], Generic[T]):
    """Async version of BaseAgent for concurrent execution."""

    async def arun(self, input_data: dict[str, Any]) -> T:
        """Async version of run() method."""
        self._trace = []
        self._trace_id = self._generate_trace_id()

        # Async validation
        await self._avalidate_input(input_data)

        # Async execution with tracing
        result = await self._aexecute(input_data)

        # Async validation of output
        await self._avalidate_output(result)

        return result

    async def _avalidate_input(self, input_data: dict[str, Any]) -> None:
        """Async input validation."""
        # Implement async validation logic
        pass

    async def _avalidate_output(self, result: T) -> None:
        """Async output validation."""
        # Implement async validation logic
        pass

    async def _aexecute(self, input_data: dict[str, Any]) -> T:
        """Async execution - override in subclasses."""
        raise NotImplementedError


class AsyncAgentPool:
    """Pool of async agents for concurrent execution."""

    def __init__(self, agents: list[AsyncBaseAgent], max_concurrent: int = 10):
        self.agents = agents
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def run_batch(self, inputs: list[dict[str, Any]]) -> list[T]:
        """Run multiple inputs concurrently with rate limiting."""
        async def run_single(input_data: dict[str, Any]) -> T:
            async with self.semaphore:
                # Round-robin agent selection
                agent = self.agents[len(self.agents) % len(self.agents)]
                return await agent.arun(input_data)

        tasks = [run_single(inp) for inp in inputs]
        return await asyncio.gather(*tasks)
