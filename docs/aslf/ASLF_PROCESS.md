# ASLF process — repeatable workflow

Pipeline:

```text
Observe → Record → Classify → Test → Learn → Prioritize → Prevent regression
```

Each stage below lists **purpose**, **inputs**, **outputs**, **examples**, and **completion criteria**.

---

## 1. Observe

**Purpose:** Catch signals early (CI red, user report, odd output, doc drift).

**Inputs:** PR checks, local script output, issues, manual matchmaker smoke, API errors.

**Outputs:** Raw notes, links, or redacted excerpts (see [`evidence/README.md`](evidence/README.md)).

**Examples:** `lint-agents.sh` fails on frontmatter; `build_agent_matchmaker.py` traceback; `qa-reality-capture.sh` port bind error.

**Completion criteria:** You can state *what* failed or worried you, *where* (path/job), and *when* (date or commit).

---

## 2. Record

**Purpose:** Make the signal durable and searchable.

**Inputs:** Observation notes, CI URLs, command lines, exit codes.

**Outputs:** New rows in [`FAILURE_PATTERNS.md`](FAILURE_PATTERNS.md) or [`TEST_DECISION_LOG.md`](TEST_DECISION_LOG.md); changelog entry if user-visible or process-critical; optional `./scripts/qa-log.sh "..."`.

**Examples:** Add a TEST_DECISION_LOG entry when you chose `HTTP_ONLY=1` QA after a catalog change.

**Completion criteria:** Another contributor could reproduce or verify from your record without asking you.

---

## 3. Classify

**Purpose:** Decide if this is one-off noise, recurring pattern, regression, or risk-map update.

**Inputs:** Record from step 2; git history; prior patterns.

**Outputs:** Tag: `one-off` | `pattern` | `regression` | `risk` | `doc-only`; link related files/commits.

**Examples:** Port `PermissionError` during QA classified as environmental flakiness vs. script bug—evidence drives the label.

**Completion criteria:** Classification is justified in one sentence with evidence.

---

## 4. Test

**Purpose:** Prove or disprove impact with the **smallest** relevant check set.

**Inputs:** `13_TESTING.md`, affected modules from `RISK_MAP.md`, guards from `REGRESSION_MEMORY.md`.

**Outputs:** Pass/fail, logs; new or updated tests/checks only when justified.

**Examples:** After export script change, run `export_cursor_pack.py --limit N` and catalog build.

**Completion criteria:** You ran (or consciously skipped with documented reason) checks mapped to the change.

---

## 5. Learn

**Purpose:** Extract a rule or heuristic for next time.

**Inputs:** Test results, root cause, side effects.

**Outputs:** Update `FAILURE_PATTERNS.md` (root cause, detection, fix), `QA_FEEDBACK_LOOP.md` answers for the task, optional `17_DECISIONS.md` if policy changes.

**Examples:** “Always rerun HTTP-only QA after `catalog.json` regeneration.”

**Completion criteria:** One concrete “next time we will…” statement exists.

---

## 6. Prioritize

**Purpose:** Focus effort on high-leverage areas.

**Inputs:** `RISK_MAP.md`, change frequency, external deps, weak coverage.

**Outputs:** Updated `RISK_MAP.md` sections; ordered follow-ups in tasks or issues.

**Examples:** Elevate `supabase-web` when it becomes primary UI; note “weak coverage” on new `lib/` module.

**Completion criteria:** Risk map reflects current reality or documents unknowns explicitly.

---

## 7. Prevent regression

**Purpose:** Ensure the same failure mode costs less next time.

**Inputs:** Regression case from step 5; guard test or manual checklist item.

**Outputs:** New or updated row in [`REGRESSION_MEMORY.md`](REGRESSION_MEMORY.md); automation only if cheap and safe.

**Examples:** Document “guard test: catalog build + HTTP_ONLY QA” for catalog pipeline changes.

**Completion criteria:** A named guard (automated or manual) exists and is linked to the failure mode.
