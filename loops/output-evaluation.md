# Output Evaluation Loop

Goal: verify that a VSL or ads package actually used the Marketing Swipe File without confusing keyword overlap with quality.

## Steps

1. Generate or select a strategy pack.
2. Create the output and include `insight_id` references in the source version.
3. Prepare a Codex-first judgment JSON with criterion scores, justification, and citation-fidelity notes from `docs/output-evaluation-rubric.md`.
4. Run:
   `scripts/evaluate_output.py --output <artifact.md> --artifact-type <vsl|ads> --strategy-pack <strategy_pack.json> --judgment-json <judgment.json> --report-json <report.json> --report-md <report.md>`
5. Treat `keyword_presence_check` as a cheap secondary proxy only; never use it as the final score.
6. For R10-style blind comparisons, use `scripts/generate_output_blind_review.py` to strip source sections, randomize A/B, write a local ignored key, and stop before external judgment.

## Done

- Source output cites `insight_id` values.
- Final report validates against `schemas/output_evaluation.schema.json`.
- Report includes per-criterion scores and justification.
- Citation fidelity checks every cited `insight_id`.
- Unsupported claims are removed, marked as hypotheses, or cause the report to fail.
