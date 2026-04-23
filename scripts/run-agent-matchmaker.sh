#!/usr/bin/env bash
# Start the local Agent Matchmaker (static UI + optional Gemini API).
# Prereq: pip install -r agent-matchmaker/requirements-app.txt (use repo .venv — see agent-matchmaker/README.md).
# API key: repo-root `.gemini_api_key` (one line), or `.env`, or export GEMINI_API_KEY (optional if pasting in UI)

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Prefer repo .venv so Gemini deps are visible (Homebrew python3 is often PEP 668–managed and cannot pip install system-wide).
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
else
  PYTHON="python3"
fi
# Export vars from .env so Python inherits them (same as many other tools). Optional
# second file overrides the first for duplicate keys.
set -a
[[ -f "$ROOT/.env" ]] && . "$ROOT/.env"
[[ -f "$ROOT/.env.local" ]] && . "$ROOT/.env.local"
[[ -f "$ROOT/agent-matchmaker/.env" ]] && . "$ROOT/agent-matchmaker/.env"
set +a
exec "$PYTHON" agent-matchmaker/webapp.py "$@"
