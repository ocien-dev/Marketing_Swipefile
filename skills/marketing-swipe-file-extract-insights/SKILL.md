---
name: marketing-swipe-file-extract-insights
description: Extract, classify, deduplicate, and audit Marketing Swipe File insights from transcript chunks or complementary assets. Use when Codex needs to work with extraction packets, create insights.json files, enforce evidence-backed atomic insights, run taxonomy classification, dedupe repeated insights, and validate insight quality before consolidation.
---

# Marketing Swipe File Extract Insights

## Overview

Use this skill when turning content segments or extraction packets into `insights.json`.

## Workflow

1. Prefer chunked packets for long episodes:
   `data/processed/{video_id}/chunked_extraction_packets/{extractor}/chunk_###_packet.md`
2. Save extractor outputs to:
   `data/processed/{video_id}/chunked_insights/{extractor}/chunk_###_insights.json`
3. For asset extraction packets, use `scripts/prepare_extraction_packet.py` with `--extractor asset`.
4. After each `insights.json`, run:
   `scripts/classify_taxonomy.py --input <insights.json>`
   `scripts/dedupe_insights.py --input <insights.json>`
   `scripts/audit_insights.py --input <insights.json>`
5. Consolidate accepted outputs with `scripts/consolidate_exports.py`.

## Rules

- Every insight must be atomic, actionable, and supported by evidence.
- Keep original quotes exact.
- Use `confidence_score < 0.75` and `review_status=needs_review` for weak or inferential insights.
- Do not use insights without evidence in strategy packs or final outputs.
- Use stable `dedupe_key` values that survive reprocessing.

## Extractor Focus

- `vsl`: lead, mechanism, proof, objection, CTA, narrative structure.
- `ads`: hooks, angles, scripts, tests, creative hypotheses.
- `offer`: promise, stack, bonus, price, guarantee, urgency.
- `funnel`: acquisition path, checkout, upsell, remarketing, retention.
- `copy`: persuasion, headlines, claims, proof, objection handling.
- `ops`: production, management, execution routines.
- `asset`: frameworks, templates, spreadsheets, checklists, complete or partial copy.
