# Failure patterns

Recurring bugs and failures. **Append new patterns**; do not delete history—strike through or mark `resolved` with date if obsolete.

Copy the block below for each new pattern.

---

## Pattern ID — FP-001 (example from changelog evidence)

- Date first observed: 2026-04-25
- Area: `scripts/qa-reality-capture.sh` / local HTTP QA
- Symptom: `PermissionError` binding local server port during QA capture
- Root cause: environment/sandbox port availability (initial run); not necessarily application logic
- Trigger: running full or HTTP-only QA in restricted environment
- Detection method: script stderr; `agent-matchmaker/qa-screenshots/test-results.json` when run completes
- Fix applied: rerun in environment with allowed bind; documented in changelog
- Test added: n/a (environmental); operational note
- Regression risk: Low for catalog content; medium for “green CI locally” assumptions
- Related files: `scripts/qa-reality-capture.sh`, `docs/project-operating-system/22_CHANGELOG.md`
- Related commits: (link when known)
- Notes: Treat first-failure vs rerun as evidence that failures can be environmental—classify before rewriting scripts.

---

## Pattern ID — _Template_ (copy from here)

- Date first observed:
- Area:
- Symptom:
- Root cause:
- Trigger:
- Detection method:
- Fix applied:
- Test added:
- Regression risk:
- Related files:
- Related commits:
- Notes:
