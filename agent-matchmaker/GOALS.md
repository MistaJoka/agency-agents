# Agent Matchmaker — product goals

Use this file to record **which direction** you are taking the local “use this repo” experience. Pick one primary track; others can be stretch goals.

## Default: polish (recommended)

Improve the existing static page + `webapp.py` flow: UX, filters, copy-to-clipboard, docs, and safety for localhost. No rewrite of the catalog pipeline unless needed.

**Baseline verified (repeat anytime):**

1. `python3 scripts/build_agent_matchmaker.py` — writes `catalog.json` and `index.html`.
2. Open `agent-matchmaker/index.html` in a browser (fully offline), or run `./scripts/run-agent-matchmaker.sh` and open `http://127.0.0.1:8765/`.
3. Optional: `curl -s http://127.0.0.1:8765/api/health` — expect `{"ok": true, ...}` when the server is running (Gemini fields depend on installed packages).

## Replace

Greenfield or alternate UI/runtime (e.g. different framework) while **keeping** `catalog.json` generation from `scripts/build_agent_matchmaker.py` unless you intentionally fork the schema.

## MCP stretch

Expose ranked agent picks to your IDE via Model Context Protocol so chat can call the same logic as `matchmaker_lib.run_match_request` / heuristics without opening the browser. See [RECOMMENDED_AGENTS.md](RECOMMENDED_AGENTS.md) for the **MCP Builder** specialist when you choose this track.

---

**Current focus (edit when you decide):** polish