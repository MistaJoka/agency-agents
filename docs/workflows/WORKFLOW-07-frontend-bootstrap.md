# WORKFLOW-07 — Frontend bootstrap

## Overview
Single-page IIFE that runs once per page load in `index.template.html` (and its built twin `index.html`). Loads the agent catalog, probes `/api/health`, initializes the "gemini chip" runtime indicator, restores a persisted API key from `localStorage`, wires up form controls and keyboard shortcuts, and chooses between three operating modes: `file://` offline, `http` with healthy Gemini, `http` degraded.

Source: `agent-matchmaker/index.template.html` lines 1140–1757 (IIFE).

## Actors
| Actor | Role |
|-------|------|
| Browser (user agent) | Executes the IIFE |
| `loadCatalog` | Chooses source (`fetch(catalog.json)` vs embedded base64) |
| `fetch /api/health` | Probes server SDK + key availability |
| `localStorage[agency-agents:matchmaker:gemini-api-key]` | Client-side persisted key |
| DOM elements | `#goal`, `#api-key`, `#use-ai-ranking`, `#gemini-chip`, `#ai-advanced-details`, results, filters |
| Operator-configured server | Provides `/api/health` + `/api/match` |

## Prerequisites
- `index.html` reached via `http(s)://` (full mode) or `file://` (degraded mode).
- For `http` mode: webapp running (WF-01 complete).
- Base64 catalog placeholder `__AGENT_CATALOG_B64__` populated at build time by `scripts/build_agent_matchmaker.py` (consumed as `window.__agentCatalogB64`).

## Trigger
Page load / reload; IIFE self-invokes at end of `<script>`.

## Workflow Tree

### Step 1 — Detect protocol
- Actor: IIFE
- Action: `isFile = window.location.protocol === "file:"`
- Output: routes catalog load and disables AI toggle in `file://`

### Step 2 — Load catalog
- Actor: `loadCatalog()`
- Action:
  - If `http(s):` → `fetch("catalog.json")`. On `r.ok` and array non-empty, use it.
  - On error / non-OK / empty / `file://` → decode `window.__agentCatalogB64` via `atob` + `JSON.parse`.
- SUCCESS: `CATALOG` = array of agent objects
- FAILURE:
  - `fetch` rejects (network) → silently falls back to embedded
  - Embedded base64 missing/invalid → returns `[]` → UI renders "no catalog loaded" once a heuristic match is attempted (no explicit empty-state warning before submit)
- Observable: category checkboxes populate from `[...new Set(CATALOG.map(a=>a.category))]`; empty catalog = empty division box

### Step 3 — Populate filters + focus tags
- Actor: IIFE
- Action: build checkboxes for divisions (`DIVISION_LABELS`) and focus tags (`FOCUS_TAGS`); bind `change` → `updateFilterBadge`.
- SUCCESS: UI populated
- FAILURE: empty `CATALOG` → no division checkboxes (tags still appear)

### Step 4 — Restore persisted API key
- Actor: IIFE
- Action: if `!isFile && #api-key` exists, read `localStorage[LS_GEMINI]`, populate input; bind `blur` → `persistGeminiKeyFromInput`.
- FAILURE: localStorage blocked (private mode) → caught silently, input left blank

### Step 5 — Runtime modal wiring
- Actor: IIFE
- Action: bind chip click, backdrop click, close button; install document keydown handler for Esc + Tab focus trap over `FOCUSABLE_SEL`.
- SUCCESS: modal toggles predictably
- FAILURE: missing DOM nodes → null-guards short-circuit; no exception

### Step 6 — `file://` branch
- Condition: `isFile`
- Action: `setGeminiChip("off","file:// mode")`; disable and uncheck `#use-ai-ranking`; show `#gemini-hint-file`.
- Outcome: state `UI_FILE_MODE` — submit routes to heuristic only.

### Step 7 — `http` health probe
- Condition: `!isFile && #ai-server-status && #use-ai-ranking`
- Action: `fetch("/api/health", {cache:"no-store"})`.
  - Non-OK response → chip `err`/"unreachable", leave toggle state default.
  - OK + `gemini_installed:false` → message: "install gemini…"; disable+uncheck toggle; chip `err`/"sdk missing".
  - OK + `gemini_installed:true, server_gemini_key:true` → auto-check toggle; chip `ready`/"key loaded".
  - OK + no key → uncheck toggle; message: "no server key — add .gemini_api_key / GEMINI_API_KEY, or paste one under runtime"; chip `needkey`/"no key".
  - Fetch throws (server down) → chip `err`/"unreachable"; status text suggests `python3 agent-matchmaker/webapp.py`.
- SUCCESS: `serverGeminiKeyCached`, `geminiInstalledCached` set; `updateMatchButton()` sets button label ("ask gemini" vs "find agents (offline)")
- FAILURE: caught by `.catch`

### Step 8 — Wire submit controls
- Actor: IIFE
- Action:
  - `#use-ai-ranking change`: if checked AND http AND no server key → auto-open runtime modal (prompts user to paste key). If unchecked → close modal. Always call `updateMatchButton`.
  - `#temp input`: update `#temp-val` text.
  - `#goal keydown`: Cmd/Ctrl+Enter triggers `#btn-match` click if not disabled.
  - `#btn-match click`: dispatch to `renderGemini()` if `geminiAvailable()` else `render()`; finally scroll matches into view on narrow viewports (unless `prefers-reduced-motion`).
  - `#btn-clear click`: reset fields, clear localStorage key, reset toggle to `serverGeminiKeyCached`, close modal, reset model/temperature/filter checkboxes, clear results/meta/summary/orchestrator banners.

### Step 9 — Idle state
- Meta strip: "waiting on your prompt — describe what you're shipping."
- UI state: `UI_IDLE` (or `UI_FILE_MODE`).

## ABORT_CLEANUP
None — bootstrap is synchronous/idempotent within the page. Navigating away discards everything.

## State Transitions
```
(page load) ─► CATALOG_LOADED ─► FILTERS_BUILT ─► KEY_RESTORED ─► MODAL_WIRED
     │
     ├─ file:// ──────────────► UI_FILE_MODE (idle)
     └─ http ── health.then ─┬─ ok + key ──────► UI_IDLE (chip ready, AI on)
                             ├─ ok + no key ───► UI_IDLE (chip needkey, AI off)
                             ├─ ok + no SDK ───► UI_IDLE (chip err, AI disabled)
                             └─ fetch catch ───► UI_IDLE (chip err, AI off)
```

## Handoff Contracts

### From build script
- `window.__agentCatalogB64` is base64 of the catalog JSON. Template placeholder: `__AGENT_CATALOG_B64__`.
- `catalog.json` served by webapp at `/catalog.json` (same directory served by `SimpleHTTPRequestHandler`).

### To submit workflows (WF-08 / WF-09)
- `geminiAvailable()` returns `!isFile && geminiInstalledCached && useAiRankingEl.checked` — gates `renderGemini` vs `render`.
- `serverGeminiKeyCached` influences clear/reset toggle default.

### To `/api/health`
Consumed fields: `ok` (bool), `gemini_installed` (bool), `server_gemini_key` (bool). Any missing field treated as falsy.

## Cleanup Inventory
| Resource | Lifetime | Cleanup |
|----------|----------|---------|
| Event listeners (chip, backdrop, keydown, form) | page lifetime | browser GC on navigate |
| `localStorage[LS_GEMINI]` | persists | cleared by `#btn-clear` or manual removal |
| Fetched catalog array | page lifetime | GC on navigate |

## Test Cases
| # | Scenario | Expected |
|---|----------|----------|
| T1 | Load over http, server ready with key | Chip "key loaded", AI toggle on, button "ask gemini" |
| T2 | Load over http, server up, no key | Chip "no key", toggle off, clicking toggle opens runtime modal |
| T3 | Load over http, server up, no SDK | Chip "sdk missing", toggle disabled |
| T4 | Load over http, server down | Chip "unreachable", status text suggests starting webapp |
| T5 | Load `file://index.html` | Chip "file:// mode", toggle disabled, embedded catalog used |
| T6 | Corrupt `__agentCatalogB64` | `JSON.parse` throws, caught → empty catalog → no divisions render |
| T7 | `fetch(catalog.json)` returns 200 with `{}` (not array) | Falls back to embedded catalog |
| T8 | `localStorage` disabled (private mode) | Key restore silent-fails; blur persist silent-fails; input still usable per session |
| T9 | Cmd+Enter in goal textarea | Triggers `#btn-match` click if enabled |
| T10 | Narrow viewport (<960px) post-submit | Smooth scroll to results (respects `prefers-reduced-motion`) |
| T11 | Focus trap: Tab at last focusable in modal | Wraps to first |
| T12 | Esc with modal open | Closes modal, returns focus to chip if focus was inside |
| T13 | Clear button with persisted key | `localStorage` entry removed, input blanked |
| T14 | `/api/health` returns malformed JSON | `.json()` rejects → `.catch` → chip "unreachable" |

## Assumptions
| # | Assumption | Impact if wrong |
|---|------------|-----------------|
| A1 | `catalog.json` served at same origin as HTML | Cross-origin fetch without CORS would fall to embedded — silently stale |
| A2 | Embedded catalog and live `catalog.json` both valid JSON | Corrupt embed → empty UI; corrupt live → falls back to embed (may be stale) |
| A3 | `localStorage` is appropriate for a Gemini API key | Secret stored client-side; xss risk; any other page on same origin can read it |
| A4 | `/api/health` is cheap enough to call on every page load | Re-runs `load_dotenv_repo` server-side; acceptable |
| A5 | `prefers-reduced-motion` captured once at load (not live) | User toggling OS setting mid-session not reflected |
| A6 | DOM elements in the template remain stable IDs | Template refactor without updating IIFE silently breaks features |
| A7 | Base64-embedded catalog fits in HTML without overrunning parser limits | With hundreds of agents, HTML payload balloons but remains under typical limits |

## Open Questions
- Q1: Should an empty catalog produce a visible banner at bootstrap, not wait until submit?
- Q2: Should the persisted key in `localStorage` be redacted (e.g. stored only when user explicitly opts in)? Currently auto-persisted on blur.
- Q3: Should the AI toggle auto-checking when server has a key be configurable? Some users may want opt-in always.
- Q4: On `/api/health` transient failure (first load race with server startup), there's no retry. Is a single-try probe acceptable UX?
- Q5: `setGeminiChip("err","unreachable")` is shown even if `fetch` rejects on an extension-blocked request — indistinguishable from server-down. Worth disambiguating?
