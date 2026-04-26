# Risk map (living document)

Update when architecture, ownership, or test coverage changes. Mark **UNKNOWN** instead of guessing.

## High-risk files / modules

| Area | Why | Guard |
|------|-----|-------|
| `scripts/build_agent_matchmaker.py` | Drives `agent-matchmaker/catalog.json` and static UI | Catalog build + smoke per `REGRESSION_MEMORY` RC-001 |
| `agent-matchmaker/` (generated + static assets) | User-facing browse/search | HTTP-only or full QA script |
| `lib/` normalizers, registry, exporters | Data shape and provenance | Commands in `13_TESTING.md` for touched surface |
| `.github/workflows/lint-agents.yml` + `scripts/lint-agents.sh` | PR gate for agent content | CI + local lint on changed files |

## Fragile flows

- Optional Gemini / external API paths — fail closed; keys not in repo
- Full Playwright/visual QA — environment-dependent (see FP-001)
- Registry sync / multi-source imports — fewer automated tests; treat as high scrutiny

## Frequently changed areas

- Agent category `*.md` files (volume + merge conflicts)
- `agent-matchmaker/catalog.json` when rebuild committed after agent adds

## Weak test coverage (gaps)

- No unified `pytest` / `vitest` suite at repo root for all Python/TS
- `supabase-web`: lint + build only; no `npm test` in `package.json` yet
- `lib/` and importers: rely on manual script runs and integration habits

## Unclear ownership

- **`supabase-web` product role** — see `docs/project-operating-system/16_TASKS.md` (UNKNOWN until decided)
- Long-term registry vs matchmaker source of truth — decision pending

## External APIs / services

- Gemini (optional matchmaker)
- Supabase client in `supabase-web` (hosted project configuration not in repo)
- GitHub Actions runners (CI availability)

## UI flows needing manual visual QA

- Matchmaker layout, search, ranking UI after HTML/CSS/JS changes
- `supabase-web` screens after React/CSS changes

---

**Review cadence:** skim this file before large PRs; update in the same PR when you change risk profile.
