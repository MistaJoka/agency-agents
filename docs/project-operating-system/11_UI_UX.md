# UI / UX

## Visual UI

Yes. The current core UI is the static/local agent matchmaker. `supabase-web` is a separate experimental web UI.

## Design Goal

Make agent discovery fast, clear, and trustworthy.

## User Should Feel

They can quickly narrow a large agent catalog to relevant specialists and understand why a result is useful.

## Main Surfaces

- Agent matchmaker page.
- Source/details view.
- Local server/API-backed matching path.
- Documentation and workflow pages.

## First Interaction

Search, filter, or describe a project goal.

## Primary Action

Find agents.

## Secondary Actions

- Inspect source.
- Copy/use selected agent.
- Run local server for model-backed matching.
- Rebuild catalog after content changes.

## Empty State

Tell the user no agents matched and offer clear recovery: clear filters, broaden search, or rebuild catalog.

## Error State

Explain whether the failure is catalog loading, local server, API key/model, or source path related.

## Accessibility Basics

- Keep controls labeled.
- Preserve keyboard usability where practical.
- Avoid making API-backed matching the only route.
- Keep static/offline mode understandable.

## Unknowns

- Final visual direction for `supabase-web`.

