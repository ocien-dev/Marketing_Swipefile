# Asset Processing Loop

Goal: process complementary files obtained by the user.

## Steps

1. Place files in `data/input/assets/{video_id}/`.
2. Run:
   `scripts/run_asset_pipeline.py --episode-video-id <video_id> --input-dir data/input/assets/<video_id>`
3. Prepare asset extraction packets with the `asset` extractor when needed.
4. Save asset insights to `data/processed/assets/{asset_id}/insights.json`.
5. Run classification, dedupe, audit, summaries, and consolidation.

## Done

- Raw asset metadata and original file are preserved.
- `content_segments.json` exists with page/sheet/cell/slide/section locators where possible.
- `asset_summary.md` exists.
- Asset-derived insights are linked to `episode_video_id` and `asset_id`.
