---
name: marketing-swipe-file-ingest
description: Ingest YouTube episodes into the Marketing Swipe File. Use when Codex needs to add or process VTurb/KiwiCast/Hotmart Cast YouTube URLs, collect metadata, collect or mark transcripts, normalize transcript segments, create extraction chunks, detect initial assets, generate extraction packets, and log the local episode pipeline.
---

# Marketing Swipe File Ingest

## Overview

Use this skill to move an episode from URL or local `video_id` into the local Codex-first pipeline.

## Workflow

1. Check `README.md`, `docs/marketing-swipe-file-handoff.md`, and `docs/execution-log.md` if the current state is unclear.
2. Use bundled Python, not plain `python`, when PATH is uncertain:
   `C:\Users\luish\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`
3. For a new URL, run:
   `scripts/run_episode_pipeline.py --url <youtube_url>`
4. For an existing episode after Playwright transcript fallback, run:
   `scripts/run_episode_pipeline.py --video-id <video_id> --skip-metadata --skip-transcript`
5. If the direct caption endpoint produces zero segments, do not fake a transcript. Use the Playwright fallback procedure in `docs/marketing-swipe-file-handoff.md`, then rerun the pipeline.

## Outputs

- `data/raw/youtube/{video_id}/metadata.json`
- `data/raw/youtube/{video_id}/transcript_original.json`
- `data/processed/{video_id}/content_segments.json`
- `data/processed/{video_id}/chunks/chunk_index.json`
- `data/processed/{video_id}/referenced_assets.json`
- `data/processed/{video_id}/acquisition_tasks.json`
- `data/processed/{video_id}/chunked_extraction_packets/`
- `data/processed/{video_id}/episode_summary.md`
- `data/logs/episode_pipeline_*.jsonl`

## Rules

- Preserve raw transcript and metadata; never overwrite local source material with invented data.
- Keep generated raw/processed data local and ignored by Git unless explicitly requested otherwise.
- Prefer chunked extraction packets for long episodes; full packets can be too large.
- Treat `transcript_fallback_needed.md` as a normal blocked state, not as a failed implementation.
