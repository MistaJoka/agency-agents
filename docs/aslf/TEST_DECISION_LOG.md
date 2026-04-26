# Test decision log

Why tests were run or skipped, and what we learned. **Append** new decisions.

---

## Decision ID — TD-001 (example)

- Date: 2026-04-25
- Change/issue: Project operating system documentation overlay
- Risk area: README links, matchmaker static catalog still loads
- Evidence: Changelog entry; need to prove catalog build + HTTP QA still valid
- Tests selected: `python3 scripts/build_agent_matchmaker.py`, `HTTP_ONLY=1 ./scripts/qa-reality-capture.sh`
- Why these tests: Cover catalog generation and basic matchmaker HTTP behavior per `13_TESTING.md`
- Result: Pass after rerun; initial QA run hit port permission issue (see `FAILURE_PATTERNS.md` FP-001)
- Follow-up: Document environmental flakiness; do not rewrite QA script without stronger evidence

---

## Decision ID — _Template_

- Date:
- Change/issue:
- Risk area:
- Evidence:
- Tests selected:
- Why these tests:
- Result:
- Follow-up:
