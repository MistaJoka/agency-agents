# Decisions

## 2026-04-25 - Template Integration Strategy

Decision: adopt the agnostic app development template as a documentation and QA overlay under `docs/project-operating-system/`.

Reason: the template improves planning, regression discipline, FMAE review, and AI handoff quality, but its generic app skeleton does not match this repo's existing content-first structure.

Rejected option: replace the repo root with the template.

Why rejected: too much churn, likely broken links/scripts, and low benefit because the template is mostly empty scaffolding.

## 2026-04-25 - Core Project Posture

Decision: keep the project local-first for core catalog/matchmaker workflows.

Reason: static/local use is currently the most reliable and least complex path. Optional Gemini, registry sync, export packs, and future hosted UI remain additive.

## 2026-04-25 - ASLF QA Memory Layer

Decision: add an Adaptive Statistical Learning Framework (ASLF) as **process-only** documentation under `docs/aslf/`, plus light GitHub templates and optional `scripts/qa-log.sh`.

Reason: accumulate evidence from tests, CI, and incidents into structured logs so contributors and AI agents prioritize risk and avoid blind rewrites—without introducing ML or changing production behavior in this step.

Rejected option: automated ML on logs in-repo.

Why rejected: out of scope; start with smallest useful process layer.

