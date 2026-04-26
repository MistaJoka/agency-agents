# WORKFLOW-14 — Team Builder, saved workflows, registry + plan APIs

## Overview

Users compose an **ordered sequence** of catalog agents and registry items (skills / imported agents), optionally ask Gemini for a suggested order, and **persist** named workflows in `localStorage`. Supporting HTTP endpoints expose registry metadata and Gemini plan generation when `webapp.py` runs.

## Storage (browser)

| Key | Purpose |
|-----|---------|
| `agency-agents:workflows:v1` | JSON array of saved workflow documents |
| `agency-agents:team-draft:v1` | In-progress draft: goal, steps, editing id/title |

### Workflow document shape

- `schemaVersion` (number, currently `1`)
- `id` (string), `title`, `goal` (optional), `createdAt`, `updatedAt` (ISO strings)
- `steps`: array of `{ stepId, ordinal, kind: "agent" \| "skill", refId, titleSnapshot, note }`
  - **agent** `refId`: catalog `path` (e.g. `engineering/foo.md`)
  - **skill** (or registry-only agent): `refId`: `registry_items.id` from SQLite

Export/import: single workflow JSON or array; import merges by `id`.

## HTTP (local server)

### `GET /api/registry-items`

- **Handler:** `webapp.py::Handler.do_GET`
- **Logic:** `matchmaker_lib.fetch_registry_metadata()` — metadata columns only, no raw markdown
- **Response:** `{ "ok": true, "items": [ ... ] }`; empty `items` if `data/registry.sqlite` is missing or unreadable

### `POST /api/plan-sequence`

- **Handler:** `webapp.py::Handler.do_POST` (same Gemini key rules as `/api/match`)
- **Body:** `goal` (required), optional `categories`, `extra`, `api_key`, `model`, `temperature`, `source_ids`, `max_steps`
- **Logic:** `matchmaker_lib.run_plan_sequence_request` → `call_gemini` with `PLAN_SEQUENCE_INSTRUCTION` → `validate_plan_sequence` (unknown `ref_id` dropped, dedupe, cap)
- **Response:** `{ "ok": true, "summary", "steps", "warnings" }` or `{ "ok": false, "error" }`

### `GET /api/health` extension

- Adds `registry_items_count` (length of metadata fetch) for quick diagnostics.

## Frontend

- **Source:** `agent-matchmaker/index.template.html` (rebuild with `scripts/build_agent_matchmaker.py`)
- **Team Builder (main workspace):** Inside `div.wrap` / `#workspace-route-team` — pick list (catalog + registry), ordered steps with notes, Gemini suggest, clear/save/export/import. Sidebar **Team Builder** nav switches masthead + hides the matchmaker bento (`#workspace-route-matchmaker`).
- **Workflows panel:** Sidebar list — load in builder (switches main workspace to team), duplicate, delete, export, import
- **Explore:** each row has **team** — adds agent, switches main workspace to team builder, opens sidebar stub panel

## QA (manual)

1. Run `python3 agent-matchmaker/webapp.py`, open the app, open **Team Builder**.
2. Add steps from the pick list; reorder and remove; reload page — draft should restore from `agency-agents:team-draft:v1`.
3. **Save workflow**, open **Workflows**, **Load in builder**, edit, save again — same id should update.
4. **Export** JSON and **Import** on another tab — workflows merge.
5. With `data/registry.sqlite` present (after `normalize_sources.py`), confirm registry rows appear in the pick list and `GET /api/registry-items` returns them.
6. With Gemini configured, **Suggest order (Gemini)** fills the sequence; unknown ids should appear only in `warnings`, not as steps.
