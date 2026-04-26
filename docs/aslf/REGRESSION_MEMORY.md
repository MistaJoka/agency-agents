# Regression memory

What must not break again. **Add** a row per guarded flow; update **Last verified** when re-checked.

---

## Regression Case — RC-001

- Feature/flow: Build static agent catalog and load matchmaker
- Previous failure: (none critical to date; operational QA noise documented in FP-001)
- Expected behavior: `python3 scripts/build_agent_matchmaker.py` succeeds; static matchmaker loads catalog; search works
- Guard test: `python3 scripts/build_agent_matchmaker.py` + `HTTP_ONLY=1 ./scripts/qa-reality-capture.sh` when tooling touched
- Manual check: Open matchmaker, search known agent, inspect source link
- Risk level: High (core MVP)
- Last verified: 2026-04-25 (per changelog)

---

## Regression Case — RC-002

- Feature/flow: Agent markdown lint on PR (category agent files)
- Previous failure: (document here when CI or local lint breaks on valid agents)
- Expected behavior: `scripts/lint-agents.sh` passes for changed agent `.md` files
- Guard test: Local run of `./scripts/lint-agents.sh <files>` before push; CI `lint-agents` workflow
- Manual check: n/a if CI green
- Risk level: Medium
- Last verified: (set when next verified)

---

## Regression Case — _Template_

- Feature/flow:
- Previous failure:
- Expected behavior:
- Guard test:
- Manual check:
- Risk level:
- Last verified:
