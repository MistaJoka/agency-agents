#!/usr/bin/env bash
# Full QA matrix: FORWARD then REVERSE (Agent Matchmaker).
# See: agent-matchmaker/QA-SEQUENCE.md · agent-matchmaker/QA-FMEA.md
#
#   ./scripts/qa-test-matrix.sh
#   MATRIX_SKIP_GEMINI=1 ./scripts/qa-test-matrix.sh   # skip strict POST /api/match steps
#
# Uses same env as qa-reality-capture.sh: BASE_URL, NO_SERVER, PORT

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export BASE_URL="${BASE_URL:-http://127.0.0.1:8765}"
export NO_SERVER="${NO_SERVER:-0}"
export PORT="${PORT:-8765}"
SKIP_GEMINI="${MATRIX_SKIP_GEMINI:-0}"

_run() {
  echo "" >&2
  echo ">>> $*" >&2
  echo "" >&2
}

_run "========== QA MATRIX: FORWARD =========="

_run "F0 — rebuild catalog + index.html"
python3 "$ROOT/scripts/build_agent_matchmaker.py"

_run "F1 — HTTP-only (markers + health)"
HTTP_ONLY=1 MATCH_SMOKE=0 MATCH_SMOKE_STRICT=0 "$ROOT/scripts/qa-reality-capture.sh"

_run "F2 — Playwright + PNGs + layout"
HTTP_ONLY=0 MATCH_SMOKE=0 MATCH_SMOKE_STRICT=0 "$ROOT/scripts/qa-reality-capture.sh"

if [[ "$SKIP_GEMINI" == "1" ]]; then
  echo "" >&2
  echo "(MATRIX_SKIP_GEMINI=1 — skipping F3 strict Gemini smoke)" >&2
else
  _run "F3 — strict Gemini smoke + HTTP-only"
  MATCH_SMOKE=1 MATCH_SMOKE_STRICT=1 HTTP_ONLY=1 "$ROOT/scripts/qa-reality-capture.sh"
fi

_run "========== QA MATRIX: REVERSE =========="

if [[ "$SKIP_GEMINI" != "1" ]]; then
  _run "R1 — strict Gemini smoke first"
  MATCH_SMOKE=1 MATCH_SMOKE_STRICT=1 HTTP_ONLY=1 "$ROOT/scripts/qa-reality-capture.sh"
else
  echo "" >&2
  echo "(MATRIX_SKIP_GEMINI=1 — skipping R1 strict Gemini smoke)" >&2
fi

_run "R2 — full Playwright"
HTTP_ONLY=0 MATCH_SMOKE=0 MATCH_SMOKE_STRICT=0 "$ROOT/scripts/qa-reality-capture.sh"

_run "R3 — HTTP-only"
HTTP_ONLY=1 MATCH_SMOKE=0 MATCH_SMOKE_STRICT=0 "$ROOT/scripts/qa-reality-capture.sh"

_run "R4 — rebuild catalog again"
python3 "$ROOT/scripts/build_agent_matchmaker.py"

python3 -c "import json; json.load(open('$ROOT/agent-matchmaker/catalog.json'))" >/dev/null

echo "" >&2
echo "========== QA MATRIX: COMPLETE ==========" >&2
echo "Evidence: $ROOT/agent-matchmaker/qa-screenshots/test-results.json" >&2
