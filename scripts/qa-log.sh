#!/usr/bin/env bash
# Append a timestamped line to docs/aslf/evidence/session-log.md
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$ROOT/docs/aslf/evidence/session-log.md"
MSG="${*:-}"

if [[ -z "$MSG" ]]; then
  echo "Usage: $0 <message>" >&2
  exit 1
fi

TS="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
printf '\n- `%s` %s\n' "$TS" "$MSG" >>"$LOG"
echo "Appended to $LOG"
