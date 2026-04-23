# Agent Matchmaker (local)

**Docs:** [GOALS.md](GOALS.md) (polish vs replace vs MCP) · [RECOMMENDED_AGENTS.md](RECOMMENDED_AGENTS.md) (which Agency agents to activate while building this tool)

## GitHub Pages (public demo)

This repo includes a workflow ([`.github/workflows/github-pages.yml`](../.github/workflows/github-pages.yml)) that rebuilds the static `index.html` + `catalog.json` and deploys the `agent-matchmaker/` folder to [GitHub Pages](https://docs.github.com/en/pages).

1. In the repository on GitHub, open **Settings → Pages** (or **Environments** if prompted).
2. Under **Build and deployment**, set **Source** to **GitHub Actions** (not a branch / `docs` folder).
3. Push to `main` (or run the workflow manually). The live URL is typically `https://<user>.github.io/<repo>/` (project site), e.g. `https://yourname.github.io/agency-agents/`.

**On Pages:** search, heuristics, and the embedded catalog work in the browser. The **local-only** features still need your machine: `POST /api/match` (Gemini) and `GET /api/agent-source` require `python3 agent-matchmaker/webapp.py` on `http://127.0.0.1`, not a static host.

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

```bash
./scripts/run-agent-matchmaker.sh
```

Or:

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

- **One command (starts the server if needed, writes `agent-matchmaker/qa-screenshots/test-results.json`):**
  - `HTTP_ONLY=1 ./scripts/qa-reality-capture.sh` — HTTP + HTML marker checks (no extra deps).
  - `./scripts/qa-reality-capture.sh` — same, plus full-page PNGs when Playwright is available. The script uses **`./.venv/bin/python3`** when that path exists; otherwise it uses `python3` from your environment.
- If the app is already running: `NO_SERVER=1 ./scripts/qa-reality-capture.sh` (uses `BASE_URL`, default `http://127.0.0.1:8765`).
- Default readiness in JSON is **NEEDS_WORK** until both HTTP and visual runs succeed (matches an evidence-first integration review).

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
