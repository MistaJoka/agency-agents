# Examples

## Good Change Request Shape

Change: update the matchmaker ranking logic.

Why: current results miss relevant agents for multi-agent project planning goals.

Working code to protect:

- Static catalog loading.
- Offline heuristic fallback.
- Existing source inspection.

Tests:

- Build catalog.
- Run HTTP-only QA.
- Manually search for known agents.
- Add FMAE for ranking failure modes.

## Bad Change Request Shape

"Move everything into a new app template and clean it up."

Why bad:

- It changes too much at once.
- It risks breaking links and scripts.
- It does not identify the user-visible improvement.
- It makes regression failures hard to isolate.

