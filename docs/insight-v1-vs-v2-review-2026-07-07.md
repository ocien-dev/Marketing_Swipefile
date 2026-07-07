# Insight v1 vs v2 Review - 2026-07-07

## Scope

- Blind sample: `data\exports\insight_v1_v2_blind_sample_2026-07-07.csv`
- Local de-anonymization key: `data\exports\insight_v1_v2_blind_key_2026-07-07.json`
- Paired sample generated: 40 pair(s).
- R08 target: 40 comparable pair(s) after R07 reaches 15 fully extracted v2 episode(s).
- Raw transcript quotes are kept only in ignored local CSV exports, not copied into this tracked report.

## Verdict

Pending blind judgment. No v1/tie/v2 score has been computed from labels or v2 self-declared fields.

## Blindness Limitation

This is label-blind, not style-blind. The A/B sample hides whether each side is v1 or v2, but the v2 format can still be recognizable because it often includes richer editorial fields. Treat this as a partial-blind review and keep the external judge separate from the extractor.

## Blind Judging Instructions

- Fill each `judgment_*` column with `A`, `B`, or `tie` while looking only at the blind CSV.
- Judge quote cleanliness using the detector columns for both sides plus the quote text itself.
- After external judging and owner authorization, run `scripts/generate_insight_v1_v2_review.py --mode score --judgments <filled_csv>` to de-anonymize and compute the score.

## Decision

- MSF-R07 reached the amended Route B coverage gate: 15 fully extracted v2 episodes and 246 target chunks.
- Stop Codex extraction at this point. Do not run `--mode score` until the blind CSV is judged externally and the owner authorizes scoring.
- Gate R1 decision remains pending external blind judgment; MSF-R14 backfill stays paused, with MSF-R03 to be reopened before post-gate chunk backfill.
