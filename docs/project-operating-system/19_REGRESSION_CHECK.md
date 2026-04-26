# Regression Check

Use this before and after meaningful changes.

## Working Code Lock

Before editing, identify:

- What already works.
- How it is checked.
- Which files should not be touched.
- Smallest safe change.
- Rollback path.

## Core Flows to Protect

- Agent Markdown remains in existing category directories.
- `scripts/build_agent_matchmaker.py` can rebuild the matchmaker catalog.
- Static `agent-matchmaker/index.html` can load catalog data.
- Local server can serve matchmaker routes.
- Optional Gemini matching failure does not break offline matching.
- Registry sync remains opt-in.
- Registry normalization preserves source ids and paths.
- Export scripts do not require unrelated runtime changes.

## Minimum Regression Commands

```bash
python3 scripts/build_agent_matchmaker.py
HTTP_ONLY=1 ./scripts/qa-reality-capture.sh
```

## Additional Checks by Area

- Matchmaker UI change: run full QA capture when Playwright is available.
- Registry change: run sync/normalize/export commands with a small enabled source set.
- Exporter change: inspect generated output under ignored export paths.
- `supabase-web` change: run `npm run build` in `supabase-web`.
- Security/API change: complete FMAE table in `25_QA_FMAE_PLAYBOOK.md` or the task notes.

## Pass/Fail Logging

Record in `22_CHANGELOG.md`:

- Commands run.
- Result.
- Failures.
- Fixes.
- Remaining risk.

