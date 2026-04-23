# WORKFLOW-09 — Frontend submit — offline heuristic

## Overview

Deterministic ranking of catalog agents entirely in the browser: no `fetch` to `/api/match`, no Gemini. Used when **Smart match (Gemini)** is off, when the SDK or key is unavailable, or when the user is in **`file://`** mode ([WF-13](./REGISTRY.md)). Results are rendered with the same card chrome as the Gemini path (`buildMatchCard`: fit 0–100, “why” prose, optional caveat, path, links).

**Source:** `agent-matchmaker/index.template.html` (built copy: `index.html`) — IIFE functions `rankAllAgents`, `scoreAgents`, `attachOfflineFitScores`, `offlineWhyFromEvidence`, `offlineCaveatForList`, `offlineSummaryFromList`, `render`, `buildMatchCard`, `followUpAgents`.

## Actors

| Actor | Role |
|-------|------|
| User | Enters goal, optional extra context, division checkboxes, focus tags |
| `rankAllAgents` | Scores every catalog row; attaches `evidence` for explainability |
| `scoreAgents` | Picks top 12 with positive score, else top 8 fallback; applies `attachOfflineFitScores` |
| `render` | Fills `#gemini-summary`, `#orchestrator-callout`, `#results`, `#results-meta` |
| `OFFLINE_LEXICAL` | One-time corpus stats: per-agent token sets + `idf(term)` |
| Embedded / fetched `CATALOG` | Agent objects (`path`, `category`, `name`, `description`, `vibe`, `emoji`) |

## Prerequisites

- `CATALOG` loaded ([WF-07](./WORKFLOW-07-frontend-bootstrap.md)): `fetch("catalog.json")` on `http(s):`, or `window.__agentCatalogB64` on `file://` / fallback.
- DOM: `#goal`, `#extra-ctx`, `#division-boxes`, `#focus-tags`, `#results`, `#gemini-summary`, `#orchestrator-callout`, `#results-meta`.

## Trigger

- Click **find agents (offline)** (`#btn-match` when `geminiAvailable()` is false).
- Same button label path when AI toggle off or health denies Gemini.

## Workflow tree

### Step 1 — Read inputs

- **Actor:** `rankAllAgents`
- **Action:** `goal` from `#goal`, `extra` from `#extra-ctx`, `queryText = join` with newline; `goalTokens = collectTextTokens(queryText)`; selected divisions and focus tags from checkboxes.
- **Output:** token list, filters, `multiDivision` flag.

### Step 2 — `multiDivision` heuristics

- **Condition:** `selectedCats.length >= 3` **or** goal/extra matches `(orchestrat|workflow|pipeline|multiple agents|handoff|full stack project)`.
- **Output:** boolean passed to `render` for orchestration callout.

### Step 3 — Per-agent raw score + evidence

- **Actor:** `OFFLINE_LEXICAL.rows.map`
- **Scoring (additive):**
  - **Division:** +18 if agent’s `category` is in selected divisions (when any division selected).
  - **Terms:** for each `goalTokens` present in agent haystack tokens: `+ 3.6 * idf(tok)`; if token in lowercase name: `+ 2.4 * idf(tok)`. Contributions aggregated into `topMatchedTerms` (top 5 by contribution).
  - **Bigrams:** adjacent pairs in `goalTokens` both present; substring `a + " " + b` in haystack: +5.5 each hit (`phraseCount`).
  - **Compact query:** normalized spaces, length ≥ 8, substring in haystack: +24 (`compactQueryHit`).
  - **Focus tags:** each configured key string contained in haystack: +7; labels stored in `tagHitLabels`.
  - **Games path:** `game-development` in path and “games” tag: +10.
  - **China / APAC:** regex on query and “china” tag: +5.
- **Output:** `{ agent, score, evidence }` per row; sort descending by `score`.

### Step 4 — Shortlist + display fit

- **Actor:** `scoreAgents`
- **Action:** Prefer `score > 0`, up to 12; else first 8 rows (scores may be 0). `attachOfflineFitScores`: maps raw scores to **display** `fitDisplay` 1–100 via min–max within the list; if all scores ≤ 0, uses a descending ladder (58, 55, …).
- **Note:** Follow-up suggestions (`followUpAgents`) still order by **raw** `score` from `rankAllAgents`.

### Step 5 — Batch copy + orchestration strip

- **Actor:** `render`
- **Summary:** `offlineSummaryFromList(list, queryText)` → `#gemini-summary` as `summary · …` (same region as Gemini).
- **Orchestration:** If `multiDivision` and orchestrator agent found in catalog (`specialized/`, name matches `orchestrator`), `#orchestrator-callout` uses **`orchestration ·`** prefix (parity with Gemini) plus rationale parts (division count, regex intent) and optional vibe snippet; github + local controls appended as safe HTML.

### Step 6 — Cards + meta

- **Actor:** `render` + `buildMatchCard`
- **Per card:** `offlineWhyFromEvidence(evidence, agent)` as main “why” paragraph; **caveat** only on rank 1 from `offlineCaveatForList` (short query, tie scores, or zero-signal fallback).
- **Copy payload:** `fit_score` = `fitDisplay`, `heuristic_score` = rounded raw score, `summary` / `orchestration` strings for plain-text export.
- **Meta strip:** Explains offline mode and that aside scores are rescaled within the list (or “no strong signal…” when top raw score is 0).

## Handoff contracts

### Inputs (implicit)

| Source | Field |
|--------|--------|
| DOM | `goal`, `extra`, division checkboxes, focus tag checkboxes |
| Data | `CATALOG`, `OFFLINE_LEXICAL`, `FOCUS_TAGS` |

### Outputs (DOM)

| Region | Content |
|--------|---------|
| `#gemini-summary` | Offline batch summary (always shown when list non-empty) |
| `#orchestrator-callout` | Optional orchestration + links |
| `#results-meta` | Status / mode explanation |
| `#results` | `article.card` nodes from `buildMatchCard` |

## Failure / edge cases

| Case | Behavior |
|------|----------|
| Empty `CATALOG` | `list` empty → meta “no catalog loaded”, empty state paragraph |
| All scores zero | Fallback slice of 8 agents; display fit ladder; caveat mentions weak overlap |
| Very short query | Caveat on first card suggests broad ranking |

## Test ideas (manual)

1. **Offline only:** Turn off Smart match, enter a niche token rare in catalog — top card should show high fit and “Lexical overlap on: …”.
2. **Divisions:** Select one division; verify division-only boost in why text when token signal weak.
3. **Multi-division + goal text:** Select ≥3 divisions or type “pipeline orchestration” — orchestration callout visible with `orchestration ·` label.
4. **`file://`:** Open built `index.html` from disk; submit — summary + cards without network.

## Related workflows

- [WF-07](./WORKFLOW-07-frontend-bootstrap.md) — catalog load, `geminiAvailable`, `file://`
- [WF-04](./WORKFLOW-04-api-match.md) — `POST /api/match` Gemini path consumed by `renderGemini` in the template
- [Registry](./REGISTRY.md) — WF-08 / WF-09 journey mapping
