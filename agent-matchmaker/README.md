# Agent Matchmaker (local)

**Docs:** [GOALS.md](GOALS.md) (polish vs replace vs MCP) · [RECOMMENDED_AGENTS.md](RECOMMENDED_AGENTS.md) (which Agency agents to activate while building this tool)

## GitHub Pages (public demo)

This repo includes a workflow ([`.github/workflows/github-pages.yml`](../.github/workflows/github-pages.yml)) that rebuilds the static `index.html` + `catalog.json` and deploys the `agent-matchmaker/` folder to [GitHub Pages](https://docs.github.com/en/pages).

1. In the repository on GitHub, open **Settings → Pages** (or **Environments** if prompted).
2. Under **Build and deployment**, set **Source** to **GitHub Actions** (not a branch / `docs` folder).
3. Push to `main` (or run the workflow manually). The live URL is typically `https://<user>.github.io/<repo>/` (project site), e.g. `https://yourname.github.io/agency-agents/`.

**Hash routes (shareable agent pages):** deep links use the fragment only, so they work on project GitHub Pages without a server-side router: `#/agent/<url-encoded-repo-relative-path>`, e.g. `#/agent/engineering%2Fexample-agent.md`. API calls from the UI use the same origin-relative pattern as `resolveApi("/data/sources.json")` so paths stay correct under a project base URL (not only domain root).

**On Pages:** search, heuristics, and the embedded catalog work in the browser. The **local-only** features still need your machine: `POST /api/match` (Gemini) and `GET /api/agent-source` require `python3 agent-matchmaker/webapp.py` on `http://127.0.0.1`, not a static host.

**Catalog `source` field:** `python3 scripts/build_agent_matchmaker.py` embeds full markdown in each catalog entry as `source` so the dedicated agent view can render the profile without another fetch. Rebuild after editing agent files.

**Verify after deploy (dogfood):** open the published project URL (e.g. `https://<user>.github.io/<repo>/`), then a share link such as `https://<user>.github.io/<repo>/#/agent/<encoded-path>`. The Pages artifact uses `agent-matchmaker/` as the site **root** (not `/agent-matchmaker/`), so `resolveApi`/`catalog.json` and hash routing use the same origin as the index. Confirm the dedicated profile opens and the shell title returns after **Back** / **Esc**.

---

Two ways to pick agents from this repo:

1. **Static page** — open `agent-matchmaker/index.html` in a browser (offline, heuristic ranking). Regenerate with `python3 scripts/build_agent_matchmaker.py`.
2. **Local web app** — same UI served over HTTP; optional **Gemini** ranking via `POST /api/match` (recommended when you have a Google API key).

## Local web app

### Setup

```bash
cd /path/to/agency-agents
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r agent-matchmaker/requirements-app.txt
```

The app uses the **`google-genai`** package (`from google import genai`). Use **Python 3.10+** (required by current `google-genai` releases).

**`data/sources.json`:** with `webapp.py`, the UI fetches `GET /data/sources.json` (served from the repo `data/sources.json`). Offline/static `index.html` uses the embedded sources blob from the last `build_agent_matchmaker.py` run, so a 404 on a pure static host does not block the explore UI.

For Gemini, set an API key (either name is accepted by the Google SDK):

```bash
export GEMINI_API_KEY="your-key"
# or
export GOOGLE_API_KEY="your-key"
```

Optional: create a **repo-root** `.env` file:

```env
GEMINI_API_KEY=your-key
```

The server loads `.env` automatically via `python-dotenv`.

Ensure the catalog exists (created automatically on first launch if missing, or run manually):

```bash
python3 scripts/build_agent_matchmaker.py
```

### Run

`run-agent-matchmaker.sh` is a **bash** script. Run it with the shell, not with `python3` (using `python3` on that path will raise `SyntaxError`).

```bash
./scripts/run-agent-matchmaker.sh
# or: bash ./scripts/run-agent-matchmaker.sh
# If ./… is “permission denied”: chmod +x scripts/run-agent-matchmaker.sh
# Python-only runners: python3 scripts/run_agent_matchmaker.py
```

Or start Python directly (same app, no `.env` sourcing from the shell wrapper):

```bash
python3 agent-matchmaker/webapp.py
```

Then open **http://127.0.0.1:8765/** (default). Use `--port` / `--host` if you need different values.

### Usage

- Leave **Smart match (Gemini)** off for fast offline-style heuristic ranking (no key).
- Turn **Smart match (Gemini)** on, add your goal and optional divisions, then **Find agents**. You can paste an API key in the form, or rely on `GEMINI_API_KEY` / `.env` on the machine running `webapp.py`.

After adding or editing agent markdown files, rebuild the catalog:

```bash
python3 scripts/build_agent_matchmaker.py
```

If a model name errors (API lists change), choose another in the form (defaults to `gemini-2.5-flash`; `gemini-1.5-flash` is a common fallback).

## Reality / QA (evidence, not fantasy)

- **Failure modes + sequences (run every meaningful test pass):** [QA-FMEA.md](QA-FMEA.md) (what can break and how to catch it) · [QA-SEQUENCE.md](QA-SEQUENCE.md) (forward + reverse steps). **Full matrix (forward then reverse):** `./scripts/qa-test-matrix.sh` from repo root. Use `MATRIX_SKIP_GEMINI=1 ./scripts/qa-test-matrix.sh` when no API key is configured (skips strict `POST /api/match` steps).
- **One command (starts the server if needed, writes `agent-matchmaker/qa-screenshots/test-results.json`):**
  - `HTTP_ONLY=1 ./scripts/qa-reality-capture.sh` — HTTP + HTML marker checks (no Playwright, no browser flows).
  - `./scripts/qa-reality-capture.sh` — adds full-page PNGs, horizontal-overflow checks, and **scripted Playwright UI flows** (hash `#/agent/…`, dedicated overlay, copy / use-in-matchmaker / view full markdown, Back/Esc, invalid hash, explore `github`/`local` link regression) when Playwright is installed. The script uses **`./.venv/bin/python3`** when that path exists; otherwise it uses `python3` from your environment.
- If the app is already running: `NO_SERVER=1 ./scripts/qa-reality-capture.sh` (uses `BASE_URL`, default `http://127.0.0.1:8765`).
- **Recommended CI matrix (from repo root):** quick gate `HTTP_ONLY=1`; full UI evidence `./scripts/qa-reality-capture.sh` (Playwright + PNGs + flows); optional Gemini `MATCH_SMOKE=1 MATCH_SMOKE_STRICT=1 HTTP_ONLY=1 ./scripts/qa-reality-capture.sh` when a key is available (strict makes skipped smoke a failure).
- Default readiness in JSON is **NEEDS_WORK** until HTTP, screenshots, and UI flows all succeed (or you only run `HTTP_ONLY` and accept the stricter “evidence” note in JSON).
- **CI:** [`.github/workflows/agent-matchmaker-qa.yml`](../.github/workflows/agent-matchmaker-qa.yml) runs the same Playwright + HTTP checks on pushes/PRs (paths under `agent-matchmaker/` and related scripts). Optional manual Gemini smoke: [`.github/workflows/agent-matchmaker-gemini-smoke.yml`](../.github/workflows/agent-matchmaker-gemini-smoke.yml) (set repo secret `GEMINI_API_KEY`).

- **Gemini end-to-end (optional):** `MATCH_SMOKE=1 ./scripts/qa-reality-capture.sh` adds a `POST /api/match` call with a tiny goal. The server must run with **`google-genai`** installed (`requirements-app.txt`) and expose an API key to the server process, **or** you set `GEMINI_API_KEY` / `GOOGLE_API_KEY` / `MATCH_SMOKE_API_KEY` in the environment when running QA so the client can send `api_key` in the JSON body. If smoke cannot run (no Gemini on server, no key), status is **skipped** and the script still exits **0** unless `MATCH_SMOKE_STRICT=1`. For CI gates, use **`MATCH_SMOKE_STRICT=1`**: then skipped or failed smoke exits **non-zero** and downgrades the JSON verdict. Direct: `python3 agent-matchmaker/qa_reality_check.py --match-smoke [--match-smoke-strict]`.

### QA virtualenv (macOS / Homebrew Python, PEP 668)

System Python often refuses `pip install` with **externally-managed-environment**. Use a virtualenv in the repo root.

**Recommended: one `.venv` for the app and QA** (matches `qa-reality-capture.sh`):

```bash
cd /path/to/agency-agents
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r agent-matchmaker/requirements-app.txt -r agent-matchmaker/requirements-qa.txt
python3 -m playwright install chromium
```

Then `./scripts/qa-reality-capture.sh`, or with the server already up: `NO_SERVER=1 ./scripts/qa-reality-capture.sh`.

**Optional: QA-only venv** (Playwright only, separate from app deps). Use e.g. `.venv-qa` (ignored by git in this repo). Start the matchmaker elsewhere (another terminal with `requirements-app.txt`, or `./scripts/run-agent-matchmaker.sh`), then:

```bash
cd /path/to/agency-agents
python3 -m venv .venv-qa
source .venv-qa/bin/activate
pip install -r agent-matchmaker/requirements-qa.txt
python3 -m playwright install chromium
NO_SERVER=1 ./scripts/qa-reality-capture.sh
# or: python3 agent-matchmaker/qa_reality_check.py --base-url http://127.0.0.1:8765
```

`qa-reality-capture.sh` only auto-picks `./.venv/bin/python3`. With `.venv-qa` active and no `./.venv`, the script falls back to **`python3` on your PATH** (the activated venv), so `NO_SERVER=1 ./scripts/qa-reality-capture.sh` works after `source .venv-qa/bin/activate`. If both `.venv` and `.venv-qa` exist, remove or rename `.venv` for that shell session, or invoke `qa_reality_check.py` directly with `.venv-qa/bin/python3`.
