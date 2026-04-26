# Deployment and Distribution

## Where It Runs First

Local machine and static browser usage.

## Where It May Run Later

- GitHub Pages static demo.
- Hosted web app if `supabase-web` direction is confirmed.
- Tool-specific export destinations.

## Distribution Type

- Local run
- Static web deploy
- Generated integration packs
- Optional future hosted app

## Environment Variables

- `GEMINI_API_KEY` or `GOOGLE_API_KEY` for optional Gemini matching.
- Future Supabase variables are `UNKNOWN`.

## Local Run Commands

```bash
python3 scripts/build_agent_matchmaker.py
python3 agent-matchmaker/webapp.py
./scripts/run-agent-matchmaker.sh
```

## Build Commands

```bash
python3 scripts/build_agent_matchmaker.py
```

For `supabase-web` only when that app is touched:

```bash
cd supabase-web
npm run build
```

## Test Commands

```bash
HTTP_ONLY=1 ./scripts/qa-reality-capture.sh
```

## Release Steps

1. Rebuild generated catalog/static output when agent content changes.
2. Run relevant regression checks.
3. Update docs/changelog.
4. Push or deploy through the existing configured workflow.

## Rollback Plan

Use git to revert the specific change. Do not delete imported source clones as the only rollback unless the issue is disk cleanup; source enablement is controlled by `data/sources.json`.

## Monitoring / Logs

Local logs and generated QA output are the current evidence sources. Hosted monitoring is `UNKNOWN`.

