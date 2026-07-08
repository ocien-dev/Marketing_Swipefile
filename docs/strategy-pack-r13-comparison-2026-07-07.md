# MSF-R13 Strategy Pack Comparison - 2026-07-07

## Scope

- Regenerated low-ticket VSL and ads packs from `data/exports/curated_insights.json`.
- Compared against the previous v2 raw-base packs generated for MSF-R10.
- Evaluated the curated packs with the MSF-R09 honest evaluator as support artifacts.
- External technical review approved the R3 criteria on 2026-07-07.
- Gate R3 is formally approved.

## Inputs And Outputs

| artifact | old v2 pack | curated pack | evaluation |
| --- | --- | --- | --- |
| VSL | `data/exports/strategy_pack_v2_vsl_lowticket_2026-07-07.json` | `data/exports/strategy_pack_curated_vsl_lowticket_2026-07-07.json` | `data/exports/strategy_pack_curated_vsl_lowticket_evaluation_2026-07-07.md` |
| ads | `data/exports/strategy_pack_v2_ads_lowticket_2026-07-07.json` | `data/exports/strategy_pack_curated_ads_lowticket_2026-07-07.json` | `data/exports/strategy_pack_curated_ads_lowticket_evaluation_2026-07-07.md` |

## Diversity Comparison

| pack | old top-20 max episode | new top-20 max episode | old top-10 avg Jaccard | new top-10 avg Jaccard | old top-10 max Jaccard | new top-10 max Jaccard |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| VSL | 5 | 3 | 0.1099 | 0.1025 | 0.2500 | 0.2195 |
| ads | 10 | 3 | 0.4912 | 0.0800 | 0.6066 | 0.1811 |

## Pack Quality

| pack | result count | unique ids | process-tag coverage | honest evaluator score | decision |
| --- | ---: | ---: | --- | ---: | --- |
| curated VSL | 20 | 20 | present in pack items | 33/40 | pass |
| curated ads | 20 | 20 | present in pack items | 35/40 | pass |

## Observations

- MSF-R11 cap worked: no curated pack has more than 3 insights from the same episode in the top-20.
- The top-10 thesis cap worked: the ads pack no longer has two items with the same title-derived thesis in the top-10.
- The ads pack improved materially: the old raw v2 pack was dominated by `wHdyTM-nVqg` with 10/20 items and near-duplicate creative entries; the curated pack reduced the top episode to 3/20 and cut top-10 average Jaccard from 0.4912 to 0.0800.
- The VSL pack was already less redundant, but the curated version still enforces the episode cap, adds `process_tags`, and lowers max top-10 Jaccard.
- Curated packs expose process tags directly, which makes them better inputs for the first MSF-S skill wave after Gate R3.
- Limitation: the R09 evaluation here treats strategy packs as support artifacts, not final VSL/ad copy. It validates traceability, usefulness, and citation fidelity.

## External Review Notes

- Score calibration: `editorial_score` is compressed in the first curated lot (min 90, median 97). Calibrate the rubric with the owner sample annotations before the next lot.
- Title cleanup: one title contains a boilerplate suffix to rewrite before the next pack refresh: `...em lateralizar`.
- Coverage note: `process-copy-anuncios` has 18 curated items. This is acceptable to start MSF-S; the later backfill should expand this tag.

## Decision State

- MSF-R11, MSF-R12, and MSF-R13 are done.
- Gate R3 is approved as of 2026-07-07.
- `curated_insights` is the candidate/default source for strategy packs and the first MSF-S wave.
- Next session starts EPIC MSF-S with MSF-S01 (skill contract) and MSF-S02 (retrieval by `process_tags`).
