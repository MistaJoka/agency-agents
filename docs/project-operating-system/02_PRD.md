# Product Requirements Document

## Problem

The repo has valuable agent content and tooling, but the project has expanded beyond a simple prompt catalog. Without a central operating spec, future contributors can accidentally break links, scripts, catalogs, source provenance, or working matchmaker flows while trying to improve the project.

## Target User

A builder or maintainer who wants to find, use, improve, import, or export specialist AI agents with clear provenance and low setup friction.

## User Pain

- Agent content is spread across many directories.
- Matchmaker, registry, strategy docs, and web-app work have different mental models.
- AI-assisted changes can overreach if the project intent and regression rules are not explicit.
- Import/export work needs provenance and repeatable checks.

## Desired Outcome

The project remains easy to browse, run, extend, and verify while preserving the curated content.

## MVP Promise

This project helps builders find and use specialized AI agents so they can assemble better AI-assisted workflows without starting from generic prompts.

## Core Use Cases

- Browse agents by category.
- Search/filter/rank agents in the local matchmaker.
- Build or refresh `agent-matchmaker/catalog.json`.
- Run optional Gemini matching locally.
- Import and normalize enabled external sources into a registry.
- Export registry content into tool-specific packs.
- Follow NEXUS docs for coordinated multi-agent workflows.

## Success Metrics

- Existing matchmaker build and local QA checks pass.
- Agent files remain discoverable.
- Registry commands are documented and reversible.
- New work includes a regression/FMAE path when it affects runtime behavior.

## Constraints

- Preserve existing curated content.
- Avoid destructive source sync behavior.
- Keep external source fetching opt-in.
- Do not require cloud services for core local usage.
- Keep secrets out of tracked files.

## Non-Goals

- Replacing the existing repo with a generic app template.
- Moving all content into a new `src/` layout.
- Making Supabase mandatory for local catalog use.
- Enabling all remote sources by default.

## Confidence

Medium-high for current local/static workflows. Medium for future registry-driven UI and Supabase direction.

