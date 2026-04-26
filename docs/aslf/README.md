# ASLF — Adaptive Statistical Learning Framework (this repo)

## Purpose

ASLF here is **process-first**: turn **historical evidence** (CI output, test runs, bugs, manual QA, changelogs) into **durable, structured memory** so humans and AI agents test smarter, prioritize risk, and avoid repeating failures—**without** rewriting working code by default.

This is **not** a machine-learning model. It is a lightweight QA and learning loop backed by markdown logs.

## Evidence we use

- GitHub Actions logs (e.g. agent lint, Pages build)
- Local commands from [`docs/project-operating-system/13_TESTING.md`](../project-operating-system/13_TESTING.md)
- Issue and PR descriptions
- [`docs/project-operating-system/22_CHANGELOG.md`](../project-operating-system/22_CHANGELOG.md) and decisions in [`17_DECISIONS.md`](../project-operating-system/17_DECISIONS.md)
- Redacted snippets or summaries in [`evidence/`](evidence/) (optional; never commit secrets)
- Manual notes from matchmaker/catalog/registry checks

## How to use this folder

**Before changing code** (especially scripts, matchmaker, registry, exports, `supabase-web/`):

1. Skim [`REGRESSION_MEMORY.md`](REGRESSION_MEMORY.md)
2. Skim [`FAILURE_PATTERNS.md`](FAILURE_PATTERNS.md)
3. Skim [`RISK_MAP.md`](RISK_MAP.md)

**After changing code or closing a bug:**

1. Run checks from `13_TESTING.md` that match the risk area.
2. Log meaningful outcomes in [`TEST_DECISION_LOG.md`](TEST_DECISION_LOG.md) when test choice or results matter for the future.
3. If you fixed a defect or found a new recurring failure, update [`FAILURE_PATTERNS.md`](FAILURE_PATTERNS.md) and/or [`REGRESSION_MEMORY.md`](REGRESSION_MEMORY.md).
4. Refresh [`RISK_MAP.md`](RISK_MAP.md) when coverage, ownership, or fragility changes.
5. For every task wrap-up, use [`QA_FEEDBACK_LOOP.md`](QA_FEEDBACK_LOOP.md).

**Canonical workflow:** [`ASLF_PROCESS.md`](ASLF_PROCESS.md)

## Rules (non-negotiable)

- **Preserve working code.** No drive-by refactors.
- **No production behavior change** unless the task scope and evidence justify it.
- **Every code-facing recommendation should cite evidence** (issue, CI run, log path, changelog entry, or test output).
- **Do not delete** existing logs, QA artifacts, or docs; **append or amend** ASLF files instead.
- **Traceability:** tie updates to observed issue, affected area, test run, result, and follow-up decision (see templates in each file).

## Quick links

| File | Role |
|------|------|
| [`ASLF_PROCESS.md`](ASLF_PROCESS.md) | End-to-end loop and criteria |
| [`FAILURE_PATTERNS.md`](FAILURE_PATTERNS.md) | Recurring bugs / failures |
| [`TEST_DECISION_LOG.md`](TEST_DECISION_LOG.md) | Why tests were run or added |
| [`REGRESSION_MEMORY.md`](REGRESSION_MEMORY.md) | What must not break again |
| [`QA_FEEDBACK_LOOP.md`](QA_FEEDBACK_LOOP.md) | Post-task questions |
| [`RISK_MAP.md`](RISK_MAP.md) | Living risk map |
| [`evidence/README.md`](evidence/README.md) | How to store redacted evidence |

## Optional helper

Append a timestamped line to the session log (tracked):

```bash
./scripts/qa-log.sh "HTTP_ONLY QA passed after catalog rebuild"
```
