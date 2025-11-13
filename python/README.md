Python Server for GPT-5-nano
============================

This folder now contains a **single** FastAPI server that proxies requests from Lean Copilot to OpenAI's GPT-5-nano API. Each `/generate` call forwards one prompt and returns **exactly five** completions.

## Requirements

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn loguru openai
export OPENAI_API_KEY=sk-...
```

## Running the Server

```bash
uvicorn server:app --port 23337
```

After the server is up running, you can go to `LeanCopilotTests/ModelAPIs.lean` to point Lean at this endpoint (or register another GPT-5-nano host/port).

## Testing & Monitoring

The recommended regression test is to build the tactic examples:

```bash
lake build LeanCopilotTests
# or target LeanCopilotTests/TacticSuggestion.lean specifically
```

These examples exercise `suggest_tactics`, so any API error from the Python server shows up immediately in Lean. The server now enforces OpenAI Structured Outputs, meaning schema violations and safety refusals raise HTTP errors. If you run the server as a service, inspect it with `journalctl -u <service-name>` whenever a request fails.

## Contributions

We currently scope the server to GPT-5-nano only; please keep contributions aligned with that goal. We use [`black`](https://pypi.org/project/black/) to format code in this folder.
