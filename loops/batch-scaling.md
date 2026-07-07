# Batch Scaling Loop

Goal: keep expanding and processing the VTurb podcast inventory until a target number of complete videos is reached.

## Steps

1. Count complete videos with `scripts/run_episode_batch.py --target-complete 50 --status-only`.
2. Discover more VTurb channel videos with `scripts/discover_vturb_youtube_videos.py --append --append-limit <n>`.
3. Append only deduped URLs to `data/input/youtube_urls.csv`.
4. Run `scripts/run_episode_batch.py --target-complete 50 --use-playwright-fallback`.
5. Let blocked transcript videos remain blocked; continue with the next queued episode.
6. Use `--start-priority` and `--max-attempts` to continue after known blocked ranges without repeating the whole queue.
7. Consolidate exports and update `docs/execution-log.md` when the batch advances.

## Complete Video Gate

A video counts only after metadata, transcript segments, normalized segments, chunks, and audited `insights.json` exist.

## Transcript Fallback

Use `scripts/capture_youtube_transcript_with_playwright_cli.py` through the batch runner. It uses the current YouTube DOM transcript panel first and snapshot parsing second. If `npx` needs npm cache access outside the workspace, rerun the batch with approval.

## Stop Conditions

- Target complete-video count reached.
- Queue exhausted.
- Playwright/YouTube transcript fallback fails repeatedly and no remaining queued videos can advance.
