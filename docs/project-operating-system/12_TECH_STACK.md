# Tech Stack

## Target Platform

Hybrid local-first project:

- Markdown content repository
- Static browser app
- Python local server and scripts
- Optional external LLM API
- Experimental React/Vite app

## Frontend / UI

- Static HTML/CSS/JS in `agent-matchmaker/`
- React/Vite in `supabase-web/`

## Backend / Runtime

- Python for local server and repo scripts

## Database / Storage

- Markdown source files
- JSON catalog files
- SQLite registry database
- Optional future Supabase storage is `UNKNOWN`

## Auth

None required for local/static MVP.

## Hosting / Distribution

- Local file/browser usage
- Local Python server
- GitHub Pages for static demo
- Future hosted app is `UNKNOWN`

## Testing

- Matchmaker catalog build
- HTTP-only QA capture
- Optional Playwright visual capture
- Optional `supabase-web` build/lint checks when that app is touched

## AI Tools / Models

Optional Gemini matching through local server/API key.

## Why This Stack

The stack keeps core usage simple and local while allowing richer matching, registry workflows, and future web work.

## Stack Constraints

- Avoid making external APIs mandatory.
- Avoid cloud-first assumptions.
- Avoid changing tech stack casually.

## Confidence

Medium. Current local stack is clear; future hosted/Supabase direction is still open.

