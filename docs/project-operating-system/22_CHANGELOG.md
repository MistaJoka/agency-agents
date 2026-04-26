# Changelog

## 2026-04-25 - ASLF QA Memory (process layer)

### Change

Added `docs/aslf/` with ASLF workflow docs, failure/regression/test-decision logs, risk map, optional evidence folder, `scripts/qa-log.sh`, regression issue template, and PR checklist links. Linked ASLF from project operating-system docs, root README, and CONTRIBUTING.

### Why

Preserve QA and testing knowledge over time; make failures and guard tests traceable without rewriting working code.

### Files Touched

- `docs/aslf/*`
- `docs/project-operating-system/00_START_HERE.md`, `13_TESTING.md`, `16_TASKS.md`, `17_DECISIONS.md`, `22_CHANGELOG.md`, `20_AGENT.md`
- `README.md`, `CONTRIBUTING.md`
- `.github/PULL_REQUEST_TEMPLATE.md`, `.github/ISSUE_TEMPLATE/regression_report.yml`
- `scripts/qa-log.sh`

### Working Code Protected

- No changes to agent catalog content, matchmaker runtime, or application logic.

### Tests / Checks

- Documentation and template-only change; optional manual check that `scripts/qa-log.sh` appends to `docs/aslf/evidence/session-log.md`.

### Regression Result

Pass (no runtime behavior changed).

### FMAE Result

Low risk; main failure mode is doc drift if ASLF logs are not updated after real incidents.

## 2026-04-25 - Adopt Project Operating System Overlay

### Change

Added `docs/project-operating-system/` with customized planning, architecture, testing, regression, FMAE, task, agent, and handoff docs based on the agnostic app development template.

### Why

The repo has grown beyond a simple prompt catalog. It now needs a central operating layer that protects existing content, clarifies current product direction, and gives future AI/human contributors a regression and FMAE process.

### Files Touched

- `docs/project-operating-system/*`
- `README.md`

### Working Code Protected

- Agent category directories were not moved.
- `agent-matchmaker/` was not restructured.
- `lib/`, `scripts/`, `data/`, and `supabase-web/` were not replaced.
- Generic template `src/`, `tests/`, and `assets/` folders were not copied to the repo root.

### Tests / Checks

- `python3 scripts/build_agent_matchmaker.py` - passed; rebuilt `agent-matchmaker/index.html` and `agent-matchmaker/catalog.json` with 199 agents.
- `HTTP_ONLY=1 ./scripts/qa-reality-capture.sh` - initial sandbox run failed with `PermissionError` while binding the local server port; escalated rerun passed HTTP checks and wrote `agent-matchmaker/qa-screenshots/test-results.json`.

### Regression Result

Pass for the documentation overlay and HTTP-only matchmaker regression check. QA readiness remains `NEEDS_WORK` because the selected command intentionally skipped Playwright visual proof.

### FMAE Result

Low runtime risk because this is documentation/process overlay work. Main failure mode is documentation drift or a broken README link.

### Remaining Risks

- Some future product direction remains `UNKNOWN`.
- `supabase-web` role still needs a decision.
