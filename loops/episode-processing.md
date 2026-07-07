# Episode Processing Loop

Goal: process one YouTube episode into local Marketing Swipe File artifacts.

## Steps

1. Add or confirm URL in `data/input/youtube_urls.csv`.
2. Run:
   `scripts/run_episode_pipeline.py --url <youtube_url>`
3. If transcript fallback is needed, capture the YouTube transcript through Playwright as described in `docs/marketing-swipe-file-handoff.md`.
4. Rerun:
   `scripts/run_episode_pipeline.py --video-id <video_id> --skip-metadata --skip-transcript`
5. Extract insights from chunked packets into `data/processed/{video_id}/chunked_insights/{extractor}/`.
6. Run classification, dedupe, audit, summaries, and consolidation.

## Batch Mode

When the goal is a target count such as 50 complete videos, use the batch supervisor instead of repeating this loop manually:

1. Check current status:
   `scripts/run_episode_batch.py --target-complete 50 --status-only`
2. If the queue is too short, append discovered VTurb channel videos:
   `scripts/discover_vturb_youtube_videos.py --append --append-limit 40`
3. Run:
   `scripts/run_episode_batch.py --target-complete 50 --use-playwright-fallback`
4. If a video still has no transcript after Playwright fallback, leave it blocked and continue to the next queued video.

## Done

- Metadata, transcript, content segments, chunks, asset detection, extraction packets, episode summary, and pipeline logs exist.
- If no transcript exists, `transcript_fallback_needed.md` exists and the episode is not counted as processed.
- Insights are audited before retrieval.
