# Handoff

## Current Project State

The repo is an AI agent catalog and tooling project with local/static matchmaker, optional Gemini matching, registry/import/export foundations, NEXUS strategy docs, and an experimental `supabase-web` app.

## Current Operating Rule

Use this folder as the project operating system. Do not use it to replace the codebase.

## Known Working Areas to Preserve

- Agent content directories.
- Matchmaker catalog and UI flow.
- Local web server.
- Registry source configuration and normalization scripts.
- Export pack scripts.
- Strategy and workflow docs.

## Before Next Major Change

1. Read `01_PROJECT_SNAPSHOT.md`.
2. Check `07_MVP_SCOPE.md`.
3. Check relevant architecture/interface docs.
4. Write a task note using `16_TASKS.md`.
5. Run or plan regression checks from `19_REGRESSION_CHECK.md`.
6. Log results in `22_CHANGELOG.md`.

## Open Questions

- What is the final role of `supabase-web`?
- Should the registry replace `catalog.json` as the live matchmaker data source?
- Which external sources should be officially supported?

