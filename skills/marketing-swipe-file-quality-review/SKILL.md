---
name: marketing-swipe-file-quality-review
description: Review Marketing Swipe File data quality, insight evidence, deduplication, summaries, and output usage. Use when Codex needs to audit insights.json files, detect missing evidence or weak confidence, review episode/asset summaries, validate consolidated exports, or evaluate whether VSL/ad outputs cite and use the base properly.
---

# Marketing Swipe File Quality Review

## Overview

Use this skill before claiming an episode, asset, strategy pack, VSL, or ads package is MVP-ready.

## Checks

1. Parse JSON and compile scripts.
2. Run insight audit:
   `scripts/audit_insights.py --input <insights.json>`
3. Run classification and dedupe before consolidation:
   `scripts/classify_taxonomy.py --input <insights.json>`
   `scripts/dedupe_insights.py --input <insights.json>`
4. Generate summaries:
   `scripts/generate_summaries.py --all`
5. Refresh exports:
   `scripts/consolidate_exports.py`
6. Use `docs/insight-quality-checklist.md` and `docs/output-evaluation-rubric.md` for human-readable criteria.

## Quality Gates

- Zero insights without evidence in final outputs.
- At least 90% of usable insights should have source, locator, and quote.
- Low-confidence insights must be marked `needs_review` or treated as hypotheses.
- Acquisition tasks need explicit status and instruction.
- Strategy packs and generated outputs must list the `insight_id` values used.

## Failure Handling

- If JSON fails schema or audit checks, fix the data or rerun extraction before retrieval.
- If transcript is empty, use the Playwright fallback before extraction.
- If search returns too few results, report the base limitation and process more episodes/assets.
