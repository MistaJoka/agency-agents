# WORKFLOW-04 — `POST /api/match`

## Overview
Synchronous HTTP endpoint that accepts a user goal and returns a Gemini-ranked list of matching sub-agents drawn from a fixed catalog. Applies a hallucination guard so only paths known to `catalog.json` are returned. Produces a self-contained JSON payload; frontend consumes it to render cards.

Source: `agent-matchmaker/webapp.py::Handler.do_POST`, `matchmaker_lib.run_match_request`, `matchmaker_lib.call_gemini`, `matchmaker_lib.validate_and_merge`.

## Actors
| Actor | Role |
|-------|------|
| Browser (frontend IIFE, `renderGemini`) | Issues POST, renders result |
| `ThreadingHTTPServer` + `Handler` | Parses request, dispatches |
| `matchmaker_lib.run_match_request` | Builds prompt payload, calls Gemini, merges |
| `matchmaker_lib.call_gemini` | Configures `google.genai` client (`google-genai` package), invokes `gemini-2.5-flash` |
| Google Gemini API | LLM ranker |
| `validate_and_merge` | Hallucination guard + shape enforcement |
| `catalog.json` | Source-of-truth agent index |

## Prerequisites
- Server in state `SERVER_READY` or `SERVER_UP_NO_KEY` (SDK imported; key may be absent if request supplies one).
- `catalog.json` exists (guaranteed by WORKFLOW-01 or raises earlier).
- Network egress to `generativelanguage.googleapis.com`.
- Content-Type is JSON; `Content-Length` honest (Handler reads exactly that many bytes).

## Trigger
Any `POST /api/match` request. Browser triggers occur on "ask gemini" button click or Cmd/Ctrl+Enter on the goal textarea (guarded by `geminiAvailable()`).

## Workflow Tree

### Step 1 — Path + SDK gate
- Actor: `Handler.do_POST`
- Action: compare `urlparse(path).path` to `/api/match`; check `genai is not None`.
- Timeout: n/a (local)
- Input: raw request line
- SUCCESS: proceed
- FAILURE: path mismatch → `404`; `genai is None` → `503 {"ok":false,"error":"Install: pip install -r agent-matchmaker/requirements-app.txt"}`
- Observable: response code; no Gemini call attempted

### Step 2 — Refresh env, parse JSON body
- Actor: `Handler.do_POST`
- Action: `load_dotenv_repo()` (merges `.env` / `.env.local` / `agent-matchmaker/.env`; later overrides), read `Content-Length` bytes, `json.loads`.
- Timeout: bounded by socket read (no explicit timeout set)
- Input: headers + body
- SUCCESS: dict `body`
- FAILURE: `json.JSONDecodeError` → `400 {"error":"Invalid JSON body"}`; missing/zero `Content-Length` → parses `b"{}"` → `goal` check catches
- Observable: 400 on malformed JSON

### Step 3 — Goal validation
- Actor: `Handler.do_POST`
- Action: `(body.get("goal") or "").strip()` must be truthy.
- Input: `body["goal"]`
- SUCCESS: non-empty `goal`
- FAILURE: → `400 {"error":"Missing goal"}`

### Step 4 — API key resolution (see WF-05)
- Actor: `_resolve_api_key_for_request`
- Action: precedence: `body.api_key` → env (`GEMINI_API_KEY`, `GOOGLE_API_KEY`, `GOOGLE_GENERATIVE_AI_API_KEY`) → key file (`$GEMINI_API_KEY_FILE`, `REPO_ROOT/.gemini_api_key`, `APP_DIR/.gemini_api_key`).
- SUCCESS: non-empty key
- FAILURE: → `400` with remediation text ("put your key in `.gemini_api_key` …")
- Observable: verbose error in `data.error`

### Step 5 — Input normalization
- Actor: `Handler.do_POST`
- Action: coerce `categories` (non-list → `None`; list → filtered to strings), `extra` (non-str → `None`), `model` (default `gemini-2.5-flash`), `temperature` (default `0.25` on `TypeError`/`ValueError`), `github_base` (body → env `AGENCY_GITHUB_BASE` → hardcoded default).
- SUCCESS: sanitized kwargs
- FAILURE: none — all failure paths silently coerce

### Step 6 — Category pool filter + payload build
- Actor: `run_match_request`
- Action: load catalog (lru-cached), filter by `categories` if present, `compact_agents` truncates descriptions to 700 chars.
- SUCCESS: `payload` with `agents_in_prompt_count`
- FAILURE: empty pool → `{"ok":false,"error":"No agents in the selected divisions…"}` → serialized as `400` in Step 9
- Observable: `400` with "clear filters" message

### Step 7 — Gemini call
- Actor: `call_gemini`
- Action: `genai.configure(api_key=…)`, instantiate `GenerativeModel` with `SYSTEM_INSTRUCTION`, `generate_content` with `response_mime_type="application/json"`, temperature.
- Timeout: **none set in code** — relies on SDK/library default (see Open Questions)
- SUCCESS: parsed dict from `json.loads(resp.text)`
- FAILURE modes:
  - `resp.candidates` empty → `RuntimeError("No response from model (blocked or empty)")`
  - `resp.text` empty → `RuntimeError("Empty model response")`
  - Model returned non-JSON / malformed JSON → `json.JSONDecodeError` → `run_match_request` returns `{"ok":false,"error":"Model returned invalid JSON: …"}` → `400`
  - Any other SDK exception (network, 5xx, auth rejected, rate limit) → caught by broad `except Exception` in `run_match_request` → `{"ok":false,"error":"Request failed: …"}` → `400`
  - Exception not caught there (e.g. raised before the try block) → Handler's outer `except Exception` → `500`
- Observable: UI meta shows `data.error`

### Step 8 — Hallucination guard
- Actor: `validate_and_merge`
- Action: drop entries missing `.md` suffix, strip `"./"` prefix, dedupe, drop paths not in `catalog_by_path` (appended to `warnings`), clamp `fit_score` 0–100, enrich with `name/emoji/vibe` from catalog.
- SUCCESS: merged list + warnings
- FAILURE: `matches` not a list → warnings=`["Model returned no matches array; showing raw summary only."]`; response still `ok:true` but matches=[]
- Observable: `data.warnings` surfaced in UI meta

### Step 9 — Serialize + respond
- Actor: `Handler.do_POST`
- Action: `HTTPStatus.OK` if `result["ok"]` else `400`; JSON body with `Cache-Control: no-store`.
- SUCCESS: `200 {"ok":true, summary, suggest_agents_orchestrator, orchestrator_rationale, matches, warnings, github_base}`
- FAILURE: any uncaught exception in Steps 6–8 → `500 {"ok":false,"error":str(e)}`

## ABORT_CLEANUP
None. Request is stateless; no resources to release beyond HTTP socket (auto). Threading server isolates concurrent requests. `load_catalog` lru_cache persists deliberately across requests — no cleanup.

## State Transitions

```
UI_IDLE
  └─ submit ──► UI_QUERYING
                  ├─ 200 ok:true + matches ──► UI_RESULTS_GEMINI
                  ├─ 200 ok:true + empty matches ──► UI_RESULTS_GEMINI (empty-state card)
                  ├─ 400 ok:false ──► UI_ERROR (meta = data.error)
                  ├─ 503 SDK missing ──► UI_ERROR
                  ├─ 500 ──► UI_ERROR
                  └─ fetch throws ──► UI_ERROR (meta = "server unreachable…")
```

## Handoff Contracts

### Request body (JSON)
| Field | Type | Required | Default |
|-------|------|----------|---------|
| `goal` | string | yes | — |
| `categories` | string[] \| null | no | all categories |
| `extra` | string | no | null |
| `api_key` | string | no | server-side resolution |
| `model` | string | no | `gemini-2.5-flash` |
| `temperature` | number | no | `0.25` |
| `github_base` | string | no | env `AGENCY_GITHUB_BASE` or hardcoded default |

### Response body (JSON) — success
```
{
  "ok": true,
  "summary": string|null,
  "suggest_agents_orchestrator": bool|null,
  "orchestrator_rationale": string|null,
  "matches": [{ "path", "fit_score" (0-100), "why", "caveat", "name", "emoji", "vibe" }],
  "warnings": string[],
  "github_base": string (trailing slash)
}
```

### Response body — failure
`{ "ok": false, "error": string }` at codes 400 / 500 / 503.

## Cleanup Inventory
| Resource | Lifetime | Cleanup |
|----------|----------|---------|
| HTTP socket | per-request | stdlib `BaseHTTPRequestHandler` handles |
| `genai` global config | process lifetime | `genai.configure` re-runs per request — last caller wins; OK since single key per request |
| `load_catalog` lru_cache | process lifetime | cleared only by `ensure_catalog_exists` on initial build |

## Test Cases
| # | Scenario | Expected |
|---|----------|----------|
| T1 | Happy path: `{goal:"ship a saas landing page"}`, env key present | 200, `matches.length ∈ [6,12]`, no warnings |
| T2 | Missing goal | 400 "Missing goal" |
| T3 | Malformed JSON body | 400 "Invalid JSON body" |
| T4 | No key anywhere, no `api_key` in body | 400 remediation message |
| T5 | `genai` not importable | 503 "Install: pip install…" |
| T6 | `categories:["nonexistent-division"]` | 400 "No agents in the selected divisions…" |
| T7 | Gemini returns paths not in catalog | 200, unknown entries dropped, warnings populated |
| T8 | Gemini returns matches not a list | 200, `matches=[]`, warning "no matches array" |
| T9 | Gemini raises (network down) | 400 "Request failed: …" |
| T10 | Gemini returns non-JSON text | 400 "Model returned invalid JSON: …" |
| T11 | `temperature:"hot"` | coerced to 0.25; 200 |
| T12 | `categories:"not-a-list"` | coerced to None (all categories); 200 |
| T13 | Key from request body overrides env | 200; env key not used |
| T14 | Concurrent 10 requests | all succeed independently (ThreadingHTTPServer) |
| T15 | Gemini returns `fit_score: 9999` | clamped to 100 |
| T16 | Gemini returns duplicate paths | deduped, first wins |
| T17 | Path `"./engineering/foo.md"` from Gemini | normalized (`.lstrip("./")`) and accepted if in catalog |
| T18 | Path without `.md` suffix | silently dropped (no warning) — see Open Questions |

## Assumptions
| # | Assumption | Impact if wrong |
|---|------------|-----------------|
| A1 | `google.genai` client (timeout behavior per Google SDK) | Slow/hung Gemini blocks a server thread; no client-side kill |
| A2 | Client `Content-Length` is accurate | Under-read → invalid JSON; over-read → hang |
| A3 | Gemini obeys `response_mime_type="application/json"` and `SYSTEM_INSTRUCTION` schema | Increased hallucination-guard warnings; possible `JSONDecodeError` |
| A4 | `catalog.json` entries all carry unique `path` | Merge dedupe is the only defense against dupes in catalog itself |
| A5 | Environment merges in `load_dotenv_repo` (override=True) are safe each request | Edits to `.env` apply mid-run without restart; intended |
| A6 | Empty-pool error is user-facing enough at HTTP 400 | If clients treat 400 as bug, they miss "clear filters" remediation |
| A7 | 500 path only for pre-Gemini exceptions; Gemini errors map to 400 via `run_match_request` | Mis-categorized errors may mislead ops |

## Open Questions
- Q1: No explicit timeout on `model.generate_content`. Should we wrap with `concurrent.futures` or set SDK `request_options={"timeout":…}`? Currently a slow Gemini call ties up a thread indefinitely.
- Q2: Silent drop of entries without `.md` suffix is not warned. Should `validate_and_merge` append a warning for those too?
- Q3: Broad `except Exception` in `run_match_request` loses stack trace. Should we log server-side while returning the sanitized message?
- Q4: `genai.configure` is a global; concurrent requests with different `api_key` values race. Should we use per-request client instances once SDK supports it?
- Q5: `github_base` default hardcodes `msitarzewski/agency-agents`, but the live fork may be different. Env var is the escape hatch; is that documented?
