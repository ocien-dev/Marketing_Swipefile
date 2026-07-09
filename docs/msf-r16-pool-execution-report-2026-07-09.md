# MSF-R16 Pool Retrieval Execution Report

Date: 2026-07-09

Mode: executed through Phase 5, approved by owner audit, and committed as
code/docs only. External data remains local-only.

Runtime data root: `MSF_DATA_DIR=C:\MSF-data\Marketing_Swipe_File`.

## External Backup

Official successful backup snapshot:

`C:\MSF-data\Marketing_Swipe_File\exports\_snapshots\msf-r16-option2-2026-07-09_113257`

Rollback files:

| File | Rollback snapshot |
| --- | --- |
| `exports/insights_v2_master.json` | `insights_v2_master_bak_2026-07-09_113257.json` |
| `exports/curated_insights.json` | `curated_insights_bak_2026-07-09_113257.json` |

Hashes:

| File | Pre-R16 SHA256 | Post-R16 SHA256 |
| --- | --- | --- |
| `insights_v2_master.json` | `3f7167822feb4560b896ce3b9b364e1f8d27ac9071ca55a4bbcaeb4181084114` | `89dfee939495417367a07b6d27307e3a68d9d6b8e3a7f8c6f81f781b2e6d5b50` |
| `curated_insights.json` | `1d9a7eaf291b1febb8db140d38fc1235807f37ba7c16df6248aa8787329d18e4` | `1d9a7eaf291b1febb8db140d38fc1235807f37ba7c16df6248aa8787329d18e4` |
| `curated_insights_gate_snapshot_2026-07-08.json` | N/A | `1d9a7eaf291b1febb8db140d38fc1235807f37ba7c16df6248aa8787329d18e4` |

Two earlier attempted snapshots were created while calibrating the traceability
guard. Both aborted before replacing the live master. The live master hash
remained `3f7167822feb4560b896ce3b9b364e1f8d27ac9071ca55a4bbcaeb4181084114`
until the successful run above.

## Consolidated Pool

| Metric | Count |
| --- | ---: |
| Previous live `insights_v2_master` | 207 |
| R14 additions appended | 436 |
| Final `insights_v2_master` | 643 |
| R14 episodes | 35 |
| R14 chunks | 508 |
| `insight_id` collisions | 0 |

Additional normalization:

- Applied two internal-field NFKD fixes: `crenca` and `forca`.
- Preserved `evidence.quote_original` verbatim.
- Filled missing top-level `episode_video_id` on R14 insights from
  `evidence.episode_video_id` or the `insight_id` prefix. This keeps
  `--episode-cap 3` meaningful for pool retrieval instead of grouping new
  insights under `unknown`.

## Recomputed Scores

The R14 manual scores were discarded. All 643 items were re-scored through the
validated `generate_curated_insights.py` scorer logic and written back to
`editorial_score`.

| Metric | Value |
| --- | ---: |
| Count | 643 |
| Min | 88 |
| P25 | 94 |
| Median | 96 |
| P75 | 97 |
| Max | 100 |
| Average | 95.57 |
| `<80` | 0 |
| `80-84` | 0 |
| `85-89` | 2 |
| `90-94` | 208 |
| `95-100` | 433 |

## Floor Proposal

Recommendation: use `--min-editorial-score 90` for pool retrieval.

Rationale: it preserves the current curated quality bar, keeps 641/643 items,
and does not materially reduce first-wave skill coverage. No floor below 80 was
set or recommended.

| Floor | Total survivors | oferta | vsl | ads | low-ticket | quiz |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `>=80` | 643 | 207 | 253 | 126 | 78 | 36 |
| `>=85` | 643 | 207 | 253 | 126 | 78 | 36 |
| `>=90` | 641 | 205 | 252 | 125 | 78 | 36 |

## Coverage Before/After

| Skill tag | Curated-125 | Pool-643 |
| --- | ---: | ---: |
| `process-construcao-oferta` | 68 | 207 |
| `process-copy-vsl` | 51 | 253 |
| `process-copy-anuncios` | 18 | 126 |
| `process-produto-low-ticket` | 29 | 78 |
| `process-quiz` | 20 | 36 |

## Guards

Final live `insights_v2_master.json` guard results:

| Guard | Result |
| --- | ---: |
| Internal non-ASCII | 0 |
| Mojibake `?`, `??`, U+FFFD | 0 |
| Missing `process_tags` | 0 |
| Missing `claim_risk` | 0 |
| Missing evidence | 0 |
| Evidence traceability quote -> segment span | 1117/1117 |

Traceability supports exact matches and whitespace-normalized matches across
segment spans like `episode-transcript-0318..episode-transcript-0323`.

## Retrieval Changes

Implemented `--source pool` in:

- `scripts/search_insights.py`
- `scripts/generate_strategy_pack.py`

The pool source resolves to:

`C:\MSF-data\Marketing_Swipe_File\exports\insights_v2_master.json`

Also added:

- Explicit `pool_unavailable` retrieval state.
- Optional `--min-editorial-score`.
- `editorial_score` in strategy-pack output items for audit.
- `construcao-oferta` task alias.
- Contract `source_layer` enum allowing `v2_master_pool`.
- Template and 5 approved skills updated from curated source to pool source,
  preserving `blind_baseline_test=pass` and approved status.

## Smoke Packs

Smoke outputs were generated under:

`C:\Users\luish\AppData\Local\Temp\msf-r16-pool-smoke`

All smokes used `--source pool --min-editorial-score 90 --episode-cap 3
--thesis-cap 1 --diversity-weight 0.3`.

| Skill | Results | No Invention | Encoding | Traceability | Selected score range | Max per episode |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| `construcao-oferta` | 20 | 0 missing / 0 wrong tag | 0 mojibake | 0 findings | 92-99 | 3 |
| `copy-vsl` | 20 | 0 missing / 0 wrong tag | 0 mojibake | 0 findings | 94-99 | 3 |
| `copy-anuncios` | 20 | 0 missing / 0 wrong tag | 0 mojibake | 0 findings | 90-99 | 3 |
| `produto-low-ticket` | 20 | 0 missing / 0 wrong tag | 0 mojibake | 0 findings | 91-99 | 3 |
| `quiz` | 20 | 0 missing / 0 wrong tag | 0 mojibake | 0 findings | 92-99 | 3 |

Top-20 primary-tag audit:

| Skill tag | Top-20 items above floor 90 | Top-20 min score |
| --- | ---: | ---: |
| `process-construcao-oferta` | 20/20 | 99 |
| `process-copy-vsl` | 20/20 | 99 |
| `process-copy-anuncios` | 20/20 | 97 |
| `process-produto-low-ticket` | 20/20 | 98 |
| `process-quiz` | 20/20 | 96 |

## Validation

Passed:

- `tests/test_msf_common_encoding.py`
- `tests/test_process_tag_retrieval.py`
- `tests/test_process_skill_contract.py`
- In-memory compile for modified retrieval/scoring scripts
- `validate_process_skill.py --require-done` on all 5 approved skills
- `validate_transversal_modules.py skills/_modules/msf-transversal-copy`

Note: direct `py_compile` was not used as a final signal because OneDrive denied
`.pyc` replacement in `scripts/__pycache__`. The in-memory compile check avoids
that known Windows/OneDrive lock path.

## Commit Closure

Owner audit approved:

1. The pool source change is acceptable without reopening blind gates.
2. `--min-editorial-score 90` is accepted as the retrieval floor for pool usage.
3. The `episode_video_id` top-level fill for R14 insights is approved as a
   consolidation fix needed by episode-cap and traceability.

The committed repo changes are code/docs only. The live external data files,
backup snapshots, and gate snapshot remain gitignored/local-only under
`C:\MSF-data\Marketing_Swipe_File`.
