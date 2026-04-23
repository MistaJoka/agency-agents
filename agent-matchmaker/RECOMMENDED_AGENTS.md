# Recommended Agency agents for this app

When extending the Agent Matchmaker or building a companion “use this repo” tool, activate these specialists in **Claude Code**, **Cursor**, or any tool that reads agents from this repository. Paths are relative to the repo root.

## Spec and coordination

| Agent | Path |
| --- | --- |
| Agents Orchestrator | `specialized/agents-orchestrator.md` |
| Workflow Architect | `specialized/specialized-workflow-architect.md` |
| Product Manager | `product/product-manager.md` |

**Example prompt (Claude Code / generic):**  
“Use the Agents Orchestrator and Workflow Architect: define milestones for improving the Agent Matchmaker (search, filters, copy path, optional MCP). Use the Product Manager to keep scope to polish unless I say otherwise.”

## Build and UI

| Agent | Path |
| --- | --- |
| Rapid Prototyper | `engineering/engineering-rapid-prototyper.md` |
| Frontend Developer | `engineering/engineering-frontend-developer.md` |
| Minimal Change Engineer | `engineering/engineering-minimal-change-engineer.md` |

**Example prompt:**  
“Use the Rapid Prototyper and Frontend Developer for the matchmaker UI. Use the Minimal Change Engineer for edits to `scripts/build_agent_matchmaker.py` and `matchmaker_lib.py`.”

## Server, security, and release

| Agent | Path |
| --- | --- |
| Backend Architect | `engineering/engineering-backend-architect.md` |
| Security Engineer | `engineering/engineering-security-engineer.md` |
| DevOps Automator | `engineering/engineering-devops-automator.md` |

**Example prompt:**  
“Use the Security Engineer to review `webapp.py` (path handling, API key handling, subprocess catalog build). Use the Backend Architect only if we add persistence or split modules.”

## Before sharing beyond localhost

| Agent | Path |
| --- | --- |
| Security Engineer | `engineering/engineering-security-engineer.md` |
| Reality Checker | `testing/testing-reality-checker.md` |

**Example prompt:**  
“Use the Reality Checker and Security Engineer: is this safe to bind to LAN or production? List blockers.”

## Quality and docs

| Agent | Path |
| --- | --- |
| Codebase Onboarding Engineer | `engineering/engineering-codebase-onboarding-engineer.md` |
| Technical Writer | `engineering/engineering-technical-writer.md` |
| Code Reviewer | `engineering/engineering-code-reviewer.md` |
| Reality Checker | `testing/testing-reality-checker.md` |
| Evidence Collector | `testing/testing-evidence-collector.md` |

## Optional: IDE integration (MCP)

| Agent | Path |
| --- | --- |
| MCP Builder | `specialized/specialized-mcp-builder.md` |

**Example prompt:**  
“Use the MCP Builder: design an MCP server that wraps catalog load + heuristic or Gemini match from `agent-matchmaker/matchmaker_lib.py`, returning ranked `path` strings for the chat session.”

## Secondary (when scope fits)

- **Tool Evaluator** — `testing/testing-tool-evaluator.md` — comparing install targets or tooling.
- **Git Workflow Master** — `engineering/engineering-git-workflow-master.md` — automation around catalog commits.
- **ZK Steward** — `specialized/zk-steward.md` — personal notes on which agent worked for which task.
