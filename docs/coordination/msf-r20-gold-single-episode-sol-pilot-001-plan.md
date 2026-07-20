# MSF-R20-GOLD-SINGLE-EPISODE-SOL-PILOT-001

Status: completed - quality passed, performance result red
Execution: direct in the active chat
Model: `gpt-5.6-sol` with reasoning `high` for the entire epic
Runtime: Ubuntu 24.04 / WSL 2, Linux-native repository and data root
Scope: one selected episode, `aFabW0i9K20`

## Objective

Validate an end-to-end gold extraction that can finish in approximately ten
minutes without coordinator/worker delegation, subagents, other chats,
intermediate checkpoints or repeated broad audits.

The same `gpt-5.6-sol/high` execution reads the source, creates the extraction,
runs adversarial recall and performs the final review in a dedicated same-thread
`final_model_review` phase. The packet is frozen before that phase. This is not
a blind review by another thread; its protection is the immutable packet,
explicit phase boundary and deterministic audit provenance allowed by the gold
contract.

## Pilot hypothesis

Using Sol/high from the first semantic read should improve initial recall and
reduce the audit from a discovery mechanism to a final verification mechanism.
The pilot succeeds only if quality improves without reproducing the Wave 006
pattern of repeated patches, builds and expanding reaudits.

## Selected episode

The pilot episode is fixed before execution:

- `video_id`: `aFabW0i9K20`
- title: `Escalando 100K/Dia Como Afiliado Na Gringa (Passo A Passo) | Diogo Gomes e Gabriel Pinto - SDE #136`
- duration: 7,603 seconds, approximately 126.7 minutes;
- raw transcript: available, 1,067 source segments;
- gold-clean load: 1,067 segments and 19 chunks using the current canonical
  `clean_segments()` and `chunks_for_segments()` functions;
- semantic exercise surface: 168 numeric signals, 74 procedure signals, 78
  comparison signals, 46 experiment signals, 13 warnings and substantial
  sequence, copy, funnel and traffic-creative coverage;
- current gold state: no `gold_extraction` directory, packet or protected
  `complete/passed` state;
- prior wave manifests: not listed in Waves 004, 005 or 006.

Execution identifiers are fixed as follows:

- `revision_id`: `single-sol-aFabW0i9K20-final-001`
- `export_suffix`: `msf_r20_gold_single_sol_pilot_001_aFabW0i9K20`
- job-local root:
  `.codex-work/worker-jobs/MSF-R20-GOLD-SINGLE-EPISODE-SOL-PILOT-001`

Protected source evidence at selection time:

| Source | Physical SHA-256 | Bytes |
| --- | --- | ---: |
| `raw/youtube/aFabW0i9K20/metadata.json` | `252B728C64B4420F1F670317F17D55ECE854F006386B66ABEE2A38368ECF22F6` | 4,487 |
| `raw/youtube/aFabW0i9K20/transcript_original.json` | `8D34BC91D3F89C710F9B3D1286081154BEE16CE2A0DC2214497271843E46679F` | 275,493 |
| `processed/aFabW0i9K20/content_segments.json` | `4970719B17F057CF810C934D3D855492828C44170A61AAB7D8437DD8E40392FF` | 580,385 |

This episode was selected because it fits the declared 600-1,200 segment and
10-20 chunk window while exercising the semantic categories that previously
caused post-audit rework. Its 19 chunks intentionally test the upper edge of
the ten-minute target instead of making the pilot look fast with a trivial
episode.

Before execution, verify these hashes and source properties again in WSL and
record them in the job-local run receipt. Do not substitute another episode.
Any incompatible source change stops this pilot and requires a new plan rather
than silently selecting an easier episode.

## Non-negotiable execution rules

- Use `gpt-5.6-sol/high` for planning, extraction, recall, correction and final
  audit. Do not spawn subagents or switch models.
- Use only the active chat. Do not create, fork, message or hand off another
  thread. Do not create heartbeat or continuation automation.
- Keep the Codex app agent in its Windows environment so existing project and
  chat history remain available, but run every gold operation in WSL 2 through
  one direct `wsl.exe --distribution Ubuntu-24.04 --user luish --cd ... --exec
  ...` invocation per command.
- Inside each gold command, `uname`, repository, `.venv`, data root and temp
  root must all resolve inside the Linux filesystem, outside `/mnt/c`.
- PowerShell may launch direct WSL commands and read the Windows checkout, but
  must not run the gold Python environment, compose `bash -lc` pipelines or
  write episode data under `C:\MSF-data`.
- If WSL is unresponsive, terminate only `Ubuntu-24.04` once and retry a clean
  preflight. A second startup failure stops the pilot before episode writes;
  never fall back to the Windows runtime.
- Review the complete episode before the first persistence. Do not persist
  chunk checkpoints or partial packets.
- Keep one stable candidate namespace and one episode-local revision chain.
- Never use the final audit as an open-ended second extraction pass.

## Target timing

The primary target is at most 10 minutes from technical preflight start through
final audit decision. Record actual monotonic elapsed time for every phase.

| Phase | Target |
| --- | ---: |
| WSL preflight and preparation | 0:45 |
| Complete chronological semantic read and draft | 4:00 |
| Recall matrix and in-memory autocheck | 2:00 |
| Atomic persistence, finalizer and packet freeze | 1:15 |
| Same-thread Sol final audit | 2:00 |
| Total | 10:00 |

Any post-audit correction means the 10-minute primary target was missed, even
if the episode ultimately completes. A total above 15 minutes is a failed
performance pilot.

## Stories

### SP-S01 - WSL-native preflight and instrumentation

- Record `git status --short --branch` before writes.
- Prove Linux-native repository, Python 3.12 virtualenv, data root and temp.
- Validate raw metadata, transcript availability, episode identity, ownership
  and protected fingerprints.
- Start a job-local monotonic timing receipt with no estimated values.
- Run the episode route read-only and confirm that it is new or resumable, not
  protected complete.

### SP-S02 - One complete Sol semantic extraction

- Read all compact work orders and referenced transcript segments in order.
- Read every adjacent chunk boundary before closing the candidate inventory.
- Produce one complete review payload, including explicit zero-insight reviews
  where appropriate.
- Preserve atomic propositions, literal quotes, typed numbers, steps,
  conditions, caveats, reported attribution and useful relations.
- Do not optimize for a candidate count. Optimize for complete representation
  of useful propositions without duplication.

### SP-S03 - Mandatory pre-audit semantic recall matrix

Before any packet, create a job-local matrix that covers:

1. every discovered high-signal segment and its final disposition;
2. the candidate and exact proposition for every `captured` or `merged` signal;
3. every numeric trigger, its literal raw value and structured record or a
   source-backed exclusion reason;
4. every procedure, script or list and its ordered steps;
5. comparisons, before/after results, conditions, warnings and caveats;
6. interviewer, promo and mixed-speaker provenance;
7. overlapping candidates and their merge, distinction or symmetric relation;
8. every calibration target and proposition-level candidate equivalence;
9. every adjacent chunk boundary with its final recall decision.

Run the compiler and autocheck against the composed final state in memory.
`hard_blockers` must be empty. Audit warnings remain visible and do not trigger
mechanical rewrites. The matrix is incomplete if it only records a candidate ID
without explaining proposition equivalence.

### SP-S04 - Single atomic write and packet freeze

- Repeat read-only checks until the complete payload is clean.
- Persist the full episode in one atomic, idempotent recorder transaction.
- Invoke `finalize_gold_episode.py` once with one revision ID and export suffix.
- Require readiness, normal validation, exact five-file packet, unique IDs,
  valid relations, ledger and calibration, and unchanged fingerprints.
- Freeze packet names and physical/semantic hashes before final review.
- Do not rebuild between packet freeze and audit unless the audit opens a
  concrete finding.

### SP-S05 - Same-thread Sol final audit

- Enter an explicit `final_model_review` phase using only the frozen packet.
- Review recall, evidence, number literalness, atomicity, relations, ledger,
  calibration and speaker provenance once, comprehensively.
- Record `reviewer_model=gpt-5.6-sol`, `reasoning_effort=high`, current thread
  identity, reviewed timestamp, findings and open count.
- Passing requires zero open findings.
- Do not broaden scope after the first audit report is sealed.

If findings exist, perform exactly one consolidated source-backed correction
covering all finding IDs, create one new packet and run one focal reaudit of
those IDs only. The focal reaudit may report a new issue only when it is a
direct regression introduced by the correction. Any unrelated new discovery,
remaining finding or second correction need marks the pilot unsuccessful and
stops before `complete`.

### SP-S06 - Completion and retrospective

- Validate the accepted audit envelope read-only and register it once.
- Derive `complete/passed` and run validation with external audit required.
- Verify exact packet identity, hashes and protected fingerprints.
- Publish the verified exports snapshot only after the episode is idle.
- Record measured timing, operation counts, candidate count, audit findings,
  context bytes and exact token usage only if the platform exposes it.
- When token usage is unavailable, record `not_available`; never estimate it.
- Compare the result against the pilot decision table below.

## Operation budget

Expected successful path:

- one preparation;
- one complete review payload;
- unlimited read-only compiler checks before writing;
- one recorder apply;
- one finalizer before audit;
- one Sol audit;
- one audit registration;
- one deterministic completion build;
- one required-audit validation.

Allowed recovery path:

- one consolidated post-audit correction;
- one additional finalizer;
- one focal Sol reaudit.

No third packet, broad reaudit, second correction chain or alternative auditor
is allowed in this pilot.

## Metrics and decision table

Record the following in a job-local `episode_run_receipt.json`:

- exact start/end and elapsed milliseconds per story;
- clean segments, chunks, work-order bytes and frozen packet bytes;
- candidates, numbers, relations, calibrations and ledger dispositions;
- compiler issues and hard blockers before the single apply;
- audit warnings and findings by severity/category;
- recorder, patch, finalizer, build and audit operation counts;
- exact model token usage when surfaced by the platform, otherwise
  `not_available`.

| Result | Decision |
| --- | --- |
| At most 10 min, first audit passes, zero major findings | Green: repeat on three single episodes before increasing wave size |
| 10-15 min or one consolidated correction, then pass | Yellow: inspect the measured bottleneck and run one more single episode |
| More than 15 min, any expanding reaudit, remaining major finding or second correction | Red: do not return to multi-episode waves; harden the semantic matrix first |

## Expected artifacts

- one episode-local complete review payload and recorder receipt;
- `semantic_recall_matrix.json`;
- `episode_run_receipt.json` with measured timing;
- one final five-file packet, or two only when the single correction path is
  exercised and the first remains immutable provenance;
- one audit report, plus one focal reaudit only when required;
- final `complete/passed` verification report;
- one concise learning entry based on measured evidence.

## Out of scope

- processing more than one episode;
- subagents, coordinator/worker roles, other chats or inter-thread messages;
- PowerShell-driven gold execution;
- changing public gold schema or lowering evidence standards;
- consolidating into v2/curated/pool/master or starting Supabase;
- commit, push or deploy;
- reopening any existing `complete/passed` episode.

## Stop conditions

Stop the affected episode only for missing/incompatible source, persistent lock
or permission failure, protected fingerprint divergence, atomic rollback risk,
public-contract incompatibility, or failure of the single allowed correction
path. Routine encoding, enum, theme, number, step, relation, ledger or
calibration issues are resolved before the first atomic apply and do not create
checkpoints or external decisions.

## Execution result

- `aFabW0i9K20` completed with 19/19 reviews, 45 unique candidates,
  `hard_blockers=0`, calibration `pass`, final audit `passed/0` and protected
  fingerprints 4/4 unchanged.
- The final packet contains exactly the five required files and required-audit
  validation passed.
- Observed elapsed time was 2,279 seconds, approximately 37:59. This is a red
  performance result under the decision table.
- The initial complete payload was persisted before the in-memory one-shot
  autocheck, causing six late numeric blockers and two pre-packet patches. No
  post-audit correction was required.
- WSL handled all gold writes without Windows Python or fallback, but repeated
  invocations and `/mnt/c` job-local artifacts added avoidable variance.

Detailed evidence, model assessment, subagent assessment and the prioritized
backlog are recorded in
`docs/coordination/msf-r20-gold-single-episode-sol-pilot-001-retrospective.md`.

## Next gate

Implement the retrospective P0 and P1 items without touching real gold data,
then run one comparable single episode with one clean preview, one persistence,
one finalizer, complete monotonic telemetry and no subagents.
