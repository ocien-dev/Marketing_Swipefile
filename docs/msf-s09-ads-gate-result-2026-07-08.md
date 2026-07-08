# MSF-S09 Ads Gate Result - 2026-07-08

Status: `PASS`

Commercial signal: PASS. The with-skill family won every pair, won 30/32
rubric cells, tied 2 platform-fit cells, lost 0 cells, and swept the commercial
core.

## Scope

This report scores MSF-S09 for the third real process skill:
`msf-process-copy-anuncios`.

Inputs:

- Judged blind CSV:
  `data/exports/output_s09_ads_blind_sample_2026-07-08_judged.csv`
- Hidden key opened only after judging:
  `data/exports/output_s09_ads_blind_key_2026-07-08.json`
- Original blind sample:
  `data/exports/output_s09_ads_blind_sample_2026-07-08.csv`
- Judge: Claude Opus 4.8, external to generation.
- Blind caveat: blind de rotulo, nao de estilo.

## Key Mapping

| Pair | Briefing | A | B | Blind winner | Winner source | Encoding concern |
|---|---|---|---|---|---|---|
| S09-ADS-001 | fitness-meta-feed-quiz | com skill | sem skill | A | com skill | none |
| S09-ADS-002 | ia-lojistas-reels | sem skill | com skill | B | com skill | none |
| S09-ADS-003 | clinicas-google-search | com skill | sem skill | A | com skill | none |
| S09-ADS-004 | rh-display-retargeting | sem skill | com skill | B | com skill | none |

## Criterion Matrix

| Criterion | Pair 001 | Pair 002 | Pair 003 | Pair 004 | Total com skill | Total sem skill | Empates |
|---|---|---|---|---|---:|---:|---:|
| hook_strength_score | com skill | com skill | com skill | com skill | 4 | 0 | 0 |
| angle_clarity_score | com skill | com skill | com skill | com skill | 4 | 0 | 0 |
| avatar_fit_score | com skill | com skill | com skill | com skill | 4 | 0 | 0 |
| proof_or_plausibility_score | com skill | com skill | com skill | com skill | 4 | 0 | 0 |
| testability_score | com skill | com skill | com skill | com skill | 4 | 0 | 0 |
| platform_fit_score | empate | com skill | empate | com skill | 2 | 0 | 2 |
| creative_direction_score | com skill | com skill | com skill | com skill | 4 | 0 | 0 |
| base_usage_score | com skill | com skill | com skill | com skill | 4 | 0 | 0 |

Totals:

- Pair winners: com skill 4, sem skill 0, empates 0.
- Criterion winners: com skill 30, sem skill 0, empates 2.

## Commercial Criterion

Commercial combined criterion:

- `hook_strength_score`
- `proof_or_plausibility_score`
- `testability_score`

| Pair | Commercial winner | Hook | Proof/plausibility | Testability |
|---|---|---|---|---|
| S09-ADS-001 | com skill | com skill | com skill | com skill |
| S09-ADS-002 | com skill | com skill | com skill | com skill |
| S09-ADS-003 | com skill | com skill | com skill | com skill |
| S09-ADS-004 | com skill | com skill | com skill | com skill |

Commercial cell total: com skill 12, sem skill 0, empates 0.

Commercial pair total: com skill wins 4, sem skill wins 0, no commercial loss.

## Judge Signal

- Baselines were honest and still lost the commercial core in every pair.
- The with-skill family won hook strength, proof or plausibility, and
  testability in all 4 pairs.
- Platform fit tied in pairs 001 and 003, which is a recurring neutral signal,
  not a loss.
- No recurring weak criterion was found for the with-skill outputs.

## Encoding Verification

With-skill orphan `?` scan:

- `S09-ADS-001`, A/com skill: none.
- `S09-ADS-002`, B/com skill: none.
- `S09-ADS-003`, A/com skill: none.
- `S09-ADS-004`, B/com skill: none.

The with-skill outputs contain normal pt-BR accent characters. This is not an
encoding defect under the layered writing policy, because final human-facing
outputs preserve full accentuation. No orphan question mark, mojibake, or
ASCII-stripping artifact was found in the with-skill outputs.

## Verdict

`PASS`

Reason: the with-skill version satisfies the ads S09 PASS condition, winning
4/4 pairs, winning or tying the commercial core in every pair, losing 0 total
pairs, and showing no pending encoding defect.

Decision:

- Mark MSF-S05 as `done`.
- Mark `msf-process-copy-anuncios` as approved.
- Release MSF-S06 (`msf-process-produto-low-ticket`) as the next real skill.
- Keep MSF-S07 blocked until S06 passes its own S09.
