# Agent Matchmaker — QA sequences (forward + reverse)

Run these **on every** meaningful change to `agent-matchmaker/`, `scripts/build_agent_matchmaker.py`, or `scripts/qa-reality-capture.sh`.

**One-shot automation (recommended):** from repo root,

```bash
./scripts/qa-test-matrix.sh
```

That runs the **forward** block, then the **reverse** block (see script for exact order). Optional: `MATRIX_SKIP_GEMINI=1 ./scripts/qa-test-matrix.sh` if this machine has **no** Gemini key and you only want HTTP + Playwright.

---

## Forward sequence (baseline → deep evidence)

| Step | Intent | Command (repo root) |
|------|--------|----------------------|
| F0 | Fresh catalog + HTML | `python3 scripts/build_agent_matchmaker.py` |
| F1 | HTTP contract only (fast CI gate) | `HTTP_ONLY=1 ./scripts/qa-reality-capture.sh` |
| F2 | Layout + Playwright + PNGs | `./scripts/qa-reality-capture.sh` |
| F3 | Live `POST /api/match` (needs key + SDK on server) | `MATCH_SMOKE=1 MATCH_SMOKE_STRICT=1 HTTP_ONLY=1 ./scripts/qa-reality-capture.sh` |

**Evidence:** `agent-matchmaker/qa-screenshots/test-results.json` (and PNGs when F2 runs). Folder is gitignored.

**Interpretation:** `EVIDENCE_OK` in JSON means health + index markers + screenshots (and any enabled UI checks in `qa_reality_check.py`) passed. `NEEDS_WORK` with “HTTP evidence only” is expected when you only ran `HTTP_ONLY=1` without Playwright.

---

## Reverse sequence (stability / order independence)

Run the **same classes** of checks in **opposite order** to catch ordering assumptions, stale servers, or flaky env cleanup.

| Step | Intent | Command |
|------|--------|---------|
| R1 | Gemini smoke first | `MATCH_SMOKE=1 MATCH_SMOKE_STRICT=1 HTTP_ONLY=1 ./scripts/qa-reality-capture.sh` |
| R2 | Full Playwright pass | `./scripts/qa-reality-capture.sh` |
| R3 | HTTP-only again | `HTTP_ONLY=1 ./scripts/qa-reality-capture.sh` |
| R4 | Rebuild catalog again | `python3 scripts/build_agent_matchmaker.py` |

If **R1** is skipped (`MATRIX_SKIP_GEMINI=1`), start reverse at **R2**.

**Expected:** same overall pass/fail as forward; **R4** must still succeed (parseable `catalog.json`, non-zero agents).

---

## Manual pass (not fully automated)

Do once per release candidate (5–10 minutes):

1. Start app: `./scripts/run-agent-matchmaker.sh` (bash — **not** `python3` on the `.sh` file).
2. Open default URL; toggle **Smart match** if testing Gemini.
3. **Explore:** filter, category chips, row → dedicated **`#/agent/…`** profile; **Back**, **Esc**, peer link; **github** / **local** do not trigger row navigation.
4. **Workspace:** **Run**, **Clear**; optional filters popover.
5. Optional: paste goal, run offline + Gemini paths.

Cross-check failures against **`QA-FMEA.md`**.

---

## Prerequisites

- Repo-root **`.venv`** with `requirements-app.txt` + (for screenshots) `requirements-qa.txt` and `playwright install chromium`.
- For **F3 / R1:** `GEMINI_API_KEY` (or server key file) visible to the **same** process that runs `webapp.py`, or `MATCH_SMOKE_API_KEY` for the QA client body — see main **README** Reality / QA section.
