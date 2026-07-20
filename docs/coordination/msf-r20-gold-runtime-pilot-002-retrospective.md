# MSF-R20 Gold Runtime Pilot 002 - Retrospective

Status: completed and passed
Execution: direct in the active chat
Episode: `academyhls-4faeb011-a33d-434a-8463-b366bf0c06b8`
Title: `Modulo 2 - Aula 1 - Criando Sua Oferta`

## Result

- runtime: Ubuntu 24.04 WSL, Linux-native clone, Python, data and temp;
- source: 676 clean segments, 8 chunks and 276 prepared signals;
- context: 48,051 bytes, source-complete;
- extraction: 27 unique source-backed candidates;
- calibration: pass, 7 covered targets for minimum 3;
- deterministic gates: zero hard blockers, readiness ready, normal validator pass;
- packet: exactly five files;
- audit dossier: 111,471 bytes, source-complete and self-verifying;
- final audit: `gpt-5.6-sol/high`, passed on the initial final review with zero findings;
- lifecycle: `complete/passed`;
- protected fingerprints: 4/4 unchanged.

## Timing

The Codex epic UI reported **32m08s** from request to final response. The
instrumented episode session ran from `2026-07-15T21:18:19.382362Z` to
`2026-07-15T21:26:47.432713Z`: **508.05 seconds (8m28s)**.

Therefore, the instrumented gold core represented 26.35% of the observed epic
and **23m40s (73.65%) remained outside the episode timer**. That residual
contains episode selection, repository and contract inspection, WSL discovery,
request construction, artifact synchronization, documentation and response
composition. The current receipts do not split those activities exactly, which
is itself a telemetry defect.

| Phase | Elapsed window |
| --- | ---: |
| Certified bootstrap and compact context | 0.11s inside the Linux process |
| Integral reading and first 27-candidate payload | 4m14s |
| Two read-only inventory repairs and clean preview | 1m59s |
| Atomic apply, finalizer, packet and dossier | 26s wall window; 249ms deterministic work |
| Single final audit and complete/passed closeout | 1m49s wall window; 92ms deterministic closeout |

The first durable selector artifact was written at `18:10:25`, while bootstrap
started at `18:18:11`, proving at least 7m46s of pre-bootstrap work after that
artifact. The core completed at `18:26:47`; the Windows receipt was copied at
`18:28:17` and the retrospective was written around `18:28:49`, proving at
least another 2m02s before response composition. The remaining residual cannot
be assigned honestly because no epic-level timer existed.

## Operation count

- context generations: 1;
- read-only checks: 3;
- review applies: 1;
- review write operations: 1;
- finalizers: 1;
- builds: 2, one pending-audit build and one accepted-audit completion build;
- final audit dossiers: 1;
- audit registrations: 1;
- required-audit validations: 1.

## What worked

1. OPT-S01 removed runtime drift from the episode path. The full worktree sync
   receipt was reused with zero copies and all gold writes ran in Linux.
2. OPT-S02 reduced the complete 676-segment source to a 48 KB reading surface,
   allowing one chronological semantic pass and one episode-level payload.
3. OPT-S03 surfaced one high-risk introductory cluster. It was correctly
   acknowledged as incidental because its 40/30-minute wording described the
   previous explanation, not an offer result or target.
4. OPT-S04 reduced the final audit surface to 111 KB and the initial audit
   passed without remediation.
5. OPT-S05 closed the episode with one self-verifying receipt and generated
   summary, eliminating the previous ad hoc verifier and manual closeout.

## Friction observed

The restricted agent token returned an empty WSL distro list even though
`Ubuntu-24.04` is installed for the Windows user. Re-running `wsl.exe` in the
approved user context exposed the existing distro and clone. This was a
sandbox visibility issue, not a PowerShell or Linux processing fallback.
PowerShell remained only the Windows-side launcher; Python, gold data, packet
and audit artifacts stayed Linux-native.

The first preview found seven missing framework step lists. The second found
two numeric false positives caused by overly broad evidence and one unreviewed
risk cluster. Both inventories were repaired in memory before the only apply.
The checks consumed negligible deterministic time, but the compact payload
template should encourage framework steps by default to avoid the first loop.

Six separate WSL launcher invocations consumed 46.80s in aggregate. Most of
that time is already inside the 8m28s core and is not an explanation for the
23m40s residual, but it remains avoidable startup and parity-check overhead.

The selector, bootstrap request, receipt mirroring, retrospective and process
learning update were assembled outside the certified episode command. This
made the semantic core fast while leaving the end-to-end epic slow and partly
unobservable.

## Critical analysis

The pilot was a quality success and a partial runtime success:

- semantic reading and payload composition reached 4m14s for 676 segments;
- the first final Sol audit passed with zero findings in 1m49s;
- one atomic apply produced 27 candidates and valid 7/3 calibration coverage;
- Linux-native execution held throughout, with no Windows fallback;
- the ten-minute target was met only by the instrumented gold core;
- the complete epic missed the target by 22m08s.

The bottleneck has shifted away from deterministic gold processing. The next
optimization must target orchestration before bootstrap and after completion,
plus avoidable semantic repair loops. Reducing compiler milliseconds further
would have no material effect on the 32-minute total.

## Reduction plan

The detailed evidence, priorities and acceptance criteria are recorded in
`msf-r20-gold-runtime-pilot-002-optimization-analysis.md`.

## Decision

The optimized route proved that the gold core can finish under ten minutes on a
real 676-segment episode without reducing recall or skipping the final audit.
It did **not** prove a ten-minute end-to-end epic: the observed total was
32m08s. Implement the P0 instrumentation, selection/preflight, pre-lint and
automatic closeout improvements before the next pilot. The next acceptance
target is 10-12 minutes end to end, measured from the user's execution request
through the final response.
