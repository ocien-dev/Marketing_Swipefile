# MSF-S09 Quiz Gate Result - 2026-07-08

Status: `PASS`

Commercial signal: PASS. The with-skill family won every pair, won 32/32
rubric cells, lost 0 cells, and swept the commercial core. The initial encoding
`CONCERNS` was resolved by the hardened root guard plus external
reconfirmation of the localized encoding-fixed sample.

## Scope

This report scores MSF-S09 for the fifth real process skill:
`msf-process-quiz`.

Inputs:

- Judged blind CSV:
  `data/exports/output_s09_quiz_blind_sample_2026-07-08_judged.csv`
- Hidden key opened only after judging:
  `data/exports/output_s09_quiz_blind_key_2026-07-08.json`
- Original blind sample:
  `data/exports/output_s09_quiz_blind_sample_2026-07-08.csv`
- Encoding-fixed blind sample for reconfirmation:
  `data/exports/output_s09_quiz_blind_sample_2026-07-08_encoding_fixed.csv`
- Judge: Claude Opus 4.8, external to generation.
- Blind caveat: blind de rotulo, nao de estilo.

## Key Mapping

| Pair | Briefing | A | B | Blind winner | Winner source | Encoding concern |
|---|---|---|---|---|---|---|
| S09-QUIZ-001 | productivity-diagnostic-autonomous | com skill | sem skill | A | com skill | none |
| S09-QUIZ-002 | dental-clinic-avatar-segmentation | sem skill | com skill | B | com skill | `obje??o` in B/com skill |
| S09-QUIZ-003 | creator-low-ticket-readiness | com skill | sem skill | A | com skill | `Prot?tipo` in B/sem skill |
| S09-QUIZ-004 | skincare-product-match | sem skill | com skill | B | com skill | none |

## Criterion Matrix

| Criterion | Pair 001 | Pair 002 | Pair 003 | Pair 004 | Total com skill | Total sem skill | Empates |
|---|---|---|---|---|---:|---:|---:|
| question_diagnostic_coherence_score | com skill | com skill | com skill | com skill | 4 | 0 | 0 |
| avatar_recognition_score | com skill | com skill | com skill | com skill | 4 | 0 | 0 |
| result_personalization_score | com skill | com skill | com skill | com skill | 4 | 0 | 0 |
| mechanism_belief_score | com skill | com skill | com skill | com skill | 4 | 0 | 0 |
| proof_claim_control_score | com skill | com skill | com skill | com skill | 4 | 0 | 0 |
| offer_bridge_coherence_score | com skill | com skill | com skill | com skill | 4 | 0 | 0 |
| completion_design_score | com skill | com skill | com skill | com skill | 4 | 0 | 0 |
| base_usage_score | com skill | com skill | com skill | com skill | 4 | 0 | 0 |

Totals:

- Pair winners: com skill 4, sem skill 0, empates 0.
- Criterion winners: com skill 32, sem skill 0, empates 0.

## Commercial Criterion

Commercial combined criterion:

- `question_diagnostic_coherence_score`
- `result_personalization_score`
- `offer_bridge_coherence_score`

| Pair | Commercial winner | Diagnostic coherence | Result personalization | Offer bridge |
|---|---|---|---|---|
| S09-QUIZ-001 | com skill | com skill | com skill | com skill |
| S09-QUIZ-002 | com skill | com skill | com skill | com skill |
| S09-QUIZ-003 | com skill | com skill | com skill | com skill |
| S09-QUIZ-004 | com skill | com skill | com skill | com skill |

Commercial cell total: com skill 12, sem skill 0, empates 0.

Commercial pair total: com skill wins 4, sem skill wins 0, no commercial loss.

## Judge Signal

- Baselines were honest and still lost the commercial core in every pair.
- The with-skill family won diagnostic coherence, result personalization, and
  offer bridge coherence in all 4 pairs.
- No recurring weak criterion was found for the with-skill outputs.

## Encoding Verification

The original guard only caught a single `?` between letters and missed repeated
mid-word `?` sequences. It has been hardened in `scripts/msf_common.py` through
`orphan_question_mark_contexts`:

- Repeated mid-word mojibake: `[A-Za-z]\?+[A-Za-z]`
- Letter-attached non-final `?`: `[A-Za-z]\?+(?![\s\"'\)\]\.,;:!]|$)`

Regression coverage was added in `tests/test_msf_common_encoding.py` for both
`obje??o` and `Prot?tipo`, while preserving legitimate final question marks.

Original blind sample scan with the hardened guard:

- `S09-QUIZ-001`, A/com skill: none.
- `S09-QUIZ-002`, B/com skill: `obje??o`.
- `S09-QUIZ-003`, A/com skill: none.
- `S09-QUIZ-004`, B/com skill: none.

The hidden key maps `S09-QUIZ-002` output B to `with_skill`, so this is a
with-skill encoding concern. Root trace: the corrupted token already exists in
upstream ignored local data, including `data/exports/curated_insights.json` and
`data/processed/mCaFyZpXJdE/insights_v2.json`, so the skill inherited mojibake
from curated text that the previous guard did not catch. The strategy pack path
renders selected insight fields directly, which is why a corrupted source token
can surface in a final sample.

Encoding-fixed sample:

- `S09-QUIZ-002`, B/com skill: `obje??o` -> `objecao`
  (2 character substitutions in one localized token).
- `S09-QUIZ-003`, B/sem skill: `Prot?tipo` -> `Prototipo`
  (1 character substitution in one localized token; baseline noise).

No copy was rewritten. The correction is character-level only. The judged CSV
remains preserved with the original artifacts for audit trail.

Final scan of
`data/exports/output_s09_quiz_blind_sample_2026-07-08_encoding_fixed.csv`
found 0 mojibake hits in all outputs, including 0 in the 4 with-skill outputs.

## Reconfirmation

External audit reconfirmed MSF-S07 after reviewing the encoding-fixed sample:

- Commercial result remains PASS: com skill won 4/4 pairs, 32 criteria, lost 0
  criteria, and tied 0.
- Commercial core remains PASS: com skill won 12 cells, sem skill won 0, and 0
  cells tied.
- The hidden key maps `S09-QUIZ-002` output B to with skill, confirming that
  `obje??o` was a with-skill encoding defect.
- The encoding-fixed sample changes only two localized mojibake tokens:
  `obje??o` -> `objecao` and `Prot?tipo` -> `Prototipo`.
- No copy was rewritten; the judged CSV remains preserved unchanged as audit
  evidence.
- The hardened guard catches both mojibake forms and ignores legitimate final
  question marks.
- Final scan of the encoding-fixed sample found 0 mojibake hits.
- No Invention remains clean: 18/18 unique cited insights carry `process-quiz`.

## No Invention

- The hidden key contains 30 with-skill citation uses.
- These resolve to 18 unique `insight_id` values.
- All 18 unique citations resolve to real `curated_insights`.
- All 18 unique citations carry `process-quiz`.

## Verdict

Commercial verdict: `PASS`

Gate status: `PASS`

Reason: the with-skill version satisfies the quiz S09 commercial PASS condition,
winning 4/4 pairs, winning the commercial core in every pair, losing 0 total
pairs, and passing No Invention. The only blocker was the with-skill mojibake
encoding artifact, and that blocker was resolved by the hardened root guard,
localized encoding-fixed sample, and external reconfirmation.

Decision:

- Mark MSF-S07 as `done`.
- Mark `msf-process-quiz` as approved.
- Mark `blind_baseline_test` as `pass` in the skill contract.
- Close the first skill wave: S03, S04, S05, S06, and S07 are all
  done/approved.
- Keep backfill and agents unstarted until the owner gives the next step.
