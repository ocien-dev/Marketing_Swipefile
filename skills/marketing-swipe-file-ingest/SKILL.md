---
name: marketing-swipe-file-ingest
description: Ingest YouTube episodes into the Marketing Swipe File. Use when Codex needs to add or process VTurb/KiwiCast/Hotmart Cast YouTube URLs, collect metadata, collect or mark transcripts, normalize transcript segments, create extraction chunks, detect initial assets, generate extraction packets, and log the local episode pipeline.
---

# Marketing Swipe File Ingest

## Overview

Use this skill to move an episode from URL or local `video_id` into the local Codex-first pipeline.

## Workflow

1. Check `README.md`, `docs/marketing-swipe-file-handoff.md`, and `docs/execution-log.md` if the current state is unclear.
2. Set the runtime data root when MSF-R03 external data is active:
   ```powershell
   $dataRoot = if ($env:MSF_DATA_DIR) { $env:MSF_DATA_DIR } else { "data" }
   ```
3. Use `.venv\Scripts\python.exe -B` by default.
4. For a new URL, run:
   `scripts/run_episode_pipeline.py --url <youtube_url>`
5. For an existing episode after Playwright transcript fallback, run:
   `scripts/run_episode_pipeline.py --video-id <video_id> --skip-metadata --skip-transcript`
6. If the direct caption endpoint produces zero segments, do not fake a transcript. Use the Playwright fallback procedure in `docs/marketing-swipe-file-handoff.md`, then rerun the pipeline.

## Outputs

- `$dataRoot\raw\youtube\{video_id}\metadata.json`
- `$dataRoot\raw\youtube\{video_id}\transcript_original.json`
- `$dataRoot\processed\{video_id}\content_segments.json`
- `$dataRoot\processed\{video_id}\chunks\chunk_index.json`
- `$dataRoot\processed\{video_id}\referenced_assets.json`
- `$dataRoot\processed\{video_id}\acquisition_tasks.json`
- `$dataRoot\processed\{video_id}\chunked_extraction_packets\`
- `$dataRoot\processed\{video_id}\episode_summary.md`
- `$dataRoot\logs\episode_pipeline_*.jsonl`

## Rules

- Preserve raw transcript and metadata; never overwrite local source material with invented data.
- Keep generated raw/processed data local and ignored by Git unless explicitly requested otherwise.
- Prefer chunked extraction packets for long episodes; full packets can be too large.
- Treat `transcript_fallback_needed.md` as a normal blocked state, not as a failed implementation.
