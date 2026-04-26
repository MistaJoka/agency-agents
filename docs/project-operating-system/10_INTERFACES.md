# Interfaces

## User-Facing Interfaces

- Markdown files and docs.
- Static matchmaker page.
- Local web app.
- Python scripts.
- Generated JSON/SQLite/export files.
- Experimental `supabase-web` UI.

## Main Actions

- Browse agents.
- Search/filter/rank agents.
- Build catalog.
- Run local matchmaker server.
- Sync enabled sources.
- Normalize source content.
- Export registry packs.
- Follow NEXUS strategy workflows.

## Screens / Pages

### Static Matchmaker

Purpose: browse and rank local agents.

Input: search text, filters, optional goal text.

Output: ranked/recommended agents and source references.

States: empty, loading, error, success.

## API Endpoints

### POST /api/match

Purpose: optional Gemini-backed ranking.

Input: goal, optional filters/model/API key.

Output: ranked recommendations or error/fallback.

### GET /api/agent-source

Purpose: return local agent source content for inspection.

Input: source path identifier.

Output: Markdown/source text or error.

## CLI / Script Interfaces

- `python3 scripts/build_agent_matchmaker.py`
- `python3 agent-matchmaker/webapp.py`
- `./scripts/run-agent-matchmaker.sh`
- `python3 scripts/sync_sources.py`
- `python3 scripts/normalize_sources.py`
- `python3 scripts/export_registry.py`
- `python3 scripts/export_cursor_pack.py`
- `HTTP_ONLY=1 ./scripts/qa-reality-capture.sh`

## Interface Rule

Keep static/local usage working even when optional APIs, remote source sync, or hosted app work are unavailable.

