# Insight v1 vs v2 Review - 2026-07-07

## Scope

- Judgments: `data\exports\insight_v1_v2_blind_sample_2026-07-07_judged.csv`
- Local de-anonymization key: `data\exports\insight_v1_v2_blind_key_2026-07-07.json`
- Paired sample scored: 40 pair(s).
- R08 target: 40 comparable pair(s) after R07 reaches 15 fully extracted v2 episode(s).
- Raw transcript quotes are not copied into this tracked report.

## Verdict

Gate R1 is formally APPROVED as of 2026-07-07 by the external judge, after independent verification that batch 006 remediation removed the duplicate-takeaway cluster and corrected evidence windows.

Blind review scored: v2 wins more judged criteria than v1. The decision accepts the judged snapshot as a pre-remediation floor, not as the final post-remediation ceiling.

## Criteria Counts

| criterion | v2_wins | ties | v1_wins |
| --- | --- | --- | --- |
| specificity | 24 | 14 | 2 |
| evidence_fidelity | 19 | 10 | 11 |
| applicability | 39 | 1 | 0 |
| quote_cleanliness | 4 | 18 | 18 |

## Interpretation Notes

- Quote_cleanliness favored v1 in the judged snapshot (`v1=18`, `v2=4`, `tie=18`). The root cause was remediated after scoring through the batch 006 duplicate-takeaway, evidence-window, and quote-noise fixes.
- Applicability should be read with discount: before de-anonymization, blind sides split A=21, B=18, tie=1. The side with richer operational fields can win by structure, so specificity and evidence_fidelity are the decisive criteria.
- The score and threshold are a pre-remediation floor. Independent post-remediation verification confirmed 0 duplicate normalized `specific_takeaway` values and corrected evidence windows.
- v1 won 11 evidence_fidelity cells. This is a positive control for the instrument: the blind judge surfaced real v2 weaknesses instead of rubber-stamping the new extraction route.
- De-anonymized pair rows reference the sample as judged; batch 006 remediation can change current v2 insight IDs or quotes after scoring.

## De-Anonymized Pair Results

| pair | episode | chunk | A_version | A_id | B_version | B_id | judged_winners |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pair_001 | 8WEvN5T7J0U | chunk_002 | v1 | 8WEvN5T7J0U-tr-insight-0003 | v2 | 8WEvN5T7J0U-v2-0001 | specificity=v2, evidence_fidelity=v2, applicability=v2, quote_cleanliness=tie |
| pair_002 | 8WEvN5T7J0U | chunk_003 | v1 | 8WEvN5T7J0U-tr-insight-0005 | v2 | 8WEvN5T7J0U-v2-0002 | specificity=v2, evidence_fidelity=v2, applicability=v2, quote_cleanliness=tie |
| pair_003 | 8WEvN5T7J0U | chunk_005 | v2 | 8WEvN5T7J0U-v2-0003 | v1 | 8WEvN5T7J0U-tr-insight-0006 | specificity=v2, evidence_fidelity=v2, applicability=v2, quote_cleanliness=v2 |
| pair_004 | 8WEvN5T7J0U | chunk_006 | v1 | 8WEvN5T7J0U-tr-insight-0009 | v2 | 8WEvN5T7J0U-v2-0004 | specificity=v2, evidence_fidelity=v2, applicability=v2, quote_cleanliness=v2 |
| pair_005 | 8WEvN5T7J0U | chunk_007 | v2 | 8WEvN5T7J0U-v2-0005 | v1 | 8WEvN5T7J0U-tr-insight-0011 | specificity=v2, evidence_fidelity=v2, applicability=v2, quote_cleanliness=tie |
| pair_006 | 8WEvN5T7J0U | chunk_009 | v2 | 8WEvN5T7J0U-v2-0006 | v1 | 8WEvN5T7J0U-tr-insight-0012 | specificity=v2, evidence_fidelity=v2, applicability=v2, quote_cleanliness=v2 |
| pair_007 | 8WEvN5T7J0U | chunk_010 | v2 | 8WEvN5T7J0U-v2-0007 | v1 | 8WEvN5T7J0U-tr-insight-0014 | specificity=v2, evidence_fidelity=v2, applicability=v2, quote_cleanliness=tie |
| pair_008 | 8WEvN5T7J0U | chunk_011 | v2 | 8WEvN5T7J0U-v2-0008 | v1 | 8WEvN5T7J0U-tr-insight-0015 | specificity=v2, evidence_fidelity=v2, applicability=v2, quote_cleanliness=tie |
| pair_009 | 8WEvN5T7J0U | chunk_013 | v2 | 8WEvN5T7J0U-v2-0009 | v1 | 8WEvN5T7J0U-tr-insight-0019 | specificity=v2, evidence_fidelity=v2, applicability=v2, quote_cleanliness=tie |
| pair_010 | 8WEvN5T7J0U | chunk_014 | v2 | 8WEvN5T7J0U-v2-0010 | v1 | 8WEvN5T7J0U-tr-insight-0022 | specificity=v2, evidence_fidelity=v2, applicability=v2, quote_cleanliness=tie |
| pair_011 | BbhJn8NXRso | chunk_001 | v2 | BbhJn8NXRso-v2-0001 | v1 | BbhJn8NXRso-tr-insight-0001 | specificity=tie, evidence_fidelity=v1, applicability=v2, quote_cleanliness=v1 |
| pair_012 | BbhJn8NXRso | chunk_002 | v2 | BbhJn8NXRso-v2-0002 | v1 | BbhJn8NXRso-tr-insight-0014 | specificity=tie, evidence_fidelity=tie, applicability=v2, quote_cleanliness=tie |
| pair_013 | BbhJn8NXRso | chunk_003 | v2 | BbhJn8NXRso-v2-0003 | v1 | BbhJn8NXRso-tr-insight-0003 | specificity=tie, evidence_fidelity=v1, applicability=v2, quote_cleanliness=tie |
| pair_014 | BbhJn8NXRso | chunk_004 | v2 | BbhJn8NXRso-v2-0004 | v1 | BbhJn8NXRso-tr-insight-0005 | specificity=tie, evidence_fidelity=v1, applicability=v2, quote_cleanliness=v1 |
| pair_015 | BbhJn8NXRso | chunk_005 | v1 | BbhJn8NXRso-tr-insight-0010 | v2 | BbhJn8NXRso-v2-0005 | specificity=tie, evidence_fidelity=tie, applicability=v2, quote_cleanliness=v1 |
| pair_016 | BbhJn8NXRso | chunk_006 | v1 | BbhJn8NXRso-tr-insight-0011 | v2 | BbhJn8NXRso-v2-0006 | specificity=v2, evidence_fidelity=tie, applicability=v2, quote_cleanliness=v1 |
| pair_017 | BbhJn8NXRso | chunk_007 | v1 | BbhJn8NXRso-tr-insight-0016 | v2 | BbhJn8NXRso-v2-0007 | specificity=tie, evidence_fidelity=v2, applicability=v2, quote_cleanliness=tie |
| pair_018 | BbhJn8NXRso | chunk_008 | v1 | BbhJn8NXRso-tr-insight-0017 | v2 | BbhJn8NXRso-v2-0008 | specificity=v1, evidence_fidelity=v1, applicability=v2, quote_cleanliness=v1 |
| pair_019 | BbhJn8NXRso | chunk_009 | v2 | BbhJn8NXRso-v2-0009 | v1 | BbhJn8NXRso-tr-insight-0020 | specificity=tie, evidence_fidelity=v1, applicability=v2, quote_cleanliness=v1 |
| pair_020 | BbhJn8NXRso | chunk_010 | v1 | BbhJn8NXRso-tr-insight-0023 | v2 | BbhJn8NXRso-v2-0010 | specificity=tie, evidence_fidelity=v1, applicability=v2, quote_cleanliness=v1 |
| pair_021 | BbhJn8NXRso | chunk_011 | v1 | BbhJn8NXRso-tr-insight-0017 | v2 | BbhJn8NXRso-v2-0011 | specificity=v2, evidence_fidelity=tie, applicability=v2, quote_cleanliness=v1 |
| pair_022 | BbhJn8NXRso | chunk_013 | v1 | BbhJn8NXRso-tr-insight-0028 | v2 | BbhJn8NXRso-v2-0012 | specificity=tie, evidence_fidelity=tie, applicability=v2, quote_cleanliness=tie |
| pair_023 | JF2oC44lBG8 | chunk_001 | v1 | JF2oC44lBG8-tr-insight-0001 | v2 | JF2oC44lBG8-v2-0001 | specificity=v2, evidence_fidelity=tie, applicability=v2, quote_cleanliness=v2 |
| pair_024 | JF2oC44lBG8 | chunk_002 | v2 | JF2oC44lBG8-v2-0002 | v1 | JF2oC44lBG8-tr-insight-0004 | specificity=v2, evidence_fidelity=v2, applicability=v2, quote_cleanliness=tie |
| pair_025 | JF2oC44lBG8 | chunk_003 | v2 | JF2oC44lBG8-v2-0003 | v1 | JF2oC44lBG8-tr-insight-0005 | specificity=v2, evidence_fidelity=v2, applicability=v2, quote_cleanliness=tie |
| pair_026 | JF2oC44lBG8 | chunk_004 | v1 | JF2oC44lBG8-tr-insight-0006 | v2 | JF2oC44lBG8-v2-0004 | specificity=v1, evidence_fidelity=v1, applicability=tie, quote_cleanliness=v1 |
| pair_027 | JF2oC44lBG8 | chunk_005 | v1 | JF2oC44lBG8-tr-insight-0017 | v2 | JF2oC44lBG8-v2-0005 | specificity=tie, evidence_fidelity=tie, applicability=v2, quote_cleanliness=tie |
| pair_028 | JF2oC44lBG8 | chunk_006 | v1 | JF2oC44lBG8-tr-insight-0004 | v2 | JF2oC44lBG8-v2-0006 | specificity=v2, evidence_fidelity=v2, applicability=v2, quote_cleanliness=tie |
| pair_029 | JF2oC44lBG8 | chunk_007 | v2 | JF2oC44lBG8-v2-0007 | v1 | JF2oC44lBG8-tr-insight-0007 | specificity=v2, evidence_fidelity=tie, applicability=v2, quote_cleanliness=tie |
| pair_030 | JF2oC44lBG8 | chunk_008 | v2 | JF2oC44lBG8-v2-0008 | v1 | JF2oC44lBG8-tr-insight-0008 | specificity=v2, evidence_fidelity=v2, applicability=v2, quote_cleanliness=v1 |
| pair_031 | JF2oC44lBG8 | chunk_009 | v2 | JF2oC44lBG8-v2-0009 | v1 | JF2oC44lBG8-tr-insight-0009 | specificity=v2, evidence_fidelity=v1, applicability=v2, quote_cleanliness=v1 |
| pair_032 | JF2oC44lBG8 | chunk_010 | v1 | JF2oC44lBG8-tr-insight-0014 | v2 | JF2oC44lBG8-v2-0010 | specificity=v2, evidence_fidelity=tie, applicability=v2, quote_cleanliness=v1 |
| pair_033 | JF2oC44lBG8 | chunk_011 | v1 | JF2oC44lBG8-tr-insight-0017 | v2 | JF2oC44lBG8-v2-0011 | specificity=tie, evidence_fidelity=tie, applicability=v2, quote_cleanliness=v1 |
| pair_034 | JF2oC44lBG8 | chunk_012 | v2 | JF2oC44lBG8-v2-0012 | v1 | JF2oC44lBG8-tr-insight-0004 | specificity=v2, evidence_fidelity=v2, applicability=v2, quote_cleanliness=tie |
| pair_035 | JF2oC44lBG8 | chunk_013 | v1 | JF2oC44lBG8-tr-insight-0020 | v2 | JF2oC44lBG8-v2-0013 | specificity=tie, evidence_fidelity=v1, applicability=v2, quote_cleanliness=v1 |
| pair_036 | JF2oC44lBG8 | chunk_014 | v2 | JF2oC44lBG8-v2-0014 | v1 | JF2oC44lBG8-tr-insight-0022 | specificity=v2, evidence_fidelity=v2, applicability=v2, quote_cleanliness=tie |
| pair_037 | JF2oC44lBG8 | chunk_015 | v2 | JF2oC44lBG8-v2-0015 | v1 | JF2oC44lBG8-tr-insight-0023 | specificity=tie, evidence_fidelity=v1, applicability=v2, quote_cleanliness=v1 |
| pair_038 | JF2oC44lBG8 | chunk_016 | v2 | JF2oC44lBG8-v2-0016 | v1 | JF2oC44lBG8-tr-insight-0024 | specificity=v2, evidence_fidelity=v2, applicability=v2, quote_cleanliness=v1 |
| pair_039 | JF2oC44lBG8 | chunk_017 | v1 | JF2oC44lBG8-tr-insight-0028 | v2 | JF2oC44lBG8-v2-0017 | specificity=tie, evidence_fidelity=v1, applicability=v2, quote_cleanliness=v1 |
| pair_040 | JF2oC44lBG8 | chunk_018 | v1 | JF2oC44lBG8-tr-insight-0030 | v2 | JF2oC44lBG8-v2-0018 | specificity=v2, evidence_fidelity=v2, applicability=v2, quote_cleanliness=v1 |

## Decision

- Gate R1 is formally approved as of 2026-07-07.
- MSF-R07 and MSF-R08 can be closed as `done`.
- Proceed next to EPIC R2: MSF-R09 evaluator LLM with rubric and citation-fidelity verification, then MSF-R10 blind test against a no-base baseline using v2 as the source. The R10 blind judgment remains external.
- Before any MSF-R14 backfill of the remaining 508 chunks, reopen MSF-R03 as scheduled.
