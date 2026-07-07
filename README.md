# Marketing Swipe File

Marketing Swipe File is a Codex-first system for turning business podcasts, YouTube episodes, transcripts, and complementary files into actionable direct-response marketing intelligence.

The first source is VTurb. After the VTurb backlog is processed, the planned order is KiwiCast, Hotmart Cast, then derivative sources discovered from the base.

## Canonical Docs

- `docs/marketing-swipe-file-handoff.md`
- `docs/marketing-swipe-file-prd.md`
- `docs/marketing-swipe-file-architecture.md`
- `docs/marketing-swipe-file-mvp-backlog.md`
- `docs/marketing-swipe-file-full-backlog.md`
- `docs/marketing-swipe-file-remediation-backlog.md`
- `docs/execution-log.md`

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

Current remediation guardrail: do not scale new episodes or start Supabase/MCP until the R1/R2 gates in `docs/marketing-swipe-file-remediation-backlog.md` are closed.

## Local Data Policy

Raw transcripts, complementary files, member-area assets, PDFs, spreadsheets, and generated exports are ignored by Git by default. Keep source material local unless there is an explicit reason to publish it.

Tracked files should be limited to:

- docs
- prompts
- scripts
- tests and fixtures
- schemas/contracts
- lightweight seed files such as `data/processed/taxonomy_seed.json`
- lightweight queue files such as `data/input/academy_video_transcription_queue.csv` and `data/input/youtube_urls_academy_new.csv`

## Local Python

Use the project venv by default:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\run_episode_batch.py --target-complete 50 --status-only
```

The old Codex bundled Python path is only a fallback. The project runtime dependencies are tracked in `requirements.txt`.

## MVP Flow

1. Add candidate episodes to `data/input/youtube_urls.csv`.
2. Collect metadata into `data/raw/youtube/{video_id}/metadata.json`.
3. Collect YouTube automatic transcript into `data/raw/youtube/{video_id}/transcript_original.json`.
   - If the direct caption endpoint fails but the YouTube UI exposes "Mostrar transcricao", use the Playwright DOM/snapshot fallback.
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

Current local state as of 2026-07-07:

- 160 real VTurb URLs are listed in `data/input/youtube_urls.csv`.
- Metadata was collected for 96 listed episodes.
- 50 episodes have usable transcripts, normalized segments, chunks, asset detection, extraction packets, transcript insights, summaries, and logs.
- Remaining queued episodes without transcript/chunks should not be counted as fully processed yet.
- Local exports consolidate 253 episode records, 46 registered assets, 1,406 insights, and 13 acquisition tasks.
- The VTurb Academy layer added Drive/MP4 and HLS transcriptions through `scripts/transcribe_academy_videos.py` and `scripts/transcribe_academy_hls.py`.
- `data/input/academy_video_transcription_queue.csv` and `data/input/youtube_urls_academy_new.csv` are lightweight tracked queues; generated Academy exports remain local under ignored `data/exports/**`.
- `data/exports/acquisition_tasks_master.csv` contains 13 complementary-material acquisition tasks.
- Search, strategy-pack generation, output evaluation, dedupe, taxonomy classification, summaries, and orchestration scripts exist.
- 7 Codex skills and 5 operational loops exist for the local file-based workflow.
- The Session 1 remediation environment is validated with `.venv`, `requirements.txt`, JSON parsing, script syntax compilation, and the status-only batch check.
- MSF-R05/MSF-R06 are complete as a Codex-first pilot: `schemas/insights_v2.schema.json`, `schemas/examples/insights_v2.example.json`, `scripts/validate_insights_v2.py`, `scripts/extract_transcript_insights_llm.py`, and `prompts/extraction/base_insight_extraction_v2.md` exist; 2 local processed episodes have validated ignored `insights_v2.json` pilots.
- MSF-R07/MSF-R08 are instrumented but not complete: `scripts/consolidate_exports.py` now writes ignored local `insights_v2_master.*`, `insights_v2_status.json`, episode status, title distribution, and chunk-coverage exports; `scripts/generate_insight_v1_v2_review.py` now prepares a blind A/B sample plus local key before scoring. `docs/insight-v1-vs-v2-review-2026-07-07.md` is pending blind judgment, not a v2 win. Gate R1 is not declared because v2 coverage is still partial: 2/50 target episodes have any v2, 0/50 are fully extracted by chunk.

Proof-of-value artifacts generated locally:

- `data/exports/strategy_pack_vsl.md`
- `data/exports/strategy_pack_ads.md`
- `data/exports/generated_vsl_lowticket.md`
- `data/exports/generated_ads_lowticket.md`
- `data/exports/generated_vsl_lowticket_evaluation.md`
- `data/exports/generated_ads_lowticket_evaluation.md`

Important caveat: the raw insight base is still heuristic and should not be treated as production-grade. Continue MSF-R07 by extracting real v2 outputs for the remaining target episodes before declaring Gate R1 or moving to Supabase/MCP.
