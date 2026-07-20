# MSF-R20 Gold Runtime Pilot 003 - Optimization Analysis

Status: analysis completed
Episode: `zbNLauY2D1o`
Source: 1,233 clean segments, 21 chunks and 676 prepared signals
Result: 44 unique candidates, calibration 6/4, final audit passed, fingerprints 4/4

## Executive conclusion

Quality held. The episode was read source-completely, persisted in one atomic
review write, produced an exact five-file packet and needed only one narrow
final-audit correction: removing the unsupported word `lideranca` from G008.

The certified epic took **22m45.61s**. The first failed selector attempt and the
post-completion verification sequence extend the minimum traceable interaction
to **29m25.01s**, before any unmeasured final chat-rendering time. WSL and the
deterministic gold functions were not the dominant cost. Semantic reading,
repairing a changing prelint inventory, final audit and redundant closeout were.

The ten-minute goal should remain an average for short and standard episodes,
not a universal SLA. This 1,233-segment episode can realistically reach
12-15 minutes without weakening recall. A sub-10-minute result would require an
aggressive semantic compression or parallel reading experiment and carries a
larger quality risk.

## Evidence boundary

Exact measurements come from the launcher invocations, episode session and
self-verifying completion receipt:

- certified timer: `23:36:50.518646Z` to `23:59:36.127136Z`;
- first selector attempt began at `23:36:04.667932Z` and wrote no gold;
- final read-only verifier ended at approximately `00:05:29.673Z`;
- compact source context: 177,697 bytes;
- compact-v2 payload: 37,850 bytes;
- final audit dossier: 292,674 bytes;
- seven successful core WSL launcher calls: 49.85 seconds in aggregate;
- deterministic work after source selection: approximately 1.33 seconds;
- all percentages below use the certified 22m45.61s interval.

## Measured timeline

| Stage | Measured | Share | What happened |
| --- | ---: | ---: | --- |
| Successful selection, preflight and context | 20.29s | 1.5% | Library scan selected the 1,233-segment episode and emitted the complete compact context. The durable queue now replaces this scan. |
| Integral reading and first payload | 11m00.93s | 48.4% | All 1,233 segments were read and 44 candidates across 21 reviews were composed in compact-v2 format. |
| Prelint repair loop through clean preview | 4m51.40s | 21.3% | Three prelints were needed because evidence narrowing changed the derived ledger and exposed additional risk clusters. |
| Clean preview through apply/finalizer | 23.11s | 1.7% | The internal apply, persistence, finalizer, build and dossier work took 475.77ms; launcher boundaries dominated the wall time. |
| Final audit, remediation and completion | 6m09.83s | 27.1% | Sol found the already-warned G008 lexical overreach; one asserted field update was applied before passed/0 completion. |

Outside the certified timer:

- the first selection attempt plus the retry gap added about 45.85 seconds;
- after `complete/passed`, documentation plus Verify, Sync and Verify added
  **5m53.55s** before the last recorded verifier ended;
- only 18.64 seconds of that post-completion interval was command runtime, so
  most of it was manual reconciliation and avoidable orchestration.

## What worked

1. The direct `Ubuntu-24.04/luish` route stayed Linux-native. PowerShell only
   launched `wsl.exe`; no Windows Python fallback was used.
2. Compact-v2 preserved the full transcript while avoiding repeated canonical
   review boilerplate.
3. One atomic write persisted all 21 reviews and 44 unique IDs.
4. Numbers, steps, relations, ledger, calibration and packet identity passed.
5. The audit correction was narrow and source-backed, not a recall failure.
6. CompleteAudit produced a self-verifying receipt, performance report,
   completion summary and final response automatically.

## Reduction by stage, excluding the new priority queue

### 1. Runtime preflight and context

Current residual after the queue: WSL startup, parity receipt validation and
272ms of context construction.

Target: **5-10 seconds**.

Actions:

- reuse a valid parity receipt without a separate Verify before the episode;
- keep job files Linux-native and mirror only terminal artifacts;
- treat parity validation inside the first episode command as sufficient.

### 2. Integral reading and payload composition

Observed: **11m00.93s** for 1,233 segments and 44 candidates. Compact-v2 was
already active, so further JSON shortening alone will not recover several
minutes.

Target for a similar episode: **7m30s-9m00s**.

Actions:

- add a deterministic semantic route map before the transcript: macrosections,
  chunk boundaries, numeric anchors, procedures, comparisons and high-risk
  excluded spans, each pointing to compact clean-index ranges;
- keep the full chronological transcript immediately after the route map so no
  source text is omitted;
- compose candidates section by section in the same pass, with the current
  candidate defaults and evidence selectors prefilled mechanically;
- place claim-evidence warnings beside the affected draft candidate before the
  first prelint instead of in a later global warning list.

### 3. Prelint and semantic repairs

Observed: **4m51.40s** across three prelints. Each deterministic prelint took
about 110ms; the time was spent interpreting successive inventories.

Target: **45-90 seconds**, one prelint on routine episodes.

Actions:

- compute a read-only fixed point of candidate evidence, automatic ledger and
  risk clusters before returning the inventory;
- return every acknowledgement that will become necessary after proposed
  evidence narrowing in the same response;
- require a source-based disposition for every claim-evidence warning before
  apply. The warning remains non-blocking, but it cannot remain unseen;
- make the clean prelint result directly consumable by one-shot finalization.

### 4. Preview, apply, finalizer and packet

Observed: **23.11s wall**, but only **475.77ms** inside the final operation.

Target: **6-10 seconds**.

Actions:

- after one clean prelint, use `--one-shot` as the default instead of separate
  check and apply launches;
- preserve the same preview hash, atomic recorder transaction, rollback and
  exact five-file packet checks;
- retain separate commands only for debugging a deterministic failure.

### 5. Final Sol audit and remediation

Observed: **6m09.83s**, one narrow correction. The 292,674-byte dossier exceeded
the previous 250KB navigation target, and the G008 problem had already appeared
as a prelint warning.

Target: **3-4 minutes**, normally passed on the first audit.

Actions:

- generate dossier v2 with a compact top index, candidate claim and minimal
  quote adjacent, calibration links and warning dispositions;
- avoid duplicating derived prose already recoverable from candidate IDs and
  evidence maps while retaining the complete compact transcript;
- target at most 220-250KB for a 1,200-segment episode;
- audit unresolved warning dispositions first, then perform the global source
  and recall pass.

### 6. Verification, documentation and closeout

Observed after completion: **5m53.55s** to the last verifier, despite the
completion receipt already proving lifecycle, audit, packet, fingerprints and
validation.

Target: **15-30 seconds**.

Actions:

- make a valid completion receipt the terminal authority for the episode;
- do not run Verify, Sync and Verify after `complete/passed` unless receipt
  self-validation fails or source hashes changed;
- have CompleteAudit mirror the receipt, performance report, summary and final
  response once, then stop;
- generate the retrospective from the receipt only when a new anomaly exists.

## Projected outcome

For an episode close to this size, the practical next target is:

| Stage | Target |
| --- | ---: |
| Preflight/context | 0m05s-0m10s |
| Reading/composition | 7m30s-9m00s |
| One fixed-point prelint repair | 0m45s-1m30s |
| One-shot persistence/finalization | 0m06s-0m10s |
| Final Sol audit | 3m00s-4m00s |
| Terminal closeout | 0m15s-0m30s |
| **Total** | **11m41s-15m20s** |

The current pending inventory is highly bimodal: 143 of 175 episodes have at
most 700 clean segments, while 32 have more than 1,300. Therefore:

- up to 700 segments: target 6-10 minutes;
- 701-1,300 segments: target 11-15 minutes;
- above 1,300 segments: target 18-30 minutes until a parallel-reading method is
  separately proven.

This sizing prevents a short Academy clip and a two-hour interview from being
judged by the same elapsed-time SLA. The ten-minute objective remains realistic
as an inventory average, but not for every long episode.

## Implementation priorities

### P0 - Before the next long episode

1. Fixed-point prelint inventory for evidence, ledger and risk clusters.
2. Mandatory reviewed disposition for each claim-evidence warning.
3. Enforce one-shot after clean prelint.
4. Stop immediately on a self-validating completion receipt.

### P1 - After P0

1. Audit dossier v2 with candidate-evidence adjacency and <=250KB target.
2. Deterministic semantic route map ahead of the full transcript.
3. Per-size performance budgets in the completion report.

### P2 - Controlled experiment only

Evaluate two parallel semantic readers only on a long episode and only after P0
and P1. Measure wall time, total tokens, duplicate candidates, boundary misses
and final-audit findings against the single-reader baseline. Do not make
subagents the default without a clear quality and cost win.

## Acceptance for the next measured episode

- one clean or fixed-point prelint;
- no claim-evidence warning reaches audit without a reviewed disposition;
- one one-shot persistence/finalization command;
- initial audit passed or only a genuinely new source issue;
- no post-completion Verify/Sync/Verify sequence;
- at least 98% of wall time attributed by the canonical receipt;
- exact five-file packet, fingerprints 4/4 and no reduction in recall.

## Implementation status

Implemented on 2026-07-15:

- fixed-point risk prelint with explicit `retained_support` disposition;
- stable warning IDs and source-backed dispositions carried through finalizer and packet;
- one-shot documented as the default clean route;
- dossier v2 with compact candidate columns and audit navigation;
- terminal completion receipt with no redundant verification cycle;
- size-based performance budgets in receipt and performance report;
- 120 gold Fast Path/pipeline regressions passing in the certified WSL runtime.
