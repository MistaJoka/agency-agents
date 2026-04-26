# Agent Matchmaker — FMEA (failure modes)

Use this during **every** test pass: scan for these modes, confirm detection, and record mitigations in your PR or release notes.

| ID | Failure mode | User / system effect | Likely cause | How you detect it | Mitigation |
|----|----------------|----------------------|--------------|-------------------|------------|
| F1 | Missing or corrupt `catalog.json` | Empty or broken catalog | No build, bad deploy, partial clone | Build script errors; JSON parse fails; QA index markers fail | Run `python3 scripts/build_agent_matchmaker.py`; fix CI |
| F2 | `index.html` out of sync with `index.template.html` | Drift, missing UI | Edited template, forgot rebuild | Diff; QA substring checks fail | Rebuild before release |
| F3 | Page opened as `file://` but user expects Gemini | Health / match “broken” | No local HTTP API | `/api/health` unreachable; UI status copy | Serve with `webapp.py` over `http://127.0.0.1:…` per README |
| F4 | `webapp.py` without Gemini SDK | Smart match **503** or “no sdk” chip | Wrong Python / missing deps | `/api/health` → `gemini_installed: false` | Same interpreter as `pip install -r agent-matchmaker/requirements-app.txt`; `./scripts/run-agent-matchmaker.sh` |
| F5 | No API key for Gemini | Cannot rank with model | Env / `.env` / `.gemini_api_key` missing | `POST /api/match` 400 with key message | Configure key per README |
| F6 | Model name rejected by API | Match errors | API surface changed | Error text from `/api/match` | Change model in UI or env |
| F7 | Port already in use | Server won’t start | Stale process | stderr from `webapp.py` | Free port or `--port` |
| F8 | Playwright browsers not installed | Screenshot step errors | `pip install` without `playwright install` | QA JSON / stderr | `python3 -m playwright install chromium` |
| F9 | Bad path on `GET /api/agent-source` | Data exposure risk | Bug in path allowlist | Security review + curl probes | Only allowed roots; traversal → **404** |
| F10 | GitHub Pages base path | Wrong API URLs if resolver wrong | Subpath deploy | Manual on hosted URL | Client uses `resolveApi` for subpaths |
| F11 | Optional `data/sources.json` missing | Harmless 404 in logs | File never added | Server log noise | Ship minimal file, remove fetch, or accept 404 |
| F12 | Hash route `#/agent/…` invalid or stale | Blank or wrong profile | Bad link, renamed agent | Manual / Playwright flow tests | Validate path against catalog; close overlay |

**Review cadence:** before merge, walk IDs **F1–F4** (data + server + SDK); before release, add **F5–F10**; after UI routing changes, add **F12**.
