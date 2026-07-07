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
- `docs/marketing-swipe-file-skills-backlog.md`
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

Current remediation guardrail: Gates R1 and R2 are approved, but do not run MSF-S, the MSF-R14 backfill, Supabase, or MCP before Gate R3 closes in `docs/marketing-swipe-file-remediation-backlog.md`.

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
- MSF-R07/MSF-R08 are complete for the amended Gate R1: 15 complete v2 episodes, 246 chunks, external blind judgment, batch 006 remediation, and formal Gate R1 approval are recorded in `docs/insight-v1-vs-v2-review-2026-07-07.md` and `docs/execution-log.md`.
- MSF-R09 is complete: `scripts/evaluate_output.py` keeps the old keyword score only as `keyword_presence_check`, and the honest Codex-first rubric evaluation validates JSON against `schemas/output_evaluation.schema.json`.
- MSF-R10 is complete: external blind judgment scored `with_base_v2=14`, `baseline_no_base=0`, `tie=2`, so Gate R2 is formally approved. The sample limitation is 1 briefing x 2 artifacts; MSF-S09 still needs varied-briefing validation.
- MSF-R11 is complete: `scripts/generate_strategy_pack.py` now supports MMR/Jaccard diversity with `--diversity-weight`, `--episode-cap`, and `--source curated`; fixture test coverage exists.
- MSF-R12 is ready for owner review: local ignored `data/exports/curated_insights.json` has 125 curated v2 items and `data/exports/curated_insights_owner_review_sample_2026-07-07.csv` has the 30-item sample.
- MSF-R13 is ready for external review: curated VSL/ads packs were regenerated and evaluated as support artifacts; Gate R3 is not declared.

Proof-of-value artifacts generated locally:

- `data/exports/strategy_pack_vsl.md`
- `data/exports/strategy_pack_ads.md`
- `data/exports/generated_vsl_lowticket.md`
- `data/exports/generated_ads_lowticket.md`
- `data/exports/generated_vsl_lowticket_evaluation.md`: honest rubric score 30/40, `needs_revision`; old 39/40 was only a keyword proxy.
- `data/exports/generated_ads_lowticket_evaluation.md`: honest rubric score 30/40, `needs_revision`; old 37/40 was only a keyword proxy.
- `docs/curated-insights-r12-review-2026-07-07.md`: R12 curated lot summary.
- `docs/strategy-pack-r13-comparison-2026-07-07.md`: R13 pack comparison and evaluator result.

Important caveat: the old 39/40 and 37/40 scores do not prove value. Gate R2 is approved by the blind R10 result, R3 is ready for external review but not declared, and MSF-S/MSF-R14/Supabase/MCP remain blocked until Gate R3 closes.
