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
- `git status` currently fails with `fatal: not a git repository`, even though a `.git` directory exists. Treat Git state as unreliable until the repository metadata is repaired or reinitialized.
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
