---
name: marketing-swipe-file-scale-batch
description: Scale Marketing Swipe File podcast processing batches. Use when Codex needs to discover more VTurb YouTube episodes, append channel videos to the configured runtime queue, count fully processed videos, run the episode loop repeatedly, use Playwright transcript fallback, extract/classify/dedupe/audit insights, consolidate exports, and continue until a requested complete-video target such as 50 videos is reached.
---

# Marketing Swipe File Scale Batch

## Overview

Use this skill to move from one-off episode processing to a target-driven batch loop.

## Complete Video Definition

There are two distinct completion states. Do not conflate the legacy serving
pipeline with the parallel gold layer.

### Legacy processed

Count a video as legacy processed only when all of these exist and are
non-empty:

- `{dataRoot}/raw/youtube/{video_id}/metadata.json`
- `{dataRoot}/raw/youtube/{video_id}/transcript_original.json` with transcript segments
- `{dataRoot}/processed/{video_id}/content_segments.json`
- `{dataRoot}/processed/{video_id}/chunks/chunk_index.json`
- `{dataRoot}/processed/{video_id}/insights.json`

This state is enough for the frozen v2 serving pool. It is not a gold episode.

### Gold complete

Count a video as gold complete only when its separate
`{dataRoot}/processed/{video_id}/gold_extraction/` package has all of the
following:

- `transcript_clean.json`, `removed_segments.json`, and chronological chunks
  covering every clean segment exactly once;
- one explicit status for every work-order chunk, including a full-read
  zero-insight review when applicable;
- schema-valid `insights_exhaustive.json`, layered verbatim evidence, typed
  quantitative claims, and symmetric acyclic relations;
- `high_signal_coverage_ledger.json` with every signal captured, merged, or
  explicitly excluded;
- episode-discovered calibrations at or above the duration-proportional
  minimum, with required semantic coverage;
- zero open independent-audit findings and `gold_extraction_status.json` set
  to `complete`;
- matching protected fingerprints for `insights_v2.json`,
  `curated_insights.json`, and `insights_v2_master.json`.

`insights.json` alone never counts as gold complete. An episode with status
`awaiting_external_audit` is extraction-ready, but must not be included in a
gold batch total or any master export.

`awaiting_external_audit` is a compatibility name: the audit is external to the
executor task. A separate Codex coordinator must validate reviewer provenance,
the finding contract, zero open findings, deterministic checks, and protected
fingerprints. A worker must never approve its own output or set `passed` through
a free build argument. Preserve historical audit providers as recorded.

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
- `skills/marketing-swipe-file-youtube-transcripts`: preferred YouTube transcript fallback. Use the connected real Chrome UI first: expand the description, click the deep `Mostrar transcricao` button inside `ytd-video-description-transcript-section-renderer`, then read `transcript-segment-view-model` nodes from the `Neste video` panel. Use the legacy CLI script only when a real Chrome session is unavailable.
- `scripts/capture_youtube_transcript_with_playwright_cli.py`: older fallback wrapper. Do not use it for new transcript recovery until it matches the description-button flow in `marketing-swipe-file-youtube-transcripts`.
- `scripts/run_episode_batch.py`: supervises status, ingestion, Playwright fallback, transcript normalization, chunking, asset detection, insight extraction, taxonomy classification, dedupe, audit, summaries, and export consolidation.

## Rules

- Use the bundled Codex Python path when plain `python` is unreliable.
- Preserve raw data. Never fake transcript segments or manually mark a video complete.
- For YouTube transcript fallback, use `$marketing-swipe-file-youtube-transcripts` or its script before concluding a video is blocked.
- Prefer the main queue order by `episode_priority`; append newly discovered videos with increasing priority.
- Treat YouTube transcript failures as blocked state, not as successful extraction.
- IDs beginning with `-` must be passed as `--video-id=<id>` or through a full `--url`.
- Re-run `scripts/consolidate_exports.py` after batch processing.
- Keep raw and processed podcast data local and ignored by Git.
