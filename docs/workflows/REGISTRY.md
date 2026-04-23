# Agent Matchmaker — Workflow Registry

Source of truth: `agent-matchmaker/webapp.py`, `agent-matchmaker/matchmaker_lib.py`, `scripts/build_agent_matchmaker.py`, `agent-matchmaker/index.template.html`, `scripts/run-agent-matchmaker.sh`.

---

## View 1 — By Workflow

| ID | Workflow | Primary Component | Entry Point | Spec |
|----|----------|-------------------|-------------|------|
| WF-01 | Server startup + catalog bootstrap | `webapp.py::main` | `python3 agent-matchmaker/webapp.py` | [WORKFLOW-01](./WORKFLOW-01-server-startup.md) |
| WF-02 | Catalog build (markdown → JSON → base64-embedded HTML) | `scripts/build_agent_matchmaker.py::main` | CLI / auto-invoked by `ensure_catalog_exists` | — |
| WF-03 | `GET /api/health` | `Handler.do_GET` | HTTP GET | — |
| WF-04 | `POST /api/match` — Gemini ranking happy path + failure modes | `Handler.do_POST` → `run_match_request` → `call_gemini` → `validate_and_merge` | HTTP POST | [WORKFLOW-04](./WORKFLOW-04-api-match.md) |
| WF-05 | API key resolution (request → env → key-file) | `_resolve_api_key_for_request`, `_api_key_from_environment`, `_read_first_nonempty_key_file`, `load_dotenv_repo` | Called per `/api/match` | — |
| WF-06 | Hallucination guard (filter unknown paths, dedupe, clamp fit_score) | `matchmaker_lib.validate_and_merge` | Post-Gemini | — |
| WF-07 | Frontend bootstrap (catalog load, health probe, runtime chip) | `index.template.html` IIFE | Page load | [WORKFLOW-07](./WORKFLOW-07-frontend-bootstrap.md) |
| WF-08 | Frontend submit — Gemini path (`renderGemini`) | `index.template.html::renderGemini` | Click "ask gemini" / Cmd+Enter | — |
| WF-09 | Frontend submit — offline heuristic (`render` + `scoreAgents`) | `index.template.html::render` | Click "find agents (offline)" | — |
| WF-10 | Frontend clear/reset state | `btn-clear` handler | Click "clear" | — |
| WF-11 | Gemini key persistence to `localStorage` | `persistGeminiKeyFromInput` | `apiKeyEl` blur | — |
| WF-12 | Runtime panel open/close + focus trap | `openRuntime`/`closeRuntime`/keydown Tab+Esc | Chip click / backdrop click / Esc | — |
| WF-13 | `file://` degraded mode (embedded catalog, heuristic only) | `loadCatalog` + `isFile` branch | Open `index.html` from disk | — |

---

## View 2 — By Component

### `webapp.py`
- WF-01 startup, `ensure_catalog_exists` guard, port bind
- WF-03 `/api/health` responder
- WF-04 `/api/match` request parsing, validation, dispatch
- WF-05 three-tier key resolution

### `matchmaker_lib.py`
- WF-02 (via `ensure_catalog_exists` shell-out) 
- `load_dotenv_repo` (merges `.env`, `.env.local`, `agent-matchmaker/.env`, later wins)
- `load_catalog` (lru_cache of `catalog.json`)
- `compact_agents` (truncate description to `DESC_MAX=700`)
- `call_gemini` (configures SDK, forces `response_mime_type=application/json`)
- WF-06 `validate_and_merge`
- `run_match_request` orchestration + category filter
- `github_url` / `local_url` link helpers

### `scripts/build_agent_matchmaker.py`
- WF-02 scan `AGENT_DIRS` → parse frontmatter → base64 embed → write `index.html` + `catalog.json`

### `index.template.html` (single-page IIFE)
- WF-07 bootstrap (catalog load precedence: `fetch(catalog.json)` → `window.__agentCatalogB64`)
- WF-08 Gemini path
- WF-09 heuristic path (`scoreAgents`, division & tag weights, multi-division orchestrator callout)
- WF-10 clear
- WF-11 localStorage key `agency-agents:matchmaker:gemini-api-key`
- WF-12 runtime modal
- WF-13 file:// detection

### `scripts/run-agent-matchmaker.sh`
- Wraps WF-01; sources `.env` and `agent-matchmaker/.env` into process env before exec

---

## View 3 — By User Journey

### J-A — First-time operator, has key in `.env`
1. `./scripts/run-agent-matchmaker.sh` → **WF-01** → catalog auto-builds via **WF-02** if missing → server on `127.0.0.1:8765`
2. Browser loads page → **WF-07** → `/api/health` reports `server_gemini_key:true` → chip = "key loaded", AI toggle auto-on
3. User types goal, clicks "ask gemini" → **WF-08** → `/api/match` → **WF-04** → **WF-05** picks `.env` key → **WF-06** filters hallucinated paths → cards render

### J-B — User with no server key, pastes key in UI
1. **WF-07** → health: `server_gemini_key:false` → chip = "no key", runtime modal auto-opens on toggle
2. User pastes key → blurred → **WF-11** persists to localStorage
3. Submit → **WF-08** → body includes `api_key` → **WF-05** uses request key first
4. Gemini success → render

### J-C — Offline / `file://` user
1. Open `agent-matchmaker/index.html` directly → **WF-13** → chip "off • file:// mode"
2. AI toggle disabled → Submit → **WF-09** heuristic scoring from embedded base64 catalog

### J-D — Server reachable but Gemini SDK missing
1. **WF-07** health reports `gemini_installed:false` → toggle disabled, chip "sdk missing"
2. Fallback to **WF-09**

### J-E — Gemini 5xx / timeout / invalid JSON mid-request
1. **WF-08** → **WF-04** → `call_gemini` raises → `run_match_request` returns `{ok:false,error:...}` → 400
2. UI shows error in meta strip; user can retry or uncheck AI toggle to use **WF-09**

### J-F — Gemini hallucinates agent paths
1. **WF-04** → **WF-06** drops unknown paths, appends `warnings` entries
2. UI meta displays joined warnings; only known agents render

---

## View 4 — By State

States observable from outside the system.

| State | Owner | Entered From | Exited By | Observable Signal |
|-------|-------|--------------|-----------|-------------------|
| `SERVER_DOWN` | webapp | not started / `SystemExit(1)` from missing catalog build | successful bind | fetch fails; UI meta: "server unreachable" |
| `SERVER_UP_NO_SDK` | webapp | bind with `genai is None` | pip install + restart | `/api/health` → `gemini_installed:false`; POST returns 503 |
| `SERVER_UP_NO_KEY` | webapp | bind with key files absent and env blank | write `.gemini_api_key` / `.env` + reload | `/api/health` → `server_gemini_key:false`; POST with no `api_key` → 400 |
| `SERVER_READY` | webapp | bind with SDK + key | shutdown (KeyboardInterrupt) | `/api/health.ok=true, gemini_installed=true, server_gemini_key=true` |
| `CATALOG_STALE` | filesystem | agent `.md` added but `catalog.json` not rebuilt | re-run `build_agent_matchmaker.py` | new agent absent from results |
| `CATALOG_MISSING` | filesystem | fresh checkout | `ensure_catalog_exists` auto-builds, else `SystemExit(1)` | startup error on stderr |
| `UI_IDLE` | browser | page load complete | submit / clear | meta: "waiting on your prompt…" |
| `UI_QUERYING` | browser | submit fired, `aria-busy=true`, btn disabled | response parsed / network error | meta: "querying gemini…" |
| `UI_ERROR` | browser | `res.ok=false` / `data.ok=false` / fetch throw / JSON parse throw | resubmit / clear | meta shows error; results empty card |
| `UI_RESULTS_GEMINI` | browser | `data.ok=true` | clear / new submit | cards with `N/100` fit scores, optional summary/orchestrator banner |
| `UI_RESULTS_HEURISTIC` | browser | offline path returns list | clear / new submit | cards labelled "score N" |
| `UI_FILE_MODE` | browser | `location.protocol==='file:'` | navigating to http URL | chip "file:// mode"; AI toggle disabled |
| `UI_RUNTIME_OPEN` | browser | chip click / AI toggle while `serverGeminiKeyCached=false` | backdrop click / Esc / chip re-click | modal visible, focus trapped |

---

## Specs produced

Top-3 specified in this pass (by blast radius / failure-mode density):

1. [WORKFLOW-04](./WORKFLOW-04-api-match.md) — `POST /api/match` end-to-end. Highest branching; touches key resolution, Gemini, hallucination guard, SDK-missing, catalog missing.
2. [WORKFLOW-01](./WORKFLOW-01-server-startup.md) — Startup + catalog bootstrap. Gates every other runtime workflow; can `SystemExit(1)` on two distinct failure modes.
3. [WORKFLOW-07](./WORKFLOW-07-frontend-bootstrap.md) — Frontend bootstrap. Determines whether user can see/use Gemini at all; three-way mode split (http+ready, http+degraded, file://).
