# Execution Log - Marketing Swipe File

## 2026-07-04 - Foundation and first local scripts

Completed:

- MSF-A01: created project structure, README, `.gitignore`, `.env.example`, and directory keep files.
- MSF-A02: created local JSON contracts in `schemas/`.
- MSF-A03: created taxonomy seed in `data/processed/taxonomy_seed.json`.
- MSF-A04: created fixture transcript, description, simulated extracted asset text, spreadsheet CSV, and expected outputs.
- MSF-B04: implemented `scripts/normalize_transcript.py`.
- MSF-C02: implemented `scripts/detect_assets.py`.

Validation:

- Parsed all JSON files successfully.
- Checked repository text files for non-ASCII characters.
- Ran fixture pipeline using bundled Codex Python:
  - normalized `tests/fixtures/transcripts/fixture001_transcript_original.json`
  - generated `data/processed/fixture001/content_segments.json`
  - detected 2 referenced assets
  - generated `referenced_assets.json`, `acquisition_tasks.json`, and `manual_actions.md`
- Compared generated fixture outputs against expected files.

Notes:

- `python` is not available on PATH in the current PowerShell session. Use Codex bundled Python:
  `C:\Users\luish\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`
- Historical note: `git status` failed once with `fatal: not a git repository`, but later sessions confirmed Git status works in this workspace.
- Web search did not reliably find VTurb episode URLs, so `data/input/youtube_urls.example.csv` was created instead of inventing pilot links.

Next recommended tasks:

1. MSF-B01: fill `data/input/youtube_urls.csv` with real VTurb pilot episode URLs.
2. MSF-B02: implement real YouTube metadata collection.
3. MSF-B03: implement automatic YouTube transcript collection.
4. MSF-C01: create the LLM prompt for complementary asset detection.
5. MSF-D01: implement registration of obtained complementary files.

## 2026-07-04 - YouTube collectors and asset registration

Completed:

- MSF-B02: implemented `scripts/collect_youtube_metadata.py` and shared helpers in `scripts/youtube_common.py`.
- MSF-B03: implemented `scripts/collect_youtube_transcript.py` with safe fallback when caption tracks are unavailable.
- MSF-C01: created `prompts/assets/detect_complementary_assets.md`.
- MSF-C03: created `docs/asset-acquisition-procedure.md` and linked it from README.
- MSF-D01: implemented `scripts/register_assets.py`.

Partial progress:

- MSF-D03: `scripts/process_asset.py` supports text, Markdown, and simple HTML assets.
- MSF-D04: `scripts/process_asset.py` supports CSV spreadsheet assets.

Validation:

- Metadata smoke test succeeded with a public YouTube URL and wrote `tests/tmp/youtube/dQw4w9WgXcQ/metadata.json`.
- Transcript smoke test wrote a valid fallback transcript file with zero segments because captions were not returned in that request.
- Registered fixture CSV and Markdown assets into `tests/tmp/raw_assets/`.
- Processed fixture Markdown into 5 asset segments.
- Processed fixture CSV into 4 asset segments.
- All JSON files parsed successfully.
- All Python scripts compiled in memory without writing bytecode.
- Non-ASCII scan returned clean.

Blocked:

- MSF-B01 remains blocked until real VTurb pilot episode URLs are provided or reliably discovered.

Next recommended tasks:

1. Add 5 real VTurb URLs to `data/input/youtube_urls.csv`.
2. Run `collect_youtube_metadata.py` on the real URL list.
3. Run `collect_youtube_transcript.py` on real metadata outputs.
4. Extend `process_asset.py` for PDF, DOCX, XLSX, and PPTX.
5. Implement MSF-E01 and MSF-E02 extraction prompts.

## 2026-07-04 - Initial asset processing and extraction prompts

Completed:

- MSF-E01: created `prompts/extraction/base_insight_extraction.md`.
- MSF-E02: created specialized extractors:
  - `copy_extractor.md`
  - `vsl_extractor.md`
  - `ads_extractor.md`
  - `offer_extractor.md`
  - `funnel_extractor.md`
  - `ops_extractor.md`
  - `asset_extractor.md`

Partial progress:

- MSF-D03: implemented text, Markdown, and simple HTML support in `scripts/process_asset.py`.
- MSF-D04: implemented CSV support in `scripts/process_asset.py`.

Validation:

- Registered fixture Markdown and CSV assets.
- Processed fixture Markdown into 5 normalized asset segments.
- Processed fixture CSV into 4 normalized asset segments.
- Parsed all JSON files successfully.
- Compiled all Python scripts in memory.
- Non-ASCII scan returned clean.

Still open:

- OCR/image support for MSF-D06.
- Real VTurb URLs for MSF-B01.

## 2026-07-04 - Main complementary asset processors

Completed:

- MSF-D02: added PDF support to `scripts/process_asset.py` using `pdfplumber`.
- MSF-D03: added DOCX support using `python-docx`; text, Markdown, and simple HTML were already supported.
- MSF-D04: added XLSX support using `openpyxl`; CSV was already supported.
- MSF-D05: added PPTX support using `python-pptx`.

Validation:

- Generated temporary PDF, DOCX, XLSX, and PPTX assets in `tests/tmp/generated_assets`.
- Registered all generated assets with `scripts/register_assets.py`.
- Processed all generated assets with `scripts/process_asset.py`.
- Segment counts:
  - DOCX: 1
  - PPTX: 1
  - PDF: 1
  - XLSX: 3
- Parsed all JSON files successfully.
- Compiled all Python scripts in memory.
- Non-ASCII scan returned clean.

Still open:

- OCR/image support for MSF-D06.
- Real VTurb URLs for MSF-B01.
- Extraction runner MSF-E03.

## 2026-07-04 - Manual extraction runner and insight audit

Completed:

- MSF-E03: implemented `scripts/prepare_extraction_packet.py` for manual/semi-automated Codex extraction.
- MSF-F01: created `docs/insight-quality-checklist.md`.
- MSF-F02: implemented `scripts/audit_insights.py`.

Validation:

- Built a VSL extraction packet from fixture transcript segments:
  `tests/tmp/extraction_packets/fixture001_vsl_packet.md`.
- Audited `tests/fixtures/expected/fixture001_insights.json`.
- Audit passed with 1 valid fixture insight.

Still open:

- MSF-E04 deduplication.
- MSF-E05 taxonomy classifier.
- MSF-E06 summary generators.
- Real VTurb URLs for MSF-B01.

## 2026-07-04 - First VTurb episode and Playwright transcript fallback

Input:

- First pilot video: `https://www.youtube.com/watch?v=mCaFyZpXJdE`.

Completed:

- Collected metadata for `mCaFyZpXJdE`.
- Confirmed the direct caption endpoint returned an empty/error response.
- Used Playwright to open YouTube, expand the description, click `Mostrar transcricao`, and capture the transcript snapshot.
- Added `scripts/collect_youtube_transcript_from_playwright_snapshot.py`.
- Extracted 2,706 transcript segments into `data/raw/youtube/mCaFyZpXJdE/transcript_original.json`.
- Normalized 2,706 segments into `data/processed/mCaFyZpXJdE/content_segments.json`.
- Hardened `scripts/detect_assets.py` against false positives by adding accent-insensitive term matching and actionable-material checks.
- Reran material detection; no actionable complementary files were detected for this episode.
- Added `schemas/extraction_chunks.schema.json`.
- Added `scripts/create_extraction_chunks.py`.
- Split the 5h09 episode into 21 chapter-aware extraction chunks under `data/processed/mCaFyZpXJdE/chunks/`.
- Added `scripts/prepare_chunked_extraction_packets.py`.
- Generated 126 chunked extraction packets: 21 chunks x 6 extractors.
- Generated initial full extraction packets for VSL, ads, offer, funnel, copy, and ops under `data/processed/mCaFyZpXJdE/extraction_packets/`.

Validation:

- Parsed project JSON files successfully.
- Compiled Python scripts in memory.
- Chunking preserved all 2,706 transcript segments.
- Largest extraction chunk is below 50,000 approximate chars.

Notes:

- Full extraction packets are large, around 1.48 MB each. Prefer chunk-level extraction loops for Codex.
- `.playwright-cli/` is now ignored because snapshots are local automation artifacts.

## 2026-07-04 - Cross-chat handoff

Completed:

- Created `docs/marketing-swipe-file-handoff.md` as the canonical restart document for another Codex chat.
- Linked the handoff from `README.md`.

Use:

- Start a new chat by asking Codex to read `docs/marketing-swipe-file-handoff.md`, `README.md`, `docs/execution-log.md`, and `docs/marketing-swipe-file-full-backlog.md`.
- Continue with chunk-level extraction for `mCaFyZpXJdE`.

## 2026-07-04 - Local MVP operating layer

Completed:

- Filled `data/input/youtube_urls.csv` with 5 real VTurb pilot episodes.
- Added orchestration scripts:
  - `scripts/run_episode_pipeline.py`
  - `scripts/run_asset_pipeline.py`
- Added local base scripts:
  - `scripts/dedupe_insights.py`
  - `scripts/classify_taxonomy.py`
  - `scripts/consolidate_exports.py`
  - `scripts/search_insights.py`
  - `scripts/generate_strategy_pack.py`
  - `scripts/generate_summaries.py`
  - `scripts/evaluate_output.py`
  - `scripts/extract_description_insights.py`
- Hardened `scripts/detect_assets.py` against false positives and added detection for public mockup/banner/image links.
- Created strategy-pack retrieval prompt in `prompts/retrieval/strategy_pack_retrieval.md`.
- Created output evaluation rubric in `docs/output-evaluation-rubric.md`.
- Created operational loops in `loops/`.
- Created 6 Codex skills under `skills/`.
- Processed 3 pilot episodes through metadata, transcript, normalized segments, chunks, asset detection, extraction packets, summaries, and logs:
  - `mCaFyZpXJdE`: 2,706 transcript segments and 21 chunks.
  - `TOW0sWhPaZw`: 2,108 transcript segments and 20 chunks.
  - `yyoGeQp5yzM`: 1,142 transcript segments and 16 chunks.
- Collected metadata for 2 additional pilot episodes, but transcript extraction is still blocked:
  - `YfI0CjI_XaE`
  - `aSFAve1klsc`
- Generated 25 description-based candidate insights across the pilot set.
- Consolidated local exports in `data/exports/`.
- Generated VSL and ads strategy packs with 20 recommended angles each.
- Generated first proof-of-value artifacts:
  - `data/exports/generated_vsl_lowticket.md`
  - `data/exports/generated_ads_lowticket.md`
- Evaluated both outputs:
  - VSL: 35/40, decision `pass`.
  - Ads: 35/40, decision `pass`.

Validation:

- Custom skill frontmatter and placeholder validation passed for all 6 project skills.
- Fixture insight audit passed after dedupe/classification.
- Local search returned usable VSL results from the consolidated base.
- Official skill quick validation could not run because the bundled Python environment does not include the `yaml` module.

Notes:

- The current insights are useful for proof of value, but they are description candidates with `review_status=needs_review`; they are not a replacement for deep chunk-level extraction.
- `data/exports/acquisition_tasks_master.csv` currently contains 1 pending public-file task for the `TOW0sWhPaZw` mockup/banner Drive link.
- Some stale `transcript_fallback_needed.md` markers could not be deleted because OneDrive/Windows returned access denied; the processed episodes should be judged by transcript/chunk presence, not by stale marker filenames.

## 2026-07-04 - Deep transcript insights and updated proof-of-value outputs

Completed:

- Added `scripts/extract_transcript_insights.py` to generate evidence-backed insights from transcript chunks with segment locators, timestamps, quotes, confidence, source agent, and dedupe keys.
- Extracted 143 transcript insights from 4 processed VTurb episodes:
  - `mCaFyZpXJdE`: 52 transcript insights.
  - `TOW0sWhPaZw`: 43 transcript insights.
  - `yyoGeQp5yzM`: 26 transcript insights.
  - `aSFAve1klsc`: 22 transcript insights.
- Recovered `aSFAve1klsc` transcript through the Playwright YouTube transcript panel fallback, then processed 1,242 transcript segments into 11 chunks.
- Retried `YfI0CjI_XaE` through direct transcript collection, YouTube UI transcript panel, and signed caption URL extraction. The episode still returned empty/loading transcript data and remains blocked.
- Reran taxonomy classification, dedupe, summaries, consolidated exports, and strategy packs.
- Consolidated exports now include 5 episodes and 168 insights:
  - 143 transcript insights.
  - 25 description candidate insights.
- Updated proof-of-value artifacts to use transcript insight IDs instead of description-only candidates:
  - `data/exports/generated_vsl_lowticket.md`
  - `data/exports/generated_ads_lowticket.md`
- Re-evaluated outputs:
  - VSL: 39/40, decision `pass`.
  - Ads: 37/40, decision `pass`.

Validation:

- Audited all generated `insights.json` files:
  - `aSFAve1klsc`: passed, 22 insights.
  - `mCaFyZpXJdE`: passed, 52 insights.
  - `TOW0sWhPaZw`: passed, 43 insights.
  - `yyoGeQp5yzM`: passed, 26 insights.
  - `fixture001`: passed, 1 fixture insight.

Notes:

- Release 1 is not complete yet: the current base has 4 fully processed VTurb episodes, 1 transcript-blocked pilot episode, and 168 total insights. The Release 1 target remains 20 processed episodes and 500+ atomic insights.
- `extract_transcript_insights.py` is heuristic and evidence-located. The next scale step should include human sample review of high-use insights before treating them as final claims.
- Some stale transcript fallback marker files may remain because OneDrive/Windows can deny deletion; use transcript/chunk/insight presence as the source of truth.

## 2026-07-04 - Scaled local Release 1 data gate to 20+ episodes

Completed:

- Expanded `data/input/youtube_urls.csv` from 5 pilot URLs to 27 VTurb URLs using episode links discovered in collected VTurb descriptions.
- Collected metadata for all 27 listed episodes.
- Ran direct transcript collection for the full CSV; new videos required UI fallback because the direct caption endpoint returned empty transcript data.
- Used Playwright UI transcript fallback in batches to recover transcript JSON for additional episodes.
- Reprocessed the local episode pipeline with `--skip-metadata --skip-transcript` after fallback transcripts were saved.
- Reached 21 episodes with usable transcripts, normalized segments, chunks, asset detection, extraction packets, summaries, and transcript insights.
- 6 episodes remain blocked at transcript fallback:
  - `YfI0CjI_XaE`
  - `Rz1Y7fhXGFI`
  - `0DlzYLUmKcU`
  - `wJincuVXxxc`
  - `FV-KR1eEbCw`
  - `sVUrU9gvxyk`
- Ran `scripts/extract_transcript_insights.py --all-processed`.
- Generated 585 transcript insights across processed episodes.
- Ran taxonomy classification, dedupe, and audit for 22 local insight files.
- Regenerated summaries and consolidated exports.
- Regenerated VSL and ads strategy packs with 40 results each.
- Re-evaluated proof-of-value outputs:
  - VSL: 39/40, decision `pass`.
  - Ads: 37/40, decision `pass`.

Current counts:

- Listed VTurb URLs: 27.
- Episodes with metadata: 27.
- Episodes fully processed with transcript/chunks: 21.
- Transcript insights: 585.
- Description candidate insights: 25.
- Consolidated insights: 610.
- Pending acquisition tasks: 11.

Validation:

- Classification, dedupe, and audit completed for 22 `insights.json` files.
- `scripts/consolidate_exports.py` reported 27 episodes, 0 assets, 610 insights, and 11 acquisition tasks.

Notes:

- The Release 1 local data gate is now reached: 20+ processed episodes and 500+ atomic insights.
- Production-grade use still needs human sample review of high-use insights, because the transcript insight extractor is heuristic.
- Complementary assets are detected but not obtained/processed yet.

Next recommended tasks:

1. Extract deep chunk-level insights for the 3 processed episodes, starting with VSL, offer, funnel, and ads.
2. Retry transcript fallback for `YfI0CjI_XaE` and `aSFAve1klsc` when Playwright usage is available.
3. Add 15 more VTurb episodes only after the 3-episode extraction quality is acceptable.
4. Download/process the pending `TOW0sWhPaZw` mockup/banner asset if it is strategically useful.

## 2026-07-04 - VTurb Academy complementary asset acquisition

Completed:

- Inventoried 49 VTurb Academy lessons from the logged-in Academy area.
- Downloaded or confirmed 41 Academy-linked assets: Docs/DOCX, XLSX, PDF, GIF, help HTML files, and public external HTML pages.
- Registered 46 local assets total after combining Academy materials with the previously pending direct-link assets.
- Processed 36 assets into `data/processed/assets/{asset_id}/content_segments.json`; image/GIF assets were registered and skipped because OCR/video extraction is not implemented yet.
- Updated original acquisition tasks by exact referenced asset match:
  - 5 tasks now `obtained`.
  - 6 tasks remain `pending`.
- Expanded `data/input/youtube_urls.csv` from 27 to 36 VTurb URLs with high-confidence Academy-related channel matches.
- Created video/audio follow-up queues:
  - `data/input/academy_video_transcription_queue.csv`
  - `data/exports/vturb_academy_video_transcription_queue.csv`
- Resolved the `bit.ly/livecriativoshigao` link to a Drive folder and added its MP4s to the video/audio queue.
- Wrote the working acquisition manifest and summary:
  - `data/exports/vturb_academy_asset_manifest.csv`
  - `data/exports/vturb_academy_external_html_assets.csv`
  - `data/exports/vturb_academy_external_link_check.csv`
  - `data/exports/vturb_academy_youtube_candidates.csv`
  - `data/exports/vturb_academy_acquisition_summary.md`
- Regenerated master exports. `scripts/consolidate_exports.py` reported 27 episodes, 46 assets, 610 insights, and 11 acquisition tasks.

Notes:

- One VTurb help article linked by the Academy returned 404 and remains marked as `download_failed` in the Academy asset manifest.
- Drive/Academy videos were inventoried into a 212-row transcription queue, but audio extraction/transcription was deferred because `ffmpeg`, `yt-dlp`, and `gdown` were not available in the local PATH.
- Asset insights were not generated in this pass; the current local automation processes asset text into segments/summaries, but does not yet have an automatic asset-insight extractor.

## 2026-07-04 - Batch skill, DOM transcript capture, and 50 complete VTurb videos

Completed:

- Created the target-driven batch scaling layer:
  - `skills/marketing-swipe-file-scale-batch/`
  - `loops/batch-scaling.md`
  - Batch section in `loops/episode-processing.md`
- Added `scripts/discover_vturb_youtube_videos.py` to discover VTurb channel videos through YouTube continuation tokens and append deduped URLs to `data/input/youtube_urls.csv`.
- Added `scripts/run_episode_batch.py` to count complete videos, process incomplete queue rows, call transcript fallback, rerun the episode pipeline, extract/classify/dedupe/audit insights, generate summaries, and consolidate exports.
- Added `scripts/capture_youtube_transcript_with_playwright_cli.py` and upgraded it to DOM-first capture:
  - Opens the YouTube watch page with Playwright CLI.
  - Expands the description and clicks `Mostrar transcricao`.
  - Reads current transcript DOM elements (`transcript-segment-view-model`).
  - Falls back to snapshot parsing when needed.
- Patched video-id argument handling for IDs that begin with `-`, including `-8mIBnJwDXo`.
- Expanded English/direct-response extraction rules in `scripts/extract_transcript_insights.py` so episodes such as Stefan Georgi/RMBC generate evidence-backed insights instead of zero results.
- Discovered 160 public VTurb channel videos and appended 124 deduped URLs total across the scaling pass, bringing `data/input/youtube_urls.csv` to 160 rows.
- Recovered and processed additional VTurb transcripts through the Playwright DOM fallback.
- Reached the requested gate of 50 complete videos.
- Regenerated master exports with `scripts/consolidate_exports.py`.

Current counts:

- Listed VTurb URLs: 160.
- Episodes with metadata: 96.
- Complete videos: 50.
- Episodes with transcript segments: 50.
- Episodes with chunks: 50.
- Transcript insights: 1,198.
- Description candidate insights: 25.
- Consolidated insights: 1,223.
- Registered assets: 46.
- Acquisition tasks: 13.

Validation:

- `scripts/run_episode_batch.py --target-complete 50 --status-only` reports `complete=50`, `with_transcript=50`, and `with_chunks=50`.
- `scripts/consolidate_exports.py` reported 229 episode records, 46 assets, 1,223 insights, and 13 acquisition tasks.
- Python syntax compilation passed for the new and modified batch/capture/extraction scripts.
- Playwright DOM capture was regression-tested on `mCaFyZpXJdE` and recovered 2,706 transcript segments.
- `VQJ_Y8E6Hw0` was reprocessed from 0 to 23 audited transcript insights after English/direct-response rules were added.

Notes:

- Some videos still fail transcript fallback because the YouTube page exposes no usable transcript panel or the panel cannot be read reliably. They remain incomplete and should not be counted.
- `npx --package @playwright/cli` may need approval outside the sandbox on this Windows machine because npm writes to a global cache.
- The 50-video inventory is suitable for stronger retrieval/proof-of-value work, but production-grade claims still need human sample review of high-use insights.

## 2026-07-05 - VTurb Academy video transcription

Completed:

- Added a local transcription dependency layer under `.codex_deps/transcription` using `faster-whisper` plus `requests`.
- Added `scripts/transcribe_academy_videos.py` for Drive/MP4-style Academy video assets.
- Added `scripts/transcribe_academy_hls.py` for logged-in Academy player lessons exposed as HLS (`main.m3u8`).
- Used the logged-in Chrome Academy session to inventory internal player media and wrote:
  - `data/exports/vturb_academy_lesson_media_manifest.json`
  - `data/exports/vturb_academy_hls_probe.csv`
  - `data/exports/vturb_academy_hls_probe.json`
- Transcribed 123 Drive video assets into synthetic local episode records under `data/raw/youtube/academyvid-*` and `data/processed/academyvid-*`.
- Transcribed 33 Academy HLS lessons into synthetic local episode records under `data/raw/youtube/academyhls-*` and `data/processed/academyhls-*`.
- Implemented HLS chunked transcription to avoid memory failures on long lessons; long videos were split into about 20-minute local `.ts` chunks before Whisper transcription.
- Ran `scripts/extract_transcript_insights.py --all-processed`.
- Ran taxonomy classification across processed `insights.json` files.
- Regenerated master exports with `scripts/consolidate_exports.py`.
- Synced `data/input/academy_video_transcription_queue.csv` to `data/exports/vturb_academy_video_transcription_queue.csv`.
- Wrote `data/exports/vturb_academy_pending_transcription_actions.csv` with the 9 remaining actionable transcription follow-ups.
- Audited `data/exports/insights_master.json`; audit status `passed`.

Current counts:

- Master episode records: 253.
- Registered assets: 46.
- Consolidated insights: 1,406.
- Acquisition tasks: 13 (`8 pending`, `5 obtained`).
- Academy transcription queue rows: 212.
- Queue status: 156 `transcribed`, 1 `transcribed_empty`, 2 `skipped_over_limit`, 16 `no_internal_hls_external_material_page`, 11 `youtube_processed_existing`, 7 `youtube_in_main_queue_pending_transcript`, 2 `not_video_file_asset`, 17 `not_direct_video_external_asset`.
- Drive video assets: 123 `transcribed`, 1 `transcribed_empty`, 2 `skipped_over_limit`.
- Academy internal lessons: 33 `transcribed`, 16 without HLS/internal player media.
- YouTube channel episode candidates from Academy: 18 total; 11 already processed locally through the main YouTube pipeline and 7 still pending transcript processing in the main queue.

Validation:

- `scripts/consolidate_exports.py` reported 253 episodes, 46 assets, 1,406 insights, and 13 acquisition tasks.
- `scripts/audit_insights.py --input data/exports/insights_master.json` passed for 1,406 insights.
- In-memory Python compilation passed for 29 scripts.
- JSON parsing passed for schemas and export JSON files.

Remaining special handling:

- `AD 11.mp4` was skipped because the Drive file is about 726 MB.
- `Aula Desafio 6 Low em 30.mp4` was skipped because the Drive file is about 3 GB.
- The 16 Academy lessons without HLS should be treated as pages of materials, Drive links, external links, or YouTube candidates rather than internal player videos.
- Many short ad/swipe videos transcribed successfully but produced 0 heuristic insights; their transcripts are still available locally for manual or future extractor passes.

## 2026-07-07 - Session 1 remediation environment closeout

Completed:

- Resumed the interrupted Session 1 remediation run after `pip install -r requirements.txt` had stalled in another chat.
- Installed `requirements.txt` into the project `.venv`:
  - `pdfplumber`
  - `python-docx`
  - `openpyxl`
  - `python-pptx`
  - `faster-whisper`
- Added `.pip-tmp/` to `.gitignore` after using a local temp directory to work around Windows Temp permission errors.
- Updated README and handoff references so the project venv is the default runtime instead of the Codex bundled Python cache.
- Registered the remediation backlog as a canonical doc and restated the R1/R2 guardrail before more scale or Supabase/MCP.

Validation:

- `.\.venv\Scripts\python.exe -m pip check` returned no broken requirements.
- Imports passed for `pdfplumber`, `docx`, `openpyxl`, `pptx`, and `faster_whisper`.
- `scripts/run_episode_pipeline.py --video-id mCaFyZpXJdE --skip-metadata --skip-transcript` completed and wrote a pipeline log.
- `scripts/run_episode_batch.py --target-complete 50 --status-only` reported `listed=160`, `complete=50`, `with_transcript=50`, and `with_chunks=50`.
- In-memory syntax compilation passed for 29 Python scripts. `compileall` still hits OneDrive/Windows `.pyc` permission friction, so use in-memory compile for quick validation.
- Parsed 2,685 JSON files successfully with the project venv.
- `scripts/consolidate_exports.py` reported 253 episode records, 46 assets, 1,406 insights, and 13 acquisition tasks.
- `scripts/audit_insights.py --input data/exports/insights_master.json` passed for 1,406 insights.

Notes:

- `data/input/academy_video_transcription_queue.csv` and `data/input/youtube_urls_academy_new.csv` are lightweight queue files and can be tracked. Raw transcripts, processed outputs, generated exports, private assets, and media remain ignored by Git.
- Next remediation work should stay inside R1/R2: start with MSF-R05 and MSF-R06 rather than scaling more episodes or creating Supabase/MCP.

## 2026-07-07 - MSF-R05/MSF-R06 raw_insights_v2 pilot

Completed:

- MSF-R05: created `schemas/insights_v2.schema.json` for `raw_insights_v2` and future `curated_insights`.
- Added `schemas/examples/insights_v2.example.json`.
- Added `jsonschema` to `requirements.txt` and installed it in the project `.venv`.
- Added `scripts/validate_insights_v2.py` for formal schema validation.
- MSF-R06: implemented the Codex-first route instead of API extraction for this pilot.
- Added `prompts/extraction/base_insight_extraction_v2.md` with the quality rules from the remediation backlog.
- Added `scripts/extract_transcript_insights_llm.py` to prepare v2 packets, merge chunk outputs, validate final payloads, and write `data/processed/{video_id}/insights_v2.json`.
- Updated `loops/episode-processing.md` and `skills/marketing-swipe-file-extract-insights/SKILL.md` with the v2 workflow.

Pilot outputs:

- `data/processed/mCaFyZpXJdE/insights_v2.json`: 4 v2 insights across 2 chunks.
- `data/processed/TOW0sWhPaZw/insights_v2.json`: 4 v2 insights across 2 chunks.
- These files are local generated artifacts under ignored `data/processed/**`; they are not versioned.

Validation:

- `scripts/validate_insights_v2.py schemas/examples/insights_v2.example.json` returned `VALID`.
- `scripts/validate_insights_v2.py data/processed/mCaFyZpXJdE/insights_v2.json data/processed/TOW0sWhPaZw/insights_v2.json` returned `VALID` for both pilot files.
- Pilot titles were unique within each episode and avoided the broad v1 templates.
- Re-running `scripts/extract_transcript_insights_llm.py combine` with fixed `run_id` and `generated_at` kept the same file hashes:
  - `mCaFyZpXJdE`: `9A40ABC79A1930F65770217152E59426ABF1B1C10361E35DA4E36669435DAC34`
  - `TOW0sWhPaZw`: `82394D8A8814A8566E64C3C96577C9A7AA38BE13DFE0E7584B66193F2076A5A5`
- Evidence quote check passed: 8/8 pilot quotes matched their source transcript segments.
- `.\.venv\Scripts\python.exe -m pip check` returned no broken requirements.
- In-memory script compilation passed for 31 Python scripts.

Cost and effort:

- Route: Codex-first manual extraction (`route=codex_manual`).
- External API cost: `$0`.
- Pilot effort: 2 processed episodes, 4 chunks, 8 manually reviewed v2 insights.

Next:

- MSF-R07: run v2 extraction over the 50 complete episodes and update consolidation to produce `data/exports/insights_v2_master.json`.
- MSF-R08: compare a paired v1/v2 sample before declaring the R1 gate.

## 2026-07-07 - MSF-R07/MSF-R08 instrumentation and pilot review

Completed:

- Updated `scripts/consolidate_exports.py` to keep the v1 master unchanged while also generating ignored local v2 exports:
  - `data/exports/insights_v2_master.json`
  - `data/exports/insights_v2_master.csv`
  - `data/exports/insights_v2_status.json`
  - `data/exports/insights_v2_episode_status.csv`
  - `data/exports/insights_v2_title_distribution.csv`
- Added v2 validation during consolidation; invalid `insights_v2.json` files are reported and excluded from the v2 master.
- Added `scripts/generate_insight_v1_v2_review.py` to produce a paired v1/v2 review without copying raw transcript quotes into tracked docs.
- Generated `docs/insight-v1-vs-v2-review-2026-07-07.md` from the current pilot data.

Current v2 status:

- `scripts/consolidate_exports.py` reported 253 episode records, 46 assets, 1,406 v1 insights, 8 v2 insights, and 13 acquisition tasks.
- R07 coverage is 2/50 target episodes.
- `data/exports/insights_v2_status.json` reports 0 invalid v2 files, title distribution OK for the current pilot, and `gate_r1_ready=false`.
- The review has 8 pilot pairs, not the 40-pair R08 acceptance sample.

Validation:

- `scripts/consolidate_exports.py` completed with the project `.venv`.
- `scripts/generate_insight_v1_v2_review.py --date 2026-07-07` completed and wrote the review doc.
- In-memory compile passed for the edited/new Python files. Direct `py_compile` still hits OneDrive/Windows `.pyc` permission friction.

Decision:

- MSF-R07 is in progress, not done.
- MSF-R08 remains blocked until MSF-R07 reaches the 50 target episodes.
- Gate R1 is not declared.

Next:

- Continue Codex-first v2 extraction for the remaining target episodes, then rerun `scripts/consolidate_exports.py`.
- Re-run `scripts/generate_insight_v1_v2_review.py --date <date>` only after the v2 master can supply at least 40 comparable pairs.
