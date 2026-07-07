# Episode Processing Loop

Goal: process one YouTube episode into local Marketing Swipe File artifacts.

## Steps

1. Add or confirm URL in `data/input/youtube_urls.csv`.
2. Run:
   `scripts/run_episode_pipeline.py --url <youtube_url>`
3. If transcript fallback is needed, capture the YouTube transcript through Playwright as described in `docs/marketing-swipe-file-handoff.md`.
4. Rerun:
   `scripts/run_episode_pipeline.py --video-id <video_id> --skip-metadata --skip-transcript`
5. Extract insights:
   - v1 heuristic/current path: run or update `scripts/extract_transcript_insights.py`.
   - v2 remediation path: use the Codex-first loop below to generate `insights_v2.json`.
6. Run classification, dedupe, audit, summaries, and consolidation.

## R06 raw_insights_v2 Codex-First Loop

Use this only after MSF-R05 schema validation passes.

1. Prepare the Codex packets for selected chunks:
   `scripts/extract_transcript_insights_llm.py prepare --video-id <video_id> --chunks <chunk_numbers>`
2. Read each generated packet under:
   `data/processed/{video_id}/llm_v2_packets/`
3. Extract at most 5 high-quality insights per chunk using `prompts/extraction/base_insight_extraction_v2.md`.
4. Save chunk outputs to:
   `data/processed/{video_id}/llm_v2_outputs/chunk_###_insights.json`
5. Combine and validate:
   `scripts/extract_transcript_insights_llm.py combine --video-id <video_id>`
6. Validate final output explicitly:
   `scripts/validate_insights_v2.py data/processed/{video_id}/insights_v2.json`

Rules:

- Prefer zero insights over generic ones.
- Do not reuse v1 template titles.
- Do not use promotional or description boilerplate as evidence.
- Re-running `combine` overwrites the final file from chunk outputs and does not append duplicates.

## R07 Extraction Session Protocol

For MSF-R07, the owner decision is Route B: Codex-first, no API. A session is an extraction run, not a documentation review.

Session rules:

- Process whole episodes, one at a time.
- Minimum session target: 20 chunks processed.
- Start with already initiated episodes and strategy-pack-relevant material, especially VSL/ads: `mCaFyZpXJdE`, then `TOW0sWhPaZw`.
- During extraction, do not re-read canonical docs. The required context is only `prompts/extraction/base_insight_extraction_v2.md`, `schemas/insights_v2.schema.json`, and the chunk packet/content being processed.
- Validate every chunk output through `scripts/extract_transcript_insights_llm.py combine` plus `scripts/validate_insights_v2.py`.
- Run quote-noise checks on all new evidence. Reject or reprocess evidence containing promo CTAs, "inscreva-se", "assista tambem", hashtags, unrelated episode-title lists, or description boilerplate.
- At session close, run `scripts/consolidate_exports.py`.
- Record throughput in `docs/execution-log.md`: chunks processed, session time cost, episodes touched, insights added, validation status, and updated estimate to the amended R1 gate.
- Commit the versioned docs/scripts changed in the session. Generated `data/processed/**` and `data/exports/**` remain local ignored artifacts unless policy changes.

Amended R1 gate for Route B:

- Gate R1 requires 15-20 complete episodes by chunk, roughly 225-300 chunks.
- Prioritize episodes whose insights feed VSL/ads strategy packs plus already initiated episodes.
- The original 50-episode coverage becomes continuous post-gate work under MSF-R14.
- When the amended coverage is reached, generate the blind 40-pair sample with `scripts/generate_insight_v1_v2_review.py --mode prepare` and stop. Blind judgment happens outside Codex.

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
- R06/R1 work uses `insights_v2.json`; v1 remains intact until the v1-vs-v2 review declares the R1 gate.
