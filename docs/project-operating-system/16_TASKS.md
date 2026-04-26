# Tasks

## MVP Definition

User can:

1. Browse/search/rank local agents.
2. Inspect agent source content.
3. Build or refresh the static catalog.
4. Optionally use Gemini-backed matching.
5. Opt into external source sync and registry/export workflows.

Success means the project remains locally usable and content-safe while improvements are made.

## Phase 0 - Project Definition

- [x] Define project identity in this operating-system folder.
- [x] Confirm overlay approach, not replacement.
- [x] Capture non-goals.
- [ ] Resolve future `supabase-web` role.

## Phase 1 - Documentation Integration

- [x] Add project operating-system docs.
- [x] Link docs from root README.
- [x] Add initial changelog entry.
- [x] Add ASLF QA memory under `docs/aslf/` (process-first; no ML).
- [ ] Review remaining `UNKNOWN` items.
- [ ] Keep `docs/aslf/RISK_MAP.md` and regression memory current when tooling or MVP scope shifts.

## Phase 2 - Current Workflow Protection

- [ ] Confirm catalog build command.
- [ ] Confirm HTTP-only QA command.
- [ ] Confirm registry commands after registry changes.
- [ ] Confirm export commands after exporter changes.

## Phase 3 - Future Registry/Product Work

- [ ] Decide if registry becomes matchmaker data source.
- [ ] Decide if `supabase-web` is public product UI, admin UI, or experiment.
- [ ] Add task-specific FMAE before runtime changes.

## Not Allowed Yet

- Full root restructure.
- Mandatory Supabase dependency.
- Enabling all external sources by default.
- Removing existing content categories.

