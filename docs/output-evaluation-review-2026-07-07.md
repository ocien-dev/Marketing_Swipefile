# Output Evaluation Review - 2026-07-07

## Scope

- Remediation item: MSF-R09.
- Route: Codex-first, no paid API.
- Rubric: `docs/output-evaluation-rubric.md`.
- Evaluator script: `scripts/evaluate_output.py`.
- Validation schema: `schemas/output_evaluation.schema.json`.

## Method

- The old evaluator remains available only as `keyword_presence_check`.
- Final score now requires a Codex-authored judgment JSON with criterion scores, justification, and citation-fidelity notes.
- The script loads the output, briefing, cited `insight_id` values, strategy pack, and local insight masters to attach evidence context.
- Reports are validated as JSON before markdown rendering.

## Results

| artifact | old keyword proxy | honest score | decision | delta |
| --- | --- | --- | --- | --- |
| `generated_vsl_lowticket.md` | 39/40 `pass` | 30/40 | `needs_revision` | -9 |
| `generated_ads_lowticket.md` | 37/40 `pass` | 30/40 | `needs_revision` | -7 |

## Interpretation

- The old 39/40 and 37/40 scores are not proof of value. They measured vocabulary overlap and are now classified only as keyword proxies.
- Citation fidelity was directionally acceptable for both old artifacts, but both rely on v1/heuristic material and do not place evidence close enough to the claims they make.
- The old artifacts remain useful as historical drafts, not as Release 1 proof.

## R10 Result

- Generated local ignored with-base v2 outputs:
  - `data/exports/r10_with_base_vsl_lowticket_2026-07-07.md`
  - `data/exports/r10_with_base_ads_lowticket_2026-07-07.md`
- Generated local ignored baseline outputs without base:
  - `data/exports/r10_baseline_vsl_lowticket_2026-07-07.md`
  - `data/exports/r10_baseline_ads_lowticket_2026-07-07.md`
- Prepared blind package:
  - `data/exports/output_r10_blind_sample_2026-07-07.csv`
  - `data/exports/output_r10_blind_key_2026-07-07.json`
  - `docs/output-r10-blind-review-2026-07-07.md`
- External blind judgment was later scored from `data/exports/output_r10_blind_sample_2026-07-07_judged.csv`.
- De-anonymized result: `with_base_v2=14`, `baseline_no_base=0`, `tie=2`.
- Gate R2 is approved; see `docs/output-r10-blind-review-2026-07-07.md`.

## Decision

- MSF-R09 is done.
- MSF-R10 is done.
- Gate R2 is approved; next session is EPIC R3.
