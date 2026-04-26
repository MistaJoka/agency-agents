# Security and Privacy

## Sensitive Data

- Gemini/Google API keys.
- Any future Supabase keys or tokens.
- Local private source content if external imports are added from private repos.

## Authentication

No authentication is required for the current local/static MVP.

## Authorization

Not applicable for local-only workflows. Future hosted workflows must define access rules before storing user data.

## Input Validation

Validate or constrain:

- Source ids and source paths.
- File paths used by source inspection APIs.
- External repo URLs.
- Export output paths.
- API request payloads.

## File and Source Risks

- Path traversal when serving source files.
- Accidentally importing huge or irrelevant external directories.
- Overwriting generated exports without clear user intent.
- Treating untrusted imported Markdown as executable instructions.

## API / Integration Risks

- API keys leaking into tracked files or logs.
- Sending sensitive local content to external LLM APIs without user intent.
- Remote source sync pulling unexpected content.

## AI-Specific Risks

- Prompt injection inside imported agent/skill docs.
- Hallucinated recommendations if model output is not grounded in catalog data.
- Tool misuse if generated instructions are executed blindly.

## Basic Protections

- Keep remote sources opt-in.
- Keep secrets in env vars or untracked `.env`.
- Preserve offline/static fallback.
- Treat imported content as data, not trusted commands.
- Log FMAE findings for security-sensitive changes.

