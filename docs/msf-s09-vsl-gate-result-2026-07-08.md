# MSF-S09 VSL Gate Result - 2026-07-08

Status: `PASS`

Commercial signal: PASS. The initial encoding `CONCERNS` was resolved by root
normalization fixes plus external reconfirmation of the one-character corrected
sample.

## Scope

This report scores MSF-S09 for the second real process skill:
`msf-process-copy-vsl`.

Inputs:

- Judged blind CSV:
  `data/exports/output_s09_vsl_blind_sample_2026-07-08_judged.csv`
- Hidden key opened only after judging:
  `data/exports/output_s09_vsl_blind_key_2026-07-08.json`
- Original blind sample:
  `data/exports/output_s09_vsl_blind_sample_2026-07-08.csv`
- Encoding-fixed sample for reconfirmation:
  `data/exports/output_s09_vsl_blind_sample_2026-07-08_encoding_fixed.csv`
- Judge: Claude Opus 4.8, external to generation.
- Blind caveat: blind de rotulo, nao de estilo.

## Key Mapping

| Pair | Briefing | A | B | Blind winner | Winner source | Encoding concern |
|---|---|---|---|---|---|---|
| S09-VSL-001 | doces-saude-comportamental | sem skill | com skill | B | com skill | `cansa?o` in B/com skill |
| S09-VSL-002 | b2b-propostas-diagnosticas | com skill | sem skill | A | com skill | none |
| S09-VSL-003 | financas-cheque-especial | com skill | sem skill | A | com skill | none |
| S09-VSL-004 | violao-assinatura-adultos | sem skill | com skill | B | com skill | none |

## Criterion Matrix

| Criterion | Pair 001 | Pair 002 | Pair 003 | Pair 004 | Total com skill | Total sem skill | Empates |
|---|---|---|---|---|---:|---:|---:|
| clarity_score | empate | empate | empate | empate | 0 | 0 | 4 |
| curiosity_score | com skill | com skill | com skill | com skill | 4 | 0 | 0 |
| specificity_score | com skill | com skill | com skill | com skill | 4 | 0 | 0 |
| mechanism_belief_score | com skill | com skill | com skill | com skill | 4 | 0 | 0 |
| proof_score | com skill | com skill | com skill | com skill | 4 | 0 | 0 |
| objection_handling_score | com skill | empate | empate | com skill | 2 | 0 | 2 |
| offer_bridge_score | com skill | com skill | com skill | com skill | 4 | 0 | 0 |
| base_usage_score | com skill | com skill | com skill | com skill | 4 | 0 | 0 |

Totals:

- Pair winners: com skill 4, sem skill 0, empates 0.
- Criterion winners: com skill 26, sem skill 0, empates 6.

## Commercial Criterion

Commercial combined criterion:

- `mechanism_belief_score`
- `proof_score`
- `objection_handling_score`

| Pair | Commercial result | Mechanism/belief | Proof | Objection handling |
|---|---|---|---|---|
| S09-VSL-001 | com skill wins | com skill | com skill | com skill |
| S09-VSL-002 | com skill wins | com skill | com skill | empate |
| S09-VSL-003 | com skill wins | com skill | com skill | empate |
| S09-VSL-004 | com skill wins | com skill | com skill | com skill |

Commercial cell total: com skill 10, sem skill 0, empates 2.

Commercial pair total: com skill wins 4, sem skill wins 0, no commercial loss.

## Judge Signal

- Baselines were competent, so this was a harder gate than S04.
- Clarity tied in all 4 pairs.
- Objection handling tied in 2 pairs.
- The with-skill family still won or tied every criterion in every pair and
  won the commercial core through named mechanism, proof by demonstration,
  specificity, and offer bridge.

## Encoding Verification

The artifact `cansa?o` appears in `S09-VSL-001`, output B. The hidden key maps
B to `with_s03_skill`, so this is a with-skill artifact, not baseline noise.

With-skill orphan `?` scan:

- `S09-VSL-001`, B/com skill: one orphan question mark in
  `...antes do cansa?o bater...`
- `S09-VSL-002`, A/com skill: none.
- `S09-VSL-003`, A/com skill: none.
- `S09-VSL-004`, B/com skill: none.

Legitimate punctuation question marks were ignored by the orphan scan.

Remediation applied in working tree:

- Added shared `transliterate_ascii` and `orphan_question_mark_contexts`
  helpers to `scripts/msf_common.py`.
- Extended `scripts/audit_insights_v2_text.py` to flag orphan question marks
  in generated text.
- Preserved the judged CSV unchanged.
- Wrote an encoding-fixed sample copy:
  `data/exports/output_s09_vsl_blind_sample_2026-07-08_encoding_fixed.csv`.

## Reconfirmation

External audit reconfirmed MSF-S03 after reviewing the encoding-fixed sample:

- Commercial result remains PASS: com skill won 4/4 pairs, 26 criteria, lost 0
  criteria, and tied 6.
- Commercial core remains PASS: com skill won 10 cells, sem skill won 0, and 2
  cells tied.
- The encoding-fixed sample differs from the judged original by exactly one
  character-level correction: `cansa?o` -> `cansaco`.
- The judged CSV remains preserved unchanged as audit evidence.
- Root fix is in place: `transliterate_ascii` uses Unicode NFKD transliteration
  in `scripts/msf_common.py`, and `scripts/audit_insights_v2_text.py` now flags
  orphan question marks in generated text.

## Verdict

`PASS`

Reason: the with-skill version satisfies the commercial PASS condition, winning
4/4 pairs and 10/12 commercial criterion cells without losing any pair or
criterion. The only blocker was the with-skill orphan `?` encoding artifact, and
that blocker was resolved by a one-character corrected sample plus root
normalization/audit fixes confirmed by external review.

Decision:

- Mark MSF-S03 as `done`.
- Mark `msf-process-copy-vsl` as approved.
- Release MSF-S05 (`msf-process-copy-anuncios`) as the next real skill.
- Keep MSF-S06 and MSF-S07 blocked until S05 passes its own S09.
