# MSF-R20-GOLD-RUNTIME-PILOT-001 - Retrospectiva e plano de reducao

Status: OPT-S01 through OPT-S05 implemented; next step is a fresh real pilot
Episode: `E9nZMgzzxz4`
Date: 2026-07-15

## Objective

Explain the full 1h09m14s runtime, preserve the quality gains of the gold flow
and define concrete changes for four target intervals:

- preparation: 10 minutes to 1-2 minutes;
- semantic reading and composition: 17 minutes to 5-8 minutes;
- initial final Sol audit: 19 minutes to 5-8 minutes;
- verification and closeout: 11 minutes to 1-2 minutes.

No proposal below weakens integral reading, source-backed evidence, number
literalness, relations, ledger, calibration, fingerprints or final Sol audit.

## Observed timeline

| Phase | Observed |
| --- | ---: |
| Preparation and flow implementation | 10m31.85s |
| Context invocation | 3.68s |
| Integral reading and payload composition | 17m44.48s |
| Compiler/autocheck and pre-apply preparation | 43.30s |
| Initial one-shot finalization | 4.12s |
| Initial final Sol audit | 19m42.36s |
| Remediation 1 and focal reaudit | 6m40.86s |
| Remediation 2 and final focal reaudit | 2m18.51s |
| Accepted-audit completion | 22.64s |
| Verification, documentation and response closeout | 11m02.20s |
| Total Codex work time | 1h09m14s |

The deterministic gold code was not the bottleneck. Context generation took
23.39 ms, the one-shot pipeline took 453.84 ms and accepted-audit completion
took 146.21 ms internally. Semantic reading, audit and remediation dominated.

## Measured context and audit surface

| Artifact or view | Bytes |
| --- | ---: |
| Transcript text only | 166,792 |
| Current model context | 312,477 |
| Physical reading-context JSON | 429,751 |
| Compact lines retaining full segment IDs | 209,621 |
| Compact lines using clean-index aliases | 177,141 |
| Initial compact payload, 22 reviews and 41 candidates | 39,110 |
| Final audit bundle | 199,027 |
| Full five-file packet | 1,149,692 |

The current reading representation spends 145,685 model-facing bytes on JSON
structure beyond transcript text. Clean-index alias lines preserve all text and
timestamps while reducing the current context by 43.31%.

The final audit had a 199 KB bundle and a 433 KB transcript available, while
the complete packet was 1.15 MB. A single audit dossier made from a 177 KB
transcript view, the 39 KB semantic draft shape and a compact risk/calibration
summary can remain below 250 KB without dropping source text or candidates.

## Recall evidence

The final ledger contained 341 excluded signal-bearing segments grouped into
120 contiguous clusters. Generic review of all exclusions is too broad:

- 239 excluded segments carried `sequence`;
- 59 carried `procedure`;
- 39 carried `number`;
- 62 carried `comparison`;
- 70 carried `copy`;
- 18 carried `warning`;
- 12 carried `experiment`.

A deterministic weighted risk view reduced the 120 clusters to 18 at threshold
8. The three audit findings become mandatory regression fixtures:

1. playback-speed tactic and its 0.9x, 1.1x, 1.2x and 1.3x values;
2. argument substance being more important than the chosen structure;
3. the five-question sleep self-assessment and its qualification logic.

The risk view is a recall accelerator, not a replacement for integral reading.
It highlights likely false `low_signal` exclusions before the first packet.

## Target flow

```text
certified runtime receipt
-> one bootstrap request
-> compact source-complete transcript view
-> compact episode-level semantic draft
-> compiler plus full autocheck in memory
-> high-risk exclusion recall view
-> one atomic write and finalizer
-> one frozen compact audit dossier
-> one Sol high audit
-> one completion receipt and concise closeout
```

## P0 - Preparation from 10 minutes to 1-2 minutes

### Cause

The pilot mixed production extraction with implementation work. Before the
first context receipt it modified the launcher, context output, sync manifest
and tests, diagnosed WSL visibility and corrected an argument-binding mistake.

### Changes

1. Freeze and certify the runtime before starting the episode timer.
2. Add one `bootstrap` action that selects or accepts the episode, verifies raw
   sources, validates cached parity, prepares gold if absent and writes the
   compact context plus run manifest.
3. Pass one file-based request to WSL. PowerShell supplies only distro, user,
   cwd, Linux executable and request path; it does not forward an open-ended
   argument array.
4. Reuse a parity receipt only when manifest hash, Windows hashes and Linux
   hashes still match. Sync only changed allowlist files.
5. Generate the job-local plan, source baseline and telemetry automatically.
6. Run the full regression before runtime certification, not during each
   production episode. An episode runs only episode validators when code did
   not change.

### Budget

- cached parity and WSL preflight: 10-20 seconds;
- source and ownership checks: 15-30 seconds;
- preparation/context/run manifest: 20-40 seconds;
- total target: 60-120 seconds.

## P0 - Reading and composition from 17 minutes to 5-8 minutes

### Cause

The model read 312 KB where only 167 KB was transcript text, navigated repeated
JSON keys and full video-prefixed segment IDs, and composed review wrappers that
the compiler can derive mechanically.

### Changes

1. Add a source-complete compact format such as
   `clean_index|start_seconds|text|signal_tags`, with tags omitted when empty.
2. Use clean-index aliases in drafts. The compiler expands aliases to canonical
   segment IDs and hydrates quote text verbatim from the transcript.
3. Accept an episode-level candidate list plus explicit zero-insight chunk
   numbers. The compiler assigns candidates to chunks and creates review
   wrappers and stable IDs.
4. Precompute a literal number inventory and procedural/condition markers. The
   model confirms role and proposition or marks each item incidental; it does
   not rediscover mechanical tokens.
5. Run one semantic pass over the compact transcript and one short recall pass
   over the high-risk exclusion view before the first write.
6. Keep one compiler check and one one-shot apply. Routine enum, theme, ASCII,
   quote and number issues remain in the same in-memory correction loop.

### Budget

- ingest all compact transcript text: 2-3 minutes;
- compose semantic candidates: 2-3 minutes;
- number, calibration and risk-recall sweep: 1-2 minutes;
- total target: 5-8 minutes.

### Guard

The compact context must contain every clean segment exactly once. A test must
reconstruct the canonical ordered `(clean_index, start_seconds, text)` sequence
and prove semantic identity with `transcript_clean.json`.

## P0 - Initial Sol audit from 19 minutes to 5-8 minutes

### Cause

The auditor navigated several JSON files and repeated structures. Full recall
required transcript access, while candidate evidence, ledger and packet
integrity were distributed across the bundle and packet.

### Changes

1. Generate one frozen `final_audit_dossier.jsonl` after finalization.
2. Include the compact full transcript once, all candidate claims and semantic
   fields, evidence index ranges, number records, relations, calibration links,
   warnings, packet hashes and fingerprints.
3. Replace the 402 KB ledger body with disposition counts, referential checks
   and the compact excluded-cluster risk view. Deterministic ledger validity is
   represented by signed validator results.
4. Require the dossier to remain at or below 250 KB for this episode size.
5. Start one Sol high audit directly on the dossier and require one structured
   audit JSON response. No exploratory packet navigation or separate helper
   calls are part of the normal audit route.
6. Preserve blind provenance: the dossier contains sources, final artifacts and
   deterministic results, never executor reasoning or prior audit conclusions.

### Budget

- load and orient on one dossier: under 1 minute;
- full transcript/candidate semantic audit: 3-5 minutes;
- structured verdict and finding validation: 1-2 minutes;
- total target: 5-8 minutes.

### Guard

The dossier is an index over the frozen packet, not a substitute for it. Tests
must prove every candidate and transcript segment appears exactly once and all
packet hashes resolve to the frozen five files.

## P0 - Verification and closeout from 11 minutes to 1-2 minutes

### Cause

The accepted audit completed in under one second, but closeout added an ad hoc
Python verifier, a fingerprint-shape correction, shell quoting retries, manual
documentation edits and repeated diff/syntax checks.

### Changes

1. Make `CompleteAudit` write one canonical
   `episode_completion_receipt.json` containing status, audit, candidate count,
   calibration, exact packet names/hashes, source hashes, fingerprints, command
   metrics and the full elapsed timeline.
2. Validate the receipt inside the same Linux process before returning success.
3. Produce a compact Markdown closeout automatically from that receipt.
4. Do not create per-episode verifiers. Add a new verifier only when the public
   receipt contract itself changes, with tests in the implementation epic.
5. Do not rerun the full test suite after an episode when the certified runtime
   hash is unchanged. Run only required episode validation and `git diff
   --check` when repository files changed.
6. Update process learnings only for an actual new anomaly; routine successful
   episodes need no manual documentation edit.

### Budget

- accepted-audit build and required validator: under 15 seconds;
- final receipt and self-verification: under 15 seconds;
- generated closeout and final response: 30-60 seconds;
- total target: 60-120 seconds.

## Implementation stories

### OPT-S01 - Certified bootstrap

- Extend the WSL launcher and Linux driver with a file-based bootstrap request.
- Add cached parity validation and automatic run-manifest generation.
- Reject production start when runtime files are dirty after certification.

### OPT-S02 - Compact integral context and draft

- Add compact transcript JSONL with clean-index aliases.
- Add episode-level compact candidate input and deterministic review hydration.
- Prove transcript and quote identity.

### OPT-S03 - Pre-packet risk recall

- Add deterministic excluded-cluster scoring and lexical prominence cues.
- Require the three pilot omissions as regression fixtures.
- Keep uncertain clusters as model review items, never automatic candidates.

### OPT-S04 - Single audit dossier

- Generate a frozen dossier at finalization.
- Include complete transcript/candidate coverage and signed deterministic gates.
- Add dossier size, identity and completeness tests.

### OPT-S05 - Self-verifying completion receipt

- Consolidate accepted audit, build, required validator, source hashes, packet
  identity, fingerprints, metrics and Markdown closeout in one command.
- Remove the need for ad hoc post-completion scripts.

## Acceptance for the next pilot

- no repository code changes after the episode timer starts;
- preparation at or below 2 minutes;
- compact context at or below 190 KB and source-complete;
- reading, composition and recall at or below 8 minutes;
- high-risk view contains all three historical missed propositions;
- audit dossier at or below 250 KB and source-complete;
- initial Sol audit at or below 8 minutes;
- closeout at or below 2 minutes;
- zero hard blockers, exact five-file packet and unchanged fingerprints;
- audit passed with zero findings, or findings measured separately without
  pretending the no-remediation target was met.

## Implementation result

- OPT-S01: complete Linux-native Git clone sync, cached parity, direct
  file-based bootstrap, explicit startup stage and no Windows fallback.
- OPT-S02: source-complete compact JSONL context and episode-level compact v2
  payload with deterministic review, id and quote hydration.
- OPT-S03: excluded-cluster risk scoring plus mandatory reviewed disposition in
  the optimized route; the three historical omission patterns are fixtures.
- OPT-S04: one self-verifying JSONL audit dossier with transcript, candidates,
  calibration, warnings, risk view, packet and fingerprint identity.
- OPT-S05: one completion command emits a canonical receipt and generated
  Markdown closeout after passed audit, build and required validation.

The Linux runtime is now a complete Git clone whose current tracked and
untracked worktree is mirrored and hash-certified. The prior partial allowlist
cannot silently omit a new P0/P1 file.

## Total-time reality

The requested ranges sum to 12-20 minutes, with a midpoint of 16 minutes. They
cannot mathematically produce a ten-minute average while reading and auditing
remain sequential. The next honest milestone is 18 minutes with unchanged
quality, followed by a 12-minute stretch target. A strict ten-minute target
would require approximately 1 minute preparation, 4 minutes reading, 4 minutes
audit and 1 minute closeout, with zero remediation; that should not be promised
until two consecutive pilots prove it.
