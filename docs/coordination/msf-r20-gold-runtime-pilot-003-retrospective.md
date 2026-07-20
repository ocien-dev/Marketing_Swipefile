# MSF-R20 Gold Runtime Pilot 003 - Retrospective

Status: completed and passed
Execution: direct in the active chat
Episode: `zbNLauY2D1o`
Title: `Os Segredos Para Criar Um Negocio De 9 Digitos | Bruno Simantob - Segredos da Escala #104`

## Result

- runtime: Ubuntu 24.04 WSL with explicit distro and user;
- source: 1,233 clean segments, 21 chunks and 676 prepared signals;
- context: 177,697 bytes, source-complete;
- extraction: 44 unique source-backed candidates;
- calibration: pass, 6 covered targets for minimum 4;
- deterministic gates: zero hard blockers, readiness ready and validators pass;
- persistence: one atomic review write for all 21 chunks;
- packet: exactly five files;
- final audit: `gpt-5.6-sol/high`, passed after one narrow source-claim remediation;
- lifecycle: `complete/passed`, zero open findings;
- protected fingerprints: 4/4 unchanged.

## Timing

The durable timer ran from `2026-07-15T23:36:50.518646Z` through generated
closeout at `2026-07-15T23:59:36.127136Z`: **22m45.61s**.

| Phase | Elapsed window |
| --- | ---: |
| Selection, bootstrap and compact context | 20.29s |
| Integral reading and first 44-candidate payload | 11m00.93s |
| Three prelint repairs and official preview | 5m14.40s |
| Atomic apply, finalizer, packet and first dossier | 23.11s |
| Final audit, one-field remediation and audited closeout | 6m09.83s |

The initial selector request for 800-1,200 segments found no eligible episode
and wrote no gold state. The successful retry widened the range to 500-1,600
and selected the closest available episode at 1,233 segments. That failed
selection happened before the durable timer above, so the full interaction was
slightly longer than 22m45.61s.

## What worked

1. The explicit `Ubuntu-24.04/luish` route held end to end. PowerShell only
   launched `wsl.exe`; Python, data, temp, packet and audit work stayed Linux.
2. The compact context preserved all 1,233 transcript segments and supported a
   single chronological reading pass.
3. Prelint prevented all compiler, numeric and recall blockers from reaching
   the only review write.
4. All 21 reviews persisted atomically in one operation, with 44 unique IDs.
5. CompleteAudit generated a self-verifying receipt, performance report,
   summary and final response automatically.

## Friction observed

The strict default selector band stopped instead of offering the nearest safe
candidate only 33 segments above the limit. Selection should rank a bounded
fallback and expose the deviation rather than require a manual retry.

Risk acknowledgements appeared in two waves because the automatic ledger
preview changed after evidence was narrowed. Read-only checks are cheap, but
the semantic repair loop cost 4m38s between the first and third prelint. The
prelint inventory should compute the stable fixed point of evidence, ledger and
risk clusters in one report.

The first prelint already warned that G008 had weak lexical alignment. The
final audit correctly found that only the word `lideranca` was unsupported and
removed it with one asserted patch. Audit warnings must remain non-blocking,
but the executor should inspect every claim-evidence warning before the only
apply when the correction is this local and source-backed.

## Decision

P0 materially improved observability and removed the large unmeasured residual:
the complete certified episode now has one timer and automatic closeout. It did
not reach the 10-12 minute end-to-end target on a 1,233-segment episode. The
next optimization should focus on stable one-pass prelint inventory and a
bounded nearest-candidate selector fallback; deterministic processing is
already sub-second and is no longer the meaningful bottleneck.
