# MSF-R20-GOLD-SINGLE-EPISODE-SOL-PILOT-002

Status: completed - final quality passed; performance classified red
Execution: direct in the active chat, without subagents or other chats
Model: `gpt-5.6-sol` with reasoning `high` for the entire epic
Runtime: WSL 2 with Linux-native repository, virtualenv, data and temp roots
Scope: one selected episode, `iuBPODaMz7s`

## Objective

Validate the P0/P1 gold optimizations on one real episode comparable to the
first Sol pilot. The epic must preserve full semantic recall while reducing the
end-to-end elapsed time, repeated context and post-write correction surface.

The target path is one complete chronological read, one clean in-memory
preview, one atomic persistence, one finalizer and one final Sol audit. There
are no intermediate audits, subagents, coordinator/worker handoffs, chunk
checkpoints or provisional packets.

This document only selects and plans the episode. Creating this plan does not
authorize preparation, review persistence, build, packet generation or audit.

## Selected episode

The episode is fixed before execution:

- `video_id`: `iuBPODaMz7s`;
- title: `Fazendo Criativos Que Vendem Milhoes Na Pratica | Tiago Filemon - Segredos da Escala #046`;
- duration: 8,229 seconds, approximately 137.2 minutes;
- raw transcript: available, 1,071 source segments;
- current clean source: 1,071 segments;
- expected chunk load: 17 chunks under the current 12,000-character and
  600-second canonical boundaries;
- current gold state in the read-only safety mirror: no `gold_extraction`
  directory and no isolated export;
- subject surface: creative strategy, direct-response advertising, testing,
  hooks, copy and scaling, which gives the pilot a strong semantic exercise;
- comparison baseline: the first pilot had 1,067 segments and 19 chunks, so
  this episode is close enough for a useful performance comparison.

Execution identifiers are fixed:

- `revision_id`: `single-sol-iuBPODaMz7s-final-001`;
- `export_suffix`: `msf_r20_gold_single_sol_pilot_002_iuBPODaMz7s`;
- Linux job root:
  `/home/luish/.cache/msf/jobs/MSF-R20-GOLD-SINGLE-EPISODE-SOL-PILOT-002`;
- repository receipt mirror:
  `.codex-work/worker-jobs/MSF-R20-GOLD-SINGLE-EPISODE-SOL-PILOT-002`.

Selection evidence was collected read-only from the Windows safety mirror on
2026-07-15:

| Source | Physical SHA-256 | Bytes |
| --- | --- | ---: |
| `raw/youtube/iuBPODaMz7s/metadata.json` | `496942F3418C9B40CBE01485EEC3F17468844ED8C3C23F9DFB903607B3366602` | 4,357 |
| `raw/youtube/iuBPODaMz7s/transcript_original.json` | `9D93AD72CBE963D74E4D530AB3FBD3141FE9A4208076A4BA030131F73DDD6585` | 291,095 |
| `processed/iuBPODaMz7s/content_segments.json` | `3C3B2E8895969EA6122163048AEA39742F076EEEC1B0C9D3035C86DBBA20ACEF` | 597,132 |

The three source documents identify `iuBPODaMz7s`, metadata reports
`transcript_status=available`, and raw and clean counts both equal 1,071.

The current Windows agent context returned no registered WSL distribution from
`wsl.exe --list --quiet`. Therefore, execution story SP2-S01 must first prove
that the canonical WSL distribution and Linux-native data root are visible and
that their source hashes match this selection. A mismatch or missing Linux
source stops before any episode write; Windows gold execution is not a
fallback.

## Pilot hypothesis

The P0/P1 route should remove the largest costs observed in pilot 001:

1. late discovery of numeric blockers after persistence;
2. verbose full-state recall artifacts;
3. episode-specific correction helpers and audit probes;
4. repeated Windows/WSL process and filesystem crossings;
5. multiple persistence, patch and build operations.

For an episode near 1,000 segments, the operational target is 12 to 18 minutes.
Ten minutes remains a stretch target, not a quality-compromising hard cap.

## Non-negotiable rules

- Use `gpt-5.6-sol/high` for source reading, composition, recall, correction and
  final audit.
- Use only the active chat. Do not create subagents, other chats, handoffs,
  heartbeat or continuation automation.
- Use the canonical Linux-native WSL repository, `.venv`, data root, temp and
  job directory for every gold operation.
- Do not use Windows Python, PowerShell gold writes, `/mnt/c` job-local files or
  a Windows data fallback.
- Preserve quotes byte-for-byte. Normalize only internal editorial fields under
  the current contract.
- Read all chunks and adjacent boundaries before the first persistence.
- Run the official compact compiler and autocheck against the composed state in
  memory. Persist only when `hard_blockers=0`.
- Keep audit warnings visible. Do not rewrite source-backed claims merely to
  make an ambiguous calibration target pass.
- Generate no provisional packet. The only pre-audit packet is the finalizer's
  exact five-file packet.
- Begin the final audit only after deterministic execution is complete and the
  packet is frozen.
- Do not commit, push, deploy, consolidate gold or start Supabase in this epic.

## Stories

### SP2-S01 - WSL preflight and monotonic telemetry

- Record `git status --short --branch` before the first episode write.
- Prove the WSL distribution, Linux-native repository, Python 3.12 virtualenv,
  data root and writable temp/job roots.
- Verify metadata identity, transcript availability, source hashes, absence of
  protected complete state, export ownership and protected fingerprints.
- Confirm that the current canonical cleaning produces 1,071 clean segments
  and record the actual chunk count.
- Start the official monotonic run receipt before context generation.
- Stop before writes if WSL visibility, source identity, ownership or a
  protected fingerprint diverges.

### SP2-S02 - Compact context and complete Sol read

- Generate the official context in at most three chronological slabs using
  `run_gold_episode_fast.py --context --slabs 3`.
- Read every clean segment exactly once in the primary context and inspect all
  adjacent chunk boundaries.
- Compose one `gold_episode_compact_v1` payload covering every chunk, including
  explicit zero-insight reviews where appropriate.
- Capture atomic propositions, literal evidence, material numbers, ordered
  steps, conditions, caveats, reported attribution and useful relations.
- Keep minimal evidence narrow. Put broader context in support only when it
  materially sustains the same proposition.

### SP2-S03 - Sparse adversarial recall

- Use the sparse recall view instead of materializing a duplicate full matrix
  for model consumption.
- Resolve all high-signal segments without a destination or valid exclusion.
- Recheck numbers, percentages, prices, periods, comparisons, before/after
  results, experiments, scripts, steps, conditions, warnings and caveats.
- Recheck mixed-speaker, interviewer and promotional support.
- Recheck candidate overlaps and symmetric, acyclic relations.
- Recheck every calibration target for proposition-level equivalence and
  distinct target identity.
- Record only unresolved or justified items in the model-facing artifact; keep
  the complete deterministic matrix derived on disk.

### SP2-S04 - Clean preview before write

- Run the official compact route in read-only `--check` mode.
- Correct the complete compiler/autocheck inventory locally in the payload.
- Repeat read-only checks as needed; routine schema, ASCII, enum, theme,
  evidence, number, step, relation, ledger and calibration issues are not
  checkpoints.
- Require a clean preview receipt bound to payload, source, composed review,
  revision and export semantic hashes.
- Confirm that all work remains in the Linux-native job root and that no episode
  file changed during checks.

### SP2-S05 - One persistence, finalizer and audit bundle

- Apply exactly the payload/hash approved by the clean preview receipt.
- Persist all reviews in one atomic, idempotent recorder transaction.
- Run the approved finalizer once with the fixed revision ID and export suffix.
- Require readiness, normal validation, unique candidate IDs, source-backed
  evidence, valid relations, coherent derived ledger, valid calibration and
  unchanged fingerprints.
- Require exactly:
  `packet_manifest.json`, `transcript_clean.json`,
  `insights_exhaustive.json`, `high_signal_coverage_ledger.json` and
  `calibration_tests.json`.
- Generate the standard compact `final_audit_bundle.json`; do not create an
  episode-specific audit helper.
- Freeze packet names plus physical and semantic hashes before audit.

### SP2-S06 - Single final Sol audit and completion

- Enter a dedicated `final_model_review` phase only after packet freeze.
- Audit the complete frozen packet once for recall, evidence literalness,
  numbers, atomicity, steps, caveats, relations, ledger, calibration and speaker
  provenance.
- Record model, effort, phase route, thread provenance, findings and open count.
- Passing requires zero open findings and unchanged packet/fingerprints.
- If the final audit opens findings, perform one consolidated source-backed
  correction and one focal reaudit. This makes the performance result at least
  yellow even if quality ultimately passes.
- A second correction chain, broad reaudit or unrelated new finding makes the
  pilot red and stops before `complete`.
- Register an accepted final audit once, derive `complete/passed`, and run the
  required-audit validator.

### SP2-S07 - Measured retrospective and learning cycle

- Close the monotonic timing receipt with exact elapsed milliseconds by phase.
- Record clean segments, chunks, context bytes, compact payload bytes, sparse
  recall bytes, candidates, numbers, relations, calibration, warnings and
  findings.
- Record actual counts of checks, recorder applies, patches, finalizers, builds,
  audits and WSL invocations.
- Record platform token usage only when surfaced; otherwise use
  `not_available`.
- Compare against pilot 001: 2,279 seconds, 945,320 job-local bytes, two
  pre-packet patches, one finalizer and one passing audit.
- Append one concise, evidence-based learning entry and decide whether the next
  step is another single pilot, a controlled model A/B or a small wave.

## Operation budget

Expected green path:

- one context generation;
- one compact episode payload;
- repeatable read-only checks;
- one clean preview receipt;
- one recorder apply;
- zero post-write editorial patches;
- one finalizer/build;
- one final audit;
- one audit registration and deterministic completion validation.

Allowed recovery path:

- one consolidated post-audit correction;
- one additional finalizer;
- one focal reaudit.

The recovery path is allowed for quality completion but misses the green
performance goal.

## Acceptance criteria

### Quality

- 100% of chunks have current, complete review hashes.
- Candidate IDs are unique and every candidate is source-backed.
- Adversarial recall and adjacent boundaries are complete.
- `hard_blockers=0` before the first persistence.
- Numbers are literal and typed only when material to the proposition.
- Procedures have ordered steps; caveats and attribution remain honest.
- Relations are symmetric, acyclic and useful.
- Derived ledger and calibration are referentially and semantically valid.
- The final packet contains exactly five files.
- Final audit is `passed` with zero open findings.
- Required-audit validation passes and lifecycle becomes `complete/passed`.
- All protected fingerprints remain equal.

### Performance

- Green: at most 14 minutes, one persistence, zero post-write patch and first
  audit passes.
- Yellow: more than 14 and at most 18 minutes, or one consolidated correction,
  with final quality pass.
- Red: more than 18 minutes, repeated persistence/build, second correction,
  expanding reaudit or unresolved finding.
- Model-facing job-local bytes are at least 60% below the pilot 001 baseline of
  945,320 bytes.
- No episode-specific correction helper or audit probe is created.

### Runtime

- Every gold write is executed in the Linux-native WSL environment.
- No Windows Python, `/mnt/c` job-local state or PowerShell gold write occurs.
- Source hashes in WSL match the fixed selection evidence before execution.

## Stop conditions

Stop before or between atomic operations only for missing or incompatible
source, persistent WSL/runtime failure, ownership conflict, persistent lock or
permission failure, protected fingerprint divergence, rollback risk, public
contract incompatibility or two materially different atomic routes failing.

Routine draft and validation issues are corrected inside the epic and do not
cause an intermediate audit, checkpoint or external decision.

## Out of scope

- processing any other episode;
- subagents, coordinator/worker delegation or other chats;
- changing public schemas or weakening evidence rules;
- publishing raw data, transcripts, packets or exports;
- consolidation into v2/curated/pool/master;
- Supabase, commit, push or deploy;
- reopening an existing `complete/passed` episode.

## Execution result

- Episode completed: `iuBPODaMz7s`.
- Final lifecycle: `complete/passed`, with 39 unique candidates and zero open
  findings.
- Final packet: five expected files under
  `msf_r20_gold_single_sol_pilot_002_iuBPODaMz7s`.
- Calibration: pass, 5 covered targets for a minimum of 4.
- Protected fingerprints: 4/4 unchanged.
- Performance: 1,884.3 seconds end to end, classified red because it exceeded
  18 minutes and required repeated post-audit persistence after stale derived
  ledger state blocked the first recovery finalization.
- Detailed evidence and next recommendation are in
  `msf-r20-gold-single-episode-sol-pilot-002-retrospective.md`.
