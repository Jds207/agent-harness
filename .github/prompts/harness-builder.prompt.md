# Harness Builder Prompt Template

**How to use this template:**
1. Copy everything below the line
2. Paste it into GitHub Copilot Chat
3. Replace `[YOUR REQUEST HERE]` with what you want to build

---

Enter HARNESS BUILDER MODE.

Follow .github/copilot-instructions.md exactly.

Current target: harness v0.1.0 (MVP with BaseAgent + schemas + reliability + observability + basic feedback).

Philosophy reminder (never violate):
- Systems engineering, not prompt engineering
- Correctness by construction (schemas + invariants at every step)
- Failures are first-class data: typed, classified, logged, and turned into reusable feedback loops
- Prioritize reliability, observability, and repeatability

Output rules:
- First restate the relevant principle(s)
- Think step-by-step
- Output the COMPLETE ready-to-copy file(s) with full type hints, Google-style docstrings, and "Why this design" comments
- End with a short "Why this improves reliability" section

Now do this: [YOUR REQUEST HERE]