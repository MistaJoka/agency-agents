# MVP Scope

## MVP Goal

Preserve and improve the existing agent catalog, local matchmaker, registry foundations, and documentation while keeping local use simple.

## User Can Do These Things

1. Browse and search local agents.
2. Run/build the matchmaker catalog.
3. Use optional Gemini matching locally.
4. Enable selected external sources and normalize them into the registry.
5. Export registry content into supported pack formats.

## MVP Does Not Include

- Full repo restructuring.
- Mandatory Supabase usage.
- Paid accounts or billing.
- Cloud-only operation.
- Enabling every external source by default.

## MVP Success Means

The repo can be used locally, core commands are documented, curated content remains intact, and future changes have a regression/FMAE path.

## MVP Failure Means

Users cannot build or browse the catalog, source links break, registry scripts lose provenance, or changes overwrite curated content.

## Maximum Complexity Allowed

Moderate. Keep core local usage simple; isolate advanced registry and web-app work.

## Launch Condition

The MVP is ready when:

- Static/local matchmaker flows are documented and checked.
- Registry commands are documented and reversible.
- README points to this operating-system folder.
- FMAE/regression checklist exists for meaningful future changes.

