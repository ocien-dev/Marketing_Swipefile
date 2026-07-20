# MSF-R20 Gold Runtime Pilot 004 - Optimization Plan

Status: implemented
Episode: `academyhls-861b5d3a-0b6e-4547-971e-750a33985306`

## Diagnosis

The previous comparable pilot used 1,233 segments and 21 chunks. Pilot 004 used
2,349 segments and 25 chunks: only 19% more chunks, but 90.5% more transcript
segments. It is therefore comparable by chunk count, not by semantic reading
load.

The durable artifact window ran from `2026-07-16T02:41:16.245Z` to the passed
audit judgment at `2026-07-16T04:24:43.082Z` (1h43m27s). The retrospective was
written at approximately `2026-07-16T04:36:11Z`, making the observable closeout
window about 1h54m55s.

| Phase | Wall time | Main cause |
| --- | ---: | --- |
| Selection and bootstrap | 1m58s | one unsuccessful source route plus the successful selection |
| Integral reading and initial payload | 11m10s | 2,349 transcript segments and 40 initial candidates |
| Five prelint cycles and first one-shot | 24m47s | semantic repairs plus repeated WSL orchestration |
| Final audit round 1 | 9m12s | incomplete ledger surface plus six semantic findings |
| Remediation round 1 | 20m37s | no official route for updating already-complete reviews |
| Final audit round 2 | 6m40s | four residual findings |
| Remediation round 2 | 23m57s | helper construction, stale zero-draft receipt and re-finalization |
| Final audit round 3 | 7m00s | passed with zero open findings |
| Completion and documentation | 9m33s | registration, verification and manual retrospective |

The 13 recorded launcher calls consumed only 108.32 seconds in total. The first
one-shot used 754.68 ms internally and the first remediation one-shot used
687.20 ms. WSL was not the dominant cost; semantic loops and the missing
post-audit lane were.

## Decision

Do not revert the Linux-native data root, durable priority queue, compact
context, one-shot finalizer, full final dossier or single Sol audit phase.

Revert only the accidental behavior that treated a post-audit correction as a
new initial extraction. A fully reviewed episode must not re-enter the compact
pending-chunk recorder.

## Implemented Changes

### OPT-004-P0-01 - Canonical post-audit lane

`run_gold_episode_fast.py --remediate --patch <manifest>` now:

1. composes the declared patch against all existing reviews in memory;
2. runs autocheck on that composed final state before writing;
3. applies the patch transactionally once;
4. recovers idempotently when the patch receipt already proves application;
5. calls the official finalizer without an empty recorder payload;
6. emits and validates a fresh source-complete audit dossier.

Expected impact: reduce a safe post-audit correction from 20-24 minutes of
helper/orchestration work to one model edit plus a sub-second deterministic
command, normally 4-8 minutes end to end.

### OPT-004-P0-02 - Deterministic WSL environment

`invoke_gold_wsl.ps1` now launches clone, sync and runtime through
`/usr/bin/env` with Linux-only `PATH`, explicit `HOME`, UTF-8 locale and
`PYTHONNOUSERSITE=1`. WindowsApps binaries can no longer win command
resolution inside the gold route.

### OPT-004-P1-01 - Volume-proportional semantic closure

For episodes above 1,300 segments, retain the 18-30 minute performance band.
Before the first one-shot, perform one consolidated closure pass over:

- multi-value and before/after numbers;
- procedures and proof demonstrations;
- parent/child decompositions;
- high-risk excluded spans and chunk boundaries;
- speaker attribution and promotional language;
- calibration equivalence and caveats.

This is executor recall, not an intermediate audit. The target is one initial
Sol audit, not an unrealistically short first read followed by two remediations.

### OPT-004-P1-02 - Terminal closeout

Keep the completion receipt as terminal authority. After it proves audit,
packet, fingerprints and lifecycle, generate the performance summary once and
stop. Target: 1-2 minutes after the passed audit.

## New Performance Target

For an episode above 1,300 segments:

| Phase | Target |
| --- | ---: |
| Selection/bootstrap | under 30s |
| Reading and payload | 12-18m |
| Consolidated prelint/closure | 3-6m |
| One-shot deterministic work | under 30s |
| Initial final audit | 5-8m |
| Optional single remediation | 4-8m |
| Completion | 1-2m |

Expected normal total: 22-35 minutes. A universal ten-minute ceiling is not a
safe target for a 2,349-segment episode.

## Validation

- focused remediation and launcher regressions: 2 passed;
- full Fast Path regression: 103 passed;
- gold pipeline regression: 18 passed;
- combined run: 119 passed and two OneDrive lock failures; both affected tests
  passed when repeated in the native temp directory;
- Python compile without project bytecode: passed;
- PowerShell parser and flattened dry-run argv: passed;
- skill `quick_validate.py`: passed;
- `git diff --check`: passed, with existing line-ending warnings only;
- no real gold, packet, audit or fingerprint writes.
