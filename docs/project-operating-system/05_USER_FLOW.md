# User Flow

## Starting Point

The user opens the repo, the static matchmaker page, or the local matchmaker server.

## User Goal

Find useful agents for a project task and optionally export or use the selected content elsewhere.

## Main Flow

1. User describes a task or browses by division/category.
2. Matchmaker loads the local catalog.
3. User filters, searches, or ranks agents.
4. User opens source details or recommendations.
5. User copies, installs, exports, or follows the recommended workflow.

## Success State

The user identifies the right agent or set of agents and has a clear next action.

## Failure State

The catalog is stale/missing, source file paths break, optional model matching fails without a fallback, or exported packs omit required content.

## Empty State

No matching agents found; UI should allow clearing filters or using broader search.

## Error State

Display a clear local/runtime/API error without hiding the offline heuristic path.

## Friction Points

- Distinguishing static browser mode from local server mode.
- Optional Gemini API key setup.
- Keeping generated catalog files in sync with agent Markdown.
- Understanding registry outputs versus current matchmaker catalog.

## Unknowns

- Final flow for registry-backed search in the UI.

