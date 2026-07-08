# Asset Processing Loop

Goal: process complementary files obtained by the user.

## Steps

1. Set the runtime data root when MSF-R03 external data is active:
   ```powershell
   $dataRoot = if ($env:MSF_DATA_DIR) { $env:MSF_DATA_DIR } else { "data" }
   ```
2. Place files in `$dataRoot\input\assets\{video_id}\`.
3. Run:
   `scripts/run_asset_pipeline.py --episode-video-id <video_id> --input-dir "$dataRoot\input\assets\<video_id>"`
4. Prepare asset extraction packets with the `asset` extractor when needed.
5. Save asset insights to `$dataRoot\processed\assets\{asset_id}\insights.json`.
6. Run classification, dedupe, audit, summaries, and consolidation.

## Done

- Raw asset metadata and original file are preserved.
- `content_segments.json` exists with page/sheet/cell/slide/section locators where possible.
- `asset_summary.md` exists.
- Asset-derived insights are linked to `episode_video_id` and `asset_id`.
