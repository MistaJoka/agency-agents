# AI Agent Instructions

## Role

You are working in an existing content-first agent catalog and tooling repo. Preserve working content and local workflows.

## Priorities

1. Protect curated agent content.
2. Keep local/static usage working.
3. Keep optional integrations optional.
4. Make small, well-reasoned changes.
5. Use FMAE and regression checks for meaningful runtime/data/interface changes.

## Do Not

- Replace the repo with a generic template.
- Move content directories unless explicitly requested.
- Enable remote source fetching by default.
- Store secrets in tracked files.
- Rewrite working scripts just because a cleaner pattern exists.
- Treat `supabase-web` as the primary product until that decision is made.

## Required Before Meaningful Edits

- State what already works.
- State what will change.
- State why the change is needed.
- Identify tests/checks.
- Add or update changelog notes.
- For tooling or runtime-impacting work, review ASLF memory: [`docs/aslf/REGRESSION_MEMORY.md`](../aslf/REGRESSION_MEMORY.md), [`FAILURE_PATTERNS.md`](../aslf/FAILURE_PATTERNS.md), [`RISK_MAP.md`](../aslf/RISK_MAP.md), then update those logs after fixes or new patterns ([`docs/aslf/README.md`](../aslf/README.md)).

## Required Review Passes

1. Forward pass: user action to result.
2. Backward pass: promised result to required dependencies.
3. Cohesion pass: names, paths, data, UI, scripts, docs, and tests agree.

