# MSF-R20 Gold Runtime Pilot 002 - Optimization Analysis

Status: analysis completed
Episode: `academyhls-4faeb011-a33d-434a-8463-b366bf0c06b8`
Observed epic duration: 32m08s
Instrumented gold core: 8m28.05s
Uninstrumented residual: 23m39.95s

## Executive conclusion

The extraction itself became substantially faster and retained quality. The
episode produced 27 source-backed candidates, calibration passed at 7/3, all
deterministic gates passed, the first final Sol audit returned zero findings,
and all protected fingerprints remained unchanged.

The full epic did not meet the ten-minute objective. Only 26.35% of the Codex
wall time was covered by the certified episode session; 73.65% sat before
bootstrap or after deterministic completion. Optimizing the compiler or build
alone cannot recover that time.

## Evidence boundary

The following measurements are exact:

- Codex UI total reported by the owner: 32m08s;
- session receipt total: 508.05s;
- integral reading through first payload: 254.43s;
- two repair loops through clean preview: 118.53s;
- clean preview through apply/finalizer/dossier: 26.08s;
- final audit and accepted-audit completion: 108.90s;
- six WSL launcher calls: 46.80s in aggregate;
- first durable selector artifact to bootstrap start: at least 7m46s;
- core completion to retrospective write: at least 2m02s.

The 23m40s residual cannot be split exactly between selection, repository
inspection, WSL discovery and closeout because the epic timer began at
bootstrap. Estimates must not be presented as measured stage durations.

## What worked

1. **Linux-native runtime:** every recorded invocation has
   `windows_fallback_used=false`. PowerShell only launched WSL; Python, gold
   data, packet and audit artifacts stayed in Linux.
2. **Compact source-complete context:** 676 segments became a 48,051-byte
   chronological reading surface without omitting source text.
3. **Semantic throughput:** the full read and 27-candidate composition took
   4m14s, already close to the practical floor for careful manual semantics.
4. **Single persistence:** three repeatable read-only checks led to one atomic
   apply and one review write.
5. **Final audit surface:** the 111,471-byte dossier allowed the initial
   `gpt-5.6-sol/high` audit to pass in 1m49s with no remediation.
6. **Quality controls:** numbers, calibration, ledger, packet identity and four
   protected fingerprints all passed.

## What consumed avoidable time

1. **The epic clock started too late.** Selection, environment discovery and
   closeout were invisible to the official 8m28s measurement.
2. **Selection was ad hoc.** A job-local selector and request file were created
   before the certified runtime could begin.
3. **WSL discovery used two security contexts.** The restricted token could not
   see the user's distro, so the installed `Ubuntu-24.04` had to be confirmed
   again in user context.
4. **Six process launches repeated parity/startup work.** This cost 46.80s even
   though the runtime was already healthy.
5. **The first payload lacked predictable fields.** Seven framework candidates
   needed `steps`; the next loop repaired two broad-evidence number false
   positives and one required risk acknowledgement.
6. **Closeout was still partly manual.** Linux receipts were mirrored to the
   Windows job directory, then the retrospective, learning registry and final
   response were composed separately.

## Reduction by stage

| Stage | Observed evidence | Main waste | Next target | Required change | Acceptance proof |
| --- | ---: | --- | ---: | --- | --- |
| Epic start, selection and preflight | Part of the 23m40s residual; at least 7m46s after the first selector artifact | Ad hoc selector, contract rereads, sandbox/user WSL discovery | 45-90s | Add an official Linux `select-next` command that emits the selected episode, hashes, revision/export IDs and bootstrap request; configure and certify distro/user once; start the epic timer before selection | One command reaches a source-complete context in <=90s and records every subphase |
| Runtime bootstrap and context | 8.36s launcher; 115ms inside runtime | Process startup and repeated parity check | 5-8s | Reuse a valid parity receipt and combine selection plus bootstrap in one direct WSL invocation | One launch, no sync copies, no Windows fallback |
| Integral reading and payload composition | 4m14s | Legitimate semantic work plus manual field scaffolding | 3m30s-4m | Present chronological semantic sections, calibration targets and risk clusters in the initial context; prefill only mechanical candidate structure and a `steps` skeleton for procedural types | Full source read, equivalent recall and first payload in <=4m |
| Check and correction loops | 1m59s across three previews | Missing steps, broad evidence around numbers, late risk acknowledgement | 30-60s | Run an in-memory pre-lint before the first official check for procedural steps, literal number support, evidence-window width and required risk decisions | First official check clean on routine episodes; no reduction in blocker severity |
| Apply, finalizer, packet and dossier | 26s wall; 249ms deterministic work | Separate launcher and parity startup dominate | 8-12s | Keep clean check, apply, finalizer and dossier in one Linux process after the payload hash is fixed | One apply, one finalizer, exact five-file packet, one dossier |
| Final Sol audit and accepted closeout | 1m49s | Dossier navigation and a separate completion launch | 60-90s | Add a top-level candidate/risk index and speaker provenance to the dossier; register a passed audit and complete in the same certified runtime session | Initial audit remains blind/source-complete and completes in <=90s |
| Documentation and response closeout | At least 2m02s, plus an unknown share of residual | Receipt copying, manual metrics reconciliation and prose generation | 20-45s | Make completion mirror the canonical receipt, emit the full performance report and generate the final recap directly from verified fields; update learnings only for new anomalies | Final response cites one canonical receipt and no ad hoc verifier/doc pass is needed |

## Priorities

### P0 - Before the next pilot

1. Start a durable epic timer at the first action and stop it after closeout.
2. Implement official `select-next + bootstrap-request` generation in Linux.
3. Certify `Ubuntu-24.04` and user `luish` in the launcher so restricted-token
   discovery is never treated as runtime absence.
4. Add pre-lint for `steps`, numeric literal support, evidence width and risk
   acknowledgement before the first official preview.
5. Extend the completion receipt with selection, preflight, documentation and
   response timing, and auto-generate the closeout report.

Implementation status on 2026-07-15: **completed**.

- `SelectBootstrap` captures the start before sync and invokes official
  source-complete selection plus bootstrap without distro enumeration.
- `--prelint` returns the composed compiler/autocheck inventory without a
  preview receipt or gold write.
- the compact context now carries numeric indices, calibration indices and the
  procedural/risk draft contract without repeating transcript quotes;
- completion emits the canonical receipt, performance report, summary and
  generated final response, with an optional final-only Windows mirror;
- Windows/Linux parity passed read-only for 280 files with zero copies and zero
  conflicts after sync;
- the gold regression suite passed 113 tests.

### P1 - After the next measured pilot

1. Collapse repeated WSL startup/parity checks into one episode process where
   transactional boundaries still remain explicit.
2. Add a compact candidate/risk/calibration navigation index to the audit
   dossier.
3. Encode speaker provenance so instructor principles do not create repeated
   promo/interviewer warning inspection.
4. Mirror only final receipts from Linux to Windows automatically.

### P2 - Only if the 10-12 minute target is still missed

1. Adapt context grouping to episode length while preserving one chronological
   source-complete pass.
2. Cache stable contract/schema summaries by semantic hash.
3. Add aggregate dashboards across pilots, but never substitute aggregate
   metrics for the per-episode receipt.

## Next-pilot acceptance

The next episode should be close to 1,000 clean segments and must be measured
from the user's execute request through the final response. It passes the
runtime experiment only when all of the following hold:

- end-to-end wall time is 10-12 minutes, not merely the gold core;
- selection plus source-complete context is <=90 seconds;
- first official check is clean or requires at most one source-backed repair;
- integral semantic reading is documented and recall is not reduced;
- the first final Sol audit passes or any finding is genuinely editorial;
- one atomic apply, one finalizer and exact five-file packet;
- all protected fingerprints remain unchanged;
- the completion receipt accounts for at least 95% of the observed wall time.

## Decision

Keep the optimized gold route. Its quality and semantic throughput are proven.
Do not yet claim a ten-minute average. Implement P0, then run one measured
near-1,000-segment pilot. If the first-check and telemetry targets hold, a
10-12 minute end-to-end average becomes realistic for medium episodes.
