# MSF-R16 Consolidation Plan - Corrected Dry Run

Date: 2026-07-09

Mode: proposal only. No live base file was overwritten and no commit was made.

Runtime data root: `MSF_DATA_DIR=C:\MSF-data\Marketing_Swipe_File`.

## Correction From The First Proposal

The first proposal treated the R14 manual `editorial_score` values as comparable to the current curated scores. That was wrong.

- Current curated scores were produced by `scripts/generate_curated_insights.py` and sit at the effective curated bar of 90+.
- The 436 R14 scores were manual Rota B checkpoint scores: min 78, max 89.
- Therefore append-only selection using those manual scores would lower the curated floor from 90 to 78.

This corrected dry run ignores the manual R14 scores for selection and re-scores all 643 candidate insights through the validated curated generator.

Manual R14 scores, ignored for R16 selection:

| Bucket | Count |
| --- | ---: |
| `<80` | 5 |
| `80-84` | 317 |
| `85-89` | 114 |
| `90+` | 0 |
| **Total** | **436** |

## Dry-Run Method

1. Read live external inputs:
   - `exports/insights_v2_master.json`: 207 insights.
   - `processed/<episode_id>/insights_v2.json`: 436 new R14 insights.
   - `exports/curated_insights.json`: 125 current curated insights.
2. Build a temporary candidate master at `%TEMP%\msf-r16-preview\insights_v2_master_643_candidate.json`.
3. Apply only deterministic NFKD microfixes to the candidate, not to the live base.
4. Run the validated generator against the temporary candidate, writing only to temp files.

Preview command:

```powershell
.\.venv\Scripts\python.exe -B scripts\generate_curated_insights.py `
  --input "$env:TEMP\msf-r16-preview\insights_v2_master_643_candidate.json" `
  --output "$env:TEMP\msf-r16-preview\curated_preview.json" `
  --review-sample "$env:TEMP\msf-r16-preview\curated_preview_owner_review_sample.csv" `
  --report "$env:TEMP\msf-r16-preview\curated_preview_report.md" `
  --score-floor 90 `
  --target-count 125 `
  --min-count 0 `
  --max-count 1000 `
  --cluster-threshold 0.62 `
  --cluster-cap 3
```

Notes:

- `--score-floor 90` represents the current effective curated bar.
- `--target-count 125`, `--cluster-threshold 0.62`, and `--cluster-cap 3` preserve the R12 generator behavior.
- `--min-count 0` and `--max-count 1000` only relax the preview validation envelope; they do not change ranking, scoring, clustering, or target count.
- The curated generator uses similarity clustering plus `cluster_cap`. MMR is not implemented in this script; MMR is part of the strategy-pack retrieval layer. Cluster/cap collisions below are therefore the real collisions for this curated preview.

Generator output:

| Output | Value |
| --- | --- |
| Preview curated file | `%TEMP%\msf-r16-preview\curated_preview.json` |
| Source insights | 643 |
| Curated preview | 125 |
| Preview clusters | 120 |
| Review sample | 30 |

## Merge Candidate

Dry-run merge result:

| Check | Result |
| --- | ---: |
| Current v2 master | 207 |
| R14 additions | 436 |
| Projected v2 master candidate | 643 |
| R14 episodes represented | 35 |
| R14 chunks represented | 508 |
| Invalid source episode files | 0 |
| `insight_id` collisions current vs R14 | 0 |
| Duplicate `insight_id` in candidate | 0 |

## NFKD Microfix Before Re-Score

The candidate applies two localized internal-field transliterations before running the generator. Evidence quotes remain verbatim UTF-8.

| Insight | Field | Before | After |
| --- | --- | --- | --- |
| `mCaFyZpXJdE-v2-0008` | `insight_ptbr` | `crenca` with accented source char | `crenca` |
| `mCaFyZpXJdE-v2-0002` | `insight_ptbr` | `forca` with accented source char | `forca` |

Live base impact in this dry run: none. These changes exist only in the temp candidate.

## Recomputed Editorial Scores

Scores below were recomputed by `generate_curated_insights.py` logic over the 643 candidate insights. They do not use manual R14 checkpoint scores.

| Pool | Count | Min | P25 | Median | P75 | Max | Average |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Candidate 643 | 643 | 88 | 94 | 96 | 97 | 100 | 95.57 |
| Current 207 | 207 | 88 | 94 | 97 | 98 | 100 | 95.60 |
| New R14 436 | 436 | 91 | 94 | 96 | 97 | 100 | 95.56 |

Score buckets after re-score:

| Pool | 85-89 | 90-94 | 95-100 |
| --- | ---: | ---: | ---: |
| Candidate 643 | 2 | 208 | 433 |
| Current 207 | 2 | 56 | 149 |
| New R14 436 | 0 | 152 | 284 |

Bar 90 result:

| Pool | Cross bar 90 | Below bar |
| --- | ---: | ---: |
| Candidate 643 | 641 | 2 |
| Current 207 | 205 | 2 |
| New R14 436 | 436 | 0 |

The key corrected number: **436/436 R14 insights cross the score bar after script re-score**. The limiting factor is therefore not the score bar. It is the generator's `target-count=125`, priority ranking, and cluster cap.

## Curated Preview

Running the generator on the 643 candidate insights with bar 90 and target 125 produces:

| Metric | Count |
| --- | ---: |
| Curated preview total | 125 |
| Similarity clusters in preview | 120 |
| New R14 insights selected | 76 |
| Current-master insights selected | 49 |
| Selected old insights already in live curated | 49 |
| Selected old insights not in live curated | 0 |

Preview score distribution:

| Metric | Value |
| --- | ---: |
| Min | 91 |
| P25 | 96 |
| Median | 97 |
| P75 | 99 |
| Max | 100 |
| Average | 96.87 |
| 90-94 | 17 |
| 95-100 | 108 |

Interpretation: the script preserves an elite 125-item curated layer, but the new R14 material displaces 76 of the 125 slots. If R16 should keep all 125 previous curated items and add R14 on top, that is a different policy from the validated generator's current target-count behavior and needs owner approval.

## Process Tag Distribution In Preview

Full process-tag distribution for the 125-item curated preview:

| Process tag | Count |
| --- | ---: |
| `process-copy-vsl` | 84 |
| `process-construcao-oferta` | 80 |
| `process-mecanismo-big-idea` | 72 |
| `process-prova-depoimentos` | 46 |
| `process-produto-low-ticket` | 29 |
| `process-copy-anuncios` | 26 |
| `process-quiz` | 18 |
| `process-headlines-hooks` | 18 |
| `process-precificacao` | 17 |
| `process-argumentacao-objecoes` | 17 |
| `process-pesquisa-avatar` | 14 |
| `process-arquitetura-funil` | 10 |
| `process-validacao-oferta` | 8 |
| `process-pesquisa-mercado` | 7 |
| `process-teste-variacao-criativos` | 7 |
| `process-storytelling` | 6 |
| `process-video-anuncio` | 5 |
| `process-estrategia-negocio` | 3 |
| `process-posicionamento-marca` | 3 |
| `process-checkout` | 3 |
| `process-area-membros` | 3 |
| `process-cro-testes` | 3 |
| `process-trafego-organico` | 2 |
| `process-processos-operacao` | 2 |
| `process-escada-produtos` | 2 |
| `process-lancamento` | 2 |
| `process-metricas-analise` | 2 |
| `process-planejamento-campanha` | 1 |
| `process-gestao-time` | 1 |
| `process-analise-concorrencia` | 1 |
| `process-ia-marketing` | 1 |
| `process-financas-margem` | 1 |
| `process-copy-carta-vendas` | 1 |
| `process-assinatura-recorrencia` | 1 |
| `process-producao-vsl-player` | 1 |
| `process-copy-paginas` | 1 |

First-wave skill tags:

| Skill process tag | Preview total | New R14 contribution |
| --- | ---: | ---: |
| `process-construcao-oferta` | 80 | 41 |
| `process-copy-vsl` | 84 | 58 |
| `process-copy-anuncios` | 26 | 21 |
| `process-produto-low-ticket` | 29 | 17 |
| `process-quiz` | 18 | 5 |

## Real Cluster And Cap Collisions

These numbers come from the generator's similarity clustering, not from a prefixed `dedupe_key` approximation.

All 643 candidate insights:

| Metric | Count |
| --- | ---: |
| Similarity clusters | 599 |
| Multi-item similarity clusters | 8 |
| Items collapsed by similarity | 44 |
| Mixed old+new clusters | 0 |
| New-only clusters | 436 |
| Old-only clusters | 163 |
| New items inside old clusters | 0 |

Eligible pool at score >= 90:

| Metric | Count |
| --- | ---: |
| Eligible similarity clusters | 599 |
| Eligible multi-item clusters | 8 |
| Eligible items collapsed by similarity | 42 |

Selected curated preview:

| Metric | Count |
| --- | ---: |
| Selected items | 125 |
| Selected similarity clusters | 120 |
| Selected multi-item clusters | 3 |
| Extra selected items in already selected clusters | 5 |
| Max selected items per cluster | 3 |
| Items skipped by `cluster_cap=3` before target filled | 15 |

Interpretation: R14 does not collide with the old master by similarity. The cap still matters because some high-ranking old/internal clusters have enough items to trigger `cluster_cap=3`.

## New R14 Entrants By Episode

This table counts new R14 insights selected into the 125-item curated preview, not merely insights crossing score 90.

| Episode | Chunks | New insights | Selected into preview |
| --- | ---: | ---: | ---: |
| `-8mIBnJwDXo` | 16 | 12 | 5 |
| `35uL_nCmZ0k` | 10 | 10 | 0 |
| `4Ad8K3xIX4g` | 10 | 10 | 0 |
| `7sa0JIa4RaQ` | 11 | 10 | 0 |
| `9Iahajs5RDU` | 16 | 13 | 0 |
| `9jZvoPzaXR4` | 18 | 15 | 1 |
| `CfeU1dmgfYw` | 15 | 10 | 2 |
| `E9nZMgzzxz4` | 14 | 19 | 8 |
| `EG-YXLmJqAs` | 15 | 12 | 0 |
| `FF57kVKru3Y` | 17 | 13 | 0 |
| `GSSh_3RoU98` | 13 | 11 | 4 |
| `K8THfJoNWKU` | 23 | 12 | 2 |
| `M9GCw_ojfwk` | 21 | 12 | 1 |
| `NlZ4rbm2Jvs` | 14 | 15 | 2 |
| `S3Cvlf5jH2E` | 16 | 13 | 4 |
| `VQJ_Y8E6Hw0` | 11 | 11 | 5 |
| `W734UsIuOCI` | 14 | 12 | 3 |
| `Z9GyOMD1MiE` | 14 | 14 | 0 |
| `_hXmiIEac6w` | 15 | 10 | 4 |
| `a7BV6Ckbm6E` | 15 | 11 | 1 |
| `aFabW0i9K20` | 12 | 12 | 3 |
| `awbrqeqq-io` | 10 | 10 | 2 |
| `b1R3cnLXdks` | 15 | 12 | 0 |
| `ccdmYIGYob0` | 15 | 17 | 7 |
| `icryHLwikKw` | 8 | 10 | 0 |
| `iuBPODaMz7s` | 19 | 23 | 8 |
| `jxHiJHkPL8M` | 18 | 15 | 0 |
| `mvjE0UR5aVc` | 15 | 10 | 0 |
| `ngHQnIq3Y2s` | 10 | 10 | 0 |
| `pj5A6KEFkKM` | 14 | 14 | 7 |
| `r8DCWt6blio` | 19 | 12 | 0 |
| `rx1uxvGrakk` | 19 | 16 | 4 |
| `uOueeXlYs9Y` | 12 | 10 | 0 |
| `z0adfyWscI0` | 12 | 10 | 3 |
| `zbNLauY2D1o` | 12 | 10 | 0 |
| **Total** | **508** | **436** | **76** |

## Projected Guards

Guards on the 643-item candidate after NFKD microfix:

| Guard | Result |
| --- | ---: |
| Internal non-ASCII | 0 |
| Mojibake `?`, `??`, U+FFFD | 0 |
| Missing `process_tags` | 0 |
| Missing `claim_risk` | 0 |
| Missing evidence | 0 |
| Evidence traceability quote -> segment span | 1117/1117, 100% |

Guards on the 125-item curated preview:

| Guard | Result |
| --- | ---: |
| Internal non-ASCII | 0 |
| Mojibake `?`, `??`, U+FFFD | 0 |
| Missing `process_tags` | 0 |
| Missing `claim_risk` | 0 |
| Missing evidence | 0 |
| Evidence traceability quote -> segment span | 174/174, 100% |

Traceability note: span references like `episode-transcript-0004..episode-transcript-0011` were expanded before matching `evidence.quote_original` against `text_original`.

## Owner Decision Needed

The corrected dry run does not show a "many below bar" problem. It shows a selection-policy problem:

- Re-scored R14 is strong enough for the current bar: 436/436 cross 90.
- The validated generator still outputs only 125 curated items.
- Under that elite-125 policy, 76 new R14 insights enter and 49 current curated insights remain.

Trade-off options:

1. Elite curated stays narrow: accept the generated 125-item preview as the new curated layer and use the 643-item v2 master as the broad retrieval pool.
2. Preserve prior curated plus add R14: change policy to append/expand curated, but this intentionally departs from current `target-count=125`.
3. Keep curated production-safe and create a second broad layer, for example `retrieval_pool_v2`, from the 643 master for exploratory agents or lower-risk strategy-pack recall.

No bar should be lowered. If anything changes, the choice is target size, retrieval layer, or editorial policy.

## Snapshot And Rollback Plan

Before any future execution that writes external data, create:

`C:\MSF-data\Marketing_Swipe_File\exports\_snapshots\msf-r16-YYYYMMDD-HHMMSS\`

Snapshot contents:

- `insights_v2_master.json`
- `curated_insights.json`
- `manifest.sha256`
- `r16_projection_summary.json`

Current live fingerprints captured before this dry run:

| File | Bytes | SHA256 |
| --- | ---: | --- |
| `insights_v2_master.json` | 968913 | `3f7167822feb4560b896ce3b9b364e1f8d27ac9071ca55a4bbcaeb4181084114` |
| `curated_insights.json` | 555280 | `1d9a7eaf291b1febb8db140d38fc1235807f37ba7c16df6248aa8787329d18e4` |

Required pre-write checks:

1. Snapshot files exist and hashes match the live files before rewrite.
2. Candidate master count is exactly 643.
3. Curated candidate count and policy match the owner decision.
4. `insight_id` duplicates = 0.
5. Mojibake = 0.
6. Internal non-ASCII = 0 after deterministic NFKD microfixes.
7. Traceability = 100%.
8. `process_tags`, `claim_risk`, and evidence are present for every item.
9. Strategy-pack smoke confirms the selected retrieval source reads from `MSF_DATA_DIR`.

Rollback:

1. Stop downstream pack/skill generation.
2. Copy snapshot files back over the live external files.
3. Recompute hashes and compare with `manifest.sha256`.
4. Rerun retrieval smoke against `curated_insights.json`.
5. Record rollback in `docs/execution-log.md` before any new attempt.

## Proposed Execution After Owner Approval

Recommended execution sequence once the owner chooses the policy:

1. Snapshot current live external master and curated files.
2. Build the 643-item candidate.
3. Apply the two deterministic NFKD microfixes.
4. Run `generate_curated_insights.py` with the owner-approved policy.
5. Run candidate guards.
6. Only then replace the live external files.
7. Regenerate strategy packs from the selected retrieval source.
8. Update execution log and backlog.

No commit is proposed until after the owner approves the policy and the external data rewrite is actually executed and verified.
