# WORKFLOW-01 — Server startup + catalog bootstrap

## Overview
One-shot boot sequence for `webapp.py`. Merges `.env` files, verifies `catalog.json` exists (building it from agent markdown if not), prints diagnostic credentials state, and binds a `ThreadingHTTPServer`. Every other runtime workflow depends on this completing.

Source: `agent-matchmaker/webapp.py::main`, `matchmaker_lib.ensure_catalog_exists`, `matchmaker_lib.load_dotenv_repo`, `scripts/run-agent-matchmaker.sh`, `scripts/build_agent_matchmaker.py`.

## Actors
| Actor | Role |
|-------|------|
| Operator | Invokes `./scripts/run-agent-matchmaker.sh` or `python3 agent-matchmaker/webapp.py` |
| `run-agent-matchmaker.sh` | Sources `.env` files into process env before exec |
| `webapp.main` | Parses `--host/--port`, orchestrates boot |
| `matchmaker_lib.ensure_catalog_exists` | Shells out to build script if `catalog.json` missing |
| `scripts/build_agent_matchmaker.py` | Scans `AGENT_DIRS`, writes `catalog.json` + `index.html` |
| `ThreadingHTTPServer` | Listens on `host:port` |

## Prerequisites
- Python 3 available at `python3`.
- `pip install -r agent-matchmaker/requirements-app.txt` (optional — server still starts without `google-genai`, but `/api/match` returns 503 until installed).
- At least one agent markdown file with valid frontmatter under one of `AGENT_DIRS` if catalog needs building.
- `agent-matchmaker/index.template.html` present (for initial build).

## Trigger
Operator runs `python3 agent-matchmaker/webapp.py [--host HOST] [--port PORT]` or the wrapper shell script.

## Workflow Tree

### Step 1 — Load env files (pre-main, via wrapper)
- Actor: `run-agent-matchmaker.sh`
- Action: `set -a; . .env; . agent-matchmaker/.env; set +a`
- SUCCESS: env exported to Python process
- FAILURE: file missing → silently skipped (guarded by `[[ -f … ]]`); malformed `.env` → shell syntax error, script aborts via `set -e`

### Step 2 — `main()` re-merges env for in-process guarantees
- Actor: `webapp.main` → `load_dotenv_repo`
- Action: iterate `REPO_ROOT/.env`, `REPO_ROOT/.env.local`, `APP_DIR/.env`; `load_dotenv(path, override=True)` so later files win.
- SUCCESS: env populated
- FAILURE: `python-dotenv` not installed → `load_dotenv is None` → skipped silently (`.env` keys only picked up via shell wrapper)

### Step 3 — Parse CLI args
- Actor: `argparse`
- Action: `--host` (default `127.0.0.1`), `--port` int (default `8765`).
- FAILURE: invalid types → argparse writes to stderr, exits 2

### Step 4 — Ensure catalog
- Actor: `ensure_catalog_exists`
- Action: if `APP_DIR/catalog.json` exists → return. Else invoke `python3 scripts/build_agent_matchmaker.py` with `cwd=REPO_ROOT`, `check=True`. On success, `load_catalog.cache_clear()`.
- Timeout: none (subprocess runs to completion; fast in practice)
- SUCCESS: `catalog.json` present
- FAILURE modes:
  - Build script missing → `FileNotFoundError` → caught in `main`, printed to stderr, `SystemExit(1)`
  - Build script exits non-zero (e.g. no agents found, template missing `__AGENT_CATALOG_B64__` placeholder, output dir unwritable) → `CalledProcessError` → `SystemExit(1)` with "Could not build catalog"
  - Silent edge: some agent `.md` files lack required `name/description/color` frontmatter → skipped individually; if *all* skipped → build prints "No agents found" and exits 1

### Step 5 — Credential probe (informational only)
- Actor: `main`
- Action: compute `_gemini_ready = bool(_api_key_from_environment() or _read_first_nonempty_key_file())`.
- SUCCESS: flag used only to decide startup log message
- FAILURE: never fails startup — no key is a valid `SERVER_UP_NO_KEY` state

### Step 6 — Bind socket
- Actor: `ThreadingHTTPServer((host, port), Handler)`
- Action: `bind()` + `listen()`.
- SUCCESS: prints `Serving {APP_DIR}` and open URL; prints Gemini status hint
- FAILURE modes:
  - Port already in use → `OSError: [Errno 48] Address already in use` → **uncaught**, traceback to stderr, exit 1
  - Privileged port without perms → `PermissionError` → uncaught, exit 1
  - Host invalid → `socket.gaierror` → uncaught

### Step 7 — Serve forever
- Actor: `httpd.serve_forever`
- SUCCESS: request handling loop; state = `SERVER_READY` or `SERVER_UP_NO_KEY` / `SERVER_UP_NO_SDK`
- FAILURE: `KeyboardInterrupt` caught, prints `\nStopped.`, process exits 0. Other exceptions bubble up; socket left to OS.

## ABORT_CLEANUP
- On `SystemExit(1)` in Step 4: no socket bound; nothing to clean.
- On Step 6 bind failure: nothing to clean.
- On KeyboardInterrupt (Step 7): `httpd.server_close()` is **not** called explicitly — relies on process exit to release the socket. Rapid restart on same port usually OK due to `SO_REUSEADDR`, but Darwin may briefly refuse.

## State Transitions
```
(init) ─► ENV_LOADED ─► ARGS_PARSED ─► CATALOG_READY
                                         │
                                         ├─ bind fail ─► (exit 1)
                                         │
                                         └─► LISTENING
                                                 ├─ SDK absent ─► SERVER_UP_NO_SDK
                                                 ├─ SDK+no key ─► SERVER_UP_NO_KEY
                                                 └─ SDK+key ──── ► SERVER_READY
                                                                     │
                                                                     └─ SIGINT ─► (exit 0)
```

## Handoff Contracts

### To `/api/health` (WF-03)
Reads `genai is not None`, and (`_server_has_gemini_credentials()`) — which re-runs `load_dotenv_repo` each call, so mid-run `.env` edits propagate to the chip.

### To `/api/match` (WF-04)
Relies on `catalog.json` being present (Step 4 guarantee) and `load_catalog` succeeding.

### From build script
`scripts/build_agent_matchmaker.py` writes both `agent-matchmaker/catalog.json` and `agent-matchmaker/index.html` (template + base64 catalog). Startup only requires `catalog.json`; `index.html` is consumed by the browser later.

## Cleanup Inventory
| Resource | Lifetime | Cleanup |
|----------|----------|---------|
| TCP listening socket | process lifetime | implicit on exit (no `server_close()`) |
| Subprocess for catalog build | one-shot | `subprocess.run` blocks until complete |
| dotenv overrides in `os.environ` | process lifetime | none — process exit |
| `load_catalog` lru_cache | process lifetime | `cache_clear()` after fresh build only |

## Test Cases
| # | Scenario | Expected |
|---|----------|----------|
| T1 | Fresh clone, no `catalog.json`, script present | Build runs, `catalog.json` written, server listens |
| T2 | `catalog.json` already present | Build skipped; server listens |
| T3 | `scripts/build_agent_matchmaker.py` deleted | `FileNotFoundError` → exit 1 with clear message |
| T4 | Template missing placeholder | `CalledProcessError` → exit 1 "Could not build catalog" |
| T5 | All agent frontmatter invalid | Build exits 1 ("No agents found"); server never starts |
| T6 | Port 8765 already bound | Uncaught `OSError`, traceback, exit 1 |
| T7 | `--port 80` as non-root | PermissionError traceback |
| T8 | `--host 0.0.0.0` | Binds on all interfaces; health reachable from LAN |
| T9 | No Gemini SDK installed | Server starts; stderr hint; `/api/match` later returns 503 |
| T10 | No key anywhere | Server starts; stderr "no key yet" hint; `SERVER_UP_NO_KEY` |
| T11 | Key only in `agent-matchmaker/.env` | `load_dotenv_repo` override ensures it wins |
| T12 | SIGINT during serve | Prints "Stopped.", exit 0 |

## Assumptions
| # | Assumption | Impact if wrong |
|---|------------|-----------------|
| A1 | `sys.executable` (the interpreter running webapp) is usable to run build script | Build could fail on exotic venv setups |
| A2 | `cwd=REPO_ROOT` during build is the only cwd needed | Build script also uses absolute paths via `REPO_ROOT` constant, so robust |
| A3 | Operator is fine with uncaught socket errors on port conflict | Poor UX; could be improved with explicit try/except |
| A4 | `.env` files don't contain shell-active constructs that break the wrapper's `set -a` source | Malformed `.env` will abort before Python runs |
| A5 | `python-dotenv` optional — wrapper shell handles env when it's not installed | Running `python3 webapp.py` directly without wrapper and without dotenv installed means `.env` not loaded |
| A6 | Catalog-build subprocess returns fast (<few seconds) | No timeout; catastrophic if scan hangs on a mounted network FS |

## Open Questions
- Q1: Should port-in-use be caught and reported as a friendly message with suggested `--port`?
- Q2: Should `httpd.server_close()` be called in `finally` to release the socket deterministically?
- Q3: Is `ensure_catalog_exists` re-run intentionally skipped when `catalog.json` is present but stale (new agents added since last build)? Currently yes — operator must re-run build script manually.
- Q4: On `FileNotFoundError` in Step 4, should the error message include how to regenerate the script / where to get it?
