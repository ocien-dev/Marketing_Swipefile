# Marketing Swipe File Contracts

These schemas define the local file contracts used before Supabase becomes the source of truth.

## Contract Files

- `metadata.schema.json`: YouTube episode metadata.
- `transcript_original.schema.json`: Raw YouTube automatic transcript.
- `content_segments.schema.json`: Normalized transcript, description, comment, or asset segments.
- `referenced_assets.schema.json`: Complementary materials mentioned in an episode.
- `acquisition_tasks.schema.json`: Manual or semi-manual actions required to obtain referenced materials.
- `asset_metadata.schema.json`: Local metadata for obtained complementary files.
- `insights.schema.json`: Atomic marketing intelligence extracted from transcripts or assets.
- `episode_summary.template.md`: Markdown template for episode summaries.
- `asset_summary.template.md`: Markdown template for complementary file summaries.

## Rules

- Every insight must include evidence.
- Every evidence item must point to an episode, asset, segment, timestamp, page, slide, or sheet/range where applicable.
- Every generated file should include `schema_version`.
- Reprocessing must not duplicate records; use `youtube_video_id`, `asset_id`, `checksum`, and `dedupe_key`.
- Keep raw and processed episode data local by default.

