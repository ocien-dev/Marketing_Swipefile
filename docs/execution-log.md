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

## 2026-07-07 - Correction to MSF-R07/MSF-R08 gate harness

Problem found:

- The first `scripts/generate_insight_v1_v2_review.py` scoring path was not acceptable for Gate R1.
- `criterion_winners` could only return `v2` or `tie`, so the 8/8 pilot result was tautological.
- The previous quote-cleanliness check used v2 self-declared fields such as `evidence_strength` and `evidence_cleanliness`, which cannot count as proof in a v1/v2 comparison.

Corrected:

- Rewrote `scripts/generate_insight_v1_v2_review.py` as a two-step blind workflow:
  - `--mode prepare` writes `data/exports/insight_v1_v2_blind_sample_<date>.csv` with randomized A/B order and blank `judgment_*` columns.
  - It also writes `data/exports/insight_v1_v2_blind_key_<date>.json` as a local ignored de-anonymization key.
  - `--mode score --judgments <filled_csv>` de-anonymizes and computes v1/tie/v2 counts only after blind judgment.
- The script now runs the same quote-noise detector on both sides for subscribe CTAs, engagement CTAs, description CTAs, watch-next language, hashtags, and other episode titles.
- Regenerated `docs/insight-v1-vs-v2-review-2026-07-07.md` as pending blind judgment. It no longer declares a pilot v2 win.
- Updated `scripts/consolidate_exports.py` so `data/exports/insights_v2_status.json` reports chunk coverage as well as episode coverage.

Current corrected status:

- R07 target set: 50 complete v1 episodes from `data/input/youtube_urls.csv`.
- Current v2 coverage: 2/50 target episodes have any v2.
- Current full-episode v2 coverage: 0/50 target episodes are fully extracted by chunk.
- Current chunk coverage: 4/754 target chunks extracted.
- `gate_r1_ready=false`.

Validation:

- In-memory compile passed for `scripts/consolidate_exports.py` and `scripts/generate_insight_v1_v2_review.py`.
- `scripts/consolidate_exports.py` completed and printed `R07 v2 coverage: 2/50 target episode(s) with v2, 0/50 fully extracted, 4/754 target chunk(s), gate_r1_ready=False.`
- `scripts/generate_insight_v1_v2_review.py --date 2026-07-07 --seed 20260707` completed and wrote the blind sample, local key, and pending report.
- `scripts/generate_insight_v1_v2_review.py --mode score` was smoke-tested against the blank blind CSV and correctly reported 32 pending criterion cells instead of producing a false score.

Backlog status correction:

- MSF-R01, MSF-R02, and MSF-R04 marked `done`.
- MSF-R03 marked `deferred`, because data relocation outside OneDrive was not actually executed.

## 2026-07-07 - MSF-R07 Codex-first batch 001

Scope:

- Route: Codex-first manual extraction (`route=codex_manual`), because `OPENAI_API_KEY` was missing and the `openai` package was not installed in `.venv`.
- Batch: `mCaFyZpXJdE` chunks 001 and 002.
- Rationale: continue in priority order and keep the first post-harness batch small enough for real review.

Outputs:

- Added local ignored chunk outputs:
  - `data/processed/mCaFyZpXJdE/llm_v2_outputs/chunk_001_insights.json`
  - `data/processed/mCaFyZpXJdE/llm_v2_outputs/chunk_002_insights.json`
- Recombined `data/processed/mCaFyZpXJdE/insights_v2.json`.
- `mCaFyZpXJdE` now has 9 v2 insights across 4 chunks.

Validation:

- `scripts/extract_transcript_insights_llm.py combine --video-id mCaFyZpXJdE --run-id mCaFyZpXJdE-r07-codex-batch-001 --generated-at 2026-07-07T13:00:00Z --max-insights-per-chunk 5` completed.
- `scripts/validate_insights_v2.py data/processed/mCaFyZpXJdE/insights_v2.json data/processed/TOW0sWhPaZw/insights_v2.json` returned `VALID` for both.
- New batch evidence check: 5/5 new quotes matched their source `content_segments.json` segment text, with no hits for `inscreva`, `assista tambem`, or hashtags.
- `scripts/consolidate_exports.py` completed and reported 253 episode records, 46 assets, 1,406 v1 insights, 13 v2 insights, and 13 acquisition tasks.

Updated R07 status:

- Target episodes with any v2: 2/50.
- Fully extracted v2 target episodes: 0/50.
- Target chunks extracted: 6/754.
- `gate_r1_ready=false`.

Risk note:

- No OneDrive lock/permisson issue appeared during this batch. If locks/permissons appear in future batches, reopen MSF-R03 before continuing extraction.

## 2026-07-07 - MSF-R07 Route B amendment and extraction session

Decision registered:

- MSF-R07 remains on Route B: Codex-first, no API.
- Gate R1 is amended to require 15-20 complete episodes by chunk, roughly 225-300 chunks, prioritizing VSL/ads strategy-pack material and the already initiated episodes `mCaFyZpXJdE` and `TOW0sWhPaZw`.
- The original 50-episode coverage target is moved to continuous post-gate work under MSF-R14.
- Rule unchanged: when amended coverage is reached, generate a blind 40-pair sample with `scripts/generate_insight_v1_v2_review.py --mode prepare` and stop. Blind judgment remains external to Codex.

Completed:

- Updated `docs/marketing-swipe-file-remediation-backlog.md` with the MSF-R07 acceptance amendment, reason, gate scope, and MSF-R14 absorption of the 50-episode continuation.
- Updated `loops/episode-processing.md` with the R07 extraction session protocol: whole episodes, one at a time, minimum 20 chunks per session, no canonical-doc reread during extraction, schema validation per chunk/final file, quote-noise check, consolidation, execution-log throughput, and commit at session close.
- Updated `scripts/extract_transcript_insights_llm.py` so processed chunk output files count toward `input_chunk_ids` even when `insights` is empty. This lets the Codex-first route honestly mark weak or promo-contaminated chunks as processed without forcing generic insights.
- Updated `scripts/consolidate_exports.py` to separate the continuous 50-episode tracking target from the amended gate fields:
  - `r07_gate_route=codex_manual_no_api`
  - `r07_gate_min_complete_episodes=15`
  - `r07_gate_max_complete_episodes=20`
  - `r07_gate_expected_chunk_range=225-300`

Extraction outputs:

- Completed `mCaFyZpXJdE` in v2: 21/21 chunks, 24 insights v2.
- Completed `TOW0sWhPaZw` in v2: 20/20 chunks, 18 insights v2.
- New session throughput: 35 new chunks processed, 29 new insights added, 2 episodes closed by chunk.
- Local timestamp window for repo writes and validation artifacts: 13:13-13:19 America/Sao_Paulo. API cost: `$0`.

Validation:

- `scripts/validate_insights_v2.py data/processed/mCaFyZpXJdE/insights_v2.json data/processed/TOW0sWhPaZw/insights_v2.json` returned `VALID` for both files.
- New evidence quote check: 29/29 new evidence quotes matched their source transcript segment exactly.
- New evidence quote-noise check: 0 hits for promo CTAs, `inscreva`, `assista tambem`, hashtags, or description boilerplate.
- `scripts/consolidate_exports.py` completed and reported 253 episode records, 46 assets, 1,406 v1 insights, 42 v2 insights, and 13 acquisition tasks.
- Updated R07 status: 2/50 target episodes have v2 and are fully extracted, 41/754 target chunks extracted, `gate_r1_ready=false`.
- In-memory compile passed for `scripts/extract_transcript_insights_llm.py` and `scripts/consolidate_exports.py`. Direct `py_compile` still hits OneDrive/Windows `.pyc` permission friction.

Calibration:

- Current amended gate progress: 2/15 minimum complete episodes; 41 chunks extracted.
- Remaining to the lower bound is roughly 184 chunks and 13 complete episodes.
- At the observed throughput of 35 chunks per session, estimate 6 more sessions to reach the 15-episode lower bound and 8 sessions to reach the 20-episode upper bound, depending on next-episode chunk counts.

## 2026-07-07 - MSF-R07 Codex-first batch 004

External review:

- The previous 42-insight lot was approved externally: 42/42 unique titles, distributed `claim_risk`, and amended gate instrumentation accepted.
- Owner adjustment: use `.\.venv\Scripts\python.exe -B` or `PYTHONDONTWRITEBYTECODE=1` in R07 sessions to avoid OneDrive `.pyc` permission errors.
- Owner reminder: reopen MSF-R03 between Gate R1 and the backfill of the remaining chunks.

Scope:

- Route: Codex-first manual extraction (`route=codex_manual`), no API.
- Session protocol: whole episodes, one at a time, minimum 20 chunks.
- Episodes processed:
  - `yyoGeQp5yzM`: 16/16 chunks, 12 insights v2.
  - `aSFAve1klsc`: 11/11 chunks, 10 insights v2.

Validation:

- Commands were run with `python -B`; no `.pyc` permission error occurred.
- `scripts/validate_insights_v2.py data/processed/yyoGeQp5yzM/insights_v2.json data/processed/aSFAve1klsc/insights_v2.json` returned `VALID` for both files.
- New evidence quote check: 22/22 new evidence quotes matched their source transcript segment exactly.
- New evidence quote-noise check: 0 hits for promo CTAs, `inscreva`, `assista tambem`, hashtags, `primeiro link`, or description boilerplate.
- `scripts/consolidate_exports.py` completed and reported 253 episode records, 46 assets, 1,406 v1 insights, 64 v2 insights, and 13 acquisition tasks.
- Status after consolidation: 4/50 target episodes fully extracted in v2, 68/754 target chunks extracted, `gate_r1_ready=false`.
- Title uniqueness: 64/64 unique v2 titles.
- `claim_risk` distribution: `low=25`, `medium=35`, `high=4`.
- In-memory compile passed for `scripts/extract_transcript_insights_llm.py` and `scripts/consolidate_exports.py` with `python -B`.

Throughput and calibration:

- New session throughput: 27 chunks processed, 22 insights added, 2 episodes closed by chunk. API cost: `$0`.
- Current amended gate progress: 4/15 minimum complete episodes; 68 chunks extracted.
- Remaining to the lower bound is roughly 157 chunks and 11 complete episodes.
- At the observed recent throughput range of 27-35 chunks per session, estimate 5-6 more sessions to reach the 15-episode lower bound and 7-9 sessions to reach the 20-episode upper bound, depending on next-episode chunk counts.

## 2026-07-07 - MSF-R07 encoding micro-fixes and batch 005

External review:

- Batch 004 was approved externally: 64/64 unique titles and distributed `claim_risk`.
- Required micro-fixes before the next lot:
  - Correct `confian?a` to `confianca` in the `yyoGeQp5yzM` insight title.
  - Normalize the non-ASCII characters in `TOW0sWhPaZw-v2-0004` `use_case`.
  - Add a post-lot scan for non-ASCII and orphan `?` artifacts in editorial v2 fields.

Completed:

- Added `scripts/audit_insights_v2_text.py`.
- Updated `loops/episode-processing.md` so every R07 session runs the editorial text scan after each lot.
- Applied structured local JSON fixes to `insights_v2.json` files and corresponding `llm_v2_outputs` so future `combine` runs do not reintroduce the encoding artifacts.
- The auditor now scans final `insights_v2.json` files and chunk outputs.

Extraction scope:

- Route: Codex-first manual extraction (`route=codex_manual`), no API.
- Commands were run with `python -B`.
- Episodes processed:
  - `8WEvN5T7J0U`: 14/14 chunks, 10 insights v2.
  - `L7u7r6rOl68`: 16/16 chunks, 14 insights v2.

Validation:

- `scripts/audit_insights_v2_text.py` passed: `VALID editorial_text_files=104`.
- `scripts/validate_insights_v2.py data/processed/8WEvN5T7J0U/insights_v2.json data/processed/L7u7r6rOl68/insights_v2.json` returned `VALID` for both files.
- New evidence quote check: 24/24 new evidence quotes matched their source transcript segment exactly.
- New evidence quote-noise check: 0 hits for promo CTAs, `inscreva`, `assista tambem`, hashtags, `primeiro link`, `clicar no link`, or description boilerplate.
- `scripts/consolidate_exports.py` completed and reported 253 episode records, 46 assets, 1,406 v1 insights, 88 v2 insights, and 13 acquisition tasks.
- Status after consolidation: 6/50 target episodes fully extracted in v2, 98/754 target chunks extracted, `gate_r1_ready=false`.
- Title uniqueness: 88/88 unique v2 titles.
- `claim_risk` distribution: `low=33`, `medium=51`, `high=4`.
- In-memory compile passed for `scripts/audit_insights_v2_text.py`, `scripts/extract_transcript_insights_llm.py`, and `scripts/consolidate_exports.py` with `python -B`.

Throughput and calibration:

- New session throughput: 30 chunks processed, 24 insights added, 2 episodes closed by chunk. API cost: `$0`.
- Current amended gate progress: 6/15 minimum complete episodes; 98 chunks extracted.
- Remaining to the lower bound is roughly 127 chunks and 9 complete episodes.
- At the observed recent throughput range of 27-35 chunks per session, estimate 4-5 more sessions to reach the 15-episode lower bound and 6-8 sessions to reach the 20-episode upper bound, depending on next-episode chunk counts.

## 2026-07-07 - MSF-R07 autonomous gate completion and blind sample prepare

Owner decision:

- Batch 005 was approved externally: 88/88 unique titles, zero encoding residue, and healthy per-episode density.
- Because `scripts/audit_insights_v2_text.py` is now in the protocol, external review per lot is suspended.
- Continue R07 autonomously only until 15 fully extracted episodes, then generate the blind 40-pair sample with `--mode prepare` and stop. Do not run `--mode score`; blind judgment remains external.

Extraction scope:

- Route: Codex-first manual extraction (`route=codex_manual`), no API.
- Commands were run with `python -B`.
- Episodes completed:
  - `v6luZ9KvmOI`: 14/14 chunks, 10 insights v2.
  - `zoChfFHnlOQ`: 18/18 chunks, 16 insights v2.
  - `qj04cUeaRAw`: 15/15 chunks, 12 insights v2.
  - `cL3FuW8bAMA`: 17/17 chunks, 15 insights v2.
  - `JF2oC44lBG8`: 19/19 chunks, 19 insights v2.
  - `qohJceyapS0`: 17/17 chunks, 15 insights v2.
  - `YcqJ_vrjf-g`: 16/16 chunks, 8 insights v2.
  - `wHdyTM-nVqg`: 19/19 chunks, 14 insights v2.
  - `BbhJn8NXRso`: 13/13 chunks, 12 insights v2.

Validation:

- `scripts/validate_insights_v2.py` returned `VALID` for all 9 new episode files.
- `scripts/audit_insights_v2_text.py` passed: `VALID editorial_text_files=261`.
- New evidence quote check: 121/121 new evidence quotes matched their source transcript segment exactly.
- New evidence quote-noise check: 0 hits for promo CTAs, `inscreva`, `assista tambem`, hashtags, `primeiro link`, `clicar no link`, recommendation cards, or description boilerplate.
- `scripts/consolidate_exports.py` completed and reported 253 episode records, 46 assets, 1,406 v1 insights, 209 v2 insights, and 13 acquisition tasks.
- Status after consolidation: 15/50 target episodes fully extracted in v2, 246/754 target chunks extracted, `gate_r1_ready=true`, amended gate coverage ready.
- Title repetition above 5%: 0. Validation errors: 0.

Blind sample:

- Ran `scripts/generate_insight_v1_v2_review.py --mode prepare --date 2026-07-07 --seed 20260707 --sample-size 40 --target-pairs 40 --target-episodes 15`.
- Wrote blind sample to `data/exports/insight_v1_v2_blind_sample_2026-07-07.csv`.
- Wrote local de-anonymization key to `data/exports/insight_v1_v2_blind_key_2026-07-07.json`.
- Updated `docs/insight-v1-vs-v2-review-2026-07-07.md` as pending blind judgment.
- Did not run `--mode score`.

Throughput and stop point:

- New session throughput: 148 chunks processed, 121 insights added, 9 episodes closed by chunk. API cost: `$0`.
- Time cost: 1 autonomous Codex session; terminal wall-clock was not separately stopwatched.
- Current amended gate progress: 15/15 minimum complete episodes; 246 chunks extracted, inside the expected 225-300 chunk gate range.
- Stop extraction here. Next step is external blind judgment, then Gate R1 decision. Before any post-gate backfill, reopen MSF-R03 as scheduled.

## 2026-07-07 - MSF-R08 blind score and pre-gate remediation

External blind judgment:

- External judge completed `data/exports/insight_v1_v2_blind_sample_2026-07-07_judged.csv`: 40/40 pairs and 160/160 criterion cells filled.
- Ran `scripts/generate_insight_v1_v2_review.py --mode score --judgments data/exports/insight_v1_v2_blind_sample_2026-07-07_judged.csv`.
- Wrote the de-anonymized score report to `docs/insight-v1-vs-v2-review-2026-07-07.md`.
- Score result: specificity `v2=24`, `tie=14`, `v1=2`; evidence_fidelity `v2=19`, `tie=10`, `v1=11`; applicability `v2=39`, `tie=1`, `v1=0`; quote_cleanliness `v2=4`, `tie=18`, `v1=18`.
- Interpretation caveat recorded in the report: applicability is structurally biased toward the side with operational fields; blind-side applicability split was `A=21`, `B=18`, `tie=1`. Specificity and evidence_fidelity remain the decisive criteria.
- Gate R1 was not declared in this session.

Mandatory investigation:

- Confirmed duplicate normalized `specific_takeaway` in the v2 base after blind review, including the judge's Bbh/JF2 cluster.
- Regression source: batch 006 extraction template reused generic `specific_takeaway` text while suffixing titles by chapter. Earlier batches had no per-episode duplicate takeaway clusters in the same check.
- Remediated batch 006 chunk outputs and recombined final `insights_v2.json` files from source chunk outputs.
- Removed or rewrote promo/intro-backed evidence in affected batch 006 items, including `qohJceyapS0-v2-0002`, `qj04cUeaRAw-v2-0001`, `BbhJn8NXRso-v2-0005`, and `JF2oC44lBG8-v2-0019`.
- Differentiated remaining repeated takeaways across batch 006 episodes, then reran the duplicate scan: `duplicate_takeaway_groups=0`, `duplicate_items=0`.

Protocol and validation:

- Added normalized duplicate `specific_takeaway` checking to `scripts/audit_insights_v2_text.py`.
- Added promo/intro patterns to the review quote-noise detector: imersao/treinamento pitch language, intro narration, and `espero que voces gostem`.
- Updated `loops/episode-processing.md` so evidence can span complete segment ranges and post-lot scans include duplicate takeaway checks.
- Full v2 schema validation passed for all 15 `insights_v2.json` files.
- `scripts/audit_insights_v2_text.py` passed: `VALID editorial_text_files=261`.
- Evidence quote check passed across the current v2 base: 207/207 quotes matched their source segment or segment range; 0 quote-noise hits with the updated detector.
- `scripts/consolidate_exports.py` completed and reported 253 episode records, 46 assets, 1,406 v1 insights, 207 v2 insights, and 13 acquisition tasks.
- Status after consolidation: 15/50 target episodes fully extracted in v2, 246/754 target chunks extracted, `gate_r1_ready=true` for amended coverage only. Formal Gate R1 decision remains pending owner review.

## 2026-07-07 - Process taxonomy seed and process_tags post-processing

Scope:

- Documentation/process-taxonomy session only; R07 extraction prompt was not changed.
- External taxonomy seed accepted locally as `taxonomy_version=2026-07-07.1`.

Validation:

- Parsed `data/processed/taxonomy_seed.json` successfully.
- Non-ASCII scan passed for `data/processed/taxonomy_seed.json` and `docs/process-taxonomy.md`: 0 non-ASCII characters in both files.
- Seed structure check passed: 12 `process_area` terms, 58 `process` terms, 0 duplicate ids, 0 invalid `process-*` ids, and 0 invalid process parent references.
- `scripts/validate_insights_v2.py` passed for all 15 current v2 episode files after adding optional `process_tags` support to the v2 schema.

Implementation:

- Extended `scripts/classify_taxonomy.py` to assign `process_tags` as deterministic post-processing over v1/v2 payloads by matching active `process` terms and synonyms from the taxonomy seed.
- Insights with no process match are written to a review queue and receive no generic process fallback tag.
- `scripts/consolidate_exports.py` now preserves `process_tags` in v1/v2 CSV exports when present.
- `loops/episode-processing.md` now requires process-tag classification after each R07 consolidation and reporting of unmatched insight counts.
- MSF-R12 now requires `curated_insights.process_tags` with at least one valid `process-*` tag.
- MSF-R16 now reserves process tables/FKs and outcome annotations linked to used insights.

Classification run:

- Rebuilt exports with `scripts/consolidate_exports.py`: 253 episode records, 46 assets, 1,406 v1 insights, 207 v2 insights, and 13 acquisition tasks.
- Ran process-tag classification on `data/exports/insights_master.json`: 1,406 insights classified; 3 insights without process match written to `data/exports/process_tag_review_queue_v1.json`.
- Ran process-tag classification on `data/exports/insights_v2_master.json`: 207 insights classified; 0 insights without process match written to `data/exports/process_tag_review_queue_v2.json`.

## 2026-07-07 - Gate R1 formal approval

Decision:

- Gate R1 formally APPROVED by the external judge on 2026-07-07 after independent verification of batch 006 remediation.
- Independent verification confirmed 0 duplicate normalized `specific_takeaway` values in v2 and corrected evidence windows after remediation.
- MSF-R07 and MSF-R08 are closed as `done`; R07 extraction remains stopped at the amended gate sample.
- MSF-R14 backfill of the remaining 508 chunks stays deferred until MSF-R03 is reopened and the R2 sequence is handled.

Caveats from the decision:

- `quote_cleanliness` favored v1 in the judged snapshot (`v1=18`, `v2=4`, `tie=18`); the root cause was remediated after scoring.
- `applicability` must be read with structural discount because the side with operational fields can win by format; specificity and evidence_fidelity are the decisive criteria.
- The score and threshold are a pre-remediation floor, not the post-remediation ceiling.
- v1 won 11 evidence_fidelity cells, which confirms the blind instrument was honest enough to surface weaknesses in v2.

Taxonomy validation:

- Revalidated `data/processed/taxonomy_seed.json` with `python -B`: parse succeeded, `taxonomy_version=2026-07-07.1`, 12 `process_area` terms, 58 `process` terms, 0 duplicate ids, 0 invalid `process-*` ids, and 0 invalid process parent references.
- Re-ran non-ASCII scan for `data/processed/taxonomy_seed.json` and `docs/process-taxonomy.md`: 0 non-ASCII characters in both files.
- Both taxonomy files are already tracked in commit `79c376c`; there are no pending taxonomy file changes at this decision point.

Next session:

- Start EPIC R2 with MSF-R09: evaluator LLM with rubric plus citation-fidelity verification.
- Then run MSF-R10: blind test against a no-base baseline using v2 as the source. The R10 blind judgment remains external.
- Reminder remains active: reopen MSF-R03 before any MSF-R14 backfill of the remaining 508 chunks.

## 2026-07-07 - MSF-R09 honest output evaluator and R10 blind prepare

Start guardrail:

- Pushed `main` to `origin/main` before any other work, bringing the remote up to commit `5609130`.
- Read `docs/marketing-swipe-file-handoff.md`, the EPIC R2 block in `docs/marketing-swipe-file-remediation-backlog.md`, and `docs/output-evaluation-rubric.md`.

MSF-R09 implementation:

- Updated `scripts/evaluate_output.py` so the previous keyword score is now `keyword_presence_check`, explicitly marked as a secondary proxy and never the final score.
- Added `schemas/output_evaluation.schema.json` for honest output evaluation reports.
- The honest evaluator route is Codex-first/no API: Codex writes a separate judgment JSON, then the script validates, attaches citation context from local masters/strategy packs, computes the rubric score, and renders JSON/Markdown reports.
- Updated `loops/output-evaluation.md` with the new protocol and the R10 blind prepare workflow.

MSF-R09 results:

- Re-evaluated `data/exports/generated_vsl_lowticket.md`: old keyword proxy 39/40 `pass`; honest rubric score 30/40 `needs_revision`; delta -9.
- Re-evaluated `data/exports/generated_ads_lowticket.md`: old keyword proxy 37/40 `pass`; honest rubric score 30/40 `needs_revision`; delta -7.
- Both reports passed `schemas/output_evaluation.schema.json`.
- Recorded the result in `docs/output-evaluation-review-2026-07-07.md`; README, handoff, and backlog no longer cite 39/40 or 37/40 as proof of value.

MSF-R10 prepare only:

- Generated v2 strategy packs locally from `data/exports/insights_v2_master.json` for the same low-ticket briefing.
- Generated local ignored R10 outputs:
  - with-base v2 VSL/ads: `data/exports/r10_with_base_vsl_lowticket_2026-07-07.md`, `data/exports/r10_with_base_ads_lowticket_2026-07-07.md`
  - no-base baseline VSL/ads: `data/exports/r10_baseline_vsl_lowticket_2026-07-07.md`, `data/exports/r10_baseline_ads_lowticket_2026-07-07.md`
- Added `scripts/generate_output_blind_review.py` and prepared `data/exports/output_r10_blind_sample_2026-07-07.csv` plus local ignored key `data/exports/output_r10_blind_key_2026-07-07.json`.
- Wrote pending report `docs/output-r10-blind-review-2026-07-07.md`.
- Verified the blind CSV has 2 pairs and no `insight_id`, `with_base`, or `baseline` leakage.
- Stopped before judgment: no R10 score was run and Gate R2 remains pending external judge.

Validation:

- Used `.\.venv\Scripts\python.exe -B` throughout.
- Reran non-ASCII scan on tracked changed files before commit.
- Reran `scripts/audit_insights_v2_text.py` for the v2 editorial/audit protocol.
- Reran `git diff --check`.

## 2026-07-07 - MSF-R10 blind score and Gate R2 approval

External blind judgment:

- External judge completed `data/exports/output_r10_blind_sample_2026-07-07_judged.csv`: 2/2 pairs and 16/16 criterion cells.
- Ran `scripts/generate_output_blind_review.py --mode score` with `python -B`, using the local ignored key only after the judged CSV was returned.
- De-anonymized key confirmed side B was `with_base_v2` for both pairs.
- Result: `with_base_v2=14`, `baseline_no_base=0`, `tie=2`; VSL with base won 7/8 and tied 1/8; ads with base won 7/8 and tied 1/8.
- Gate R2 formally APPROVED because output with base won or tied the baseline.

Caveats:

- Judge was blind to label, not style; base vocabulary and mechanics may be recognizable.
- Judgment was anchored in content quality: specificity, mechanics, testability, and operational usefulness, not vocabulary alone.
- Sample limitation: 1 briefing x 2 artifacts. This is sufficient for the formal R2 criterion, but MSF-S09 must validate varied briefings.

Updates:

- Updated `docs/output-r10-blind-review-2026-07-07.md`, `docs/output-evaluation-review-2026-07-07.md`, the remediation backlog, README, and handoff.
- MSF-R09 remains `done`; MSF-R10 is now `done`.
- Next session: EPIC R3 with MSF-R11 diversity in ranking, MSF-R12 first curated_insights lot, and MSF-R13 regenerated packs.

## 2026-07-07 - EPIC R3 retrieval and curation prepare

MSF-R11:

- Updated `scripts/generate_strategy_pack.py` with MMR-style Jaccard diversity using `--diversity-weight` default `0.3`.
- Added `--episode-cap` default `3` so top-N packs are not dominated by one source episode.
- Added `--thesis-cap` default `1` for the top-10 so title-derived near-thesis duplicates do not occupy the decisive block.
- Added `--source curated` to read `data/exports/curated_insights.json`.
- Added `tests/fixtures/strategy_pack_diversity_fixture.json` and `tests/test_strategy_pack_diversity.py`.
- Test result with `python -B`: `VALID strategy_pack_diversity_fixture`.

MSF-R12:

- Added `scripts/generate_curated_insights.py`.
- Generated local ignored `data/exports/curated_insights.json` from 207 v2 insights.
- Curated lot count: 125 items; 113 clusters; 0 items below score floor 50 included.
- Score distribution: min 90, max 100, average 96.67.
- Process tags: 125/125 have at least 1 valid `process-*` tag and at least 1 first-wave priority process tag.
- Owner review sample: `data/exports/curated_insights_owner_review_sample_2026-07-07.csv` with 30 rows.
- Report: `docs/curated-insights-r12-review-2026-07-07.md`.

MSF-R13:

- Regenerated curated packs:
  - `data/exports/strategy_pack_curated_vsl_lowticket_2026-07-07.json`
  - `data/exports/strategy_pack_curated_ads_lowticket_2026-07-07.json`
- Compared curated packs against old v2 packs in `docs/strategy-pack-r13-comparison-2026-07-07.md`.
- VSL pack: top-20 max episode count changed from 5 to 3; top-10 average Jaccard changed from 0.1099 to 0.1025; honest evaluator score 33/40 `pass`, citation fidelity `pass`.
- Ads pack: top-20 max episode count changed from 10 to 3; top-10 average Jaccard changed from 0.4912 to 0.0800; honest evaluator score 35/40 `pass`, citation fidelity `pass`; no repeated title-derived thesis remained in the top-10.

Decision state:

- MSF-R11 is `done`.
- MSF-R12 is `ready_for_owner_review`.
- MSF-R13 is `ready_for_external_review`.
- Gate R3 was not declared. External review remains required before MSF-S, MSF-R14 backfill, Supabase, or MCP work.

Validation:

- All commands used `.\.venv\Scripts\python.exe -B`.
- Reran the R11 fixture test.
- Reran in-memory syntax compilation for edited Python scripts.
- Reran non-ASCII scans on tracked changed files and R12 sample/report.
- Reran `scripts/audit_insights_v2_text.py`.
- Reran `git diff --check`.

## 2026-07-07 - Gate R3 formal approval

Decision:

- Gate R3 formally APPROVED on 2026-07-07.
- Owner review of the R12 30-item sample is complete: the owner kept the filled sample decisions as indicated, with no mass rejection.
- External technical review approved the R3 criteria: packs have no dominant duplication, curated lot is integral, and honest evaluator results are `pass`.
- MSF-R11, MSF-R12, and MSF-R13 are now `done`.

Registered observations:

- `editorial_score` is compressed in the first curated lot (min 90, median 97). Calibrate the scoring rubric with owner annotations before the next curated batch.
- One title has a boilerplate suffix to rewrite before the next pack refresh: `...em lateralizar`.
- `process-copy-anuncios` has 18 curated items. This is sufficient to start MSF-S; later backfill should expand coverage.

Next session:

- EPIC MSF-S is unblocked.
- Start with MSF-S01: skill contract.
- Then MSF-S02: retrieval by `process_tags`.
- Updated `docs/marketing-swipe-file-skills-backlog.md`: MSF-S01 and MSF-S02 moved from gate-blocked to `not_started`; downstream skills remain blocked by their own dependencies.
- MSF-R14 backfill, Supabase, and MCP remain later work. Reopen MSF-R03 before any MSF-R14 backfill of the remaining 508 chunks.

## 2026-07-07 - Owner review CSV encoding remediation

Bug:

- External audit confirmed that `data/exports/curated_insights_owner_review_sample_2026-07-07.csv` corrupted `evidence_quote` by deleting accented characters during CSV export.
- Source bases remained integral: `data/exports/insights_v2_master.json` and `data/exports/curated_insights.json` were not affected.

Fix:

- Updated `scripts/generate_curated_insights.py` so evidence quotes are copied verbatim from source evidence and owner-facing review CSVs are written as `utf-8-sig`.
- Added NFKD-based ASCII transliteration helper for future editorial-only ASCII needs; ASCII deletion via `errors=ignore` is no longer used in the review export path.
- Preserved existing `owner_decision` and `owner_notes` when regenerating the sample.
- Extended `scripts/audit_insights_v2_text.py` to fail on known accent-deletion artifacts in editorial fields and generated CSV/MD exports.

Validation:

- Regenerated the owner review sample locally after the fix.
- Confirmed 30/30 sample `evidence_quote` values match the corresponding first evidence quote in `curated_insights.json`.
- Confirmed 29/30 sample rows now preserve non-ASCII evidence text where present; the CSV starts with UTF-8 BOM (`efbbbf`).
- Confirmed existing owner decisions/notes remained populated: 16 `aprovar`, 9 `aprovar_com_ajuste_evidencia`, 3 `revisar_antes_default`, 2 `mesclar_manter_um`; 30/30 notes populated.
- `scripts/audit_insights_v2_text.py` passed on 261 v2 files and 43 generated CSV/MD exports; broken accent-deletion pattern hits: 0.
- The Gate R3 approval remains valid; the corrected quotes are more readable than the reviewed export.

## 2026-07-07 - Layered writing policy before MSF-S01

Decision:

- Owner formalized the writing policy after the R12 sample review and the CSV normalizer bug fix.
- Internal layer uses ASCII only by Unicode NFKD transliteration when ASCII is required: data fields, ids, tags, titles, takeaways, repo docs, internal playbooks, and retrieval recipes. No character deletion.
- Evidence quotes remain verbatim UTF-8 with accents in every artifact, including CSV exports written as `utf-8-sig`.
- Final human-facing outputs (VSL, ads, quiz, emails, templates, and skill examples) must use full pt-BR accentuation and correct spelling.

Implementation:

- Registered the policy in `docs/marketing-swipe-file-handoff.md` and in the anatomy/acceptance of `docs/marketing-swipe-file-skills-backlog.md`.
- Updated `docs/output-evaluation-rubric.md` and `scripts/evaluate_output.py`: MSF-R09 now emits `language_encoding_check`; known ASCII-stripping artifacts fail quality, and final pt-BR outputs without accented letters require revision before approval.
- Centralized the accent-deletion wordlist in `scripts/msf_common.py` and kept `scripts/audit_insights_v2_text.py` using it across generated CSV/MD text.
- Clarified scan scope in `loops/episode-processing.md`: non-ASCII scans apply to internal editorial fields and must not conflict with verbatim quotes or final pt-BR outputs.

Next:

- MSF-S01 and MSF-S02 remain `not_started` and will begin in a separate session, per owner instruction.

## 2026-07-07 - MSF-S01/MSF-S02 foundation

MSF-S01:

- Added the instantiable process-skill template at `skills/_templates/msf-process-skill/`.
- Added `schemas/msf_process_skill_contract.schema.json`.
- Added `scripts/create_process_skill.py` to instantiate `skills/msf-process-{slug}/` from the template and validate requested `process_tags` against `data/processed/taxonomy_seed.json`.
- Added `scripts/validate_process_skill.py` to validate contract shape, required files, frontmatter, process tags, citation markers, internal ASCII policy, and the Definition of Done checklist. `--require-done` requires all checklist items to be `pass`.
- The contract records the citation format `[insight:<insight_id>]`, generic marker `[generic-practice]`, and layered writing policy: internal ASCII by NFKD, evidence quotes verbatim UTF-8, final outputs in full pt-BR.

MSF-S02:

- Updated `scripts/search_insights.py` with `--source`, default `curated`, and `--process-tags` / `--process-tag-mode any|all`.
- Updated `scripts/generate_strategy_pack.py` so `curated_insights` is the default source, `--process-tags` filters candidates, and pack JSON records `process_tag_filter`.
- Preserved MSF-R11 controls: MMR/Jaccard diversity, `--episode-cap`, and `--thesis-cap`.
- Hardened `keyword_score` to match multi-word keywords against normalized source text instead of a joined token set, avoiding nondeterministic ordering in the diversity fixture.
- Updated `scripts/msf_common.py` with shared process-tag parsing/matching helpers and richer curated insight text for search.
- Updated `skills/marketing-swipe-file-retrieve/` with curated/process-tag examples.
- Added tests: `tests/test_process_skill_contract.py` and `tests/test_process_tag_retrieval.py`.

Validation:

- `.\.venv\Scripts\python.exe -B tests\test_process_skill_contract.py` -> `VALID process_skill_contract`.
- `.\.venv\Scripts\python.exe -B tests\test_process_tag_retrieval.py` -> `VALID process_tag_retrieval`.
- `.\.venv\Scripts\python.exe -B tests\test_strategy_pack_diversity.py` repeated 5x -> `VALID strategy_pack_diversity_fixture`.
- `.\.venv\Scripts\python.exe -B scripts\validate_process_skill.py .tmp\process-skill-smoke\msf-process-copy-vsl` -> `VALID process_skill`.
- Smoke generated a curated VSL pack with `--process-tags process-copy-vsl,process-mecanismo-big-idea`; all selected insights came from the requested tags and preserved episode/thesis diversity.

Decision state:

- MSF-S01 is `done`.
- MSF-S02 is `done`.
- No MSF-S03..S07 process skill was started.
- Next MSF-S step: MSF-S08 transversal modules, then instantiate the first real process skill in the documented density order.

External review:

- Foundation MSF-S01/MSF-S02 approved after external review: tests pass, the template has the full required file set, the validator enforces placeholders/checklist contract, `writing_policy` is present in the contract, and retrieval defaults to curated insights with `--process-tags`.

## 2026-07-07 - MSF-S08 transversal copy modules

Implementation:

- Created `skills/_modules/msf-transversal-copy/` as a shared module set, not as standalone active process skills.
- Added `transversal:mecanismo-big-idea` for `process-mecanismo-big-idea`.
- Added `transversal:prova-depoimentos` for `process-prova-depoimentos`.
- Added `schemas/msf_transversal_module_contract.schema.json`.
- Added `scripts/validate_transversal_modules.py`.
- Added `tests/test_transversal_modules_contract.py`.
- Updated the process-skill template so future S03-S07 skills import shared module files by reference instead of copying shared playbook content.
- Added owner-audit packet: `docs/msf-s08-transversal-modules-review-2026-07-07.md`.

Audit state:

- Current local `curated_insights` coverage: 30 items for `process-mecanismo-big-idea` and 33 items for `process-prova-depoimentos`.
- Both modules are declared consumable by S03-S07, satisfying the "at least two skills" S08 requirement.
- External audit approved MSF-S08 on 2026-07-07: all 17 citations resolve to real `curated_insights`, carry the declared tag, and pass No Invention.
- The mechanism/proof boundaries are approved.
- `module.contract.json` now marks the module set and both modules as `approved`.
- `schemas/msf_process_skill_contract.schema.json` and the process-skill template now carry `module_inheritance_policy` for S04+: deduplicate evidence counts by `insight_id` across imported modules, especially `zoChfFHnlOQ-v2-0008` and `mCaFyZpXJdE-v2-0011`, and keep process-specific logic in the process skill while transversal claims stay at principle level.
- MSF-S08 is `done`.
- MSF-S04 is released as the next real process skill; S03/S05-S07 remain after S04 validates the skill -> retrieval -> rubric -> blind-test pipeline.
- No S04/S03-S07 process skill was started in this close-out.

Validation:

- `.\.venv\Scripts\python.exe -B scripts\validate_transversal_modules.py skills\_modules\msf-transversal-copy` -> `VALID transversal_modules`.
- `.\.venv\Scripts\python.exe -B tests\test_transversal_modules_contract.py` -> `VALID transversal_modules_contract`.
- Existing S01/S02 regressions still passed: `tests\test_process_skill_contract.py`, `tests\test_process_tag_retrieval.py`, and `tests\test_strategy_pack_diversity.py`.
- Contract/schema JSON parse passed for process-skill and transversal-module schemas/contracts.
- In-memory compile passed for the touched Python scripts.
- Non-ASCII scan passed on the changed internal files.
- `git diff --check` passed.
- Smoke packs generated 8 selected insights for each transversal tag, and all selected insights contained the requested tag.

## 2026-07-08 - MSF-S04 offer-construction skill and S09 blind prepare

Implementation:

- Created `skills/msf-process-construcao-oferta/` with
  `scripts/create_process_skill.py`.
- Filled the 8-file process-skill anatomy: `SKILL.md`,
  `skill.contract.json`, `retrieval.md`, `rubric.md`,
  `templates/output-template.md`, `examples/briefing.md`,
  `examples/output-approved.md`, and `agents/openai.yaml`.
- Imported `transversal:mecanismo-big-idea` and
  `transversal:prova-depoimentos` by reference.
- Applied `module_inheritance_policy`: dedupe evidence counts by unique
  `insight_id` across modules, especially `zoChfFHnlOQ-v2-0008` and
  `mCaFyZpXJdE-v2-0011`; offer-specific pricing, anchoring, stack, bonus,
  guarantee, value ladder, CTA, and backend logic remain in S04.
- Updated `skills/_templates/msf-process-skill/skill.contract.json` so future
  process skills require `agents/openai.yaml`.
- Synced the text status of `skills/_modules/msf-transversal-copy/` module
  docs to `approved`.

S09 prepare:

- Generated 3 varied blind offer pairs for owner judgment:
  - health/pilates low ticket;
  - B2B LGPD diagnostic offer;
  - recurring guitar education subscription.
- Wrote the blind sample to
  `data/exports/output_s09_blind_sample_2026-07-08.csv`.
- Wrote the hidden key to
  `data/exports/output_s09_blind_key_2026-07-08.json`.
- Generated audit strategy packs for each briefing:
  - `data/exports/strategy_pack_s09_offer_001_2026-07-08.*`
  - `data/exports/strategy_pack_s09_offer_002_2026-07-08.*`
  - `data/exports/strategy_pack_s09_offer_003_2026-07-08.*`
- The CSV has blank offer-rubric fields and no source-label leakage
  (`with_s04_skill`, `no_skill_no_base`, `with_base`, `baseline`, or
  `insight:`).
- No S09 verdict was generated. Judgment remains external.

Decision state:

- MSF-S04 moved to owner judgment with status `ready_for_owner_audit`.
- MSF-S09 is `in_progress` for S04 only.
- S03/S05-S07 remain blocked until S09 approves the offer skill.
- No commit was created, per owner instruction.

Validation:

- `.\.venv\Scripts\python.exe -B scripts\validate_process_skill.py skills\msf-process-construcao-oferta` -> `VALID process_skill`.
- `.\.venv\Scripts\python.exe -B scripts\validate_transversal_modules.py skills\_modules\msf-transversal-copy` -> `VALID transversal_modules`.
- `.\.venv\Scripts\python.exe -B tests\test_process_skill_contract.py` -> `VALID process_skill_contract`.
- `.\.venv\Scripts\python.exe -B tests\test_process_tag_retrieval.py` -> `VALID process_tag_retrieval`.
- `.\.venv\Scripts\python.exe -B tests\test_transversal_modules_contract.py` -> `VALID transversal_modules_contract`.
- `.\.venv\Scripts\python.exe -B tests\test_strategy_pack_diversity.py` -> `VALID strategy_pack_diversity_fixture`.
- S09 blind CSV structural check passed: 3 pairs, 10 blank judging fields,
  hidden key has 3 pairs.
- Contract/key JSON parse passed.
- Internal non-ASCII scan passed for S04 internal files, updated module docs,
  template contract, and skills backlog.
- `git diff --check` passed.

## 2026-07-08 - MSF-S09 offer gate result

Inputs:

- Judged blind CSV:
  `data/exports/output_s09_blind_sample_2026-07-08_judged.csv`.
- Hidden key:
  `data/exports/output_s09_blind_key_2026-07-08.json`.
- Result report:
  `docs/msf-s09-offer-gate-result-2026-07-08.md`.
- Judge: Claude Opus 4.8, key not opened during judgment.
- Blind caveat: blind de rotulo, nao de estilo.

Apuration:

- Pair winners after key mapping: com skill 3, sem skill 0, empates 0.
- Criterion winners: com skill 24, sem skill 0, empates 0.
- Commercial combined criterion (`mechanism_belief_bridge`,
  `pricing_anchoring`, `proof_claim_control`): com skill 3, sem skill 0,
  empates 0.
- Weak recurring criteria: none.
- Verdict: PASS.

Decision state:

- MSF-S04 is `done`.
- `msf-process-construcao-oferta` is approved; its
  `validation_checklist` is marked `pass`.
- MSF-S03 is released as the next real process skill.
- MSF-S05/MSF-S06/MSF-S07 remain blocked until S03 validates its own skill ->
  retrieval -> rubric -> blind-test pipeline.
- External independent audit confirmed PASS, citation resolution against
  curated insights, No Invention, and overlap-id dedupe.
- Owner requested commit + push of the approved S04/S09 trail, including the
  judged CSV and ignored S09 exports for audit history.
- Next S09 protocol note: vary briefings more (N > 3 when feasible) and
  alternate the no-skill baseline author where possible.

Validation:

- `.\.venv\Scripts\python.exe -B scripts\validate_process_skill.py skills\msf-process-construcao-oferta --require-done` -> `VALID process_skill`.
- `.\.venv\Scripts\python.exe -B scripts\validate_transversal_modules.py skills\_modules\msf-transversal-copy` -> `VALID transversal_modules`.
- Regressions passed: `tests\test_process_skill_contract.py`,
  `tests\test_process_tag_retrieval.py`,
  `tests\test_transversal_modules_contract.py`, and
  `tests\test_strategy_pack_diversity.py`.
- S09 apuration check passed: verdict PASS, 3 pair wins with skill, 24
  criterion wins with skill, and 3 commercial combined wins with skill.
- Contract/key JSON parse passed.
- Internal non-ASCII scan passed.
- `git diff --check` passed.

## 2026-07-08 - MSF-S03 copy VSL skill and S09 blind prepare

Inputs:

- Owner requested MSF-S03 as the next real process skill after S04/S09 PASS.
- Skill under test: `skills/msf-process-copy-vsl/`.
- Primary process tag: `process-copy-vsl`.
- Imported transversal module tags: `process-mecanismo-big-idea` and
  `process-prova-depoimentos`.

Implementation:

- Created `skills/msf-process-copy-vsl/` with
  `scripts/create_process_skill.py`.
- Filled the 8 process-skill files: `SKILL.md`, `skill.contract.json`,
  `retrieval.md`, `rubric.md`, `templates/output-template.md`,
  `examples/briefing.md`, `examples/output-approved.md`, and
  `agents/openai.yaml`.
- Kept internal playbook/retrieval/rubric/contract text ASCII; final template
  and examples use full pt-BR accents.
- Imported transversal modules by reference and preserved the inherited
  `module_inheritance_policy`: dedupe evidence by `insight_id`, count
  `zoChfFHnlOQ-v2-0008` and `mCaFyZpXJdE-v2-0011` once, and keep VSL-specific
  lead, structure, proof placement, objections, offer bridge, and CTA inside
  the skill.
- Aligned `rubric.md` to `docs/output-evaluation-rubric.md` with criteria:
  clarity, curiosity, specificity, mechanism/belief, proof, objection
  handling, offer bridge, and base usage.
- Commercial combined criterion for VSL: `mechanism_belief_score`,
  `proof_score`, and `objection_handling_score`.

S09 blind sample:

- Prepared 4 varied VSL briefings:
  - `S09-VSL-001` health behavior / responsible weight loss.
  - `S09-VSL-002` B2B consulting proposal workshop.
  - `S09-VSL-003` personal finance / overdraft cycle.
  - `S09-VSL-004` guitar subscription for adult beginners.
- Wrote blind CSV:
  `data/exports/output_s09_vsl_blind_sample_2026-07-08.csv`.
- Wrote hidden key:
  `data/exports/output_s09_vsl_blind_key_2026-07-08.json`.
- Wrote strategy packs:
  - `data/exports/strategy_pack_s09_vsl_001_2026-07-08.*`
  - `data/exports/strategy_pack_s09_vsl_002_2026-07-08.*`
  - `data/exports/strategy_pack_s09_vsl_003_2026-07-08.*`
  - `data/exports/strategy_pack_s09_vsl_004_2026-07-08.*`
- CSV has blank VSL-rubric fields and no source-label leakage
  (`with_s03`, `no_skill`, `baseline`, `com skill`, `sem skill`,
  `curated`, `Marketing Swipe`, or `insight:`).
- No S09 verdict was generated. Judgment remains external.

Decision state:

- MSF-S03 moved to owner judgment with status `ready_for_owner_audit`.
- MSF-S09 is `in_progress` for S03 VSL.
- MSF-S05/MSF-S06/MSF-S07 remain blocked until S03 validates its own skill ->
  retrieval -> rubric -> blind-test pipeline.
- No commit was created, per owner instruction.

Validation:

- `.\.venv\Scripts\python.exe -B scripts\validate_process_skill.py skills\msf-process-copy-vsl --require-done` -> `VALID process_skill`.
- `.\.venv\Scripts\python.exe -B scripts\validate_transversal_modules.py skills\_modules\msf-transversal-copy` -> `VALID transversal_modules`.
- Regressions passed: `tests\test_process_skill_contract.py`,
  `tests\test_process_tag_retrieval.py`,
  `tests\test_transversal_modules_contract.py`, and
  `tests\test_strategy_pack_diversity.py`.
- S03 citation No Invention check passed: 23 real playbook citations resolve to
  `curated_insights` and all carry `process-copy-vsl`.
- S09 blind CSV structural check passed: 4 pairs and 10 blank judging fields.
- Source-leak scan on the blind CSV passed.
- Internal non-ASCII scan passed for S03 internal files, backlog, and
  execution log.
- `git diff --check` passed.

## 2026-07-08 - MSF-S09 VSL gate apuration

Inputs:

- Judged blind CSV:
  `data/exports/output_s09_vsl_blind_sample_2026-07-08_judged.csv`.
- Hidden key:
  `data/exports/output_s09_vsl_blind_key_2026-07-08.json`.
- Result report:
  `docs/msf-s09-vsl-gate-result-2026-07-08.md`.
- Judge: Claude Opus 4.8, key not opened during judgment.
- Blind caveat: blind de rotulo, nao de estilo.

Apuration:

- Key mapping:
  - `S09-VSL-001`: A = sem skill, B = com skill; blind winner B.
  - `S09-VSL-002`: A = com skill, B = sem skill; blind winner A.
  - `S09-VSL-003`: A = com skill, B = sem skill; blind winner A.
  - `S09-VSL-004`: A = sem skill, B = com skill; blind winner B.
- Pair winners after key mapping: com skill 4, sem skill 0, empates 0.
- Criterion winners: com skill 26, sem skill 0, empates 6.
- Commercial combined criterion (`mechanism_belief_score`, `proof_score`,
  `objection_handling_score`): com skill 10 cells, sem skill 0, empates 2.
- Commercial pair result: com skill wins or ties the commercial core in all 4
  pairs and loses none.

Encoding verification:

- `S09-VSL-001` output B maps to `with_s03_skill`.
- Output B contains one orphan question-mark artifact:
  `...antes do cansa?o bater...`.
- Other with-skill outputs have no orphan question marks. Legitimate question
  punctuation was ignored.
- Added `transliterate_ascii` and `orphan_question_mark_contexts` helpers in
  `scripts/msf_common.py`.
- Extended `scripts/audit_insights_v2_text.py` to flag orphan question marks
  in generated text.
- Preserved the judged CSV unchanged and wrote an encoding-fixed sample copy:
  `data/exports/output_s09_vsl_blind_sample_2026-07-08_encoding_fixed.csv`.

Decision state:

- Verdict: `CONCERNS`.
- Commercial signal passes, but MSF-S03 is not approved until owner
  reconfirms the encoding-fixed sample.
- MSF-S03 remains `ready_for_owner_audit`.
- `msf-process-copy-vsl` is not marked approved; `blind_baseline_test` is back
  to `pending`.
- MSF-S05/MSF-S06/MSF-S07 remain blocked.
- No commit was created, per owner instruction.

Validation:

- `.\.venv\Scripts\python.exe -B scripts\validate_process_skill.py skills\msf-process-copy-vsl` -> `VALID process_skill`.
- `.\.venv\Scripts\python.exe -B scripts\validate_process_skill.py skills\msf-process-copy-vsl --require-done` intentionally remains blocked with `checklist_not_pass=blind_baseline_test` until owner reconfirmation.
- `.\.venv\Scripts\python.exe -B scripts\validate_transversal_modules.py skills\_modules\msf-transversal-copy` -> `VALID transversal_modules`.
- Regressions passed: `tests\test_process_skill_contract.py`,
  `tests\test_process_tag_retrieval.py`,
  `tests\test_transversal_modules_contract.py`, and
  `tests\test_strategy_pack_diversity.py`.
- S09 VSL apuration check passed: verdict CONCERNS, commercial PASS, 4 pair
  wins with skill, 26 criterion wins with skill, 10 commercial cells with
  skill, and 6 ties.
- S03 citation No Invention check passed: 23 real playbook citations resolve
  to `curated_insights` and all carry `process-copy-vsl`.
- Encoding helper check passed: `cansaco` is the expected ASCII transliteration,
  and
  `orphan_question_mark_contexts` flags `cansa?o` but not legitimate question
  punctuation.
- With-skill orphan scan: judged CSV has 1 preserved artifact; encoding-fixed
  sample has 0.
- Internal non-ASCII scan passed.
- `git diff --check` passed.

## 2026-07-08 - MSF-S03 copy VSL approval after encoding reconfirmation

Inputs:

- Owner reconfirmed MSF-S03 after external audit of the encoding-fixed sample.
- Commercial PASS stands: com skill won 4/4 pairs, 26 criteria, lost 0, and
  tied 6.
- Commercial core stands: com skill 10 cells, sem skill 0, empates 2.
- The encoding-fixed sample differs from the original blind sample by exactly
  one character-level correction: `cansa?o` -> `cansaco`.
- The judged CSV remains preserved unchanged with the original `?` artifact as
  audit evidence.

Implementation:

- Updated `skills/msf-process-copy-vsl/SKILL.md` to `approved`.
- Updated `skills/msf-process-copy-vsl/skill.contract.json` so
  `blind_baseline_test` is `pass`.
- Updated `docs/msf-s09-vsl-gate-result-2026-07-08.md` from `CONCERNS` to
  `PASS`, recording the resolved encoding concern.
- Updated `docs/marketing-swipe-file-skills-backlog.md`: MSF-S03 is `done`,
  `msf-process-copy-vsl` is approved, MSF-S05 is `ready`, and
  MSF-S06/MSF-S07 remain blocked until S05 passes its own S09.

Validation:

- `.\.venv\Scripts\python.exe -B scripts\validate_process_skill.py skills\msf-process-copy-vsl --require-done` -> `VALID process_skill`.
- `.\.venv\Scripts\python.exe -B scripts\validate_transversal_modules.py skills\_modules\msf-transversal-copy` -> `VALID transversal_modules`.
- `pytest` is not installed in the repo `.venv`; the four regression files were
  executed through their `test_*` functions directly and passed:
  `tests\test_process_skill_contract.py`, `tests\test_process_tag_retrieval.py`,
  `tests\test_transversal_modules_contract.py`, and
  `tests\test_strategy_pack_diversity.py`.
- S09 VSL apuration check passed: verdict PASS, 4 pair wins with skill, 26
  criterion wins with skill, 10 commercial cells with skill, and 6 ties.
- S03 citation No Invention check passed: 23 real playbook citations resolve to
  `curated_insights` and all carry `process-copy-vsl`.
- Encoding guard check passed: `transliterate_ascii` converts the accented
  source to `cansaco` by NFKD, `orphan_question_mark_contexts` catches
  `cansa?o`, judged CSV preserves 1 orphan artifact, and the encoding-fixed
  sample has 0.
- Delta check passed: original blind sample vs encoding-fixed sample differs by
  exactly one character (`?` -> `c`) for `cansa?o` -> `cansaco`.
- Method note for S05 S09: keep honest baselines, and run
  `orphan_question_mark` guard plus internal non-ASCII scan on with-skill
  outputs before sending the blind sample to the external judge.

## 2026-07-08 - MSF-S05 copy ads skill and S09 blind prepare

Inputs:

- Owner requested MSF-S05 as the next real process skill after S03/S09 VSL PASS.
- Skill under test: `skills/msf-process-copy-anuncios/`.
- Primary process tag: `process-copy-anuncios`.
- Imported transversal module tags: `process-mecanismo-big-idea` and
  `process-prova-depoimentos`.
- S06/S07 remain blocked until S05 passes its own S09.

Implementation:

- Created `skills/msf-process-copy-anuncios/` with
  `scripts/create_process_skill.py`.
- Filled the 8 process-skill files: `SKILL.md`, `skill.contract.json`,
  `retrieval.md`, `rubric.md`, `templates/output-template.md`,
  `examples/briefing.md`, `examples/output-approved.md`, and
  `agents/openai.yaml`.
- Kept internal playbook/retrieval/rubric/contract text ASCII; final template
  and examples use full pt-BR accents.
- Imported transversal modules by reference and preserved the inherited
  `module_inheritance_policy`: dedupe evidence by `insight_id`, count
  `zoChfFHnlOQ-v2-0008` and `mCaFyZpXJdE-v2-0011` once, and keep ad-specific
  hook, angle, script, variation logic, platform fit, creative direction, CTA,
  and testing order inside the skill.
- Aligned `rubric.md` to `docs/output-evaluation-rubric.md` with criteria:
  hook strength, angle clarity, avatar fit, proof or plausibility,
  testability, platform fit, creative direction, and base usage.
- Commercial combined criterion for ads: `hook_strength_score`,
  `proof_or_plausibility_score`, and `testability_score`.

S09 blind sample:

- Prepared 4 varied ads briefings:
  - `S09-ADS-001` Meta feed image ad for home-fitness quiz.
  - `S09-ADS-002` Reels/short-video ad for small-store AI course.
  - `S09-ADS-003` Google Search ad for clinic financial diagnosis.
  - `S09-ADS-004` Google Display retargeting ad for HR onboarding SaaS.
- Wrote blind CSV:
  `data/exports/output_s09_ads_blind_sample_2026-07-08.csv`.
- Wrote hidden key:
  `data/exports/output_s09_ads_blind_key_2026-07-08.json`.
- Wrote strategy packs:
  - `data/exports/strategy_pack_s09_ads_001_2026-07-08.*`
  - `data/exports/strategy_pack_s09_ads_002_2026-07-08.*`
  - `data/exports/strategy_pack_s09_ads_003_2026-07-08.*`
  - `data/exports/strategy_pack_s09_ads_004_2026-07-08.*`
- Baselines were written as honest copy attempts, not deliberately generic.
- The first inline CSV generation path exposed PowerShell accent loss, so the
  sample was regenerated through ASCII-only Unicode escapes and rechecked.
- CSV has blank ads-rubric fields and no source-label leakage (`with_s05`,
  `no_skill`, `baseline`, `com skill`, `sem skill`, `curated`,
  `Marketing Swipe`, or `insight:`).
- No S09 verdict was generated. Judgment remains external.

Decision state:

- MSF-S05 moved to owner judgment with status `ready_for_owner_audit`.
- MSF-S09 is `in_progress` for S05 ads.
- MSF-S06/MSF-S07 remain blocked until S05 validates its own skill ->
  retrieval -> rubric -> blind-test pipeline.
- No commit was created, per owner instruction.

Validation:

- `.\.venv\Scripts\python.exe -B scripts\validate_process_skill.py skills\msf-process-copy-anuncios` -> `VALID process_skill`.
- `.\.venv\Scripts\python.exe -B scripts\validate_transversal_modules.py skills\_modules\msf-transversal-copy` -> `VALID transversal_modules`.
- `pytest` is not installed in the repo `.venv`; the four regression files were
  executed through their `test_*` functions directly and passed:
  `tests\test_process_skill_contract.py`, `tests\test_process_tag_retrieval.py`,
  `tests\test_transversal_modules_contract.py`, and
  `tests\test_strategy_pack_diversity.py`.
- S05 citation No Invention check passed: 18 real playbook citations resolve to
  `curated_insights` and all carry `process-copy-anuncios`.
- S09 ads key citation check passed: 12 unique with-skill citations resolve to
  `curated_insights` and all carry `process-copy-anuncios`.
- S09 ads blind CSV structural check passed: 4 pairs and 40 blank judging
  fields.
- Source-leak scan on the blind CSV passed.
- With-skill output encoding guard passed: 0 orphan question marks and all 4
  with-skill outputs preserve pt-BR accents.
- `git diff --check` passed before docs update; final scan and diff check run
  after this log update.

## 2026-07-08 - MSF-S09 ads apuration and S05 approval

Inputs:

- Owner-provided blind judgment:
  `data/exports/output_s09_ads_blind_sample_2026-07-08_judged.csv`.
- Hidden key opened only after judging:
  `data/exports/output_s09_ads_blind_key_2026-07-08.json`.
- Skill under test: `skills/msf-process-copy-anuncios/`.
- PASS rule: with-skill must win or tie the commercial core in every pair, lose
  no pair overall, and have no pending encoding defect in with-skill outputs.

Apuration:

- A/B mapping by key:
  - `S09-ADS-001`: A = with skill, B = no skill; blind winner A.
  - `S09-ADS-002`: A = no skill, B = with skill; blind winner B.
  - `S09-ADS-003`: A = with skill, B = no skill; blind winner A.
  - `S09-ADS-004`: A = no skill, B = with skill; blind winner B.
- Pair result: with skill 4, no skill 0, ties 0.
- Criterion result: with skill 30, no skill 0, ties 2.
- The 2 ties were `platform_fit_score` in pairs 001 and 003.
- Commercial core (`hook_strength_score`, `proof_or_plausibility_score`,
  `testability_score`): with skill 12, no skill 0, ties 0.
- Gate report written to
  `docs/msf-s09-ads-gate-result-2026-07-08.md`.

Encoding:

- `orphan_question_mark_contexts` found 0 orphan question marks in the 4
  with-skill outputs selected through the hidden key.
- Raw non-ASCII scan of with-skill final outputs found only normal Latin
  accent codepoints (`U+00C9`, `U+00E1`, `U+00E2`, `U+00E3`, `U+00E7`,
  `U+00E9`, `U+00EA`, `U+00ED`, `U+00F3`, `U+00F4`, `U+00F5`, `U+00FA`).
  These are valid final-output accents under the layered writing policy, not
  encoding defects.
- Internal non-ASCII scan passed for the ads skill internal files and docs.

Decision state:

- Verdict: `PASS`.
- MSF-S05 marked `done` in the skills backlog.
- `msf-process-copy-anuncios` marked approved in `SKILL.md`.
- `blind_baseline_test` marked `pass` in
  `skills/msf-process-copy-anuncios/skill.contract.json`.
- MSF-S06 (`msf-process-produto-low-ticket`) released as the next real skill.
- MSF-S07 remains blocked until S06 passes its own S09.
- No commit was created, per owner instruction.

Validation:

- `.\.venv\Scripts\python.exe -B scripts\validate_process_skill.py skills\msf-process-copy-anuncios --require-done` -> `VALID process_skill`.
- `.\.venv\Scripts\python.exe -B scripts\validate_transversal_modules.py skills\_modules\msf-transversal-copy` -> `VALID transversal_modules`.
- Direct regression execution passed for:
  `tests\test_process_skill_contract.py`, `tests\test_process_tag_retrieval.py`,
  `tests\test_transversal_modules_contract.py`, and
  `tests\test_strategy_pack_diversity.py`.
- Reproducible S09 ads apuration check passed:
  pair `4-0-0`, criteria `30-0-2`, commercial core `12-0-0`.

## 2026-07-08 - MSF-S05 external approval and versioning closure

Inputs:

- Owner reported independent external audit approval for MSF-S05/S09 Ads.
- External audit reproduced the hidden-key mapping: with-skill won 4/4 pairs.
- External audit confirmed No Invention for 12 with-skill citations resolving to
  real `curated_insights` with `process-copy-anuncios`.
- External audit confirmed encoding clean, with no remaining caveat.

Versioning scope:

- Versioned the S05 skill directory:
  `skills/msf-process-copy-anuncios/`.
- Versioned the S09 Ads gate report:
  `docs/msf-s09-ads-gate-result-2026-07-08.md`.
- Versioned backlog and execution-log updates.
- Kept ignored S09 Ads exports local-only under `data/exports/`, per owner
  instruction; the versioned gate report records the result numbers
  `4-0-0`, `30-0-2`, and `12-0-0`.
- MSF-S06 remains the next real skill to start only after explicit owner prompt.

Closure validation:

- `.\.venv\Scripts\python.exe -B scripts\validate_process_skill.py skills\msf-process-copy-anuncios --require-done` -> `VALID process_skill`.
- Local S09 Ads key No Invention check passed: 20 citation uses, 12 unique
  citations, 0 missing, and 0 without `process-copy-anuncios`.
- Internal non-ASCII scan passed for docs and S05 internal skill files.
- `git diff --check` passed.

## 2026-07-08 - MSF-S06 low-ticket product skill and S09 blind prepare

Inputs:

- Owner requested MSF-S06 as the next real process skill after S05/S09 Ads
  PASS.
- Skill under test: `skills/msf-process-produto-low-ticket/`.
- Primary process tag: `process-produto-low-ticket`.
- Imported transversal module tags: `process-mecanismo-big-idea` and
  `process-prova-depoimentos`.
- S07 remains blocked until S06 passes its own S09.

Implementation:

- Created `skills/msf-process-produto-low-ticket/` with
  `scripts/create_process_skill.py`.
- Filled the 8 process-skill files: `SKILL.md`, `skill.contract.json`,
  `retrieval.md`, `rubric.md`, `templates/output-template.md`,
  `examples/briefing.md`, `examples/output-approved.md`, and
  `agents/openai.yaml`.
- Kept internal playbook/retrieval/rubric/contract text ASCII; final template
  and examples use full pt-BR accents.
- Imported transversal modules by reference and preserved the inherited
  `module_inheritance_policy`: dedupe evidence by `insight_id`, count
  `zoChfFHnlOQ-v2-0008` and `mCaFyZpXJdE-v2-0011` once, and keep
  low-ticket-specific transformation, scope, format, price-value logic,
  consumability, backend bridge, and validation plan inside the skill.
- Defined the low-ticket rubric criteria:
  `entry_transformation_clarity_score`, `avatar_promise_fit_score`,
  `scope_consumability_score`, `price_value_coherence_score`,
  `mechanism_belief_score`, `proof_claim_control_score`,
  `backend_ascension_bridge_score`, and `base_usage_score`.
- Commercial combined criterion for low ticket:
  `entry_transformation_clarity_score`, `price_value_coherence_score`, and
  `backend_ascension_bridge_score`.

S09 blind sample:

- Prepared 4 varied low-ticket briefings:
  - `S09-LOWTICKET-001` paid 7-day nutrition-planning challenge.
  - `S09-LOWTICKET-002` ebook + mini-course for MEI cash separation.
  - `S09-LOWTICKET-003` template kit for agency onboarding.
  - `S09-LOWTICKET-004` recorded guitar workshop for adult beginners.
- Wrote blind CSV:
  `data/exports/output_s09_lowticket_blind_sample_2026-07-08.csv`.
- Wrote hidden key:
  `data/exports/output_s09_lowticket_blind_key_2026-07-08.json`.
- Wrote strategy packs:
  - `data/exports/strategy_pack_s09_lowticket_001_2026-07-08.*`
  - `data/exports/strategy_pack_s09_lowticket_002_2026-07-08.*`
  - `data/exports/strategy_pack_s09_lowticket_003_2026-07-08.*`
  - `data/exports/strategy_pack_s09_lowticket_004_2026-07-08.*`
- Baselines were written as honest product strategy attempts, not deliberately
  generic.
- CSV has blank low-ticket rubric fields and no source-label leakage
  (`with_s06`, `no_skill`, `baseline`, `com skill`, `sem skill`, `curated`,
  `Marketing Swipe`, or `insight:`).
- No S09 verdict was generated. Judgment remains external.

Decision state:

- MSF-S06 moved to owner judgment with status `ready_for_owner_audit`.
- MSF-S09 is `in_progress` for S06 low ticket.
- MSF-S07 remains blocked until S06 validates its own skill -> retrieval ->
  rubric -> blind-test pipeline.
- No commit was created, per owner instruction.

Validation:

- `.\.venv\Scripts\python.exe -B scripts\validate_process_skill.py skills\msf-process-produto-low-ticket` -> `VALID process_skill`.
- S06 playbook No Invention check passed: 18 real playbook citations resolve
  to `curated_insights` and all carry `process-produto-low-ticket`.
- S09 low-ticket key citation check passed: 13 unique with-skill citations
  resolve to `curated_insights` and all carry `process-produto-low-ticket`.
- S09 low-ticket blind CSV structural check passed: 4 pairs and 40 blank
  judging fields.
- Source-leak scan on the blind CSV passed.
- With-skill output encoding guard passed: 0 orphan question marks and all 4
  with-skill outputs preserve pt-BR accents.
- Closure checks passed after documentation updates:
  `validate_process_skill.py`, `validate_transversal_modules.py`, direct
  regression test execution, S09 low-ticket CSV/key checks, S06 No Invention
  checks, internal non-ASCII scan, and `git diff --check`.

## 2026-07-08 - MSF-S09 low-ticket apuration and S06 approval

Inputs:

- Owner-provided blind judgment:
  `data/exports/output_s09_lowticket_blind_sample_2026-07-08_judged.csv`.
- Hidden key opened only after judging:
  `data/exports/output_s09_lowticket_blind_key_2026-07-08.json`.
- Skill under test: `skills/msf-process-produto-low-ticket/`.
- PASS rule: with-skill must win or tie the commercial core in every pair,
  lose no pair overall, and have no pending encoding defect in with-skill
  outputs.

Apuration:

- A/B mapping by key:
  - `S09-LOWTICKET-001`: A = no skill, B = with skill; blind winner B.
  - `S09-LOWTICKET-002`: A = with skill, B = no skill; blind winner A.
  - `S09-LOWTICKET-003`: A = no skill, B = with skill; blind winner B.
  - `S09-LOWTICKET-004`: A = with skill, B = no skill; blind winner A.
- Pair result: with skill 4, no skill 0, ties 0.
- Criterion result: with skill 31, no skill 0, ties 1.
- The 1 tie was `proof_claim_control_score` in pair 003.
- Commercial core (`entry_transformation_clarity_score`,
  `price_value_coherence_score`, `backend_ascension_bridge_score`): with skill
  12, no skill 0, ties 0.
- Gate report written to
  `docs/msf-s09-lowticket-gate-result-2026-07-08.md`.

Encoding and No Invention:

- `orphan_question_mark_contexts` found 0 orphan question marks in the 4
  with-skill outputs selected through the hidden key.
- Raw non-ASCII scan of with-skill final outputs found only normal Latin accent
  codepoints. These are valid final-output accents under the layered writing
  policy, not encoding defects.
- S09 Low Ticket key No Invention check passed: 20 citation uses, 13 unique
  citations, 0 missing, and 0 without `process-produto-low-ticket`.

Decision state:

- Verdict: `PASS`.
- MSF-S06 marked `done` in the skills backlog.
- `msf-process-produto-low-ticket` marked approved in `SKILL.md`.
- `blind_baseline_test` marked `pass` in
  `skills/msf-process-produto-low-ticket/skill.contract.json`.
- MSF-S07 (`msf-process-quiz`) released as the last real skill in the first
  wave.
- No commit was created, per owner instruction.

Validation:

- `.\.venv\Scripts\python.exe -B scripts\validate_process_skill.py skills\msf-process-produto-low-ticket --require-done` -> `VALID process_skill`.
- Reproducible S09 low-ticket apuration check passed:
  pair `4-0-0`, criteria `31-0-1`, commercial core `12-0-0`.

## 2026-07-08 - MSF-S06/S09 LowTicket commit and push closure

Inputs:

- External independent audit approved MSF-S06/S09 LowTicket as `PASS`.
- Owner requested commit + push of the S06 skill, S09 gate report, backlog, and
  execution log.
- `data/exports` remains gitignored/local-only for LowTicket CSV/JSON strategy
  artifacts.

Closure validation:

- `.\.venv\Scripts\python.exe -B scripts\validate_process_skill.py skills\msf-process-produto-low-ticket --require-done` -> `VALID process_skill`.
- Internal non-ASCII scan passed for the S06 gate docs and internal skill
  files.
- `git diff --check` passed with line-ending warnings only for modified docs.
- Ignored LowTicket exports remain present on disk and outside the staged Git
  set.

Decision state:

- MSF-S06 is `done`; `msf-process-produto-low-ticket` is approved.
- MSF-S07 (`msf-process-quiz`) is released as the last real skill in the first
  wave, but not started in this closure.

## 2026-07-08 - MSF-S07 quiz funnel skill and S09 blind prepare

Inputs:

- Owner requested MSF-S07 as the last real process skill in the first wave
  after S06/S09 LowTicket PASS.
- Skill under test: `skills/msf-process-quiz/`.
- Primary process tag: `process-quiz`.
- Imported transversal module tags: `process-mecanismo-big-idea` and
  `process-prova-depoimentos`.
- S07 must pass its own S09 before the first skill wave is closed.

Implementation:

- Created `skills/msf-process-quiz/` with `scripts/create_process_skill.py`.
- Filled the 8 process-skill files: `SKILL.md`, `skill.contract.json`,
  `retrieval.md`, `rubric.md`, `templates/output-template.md`,
  `examples/briefing.md`, `examples/output-approved.md`, and
  `agents/openai.yaml`.
- Kept internal playbook/retrieval/rubric/contract text ASCII; final template
  and examples use full pt-BR accents.
- Imported transversal modules by reference and preserved the inherited
  `module_inheritance_policy`: dedupe evidence by `insight_id`, count
  `zoChfFHnlOQ-v2-0008` and `mCaFyZpXJdE-v2-0011` once, and keep quiz-specific
  questions, segmentation, result personalization, offer bridge, completion
  design, mini VSL placement, and page-level metrics inside the skill.
- Defined the quiz rubric criteria:
  `question_diagnostic_coherence_score`, `avatar_recognition_score`,
  `result_personalization_score`, `mechanism_belief_score`,
  `proof_claim_control_score`, `offer_bridge_coherence_score`,
  `completion_design_score`, and `base_usage_score`.
- Commercial combined criterion for quiz:
  `question_diagnostic_coherence_score`, `result_personalization_score`, and
  `offer_bridge_coherence_score`.

S09 blind sample:

- Prepared 4 varied quiz briefings:
  - `S09-QUIZ-001` problem-diagnostic quiz for autonomous professionals.
  - `S09-QUIZ-002` avatar-segmentation quiz for dental clinic marketing.
  - `S09-QUIZ-003` readiness quiz for low-ticket product creators.
  - `S09-QUIZ-004` product-match quiz for a minimalist skincare kit.
- Wrote blind CSV:
  `data/exports/output_s09_quiz_blind_sample_2026-07-08.csv`.
- Wrote hidden key:
  `data/exports/output_s09_quiz_blind_key_2026-07-08.json`.
- Wrote strategy packs:
  - `data/exports/strategy_pack_s09_quiz_001_2026-07-08.*`
  - `data/exports/strategy_pack_s09_quiz_002_2026-07-08.*`
  - `data/exports/strategy_pack_s09_quiz_003_2026-07-08.*`
  - `data/exports/strategy_pack_s09_quiz_004_2026-07-08.*`
- Baselines were written as honest quiz-funnel attempts, not deliberately
  generic.
- CSV has blank quiz rubric fields and no source-label leakage
  (`with_skill`, `no_skill`, `baseline`, `com skill`, `sem skill`, `curated`,
  `Marketing Swipe`, `insight:`, or `msf-process`).
- No S09 verdict was generated. Judgment remains external.

Encoding and No Invention:

- Initial CSV guard caught 2 orphan question marks in with-skill outputs
  (`cren?a` and `vi?o`), caused by the write path. The CSV was corrected at the
  encoding layer without changing quiz logic.
- Final `orphan_question_mark_contexts` check found 0 orphan question marks in
  the 4 with-skill outputs selected through the hidden key.
- Raw non-ASCII scan of with-skill final outputs found normal Latin accent
  codepoints. These are valid final-output accents under the layered writing
  policy, not encoding defects.
- S07 playbook No Invention check passed: 18 citation uses, 17 unique playbook
  citations, 0 missing, and 0 without `process-quiz`.
- S09 Quiz key No Invention check passed: 30 citation uses, 18 unique with-skill
  citations, 0 missing, and 0 without `process-quiz`.

Decision state:

- MSF-S07 moved to owner judgment with status `ready_for_owner_audit`.
- MSF-S09 is `in_progress` for S07 quiz.
- `blind_baseline_test` remains `pending` in
  `skills/msf-process-quiz/skill.contract.json` until external blind judgment.
- The first skill wave is not closed yet.
- No commit was created, per owner instruction.

Validation:

- `.\.venv\Scripts\python.exe -B scripts\validate_process_skill.py skills\msf-process-quiz` -> `VALID process_skill`.
- `.\.venv\Scripts\python.exe -B scripts\validate_transversal_modules.py skills\_modules\msf-transversal-copy` -> `VALID transversal_modules`.
- Direct regression tests passed:
  `tests/test_process_skill_contract.py`, `tests/test_process_tag_retrieval.py`,
  `tests/test_transversal_modules_contract.py`, and
  `tests/test_strategy_pack_diversity.py`.
- S09 Quiz blind CSV structural check passed: 4 pairs and 40 blank judging
  fields.
- Source-leak scan on the blind CSV passed.
- Closure checks passed after documentation updates: process-skill validation,
  transversal-module validation, direct regression test execution, S07 No
  Invention checks, S09 Quiz CSV/key checks, internal non-ASCII scan, and
  `git diff --check`.

## 2026-07-08 - MSF-S09 Quiz apuration and encoding concerns

Inputs:

- Owner supplied the judged blind CSV:
  `data/exports/output_s09_quiz_blind_sample_2026-07-08_judged.csv`.
- Hidden key opened after judging:
  `data/exports/output_s09_quiz_blind_key_2026-07-08.json`.
- Owner-reported blind winners: 001=A, 002=B, 003=A, 004=B; criteria 32-0-0;
  commercial core 12-0-0.

Apuration:

- Key mapping: 001 A=com skill, 002 B=com skill, 003 A=com skill, 004 B=com
  skill.
- Pair result: com skill 4, sem skill 0, empates 0.
- Criterion result: com skill 32, sem skill 0, empates 0.
- Commercial core
  (`question_diagnostic_coherence_score`, `result_personalization_score`,
  `offer_bridge_coherence_score`): com skill 12, sem skill 0, empates 0.
- No Invention passed for the S09 key: 30 citation uses, 18 unique
  `insight_id` values, 0 missing from `curated_insights`, and 0 without
  `process-quiz`.

Encoding handling:

- Hardened `orphan_question_mark_contexts` in `scripts/msf_common.py` to catch
  repeated mid-word `?` mojibake (`obje??o`) and single mid-word `?`
  (`Prot?tipo`) while allowing legitimate final question marks.
- Added regression coverage in `tests/test_msf_common_encoding.py`, including
  direct helper checks and `audit_generated_text` checks.
- Hardened guard scan of the original blind sample found:
  - `S09-QUIZ-002`, output B/com skill: `obje??o`.
  - `S09-QUIZ-003`, output B/sem skill: `Prot?tipo`.
- Root trace: `obje??o` already exists in ignored upstream local data,
  including `data/exports/curated_insights.json` and
  `data/processed/mCaFyZpXJdE/insights_v2.json`; the strategy pack path renders
  selected insight fields directly, so the skill inherited corrupted source
  text that the previous guard missed.
- Wrote encoding-fixed blind sample:
  `data/exports/output_s09_quiz_blind_sample_2026-07-08_encoding_fixed.csv`.
- Diff is localized to mojibake characters only:
  - `S09-QUIZ-002`, output B/com skill: `obje??o` -> `objecao`
    (2 character substitutions in one token).
  - `S09-QUIZ-003`, output B/sem skill: `Prot?tipo` -> `Prototipo`
    (1 character substitution in one token).
- Final guard scan of the encoding-fixed sample found 0 mojibake hits in all
  outputs, including 0 in the 4 with-skill outputs.

Docs and decision state:

- Added `docs/msf-s09-quiz-gate-result-2026-07-08.md`.
- Updated `docs/marketing-swipe-file-skills-backlog.md`.
- Commercial verdict is `PASS`; gate status remains `CONCERNS`.
- MSF-S07 remains `ready_for_owner_audit`; `msf-process-quiz` is not approved;
  `blind_baseline_test` remains pending; the first skill wave remains open until
  external reconfirmation clears the encoding concern.
- No commit was created, per owner instruction.

## 2026-07-08 - MSF-S07/S09 Quiz approval and first-wave closure

Inputs:

- External independent audit reconfirmed MSF-S07 after reviewing the
  encoding-fixed sample.
- Owner confirmed the key mapping and commercial PASS: com skill won 4/4 pairs,
  32/32 criteria, and 12/12 commercial-core cells.
- Owner confirmed the encoding-fixed sample changed only two mojibake tokens:
  `obje??o` -> `objecao` and `Prot?tipo` -> `Prototipo`, with no copy rewrite.
- Owner confirmed the hardened guard catches both artifacts, ignores legitimate
  final question marks, and finds 0 mojibake in the corrected sample.
- Owner confirmed No Invention: 18/18 unique citations carry `process-quiz`.

Implementation:

- Updated `docs/msf-s09-quiz-gate-result-2026-07-08.md` from `CONCERNS` to
  `PASS`, preserving the initial concern and recording its resolution.
- Updated `skills/msf-process-quiz/SKILL.md` to `approved`.
- Updated `skills/msf-process-quiz/skill.contract.json` so
  `blind_baseline_test` is `pass`.
- Updated `docs/marketing-swipe-file-skills-backlog.md`: MSF-S07 is `done`,
  MSF-S09 is `done`, the first wave is closed, and MSF-S10 is
  `ready_for_planning`.

Decision state:

- First wave closed: S04 offer, S03 VSL, S05 ads, S06 low-ticket, and S07 quiz
  are all done/approved.
- Next planning milestones are registered but not started:
  - Reopen MSF-R03 for data outside OneDrive before MSF-R14/backfill.
  - Plan the agent layer that consumes the 5 validated skills.
- No backfill or agent work was started in this closure.

Validation:

- `.\.venv\Scripts\python.exe -B scripts\validate_process_skill.py skills\msf-process-quiz --require-done` -> `VALID process_skill`.
- `.\.venv\Scripts\python.exe -B tests\test_msf_common_encoding.py` -> `VALID msf_common_encoding`.
- Direct regression tests passed:
  `tests/test_process_skill_contract.py`, `tests/test_process_tag_retrieval.py`,
  and `tests/test_transversal_modules_contract.py`.
- `.\.venv\Scripts\python.exe -B scripts\validate_transversal_modules.py skills\_modules\msf-transversal-copy` -> `VALID transversal_modules`.
- S09 Quiz No Invention check passed: 30 citation uses, 18 unique citations, 0
  missing, and 0 without `process-quiz`.
- Hardened guard check on the encoding-fixed sample passed:
  with-skill mojibake hits 0, all-output mojibake hits 0.
- Internal non-ASCII scan passed on repo internal docs/scripts/skill files
  touched in this closure.
- `git diff --check` passed with LF/CRLF warnings only.

## 2026-07-08 - MSF-R03 data migration out of OneDrive

Scope:

- Executed MSF-R03 phases 1-4 to move ignored/local-only runtime data out of
  the OneDrive-backed repo tree.
- Approved external root: `C:\MSF-data\Marketing_Swipe_File`.
- No junction was created.
- `data/processed/taxonomy_seed.json` remains the canonical repo-tracked
  taxonomy seed.

Implementation:

- Added data-root helpers in `scripts/msf_common.py`: `repo_root`,
  `repo_data_root`, `data_root`, `data_path`, and `repo_data_path`.
- Migrated runtime defaults from hardcoded `data/...` paths to `data_path(...)`.
- Kept taxonomy defaults on `repo_data_path("processed", "taxonomy_seed.json")`.
- Updated current operational docs, loops, retrieval recipes, and legacy local
  skills to mention `MSF_DATA_DIR`.
- Added `MSF_DATA_DIR=C:\MSF-data\Marketing_Swipe_File` to `.env.example`.
- Persisted the user environment variable with
  `setx MSF_DATA_DIR "C:\MSF-data\Marketing_Swipe_File"`.

Copy and cleanup:

- Pre-delete coverage check rebuilt
  `git ls-files --others --ignored --exclude-standard data`.
- Manifest coverage passed: 9,713 files covered in external root, 9,709 regular
  files matched by byte-size, and 4 cache symlinks matched by resolved
  payload/hash.
- Deleted exactly the 9,713 ignored/local-only manifest files from repo `data/`.
- Preserved all tracked data files: `.gitkeep` files, lightweight tracked queues,
  `taxonomy_seed.json`, and previously tracked S09 audit artifacts.
- Post-delete repo data check: 31 actual `data/` files, 31 tracked `data/`
  files, 0 extra ignored/local-only payload files, 0 missing tracked files.

Validation:

- New process using the persistent user environment resolved
  `data_root=C:\MSF-data\Marketing_Swipe_File`.
- 5 process-skill validators with `--require-done` passed.
- `scripts/validate_transversal_modules.py skills\_modules\msf-transversal-copy`
  passed.
- Generated 1 real strategy pack per approved first-wave skill; all read
  `C:\MSF-data\Marketing_Swipe_File\exports\curated_insights.json`.
- No Invention passed for the 5 skills against external curated.
- Hardened mojibake guard passed on the post-delete generated packs: 0 findings.
- `git ls-files --deleted` returned 0.
- `git diff --check` passed with LF/CRLF warnings only.

Decision state:

- MSF-R03 is `done`.
- MSF-R14 backfill is the next milestone, but was not started; it remains
  waiting for an explicit owner prompt.

## 2026-07-08 - MSF-R15 grounding hardening A+B

Scope:

- Executed the approved low-risk portions of MSF-R15 before the additive output
  contract rollout.
- Front A hardened retrieval and encoding guards.
- Front B cleaned mojibake tokens in the live external base.
- Front C was documented as a proposal only in
  `docs/msf-r15-output-contract-plan.md`; skill files were not changed in this
  commit.

Implementation:

- Added explicit curated retrieval states in `scripts/msf_common.py`.
- `scripts/search_insights.py` and `scripts/generate_strategy_pack.py` now
  return `curated_unavailable` when `--source curated` cannot resolve
  `exports/curated_insights.json`, and markdown output opens with
  `SEM BASE - resposta nao fundamentada`.
- Centralized the mojibake guard to detect mid-word `?` runs and U+FFFD while
  preserving legitimate question marks.
- Added reusable evidence traceability checking: every
  `evidence.quote_original` must match the referenced segment's
  `text_original` span.
- Extended tests for missing curated state, mojibake detection, legitimate
  questions, U+FFFD, and evidence traceability.

External data cleanup:

- Cleaned internal editorial fields in
  `C:\MSF-data\Marketing_Swipe_File\exports\curated_insights.json`.
- Cleaned internal editorial fields in
  `C:\MSF-data\Marketing_Swipe_File\exports\insights_v2_master.json`.
- Evidence quotes remained verbatim UTF-8; `evidence.quote_original` was not
  normalized or rewritten.
- Post-cleanup counts remained unchanged: 125 curated insights and 207 v2 master
  insights.
- Post-cleanup mojibake guard result: 0 `?` artifacts and 0 U+FFFD in the
  targeted internal fields of both external files.

Validation:

- `tests/test_msf_common_encoding.py` passed.
- `tests/test_process_tag_retrieval.py` passed.
- `tests/test_strategy_pack_diversity.py` passed.
- Missing-curated smoke test passed: outputs open with
  `SEM BASE - resposta nao fundamentada`.
- Curated real smoke test passed with `retrieval_state=available`, reading from
  `C:\MSF-data\Marketing_Swipe_File\exports\curated_insights.json`.
- `scripts/audit_insights_v2_text.py` passed separately on external curated and
  external v2 master.
- Internal non-ASCII scan passed on touched repo files.
- `git diff --check` passed with LF/CRLF warnings only.

Decision state:

- Fronts A+B are approved and ready to commit.
- Front C remains proposal-first until implemented and returned for owner audit.

## 2026-07-08 - MSF-R15 output contract Front C

Scope:

- Implemented the approved additive output contract from
  `docs/msf-r15-output-contract-plan.md`.
- No retrieval files, examples, or `SKILL.md` files were changed.
- Blind gate status was preserved: every approved skill kept
  `blind_baseline_test=pass`.

Implementation:

- Added `output_contract` to
  `schemas/msf_process_skill_contract.schema.json`.
- Added the five required sections to the process-skill template and the five
  approved process skills:
  - evidence binding
  - claim fence
  - proof fit
  - testable bet
  - coherence check
- Added output-contract checks to the template rubric and the five approved
  skill rubrics.
- Added the six-question consumer checklist to
  `skills/_modules/msf-transversal-copy/modules/mecanismo-big-idea.md`.

Validation:

- `scripts/validate_process_skill.py --require-done` passed for:
  - `skills\msf-process-construcao-oferta`
  - `skills\msf-process-copy-vsl`
  - `skills\msf-process-copy-anuncios`
  - `skills\msf-process-produto-low-ticket`
  - `skills\msf-process-quiz`
- `scripts/validate_transversal_modules.py skills\_modules\msf-transversal-copy`
  passed.
- Output-contract smoke confirmed all five sections render for each approved
  skill.
- Missing-curated smoke passed: generated output opens with
  `SEM BASE - resposta nao fundamentada` and reports
  `retrieval_state=curated_unavailable`.
- Encoding guard on smoke outputs passed with 0 mojibake findings.
- `git diff --check` passed.

Decision state:

- MSF-R15 is `done`.
- This was an additive contract hardening; no blind S09 gate was reopened.

## 2026-07-09 - MSF-R16 retrieval pool consolidation

Scope:

- Executed the owner-approved option 2: keep the curated-125 gate snapshot as
  audit reference and use the cleaned, re-scored v2 master as the broad
  retrieval pool.
- External data root was `C:\MSF-data\Marketing_Swipe_File`.
- No curated rewrite was committed to git; external data remains local-only.

External data state:

- Backed up live external files before rewrite at
  `C:\MSF-data\Marketing_Swipe_File\exports\_snapshots\msf-r16-option2-2026-07-09_113257`.
- `insights_v2_master.json`: 207 + 436 R14 insights = 643 total, 0
  `insight_id` collisions.
- R14 manual scores were discarded; all 643 insights were re-scored through the
  validated curated scorer on one scale.
- Recomputed score distribution: min 88, median 96, max 100; 641/643 items are
  at `editorial_score >= 90`.
- `curated_insights_gate_snapshot_2026-07-08.json` was created as the
  reference set that passed the blind gates.
- SHA256 hashes:
  - pre-R16 `insights_v2_master.json`:
    `3f7167822feb4560b896ce3b9b364e1f8d27ac9071ca55a4bbcaeb4181084114`
  - post-R16 `insights_v2_master.json`:
    `89dfee939495417367a07b6d27307e3a68d9d6b8e3a7f8c6f81f781b2e6d5b50`
  - `curated_insights.json` before/after and gate snapshot:
    `1d9a7eaf291b1febb8db140d38fc1235807f37ba7c16df6248aa8787329d18e4`

Implementation:

- Added `pool` retrieval source for
  `C:\MSF-data\Marketing_Swipe_File\exports\insights_v2_master.json`.
- Added explicit `pool_unavailable` retrieval state.
- Added `--min-editorial-score` to `search_insights.py` and
  `generate_strategy_pack.py`.
- The approved first-wave skills and template now use `--source pool
  --min-editorial-score 90` in retrieval commands.
- Skill contracts now allow `source_layer=v2_master_pool`.
- Blind gate status was preserved: all five approved skills keep
  `blind_baseline_test=pass`.

Validation:

- Final live master guards: internal non-ASCII 0, mojibake 0, missing
  `process_tags` 0, missing `claim_risk` 0, missing evidence 0.
- Evidence traceability passed: 1117/1117 quotes matched their referenced
  transcript spans.
- Coverage vs curated-125:
  - `process-construcao-oferta`: 68 -> 207
  - `process-copy-vsl`: 51 -> 253
  - `process-copy-anuncios`: 18 -> 126
  - `process-produto-low-ticket`: 29 -> 78
  - `process-quiz`: 20 -> 36
- Smoke strategy packs for all five skills passed with `--source pool
  --min-editorial-score 90`, No Invention 0 missing / 0 wrong tag, encoding 0,
  traceability 0 findings.
- `tests/test_msf_common_encoding.py`, `tests/test_process_tag_retrieval.py`,
  `tests/test_process_skill_contract.py`, five
  `validate_process_skill.py --require-done` runs, and
  `validate_transversal_modules.py` passed.
- `git diff --check` passed with Windows LF/CRLF warnings only.

Decision state:

- MSF-R16 is `done`.
- Retrieval migrated from the curated-only layer to the 643-item v2 master pool
  with approved floor `--min-editorial-score 90`.
- Supabase, pgvector, MCP, and agent-layer work were not started.

## 2026-07-10 - L7 gold-standard isolated transcript reprocessing

Scope:

- Reprocessed only `L7u7r6rOl68` into the separate external-data directory
  `processed/L7u7r6rOl68/gold_extraction`.
- Preserved `insights_v2.json`, curated exports, and master exports unchanged.
- Did not use Supabase or make any remote change.

Implementation:

- Added `scripts/reprocess_gold_episode.py` for deterministic transcript cleanup,
  chronological chunks, and a recall-oriented lexical signal inventory. The
  1,504 lexical signals are explicitly not an insight layer.
- Added `scripts/build_gold_semantic_extraction.py` for reviewed semantic specs,
  multisegment evidence, structured numbers, parent/child relations, semantic
  calibration, editorial-audit enforcement, and final artifact generation.
- Added focused tests in `tests/test_reprocess_gold_episode.py` and
  `tests/test_build_gold_semantic_extraction.py`.

Validation:

- The two focused test files passed: 6 tests.
- The episode run retained 1,941 segments, removed 39 recommendation segments,
  and created 35 chronological chunks.
- Full-chunk semantic review produced 139 insights: 139 unique titles, 139
  unique takeaways, 247 structured quantitative claims, 104 parent relations,
  and 15 records with explicit child relations.
- The lexical coverage ledger has 1,230 captured, 5 merged, and 269 excluded
  entries; all 1,504 lexical signals have a disposition.
- Independent editorial audit closed four recovered omissions and finished with
  zero open findings. Semantic calibration passed 12/12.
- Protected transcript, v2, curated, and master fingerprints match the
  preprocessing snapshot; no remote system or master export was changed.

## 2026-07-10 - MSF-R20 pilot gold tooling and external-audit preparation

Scope:

- Added generic, local-only gold extraction tooling for the Route B workflow.
- Kept the frozen v2, curated, and master layers unchanged. No API, Supabase,
  commit, push, or remote operation was used.

Implementation:

- Added schema validation, canonical themes, structured numbers, relation
  symmetry and cycle checks, calibration deduplication, categorized ledger
  exclusions, idempotent checkpoint state, and blind audit-packet export.
- Added an idempotency guard that reuses a compatible reviewed signal inventory
  when transcript input is unchanged, preventing a rerun from narrowing ledger
  coverage.
- Recorded the external blind approval of `awbrqeqq-io` and exported its packet
  retroactively. Every pilot episode that is awaiting audit now has an isolated
  packet under `C:\MSF-data\Marketing_Swipe_File\exports`.

Validation:

- Direct gold-tooling tests passed: 16. Python compilation passed.
- L7 and awbr rerun proof: candidate IDs, layered evidence, and protected v2,
  curated, and master fingerprints remained unchanged.
- L7 and awbr are complete after their passed external audits. The four new
  pilot episodes are deterministic-pass and awaiting blind external audit.
- Historical note: the approved pre-R20 L7 ledger reported 1,504 entries. Its
  local pre-rerun inventory was replaced before the preservation guard existed;
  the reconstructed report has 1,410 entries. Insight IDs and evidence are
  unchanged, but this count discrepancy remains explicitly recorded rather
  than treated as an equivalent coverage rerun.

## 2026-07-11 - MSF-R20 Codex coordinator quality gate

Scope and independence:

- The Codex coordinator audited the four pending pilot packets in order:
  `35uL_nCmZ0k`, `_hXmiIEac6w`, `aSFAve1klsc`, and `cL3FuW8bAMA`.
- Initial judgments were sealed before reading worker history, manual reviews,
  editorial reports, validation reports, or dedupe queues. The review was blind
  to generation history and internal decisions, but not blind to episode or
  style.
- Initial verdicts were `changes_requested`: six, two, four, and four findings,
  respectively. Findings covered ledger orphans, calibration duplication,
  omitted quantitative context, number normalization, editorial corruption,
  missing caveats, duplicated editorial claims, and one promotional item.
- Sealed audits and reaudits are local under
  `.codex-work/msf-r20-coordinator-audits`; they are intentionally excluded from
  Git together with the operational queue.

Implementation and migration:

- Worker `019f4c90-b9dc-7e32-8ff1-57f8896386d3` (`gpt-5.6-terra/high`)
  hardened audit provenance and the complete gate, corrected the four episodes,
  regenerated isolated packets, and did not self-approve or write the sealed
  coordinator audits.
- `status=passed` now rejects open or malformed findings. Completion derives
  from a valid `editorial_audit_report.json`, requires a reviewer task separate
  from the executor, zero open findings, deterministic validation, and preserved
  fingerprints.
- Future review is provider-neutral and uses a separate Codex coordinator.
  Historical Claude references remain truthful records. The compatibility name
  `awaiting_external_audit` remains, with external meaning external to the
  executor task.
- Added the durable coordination contract, queue, worker event template, owner
  decision gate, and separate pre-production commit/push/deploy gates.

Reaudit result:

- All 16 initial findings were verified resolved. The four coordinator reaudits
  passed with zero open findings and were registered through the hardened audit
  script.
- All four episodes now report `status=complete`, `audit_status=passed`, a
  separate coordinator reviewer, and `open_findings=0`.
- No gold was consolidated into v2, curated, pool, or master, and Supabase was
  not started.

Coordinator validation:

- Real-data deterministic validation passed for all four episode directories
  before audit registration and again with `--require-external-audit` after
  registration/build.
- Packet inspection confirmed JSON integrity, candidate-to-ledger coverage,
  evidence and context ranges, relation symmetry/no cycles, calibration target
  separation, corrected numeric ranges, removal of the promotional `cL3` item,
  and no remaining corrupted editorial question marks.
- Direct pure-function tests passed 18. Five filesystem-isolation cases could
  not create temporary directories under OneDrive or the alternate local
  visualization root due `PermissionError`; no lock was forced or cleaned. The
  worker's same suite passed all 23 before delivery.
- Python source compilation and `git diff --check` passed.

Protected fingerprint proof:

- `35uL_nCmZ0k/insights_v2.json`:
  `500a7c243975b98604b19a5faa49269187fa4cedf63a7c0c58265095e8300a0d`
- `_hXmiIEac6w/insights_v2.json`:
  `9e349b7e87bab72ec711bf700a09def4e83b8df6e3abc9e5e906b7cc5228d8f4`
- `aSFAve1klsc/insights_v2.json`:
  `68222ab8072c75958d5490e2409ac92dd75ec32a847f4b73084b28f00ffb866c`
- `cL3FuW8bAMA/insights_v2.json`:
  `129e799f5a6929fc3ab7a6818a24b923e7f33acbbd98f5b5bf77311a4672e582`
- `curated_insights.json`:
  `1d9a7eaf291b1febb8db140d38fc1235807f37ba7c16df6248aa8787329d18e4`
- `insights_v2_master.json`:
  `67eb13df5b26bf7bde95711a8c1bd108ffeaed897b181378b70fb7ade536e53e`
- `insights_master.json`:
  `2b0639f7b957d3b63c977abbda2e86ba392964281e6c6b26dce5782a20c7710e`
- All values matched the pre-worker snapshot after final builds.

Owner policies recorded:

- `production_status=pre_production`; only the owner can declare production.
  Commit, push, and deploy are independent gates and may be executed
  autonomously only after their own criteria pass.
- Context does not create a preventive gate. The same coordinator and designated
  worker are retained. No App Server, CLI, helper, hook, automation, slash
  message, or worker rotation is used to compact preventively, and new work is
  not blocked by context percentage.

Release gates:

- `APROVADO PARA COMMIT`: executed locally as `3d224f7` (`feat: harden
  MSF-R20 Codex quality gate`). The staged set contained 30 reviewed project
  files and excluded `.codex-work`, `C:\MSF-data`, generated exports, secrets,
  and bytecode.
- Post-commit validation: all four real-data validators passed again with
  `--require-external-audit`. The pre-existing local R18 commit `db42b0c` was
  inspected and its three direct citation-audit tests passed.
- `APROVADO PARA PUSH`: approved for the current `main` range to
  `origin/main`, including the already-local R18 commit, the R20 implementation,
  and this release record. Required post-action validation is remote/local ref
  equality and a clean tracked worktree.
- Rollback strategy: use additive `git revert` for the published commit(s); no
  force push, destructive reset, rebase, or history rewrite.
- `APROVADO PARA DEPLOY`: not granted. No preview/staging/pre-production deploy
  destination was identified, and no deploy was invented.

### 2026-07-11 - Preventive context compaction revoked

- The owner tested the App Server experiment on worker
  `019f4c90-b9dc-7e32-8ff1-57f8896386d3`. Although an internal completion item
  was reported, the Codex app continued to display 68 percent context usage.
- The experiment is not accepted as evidence of actual app-context compaction.
  Do not call `thread/compact/start` or use CLI helpers, scripts, hooks,
  automations, slash messages, or worker rotation for preventive compaction.
- Keep the same coordinator and the same `Extração Padrão-Ouro` worker. Context
  percentage does not block a new job, and checkpoints remain recommended but
  are not a precondition.
- Codex may compact automatically when it reaches its own native limit. Do not
  claim manual, preventive, or automatic compaction without confirmation from
  the real Codex interface or event.

## 2026-07-11 - R20 external-audit follow-up paused on filesystem lock

- An independently supplied external audit handoff identified a recall and
  ledger gap in `_hXmiIEac6w`, clean indices 740--745: the guest says story
  connects the lead to the offer/pitch and is the main driver of pitch
  retention. The coordinator independently read those transcript segments and
  confirmed neither a candidate nor a specific ledger disposition covered the
  claim.
- The coordinator sealed `MSF-R20-HX-003` as a minor, open,
  `changes_requested` finding in local coordinator provenance. The proposed
  execution job is `MSF-R20-EXTERNAL-FINDING-001` and is limited to that
  episode's gold-extraction directory and isolated audit packet.
- Registering the sealed finding through
  `record_gold_external_audit.py` stopped at a `GoldPauseError` caused by a
  filesystem `PermissionError` replacing
  `C:\MSF-data\Marketing_Swipe_File\processed\_hXmiIEac6w\gold_extraction\editorial_audit_report.json`.
  No retry, forced write, worker delegation, consolidation, push, or deploy
  occurred. The existing package validator still passes, but its passed audit
  state is treated as stale until the follow-up audit can be recorded.

## 2026-07-11 - Codex-only autonomy and R20 follow-up dispatch

- Owner policy now makes future Marketing Swipe File coordination Codex-only.
  No Claude audit, permission, execution, or approval is required for future
  queue transitions or gates. Historical Claude records remain immutable
  provenance; later Claude material is optional supplementary evidence only.
- The local data-root audit record for `_hXmiIEac6w` was subsequently written
  through the hardened recorder with `status=changes_requested`, one open
  minor finding (`MSF-R20-HX-003`), and Codex coordinator provenance. The
  required-audit validator fails with `external audit has not passed`, as it
  must until the correction is independently reaudited.
- `MSF-R20-EXTERNAL-FINDING-001` was dispatched to the designated
  `gpt-5.6-terra/high` worker. Its scope is only the `_hXmiIEac6w` gold
  extraction and isolated packet; no Claude task is part of the execution or
  quality gate.

## 2026-07-11 - R20 `_hXmiIEac6w` Codex-only repair approved

- The coordinator independently confirmed the missing story-to-pitch retention
  claim at clean indices 740--744 and sealed `MSF-R20-HX-003` as an open minor
  finding. The worker added `G028` with verbatim evidence from segments 0741,
  0742, 0744, and 0745; its ledger entries are all `captured` for that
  candidate.
- The correction exposed a gate defect: non-required deterministic validation
  incorrectly failed whenever an otherwise valid audit had open findings. The
  minimal fix makes that error conditional on `require_external_audit`; the
  new focused regression covers a `changes_requested` report with an open
  finding. Eleven focused tests passed using the existing installed Python
  3.12 and an explicitly scoped local data-root basetemp; no dependency was
  installed.
- The coordinator reaudited the rebuilt blind packet independently and recorded
  `passed` with zero open findings. The worker then rebuilt from that sealed
  report without editing audit provenance. Coordinator final validation passed
  with `--require-external-audit`: `_hXmiIEac6w` is `complete`,
  `audit_status=passed`, and `open_audit_findings=0`. It has 28 distinct
  candidates, calibration `6/4 pass`, an exported packet, and equal protected
  before/after fingerprints.
- Future workflow remains Codex-only. Historical Claude provenance is retained
  but has no approval, execution, or gate role. No commit, push, deploy,
  consolidation, or Supabase action occurred in this repair.

## 2026-07-11 - Worker stall escape policy

- Owner policy: after three consecutive returns of the same job/subtask without
  material progress, the coordinator must stop repeating the same instruction,
  diagnose the common cause, record the attempts, and send a bounded alternative
  path. Material progress is a new artifact, validated outcome,
  decision-resolving evidence, or safe state transition.
- A worker stalled for more than 30 minutes on one installation, command, or
  other indivisible action must report timing and output. The coordinator then
  provides a different command/path; the 30-minute limit is per action, not the
  total job. Existing lock, permission, and damage-risk pauses remain in force.

## 2026-07-11 - MSF-R20 pilot retrospective and next-wave hardening

- Closed coordinator job `MSF-R20-PILOT-LEARNINGS-001` after measuring the five
  episodes selected by the R20 pilot plan. Together they contain 5,608 clean
  segments, 97 chunks, 195 gold candidates, and 3,769 ledger entries; all five
  are `complete/passed` with zero open findings and calibration 32/19 pass.
- Recorded the pilot evidence and decisions in
  `docs/coordination/msf-r20-pilot-retrospective.md`. `L7u7r6rOl68` remains a
  separate pre-pilot baseline and is not counted in the five-episode table.
- Classified 17 audit-cycle findings: 8 major and 9 minor; 7 editorial, 4
  calibration, 3 numeric, and 3 involving recall or ledger coverage.
- Preserved the existing architecture and added two mandatory next-wave gates:
  one technical preflight per job and an executor-side adversarial semantic
  recall pass before blind packet export. Ledger presence now explicitly does
  not count as coverage unless the destination candidate expresses the same
  useful proposition, including claims split across adjacent chunks.
- Updated the gold contract, coordination protocol, worker template, extraction
  prompt, scale-batch skill, pilot plan, AGENTS protocol, and durable queues. No
  episode artifact, audit report, protected layer, remote system, or Supabase
  state was changed.

## 2026-07-11 - Execução enxuta de épico/story na wave 001 do R20

- O owner pediu menor uso de contexto e tokens depois que o processamento
  contínuo por micro-checkpoints do primeiro episódio da wave de dois episódios
  se mostrou caro demais.
- O coordenador pausou o worker em checkpoint seguro depois do reparo de
  evidência numérica 025-036. Ele não iniciou a faixa seguinte, builder,
  validador, export, auditoria ou o segundo episódio.
- docs/coordination/msf-r20-wave-001-lean-plan.md passou a ser o plano durável:
  um épico é delegado por vez, suas stories internas documentadas são executadas
  sequencialmente pelo worker e, depois, o coordenador revisa o épico antes do
  próximo. A remediação numérica começa por diagnóstico residual determinístico
  e limita cada story de correção direcionada a doze candidatos ou oito chunks.
- As atribuições de modelo/esforço do coordenador e worker não mudaram. Não
  houve commit, push, deploy, consolidação ou ação no Supabase.
- O plano foi corrigido para um épico por vez: as stories documentadas são
  concluídas sequencialmente antes de o coordenador revisar o épico e liberar o
  próximo. Depois o owner pediu somente planejamento; o Epic E1 ficou
  explicitamente retido até nova liberação de execução.
- Uma breve delegação de E1 foi revogada antes de qualquer comando. O worker
  confirmou awaiting_owner_execution_release e permanece idle.

## 2026-07-11 - Registro simples obrigatório antes de delegar

- Owner policy: imediatamente antes de cada delegação ao worker, o coordenador
  deve publicar na conversa um registro completo em linguagem simples do que
  será executado. O registro explica objetivo, sequência de ações, arquivos
  que podem mudar, artefatos e validações esperados, exclusões, condições de
  parada e o próximo quality gate.
- O texto é um plano, nunca uma alegação de que o trabalho já foi executado.
  Sua versão concisa também fica no plano do épico e no campo
  `pre_delegation_brief` da fila durável. Mudança material de escopo exige um
  novo registro antes de uma nova delegação.

## 2026-07-11 - Liberação do Epic E1 da wave 001

- O owner liberou a execução do Epic E1 para `mCaFyZpXJdE`. O ponto de partida
  continua sendo o checkpoint seguro do reparo 025-036, confirmado pelo evento
  `MSF-R20-WAVE-001-018`; a delegação anterior foi revogada antes de qualquer
  comando.
- Antes do envio ao worker, o coordenador publicará o EXECUTION BRIEF em pt-BR
  simples, conforme o protocolo. O Epic E1 permanece restrito ao diagnóstico
  residual, correções planejadas e prontidão do packet cego; não autoriza
  auditoria, consolidação, release, Supabase nem início de `TOW0sWhPaZw`.

## 2026-07-11 - Diagnóstico do E1 e exceção única de escopo

- O primeiro build do E1 encontrou 18 erros de raw ausente na evidência mínima,
  em 13 candidatos distintos: G058, G059, G060, G061, G063, G066, G068, G069,
  G070, G071, G073, G075 e G076. Ele preservou 79 candidatos e calibração
  aprovada; nenhuma correção, segundo build, validação normal ou export foi
  iniciado.
- O limite padrão do plano é 12 candidatos por story. Como os 13 pertencem à
  mesma causa conhecida e o excedente é de um único candidato, o coordenador
  autorizou exceção única documentada dentro do mesmo Epic E1. Isso evita um
  novo diagnóstico e não amplia ownership, episódio, dados consolidados ou
  privilégio de release.

## 2026-07-11 - Auditoria do coordenador do packet E1 de mCaFyZpXJdE

- O worker entregou packet cego de cinco arquivos com 79 candidatos, 2.106
  entradas no ledger e calibração 10/7 pass. O coordenador fez a auditoria
  independente e selou
  `.codex-work/msf-r20-coordinator-audits/mCaFyZpXJdE_audit.json` como
  `changes_requested`.
- A auditoria confirmou IDs e JSONs consistentes; 0 quote, tempo ou contexto
  inválidos; ledger com 976 captured, 1.130 excluded, reasons válidos e todos
  os candidatos referenciados; 28 calibrações sem target semântico duplicado;
  relações vazias sem assimetria/ciclo; e editorial específico com risco de
  claim coerente.
- O único finding aberto é `MSF-R20-MCA-001` (major): quatro `numbers.raw`
  perderam acentos em G009, G035 e G042 e não são exatamente verbatim da
  evidência. E1-S06 está limitado a corrigir esses quatro strings e a
  reconstruir/validar/exportar o packet; E1-S07 será uma nova auditoria do
  coordenador.
- Os cinco fingerprints protegidos da wave permanecem iguais ao snapshot.
  Não houve commit, push, deploy, consolidação ou ação no Supabase.

## 2026-07-11 - Reauditoria E1 aprovada; registro determinístico pendente

- O worker aplicou exclusivamente as quatro correções verbatim de
  `MSF-R20-MCA-001`, e o novo packet manteve 79 candidatos, 2.106 entradas no
  ledger, calibração 10/7 pass e lifecycle `awaiting_external_audit`.
- O coordenador selou
  `.codex-work/msf-r20-coordinator-audits/mCaFyZpXJdE_reaudit_001.json` como
  `passed`: os quatro `numbers.raw` agora são literais, não há quote, tempo,
  contexto ou raw inválido e não há finding aberto. Os cinco fingerprints
  protegidos continuam iguais ao snapshot.
- Próximo passo estreito: E1-S08 usa o script endurecido para registrar o
  julgamento aprovado, derivar `complete/passed` e executar a validação final.
  O worker não pode alterar o julgamento; `TOW0sWhPaZw` continua bloqueado.

## 2026-07-11 - Coordenação por evento sem acompanhamento ativo

- O owner definiu que, depois de delegar um job, o coordenador deve encerrar o
  próprio turno. Enquanto o worker executa, não há polling, heartbeat, leitura
  do chat, monitoramento nem processamento paralelo pelo coordenador.
- A retomada ocorre somente por `WORKER_EVENT` final de conclusão, bloqueio ou
  decisão necessária — ou por nova instrução do owner. Checkpoints de progresso
  ficam apenas no chat do worker e não reativam o coordenador. Nesse retorno, o
  coordenador deduplica `event_id/job_id`, lê a entrega e então faz o quality
  gate sequencial.
- O contrato do worker foi ajustado para deixar explícito que o evento final é o
  canal de retomada. A falta de evento não autoriza acompanhamento ativo; o
  worker deve reenviá-lo no próximo ponto seguro.

## 2026-07-11 - E1-S08 bloqueada por envelope de auditoria e retomada segura

- A tentativa 21 de registrar a reauditoria de `mCaFyZpXJdE` parou antes de
  build ou validação. O registrador rejeitou
  `mCaFyZpXJdE_reaudit_001.json` exclusivamente porque faltavam `audit_route` e
  `open_findings`; nenhum artefato editorial, packet ou julgamento foi alterado
  pelo worker.
- O coordenador criou e selou
  `.codex-work/msf-r20-coordinator-audits/mCaFyZpXJdE_reaudit_002.json`. O novo
  envelope acrescenta `audit_route=codex_coordinator_blind_reaudit_after_worker_correction`
  e `open_findings=0`, e normaliza `segment_range` para `[322, 1724]`, como o
  contrato exige. Preserva o julgamento `passed`, o finding resolvido, reviewer,
  data de revisão, evidências e resumo de `_reaudit_001.json`.
- A tentativa 22, E1-S08-b, fica limitada a registrar esse relatório, executar
  um build e uma validação final com `--require-external-audit`. O worker não
  pode alterar o relatório selado nem dados editoriais. E2 continua bloqueado.

## 2026-07-11 - Epic E1 de mCaFyZpXJdE aprovado

- O worker entregou `MSF-R20-WAVE-001-025` como `completed`. O registrador
  retornou `passed/open_findings=0`; o builder derivou `complete` com 79
  candidatos; e a validação com `--require-external-audit` passou.
- O coordenador confirmou o evento no chat do worker e reproduziu a validação
  exigida. O relatório derivado preserva reviewer separado, rota Codex, status
  `passed`, `MSF-R20-MCA-001` como `resolved`, `open_findings=0` e a faixa
  `[322, 1724]` exigida pelo contrato.
- O packet isolado contém cinco arquivos; há 79 IDs de candidato distintos e os
  cinco fingerprints protegidos são exatamente iguais ao snapshot. Não houve
  mudança editorial, consolidação, Supabase, commit, push ou deploy.
- O Epic E1 está aprovado e concluído. O Epic E2 de `TOW0sWhPaZw` permanece
  apenas na fila e ainda precisa de seu planejamento, brief e delegação.

## 2026-07-11 - Epic E2 de TOW0sWhPaZw despachado

- O preflight do coordenador confirmou que a fonte
  `processed/TOW0sWhPaZw/content_segments.json` existe e que a pasta gold e o
  export isolado da wave ainda não existem.
- E2 foi planejado como um único épico enxuto: preflight, revisão cronológica
  completa, recall semântico adversarial e um build diagnóstico. Um único reparo
  de até 12 candidatos é permitido somente para erro objetivo de
  número/evidência, seguido de um único rebuild final; qualquer outro caso para
  com inventário e evento `blocked`.
- O worker `gpt-5.6-terra/high` recebeu ownership exclusivo de TOW gold e seu
  export isolado. Ele retornará apenas em conclusão, bloqueio ou decisão
  necessária; a auditoria cega e qualquer transição para `complete` continuam
  sob responsabilidade do coordenador.

## 2026-07-11 - E2 retomado com fonte raw canônica

- O worker bloqueou E2 antes de qualquer escrita: o preparador gold exige
  `raw/youtube/TOW0sWhPaZw/metadata.json` e `transcript_original.json`, mas a
  primeira delegação havia permitido apenas `content_segments.json`.
- O coordenador confirmou em leitura que ambos os arquivos raw existem, que
  `youtube_video_id=TOW0sWhPaZw`, `transcript_status=available` e que a
  transcrição tem 2.108 segmentos. Isso é expansão de leitura, não mudança de
  dados, schema ou fonte de verdade.
- A tentativa 24 mantém todo o ownership de escrita anterior e libera apenas a
  leitura dos dois arquivos raw. O worker continua proibido de tocar em E1,
  código, documentação, camadas consolidadas, release ou Supabase.

## 2026-07-11 - E2-S04a: correção de integridade procedural autorizada

- Após o raw autorizado, o worker concluiu preflight, 35 reviews, recall global
  e o único build diagnóstico. A calibração passou, mas o build identificou 31
  candidatos dos tipos `framework` ou `playbook_step` com `steps` vazios.
- O contrato exige `steps` não vazios para tipos procedurais. O coordenador
  conferiu o inventário e claims/evidências de amostra: os candidatos já contêm
  procedimentos ou sequências sustentados pela fonte; o defeito é estrutural,
  não um finding editorial novo.
- E2-S04a autoriza exclusivamente preencher `steps` para os 31 IDs fechados no
  plano, usando apenas claim e citações já existentes. São proibidos
  reclassificação, alteração de evidência, números, relações, títulos, candidatos
  ou qualquer outro episódio. Depois, há um único build final, uma validação
  normal e um export; qualquer novo erro encerra o job.

## 2026-07-11 - Auditoria do packet E2: um reparo editorial menor

- O worker entregou o packet de `TOW0sWhPaZw` com 2.068 segmentos limpos, 72
  candidatos distintos, 1.509 entradas no ledger, calibração 7/6 pass, packet
  de cinco arquivos e lifecycle `awaiting_external_audit/pending_external`.
- O coordenador confirmou a entrega no chat do worker, reproduziu a validação
  normal e auditou manifest, transcript, insights, ledger e calibrações. Quotes,
  contextos, números, relações, ledger, steps procedurais, calibrações e os cinco
  fingerprints protegidos passaram.
- O julgamento selado
  `.codex-work/msf-r20-coordinator-audits/TOW0sWhPaZw_audit.json` é
  `changes_requested` com o único finding minor aberto `MSF-R20-TOW-001`:
  `G072.takeaway_applicavel` contém `Me?a` em vez de `Meça`. As evidências
  transcript devem continuar verbatim.
- A auditoria declara sua limitação: o coordenador conhecia o reparo estrutural
  anterior de steps, portanto é independente do executor, mas não inteiramente
  cega ao contexto de geração. E2-S06 só registra o relatório e corrige esse
  caractere, antes de reauditoria.

## 2026-07-11 - E2-S06a: sincronização explícita do packet da wave

- E2-S06 corrigiu o gold atual de G072 e passou no build/validador normal, mas a
  reauditoria detectou que o packet `msf_r20_wave_001_TOW0sWhPaZw` ainda tinha
  `Me?a`. O gold atual e o packet de compatibilidade
  `msf_r20_piloto_TOW0sWhPaZw` já contêm `Meça`.
- A causa é determinística: o builder chama o exportador com o sufixo de
  compatibilidade `msf_r20_piloto_<video_id>`, enquanto a wave usa um caminho de
  export diferente. Não há erro no conteúdo corrigido.
- E2-S06a autoriza uma única chamada explícita ao exportador com o sufixo da
  wave, copiando somente os cinco arquivos permitidos do gold atual. Não permite
  build, validação, mudança editorial, código ou novo tratamento de dados.

## 2026-07-11 - Reauditoria E2 aprovada; registro determinístico pendente

- O export explícito sincronizou o packet da wave com o gold atual. O packet tem
  exatamente cinco arquivos, 72 IDs distintos e G072 agora contém `Meça`, sem a
  forma corrompida `Me?a`.
- O coordenador reproduziu a validação normal e confirmou os cinco fingerprints
  protegidos. A reauditoria selada
  `.codex-work/msf-r20-coordinator-audits/TOW0sWhPaZw_reaudit_001.json` é
  `passed`, com `MSF-R20-TOW-001` resolvido e `open_findings=0`; mantém a
  limitação declarada de conhecer o contexto do reparo.
- E2-S07 fica limitado a registrar esse julgamento, rodar um build e validar uma
  vez com `--require-external-audit`, para derivar `complete/passed`. O worker
  não pode editar a reauditoria ou dados editoriais.

## 2026-07-11 - Wave 001 concluída

- O worker registrou a reauditoria aprovada de `TOW0sWhPaZw`; o builder derivou
  `complete/passed` e o coordenador reproduziu a validação com
  `--require-external-audit`. O estado final é `complete`, `audit_status=passed`
  e `open_audit_findings=0`, com 72 candidatos distintos e
  `MSF-R20-TOW-001` resolvido.
- A wave termina com E1 `mCaFyZpXJdE` (28 candidatos) e E2 `TOW0sWhPaZw` (72
  candidatos) completos e aprovados. Os dois packets têm cinco arquivos e os
  cinco fingerprints protegidos permanecem idênticos ao snapshot da wave.
- Nenhum commit, push, deploy, consolidação gold ou ação no Supabase foi feita.
  A fila durável e o plano da wave foram encerrados como `done`.

## 2026-07-11 - Hardening pré-próxima wave iniciado

- A Wave 001 revelou três causas mecânicas de retrabalho: o builder exporta por
  padrão para o sufixo de compatibilidade, o preparador depende de fontes raw
  não declaradas no preflight e `steps` procedurais podem falhar somente no build
  final.
- O job `MSF-R20-NEXT-WAVE-HARDENING-001` foi criado para corrigir esses pontos
  de modo compatível e testado: sufixo explícito opcional, preflight raw sem
  escrita e modo de prontidão sem escrita antes do build final.
- O contrato de worker, AGENTS, coordenação e contrato gold passam a exigir as
  fontes raw `metadata.json` e `transcript_original.json` antes de iniciar uma
  extração. Nenhum dado real, export ou fingerprint protegido é autorizado neste
  épico.

### 2026-07-11 — Continuação mínima de validação do hardening R20

- O worker implementou H1-H4, mas duas execuções da suíte focada pararam apenas
  na limpeza do diretório temporário: primeiro no Temp global e depois no
  basetemp dentro do OneDrive. Nenhum dado real foi escrito.
- Na revisão do coordenador, foi identificada uma lacuna adicional: o preflight
  também deve rejeitar `metadata.transcript_status` diferente de `available`,
  mesmo que o transcript tenha segmentos.
- Foi autorizada somente uma continuação: teste de regressão dessa condição e
  uma execução da suíte usando
  `C:\MSF-data\Marketing_Swipe_File\.tmp\msf-r20-next-wave-hardening-001-002`.
  O próximo gate é revisão independente do diff e dos testes; commit, push,
  deploy, consolidação e Supabase continuam fora do escopo.

### 2026-07-11 — Hardening aprovado para a próxima wave

- O worker concluiu H1-H4 e informou `16 passed` no temporário externo ao
  OneDrive. A entrega foi confirmada no chat de origem.
- O coordenador revisou o diff de
  `build_gold_semantic_extraction.py`, `reprocess_gold_episode.py` e
  `test_gold_pipeline.py`; confirmou que o preflight bloqueia também
  `metadata.transcript_status` incompatível, sem escrita; e reproduziu a suíte
  focada com **16 testes passando**. `git diff --check` passou.
- Decisão: **APROVADO PARA A PRÓXIMA WAVE FUNCIONAL**. Não houve alteração de
  dados reais, exports de episódio, auditorias, fingerprints protegidos,
  commit, push, deploy, consolidação ou Supabase. O próximo trabalho deve usar
  o preflight raw e o readiness check antes do build final.

### 2026-07-11 — Wave 002 E1 planejada e liberada

- Episódio selecionado: `YcqJ_vrjf-g` (*A Fórmula dos Criativos que Vendem
  7D/Dia*), por combinar tema técnico de criativos com fonte pronta e tamanho
  controlado de 1.593 segmentos.
- O coordenador executou o preflight raw sem escrita: metadata e transcript
  estão disponíveis e consistentes; a pasta gold e o export próprio da Wave 002
  estavam ausentes antes da delegação.
- O épico exige preparação, revisão cronológica integral, recall adversarial,
  readiness sem escrita e um único build/export para
  `msf_r20_wave_002_YcqJ_vrjf-g`. O limite do worker é
  `awaiting_external_audit/pending_external`; a auditoria e qualquer conclusão
  continuam sendo gates separados do coordenador.

### 2026-07-11 — Wave 002 E1: correção procedural limitada

- O worker preparou 1.553 segmentos limpos em 23 chunks, registrou 23 reviews,
  47 candidatos, 246 sinais e 16 calibrações. O readiness read-only bloqueou
  antes do build somente por `steps` ausentes em G003, G028, G040 e G043.
- O coordenador confirmou a entrega no chat de origem, reproduziu o readiness
  com o mesmo inventário e calibração aprovada, verificou ausência de build e
  export e leu os claims/segmentos dos quatro candidatos.
- Decisão: manter os quatro como `framework` e acrescentar somente passos
  sustentados. Nenhum outro campo pode mudar. Depois haverá uma execução de
  readiness; se passar, um build com sufixo explícito, um validador normal e a
  confirmação do packet. Novo erro encerra a tentativa sem segundo reparo.

### 2026-07-11 — Wave 002 E1: auditoria cega com remediação planejada

- O packet de `YcqJ_vrjf-g` foi auditado pelo coordenador somente pelos cinco
  arquivos cegos. Passaram: manifesto, IDs, 108 quotes verbatim com tempos
  coerentes, ranges, 250 entradas de ledger, destinos captured/excluded,
  16 calibrações com 10 cobertas para mínimo 4, relações e fingerprints.
- O julgamento selado abriu três findings: ausência global de `numbers`
  estruturados em claims quantitativos materiais, quatro strings editoriais com
  `?` dentro de palavras e G027 sustentado principalmente por pergunta do
  entrevistador.
- A remediação é fechada: registrar o relatório sem editá-lo; estruturar apenas
  números materiais nos 31 candidatos listados; corrigir quatro strings ASCII;
  reescrever G027 sobre o caso diretamente sustentado de usar repertório quando
  só há manchete e excluir 0764 como interviewer_restate. Depois: um readiness,
  um build, um validador normal e novo packet pendente de reauditoria.

### 2026-07-11 — Wave 002 E1: reauditoria aprovada

- A reauditoria packet-only confirmou a resolução dos três findings: 58 records
  numéricos coerentes com quotes literais, nenhum caractere editorial corrompido
  e G027 sustentado diretamente por 0770/0772; 0764 está
  `excluded/interviewer_restate`.
- Integridade revalidada: 47 IDs, 108 quotes/timings verbatim, ledger de 250
  entradas, calibração 10/4 pass, relações simétricas e packet com cinco
  arquivos. Os quatro fingerprints protegidos antes/depois permanecem iguais.
- O relatório `YcqJ_vrjf-g_reaudit_001.json` foi selado como `passed` com zero
  findings abertos. Resta somente o registro determinístico, build e validador
  com auditoria exigida; não há edição editorial autorizada nessa última story.

### 2026-07-11 — Wave 002 E1 concluída

- A reauditoria aprovada foi registrada uma vez e o builder derivou
  `complete/passed` sem nova edição editorial.
- O coordenador confirmou a entrega no chat do worker e reproduziu
  `validate_gold_extraction --require-external-audit`: **pass**, sem erros.
  Estado final: 47 IDs distintos, `open_audit_findings=0`, packet com cinco
  arquivos e quatro fingerprints protegidos antes/depois idênticos.
- Decisão: **APROVADO FUNCIONALMENTE — Wave 002 E1 concluída**. Nenhum commit,
  push, deploy, consolidação ou Supabase foi solicitado ou executado. O próximo
  trabalho pode planejar outro episódio gold sob os gates já endurecidos.

### 2026-07-11 — Wave 002 E2 planejada e liberada

- Episódio selecionado: `qj04cUeaRAw` (*Lucrando Múltiplos 7D/Mês com Perpétuo
  para Público Frio*), para ampliar a base com metodologia de perpétuo em
  audiência fria.
- O preflight raw read-only passou com 1.609 segmentos; não existiam gold nem
  export da Wave 002 antes da delegação.
- O novo plano torna explícito o autocheck de números materiais, texto ASCII e
  distinção entre fala do entrevistado e perguntas do entrevistador, para
  reduzir uma rodada corretiva observada em E1. O worker pode entregar somente
  um packet pendente de auditoria independente.

### 2026-07-11 — Wave 002 E2: auditoria cega e correção limitada

- O packet inicial tinha 25 candidatos, 18 numbers, ledger de 1.155 entradas e
  calibração 19/5 pass. A auditoria cega confirmou integridade de manifesto,
  quotes/timings, relações, ledger, calibração e encoding.
- Três findings foram selados: G002 e G005 são bio/promo; G017, G023 e G024
  usam evidências mínimas truncadas; G014 normaliza o ano como 25 em vez de
  2025.
- A remediação é fechada: registrar o relatório sem editá-lo, remover os dois
  candidatos impróprios, reescrever os três com fala afirmativa adjacente e
  corrigir somente o valor normalizado do ano. Depois haverá um readiness, um
  build, um validador normal e nova auditoria independente.

### 2026-07-11 — Wave 002 E2: correção residual de literalidade planejada

- A auditoria selada foi registrada e o inventário fechado foi aplicado. O
  readiness único parou antes de build, validação ou export por duas falhas
  literais: G017 não incluía 0920 na evidência mínima do intervalo `2, 3, 4, 10
  dias`, e G024 mantinha `tr?s` em vez da grafia literal `três` de 1358.
- O coordenador confirmou que a alternativa mínima é segura: acrescentar 0920
  somente à evidência mínima de G017 e trocar somente o `numbers.raw` de G024
  pela grafia literal. A story E2-S07e não relê a auditoria, não a registra de
  novo e não altera outros campos editoriais.
- Depois haverá uma única tentativa de readiness; se aprovada, um build e um
  validador normal. O packet deve continuar pendente de auditoria, com os três
  findings ainda abertos. Não houve commit, push, deploy, consolidação ou
  Supabase.

### 2026-07-11 — Wave 002 E2: reauditoria com um finding residual

- O packet rederivado passou em readiness, build e validação normal: 23 IDs,
  calibração 16/4, cinco arquivos cegos e fingerprints protegidos iguais. Ele
  permaneceu corretamente pendente, com os três findings da auditoria inicial.
- A reauditoria independente confirmou que G002/G005 foram removidos com os
  destinos corretos no ledger e que G014 normaliza 2025. Esses dois findings
  estão resolvidos.
- G024 continua incompleto: a minimal_quote não traz a decisão do dia atual
  (1359/1361) nem a redução de verba antes do desligamento (1363-1367), que são
  a continuação material do framework e ficaram excluídos do ledger. O relatório
  selado `qj04cUeaRAw_reaudit_001.json` tem um finding major aberto.
- E2-S08 registrará esse relatório e corrigirá exclusivamente G024 e os
  segmentos de ledger definidos. Depois fará uma única sequência de readiness,
  build e validação normal. Não houve commit, push, deploy, consolidação ou
  Supabase.

### 2026-07-11 — Wave 002 E2: normalização ASCII residual planejada

- E2-S07e resolveu G017 ao incluir 0920 na evidência mínima. O único readiness
  seguinte voltou a parar em G024, sem build, validação ou export.
- A inspeção independente confirmou o dado gravado como `tr?s` e confirmou no
  contrato do validador que campos estruturados podem usar a forma ASCII NFKD
  da evidência verbatim. A forma comparável de `três` é `tres`.
- E2-S07f trocará exclusivamente esse `numbers.raw`; depois fará uma única
  tentativa de readiness, build e validação normal, se cada gate anterior
  passar. A auditoria não será registrada novamente e os três findings seguem
  abertos até a nova reauditoria. Não houve release, consolidação ou Supabase.

### 2026-07-11 — Wave 002 E2: reauditoria final aprovada

- O packet final permanece íntegro: cinco arquivos cegos, 23 candidatos,
  quotes verbatim, números, ledger, relações e calibração 17/3 com targets
  distintos passaram. Os fingerprints protegidos permanecem iguais.
- G024 agora traz, em evidência mínima e ledger, a sequência integral 7-3-1,
  a decisão pelo dia atual, a redução proporcional de 50%-70% antes de
  desligar e a retomada de 20%. Isso resolve o último finding major.
- O relatório selado `qj04cUeaRAw_reaudit_002.json` está `passed` com zero
  findings abertos. Resta apenas registrá-lo e rodar o build/validador com
  auditoria exigida; não há edição editorial autorizada nessa story final.

### 2026-07-11 — Wave 002 E2 concluída

- A reauditoria aprovada foi registrada uma vez, o builder derivou
  `complete/passed` sem editar conteúdo e a validação final com
  `--require-external-audit` passou sem erros.
- Quality gate independente reproduzido pelo coordenador: `complete`,
  `audit_status=passed`, `open_audit_findings=0`, 23 IDs únicos, relatório de
  revisor separado válido, packet com os cinco arquivos cegos e quatro
  fingerprints protegidos idênticos antes/depois.
- Decisão: **APROVADO FUNCIONALMENTE — Wave 002 E2 concluída**. Não houve
  commit, push, deploy, consolidação ou Supabase.

### 2026-07-11 — Wave 003 ampliada para três episódios

- O owner pediu mais escala por épico. A coordenação passou a permitir uma
  delegação multi-episódio explicitamente delimitada, executada sequencialmente
  no mesmo worker e com ownership/export isolado por episódio.
- Para reduzir loops antes da auditoria, cada episódio pode usar um readiness
  diagnóstico, um reparo interno do inventário determinístico e um readiness
  final. Depois há no máximo um build e um validador normal. O worker envia
  somente um evento final consolidado; a auditoria continua independente.
- Selecionados `VQJ_Y8E6Hw0`, `icryHLwikKw` e `4Ad8K3xIX4g`. Os preflights raw
  read-only passaram com 402, 405 e 497 segmentos; `content_segments.json`
  existe e os diretórios gold/exports da Wave 003 estavam ausentes.
- O plano está em `docs/coordination/msf-r20-wave-003-plan.md`. Não houve
  commit, push, deploy, consolidação ou Supabase.

### 2026-07-11 — Wave 003: auditorias cegas e remediação consolidada

- O worker entregou os três packets em um único evento. O coordenador auditou
  cada um separadamente apenas pelos cinco arquivos cegos e, depois de selar os
  julgamentos, reproduziu os três validadores normais e confirmou fingerprints
  protegidos 4/4 iguais em todos.
- VQJ recebeu 3 findings: ausência sistemática de `numbers`, omissão da faixa
  US$27-US$97 e relações/merge ausentes. icry recebeu 4: quatro blocos de recall,
  números, G008 vindo do encerramento/G007 corrompido e relações. 4Ad recebeu 4:
  números, testes de closes/micro-leads, G010 sustentado por CTA e relações.
- O processo ganhou um autocheck obrigatório antes do readiness: inventário de
  candidatos com sinais numéricos e `numbers` vazio, todos os targets de
  calibração em fail, evidência somente de entrevistador/promo/outro e grupos
  sobrepostos sem relação/merge.
- A tentativa 2 registra os três relatórios e corrige os inventários em um único
  épico sequencial, com um evento final consolidado. Não houve commit, push,
  deploy, consolidação ou Supabase.

### 2026-07-11 — Wave 003: restauração de VQJ verificada

- Os três audits foram registrados. A remediação avançou em VQJ, mas uma
  sobrescrita acidental do review 007 foi detectada antes dos gates; o worker
  restaurou o arquivo do candidate chunk preservado e retornou estado parcial.
- O coordenador verificou sete reviews completas, hashes/chunk IDs coerentes,
  24 IDs únicos G001-G024, G021-G023 corretamente no chunk 007, números e
  relações auditadas. Nenhum readiness/build/validator de remediação havia sido
  executado, portanto não há transição duplicada.
- A tentativa 3 termina os gates de VQJ sem refazer a correção e continua as
  remediações ainda pendentes de icry e 4Ad. Auditorias não serão registradas
  novamente. Não houve commit, push, deploy, consolidação ou Supabase.

### 2026-07-11 — Wave 003: VQJ reaudidado e escopo reduzido

- VQJ passou readiness, build e validador normal com 24 candidatos. A
  reauditoria resolveu a faixa US$27-US$97, mas reteve dois resíduos objetivos:
  G019 ainda não estrutura as taxas de upsells 2/3 e G015/G016 não têm a relação
  solicitada. O relatório `VQJ_Y8E6Hw0_reaudit_001.json` ficou com dois findings.
- Para evitar outra entrega parcial ampla, W3-R07 exclui VQJ e processa somente
  as remediações ainda não iniciadas de icry e 4Ad. Seus audits já estão
  registrados e não serão repetidos.
- VQJ será retomado depois em escopo estreito junto ao próximo gate adequado.
  Não houve commit, push, deploy, consolidação ou Supabase.

### 2026-07-11 — Wave 003: bloqueio seguro antes da escrita em ICRY

- A tentativa W3-R07 parou antes de qualquer escrita editorial. A montagem de
  relações referenciou o novo `icryHLwikKw-G011` antes de ele existir no mapa
  em memória e gerou `KeyError`. O chat do worker confirmou estado idle, oito
  candidatos ICRY preservados e 4Ad ainda não iniciado.
- A tentativa 5 usa caminho diferente: persiste primeiro G009-G012 sem novas
  relações, relê os reviews do disco, reconstrói o mapa completo e somente
  então adiciona relações. ICRY e 4Ad não compartilham estado em memória.
- O contador desta subtask registra uma devolução consecutiva sem progresso.
  VQJ continua read-only. Não houve commit, push, deploy, consolidação ou
  Supabase.

### 2026-07-11 — Wave 003: segunda devolução vazia e rota sem Python inline

- W3-R08 parou novamente antes de qualquer escrita: a invocação da Fase A tinha
  `SyntaxError` antes de o processo Python iniciar. ICRY preserva oito IDs e 4Ad
  preserva dez; nenhum dos dois recebeu correção editorial nessa tentativa.
- O contador da subtask passa a duas devoluções consecutivas sem progresso. A
  tentativa 6 muda materialmente a execução: começa por 4Ad e usa helpers
  job-local com `py_compile`, modo read-only `--check` e uma única aplicação,
  eliminando chamadas Python inline.
- Os helpers ficam limitados a
  `.codex-work/worker-jobs/MSF-R20-WAVE-003-W3-R09/`. Scripts do produto, docs,
  fila e audits permanecem read-only para o worker. Não houve commit, push,
  deploy, consolidação ou Supabase.

### 2026-07-11 — Wave 003: avanço em 4Ad e inventário literal fechado

- O helper file-based de 4Ad compilou, passou `--check` sem escrita e teve um
  único `--apply`. O episódio agora tem 12 candidatos, incluindo G011/G012;
  G010 usa fala do convidado e as relações auditadas foram gravadas.
- O readiness diagnóstico passou calibração e reteve apenas seis raws. A
  conferência independente fechou as formas literais em G006, G009, G011 e
  G012; valores, unidades, claims e relações não precisam mudar.
- Como houve artefato material novo, o contador de devoluções sem progresso
  volta a zero. A tentativa 7 usa helper corretivo novo, conclui 4Ad e depois
  retoma ICRY em duas fases. Não houve commit, push, deploy, consolidação ou
  Supabase.

### 2026-07-11 — Wave 003: reauditorias de 4Ad e ICRY

- As reauditorias foram formadas somente pelos cinco arquivos cegos de cada
  packet e seladas antes da leitura de status, relatórios ou fingerprints
  internos. 4Ad passou com zero findings; ICRY reteve um finding minor de
  caveats, ASCII, encoding e concordância.
- Depois do selo, o coordenador reproduziu os dois validadores normais e
  confirmou quatro fingerprints antes/depois iguais em cada episódio.
- W3-R11 registra o passe de 4Ad e deriva complete sem edição editorial. Em
  ICRY, registra changes_requested e altera somente quatro campos editoriais e
  três caveats fechados antes de novo packet/re-auditoria. Não houve commit,
  push, deploy, consolidação ou Supabase.

### 2026-07-11 — Wave 003: 4Ad concluído e ICRY aprovado

- 4Ad foi derivado para `complete/passed` com 12 IDs, zero findings, validador
  exigindo auditoria aprovado e quatro fingerprints iguais.
- O packet ICRY corrigido foi reaudidado somente pelos cinco arquivos cegos. Os
  sete ajustes estavam exatos; estrutura, quotes, números, relações, ledger e
  calibração passaram. `icryHLwikKw_reaudit_002.json` foi selado `passed/0`.
- W3-R12 conclui ICRY sem edição e corrige somente os dois resíduos selados de
  VQJ: números de upsells 2/3 em G019 e relação G016→G015. Não houve commit,
  push, deploy, consolidação ou Supabase.

### 2026-07-11 — Wave 003: VQJ aprovado para registro final

- ICRY foi derivado para `complete/passed` com 11 IDs, zero findings, validador
  exigindo auditoria aprovado e fingerprints preservados.
- O packet VQJ corrigido foi reaudidado somente pelos cinco arquivos cegos. Os
  seis records de G019 e a relação G016→G015 estavam corretos; estrutura,
  quotes, ledger, calibração e editorial passaram. A reauditoria 002 foi selada
  `passed/0`.
- O coordenador reproduziu o validador normal de VQJ e confirmou fingerprints
  4/4 iguais nos três episódios. W3-R13 fará apenas o registro determinístico e
  o gate final de VQJ. Não houve commit, push, deploy, consolidação ou Supabase.

### 2026-07-11 — Wave 003 concluída e aprovada

- VQJ foi derivado para `complete/passed` a partir da reauditoria final selada,
  sem edição editorial. O worker entregou 24 IDs, zero findings, packet com
  cinco arquivos e fingerprints 4/4 iguais.
- O coordenador reproduziu `validate_gold_extraction --require-external-audit`
  nos três episódios; todos passaram sem erros. Os estados reais são:
  VQJ 24 IDs, ICRY 11 e 4Ad 12, todos `complete/passed`, auditoria `passed` e
  zero findings.
- Os três relatórios finais registram o coordenador/thread de revisão separado
  do thread executor; packets têm cinco arquivos cada; os 12 fingerprints
  protegidos comparados permanecem iguais.
- Decisão: **APROVADO FUNCIONALMENTE — Wave 003 concluída**. Não houve commit,
  push, deploy, consolidação gold ou Supabase.

### 2026-07-12 — Fast Path gold planejado para episódios novos e retomáveis

- O owner pediu redução de tempo e consumo de tokens sem enfraquecer o padrão-
  ouro. A análise dos três episódios da Wave 003 mostrou que os work orders são
  39% a 54% maiores que o transcript limpo por repetição de texto, e que
  numbers, steps, encoding, relações e persistência artesanal ainda geram
  correções tardias.
- Foi criado `MSF-R20-GOLD-FASTPATH-001` como um único pipeline com `mode=auto`.
  Episódios novos começam em raw/preflight e chegam ao packet; episódios
  incompletos reaproveitam hashes e reviews válidos e continuam do último gate.
  Episódios `complete/passed` ficam read-only por padrão.
- O plano inclui work orders compactos, validação antes da escrita, patch
  transacional, autocheck e recall dirigido, orquestrador multi-episódio, delta
  de reauditoria, métricas, testes e atualização posterior da skill.
- Não será criado MCP nesta fase: scripts locais oferecem menor custo e menos
  superfície de falha. O épico está somente planejado/queued; não foi delegado,
  não alterou dados reais e não executou commit, push, deploy, consolidação ou
  Supabase.

### 2026-07-12 — Fast Path gold delegado para implementação

- O `EXECUTION BRIEF — MSF-R20-GOLD-FASTPATH-001` foi publicado em linguagem
  simples antes da delegação. O worker designado continua sendo Extração
  Padrão-Ouro, com `gpt-5.6-terra/high` e ownership exclusivo dos scripts,
  testes, fixtures e skill listados no plano.
- A implementação deve cobrir o mesmo `mode=auto` para episódios novos,
  retomáveis e `complete/passed` protegido, medir redução mínima de 25% nos work
  orders dos fixtures Wave 003 e preservar compatibilidade legada.
- Dados reais, exports, auditorias seladas, fila e documentos do coordenador são
  read-only. O worker enviará um único `WORKER_EVENT` final; o coordenador não
  fará polling ou processamento paralelo e retomará somente para o quality gate.

### 2026-07-12 — Fast Path: quality gate solicita primeira correção

- O worker entregou F1-F8 sem tocar dados reais. O coordenador reproduziu 36
  testes, compilou os oito módulos, passou `git diff --check` e confirmou em
  leitura que VQJ, ICRY e 4Ad continuam protegidos. A redução estimada dos work
  orders foi 66,98%, 69,26% e 66,17%.
- O resultado não foi aprovado porque os testes não cobriam seis contratos:
  runner retomável não executa gates; diretório parcial sem status parece novo;
  recorder não valida relações/IDs contra reviews persistidas; patch não remove
  candidato nem altera ledger; autocheck não detecta entrevistador; delta omite
  campos materiais, manifesto e transcript.
- Decisão: `changes_requested`, findings FP-001 a FP-006. A primeira rodada
  corretiva adicionará testes fechados e continuará sem dados reais, release,
  consolidação ou Supabase.
- O brief da correção 1/2 foi publicado e limita a retomada aos seis findings,
  scripts Fast Path/gold, testes/fixtures e skill. O coordenador encerra o turno
  após a delegação e só retoma com o próximo `WORKER_EVENT` final.

### 2026-07-12 — Fast Path: segunda correção limitada ao patch seguro

- A primeira correção resolveu runner retomável, checkpoint parcial, recorder
  global, autocheck e delta. O coordenador reproduziu 40 testes, compilação,
  diff check, proteção read-only da Wave 003, reduções de 66% a 69% e
  fingerprints atuais 4/4 em cada episódio.
- FP-004 continua aberto porque remoção e ledger update aceitam ausência de
  assert e as decisões de ledger não são validadas contra os candidatos finais.
  Também será sincronizado o help desatualizado do runner.
- A correção 2/2 fica estritamente nesses pontos. Dados reais permanecem
  read-only e não houve release, consolidação ou Supabase.
- O brief final foi publicado antes da delegação. O worker enviará somente um
  evento final; o coordenador encerra o turno e não acompanha a execução.

### 2026-07-12 — Fast Path concluído e aprovado

- A correção final tornou obrigatórias as precondições de remoção e ledger,
  validou dispositions, segmentos, duplicidade, destinos, exclusões e
  `duplicate_of` contra transcript e candidatos finais antes do batch atômico,
  e sincronizou o help do runner.
- O coordenador reproduziu 46 testes, compilou os módulos finais, passou
  `git diff --check`, confirmou o help e reexecutou o runner Wave 003 somente
  leitura. VQJ, ICRY e 4Ad foram classificados como protegidos, com reduções
  estimadas de 66,98%, 69,26% e 66,17%.
- Os fingerprints atuais continuam iguais ao snapshot: 4/4 por episódio,
  12/12 no total. Nenhum dado real, export ou auditoria foi alterado.
- Decisão: **APROVADO FUNCIONALMENTE — Fast Path liberado para a próxima wave**.
  Não houve commit, push, deploy, consolidação ou Supabase.

### 2026-07-13 — Wave 004 preparada para a primeira execução real do Fast Path

- O coordenador selecionou pela fila de prioridade os próximos três episódios
  com fonte raw elegível e sem gold existente: `yyoGeQp5yzM` (1.142 segmentos),
  `8WEvN5T7J0U` (844) e `v6luZ9KvmOI` (1.784).
- O `--preflight-raw` read-only passou nos três; metadata e transcript estão
  compatíveis, `content_segments.json` existe e os diretórios gold/exports da
  Wave 004 estavam ausentes antes da delegação.
- Foram criados o plano `msf-r20-wave-004-plan.md` e o manifesto `mode=auto`.
  O épico autoriza preparação Fast Path, revisão semântica integral, recall e
  autocheck, um reparo declarativo fechado por episódio e a geração de três
  packets cegos independentes.
- O worker altera somente os três diretórios gold, os três exports e seu
  diretório job-local. Código, docs, fila, auditorias, outros episódios,
  consolidação, Supabase e release permanecem fora de escopo.
- O `EXECUTION BRIEF` foi publicado antes da delegação. O worker enviará um
  único evento final; o coordenador encerra o turno e só retoma para auditoria
  independente e quality gate.

### 2026-07-13 — Wave 004 retomada de checkpoint semântico seguro

- O worker preparou os três episódios pelo Fast Path e interrompeu antes de
  readiness/build/packet para não alegar revisão parcial como completa.
- O coordenador confirmou em leitura que `yyoGeQp5yzM` possui 14 reviews
  completas, hashes presentes e 34 candidatos únicos. O número 32 do evento
  resumido era uma inconsistência de reporte; o disco e o chat registram 34.
- O runner read-only marcou os três episódios como
  `resumable_incomplete_gold`, sem chunks stale ou inconsistentes. Em yyo,
  somente 015–021 permanecem pendentes; os outros dois estão preparados e ainda
  sem reviews. Nenhum export existe.
- O checkpoint traz progresso material e não exige decisão do owner. W4-R01
  mantém o mesmo job e ownership: preserva 001–014, conclui yyo e seus gates e
  então processa 8WE e v6lu sequencialmente. O worker continuará enviando
  somente um evento final ao coordenador.

### 2026-07-13 — Wave 004: auditoria inicial de yyo e retomada W4-R02

- O evento `MSF-R20-WAVE-004-002` entregou `yyoGeQp5yzM` com 21 reviews, 50
  candidatos, readiness pronto, build e validador normal aprovados e packet
  cego de cinco arquivos. `8WEvN5T7J0U` ficou retomável com o chunk 001
  persistido; `v6luZ9KvmOI` permaneceu preparado e sem gates.
- O coordenador auditou yyo somente pelos cinco arquivos permitidos do packet.
  Integridade, IDs, evidências, ledger, números estruturados, relações e
  calibração passaram. A auditoria é cega ao histórico do executor, mas não ao
  episódio nem ao estilo.
- O julgamento foi selado em
  `.codex-work/msf-r20-coordinator-audits/yyoGeQp5yzM_audit.json` como
  `changes_requested`, com quatro findings major abertos: comparação de captura
  de valor por cliente, mudança temporal de diferencial, span/camadas de gestão
  e script com IA para buscar casos análogos.
- W4-R02 mantém o mesmo job e ownership. Primeiro registra o audit e corrige
  somente os quatro findings; depois conclui 8WE desde o chunk 002 e v6lu. Cada
  episódio usa recall/autocheck/readiness antes de um único build e validador;
  packets parciais continuam proibidos.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado. O
  próximo gate é a reauditoria independente de yyo e a auditoria inicial dos
  packets completos de 8WE e v6lu.

### 2026-07-13 — Wave 004: envelope compatível e retomada W4-R03

- O evento `MSF-R20-WAVE-004-003` bloqueou yyo antes de qualquer edição: o
  registrador atual exige `segment_range` numérico e rejeitou os ranges textuais
  da auditoria selada. O arquivo original e o packet ficaram preservados.
- O coordenador confirmou o contrato diretamente em
  `validate_external_audit_report` e criou
  `yyoGeQp5yzM_audit_envelope_001.json`. O envelope mantém o mesmo julgamento,
  quatro findings, evidências e ações; converte somente os ranges para clean
  indexes zero-based. A validação oficial retornou `errors=[]`.
- 8WE avançou de forma material: chunks 001 e 002 estão completos, com hashes,
  seis IDs únicos e nenhum chunk stale ou inconsistente. O runner read-only
  lista 003–014 como pendentes. v6lu continua preparado e sem review.
- W4-R03 usará somente o novo envelope para registrar yyo, corrigirá os quatro
  achados e continuará 8WE no chunk 003 antes de processar v6lu. A auditoria
  original e o envelope são read-only para o worker.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Wave 005: erro de encoding isolado antes da escrita

- O evento `MSF-R20-WAVE-005-014` não escreveu qoh 011–020: o helper de
  paridade encontrou um único `ç` em `G020.title`. O recorder não foi chamado,
  e o checkpoint 001–010 segue íntegro.
- A correção autorizada é exclusivamente `frustração→frustracao` no título.
  Para antecipar essa classe de erro, a próxima rota roda `editorial_ascii_errors`
  diretamente em todos os campos antes do helper composto de paridade.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Wave 005: primeiro checkpoint de qoh persistido

- O evento `MSF-R20-WAVE-005-013` confirmou que a rota de preflight de paridade
  resolveu o problema do primeiro lote: qoh 001–010 passou com `errors=[]` e
  foi persistido uma vez, atomicamente, com dez candidatos únicos.
- O limite nativo de contexto ocorreu depois da fronteira segura, antes de ler
  011–020. O runner independente confirma que somente 011–036 permanecem,
  sem chunk stale ou inconsistente. Não existe packet parcial nem finding de
  qualidade nesse checkpoint.
- A próxima delegação cobre somente 011–020 e reutiliza o helper read-only
  comprovado antes do recorder. A auditoria continua reservada ao episódio
  finalizado.

### 2026-07-13 — Wave 005: qoh passa a validar o payload antes de gravar

- O evento `MSF-R20-WAVE-005-012` confirmou `JF2oC44lBG8` completo pelo
  validador com auditoria exigida. Em qoh, o primeiro batch 001–010 foi
  rejeitado atomicamente antes de qualquer review, candidato ou packet ser
  escrito; os 36 chunks continuam pendentes e íntegros.
- O inventário é de contrato, não de cobertura: temas/tipos/roles não canônicos
  e quatro raws que não reproduziam literalmente a transcrição. Foi revisado e
  convertido em substituições fechadas no plano W5-R13; nenhum claim ou
  evidência precisa ser inventado.
- Para evitar nova ida e volta, a próxima tentativa usa um helper job-local de
  leitura que chama as mesmas validações do recorder antes da única escrita
  atômica. O recorder deixa de ser a primeira checagem de schema.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Wave 005: JF auditado e qoh liberado

- O evento `MSF-R20-WAVE-005-011` concluiu `JF2oC44lBG8`: 24 reviews, 27
  candidatos, hard blockers zero, finalizador e validação normal aprovados,
  packet com cinco arquivos e fingerprints 4/4 iguais.
- O coordenador auditou o packet cego e reproduziu integridade de arquivos,
  IDs, quotes/números, ledger, relações e 20 targets de calibração sem
  duplicidade. O parecer
  `.codex-work/msf-r20-coordinator-audits/JF2oC44lBG8_audit_001.json` foi
  selado com `passed` e zero findings. As quatro ambigüidades restantes são
  avisos explícitos, não alegações de cobertura nem defeitos estruturais.
- A próxima unidade é `qohJceyapS0` completa: o worker registra o audit de JF
  deterministicamente e entrega um único packet de qoh. O coordenador não faz
  revisões intermediárias e só retorna para auditoria após essa entrega.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Wave 005: zo concluído; retry de schema em JF

- O worker registrou o parecer selado de `zoChfFHnlOQ` uma vez. O coordenador
  reproduziu o validador com `--require-external-audit`: `complete/passed`,
  zero findings, 48 candidatos e sem erros. Não houve alteração editorial de
  zo durante essa transição derivada.
- A única gravação atômica planejada para `JF2oC44lBG8` 019–024 foi recusada
  antes de qualquer escrita. O checkpoint 001–018/24 e 19 IDs permanece
  preservado. A causa se limita a dois campos do payload novo: um acento em
  texto editorial de G024 e o tipo não permitido `reported_case` em G026.
- Foi autorizada uma tentativa materialmente nova, com payload novo e somente
  `G024.takeaway_applicavel: peça→peca` e `G026.type: reported_case→example`.
  Depois dela, o worker pode finalizar JF; o coordenador só retorna para auditar
  seu packet integral.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Wave 004 aprovada

- O evento 026 registrou a reauditoria aprovada de v6lu uma vez e derivou
  `complete/passed` sem editar candidatos, reviews, ledger ou calibração.
- O coordenador reproduziu `validate_gold_extraction --require-external-audit`:
  `pass/errors=[]`; v6lu tem 41 IDs únicos, zero findings e packet de cinco
  arquivos. Os quatro hashes protegidos foram recalculados e conferem com o
  snapshot.
- O runner Fast Path em modo somente leitura confirmou yyo (54), 8WE (42) e
  v6lu (41) como `protected_complete_read_only`, todos `complete/passed`.
- Decisão: Wave 004 aprovada. Nenhum commit, push, deploy, consolidação gold ou
  Supabase foi executado.

### 2026-07-13 — Reauditoria final de v6lu aprovada

- O evento 025 aplicou um único patch: G014 `students`, G024 `result` e as
  citações 1697–1702 de G041. O ledger derivado passou a capturar 1697–1702
  para G041, sem `ledger_decisions` manuais.
- A reauditoria packet-only `v6luZ9KvmOI_reaudit_002.json` foi selada como
  `passed/open_findings=0`. As verificações cegas confirmaram 41 IDs, quotes
  verbatim, números, ledger, relações, calibração e packet de cinco arquivos.
- W4-R25 fica limitado ao registro determinístico da auditoria aprovada e à
  derivação de `complete`; não há edição editorial autorizada.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Wave 005: primeiro patch aprovado; segundo patch replanejado

- O evento `MSF-R20-WAVE-005-005` confirmou que o patch editorial foi aplicado
  uma vez e o patch de calibração parou no `--check`, antes de qualquer escrita.
  O coordenador reproduziu o verificador: 48 IDs permanecem únicos e somente os
  21 candidatos autorizados foram alterados. O autocheck confirmou zero alertas
  numéricos, claim/evidência e overlap.
- A causa é mecânica e localizada: os targets históricos não persistem
  `semantic_candidate_ids`; o manifesto os assertou como `[]`, mas o patcher
  distingue campo ausente de lista vazia. Não houve alteração de calibração.
- A continuação W5-R06 usa o segundo e último patch permitido: assertions dos
  campos realmente presentes, os cinco redirects já revisados e somente o
  caveat de caso reportado de `G031`, que emergiu após o primeiro patch. Se o
  check falhar, não haverá nova tentativa de escrita neste escopo.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Wave 005: rota final extrai precondições diretamente do JSON

- O W5-R06 parou no check sem escrita. A comparação independente do
  coordenador provou que os cinco asserts de quote continham barras invertidas
  literais (`\\u00e9`, por exemplo), enquanto o gold tem os caracteres UTF-8.
  Não era divergência editorial nem alteração do episódio.
- O W5-R07 substitui a redação manual de quotes por gerador job-local que lê o
  estado atual de `calibration_tests.json`, verifica igualdade e hexadecimal
  UTF-8, e só então entrega o manifesto ao patcher. Ele permanece o segundo e
  último apply pré-packet; qualquer falha encerra o ramo sem nova escrita.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Wave 005: decisão necessária sobre equivalência de calibração

- O W5-R07 aplicou o segundo patch uma única vez após extrair os asserts
  diretamente do JSON atual. A cobertura chegou a 6/24, sem target duplicado;
  o patch alterou somente `calibration_tests.json` e o caveat de `G031`.
- O autocheck estrito bloqueou três equivalências: dois redirects para `G004`
  e um para `G042` têm evidência física, mas os claims editoriais não enunciam
  precisamente a proposição calibrada. O coordenador confirmou as três
  ocorrências em leitura independente.
- O limite de duas rodadas corretivas foi atingido. A Wave fica em
  `awaiting_owner_decision`; nenhum readiness, build, validator ou packet será
  produzido até que o owner escolha a próxima política de correção.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-14 — Wave 005: owner autorizou alinhamento semântico mínimo

- O owner escolheu a Opção A: uma terceira e última correção, limitada a
  `source_claim` de `G004` e `G042`. Ela não altera targets de calibração,
  evidências, números, relações ou outros candidatos.
- O plano W5-R08 registra os dois textos editoriais, o `patch_window`
  `owner_authorized_semantic_alignment`, um único check/apply e os gates que só
  podem rodar se esse patch passar.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-14 — Wave 005: janela de patch exige nova decisão

- O W5-R08 não escreveu no gold: o patcher rejeitou
  `owner_authorized_semantic_alignment`, pois seu contrato aceita apenas
  `pre_packet` ou `post_packet`.
- `pre_packet` já atingiu o limite; usar `post_packet` sem packet existente
  registraria provenance falsa. Uma exceção honesta requer extensão compatível
  do contrato e testes, o que excede a autorização editorial da Opção A.
- O episódio está `awaiting_owner_decision`; nenhum apply, readiness, build,
  validador ou export ocorreu.

### 2026-07-13 — W4-R23 corrige premissa do ledger antes de escrever

- O worker registrou a reauditoria de v6lu como `changes_requested/open=2`,
  compilou o helper e parou antes de qualquer patch ao detectar que 1698–1701
  não são decisões manuais em `manual_reviews`.
- A revisão do coordenador confirmou os quatro registros como
  `excluded/low_signal` no ledger derivado. Pelo contrato do builder, inserir
  1697–1702 em G041 gera automaticamente as entradas `captured` pertinentes;
  criar decisões manuais seria redundante.
- W4-R24 usa essa rota canônica: não registra a auditoria de novo e não altera
  `ledger_decisions`; atualiza somente G014, G024 e evidência de G041, então
  confirma o ledger derivado após build.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Wave 004: rota de inserção segura W4-R04

- O evento `MSF-R20-WAVE-004-004` confirmou o registro do envelope como
  `changes_requested/open_findings=4`. O recorder abortou atomicamente a
  remediação; nenhum candidato ou review foi parcialmente escrito.
- A inspeção independente mostrou que `G034↔G035` já é uma relação válida e
  simétrica. O erro de dangling era efeito da semântica de substituição do
  recorder: o payload continha apenas o novo G053 no chunk 015 e, portanto,
  removeria o G035 existente. O mesmo padrão descartaria candidatos atuais dos
  chunks 003, 007 e 020.
- O coordenador rejeitou a remoção da relação e definiu uma rota materialmente
  diferente: `gold_review_patch` fará apenas inserts G051–G054, com assertions
  completas de chunk/hash/IDs, `--check` sem escrita e um único `--apply`.
  G054 deve usar editorial ASCII e `role=other`; todos os candidatos anteriores
  e G034/G035 precisam permanecer inalterados.
- Depois do patch, yyo volta aos gates e o worker retoma 8WE no chunk 003 e
  v6lu. Nenhum commit, push, deploy, consolidação gold ou Supabase foi
  executado.

### 2026-07-13 — Wave 004: reauditoria yyo aprovada e retomada W4-R05

- O evento `MSF-R20-WAVE-004-005` entregou yyo com 54 candidatos após inserção
  transacional check/apply, sem alterar G034/G035 ou os candidatos anteriores.
  Readiness, build e validador normal passaram; o packet tem cinco arquivos.
- O coordenador reauditou somente o novo packet cego. G051–G054 resolvem os
  quatro findings: captura de valor, mudança de diferencial, span gerencial e
  script com IA. Ledger, evidências, 25 números, relações e 16 calibrações foram
  conferidos; não há target duplicado nem finding aberto.
- `yyoGeQp5yzM_reaudit_001.json` foi selado `passed/open_findings=0` e o
  validador do contrato retornou zero erros. O validador normal independente do
  gold também passou e os fingerprints protegidos permanecem iguais.
- W4-R05 registrará a reauditoria e derivará yyo para complete sem edição
  editorial; depois concluirá 8WE desde o chunk 003 e v6lu desde o chunk 001.
  Packets parciais continuam proibidos.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Wave 004: yyo aprovado e retomada W4-R06

- O evento `MSF-R20-WAVE-004-006` derivou yyo para `complete/passed` e avançou
  8WE até o chunk 004, sem packet parcial. v6lu permaneceu preparado.
- O coordenador reproduziu `validate_gold_extraction --require-external-audit`
  em yyo: pass, zero erros. O episódio tem 54 IDs únicos, zero finding aberto,
  cinco arquivos no packet e fingerprints protegidos iguais. O runner o marca
  `protected_complete_read_only`; o quality gate de yyo está aprovado.
- 8WE possui quatro reviews integrais com hashes e 14 IDs únicos. Não há chunk
  stale ou inconsistente; a fronteira segura é 005. v6lu continua com 31 chunks
  pendentes desde o 001.
- W4-R06 remove yyo do ownership de escrita da continuação e limita o worker a
  concluir 8WE 005–014 e v6lu 001–031, com recall/autocheck/gates e packets
  integrais.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Wave 004: 8WE retomável no chunk 007

- O evento `MSF-R20-WAVE-004-007` preservou yyo e avançou 8WE pelos chunks
  005–006, sem readiness, build ou packet parcial. v6lu não foi iniciado.
- O coordenador confirmou seis reviews integrais com hashes, 20 IDs únicos e
  zero duplicidade. O runner não encontrou stale/inconsistência e lista
  007–014 como pendentes; yyo continua protegido complete/passed.
- W4-R07 preserva 001–006, conclui 8WE e seus gates e só então abre v6lu no
  chunk 001. O checkpoint representa progresso material; o contador de retorno
  sem progresso permanece zero.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Wave 004: faixa final de 8WE liberada

- O evento `MSF-R20-WAVE-004-008` concluiu reviews 007–008 e manteve yyo
  protegido; v6lu não foi aberto antes da ordem autorizada.
- O coordenador confirmou oito reviews completos com hashes, 25 IDs únicos,
  zero duplicidade e runner sem stale/inconsistência. Restam somente 009–014.
- W4-R08 preserva 001–008 e executa a faixa final, recall/autocheck e gates de
  8WE. v6lu só começa depois do packet integral. O retorno traz progresso
  material; `no_progress_returns` permanece zero.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Wave 004: fechamento de 8WE isolado em W4-R09

- O evento `MSF-R20-WAVE-004-009` concluiu reviews 009–010. O coordenador
  confirmou dez reviews com hashes, 33 IDs únicos e nenhum chunk inconsistente;
  restam 011–014.
- Para reduzir troca de contexto e concluir um gate de cada vez, W4-R09 fica
  restrito ao fechamento de 8WE, seu recall/autocheck/gates e packet integral.
  v6lu permanece preparado e será aberto somente depois da auditoria de 8WE.
- O retorno mantém progresso material e `no_progress_returns=0`. Yyo segue
  protegido complete/passed.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Wave 004: último chunk de 8WE liberado

- O evento `MSF-R20-WAVE-004-010` concluiu reviews 011–013. O coordenador
  confirmou 13 reviews com hashes, 39 IDs únicos e somente o chunk 014
  pendente, sem stale ou inconsistência.
- W4-R10 preserva 001–013, revisa o último chunk e executa recall/autocheck,
  readiness, build, validador e packet integral. Yyo e v6lu ficam read-only.
- O retorno representa progresso material; `no_progress_returns=0`.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Wave 004: auditoria cega inicial de 8WE

- O evento `MSF-R20-WAVE-004-011` entregou `8WEvN5T7J0U` com 14 reviews,
  40 candidatos únicos, readiness pronto, build sem erros, validador normal
  aprovado e packet cego com cinco arquivos.
- Antes de ler artefatos internos do worker, o coordenador auditou somente
  manifest, transcript, insights, ledger e calibrações. O julgamento foi selado
  em `.codex-work/msf-r20-coordinator-audits/8WEvN5T7J0U_audit.json` como
  `changes_requested`, com dez findings abertos.
- O packet passou integridade e evidência verbatim, mas não o quality gate por
  duplicata editorial, três lacunas de recall, números incompletos, relações
  ausentes, dupla contagem semântica de calibração e grafias locais.
- O coordenador reproduziu `validate_gold_extraction` normal com `pass` e
  confirmou quatro fingerprints protegidos iguais antes/depois. W4-R11 limita a
  próxima rodada à remediação dos findings e rederivação do packet de 8WE;
  `yyoGeQp5yzM` e `v6luZ9KvmOI` permanecem read-only.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Wave 004: remediação de 8WE bloqueada só na calibração

- O evento `MSF-R20-WAVE-004-012` registrou o audit selado e aplicou um patch
  transacional único. O coordenador confirmou 42 candidatos únicos, remoção de
  G001, três novos candidatos de recall, números corrigidos, relações simétricas,
  validador normal aprovado, packet com cinco arquivos e fingerprints 4/4.
- O único bloqueio residual é `MSF-R20-8WE-009`: os targets 0001, 0003, 0012 e
  0568 continuam `fail`, sem deduplicação/redirecionamento para G040, G033 e
  G029. Não será aceita a cobertura mínima como substituto da correção.
- W4-R12 é uma story estreita e a segunda rodada corretiva: altera somente o
  arquivo-fonte de calibração com helper job-local, check read-only e apply
  único, seguido de uma readiness, um build, validador e export.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Wave 004: contorno do timeout de aplicação W4-R12

- O evento `MSF-R20-WAVE-004-013` informou que o helper compilou e passou em
  `--check`, mas o `--apply` via `.venv` ficou 30 minutos sem saída e foi
  interrompido. Hash, mtime, candidates, ledger e audit permaneceram iguais;
  nenhuma escrita ou receipt ocorreu.
- Conforme a regra de ação indivisível travada, o coordenador não repetirá esse
  comando. O `--check` foi reproduzido com o Python global em 1,9 segundo e
  confirmou dez targets e o hash final esperado
  `77E7F5DCF92A54381F7A18C62422536BAE0D458DE977D2C36E195D6BBA45E1B3`.
- W4-R13 autoriza uma única aplicação pelo runtime global, com preflight de
  acesso exclusivo e limite de dois minutos. Falha ou timeout encerra a story
  sem fallback de escrita no mesmo turno.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Wave 004: divergência de hash de W4-R13 é apenas CRLF

- O evento `MSF-R20-WAVE-004-014` informou apply global concluído em 6,3
  segundos, receipt com dez targets e parada segura antes dos gates porque o
  hash físico diferiu do hash LF esperado.
- A verificação independente do coordenador confirmou JSON parseável, dez
  testes, 252 quebras CRLF e nenhuma LF isolada. Normalizar somente as quebras
  para LF produz exatamente
  `77E7F5DCF92A54381F7A18C62422536BAE0D458DE977D2C36E195D6BBA45E1B3`, o
  hash declarado pelo helper/receipt. O hash físico CRLF é
  `EA3144419DE9A2B2A475D2F772BA69B96FBB357DEA57B67B97240AD4101FDB74`.
- O objeto removeu os targets independentes 0001/0003/0012/0568 e preservou a
  provenance em 0799/0611/0540. Portanto não será feita restauração, segunda
  aplicação ou normalização externa; W4-R14 executará somente readiness, build,
  validador normal e packet para reauditoria.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Wave 004: reauditoria de 8WE aprovada

- O evento `MSF-R20-WAVE-004-015` concluiu readiness, build, validador normal e
  packet depois da correção semântica das calibrações. O coordenador auditou
  somente manifest, transcript, insights, ledger e calibration_tests.
- O packet tem 42 IDs únicos, evidências verbatim válidas, ledger com 315 sinais
  captured e 283 excluded, 48 registros numéricos, três hierarquias simétricas
  e acíclicas e dez calibrações distintas; 6 passam para mínimo 3, sem target
  duplicado. O validador normal independente retornou `pass/errors=[]`.
- Os dez findings anteriores foram confirmados como resolvidos. A reauditoria
  foi selada em `8WEvN5T7J0U_reaudit_001.json` como `passed/open_findings=0` e
  seu contrato oficial passou para revisor e executor separados.
- Depois do julgamento, o coordenador confirmou quatro fingerprints protegidos
  idênticos antes/depois. W4-R15 registrará o audit e derivará `complete` sem
  editar o conteúdo gold; v6lu permanece preparado e read-only.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Wave 004: 8WE aprovado e v6lu liberado

- O evento `MSF-R20-WAVE-004-016` registrou a reauditoria aprovada e derivou
  8WE para `complete/passed/open=0`, sem edição editorial.
- O coordenador confirmou o resultado no chat do worker e reproduziu o
  validador com `--require-external-audit`: `pass/errors=[]`. O relatório
  derivado preserva integralmente metadata e dez findings resolvidos do audit
  selado; revisor e executor são separados.
- 8WE tem 42 IDs únicos, dez calibrações distintas, seis cobertas para mínimo
  três, packet com cinco arquivos e fingerprints protegidos 4/4 iguais.
  Quality gate: aprovado.
- O runner Fast Path agora protege yyo e 8WE. v6lu é o único episódio pendente,
  preparado com 31 chunks, zero stale e zero inconsistência. W4-R16 executará
  sua revisão integral, recall/autocheck, gates e packet cego.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Wave 004: v6lu retomado em lotes compactos

- O evento `MSF-R20-WAVE-004-017` passou o preflight de v6lu e persistiu os
  reviews 001–002, ambos completos, source-backed e com hashes. Há três IDs
  únicos; nenhum gate, audit ou packet foi executado.
- O coordenador confirmou o checkpoint e o runner: 003–031 pendentes, zero
  stale e zero inconsistente. Yyo e 8WE continuam protegidos.
- Como a tentativa de concluir 31 chunks num único turno encerrou na fronteira
  002, W4-R17 reduz overhead com dois batches atômicos: 003–006 e 007–010,
  usando work orders compactos e narração mínima. Isso é continuação do mesmo
  épico, não um novo episódio nem uma redução de cobertura.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Wave 004: v6lu íntegro até o chunk 010

- O evento `MSF-R20-WAVE-004-018` concluiu 003–010 em dois batches atômicos.
  O coordenador confirmou dez reviews completos com hashes, 16 IDs únicos e o
  chunk 005 como zero-insight válido.
- O runner lista 011–031 pendentes, zero stale e zero inconsistente. Nenhum
  readiness, build, validador, audit ou packet foi executado.
- W4-R18 repete o padrão eficiente para 011–014 e 015–018. Reviews 001–010,
  yyo e 8WE permanecem imutáveis.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Wave 004: v6lu íntegro até o chunk 018

- O evento `MSF-R20-WAVE-004-019` concluiu 011–018 em dois batches atômicos.
  O coordenador confirmou 18 reviews completos com hashes e 26 IDs únicos.
- Chunks 005 e 018 são zero-insight. O final de 018 contém uma proposição
  parcial preservada para leitura com 019; não será descartada nem transformada
  isoladamente em insight.
- O runner lista 019–031 pendentes, zero stale e zero inconsistente. W4-R19
  revisará 019–026 e fechará explicitamente a fronteira 018/019.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Wave 004: correção fechada do payload G027

- O evento `MSF-R20-WAVE-004-020` foi bloqueado pelo recorder antes da escrita
  do Batch A: `content_strategy` não é tema canônico e `uma live por semana`
  não aparece literalmente na evidência mínima. Batch B não foi iniciado.
- O coordenador confirmou zero review 019–022 persistido e definiu a correção
  exata: tema `creative_strategy` e raw `pelo menos uma live na semana`, forma
  presente nos segmentos 1040 e 1091. Nenhum outro campo pode mudar.
- W4-R20 reaplica Batch A atomicamente uma vez; somente após sucesso conclui
  023–026. Isso é progresso diagnóstico, portanto `no_progress_returns=0`.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Wave 004: v6lu liberado para fechamento e packet

- O evento `MSF-R20-WAVE-004-021` aplicou somente os dois deltas autorizados em
  G027 e persistiu 019–026 em dois batches atômicos. O coordenador confirmou
  26 reviews completos, 35 IDs únicos e G027 source-backed por 1040/1091.
- O runner lista apenas 027–031 pendentes, sem stale/inconsistência. O snapshot
  `protected_fingerprints.json` existe no data root e mostra 4/4 iguais.
- W4-R21 conclui os cinco reviews, recall/autocheck global, reparos limitados a
  inventários fechados, readiness, build, validador normal e packet cego.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Wave 004: auditoria cega de v6lu solicita mudanças

- O evento `MSF-R20-WAVE-004-022` entregou v6lu com 31 reviews, 39 IDs únicos,
  readiness/build/validador normal aprovados, packet de cinco arquivos e
  fingerprints protegidos 4/4 iguais.
- Antes de ler reviews, autocheck, status ou relatório interno, o coordenador
  auditou exclusivamente manifest, transcript, insights, ledger e calibrações.
  O parecer foi selado em `v6luZ9KvmOI_audit.json` como
  `changes_requested/open_findings=6`; o contrato oficial retornou zero erros.
- Os findings cobrem: normalização de quase R$ 300 mil registrada como R$ 300;
  valores materiais omitidos; bloco econômico 0835–0853 excluído como
  `low_signal`; continuações substantivas 1275–1721 descartadas; duas
  calibrações contadas sem a mesma proposição; e relações ausentes no cluster
  de webinar.
- Depois do selo, o coordenador reproduziu o validador normal
  (`pass/errors=[]`) e recalculou os quatro hashes protegidos, todos iguais ao
  snapshot. W4-R22 aplicará somente esse inventário e devolverá novo packet
  ainda pendente de reauditoria.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Wave 004 pausada para otimização ponta a ponta

- O evento `MSF-R20-WAVE-004-023` registrou a auditoria `changes_requested` de
  v6lu, aplicou um patch transacional para os seis findings e entregou novo
  packet com 41 IDs, readiness/build/validador normal aprovados e fingerprints
  protegidos 4/4 iguais. O episódio continua `awaiting_external_audit`.
- O owner interrompeu a reauditoria para corrigir a lentidão observada. A
  comparação confirmou que a Wave 004 tem 66 chunks e 3.652 segmentos limpos,
  contra 24 chunks e 1.284 segmentos na Wave 003; a métrica anterior de
  66%–69% media bytes de work orders, não custo ponta a ponta.
- Foi criado `MSF-R20-GOLD-FASTPATH-002` para implementar orçamento por carga,
  faixas contínuas de 8–12 chunks, pré-auditoria semântica, até dois patches
  pré-packet, patch genérico de calibração, `audit --check`, hashes semânticos e
  métricas reais. Todos os dados reais ficam somente leitura.
- A reauditoria atual de v6lu será retomada do packet já entregue depois do
  quality gate do Fast Path 002; W4-R22 não será repetido.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Fast Path 002 solicita primeira correção

- O evento `MSF-R20-GOLD-FASTPATH-002-001` foi confirmado no chat do worker. O
  diff ficou no ownership e os dados reais permaneceram read-only.
- O coordenador reproduziu 50 testes, compilação dos seis módulos, diff check e
  os runners read-only das Waves 003/004. Os seis status hashes permaneceram
  iguais.
- Testes adversariais encontraram quatro falhas: retomada pequena conta todo o
  raw e bloqueia; chunk stale recebe carga/faixa zero; calibração para candidato
  inexistente é aceita; e findings semânticos novos não entram no gate estrito.
  O autocheck também usa sobreposição lexical fraca, não avalia o ledger
  automático e confunde suporte misto com suporte exclusivo de entrevistador.
- FP2-001 a FP2-004 foram registrados no plano. A correção 1/2 fica limitada a
  carga ativa real, receipt semântico obrigatório, validação final de
  calibração e métricas idempotentes/honestas.
- A Wave 004 continua pausada. Nenhum commit, push, deploy, consolidação gold ou
  Supabase foi executado.

### 2026-07-13 — Fast Path 002 solicita correção final do autocheck

- O evento `MSF-R20-GOLD-FASTPATH-002-002` foi confirmado no chat inativo do
  worker. O coordenador reproduziu 55 testes, compilação, diff check e os
  runners read-only das Waves 003/004; os seis hashes de status ficaram iguais.
- FP2-001, FP2-003 e FP2-004 passaram a validação direcionada. Contudo, o
  autocheck ainda consulta IDs em campos de draft ausentes do candidato
  persistido, em vez de usar `evidence.minimal_quote` e
  `evidence.support_segments`. Em v6lu isso gerou 1.166 falsos previews de
  ledger e 1.967 itens semânticos a resolver.
- A correção 2/2 limita-se a essa resolução de IDs e a três regressões: destino
  válido não pode virar falso positivo, captured deve reconhecer sua evidência
  e sinal realmente não coberto deve continuar bloqueando. Dados reais e Wave
  004 continuam somente leitura até o gate final.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Fast Path 002 aguarda decisão sobre exclusões legítimas

- O evento `MSF-R20-GOLD-FASTPATH-002-003` foi confirmado no chat inativo do
  worker. O coordenador reproduziu 56 testes, compilação e diff check; as três
  regressões de evidência persistida passam.
- A leitura real de v6lu reduziu os falsos previews de 1.166 para 779, mas os
  779 restantes correspondem exatamente ao ledger final
  `excluded/low_signal`. Como o autocheck ainda os publica em
  `automatic_ledger_preview`, há 1.580 `review_required`, inviabilizando o
  receipt como mecanismo econômico.
- O limite de duas correções foi alcançado. A fila está em
  `awaiting_owner_decision`: autorizar FP2-002c para reconhecer exclusões
  válidas (recomendado), aceitar o receipt manual oneroso ou encerrar o Fast
  Path e retomar o fluxo anterior.
- A reauditoria de v6lu permanece pausada. Nenhum commit, push, deploy,
  consolidação gold ou Supabase foi executado.

### 2026-07-13 — Owner autoriza FP2-002c

- O owner escolheu a Opção A: uma terceira e última correção é autorizada para
  que `excluded` com razão válida encerre a prévia de ledger sem mascarar
  `captured/merged` sem evidência ou segmentos sem decisão.
- O job fica limitado ao autocheck e testes: sem receipt, `--execute`, escrita
  em dados reais, export, auditoria, fingerprint, commit, push, deploy,
  consolidação gold ou Supabase.
- A Wave 004 permanece pausada até o quality gate final do Fast Path 002.

### 2026-07-13 — Fast Path 002 aprovado e Wave 004 liberada

- O worker concluiu FP2-002c, mas o pytest do job encontrou `PermissionError`
  no basetemp e não enviou o evento final esperado. Após pedido de status do
  owner, o coordenador confirmou o chat inativo e processou a entrega sem
  duplicar a escrita.
- Em temp materialmente diferente, o coordenador reproduziu 59 testes,
  `py_compile` e `git diff --check`. O autocheck real de v6lu retornou zero
  preview de ledger, zero high-signal sem destino e zero erro de alinhamento;
  os 779 `excluded/low_signal` deixaram de inflar o receipt.
- Os runners das Waves 003/004 foram executados em leitura pura; seis hashes de
  status permaneceram iguais. Os quatro fingerprints atuais de v6lu também
  conferem com o snapshot.
- Fast Path 002 recebeu gate `approved`. A reauditoria cega do packet remediado
  de v6lu está liberada. Nenhum commit, push, deploy, consolidação gold ou
  Supabase foi executado.

### 2026-07-13 — Reauditoria de v6lu solicita dois ajustes residuais

- O coordenador reavaliou somente os cinco arquivos cegos do packet atualizado
  de `v6luZ9KvmOI`. Integridade, quotes, ledger, relações e calibração passaram
  nas verificações determinísticas.
- A reauditoria foi selada como `changes_requested/open_findings=2`: G014 usa
  unidade `leads` para `150 a 200 alunos`; G024 usa role `other` para conversão
  de `10 a 15%`; e G041 não cita 1697–1702 na evidência mínima da afirmação de
  quase prejuízo.
- W4-R23 fica limitado a esses três campos semânticos e à destinação de ledger
  correspondente, seguido pelo Fast Path, build único e validador normal. Yyo e
  8WE permanecem protegidos.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Esteira de aprendizado contínuo incorporada

- O owner aprovou adaptar as práticas observadas no `CLAUDE.md` de referência
  para o protocolo Codex do Marketing Swipe File.
- Foi criado `docs/coordination/process-learnings.md`: primeira ocorrência fica
  local, segunda entra no registro e terceira exige prevenção ou rota diferente.
  Risco crítico ou possibilidade de corrupção pode ser promovido imediatamente.
- Falhas determinísticas passam a preferir script, guard ou teste; regras gerais
  ficam na coordenação e somente heurísticas gold comprovadas entram na skill.
- O worker ganhou o campo opcional `process_learnings`, mas continua sem
  autoridade para editar AGENTS, fila, execution log ou o registro central.
- Respostas de fechamento agora separam estado, pendência real do owner, próximo
  passo autônomo e bloqueios. `SESSÃO FINALIZADA` exige fila/checkpoint
  sincronizados e ausência de job ativo.
- Validações: fila JSON parseável com IDs únicos, skill válida e concisa,
  Markdown balanceado e `git diff --check` aprovado. Nenhum dado gold, packet,
  audit, export, script do pipeline, commit, push, deploy, consolidação ou
  Supabase foi alterado.

### 2026-07-13 — Wave 005 planejada com cinco episódios

- O owner pediu ampliar o próximo épico para cinco episódios padrão-ouro.
- Foram selecionados os cinco primeiros episódios elegíveis por prioridade:
  `zoChfFHnlOQ`, `JF2oC44lBG8`, `qohJceyapS0`, `wHdyTM-nVqg` e
  `BbhJn8NXRso`. Todos têm raw, transcrição disponível e nenhum gold existente.
- A carga é 8.716 segmentos e 158 chunks estimados. O manifesto declara
  orçamento 9.000/160/5 e faixas de revisão de 10 chunks.
- O plano autoriza execução sequencial, uma correção pré-packet limitada por
  episódio, um evento final consolidado e isolamento de bloqueios.
- O runner Fast Path em leitura pura confirmou cinco rotas `new_raw_episode`,
  preflight pass, 17 faixas e carga dentro do orçamento, sem qualquer escrita.
- A wave está `queued` e ainda não foi delegada. Nenhum dado, packet, audit,
  export, commit, push, deploy, consolidação ou Supabase foi alterado.

### 2026-07-13 — Wave 005 delegada

- O owner autorizou o início da Wave 005 depois da criação e validação do plano.
- O EXECUTION BRIEF foi publicado e a delegação foi enviada ao worker
  `Extração Padrão-Ouro` com `gpt-5.6-terra/high`.
- O coordenador não fará polling, monitoramento ou análise paralela. Ele retoma
  somente após receber o WORKER_EVENT final consolidado ou nova instrução do
  owner.

### 2026-07-13 — Wave 005: evento final recuperado e entrega endurecida

- Após aviso do owner, uma leitura única do chat inativo do worker confirmou
  `MSF-R20-WAVE-005-001` como `blocked`: preflight e preparação Fast Path dos
  cinco episódios passaram, mas nenhum review, packet, build ou auditoria foi
  persistido antes da primeira fronteira atômica. Não houve perda nem escrita
  editorial parcial.
- A mesma falha de transporte já havia ocorrido no Fast Path 002. Por ser a
  segunda ocorrência confirmada, `MSF-PL-005` foi promovido: o worker deve usar
  `send_message_to_thread` para o coordenador e registrar o recibo; publicar
  apenas no próprio chat não conta como entrega.
- O pedido do owner para iniciar uma nova wave passa a autorizar planejamento e
  delegação automaticamente, salvo pedido explícito de somente planejar ou gate
  material de decisão. A Wave 005 retoma em `zoChfFHnlOQ` 001–010, sem repetir
  a preparação e sem packet parcial.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Wave 005: primeiro batch semântico aprovado

- O `MSF-R20-WAVE-005-002` chegou pelo novo canal inter-chat. `zoChfFHnlOQ`
  persistiu a faixa 001–010 em batch atômico: dez reviews completos, 17 IDs
  únicos e input hashes presentes. A tentativa inicial do recorder foi rejeitada
  antes de qualquer escrita por literal numérico ausente; o payload foi
  corrigido e a segunda tentativa persistiu sem duplicar dados.
- O coordenador confirmou estruturalmente os dez reviews e executou o runner em
  leitura pura: 011–039 são os únicos chunks pendentes; `stale=[]` e
  `inconsistent=[]`. O lifecycle permanece `awaiting_semantic_review`.
- A entrega inter-chat com evento 002 valida a prevenção `MSF-PL-005`. A
  continuação retoma somente `zoChfFHnlOQ` 011–020.
- Nenhum packet, auditoria, commit, push, deploy, consolidação gold ou Supabase
  foi executado.

### 2026-07-13 — Wave 005: segunda faixa semântica aprovada

- O evento inter-chat `MSF-R20-WAVE-005-003` entregou `zoChfFHnlOQ` 011–020.
  O coordenador confirmou 20 reviews completos com input hash, 25 IDs únicos e
  nenhuma duplicata ou problema estrutural.
- O runner em leitura pura mostra somente 021–039 pendentes, zero stale e zero
  inconsistente; a carga ativa caiu para 7.417 segmentos e 132 chunks. O
  lifecycle continua `awaiting_semantic_review` e ainda não existe packet.
- A próxima continuidade fecha 021–039 e somente então permite recall,
  autocheck, readiness, build, validador normal e export cego desse episódio.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Wave 005: autocheck bloqueia inflação técnica antes do packet

- O evento `MSF-R20-WAVE-005-004` concluiu `zoChfFHnlOQ`: 39 reviews completos,
  48 IDs únicos, zero pending/stale/inconsistent e fingerprints protegidos
  iguais. Nenhum readiness, build, validador, export ou packet foi executado.
- A reprodução independente do autocheck confirmou 20 alertas numéricos,
  calibração 1/24, um claim sem suporte lexical e 3.009 pendências high-signal.
  A inspeção mostrou que estas últimas são inflação técnica: antes do build, a
  prévia consulta apenas decisões manuais, embora `ledger_for_signals()` já
  possa derivar `captured` e exclusões válidas em memória.
- Foi aberto `MSF-R20-GOLD-FASTPATH-003`, limitado a autocheck e testes, para
  corrigir essa diferença sem escrever dados reais. A Wave 005 fica bloqueada
  até o diagnóstico residual ser honesto e finito.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Fast Path 003 aprovado; overlap genérico ainda é ruído

- O worker corrigiu o autocheck para derivar `ledger_for_signals()` em memória
  antes do build, mantendo ledger persistido final como precedência. O
  coordenador revisou a mudança e reproduziu 48 testes em temp fora do OneDrive,
  compilação em memória e `git diff --check`.
- No diagnóstico read-only de `zoChfFHnlOQ`, `automatic_ledger_preview` e
  `high_signals_without_direct_destination` caíram de 3.009 para zero;
  `review_required` caiu de 3.063 para 54. O hash de status gold permaneceu
  `C509B1FBCD9028641B74A55E69646D8FCB73E66DB0F6741E20E0AF9236D9C02A`.
- Dos 54 itens, 53 são overlaps lexicais por palavras genéricas. Foi aberto
  `MSF-R20-GOLD-FASTPATH-004`, limitado a essa heurística e testes; números,
  calibração e claim residual não serão ocultados.
- Nenhum dado gold, packet, audit, commit, push, deploy, consolidação ou
  Supabase foi alterado no Fast Path 003.

### 2026-07-13 — Fast Path 004 aprovado e remediação finita da Wave 005 liberada

- O evento direto `MSF-R20-GOLD-FASTPATH-004-001` entregou a heurística que
  ignora palavras genéricas e só suprime overlap mediante relação parent/child
  simétrica. O coordenador reproduziu 51 testes (`test_gold_fastpath` e
  `test_gold_pipeline`) em temp fora do OneDrive, compilação em memória e
  `git diff --check`.
- O autocheck read-only de `zoChfFHnlOQ` preservou o status hash
  `C509B1FBCD9028641B74A55E69646D8FCB73E66DB0F6741E20E0AF9236D9C02A`;
  `automatic_ledger_preview` e gaps high-signal são zero e os overlaps caíram
  de 53 para um. Os diagnósticos verdadeiros permanecem visíveis: 20 números,
  `G037`, `G030/G034` e calibração 1/24.
- Foi planejada e delegada a story W5-R05, limitada a esse inventário, até dois
  patches atômicos e um único ciclo de readiness/build/validador/export. Os
  demais quatro episódios permanecem sem escrita. Depois da delegação, o
  coordenador não acompanha o worker até receber o evento final direto.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-13 — Simplificação estrutural das fases finais gold autorizada

- O owner determinou que o coordenador deve delegar o épico e auditar somente
  depois de o worker concluir o episódio ou o conjunto de episódios, sem
  revisões intermediárias de readiness, patch, calibração ou packet provisório.
- Foi criado `MSF-R20-GOLD-PIPELINE-SIMPLIFICATION-001`. O fluxo alvo separa
  `hard_blockers` de `audit_warnings`, substitui janelas/contagem de patches por
  revisões completas do episódio, deriva ledger/calibração dos candidatos finais
  e gera um único packet por revisão pronta.
- Permanecem rígidos: fonte original, suporte literal de quote/número, schema e
  relações válidas, escrita atômica/rollback, fingerprints protegidos e
  auditoria independente com zero findings para `complete/passed`.

### 2026-07-13 — Quality gate 1 da simplificação gold

- O worker entregou `MSF-R20-GOLD-PIPELINE-SIMPLIFICATION-001-001`. O
  coordenador reproduziu `56 passed`, validou a skill e aprovou
  `git diff --check`; nenhuma falha de teste funcional foi encontrada.
- O quality gate de contrato abriu quatro findings: recibo idempotente sem hash
  das entradas/packet, exportação não transacional, quote de calibração não
  validado contra o transcript e heurística lexical de claim classificada como
  bloqueio em vez de warning editorial.
- Provas isoladas em temp confirmaram: review alterada reutiliza packet obsoleto,
  falha na segunda cópia deixa packet parcial e quote de calibração fabricado
  chega ao export. Nenhum dado real da Wave 005 foi escrito.
- Foi autorizada uma única rodada corretiva consolidada, agora com ownership
  explícito de `scripts/export_gold_audit_packet.py`. A Wave 005 permanece
  pausada até o segundo quality gate.

### 2026-07-13 — Quality gate 2 da simplificação gold

- O worker entregou o evento `002` e o coordenador reproduziu `64 passed`.
  Mudança semântica real agora conflita, packet parcial sofre rollback, quote de
  calibração fabricado bloqueia e heurística lexical tornou-se warning.
- Um probe adicional regravou uma review semanticamente idêntica apenas com
  CRLF. O finalizador retornou `conflict` porque compara o objeto de assinatura
  inteiro, incluindo hashes físicos, apesar de já calcular o hash semântico.
- Foi aberta a segunda e última rodada corretiva, restrita a `PS-QG-005`:
  idempotência das entradas usa somente a assinatura semântica; hashes físicos
  do packet continuam obrigatórios. Wave 005 e demais dados reais continuam
  somente leitura.

### 2026-07-13 — Pipeline simplificado aprovado e Wave 005 liberada

- O evento `MSF-R20-GOLD-PIPELINE-SIMPLIFICATION-001-003` resolveu PS-QG-005.
  O coordenador reproduziu `65 passed` e confirmou que LF/CRLF é idempotente,
  enquanto mudança semântica real continua em conflito.
- Probes confirmaram rollback sem packet parcial, bloqueio de quote de
  calibração fabricado e warnings editoriais não bloqueantes. Compilação, skill,
  diff e prova read-only das Waves 003/004/005 passaram.
- O job de simplificação foi aprovado. A Wave 005 foi liberada numa única
  execução: o worker revisa/finaliza os cinco episódios e o coordenador só
  retorna após o evento final para fazer as auditorias cegas.
- A Wave 005 foi pausada como dependência, sem desfazer os 39 reviews, 48
  candidatos ou patches válidos já persistidos em `zoChfFHnlOQ`. O manifesto
  incompatível do evento 008 não escreveu e não será contornado com provenance
  falsa.
- Este job de tooling mantém toda a Wave 005, exports, audits e dados protegidos
  em leitura pura. Nenhum commit, push, deploy, consolidação ou Supabase foi
  autorizado.

### 2026-07-13 — Wave 005: primeiro packet auditado e continuidade por episódio

- O evento `MSF-R20-WAVE-005-009` finalizou `zoChfFHnlOQ` sem blocker técnico:
  39 reviews, 48 candidatos, readiness/build/validação normal aprovados e um
  packet cego exato de cinco arquivos. `JF2oC44lBG8` chegou em checkpoint
  durável com reviews 001–018/24 e 19 IDs; os outros três episódios não foram
  alterados.
- O coordenador auditou o packet de zo independentemente: JSON parseável e
  consistente, 48 IDs únicos, referências/quotes verbatim válidos, relação
  G030→G034 simétrica, 24 targets de calibração distintos e validador
  determinístico aprovado. Os sete avisos no packet foram verificados como
  contexto editorial, não findings. O parecer selado é
  `.codex-work/msf-r20-coordinator-audits/zoChfFHnlOQ_audit_001.json`, com
  `passed` e `open_findings=0`.
- A continuidade foi reduzida para a fronteira de um episódio completo: o
  worker primeiro registra deterministicamente o audit de zo e conclui apenas
  JF (019–024, recall e packet). Não há revisão intermediária do coordenador;
  a próxima auditoria ocorrerá apenas após o packet integral de JF.
- Nenhum commit, push, deploy, consolidação gold ou Supabase foi executado.

### 2026-07-14 — Wave como unidade única de execução e auditoria

- O owner confirmou que a Wave 005 ainda estava lenta e retornava ao
  coordenador em batches e episódios, apesar do contrato de simplificação. A
  análise identificou duas causas: validação fail-fast acoplada ao recorder e
  ausência de um receipt que exigisse os cinco episódios antes da entrega.
- O worker recebeu uma pausa segura durante W5-R15. O evento
  `MSF-R20-WAVE-005-015` confirmou qoh 001–010 preservado, 011–020 ausente, dez
  candidatos únicos, nenhum packet/export parcial e nenhum blocker de dados.
- O protocolo agora define a wave multi-episódio como unidade de delegação,
  entrega e auditoria. Erros mecânicos ou source-backed são resolvidos dentro do
  worker; checkpoints ficam no próprio chat; o coordenador não audita episódios
  isolados e só retoma depois do gate consolidado 5/5.
- Foi criado `MSF-R20-GOLD-WAVE-ONE-SHOT-001` para implementar compilador
  read-only com normalização segura e inventário completo, recorder idempotente
  recuperável e gate consolidado de wave. Durante o hardening, Waves 003, 004 e
  005, golds, exports, packets, audits e fingerprints são somente leitura.
- A Wave 005 permanece pausada. Depois do quality gate do hardening, será
  retomada uma única vez a partir de qoh chunk 011, seguida por wHdy e Bbh. A
  auditoria ocorrerá numa única fase após os cinco episódios atingirem o receipt
  `ready_for_audit`.

### 2026-07-14 — Quality gate 1 do pipeline one-shot

- O evento `MSF-R20-GOLD-WAVE-ONE-SHOT-001-001` entregou o compilador puro, o
  recorder idempotente e o gate consolidado. O coordenador reproduziu `69
  passed`, compilação em memória, validação da skill e `git diff --check`.
- Execuções read-only das Waves 003, 004 e 005 preservaram 40 arquivos
  rastreados de status, auditoria, packet e fingerprints. A Wave 005 continuou
  `in_progress`; nenhum dado gold real foi alterado.
- Quatro probes adversariais impediram a aprovação: tema desconhecido virou
  `business_model`; wave incompleta escreveu recibo; episódio protegido sem
  packet passou como pronto; e ausência de evidência ocultou os demais erros do
  mesmo candidato.
- Foi aberta uma única rodada corretiva consolidada (`OS-QG-001..004`). A Wave
  005 continua pausada e só será retomada depois do quality gate final.

### 2026-07-14 — Quality gate 2 do pipeline one-shot

- O evento `MSF-R20-GOLD-WAVE-ONE-SHOT-001-002` foi reproduzido com `73
  passed`, compilação, skill e diff aprovados. Temas desconhecidos agora geram
  issue, waves incompletas não escrevem recibo e o compilador devolve múltiplos
  erros estruturados numa só checagem.
- A rota protegida passou nos casos de packet ausente ou trocado, audit inválido
  e fingerprints divergentes. Os dados reais das Waves 003–005 permaneceram
  byte a byte inalterados nas leituras do coordenador.
- Um probe adicional encontrou o residual `OS-QG-003b`: a rota pending aceitou
  o receipt de `pending-a` apontando para o packet de `pending-b` e classificou
  a wave como pronta. A segunda e última correção fica restrita a vincular o
  receipt ao `export_suffix` esperado e ao `episode_video_id` do packet.
- A Wave 005 permanece pausada até o quality gate final desse residual.

### 2026-07-14 — Pipeline one-shot aprovado e Wave 005 liberada

- O evento `MSF-R20-GOLD-WAVE-ONE-SHOT-001-003` fechou `OS-QG-003b`. O
  coordenador reproduziu `74 passed`, compilação, skill e diff aprovados.
- O probe final fez `pending-a` apontar para o packet íntegro de `pending-b`:
  o gate retornou `in_progress`, `packet_identity=false` e não criou receipt.
  Restaurado o packet correto, retornou `ready_for_audit` e gerou receipt único.
- A prova real read-only da Wave 005 acompanhou 509 arquivos sem diferença. zo
  e JF estão protegidos/prontos; qoh, wHdy e Bbh seguem nos checkpoints previstos.
- `MSF-R20-GOLD-WAVE-ONE-SHOT-001` foi aprovado. A Wave 005 foi enfileirada para
  uma única retomada autônoma e só retornará ao coordenador no gate consolidado
  dos cinco episódios ou em bloqueio externo terminal real.

### 2026-07-14 — Wave 005: checkpoint interno de qoh retomado sem novo gate

- O evento `MSF-R20-WAVE-005-016` trouxe progresso real: qoh chegou a 36/36
  reviews e 35 candidatos em batches atômicos; nenhum packet parcial,
  finalização, build, auditoria ou alteração protegida ocorreu.
- O inventário de números/calibração continua sendo correção interna. O check
  recusou um raw stale de G029 antes de escrever, sem lock, permissão, fonte ou
  fingerprint divergente.
- Pelo contrato one-shot, isso não é entrega bloqueada nem exige auditoria do
  coordenador. O mesmo worker foi devolvido para regenerar o manifesto a partir
  do estado atual, resolver qoh e só então continuar wHdy/Bbh até o receipt 5/5.

### 2026-07-14 — Autocontinuação intraworker elimina eventos de checkpoint

- A Wave 005 ainda não está concluída: zo e JF estão protegidos; qoh tem 36/36
  reviews, mas não foi finalizado; wHdy e Bbh ainda não foram processados.
- A causa dos eventos menores remanescentes foi isolada: o gate 5/5 estava
  correto, porém cada mensagem ao worker abria um turno finito e o encerramento
  desse turno ainda era publicado como WORKER_EVENT ao coordenador.
- O protocolo passou a exigir checkpoint job-local e `WORKER_SELF_CONTINUE`
  idempotente para o próprio worker em todo estado não terminal. O coordenador
  permanece sem polling e só recebe o evento terminal consolidado.
- A continuação preserva o mesmo worker, modelo/esforço, job ID, ownership e
  critérios. Duas falhas confirmadas do transporte intraworker são o único novo
  bloqueio de comunicação permitido; erros rotineiros continuam internos.

### 2026-07-14 — Wave 005 retomada após autocontinuação sem execução

- Após aviso do owner, o coordenador fez a leitura única permitida do chat idle.
  qoh estava finalizado e packet-ready; wHdy continuava no chunk 001 e Bbh não
  havia começado.
- A causa foi semântica: ao consumir `self-002`, o worker criou outra mensagem
  de continuação sem executar a `next_action`. Não houve erro de fonte, lock,
  permissão ou dado gold.
- O contrato agora exige consume-then-execute: progresso material verificável
  antes de um novo continuation ID, proibindo reenvio da mesma ação sem avanço.
- A Wave 005 foi retomada no mesmo worker a partir de wHdy chunk 001; continua
  valendo um único evento terminal consolidado ao coordenador.

### 2026-07-14 — Autocontinuação revogada; Wave 005 em retomada direta

- A leitura única após novo alerta do owner confirmou progresso real: qoh está
  packet-ready e wHdy chunk 001 foi compilado e persistido atomicamente.
- Também confirmou a limitação da superfície: `self-003` apareceu no turno
  ativo, mas não iniciou outro turno após a resposta final; o worker ficou idle.
- `WORKER_SELF_CONTINUE` foi removido do protocolo. Checkpoints permanecem
  duráveis, porém a delegação não pode terminar neles: deve continuar no mesmo
  turno até o gate consolidado.
- A retomada W5-R18 começa em wHdy chunk 002 e segue até wHdy, Bbh e receipt 5/5,
  sem evento intermediário ao coordenador.

### 2026-07-14 — Wave 005 passa a heartbeat temporário do executor

- W5-R18 terminou em 32 segundos após apenas ler wHdy chunk 002, novamente sem
  erro de fonte, lock, permissão ou validação. O chat ficou idle.
- Repetir outra retomada direta seria a mesma rota já falha. A recuperação mudou
  materialmente para heartbeat temporário anexado ao thread do worker.
- O heartbeat acorda somente o executor, retoma o checkpoint, não envia eventos
  de progresso e não exige processamento paralelo do coordenador.
- A automação é limitada à Wave 005 e deve ser desativada pelo worker depois do
  receipt 5/5 e do único WORKER_EVENT terminal.
- Heartbeat criado no app com ID
  `msf-wave-005-continuar-worker-at-gate-5-5`, intervalo de cinco minutos e alvo
  exclusivo no thread `019f4c90-b9dc-7e32-8ff1-57f8896386d3`.

### 2026-07-14 — Heartbeat pausado; runner persistente W5-R20

- O heartbeat disparou às 14:34Z e 14:39Z. No primeiro turno leu os sinais
  002–010 sem persistir; no segundo apenas declarou a revisão pendente e encerrou
  com `DONT_NOTIFY`. O worker permaneceu idle.
- A automação `msf-wave-005-continuar-worker-at-gate-5-5` foi pausada para evitar
  concorrência e duplicação.
- Foi criado `.codex-work/coordination/run-wave005-until-terminal.ps1`: runner
  sequencial que retoma o mesmo thread pela Codex CLI, verifica progresso real,
  reduz a unidade após duas tentativas sem avanço e aplica timeout de 30 minutos.
- O runner só encerra após marcador do evento terminal ou orçamento explícito,
  mantendo logs e status duráveis no diretório job-local.

### 2026-07-14 — Modelo coordenador/worker encerrado pelo owner

- O owner encerrou delegações entre chats, `WORKER_EVENT`, checkpoints
  obrigatórios, heartbeats e runners persistentes para extração gold.
- A automação `msf-wave-005-continuar-worker-at-gate-5-5` foi apagada no app.
- O runner W5-R20 e os artefatos de autocontinuação foram removidos; dados gold,
  packets, auditorias históricas e progresso persistido foram preservados.
- A execução passa a ocorrer integralmente no chat ativo, incluindo correções
  rotineiras e validação. Somente a auditoria final do épico usa
  `gpt-5.6-sol/high` ou superior, sem revisão intermediária.
- Na transição, a Wave 005 preserva zo/JF `complete/passed`, qoh packet-ready e
  wHdy reviews 001-010 com 12 IDs únicos; a próxima fronteira é wHdy chunk 011.
### 2026-07-16 - VTurb backfill optimization implementada

- P0: capability preflight unico, circuit breaker global e telemetria por fase
  implementados; headless ficou explicitamente indisponivel por
  `system_library_missing`.
- P1: 128 itens verificados no Chrome real em 75,1 min; 94 capturas, 33 falhas
  terminais e 1 ausencia; 165 eventos atomicos e cursor final zero.
- As 94 capturas foram importadas em 8 s no WSL. A regressao recuperou ainda
  `NiT0-ABoVnk` com 1.087 segmentos.
- P2: `large-v3-turbo` padrao aprovado; `small` e batch 8 rejeitados por perda
  material de tokens/numeros. Chunks de 1.200 s, overlap 2 s, receipts, reuso,
  prefetch e ETA adaptativo implementados.
- `p78Zv3_WCsM` foi transcrito integralmente em tres chunks e promovido com 998
  segmentos e cobertura 99,78%.
- Estado final desta rodada: 127/163 validos; 36 `pending_asr`; 94,42 h de
  midia; ETA quente aproximado de 42 h. Gold nao foi reconstruido antes do gate.
- Automacao semanal `atualizar-epis-dios-vturb` atualizada para scan dos cinco
  videos recentes e pipeline incremental completo toda quarta-feira as 9h.
- Validacoes: 24 testes Python e 3 testes Node verdes; runtime parity pass.

### 2026-07-16 - Catálogo VTurb completado e traduções Codex promovidas

- As 35 transcrições recuperadas foram importadas no data root Linux-native; o
  inventário terminou com 163/163 vídeos válidos, zero pendência e 163 estados
  `completed`.
- `xNrLpLTOPHU`, `9wfKG0bf53o` e `HRuMLbkMO0E` preservam a fonte em inglês e
  ganharam `transcript_pt_br.json` traduzido pelo próprio Codex; nenhuma
  tradução automática do YouTube foi usada. O pipeline gold prefere pt-BR e
  mantém o original como proveniência protegida.
- A captura DOM do Chrome repetiu cada legenda em `9wfKG0bf53o` e
  `HRuMLbkMO0E`. As cópias canônicas foram normalizadas de 1.248 para 624 e de
  910 para 455 segmentos, respectivamente, sem perda de cobertura. As capturas
  integrais anteriores à normalização foram preservadas em
  `transcript_original_browser_capture.json`.
- Os hashes das traduções apontam para os originais canônicos deduplicados, os
  três episódios têm zero pares exatos duplicados e `gold_transcript_language`
  igual a `pt-BR`.
- A fila gold foi regenerada pela classificação já estabelecida: 285 episódios
  no projeto, todos `source_complete` e nenhum `awaiting_source`.
- Validações finais: regressão ampliada com 178 testes Python aprovados e
  inventário VTurb com 163/163 transcrições válidas.

### 2026-07-16 - Complementares: fila reconciliada e pendências de mídia resolvidas

- A reconciliação da Academy corrigiu sete episódios do YouTube que ainda
  apareciam como pendentes embora já tivessem transcript canônico.
- `AD-SEXUALIDADE3.mp4` foi testado com `large-v3-turbo` com e sem VAD. A única
  saída sem VAD foram blocos repetidos de "Thank you" cobrindo todo o vídeo;
  foi classificado como `no_speech_validated`, sem promover alucinação.
- Os dois arquivos antes bloqueados por tamanho foram baixados de forma
  retomável no WSL e transcritos em `large-v3-turbo`: `AD 11.mp4` (33
  segmentos) e `Aula Desafio 6 Low em 30.mp4` (40m42s, 1.442 segmentos em
  chunks de 20 minutos).
- A fila ficou sem `skipped_over_limit` e sem `transcribed_empty`: 158
  referências transcritas, 18 referências YouTube já processadas e uma mídia
  `no_speech_validated`.
- O pipeline de Drive passou a preservar o transcript tiny anterior, retomar
  downloads parciais, separar áudio longo em chunks e detectar alucinação de
  silêncio repetitiva. O reprocessamento de qualidade das 156 fontes tiny e a
  tradução Codex ficam deliberadamente depois da promoção dos novos sources.

### 2026-07-16 - Gold Runtime Pilot 007 concluido

- `beFYVzSv2bw` terminou `complete/passed/0` com 20 reviews, 37 IDs unicos,
  calibracao pass e packet exato de cinco arquivos.
- A auditoria Sol abriu quatro findings reais; uma revisao transacional unica
  adicionou os limites 95/99, a sequencia de cinco segundos, os dois outcomes
  sonoros e a trajetoria intermediaria de escala.
- Readiness, build, validador normal e validador com auditoria obrigatoria
  passaram; fingerprints protegidos permaneceram iguais.
- Wall ate receipt: 1h31m12s; comandos deterministas: 4,28s. Os gargalos foram
  prelint semantico (25m13s), auditoria (19m39s) e remediacao/reauditoria.
- O delta de reauditoria foi rejeitado por invariantes mal definidos e a
  verificacao voltou corretamente ao dossier integral. A limitacao foi
  registrada como `MSF-PL-068`.

### 2026-07-17 - Arquitetura gold canonica consolidada

- `chronological_hybrid_v1` passou a ser a unica rota de producao: leitura
  cronologica integral, autoria semantica principal, controles deterministas,
  one-shot e auditoria Sol final unica.
- Os quatro pilotos do compilador semantico cego foram arquivados como pesquisa
  read-only. Shards, reducer global, janelas de relacao e gap resolver nao fazem
  parte do runtime executavel.
- Foram promovidos somente os controles que provaram valor: inventario
  numerico, bindings de calibracao/fronteira, disposicoes source-scoped e
  bloqueio de duplicata exata sem merge automatico.
- Contexto e bootstrap agora registram a arquitetura. Contrato, prompt, AGENTS,
  skills e plano canonico foram alinhados; 165 testes gold passaram no WSL.

### 2026-07-18 - Retrospectiva do Gold Runtime Pilot 011 e plano de simplificacao

- O run `MSF-R20-gold-next-NiT0-ABoVnk-f3321e2ba8` foi reconciliado pelos
  receipts locais: `complete/passed/0`, 142 candidatos unicos, calibracao 12/16,
  packet de cinco arquivos e fingerprints protegidos preservados.
- O wall total foi 9h43m33,4s, mas os comandos deterministas somaram apenas
  40,73s. O span de reauditoria de 8h06m59,2s esta contaminado por espera,
  interrupcao e perda de continuidade; nao representa tempo ativo do Sol.
- Contra o piloto 009, o prelint melhorou 66,8% e a auditoria inicial 42,1%,
  enquanto o total piorou 7,84x, a remediacao autoral subiu 62,1% e o job
  acumulou 182 arquivos, 27 helpers, nove finalizacoes e seis builds.
- A retrospectiva concluiu que os controles de risco, matriz numerica,
  atomicidade e dossier em duas camadas entregaram ganho real, mas o pacote de
  melhorias falhou como otimizacao ponta a ponta por fragmentar autoria,
  remediacao, derivados e continuidade da auditoria.
- Foram registrados `MSF-PL-084` a `MSF-PL-087` e criado um plano com apenas
  quatro mudancas de alto impacto: identidade terminal canonica, manifesto
  autoral unico, uma passagem adversarial pre-apply e auditoria retomavel por
  envelope/delta focal. Nenhuma mudanca de runtime ou dados foi executada nesta
  retrospectiva.

### 2026-07-18 - Simplificacao 011 implementada no runtime gold

- HI-01 implementada com registry terminal central e identidade por episodio,
  reconciliados contra a fonte ativa antes da selecao. Cursor/fila deixaram de
  certificar terminalidade; fonte alterada exige reprocesso e motivo explicitos.
- HI-02 implementada com `gold_authoring_manifest_v1` como unica autoridade
  interna de decisoes. Preview, apply e remediacao usam o mesmo hash; reviews,
  ledger, calibracao, workbench e payload sao derivados sem helper de episodio
  ou patch separado de ledger/calibracao no caminho normal.
- HI-03 implementada com view adversarial unica e receipt vinculado ao hash das
  decisoes. Regressoes F019/F037 bloqueiam calibracao apenas tematica e invalidam
  revisao adversarial stale antes da escrita.
- HI-04 implementada com audit request/envelope duraveis, materializacao do
  veredito antes de qualquer mutacao, retomada apenas da fase Sol, spans
  `interrupted` fora do tempo ativo e remediacao por manifesto completo mais
  delta focal. Delta invalido cai automaticamente para novo request do dossier
  integral, sem repetir extracao/build.
- A telemetria passou a contar audit requests e a expor separadamente quantidade
  e wall de spans interrompidos. O schema de sessao foi elevado para 1.4.0.
- Ambiente local reparado com Python 3.12.13 na `.venv`; o ambiente quebrado
  anterior foi removido depois do preflight aprovado.
- Validacoes: `py_compile` aprovado; 167 testes focados, 222 testes gold
  ampliados e 287 testes da suite completa aprovados; preflight
  `windows_native` aprovado contra `C:\MSF-data\Marketing_Swipe_File` com temp
  gravavel. A suite completa tambem revelou e fechou uma incompatibilidade de
  fixture VTurb: a lista opcional de IDs mirror-verified agora possui fallback
  vazio sem alterar o comportamento de producao, validado por 21 testes.
- Nenhum episodio real, raw, transcript, packet ou gold foi alterado. As metas
  de 25-40/35-50 minutos permanecem honestamente pendentes dos dois pilotos
  reais congelados previstos na Fase 5.

### 2026-07-18 - Conclusao da transcricao dos materiais complementares VTurb

- Concluida a atualizacao de todos os 33 HLS da VTurb Academy para
  `faster_whisper:large-v3-turbo`; os 33 backups
  `transcript_original_tiny.json` foram preservados.
- A cobertura do acervo Drive tambem foi verificada: 126 de 126 fontes
  `academyvid-*` usam `large-v3-turbo`; nao ha pendencias nos arquivos
  canonicos HLS ou Drive.
- Para aulas longas, o pipeline passou a usar checkpoints de 5 minutos. O
  seletor de `--media-id` foi corrigido para recuperar uma fonte explicitamente
  solicitada mesmo quando o status do CSV estiver stale ou duplicado, sem
  dispensar a verificacao de fonte HLS e da necessidade real de upgrade.

### 2026-07-18 - Fase 5 do benchmark real da Simplificacao Gold 011

- Executados integralmente dois episodios reais na arquitetura
  `chronological_hybrid_v1`: `jbFY16W5GTE` (1.106 segmentos, 21 chunks, 34
  candidatos) e `fBaX4ixKkFo` (1.238 segmentos, 23 chunks, 44 candidatos).
- Selecao+contexto levaram 0,80s e 2,43s; leitura/autoria, 24m23s e 19m59s;
  one-shot inicial, 4,93s e 4,06s; completion, 0,17s e 0,38s.
- A auditoria Sol inicial encontrou cinco findings no total. A remediacao
  source-backed fechou todos, mas a reauditoria 02 ainda encontrou duas
  inconsistencias locais: warning/ledger no G017 do primeiro episodio e um
  record numerico duplicado no G044 do segundo.
- Corrigida a validacao de calibracao duplicada para provar source target e
  evidencia canonica sem depender de link lexical derivado. Corrigido tambem o
  reconciliador numerico para representar repeticao oral explicitamente
  declarada sem inventar nova observacao nem consumir records de mesmo valor.
- Dossiers finais revision `benchmark-011-remediation-03` foram auditados por
  `gpt-5.6-sol/high`; ambos passaram com zero findings. Hashes permaneceram
  inalterados durante a auditoria.
- `complete_gold_episode` registrou os dois como `complete/passed/0`, packet de
  cinco arquivos, calibracao `pass`, fingerprints preservados, identidade
  terminal e `additional_verify_required=false`.
- O wall por receipt foi 3h34m01s e 3h08m10s; a wave sobreposta durou cerca de
  3h34m23s. Portanto as metas ponta a ponta de 35-50 minutos foram rejeitadas,
  apesar dos ganhos do startup, prelint deterministico, one-shot, reauditoria e
  completion.
- Telemetria nao aprovada para alegar complexidade: remediacoes/patches ficaram
  zerados apesar das escritas reais, um span stale acumulou 53m04s e os gaps nao
  classificados foram 2h13m18s e 1h20m05s. Registrados `MSF-PL-088` a
  `MSF-PL-091`.
- Validacoes finais: runtime `windows_native` aprovado com Python 3.12.13 e
  temp gravavel; `py_compile` aprovado; suite completa `293 passed`; auditoria
  final consolidada `passed/0` nos dois episodios.

### 2026-07-18 - Analise criteriosa do benchmark 011 e plano de alto impacto 012

- Reconciliados receipts, eventos, spans, dossiers e tres rodadas de auditoria
  dos episodios `jbFY16W5GTE` e `fBaX4ixKkFo`.
- A retrospectiva separa tempo deterministico, julgamento semantico, spans
  sobrepostos, spans interrompidos e gaps nao classificados; nenhum tempo de
  espera foi atribuido ao prelint ou a compute Sol.
- Ganhos confirmados contra o piloto 011 anterior: wall da wave -63,3%,
  leitura/autoria media -36,3%, crescimento pos-apply reduzido de 89,3% para
  13,3%/12,8% e artefatos observados -62,1% mesmo processando dois episodios.
- Falhas confirmadas: auditoria iniciada antes do gate final da wave, primeiro
  dossier falso-limpo com 427 segmentos unreviewed e 183 must-close, cinco
  findings major, warning/calibration churn, erro pos-commit por envelope
  ausente, contadores de remediacao zerados e gaps de 42,6%-62,3%.
- A anatomia dos dossiers mostrou que header mais workbench ocupam 62,5%-65,5%
  dos 910-931 KB; a proxima reducao deve apagar duplicacao, nao criar outro
  brief.
- Criada a retrospectiva
  `msf-r20-gold-runtime-benchmark-011-retrospective.md` e registrados
  `MSF-PL-092` a `MSF-PL-094`.
- Criado o plano `MSF-R20-GOLD-RUNTIME-SIMPLIFICATION-012` com apenas tres
  iniciativas: invariante source-complete antes de ready, remediacao local
  envelope-first transacional e uma unica superficie de auditoria com despacho
  somente no gate final da wave.
- Nenhuma melhoria foi implementada nesta etapa; dados gold, packets,
  provenance e schema publico permaneceram inalterados.

### 2026-07-18 - Implementacao da simplificacao gold 012

- Implementadas integralmente HI-012-01..03 do plano aprovado.
- Criada invariante source-complete unica e conectada a prelint, finalizer e
  dossier; falso-ready com unreviewed/must-close agora bloqueia antes do write.
- Remediacao alterada para envelope-first: request, envelope, hashes, episodio
  e dossier anterior sao precondicoes; ausencia retorna zero write/build/finalizer.
- Warning identity tornou-se local a fonte/candidato/proposicao com fallback de
  provenance; delta ganhou impact set fechado e erros pos-commit declaram o
  estado persistido e a proxima acao.
- Dossier 3.2 removeu `audit_navigation`, compactou warnings, risk recall e
  workbench como referencias e internou justificativas repetidas.
- Benchmark read-only dos fixtures reais: `jbFY16W5GTE` 909.666 -> 457.785 B
  (-49,68%); `fBaX4ixKkFo` 930.916 -> 492.286 B (-47,12%). Ambos passaram o
  validator e o teto de 500.000 B.
- Request consolidado N/N criado somente depois dos dois ramos ready, com
  hashes fisicos/semanticos congelados e rota `gpt-5.6-sol/high`.
- Validacoes: runtime Windows native pass; `py_compile` pass; regressao 159
  passed; suite completa 300 passed; `git diff --check` pass.
- Dados gold e packets persistidos nao foram alterados; commit, push e deploy
  nao foram executados.
- Registrados `MSF-PL-095` a `MSF-PL-097` e criada a retrospectiva
  `msf-r20-gold-runtime-simplification-012-retrospective.md`.
- Auditoria final consolidada `gpt-5.6-sol/high` encontrou cinco findings: um
  defeito do runtime (warning IDs duplicados) e quatro defeitos semanticos nos
  dois golds protegidos usados como fixtures.
- O defeito do runtime foi corrigido com deduplicacao somente de linhas
  semanticamente identicas e bloqueio de colisoes; regressao adicionada.
- Reauditoria focal confirmou 134 rows/134 IDs em cada dossier, zero colisoes,
  request/hash validos e fechou esse finding. Permanecem quatro findings
  semanticos; status honesto da wave: `changes_requested/4`.
- Suite final apos a correcao: `301 passed`; `py_compile` e
  `git diff --check` aprovados. Dossiers finais: 457.810 e 491.827 bytes.
- Reabertura dos episodios `complete/passed` nao foi executada porque altera
  provenance protegida e exige autorizacao material explicita do owner.
- Registrado `MSF-PL-098` e criado o relatorio
  `msf-r20-gold-runtime-simplification-012-final-audit.md`.

### 2026-07-18 - Wave gold 007 concluida com dois episodios

- Processados integralmente `eCaODMtU5GY` (1.079 segmentos, 21 chunks, 56
  candidatos) e `MiKloPf9-To` (1.051 segmentos, 19 chunks, 50 candidatos) na
  arquitetura `chronological_hybrid_v1`.
- Ambos terminaram `complete/passed/0`, packet 5/5, calibracao `pass`,
  fingerprints preservados e `additional_verify_required=false`.
- A auditoria Sol inicial encontrou 9 e 10 findings. Remediacoes source-backed
  reduziram a fila para 5/3, depois 1/0 e finalmente 0/0 na auditoria
  consolidada 003, `gpt-5.6-sol/high`.
- One-shot inicial: 3,24 s e 3,04 s. Transactions de remediacao:
  `eCaODMtU5GY` 5,77 s, 5,35 s e 5,07 s; `MiKloPf9-To` 6,58 s e 7,97 s.
  Completion: 0,20 s e 0,35 s.
- Leitura/autoria inicial: 28m55,58s e 11m05,58s. O wall sobreposto da wave
  foi aproximadamente 2h01m09s; julgamento semantico continuou dominando o
  tempo total.
- Corrigida uma contradicao do autocheck: literal ASR como `030` pode receber
  normalizacao inferida 0,30% somente quando raw, caveat e origem ASR estao
  explicitamente ligados. Regressao adicionada.
- Gate final: dois ramos protegidos, packet/audit/fingerprint validos, semantic
  SHA-256 `96016344a8a32dfa34dbd29872ae4c3b958ee98133516b3459414daf088e01da`.
- Validacoes: runtime Windows native pass, Python 3.12.13, temp gravavel;
  regressao 172 passed; suite completa 304 passed em 18,63 s; `py_compile`
  pass. Commit, push e deploy nao foram executados.
- Retrospectiva criada em
  `docs/coordination/msf-r20-wave-007-retrospective.md`.

### 2026-07-18 - Remediacao protegida e fechamento final da Simplificacao Gold 012

- O owner autorizou explicitamente corrigir os quatro findings semanticos da
  auditoria final 012 nos episodios `jbFY16W5GTE` e `fBaX4ixKkFo`.
- A revisao protegida arquivou as auditorias anteriores byte a byte e preservou
  as identidades terminais anteriores antes da nova derivacao.
- `jbFY16W5GTE` fechou bindings de G004/G005/G006/G009 e estreitou G024. A
  transacao levou 4.874,61 ms, com uma escrita de reviews, um build, um
  finalizer, um dossier, 34 candidatos e `hard_blockers=0`.
- `fBaX4ixKkFo` corrigiu G043, a aritmetica ASR source-scoped e a classificacao
  de G013. A transacao levou 4.024,33 ms, com uma escrita de reviews, um build,
  um finalizer, um dossier, 44 candidatos e `hard_blockers=0`.
- Corrigido o lifecycle para impedir que finalizacao semanticamente nova
  reutilize audit aprovado anterior. A identidade terminal so e substituida
  por revisao autorizada e replays protegidos permanecem idempotentes.
- Auditoria final unica `/root/final_sol_remediation_012`, `gpt-5.6-sol/high`,
  revisou integralmente os dois dossiers e retornou `passed/0`, sem findings
  novos. F012-01..F012-04 foram fechados.
- `complete_gold_episode` derivou ambos para `complete/passed/0`; packets 5/5,
  fingerprints preservados, receipts e identidades terminais validos. Gate
  consolidado: dois ramos ready, semantic hash
  `d0810ef1260891716c4f04d8c675498064d755ddbfd3c40e44f344ae980a8a22`.
- Validacoes finais: runtime Windows native pass, Python 3.12.13, temp gravavel,
  `py_compile` pass, suite completa `303 passed` em 28,41 s e
  `git diff --check` pass. Commit, push e deploy nao foram executados.

### 2026-07-18 - Analise criteriosa da wave 007 e plano de convergencia 013

- Reconciliados receipts, jobs, manifests, dossiers e quatro vereditos Sol dos
  episodios `eCaODMtU5GY` e `MiKloPf9-To`, comparados ao benchmark 011 e a
  implementacao 012.
- Ganho estrutural confirmado: wall da wave 3h34m23s -> 2h01m09s (-43,5%),
  media individual -47,5%, primeiro veredito consolidado de aproximadamente 13
  minutos e dossiers 36,4%-48,4% menores que os pares de 910-931 KB.
- Regressao de convergencia confirmada: primeiro veredito 5 -> 19 findings
  (+280%); 10 eram numericos e, depois da remediacao 001, seis dos oito
  restantes continuavam numericos. Foram necessarias 3/2 remediacoes e 4/3
  revisoes de dossier.
- A wave observou 109 arquivos transitórios, contra 69 no benchmark 011. O
  helper numerico manteve rows opacos ao adicionar rows tipados; o delta focal
  so descobriu dependencias globais depois da derivacao; spans de reauditoria
  fecharam durante a autoria seguinte.
- Confirmada uma lacuna de autoridade: `calibration_decisions` e validado no
  manifesto, mas nao e levado por `manifest_to_compact_payload()` ao payload
  compilado, obrigando bindings indiretos nas duplicatas do cold open.
- Criada a analise
  `docs/coordination/msf-r20-wave-007-process-analysis-013.md` e registrados
  `MSF-PL-100` a `MSF-PL-104`.
- Criado o plano `MSF-R20-GOLD-FIRST-PASS-CONVERGENCE-013` com somente duas
  iniciativas: fechamento semantico P0 na invariante existente e remediacao
  substitutiva/dependency-closed com medicao atomica.
- Seleção, runtime de prelint, one-shot, completion, transcript integral e Sol
  foram explicitamente congelados. Nenhuma melhoria foi implementada, nenhum
  gold/packet foi alterado e commit, push ou deploy nao foram executados.

### 2026-07-18 - Implementacao e benchmark da convergencia gold 013

- Implementadas HI-013-01 e HI-013-02: fechamento numerico P0 exclusivo,
  autoridade derivada de `calibration_decisions`, ledger merged para duplicata
  equivalente, remediacao substitutiva e impact closure pre-commit.
- O lifecycle fecha o span Sol na materializacao do veredito, encerra autoria
  no one-shot ready e impede sobreposicao entre fases. O benchmark revelou a
  ultima lacuna de transicao; ela foi corrigida e coberta por regressao.
- Regressao 013 final: 15 passed; regressao ampliada anterior: 315 casos
  existentes aprovados; `py_compile`, `git diff --check`, runtime Windows
  native e validacao read-only dos packets protegidos aprovados.
- Benchmark real: `-46vMG3l8Jo` (1.180 segmentos, 40 candidatos) e
  `0sB3ia6LIVM` (951 segmentos, 38 candidatos) chegaram a packet-ready com
  prelint limpo, calibracao pass, hard blockers zero, packet 5/5 e fingerprints
  preservados.
- Cada episodio fez uma escrita, um finalizer, um build e um dossier; one-shot
  de 2,774s/2,539s. Dossiers: 471.229/413.540 bytes. Zero remediacao ate a fase
  Sol e 43 arquivos job-local contra 109 na wave 007 (-60,6%).
- Wall ate os dois packets: 52m06,35s; gate Sol aberto em 54m38,92s. Spans de
  autoria foram reconciliados aos eventos one-shot factuais sem overlap.
- Request consolidado `gpt-5.6-sol/high` selado com hash
  `1121f2d96bbc09426792d396692dca2f00253a4eff938d2e4d1eaf2b3e344ed2`.
- A tentativa de auditoria externa foi bloqueada antes de transmitir dados,
  porque os dossiers locais privados exigem autorizacao explicita adicional do
  owner. Estado honesto: ambos `awaiting_external_audit/pending_external`;
  `passed/0` e `complete` ainda nao foram derivados.
- Retrospectiva criada em
  `docs/coordination/msf-r20-gold-first-pass-convergence-013-retrospective.md`.
  Commit, push e deploy nao foram executados.

### 2026-07-19 - Wave gold 009 concluida com dois episodios

- Processados integralmente `yhjZTeFNMHk` (5.289 segmentos, 51 chunks, 47
  candidatos finais) e `MGpXRmYvJDc` (943 segmentos, 17 chunks, 32 candidatos)
  na arquitetura `chronological_hybrid_v1`.
- One-shot inicial: 11,982 s e 7,175 s. Transacoes de remediacao aprovadas:
  E01 12,016 s e 12,225 s; E02 4,559 s. Completion: 0,488 s e 0,385 s.
- A auditoria Sol inicial (`gpt-5.6-sol/high`) levou 464,6 s e abriu quatro
  findings no E01 e dois no E02. A primeira reauditoria consolidada levou
  494,7 s: aprovou E02 e encontrou quatro dependencias residuais no E01. A
  reauditoria focal final do E01 levou 308,9 s e fechou todos os findings.
- E01 passou a preservar 60.000 por dia, sete lancamentos, duas a tres VSLs,
  uma semana, terceira rota de produto, equacao de valor, faixas de tamanho da
  VSL e o caso host-owned de 300/600 vendas por dia. O ledger foi redestinado
  para G044-G047 em 96 segmentos source-backed.
- E02 passou a representar 16 mil de investimento, 160 mil de resultado, a
  comparacao host-owned de 10x, 40%-50% da receita front-end como custo de
  trafego e 3K como preco de R$ 3.000.
- Corrigido o reconciliador numerico para tratar grupos portugueses `.ddd` e
  sufixo `k` adjacente como milhares; regressao adicionada para ambos.
- Ambos terminaram `complete/passed/0`, packet 5/5, calibracao `pass`,
  fingerprints preservados, identidades terminais validas e
  `additional_verify_required=false`.
- Gate consolidado: dois ramos protegidos, packet/audit/fingerprint validos,
  semantic SHA-256
  `02ecfacef87f7958f4c5f01cb7372ee613e58e52b6c070b1e5b64170b1dba86e`.
- Wall por receipt: E01 4h30m59,9s; E02 3h53m10,6s. Wall sobreposto da wave:
  aproximadamente 4h31m06s. O tempo Sol somado foi 21m08,2s; os gaps de
  autoria/orquestracao ainda dominaram o wall.
- Validacoes finais: runtime Windows native `pass`, Python 3.12.13, temp
  gravavel; suite completa `322 passed` em 48,58 s. Commit, push e deploy nao
  foram executados.
