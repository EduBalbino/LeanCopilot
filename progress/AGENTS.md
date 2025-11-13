Agent Playbook
==============

This file explains how contributors (human or automated) should use `progress/README.md` as the single source of truth for the GPT-5-nano refactor.

## Using the Progress README

1. **Before starting work** – read the Status table to understand what already changed and which tasks remain.
2. **While working** – add concise bullet updates under *Status* or *Next Steps* instead of scattering notes elsewhere.
3. **After finishing** – note the outcome (e.g., “Structured JSON stable ✅”) so future agents don't repeat the same investigation.

## Logging Ideas & Experiments

* Append potential improvements to the `Next Steps` list in the README. Keep them short, actionable, and tagged with the type of work (e.g., `[python] add exponential backoff`).
* If you spike on an idea that fails, still record it with a short rationale (“Tried enabling `response_format`, SDK 2.7.2 rejects the parameter – revisit after upgrading OpenAI library.”).

## Minimal Process

1. **Plan**: Outline tasks referencing README sections.
2. **Act**: Implement + test.
3. **Document**: Update `progress/README.md` + commit references.

Following this loop keeps the GPT-5-nano effort transparent and prevents duplicated work.

## FastAPI Server Hygiene

* Whenever you touch anything under `python/`, restart the GPT-5 server so Lean picks up the new behavior:

  ```bash
  systemctl --user restart gpt5-server.service
  journalctl --user -u gpt5-server.service -n 50
  ```

* Treat `/generate` contract changes like API migrations—note them in `progress/README.md` and the main `README`.
