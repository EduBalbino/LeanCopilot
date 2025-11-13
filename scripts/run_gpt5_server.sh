#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="/home/devpod/lean_prover/LeanCopilotLLM/LeanCopilot"
SERVER_DIR="$REPO_ROOT/python"
cd "$SERVER_DIR"
if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi
if [[ -d .venv && -f .venv/bin/activate ]]; then
  source .venv/bin/activate
fi
exec uvicorn server:app --host 0.0.0.0 --port 23337
