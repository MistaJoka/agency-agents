# Data Model

## Does This App Store Data?

Yes, mostly file-based and local generated data.

## Main Entities

- Agent
- Source
- Registry item
- Export pack
- Match request
- Strategy/playbook document

## Agent

Fields include name, description, category/division, source path, tags/keywords where available, and Markdown body.

Purpose: represent a specialist AI role or workflow unit.

## Source

Fields include source id, type, enabled flag, local/remote location, and optional item glob.

Purpose: define where importable agent/skill content comes from.

## Registry Item

Fields include stable id, source id, source path, item type, metadata, and body.

Purpose: normalize local and external content into a common registry shape.

## Export Pack

Generated output for a target tool or format.

Purpose: make registry content usable outside this repo.

## Stored Data

- Markdown source files.
- `agent-matchmaker/catalog.json`.
- `data/sources.json`.
- `data/registry.sqlite` when generated.
- Generated exports under ignored output paths.

## Sensitive Data

API keys such as Gemini/Google keys must stay in environment variables or untracked `.env` files.

## Import / Export Needs

External sources must remain opt-in. Exports should preserve source/provenance enough to debug where content came from.

## Unknowns

- Final schema expectations for any Supabase-backed data.

