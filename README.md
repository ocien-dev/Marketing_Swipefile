# Marketing Swipe File

Marketing Swipe File is a Codex-first system for turning business podcasts, YouTube episodes, transcripts, and complementary files into actionable direct-response marketing intelligence.

The first source is VTurb. After the VTurb backlog is processed, the planned order is KiwiCast, Hotmart Cast, then derivative sources discovered from the base.

## Canonical Docs

- `AGENTS.md`
- `docs/gold-extraction-contract.md`
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

Current remediation guardrail: Gates R1, R2, and R3 are approved. The first MSF-S skill wave is complete and approved. MSF-R03 is done: ignored/local-only data lives outside OneDrive under `C:\MSF-data\Marketing_Swipe_File`. Do not run the MSF-R14 backfill, Supabase, MCP, or agents until the owner explicitly starts that next step.

MSF-R20 gold extraction runs end to end in the active chat. The same execution
handles planning, extraction, routine corrections, deterministic validation and
final packets without delegation or intermediate review. Only after the whole
epic is ready does a dedicated final audit phase run with `gpt-5.6-sol` at high
reasoning or above. The lifecycle name `awaiting_external_audit` is preserved
for compatibility: `external` means external to the executor phase. Historical
audit records remain unchanged. See `AGENTS.md` and
`docs/gold-extraction-contract.md`.

## Local Data Policy

Raw transcripts, complementary files, member-area assets, PDFs, spreadsheets, and generated exports are ignored by Git by default. Keep source material local unless there is an explicit reason to publish it.

Runtime scripts resolve ignored/local-only data through `MSF_DATA_DIR` when it is set. If it is unset, scripts fall back to the repo-local `data/` tree:

```powershell
$env:MSF_DATA_DIR = "C:\MSF-data\Marketing_Swipe_File"
setx MSF_DATA_DIR "C:\MSF-data\Marketing_Swipe_File"
```

`data/processed/taxonomy_seed.json` remains the canonical repo-tracked taxonomy seed.

### WSL 2 default runtime

The preferred runtime is Ubuntu 24.04 on WSL 2, with the repository, data
root, temp directory, and virtualenv on the Linux filesystem:

```bash
git clone --branch codex/msf-r20-wsl-migration-baseline \
  https://github.com/ocien-dev/Marketing_Swipefile.git \
  "$HOME/src/Marketing_Swipe_File"
cd "$HOME/src/Marketing_Swipe_File"
export MSF_DATA_DIR="$HOME/msf-data/Marketing_Swipe_File"
export TMPDIR="$HOME/.cache/msf/tmp"
./scripts/bootstrap_wsl.sh
python scripts/verify_wsl_environment.py
```

Do not use `/mnt/c`, the OneDrive checkout, or a synced OneDrive folder as the
active data root. The gold pipeline performs many small writes and atomic
directory swaps; sync clients can introduce locks, partial uploads, mtime
churn, and avoidable I/O latency. OneDrive is suitable for an immutable,
closed backup archive created after the pipeline is idle, not for the live
working tree.

### Sharing exports with other Windows projects

Other local projects may consume a read-only, verified export snapshot without
touching the active WSL data root. Set `MSF_PUBLISHED_DIR` to a OneDrive-visible
directory (the WSL example uses `/mnt/c/Users/luish/OneDrive/Marketing_Swipe_File_Published`)
and publish explicitly after the pipeline is idle:

```bash
python -m scripts.publish_shared_exports --check
python -m scripts.publish_shared_exports --publish
python -m scripts.publish_shared_exports --verify
```

The published directory contains `published_manifest.json` plus an `exports/`
tree with the current derived JSON, CSV, Markdown and checksum files. It
excludes historical `_snapshots/`, raw media, raw transcripts, `processed/`,
receipts, and all active working directories. Consumers should read from this
snapshot only; they must never write back into it or use it as the active
pipeline data root.

GitHub protects versioned code only. Raw media, transcripts, reviews, packets,
receipts, and other ignored data under `MSF_DATA_DIR` need a separate private
backup policy. Supabase is a future serving layer, not a file-level backup of
this data tree.

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

In WSL, use `.venv/bin/python` and install `requirements-dev.txt` through
`scripts/bootstrap_wsl.sh`.

## MVP Flow

Use `$env:MSF_DATA_DIR` for runtime data after MSF-R03. If it is unset, the same paths resolve under repo-local `data/`.

1. Add candidate episodes to `input/youtube_urls.csv` under the configured data root.
2. Collect metadata into `raw/youtube/{video_id}/metadata.json`.
3. Collect YouTube automatic transcript into `raw/youtube/{video_id}/transcript_original.json`.
   - If the direct caption endpoint fails but the YouTube UI exposes "Mostrar transcricao", use the Playwright DOM/snapshot fallback.
4. Normalize transcript into `processed/{video_id}/content_segments.json`.
5. Split long episodes into extraction chunks under `processed/{video_id}/chunks/`.
6. Detect complementary materials into `referenced_assets.json`, `acquisition_tasks.json`, and `manual_actions.md`.
7. Place obtained complementary files in `input/assets/{video_id}/` under the configured data root.
8. Process assets into `processed/assets/{asset_id}/content_segments.json`.
9. Extract insights into `insights.json`.
10. Consolidate master exports.
11. Generate strategy packs and outputs such as VSLs, leads, and ads.

See `docs/asset-acquisition-procedure.md` for the manual procedure used when an episode references PDFs, docs, spreadsheets, slides, direct-message files, comment-keyword files, or member-area materials.

## Current Execution Slice

Current local state as of 2026-07-08:

- Runtime ignored/local-only data resolves through `MSF_DATA_DIR` to `C:\MSF-data\Marketing_Swipe_File`.
- Repo `data/` now contains only tracked scaffolding, tracked lightweight queues/examples, `taxonomy_seed.json`, and previously tracked S09 audit artifacts.
- 160 real VTurb URLs are listed in the runtime `input/youtube_urls.csv`.
- Metadata was collected for 96 listed episodes.
- 50 episodes have usable transcripts, normalized segments, chunks, asset detection, extraction packets, transcript insights, summaries, and logs.
- Remaining queued episodes without transcript/chunks should not be counted as fully processed yet.
- Local exports consolidate 253 episode records, 46 registered assets, 1,406 insights, and 13 acquisition tasks.
- The VTurb Academy layer added Drive/MP4 and HLS transcriptions through `scripts/transcribe_academy_videos.py` and `scripts/transcribe_academy_hls.py`.
- `data/input/academy_video_transcription_queue.csv` and `data/input/youtube_urls_academy_new.csv` are lightweight tracked queues; generated Academy exports remain local under the runtime `exports/**`.
- Runtime `exports/acquisition_tasks_master.csv` contains 13 complementary-material acquisition tasks.
- Search, strategy-pack generation, output evaluation, dedupe, taxonomy classification, summaries, and orchestration scripts exist.
- 7 Codex skills and 5 operational loops exist for the local file-based workflow.
- The Session 1 remediation environment is validated with `.venv`, `requirements.txt`, JSON parsing, script syntax compilation, and the status-only batch check.
- MSF-R05/MSF-R06 are complete as a Codex-first pilot: `schemas/insights_v2.schema.json`, `schemas/examples/insights_v2.example.json`, `scripts/validate_insights_v2.py`, `scripts/extract_transcript_insights_llm.py`, and `prompts/extraction/base_insight_extraction_v2.md` exist; 2 local processed episodes have validated ignored `insights_v2.json` pilots.
- MSF-R07/MSF-R08 are complete for the amended Gate R1: 15 complete v2 episodes, 246 chunks, external blind judgment, batch 006 remediation, and formal Gate R1 approval are recorded in `docs/insight-v1-vs-v2-review-2026-07-07.md` and `docs/execution-log.md`.
- MSF-R09 is complete: `scripts/evaluate_output.py` keeps the old keyword score only as `keyword_presence_check`, and the honest Codex-first rubric evaluation validates JSON against `schemas/output_evaluation.schema.json`.
- MSF-R10 is complete: external blind judgment scored `with_base_v2=14`, `baseline_no_base=0`, `tie=2`, so Gate R2 is formally approved. The sample limitation is 1 briefing x 2 artifacts; MSF-S09 still needs varied-briefing validation.
- MSF-R11 is complete: `scripts/generate_strategy_pack.py` now supports MMR/Jaccard diversity with `--diversity-weight`, `--episode-cap`, and `--source curated`; fixture test coverage exists.
- MSF-R12 is complete: local ignored `data/exports/curated_insights.json` has 125 curated v2 items, and the owner accepted the 30-item review sample as filled.
- MSF-R13 is complete: curated VSL/ads packs were regenerated, evaluated as support artifacts, and approved by external technical review.
- Gate R3 is formally approved with three notes: calibrate compressed `editorial_score`, rewrite one boilerplate title suffix (`...em lateralizar`), and accept `process-copy-anuncios` coverage at 18 items for the first MSF-S pass.
- MSF-S01 is complete: `skills/_templates/msf-process-skill/`, `schemas/msf_process_skill_contract.schema.json`, `scripts/create_process_skill.py`, and `scripts/validate_process_skill.py` define the process-skill contract/template.
- MSF-S02 is complete: `scripts/search_insights.py` and `scripts/generate_strategy_pack.py` default to `curated_insights` and support `--process-tags` filters.
- MSF-S08 is complete: `skills/_modules/msf-transversal-copy/` defines approved `transversal:mecanismo-big-idea` and `transversal:prova-depoimentos` modules, with review notes in `docs/msf-s08-transversal-modules-review-2026-07-07.md`.
- First-wave process skills are complete and approved: S04 offer, S03 VSL, S05 ads, S06 low-ticket, and S07 quiz.
- MSF-R03 is complete: `scripts/msf_common.py` resolves runtime data through `MSF_DATA_DIR`, ignored/local-only data was copied to `C:\MSF-data\Marketing_Swipe_File`, and repo-local ignored payloads were deleted after validation.

Proof-of-value artifacts generated locally:

- `data/exports/strategy_pack_vsl.md`
- `data/exports/strategy_pack_ads.md`
- `data/exports/generated_vsl_lowticket.md`
- `data/exports/generated_ads_lowticket.md`
- `data/exports/generated_vsl_lowticket_evaluation.md`: honest rubric score 30/40, `needs_revision`; old 39/40 was only a keyword proxy.
- `data/exports/generated_ads_lowticket_evaluation.md`: honest rubric score 30/40, `needs_revision`; old 37/40 was only a keyword proxy.
- `docs/curated-insights-r12-review-2026-07-07.md`: R12 curated lot summary.
- `docs/strategy-pack-r13-comparison-2026-07-07.md`: R13 pack comparison and evaluator result.

Important caveat: the old 39/40 and 37/40 scores do not prove value. Gate R3 is approved, MSF-S01/MSF-S02/MSF-S08 are done, MSF-S04 is next, and MSF-R14 backfill, Supabase, and MCP remain later work.
