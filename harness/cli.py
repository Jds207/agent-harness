#!/usr/bin/env python3
"""CLI tools for testing and debugging agent harness components.

Usage:
    python -m harness.cli test-agent --config examples/summarizer/config.json
    python -m harness.cli benchmark --agent summarizer --iterations 100
    python -m harness.cli validate-schema --schema examples/summarizer/schema.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any

from harness.base import AgentConfig
from harness.observability.logging import setup_logging
from telemetry.enhanced_metrics import enhanced_metrics


def load_config(config_path: str) -> AgentConfig:
    """Load agent configuration from JSON file."""
    with open(config_path) as f:
        data = json.load(f)
    return AgentConfig(**data)


def test_agent(args: argparse.Namespace) -> None:
    """Test a single agent run."""
    setup_logging(json=True, level="INFO")

    # Load config
    config = load_config(args.config)

    # Import the agent class dynamically
    module_path = args.agent_module
    class_name = args.agent_class

    # Simple dynamic import (in production, use importlib)
    if module_path == "examples.summarizer":
        from examples.summarizer import SummarizerAgent
        agent_class = SummarizerAgent
    else:
        print(f"Unknown agent module: {module_path}")
        return

    # Create agent
    agent = agent_class(config=config, metrics=enhanced_metrics)

    # Start metrics server
    enhanced_metrics.start_server(port=8000)

    # Test input
    test_input = {"document": "This is a test document for summarization."}

    try:
        start_time = time.monotonic()
        result = agent.run(test_input)
        duration = time.monotonic() - start_time

        print("✅ Agent run successful"        print(f"   Duration: {duration:.2f}s")
        print(f"   Result: {result}")
        print(f"   Trace ID: {result.trace_id}")

    except Exception as e:
        print(f"❌ Agent run failed: {e}")
        sys.exit(1)


async def benchmark_agent(args: argparse.Namespace) -> None:
    """Benchmark agent performance."""
    setup_logging(json=True, level="WARNING")

    config = load_config(args.config)

    # Import agent
    if args.agent == "summarizer":
        from examples.summarizer import SummarizerAgent
        agent_class = SummarizerAgent
    else:
        print(f"Unknown agent: {args.agent}")
        return

    agent = agent_class(config=config, metrics=enhanced_metrics)
    enhanced_metrics.start_server(port=8001)

    # Benchmark data
    test_docs = [
        "Short document.",
        "This is a medium length document with some content.",
        "This is a longer document that contains more text and should take longer to process. " * 10,
    ]

    print(f"🚀 Benchmarking {args.agent} with {args.iterations} iterations...")

    start_time = time.time()
    successes = 0
    failures = 0

    for i in range(args.iterations):
        doc = test_docs[i % len(test_docs)]
        try:
            result = await agent.arun({"document": doc})  # Assuming async support
            successes += 1
        except Exception:
            failures += 1

        if (i + 1) % 10 == 0:
            print(f"   Progress: {i+1}/{args.iterations} runs")

    total_time = time.time() - start_time
    rps = args.iterations / total_time

    print("📊 Benchmark Results:"    print(f"   Total runs: {args.iterations}")
    print(f"   Successes: {successes}")
    print(f"   Failures: {failures}")
    print(".2f"    print(".2f"
def validate_schema(args: argparse.Namespace) -> None:
    """Validate a JSON schema file."""
    try:
        with open(args.schema) as f:
            schema = json.load(f)

        # Basic validation - check required fields
        required_fields = ["type", "properties"]
        if not all(field in schema for field in required_fields):
            print(f"❌ Invalid schema: missing {required_fields}")
            sys.exit(1)

        print("✅ Schema validation passed"        print(f"   Type: {schema.get('type')}")
        print(f"   Properties: {list(schema.get('properties', {}).keys())}")

    except Exception as e:
        print(f"❌ Schema validation failed: {e}")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent Harness CLI Tools")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Test agent command
    test_parser = subparsers.add_parser("test-agent", help="Test a single agent run")
    test_parser.add_argument("--config", required=True, help="Path to agent config JSON")
    test_parser.add_argument("--agent-module", required=True, help="Agent module path")
    test_parser.add_argument("--agent-class", required=True, help="Agent class name")

    # Benchmark command
    bench_parser = subparsers.add_parser("benchmark", help="Benchmark agent performance")
    bench_parser.add_argument("--agent", required=True, help="Agent name")
    bench_parser.add_argument("--config", required=True, help="Path to agent config JSON")
    bench_parser.add_argument("--iterations", type=int, default=100, help="Number of iterations")

    # Validate schema command
    schema_parser = subparsers.add_parser("validate-schema", help="Validate JSON schema")
    schema_parser.add_argument("--schema", required=True, help="Path to schema JSON file")

    args = parser.parse_args()

    if args.command == "test-agent":
        test_agent(args)
    elif args.command == "benchmark":
        asyncio.run(benchmark_agent(args))
    elif args.command == "validate-schema":
        validate_schema(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()