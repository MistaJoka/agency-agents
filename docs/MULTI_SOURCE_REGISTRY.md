# Multi-source agent registry (Phases 1–2)

## Problem

The Agency matchmaker today compiles **this** repository’s agent markdown into `agent-matchmaker/catalog.json`. We want a **multi-source registry**: many upstream packs (and local trees) with shared provenance, without merging foreign repos into one big codebase.

## Why external sources are disabled by default

Cloning every listed repo would be slow, noisy, and can surprise people on a fresh machine. `data/sources.json` ships with `enabled: false` for every **non-local** source so **nothing** is fetched until you opt in.

## How to enable a source

1. Edit `data/sources.json`.
2. Set `"enabled": true` for the source you want.
3. Run `python3 scripts/sync_sources.py` to clone or update that tree under `data/imported_sources/<id>/`.
4. Run `python3 scripts/normalize_sources.py` to refresh `data/registry.sqlite`.

Disable again by setting `"enabled": false`; you can delete `data/imported_sources/<id>/` to reclaim disk (safe—re-clone on next sync).

## How sync works

- `python3 scripts/sync_sources.py` loads `data/sources.json`.
- **Disabled** sources: skipped.
- **Local** source (`"local": true`): no `git` operations; the current checkout is the source (same tree `build_agent_matchmaker.py` already scans).
- **Remote** source: `git clone` if missing, else `git pull --ff-only` in `data/imported_sources/{id}/` (no forced resets or destructive history rewrites in Phase 1).

## How normalization works

- `python3 scripts/normalize_sources.py` walks **enabled** sources.
- The markdown normalizer reads `.md` files, prefers YAML **frontmatter** with at least `name` and `description` (same spirit as the matchmaker’s agent files), and skips obvious top-level doc files (README, LICENSE, etc.) during discovery where applicable.
- Optional per-source **`item_glob`**: e.g. `claude-skills` uses `"**/SKILL.md"` so only pack skill entry files are ingested, not every `references/*.md` helper doc.
- Rows are written to **`data/registry.sqlite`** with a stable id of `source_id:path/to/file.md`.

**JSON export (optional):** `python3 scripts/export_registry.py` writes `data/registry_export.json` (gitignored). Use `--metadata-only` to drop large body fields. Same data as the DB—useful for search, CI, and future pack exporters.

**Cursor pack (optional):** `python3 scripts/export_cursor_pack.py` writes `data/export_packs/cursor/rules/*.mdc` (gitignored) using the same rule shape as `./scripts/convert.sh` for Cursor. Options: `--source-id claude-skills`, `--clear`, `--limit N` for a quick test. Copy the folder into a project’s `.cursor/rules` or use your global rules path.

**Not** the live matchmaker index: the UI still uses `scripts/build_agent_matchmaker.py` → `agent-matchmaker/catalog.json` until a later phase wires the registry in.

## Connection to `agent-matchmaker`

| Piece | Role |
| --- | --- |
| `scripts/build_agent_matchmaker.py` | **Current** product path: `AGENT_DIRS` → `catalog.json` + `index.html`. Unchanged in behavior. |
| `data/sources.json` + importers + `registry.sqlite` | **Foundation** for additional packs and future export packs. |

Shared layout for “where agency agents live” is centralized in `lib/agent_layout.py` so the catalog build and the local source discovery stay aligned.

## Phase 2 (current)

- **`claude-skills` is enabled** in `data/sources.json` and syncs to `data/imported_sources/claude-skills/` (gitignored clone).
- Normalization uses the same row shape as local agents; skills typically get `item_type` `skill` in SQLite (no `color` in frontmatter).
- **Matchmaker UI still reads only** `build_agent_matchmaker.py` **→** `catalog.json` (local agency tree). Registry is for pipelines / future UI / exports.

**Rollback:** set `"enabled": false` for `claude-skills`, run `sync_sources.py` (no-op for disabled), remove `data/imported_sources/claude-skills` if you want disk back; re-run `normalize_sources.py` to drop those rows from `registry.sqlite`.

## Future phases (planned)

- Export packs: `lib/exporters/` for Cursor / Codex / Claude Code bundles.
- Optional merge or filter views in the app without forking all upstream code into this repo.
