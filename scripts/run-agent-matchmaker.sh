#!/usr/bin/env bash
# Start the local Agent Matchmaker (static UI + optional Gemini API).
# Prereq: pip install -r agent-matchmaker/requirements-app.txt (use repo .venv — see agent-matchmaker/README.md).
# API key: repo-root `.gemini_api_key` (one line), or `.env`, or export GEMINI_API_KEY (optional if pasting in UI)
#
# HOW TO RUN (this file is bash, not Python):
#   ./scripts/run-agent-matchmaker.sh
#   bash ./scripts/run-agent-matchmaker.sh
# Do NOT: python3 ./scripts/run-agent-matchmaker.sh  → SyntaxError (Python tries to parse shell).

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Prefer repo .venv so Gemini deps are visible (Homebrew python3 is often PEP 668–managed and cannot pip install system-wide).
if [[ -x "$ROOT/.venv/bin/python3" ]]; then
  PYTHON="$ROOT/.venv/bin/python3"
elif [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
else
  PYTHON="python3"
fi

if ! "$PYTHON" -c "import google.generativeai" 2>/dev/null; then
  echo "" >&2
  echo "Gemini SDK missing for: $PYTHON" >&2
  echo "  The matchmaker UI will show “no sdk” until google-generativeai is installed in THIS interpreter." >&2
  echo "  Fix (repo root):" >&2
  echo "    python3 -m venv .venv && .venv/bin/python3 -m pip install -r agent-matchmaker/requirements-app.txt" >&2
  echo "  Then start again with this script (it auto-picks .venv/bin/python3 when present)." >&2
  echo "" >&2
fi
# Export vars from .env so Python inherits them (same as many other tools). Optional
# second file overrides the first for duplicate keys.
set -a
[[ -f "$ROOT/.env" ]] && . "$ROOT/.env"
[[ -f "$ROOT/.env.local" ]] && . "$ROOT/.env.local"
[[ -f "$ROOT/agent-matchmaker/.env" ]] && . "$ROOT/agent-matchmaker/.env"
set +a
exec "$PYTHON" agent-matchmaker/webapp.py "$@"
