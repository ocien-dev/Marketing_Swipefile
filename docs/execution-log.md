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
