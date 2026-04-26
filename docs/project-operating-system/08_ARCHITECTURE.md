# Architecture

## Simple Overview

The repo is a content-first agent library with build scripts, a local/static matchmaker, registry tooling, strategy docs, and an experimental web app.

## Runtime Types

- Static browser page
- Local Python web server
- CLI-style Python scripts
- Optional external LLM API call
- Vite/React app under `supabase-web`

## System Parts

- Content: agent Markdown directories and strategy/workflow docs.
- Static matchmaker: `agent-matchmaker/index.html` plus `catalog.json`.
- Local server: `agent-matchmaker/webapp.py`.
- Catalog builder: `scripts/build_agent_matchmaker.py`.
- Registry foundation: `data/sources.json`, `lib/`, `scripts/sync_sources.py`, `scripts/normalize_sources.py`.
- Exporters: `lib/exporters/` and related scripts.
- Experimental web app: `supabase-web/`.

## Data Flow

1. Agent Markdown is scanned from known content directories.
2. Catalog builder creates `agent-matchmaker/catalog.json` and static HTML.
3. Static UI loads the catalog for offline search/ranking.
4. Local server can optionally call Gemini for smarter ranking.
5. Enabled external sources can sync into `data/imported_sources/`.
6. Normalization writes registry rows into `data/registry.sqlite`.
7. Export scripts create tool-specific packs from registry data.

## Local-First or Cloud-First

Local-first for the current core product.

## Offline Support

Static matchmaker and local catalog browsing should work without network access once files are present. Gemini matching and remote source sync require external access/API credentials.

## Scaling Concern

Primary scaling issues are catalog size, source provenance, sync time, and UI search performance, not high-traffic backend scale yet.

## Unknowns

- Whether `supabase-web` becomes the primary hosted UI.
- Whether registry data replaces `catalog.json` as the live matchmaker source.

