---
name: marketing-swipe-file-scale-batch
description: Scale Marketing Swipe File podcast processing batches. Use when Codex needs to discover more VTurb YouTube episodes, append channel videos to the configured runtime queue, count fully processed videos, run the episode loop repeatedly, use Playwright transcript fallback, extract/classify/dedupe/audit insights, consolidate exports, and continue until a requested complete-video target such as 50 videos is reached.
---

# Marketing Swipe File Scale Batch

## Overview

Use this skill to move from one-off episode processing to a target-driven batch loop.

## Complete Video Definition

Count a video as complete only when all of these exist and are non-empty:

- `{dataRoot}/raw/youtube/{video_id}/metadata.json`
- `{dataRoot}/raw/youtube/{video_id}/transcript_original.json` with transcript segments
- `{dataRoot}/processed/{video_id}/content_segments.json`
- `{dataRoot}/processed/{video_id}/chunks/chunk_index.json`
- `{dataRoot}/processed/{video_id}/insights.json`

Do not count a video with only metadata, only transcript, only chunks, or a stale `transcript_fallback_needed.md`.

## Batch Workflow

1. Check status:
   `scripts/run_episode_batch.py --target-complete 50 --status-only`
2. Set the runtime data root when MSF-R03 external data is active:
   ```powershell
   $dataRoot = if ($env:MSF_DATA_DIR) { $env:MSF_DATA_DIR } else { "data" }
   ```
3. If the queue has too few videos, discover channel videos:
   `scripts/discover_vturb_youtube_videos.py --append --append-limit 40`
4. Run the target loop:
   `scripts/run_episode_batch.py --target-complete 50 --use-playwright-fallback`
5. If Playwright/NPM needs filesystem access outside the workspace, rerun the same command with approval rather than bypassing the fallback.
6. Use `--start-priority` and `--max-attempts` to continue in controlled cycles after known blocked videos.
7. Stop only when the target is reached, the queue is exhausted, or repeated Playwright/YouTube transcript failures make more progress impossible.

## Scripts

- `scripts/discover_vturb_youtube_videos.py`: reads the VTurb channel page, follows YouTube continuation tokens, writes `{dataRoot}/exports/vturb_channel_discovered_videos.csv`, and can append deduped URLs to `{dataRoot}/input/youtube_urls.csv`.
- `scripts/capture_youtube_transcript_with_playwright_cli.py`: opens a YouTube video with Playwright CLI, expands the description, clicks `Mostrar transcricao`, reads current transcript DOM elements first, falls back to snapshot parsing, and writes `transcript_original.json`.
- `scripts/run_episode_batch.py`: supervises status, ingestion, Playwright fallback, transcript normalization, chunking, asset detection, insight extraction, taxonomy classification, dedupe, audit, summaries, and export consolidation.

## Rules

- Use the bundled Codex Python path when plain `python` is unreliable.
- Preserve raw data. Never fake transcript segments or manually mark a video complete.
- Prefer the main queue order by `episode_priority`; append newly discovered videos with increasing priority.
- Treat YouTube transcript failures as blocked state, not as successful extraction.
- IDs beginning with `-` must be passed as `--video-id=<id>` or through a full `--url`.
- Re-run `scripts/consolidate_exports.py` after batch processing.
- Keep raw and processed podcast data local and ignored by Git.
