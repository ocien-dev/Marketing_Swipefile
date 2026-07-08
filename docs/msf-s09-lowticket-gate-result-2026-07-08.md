# MSF-S09 Low Ticket Gate Result - 2026-07-08

Status: `PASS`

Commercial signal: PASS. The with-skill family won every pair, won 31/32
rubric cells, tied 1 proof/claim-control cell, lost 0 cells, and swept the
commercial core.

## Scope

This report scores MSF-S09 for the fourth real process skill:
`msf-process-produto-low-ticket`.

Inputs:

- Judged blind CSV:
  `data/exports/output_s09_lowticket_blind_sample_2026-07-08_judged.csv`
- Hidden key opened only after judging:
  `data/exports/output_s09_lowticket_blind_key_2026-07-08.json`
- Original blind sample:
  `data/exports/output_s09_lowticket_blind_sample_2026-07-08.csv`
- Judge: Claude Opus 4.8, external to generation.
- Blind caveat: blind de rotulo, nao de estilo.

## Key Mapping

| Pair | Briefing | A | B | Blind winner | Winner source | Encoding concern |
|---|---|---|---|---|---|---|
| S09-LOWTICKET-001 | planejamento-alimentar-desafio | sem skill | com skill | B | com skill | none |
| S09-LOWTICKET-002 | mei-mapa-caixa-minicurso | com skill | sem skill | A | com skill | none |
| S09-LOWTICKET-003 | agencia-onboarding-kit | sem skill | com skill | B | com skill | none |
| S09-LOWTICKET-004 | violao-primeira-musica-workshop | com skill | sem skill | A | com skill | none |

## Criterion Matrix

| Criterion | Pair 001 | Pair 002 | Pair 003 | Pair 004 | Total com skill | Total sem skill | Empates |
|---|---|---|---|---|---:|---:|---:|
| entry_transformation_clarity_score | com skill | com skill | com skill | com skill | 4 | 0 | 0 |
| avatar_promise_fit_score | com skill | com skill | com skill | com skill | 4 | 0 | 0 |
| scope_consumability_score | com skill | com skill | com skill | com skill | 4 | 0 | 0 |
| price_value_coherence_score | com skill | com skill | com skill | com skill | 4 | 0 | 0 |
| mechanism_belief_score | com skill | com skill | com skill | com skill | 4 | 0 | 0 |
| proof_claim_control_score | com skill | com skill | empate | com skill | 3 | 0 | 1 |
| backend_ascension_bridge_score | com skill | com skill | com skill | com skill | 4 | 0 | 0 |
| base_usage_score | com skill | com skill | com skill | com skill | 4 | 0 | 0 |

Totals:

- Pair winners: com skill 4, sem skill 0, empates 0.
- Criterion winners: com skill 31, sem skill 0, empates 1.

## Commercial Criterion

Commercial combined criterion:

- `entry_transformation_clarity_score`
- `price_value_coherence_score`
- `backend_ascension_bridge_score`

| Pair | Commercial winner | Entry transformation | Price/value | Backend bridge |
|---|---|---|---|---|
| S09-LOWTICKET-001 | com skill | com skill | com skill | com skill |
| S09-LOWTICKET-002 | com skill | com skill | com skill | com skill |
| S09-LOWTICKET-003 | com skill | com skill | com skill | com skill |
| S09-LOWTICKET-004 | com skill | com skill | com skill | com skill |

Commercial cell total: com skill 12, sem skill 0, empates 0.

Commercial pair total: com skill wins 4, sem skill wins 0, no commercial loss.

## Judge Signal

- Baselines were honest and still lost the commercial core in every pair.
- The with-skill family won entry transformation, price-value coherence, and
  backend ascension bridge in all 4 pairs.
- `proof_claim_control_score` tied in pair 003, which is a narrow neutral
  signal, not a loss.
- No recurring weak criterion was found for the with-skill outputs.

## Encoding Verification

With-skill orphan `?` scan:

- `S09-LOWTICKET-001`, B/com skill: none.
- `S09-LOWTICKET-002`, A/com skill: none.
- `S09-LOWTICKET-003`, B/com skill: none.
- `S09-LOWTICKET-004`, A/com skill: none.

The with-skill outputs contain normal pt-BR accent characters. This is not an
encoding defect under the layered writing policy, because final human-facing
outputs preserve full accentuation. No orphan question mark, mojibake, or
ASCII-stripping artifact was found in the with-skill outputs.

## No Invention

- The hidden key contains 20 with-skill citation uses.
- These resolve to 13 unique `insight_id` values.
- All 13 unique citations resolve to real `curated_insights`.
- All 13 unique citations carry `process-produto-low-ticket`.

## Verdict

`PASS`

Reason: the with-skill version satisfies the low-ticket S09 PASS condition,
winning 4/4 pairs, winning the commercial core in every pair, losing 0 total
pairs, and showing no pending encoding or No Invention defect.

Decision:

- Mark MSF-S06 as `done`.
- Mark `msf-process-produto-low-ticket` as approved.
- Release MSF-S07 (`msf-process-quiz`) as the last real skill in the first
  wave.
