# Project Operating System

This folder adapts the agnostic app development template to this existing repo.
It is an overlay, not a replacement for the codebase.

## Purpose

Give future human and AI contributors one stable place to understand:

- What this project is now
- What must be preserved
- What the current MVP promises
- How code changes should be planned, tested, reviewed, and logged

## How to Use This Folder

1. Read `01_PROJECT_SNAPSHOT.md`.
2. Check `07_MVP_SCOPE.md` before adding scope.
3. Check `08_ARCHITECTURE.md`, `09_DATA_MODEL.md`, and `10_INTERFACES.md` before changing runtime behavior.
4. Use `13_TESTING.md`, `19_REGRESSION_CHECK.md`, and `25_QA_FMAE_PLAYBOOK.md` before and after meaningful changes.
5. Use [`docs/aslf/README.md`](../aslf/README.md) for ASLF QA memory: review regression and risk before risky edits; update logs after meaningful fixes or new test decisions.
6. Log meaningful changes in `22_CHANGELOG.md`.
7. Use `21_HANDOFF.md` before pausing or transferring work.

## Existing Codebase Protection

The template must not replace or flatten the current repo structure.

Preserve these existing areas unless a separate approved task says otherwise:

- Agent category directories such as `engineering/`, `marketing/`, `sales/`, `product/`, `strategy/`, and related content folders
- `agent-matchmaker/`
- `lib/`
- `scripts/`
- `data/`
- `docs/workflows/`
- `supabase-web/`
- Integration outputs and existing install/conversion workflows

## Build Gate

Before implementation, the change should have:

- Clear reason
- Smallest safe surface area
- Known working behavior to protect
- Regression check
- FMAE review for meaningful runtime/data/interface changes
- Changelog entry

