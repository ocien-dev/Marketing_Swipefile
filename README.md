# Marketing Swipe File

Marketing Swipe File is a Codex-first system for turning business podcasts, YouTube episodes, transcripts, and complementary files into actionable direct-response marketing intelligence.

The first source is VTurb. After the VTurb backlog is processed, the planned order is KiwiCast, Hotmart Cast, then derivative sources discovered from the base.

## Canonical Docs

- `docs/marketing-swipe-file-handoff.md`
- `docs/marketing-swipe-file-prd.md`
- `docs/marketing-swipe-file-architecture.md`
- `docs/marketing-swipe-file-mvp-backlog.md`
- `docs/marketing-swipe-file-full-backlog.md`

## Execution Principle

Build in this order:

1. Local scripts and contracts.
2. Prompts.
3. Codex skills.
4. Codex loops.
5. Supabase.
6. MCP.
7. Specialized agents.
8. UI and automation.

Do not create autonomous agents before the underlying scripts, prompts, skills, and loops have been validated on real episodes or representative fixtures.

## Local Data Policy

Raw transcripts, complementary files, member-area assets, PDFs, spreadsheets, and generated exports are ignored by Git by default. Keep source material local unless there is an explicit reason to publish it.

Tracked files should be limited to:

- docs
- prompts
- scripts
- tests and fixtures
- schemas/contracts
- lightweight seed files such as `data/processed/taxonomy_seed.json`

## MVP Flow

1. Add candidate episodes to `data/input/youtube_urls.csv`.
2. Collect metadata into `data/raw/youtube/{video_id}/metadata.json`.
3. Collect YouTube automatic transcript into `data/raw/youtube/{video_id}/transcript_original.json`.
   - If the direct caption endpoint fails but the YouTube UI exposes "Mostrar transcricao", use the Playwright snapshot fallback.
4. Normalize transcript into `data/processed/{video_id}/content_segments.json`.
5. Split long episodes into extraction chunks under `data/processed/{video_id}/chunks/`.
6. Detect complementary materials into `referenced_assets.json`, `acquisition_tasks.json`, and `manual_actions.md`.
7. Place obtained complementary files in `data/input/assets/{video_id}/`.
8. Process assets into `data/processed/assets/{asset_id}/content_segments.json`.
9. Extract insights into `insights.json`.
10. Consolidate master exports.
11. Generate strategy packs and outputs such as VSLs, leads, and ads.

See `docs/asset-acquisition-procedure.md` for the manual procedure used when an episode references PDFs, docs, spreadsheets, slides, direct-message files, comment-keyword files, or member-area materials.

## Current Execution Slice

The current implementation starts with:

- MSF-A01: project structure, README, `.gitignore`
- MSF-A02: local JSON contracts
- MSF-A03: taxonomy seed
- MSF-A04: fixtures
- Playwright transcript fallback for YouTube UI transcripts
- Chapter-aware extraction chunking for long episodes
- Batch preparation of chunk-level extraction packets
