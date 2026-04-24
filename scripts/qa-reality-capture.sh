#!/usr/bin/env bash
# Reality-style QA for the Agent Matchmaker: HTTP + markers + optional Playwright PNGs.
# Prereq app:  pip install -r agent-matchmaker/requirements-app.txt
# Prereq PNGs: pip install -r agent-matchmaker/requirements-qa.txt && python3 -m playwright install chromium
#
# Usage:
#   ./scripts/qa-reality-capture.sh
#   BASE_URL=http://127.0.0.1:9000 ./scripts/qa-reality-capture.sh
#   NO_SERVER=1 ./scripts/qa-reality-capture.sh   # you already started webapp.py
#   HTTP_ONLY=1 ./scripts/qa-reality-capture.sh   # skip Playwright (stdlib evidence only)
#   MATCH_SMOKE=1 ./scripts/qa-reality-capture.sh  # POST /api/match smoke (optional GEMINI_API_KEY for body)
#   MATCH_SMOKE=1 MATCH_SMOKE_STRICT=1 ...       # CI: fail if smoke skipped or errors
#
# Evidence: agent-matchmaker/qa-screenshots/test-results.json (+ .png when Playwright works)

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -x "$ROOT/.venv/bin/python3" ]]; then
  PYTHON="$ROOT/.venv/bin/python3"
else
  PYTHON="${PYTHON:-python3}"
fi

BASE_URL="${BASE_URL:-http://127.0.0.1:8765}"
export BASE_URL
NO_SERVER="${NO_SERVER:-0}"
HTTP_ONLY="${HTTP_ONLY:-0}"
MATCH_SMOKE="${MATCH_SMOKE:-0}"
MATCH_SMOKE_STRICT="${MATCH_SMOKE_STRICT:-0}"
PORT="${PORT:-8765}"

_started_server=""

_ensure_server() {
  if [[ "$NO_SERVER" == "1" ]]; then
    return 0
  fi
  if curl -sf "${BASE_URL}/api/health" >/dev/null 2>&1; then
    return 0
  fi
  # Only auto-start for default local URL on expected port
  if [[ "$BASE_URL" != "http://127.0.0.1:${PORT}" ]] && [[ "$BASE_URL" != "http://localhost:${PORT}" ]]; then
    echo "No server at ${BASE_URL} — start it (e.g. ./scripts/run-agent-matchmaker.sh) or set NO_SERVER=0 with default BASE_URL." >&2
    return 1
  fi
  echo "Starting agent-matchmaker on ${BASE_URL} ..." >&2
  set -a
  [[ -f "$ROOT/.env" ]] && . "$ROOT/.env"
  [[ -f "$ROOT/agent-matchmaker/.env" ]] && . "$ROOT/agent-matchmaker/.env"
  set +a
  "$PYTHON" "$ROOT/agent-matchmaker/webapp.py" --port "$PORT" &
  _started_server=$!
  trap '[[ -n "$_started_server" ]] && kill "$_started_server" 2>/dev/null' EXIT
  for _ in $(seq 1 60); do
    if curl -sf "${BASE_URL}/api/health" >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.2
  done
  echo "Server did not become ready in time." >&2
  return 1
}

_ensure_server

args=("--base-url" "$BASE_URL")
if [[ "$HTTP_ONLY" == "1" ]]; then
  args+=("--http-only")
fi
if [[ "$MATCH_SMOKE_STRICT" == "1" ]]; then
  args+=("--match-smoke" "--match-smoke-strict")
elif [[ "$MATCH_SMOKE" == "1" ]]; then
  args+=("--match-smoke")
fi

"$PYTHON" "$ROOT/agent-matchmaker/qa_reality_check.py" "${args[@]}"
echo "Evidence: $ROOT/agent-matchmaker/qa-screenshots/test-results.json" >&2
ls -la "$ROOT/agent-matchmaker/qa-screenshots" 2>/dev/null || true
