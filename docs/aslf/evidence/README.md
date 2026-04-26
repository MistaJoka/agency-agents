# ASLF evidence (optional)

Purpose: hold **redacted, shareable** excerpts of CI logs, test output, or QA notes that support entries in `FAILURE_PATTERNS.md` or `TEST_DECISION_LOG.md`.

## Rules

- **No secrets:** strip tokens, cookies, env values, internal URLs if needed.
- **Prefer summaries** in the main ASLF markdown files; put long verbatim logs here only when useful.
- Repo `.gitignore` ignores `logs/` and `*.log`; this folder is **tracked** so small evidence files can be committed deliberately.
- Do not commit large binaries; link to CI run or attach gist if huge.

## Suggested filenames

- `YYYY-MM-DD-topic-short.md` or `.txt`

## Session log

`session-log.md` is appended by `scripts/qa-log.sh` (if present). Trim or rotate if it grows too large; archive old lines to a dated file instead of deleting history silently.
