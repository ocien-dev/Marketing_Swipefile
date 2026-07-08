---
name: marketing-swipe-file-extract-insights
description: Extract, classify, deduplicate, and audit Marketing Swipe File insights from transcript chunks or complementary assets. Use when Codex needs to work with extraction packets, create insights.json files, enforce evidence-backed atomic insights, run taxonomy classification, dedupe repeated insights, and validate insight quality before consolidation.
---

# Marketing Swipe File Extract Insights

## Overview

Use this skill when turning content segments or extraction packets into `insights.json`.

## Workflow

1. Set the runtime data root when MSF-R03 external data is active:
   ```powershell
   $dataRoot = if ($env:MSF_DATA_DIR) { $env:MSF_DATA_DIR } else { "data" }
   ```
2. Prefer chunked packets for long episodes:
   `$dataRoot\processed\{video_id}\chunked_extraction_packets\{extractor}\chunk_###_packet.md`
3. Save extractor outputs to:
   `$dataRoot\processed\{video_id}\chunked_insights\{extractor}\chunk_###_insights.json`
4. For asset extraction packets, use `scripts/prepare_extraction_packet.py` with `--extractor asset`.
5. After each `insights.json`, run:
   `scripts/classify_taxonomy.py --input <insights.json>`
   `scripts/dedupe_insights.py --input <insights.json>`
   `scripts/audit_insights.py --input <insights.json>`
6. Consolidate accepted outputs with `scripts/consolidate_exports.py`.

## raw_insights_v2 Remediation Workflow

Use this path for MSF-R05/MSF-R06 and later R1 remediation. It does not replace v1 until the review gate says so.

1. Confirm the v2 schema and example validate:
   `scripts/validate_insights_v2.py schemas/examples/insights_v2.example.json`
2. Prepare Codex-first packets from existing chunks:
   `scripts/extract_transcript_insights_llm.py prepare --video-id <video_id> --chunks <chunk_numbers>`
3. Read each packet from `$dataRoot\processed\{video_id}\llm_v2_packets\`.
4. Extract at most 5 specific insights per chunk using `prompts/extraction/base_insight_extraction_v2.md`.
5. Save chunk-level JSON to `$dataRoot\processed\{video_id}\llm_v2_outputs\chunk_###_insights.json`.
6. Merge and validate:
   `scripts/extract_transcript_insights_llm.py combine --video-id <video_id>`
   `scripts/validate_insights_v2.py "$dataRoot\processed\{video_id}\insights_v2.json"`

## Rules

- Every insight must be atomic, actionable, and supported by evidence.
- Keep original quotes exact.
- Use `confidence_score < 0.75` and `review_status=needs_review` for weak or inferential insights.
- Do not use insights without evidence in strategy packs or final outputs.
- Use stable `dedupe_key` values that survive reprocessing.
- In v2, titles must be specific to the chunk. Reject generic templates such as "Expert real aumenta autoridade" unless the title names the actual mechanism or condition.
- In v2, reject evidence contaminated by "inscreva-se", "assista tambem", hashtags, episode-link lists, sponsor boilerplate, or unrelated description links.

## Extractor Focus

- `vsl`: lead, mechanism, proof, objection, CTA, narrative structure.
- `ads`: hooks, angles, scripts, tests, creative hypotheses.
- `offer`: promise, stack, bonus, price, guarantee, urgency.
- `funnel`: acquisition path, checkout, upsell, remarketing, retention.
- `copy`: persuasion, headlines, claims, proof, objection handling.
- `ops`: production, management, execution routines.
- `asset`: frameworks, templates, spreadsheets, checklists, complete or partial copy.
