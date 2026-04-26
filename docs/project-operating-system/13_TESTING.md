# Testing

## Core Thing That Must Not Break

Users must be able to build/load the local agent catalog and use the matchmaker without losing source content or provenance.

## Unit-Level Checks

- Markdown normalizers parse expected agent metadata.
- Registry/export helpers preserve stable ids and source paths.

## Integration Checks

- `python3 scripts/build_agent_matchmaker.py`
- `python3 scripts/normalize_sources.py` when registry changes are touched.
- `python3 scripts/export_registry.py` when export shape changes.
- `python3 scripts/export_cursor_pack.py --limit N` when Cursor export changes.

## E2E / Reality Checks

- `HTTP_ONLY=1 ./scripts/qa-reality-capture.sh`
- Full `./scripts/qa-reality-capture.sh` when visual dependencies are available.
- Optional Gemini smoke with `MATCH_SMOKE=1` when API dependencies and keys are available.

## Manual Checks

- Open static matchmaker and verify catalog loads.
- Search for a known agent.
- Inspect source for a known agent.
- Confirm README links remain valid.

## FMAE Quality Gate

Use FMAE for meaningful changes to:

- Catalog generation
- Registry sync/normalization
- Export pack generation
- Local web APIs
- `supabase-web`
- Source path handling
- Secrets or external API handling

## Acceptance Criteria

MVP is acceptable when:

- Catalog build works.
- Static/local matchmaker still works.
- Registry commands affected by the change still work or are documented as not touched.
- FMAE and regression notes are logged for meaningful changes.

## Test Command

Minimum for this docs overlay:

```bash
python3 scripts/build_agent_matchmaker.py
HTTP_ONLY=1 ./scripts/qa-reality-capture.sh
```

## ASLF (evidence-backed testing)

ASLF is a **process-first** layer: keep **why** tests ran and **what broke before** in [`docs/aslf/`](../aslf/README.md).

- Before deep changes to catalog, registry, exports, or `supabase-web/`, skim [`docs/aslf/REGRESSION_MEMORY.md`](../aslf/REGRESSION_MEMORY.md), [`FAILURE_PATTERNS.md`](../aslf/FAILURE_PATTERNS.md), and [`RISK_MAP.md`](../aslf/RISK_MAP.md).
- After a non-trivial fix or new test strategy, append [`TEST_DECISION_LOG.md`](../aslf/TEST_DECISION_LOG.md) and update regression or pattern docs when applicable.
- End-of-task prompts: [`QA_FEEDBACK_LOOP.md`](../aslf/QA_FEEDBACK_LOOP.md).

