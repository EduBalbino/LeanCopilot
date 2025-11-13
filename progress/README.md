LeanCopilot GPT-5-mini Focus
============================

This document tracks the current state of the LeanCopilot fork dedicated to the `gpt-5-mini` external generator.

## Current Goals

1. Remove all non-external generators and premise-selection code.
2. Route every Lean request through the Python FastAPI server that proxies OpenAI's `responses` endpoint.
3. Keep at most five structured completions per Lean request.
4. Automate the server lifecycle (systemd user service + file watcher).

## Status (Nov 13, 2025)

| Area | State | Notes |
| --- | --- | --- |
| Lean side | ✅ refactored | Only `ExternalGenerator` remains; options default to GPT-5-mini. |
| Python server | ⚠ structured output WIP | Server runs as a user service, but the new `responses` JSON contract still needs better validation (tests timing out due to OpenAI errors). |
| Systemd integration | ✅ deployed | `gpt5-server.service` autostarts, `gpt5-server.path` restarts on `python/server.py` edits. |
| Tests (`lake build LeanCopilotTests`) | ⚠ failing | Lean can't parse responses while the Python service returns OpenAI errors; run after stabilising the schema. |

## Blockers / Next Steps

1. **OpenAI responses schema** – tighten prompts or adopt official `response_format` once the SDK exposes it; add retries/backoff for non-JSON payloads.
2. **Lean tests** – re-run `lake build LeanCopilotTests` after the server consistently returns JSON.
3. **Monitoring** – add lightweight logging around the FastAPI endpoint to capture truncated responses for debugging.
4. **Docs** – keep this README and `AGENTS.md` up-to-date so other agents know the current state before touching the pipeline.

## Quick Start

```bash
systemctl --user status gpt5-server.service   # ensure the server is up
journalctl --user -u gpt5-server.service -f   # watch logs while testing
lake build LeanCopilotTests                        # rebuild Lean tests
```

Need help? Check `progress/AGENTS.md` for how to record updates and propose ideas.
