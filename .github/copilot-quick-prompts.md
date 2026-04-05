# Copilot Quick Prompts for Reliable Agent Harness

Use these exact prompts in Copilot Chat (Ctrl+Shift+I):

## Build Commands
- Build the complete harness skeleton with full folder structure, pyproject.toml, __init__.py (v0.1.0), and all base files. Follow the exact structure and philosophy in copilot-instructions.md.
- Create the complete harness/base/ folder with BaseAgent.py and AgentConfig.py
- Create the complete harness/schemas/ folder
- Create the complete harness/reliability/ folder
- Create the complete harness/observability/ folder
- Create the complete harness/feedback/ folder

## Project Commands
- Generate a brand new project folder called projects/01-invoice-extractor that depends on the harness v0.1.0 via git dependency. Include full README and example usage.
- Generate a brand new project folder called projects/02-research-agent that depends on the harness v0.2.0

## Feature Commands
- Add or improve the RetryWithFallback class. Include exponential backoff, jitter, and fallback model support.
- Add the CircuitBreaker pattern with configurable thresholds.
- Add a new business invariant called "totals must balance" to the validator.

## Maintenance Commands
- Review the file schemas.py for correctness, invariants, and reliability gaps.
- Generate comprehensive test suite for BaseAgent.
- Update the main README with new features and evolution table.
- Bump harness version to 0.2.0 and update CHANGELOG.md

Copy and paste any of the above directly into Copilot Chat.