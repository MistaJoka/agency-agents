# QA feedback loop

Run after **every meaningful task** (especially tooling, data, or UI). Capture answers in PR description, changelog, or ASLF logs as appropriate.

## Questions

1. **What changed?** (paths, behavior, user-visible vs internal)
2. **What could break?** (catalog, registry, exports, matchmaker, CI, `supabase-web`)
3. **What evidence do we have?** (CI, local commands, issues, prior patterns)
4. **What test proves it still works?** (cite `13_TESTING.md` commands)
5. **What did we learn?** (one bullet for future contributors)
6. **What should future agents check first?** (point to `RISK_MAP.md` section or regression case ID)

## When to escalate to ASLF files

| If you discovered… | Update… |
|--------------------|---------|
| Same failure twice | `FAILURE_PATTERNS.md` |
| New guard for a fixed bug | `REGRESSION_MEMORY.md` |
| Non-obvious test choice | `TEST_DECISION_LOG.md` |
| New hot spot or unknown owner | `RISK_MAP.md` |

## Completion

Loop is **done** when questions 1–4 have answers, and 5–6 are recorded if non-trivial.
