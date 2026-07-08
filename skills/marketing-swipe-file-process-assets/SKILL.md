---
name: marketing-swipe-file-process-assets
description: Register and process obtained complementary files for the Marketing Swipe File. Use when Codex needs to handle files placed in the configured runtime input/assets folder, register checksummed assets, extract normalized segments from PDF, DOCX, TXT, Markdown, HTML, CSV, XLSX, or PPTX files, generate asset summaries, and preserve evidence locators.
---

# Marketing Swipe File Process Assets

## Overview

Use this skill when the user has obtained complementary files or when fixture assets need validation.

## Workflow

1. Set the runtime data root when MSF-R03 external data is active:
   ```powershell
   $dataRoot = if ($env:MSF_DATA_DIR) { $env:MSF_DATA_DIR } else { "data" }
   ```
2. Put files under `$dataRoot\input\assets\{video_id}\`.
3. Run:
   `scripts/run_asset_pipeline.py --episode-video-id <video_id> --input-dir "$dataRoot\input\assets\<video_id>"`
4. For already registered assets, run:
   `scripts/run_asset_pipeline.py --episode-video-id <video_id>`
5. Review raw metadata, extracted segments, and `asset_summary.md`.

## Supported Inputs

- PDF: page-level extraction through `pdfplumber`.
- DOCX: paragraphs, headings, and simple tables.
- TXT/Markdown/HTML: text blocks and sections.
- CSV/XLSX: rows, sheets, and cell ranges.
- PPTX: slide text.

Image OCR is not part of the MVP flow yet. Image assets are registered but skipped with a log entry until OCR is implemented.

## Rules

- Preserve original files in `$dataRoot\raw\assets\{asset_id}\`.
- Use checksum-based asset ids to avoid duplicate registration.
- Keep page, sheet, cell, slide, or section locators in every segment when possible.
