# Output Evaluation Loop

Goal: verify that a VSL or ads package actually used the Marketing Swipe File.

## Steps

1. Generate or select a strategy pack.
2. Create the output and include `insight_id` references.
3. Run:
   `scripts/evaluate_output.py --output <artifact.md> --artifact-type <vsl|ads> --strategy-pack <strategy_pack.json> --report-md <report.md>`
4. Use `docs/output-evaluation-rubric.md` for manual scoring and revision notes.

## Done

- Output cites `insight_id` values.
- Report decision is `pass` or the revision gaps are explicit.
- Unsupported claims are removed or marked as hypotheses.
