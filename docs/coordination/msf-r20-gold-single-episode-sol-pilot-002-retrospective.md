# MSF-R20 Gold Single Episode Sol Pilot 002 - Retrospective

## Outcome

- Episode: `iuBPODaMz7s`.
- Reviews: 19/19 complete with current hashes.
- Candidates: 39 unique, source-backed IDs.
- Calibration: pass, 5/4 covered targets, no duplicate target segments.
- Final audit: `gpt-5.6-sol`, `high`, `passed`, zero open findings.
- Lifecycle: `complete/passed`.
- Packet: exactly five expected files.
- Protected fingerprints: 4/4 unchanged.
- No subagents, other chats, commit, push, deploy, consolidation or Supabase.

## Measured performance

| Metric | Pilot 001 | Pilot 002 | Result |
| --- | ---: | ---: | --- |
| End-to-end elapsed | 2,279.0 s | 1,884.3 s | 17.3% faster |
| Total Linux job-local bytes | 945,320 | 683,356 | 27.7% lower |
| Active compact payload | not recorded | 39,239 bytes | compact |
| Final audit bundle | not recorded | 133,852 bytes | compact |
| Reviews | 19 | 19 | equal |
| Final candidates | not comparable | 39 | source-backed |

The active model-facing payload plus final audit bundle was 173,091 bytes,
81.7% below the pilot 001 total job-local baseline. Total job-local reduction
was smaller because recovery preserved a 339,623-byte stale ledger backup and
both pre- and post-correction audit bundles.

The official session started at `2026-07-15T15:57:00.187719Z` and the final
complete status was written at `2026-07-15T16:28:24.487125Z`. Platform token
usage and exact WSL invocation count were not exposed by a durable receipt and
are therefore `not_available`.

## Operations

- One context generation in three slabs; 1,031 cleaned segments and 19 chunks.
- Repeated read-only compiler checks; exact count was not durably recorded.
- Three recorder applies: initial packet, consolidated audit remediation, and
  one narrow follow-up required after stale derived ledger blocked finalization.
- Three finalizer calls: two ready and one blocked before build.
- Three packet builds including deterministic completion after audit.
- Two audit judgments: initial `changes_requested/3`, focal reaudit `passed/0`.
- Two official audit registrations: the open judgment and the passing reaudit.

## What worked

1. Every gold write ran in the Linux-native WSL repository, virtualenv, data
   root and temp root. The Windows `python.exe` access failure caused no data
   write and was bypassed through the established explicit `wsl.exe` route.
2. The compact preview caught schema, step, number and evidence issues before
   the first persistence. Initial deterministic hard blockers were zero.
3. The final Sol audit found three real semantic gaps that deterministic gates
   could not establish: a two-CTA cadence, a narrator-versus-Expert test result,
   and a same-proposition support gap for G014.
4. The focal remediation resolved all three findings without broad rereading.
5. Final ledger, calibration, packet identity, required-audit validation and
   protected fingerprints all passed.

## What did not work

1. Sol/high did not eliminate first-pass semantic misses. It improved the final
   result by finding three meaningful omissions, but there is no controlled A/B
   evidence that it reduced elapsed time or correction count versus another
   model.
2. After reviews changed, the finalizer trusted the old persisted derived
   ledger during pre-build autocheck. The first recovery apply wrote valid
   reviews but blocked before rebuilding the ledger. Preserving that stale
   ledger job-locally and rederiving from current evidence fixed the episode,
   but required an avoidable extra persistence.
3. The persisted monotonic start produced negative elapsed values in later WSL
   processes. WSL VM/process restarts make cross-process monotonic subtraction
   unreliable; the retrospective had to use UTC wall-clock timestamps.
4. Repeated WSL launches remained visible at roughly 3-15 seconds each. They
   were not the primary 31-minute cost, but a single long-lived Linux driver
   would remove this fixed overhead and make telemetry reliable.

## Decision

Do not start a multi-episode wave yet. Run one more comparable single episode
only after two pipeline fixes:

1. When the composed review semantic hash changes, finalizer autocheck must
   derive ledger state from current candidates instead of treating a prior
   packet ledger as final truth.
2. Cross-invocation telemetry must use UTC wall-clock anchors plus per-process
   monotonic durations, and must durably count checks, applies, finalizers,
   builds, audits and WSL launches.

Subagents are not recommended for the next pilot. The dominant work is one
chronological semantic read with shared context; parallel agents would add
merge and provenance cost before these deterministic inefficiencies are fixed.

## Deeper runtime and legacy analysis

The Windows and Linux runtime files are byte-identical at retrospective time,
but this is not yet durable. The P0/P1 implementation remains a dirty change in
both checkouts: 908 inserted and 52 removed lines across the active runtime
surface are not present in the tracked remote commit. The pilot recovered by
copying selected files before execution. A new clone, reset, or incomplete copy
could silently run the older pipeline again.

The WSL identity was not the problem. Direct read-only probes confirmed:

- Ubuntu distribution: `Ubuntu-24.04`;
- effective user: `uid=1000(luish)`;
- `/etc/wsl.conf`: `default=luish`, `systemd=true`;
- user systemd state: `running`.

The failures came from nested parsing. Inline commands crossed PowerShell,
`wsl.exe`, `bash -lc`, and a second shell utility. Variables, command
substitutions, pipes, newline escapes and `jq` filters were interpreted at the
wrong layer. The permanent route is direct `wsl.exe --exec` with separate
arguments and a Linux Python orchestrator for multi-step work, never inline
shell composition.

The legacy extraction should be isolated, not deleted now. There are 91
`insights_v2.json` files totaling only 5,137,377 bytes (4.9 MiB), including
117,698 bytes for this episode. Deleting them would not materially improve
runtime. Their current downstream roles include `insights_v2_master`, curated
retrieval, strategy packs, protected fingerprints and rollback. Gold execution
should stop reading their content immediately, while deletion waits for a
separate migration that rebuilds and validates every downstream consumer.
