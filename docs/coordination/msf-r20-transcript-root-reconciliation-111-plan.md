# MSF-R20-TRANSCRIPT-ROOT-RECONCILIATION-111

Status: planned, not executed  
Created: 2026-07-17  
Owner: active Codex chat  
Manifest: `docs/coordination/msf-r20-transcript-root-reconciliation-111-manifest.json`

## Objective

Reconcile the 111 episodes that are source-ready in the canonical Ubuntu data
root but missing or invalid in the Windows mirror. Process them strictly by the
rank in `gold-episode-priority-queue.json`, materialize the canonical source
artifacts in `C:\MSF-data\Marketing_Swipe_File`, and prove byte/semantic parity
without re-transcribing valid media.

This epic is a source-root reconciliation, not a gold extraction wave and not
an ASR wave. Gold reviews, candidates, audits, packets, and lifecycle status are
outside its write scope.

## Confirmed cause

The transcript expansion work succeeded in `Ubuntu-24.04` and was not promoted
to the Windows mirror when later flows started consulting `C:\MSF-data`:

- Ubuntu root: 285/285 queue episodes pass the canonical source preflight;
- VTurb public catalog in Ubuntu: 163/163 valid, zero pending;
- Windows mirror: 174/285 ready, 66 missing all canonical artifacts, and 45
  containing unavailable/empty transcript placeholders;
- every one of the 111 Windows-pending episodes is ready in Ubuntu;
- `Ubuntu-24.04-msf` is a different, empty distribution and must not be used as
  the source for this reconciliation.

The historical catalog and completed-state receipts described work performed,
but they did not copy the source artifacts across data roots. Static queue
status was therefore incorrectly interpreted as proof of availability in the
Windows mirror.

## Source of truth and ownership

Read-only source:

- distribution: `Ubuntu-24.04`;
- root: `/home/luish/msf-data/Marketing_Swipe_File`;
- queue: `docs/coordination/gold-episode-priority-queue.json`;
- frozen inventories in
  `.codex-work/worker-jobs/MSF-R20-TRANSCRIPT-ROOT-RECONCILIATION-001`.

Write scope:

- `C:\MSF-data\Marketing_Swipe_File\raw\youtube\<video_id>\metadata.json`;
- `C:\MSF-data\Marketing_Swipe_File\raw\youtube\<video_id>\transcript_original.json`;
- optional `transcript_pt_br.json` when present and source-linked;
- `C:\MSF-data\Marketing_Swipe_File\processed\<video_id>\content_segments.json`;
- one isolated staging/receipt directory under
  `C:\MSF-data\Marketing_Swipe_File\.tmp\MSF-R20-TRANSCRIPT-ROOT-RECONCILIATION-111`;
- job-local evidence under
  `.codex-work/worker-jobs/MSF-R20-TRANSCRIPT-ROOT-RECONCILIATION-111`.

Forbidden:

- changing or copying `gold_extraction`, packets, exports, audits, queue
  terminal states, curated/master data, or Supabase;
- overwriting a valid Windows artifact without an exact precondition and
  rollback copy;
- running ASR or browser capture for an artifact already valid in Ubuntu;
- reading from `Ubuntu-24.04-msf` as a fallback;
- committing, pushing, deploying, or deleting provenance.

## Invariants

1. Execution order is ascending queue `rank`; no lower-priority item is
   promoted before the preceding pending item reaches a terminal receipt.
2. A source is promotable only when metadata ID matches, transcript status is
   `available`, transcript segments are non-empty, content segments are
   non-empty, and all JSON files parse.
3. Transcript text and UTF-8 bytes are copied verbatim. No NFKD, quote cleanup,
   deduplication, translation, or editorial normalization occurs here.
4. Existing invalid Windows placeholders are preserved in rollback staging
   before atomic replacement.
5. A batch failure leaves either the previous Windows state or the complete new
   state for every episode; never a partial three-file set.
6. The manifest is immutable during execution. New discoveries create a
   separate revision artifact, not an in-place change.

## Stories

### R111-S01 - Freeze and prove the 111-item delta

1. Record `git status --short --branch` before writing.
2. Verify both distributions and require `Ubuntu-24.04` to contain the source
   root; reject the empty `Ubuntu-24.04-msf` root.
3. Re-run source inventory for both roots and require exactly:
   - Windows: 174 ready, 66 missing, 45 invalid;
   - Ubuntu: 285 ready;
   - intersection: all 111 Windows-pending IDs ready in Ubuntu.
4. Verify the manifest semantic hash and queue rank monotonicity.
5. Capture physical and semantic hashes for every source artifact and the
   pre-existing Windows destination, including invalid placeholders.

Gate: 111 exact IDs, zero source-invalid items, zero duplicate IDs/ranks, and
no write outside job-local evidence.

### R111-S02 - Transactional materialization in priority order

Process eleven batches: ten batches of ten episodes and one final batch of
eleven. Inside each batch, preserve manifest order.

For each episode:

1. Copy the Ubuntu source files to an episode-specific staging directory on the
   Windows filesystem by a direct `wsl.exe --distribution Ubuntu-24.04 --user
   luish --exec ...` command.
2. Validate staged JSON, IDs, status, non-empty segments, UTF-8, and hashes.
3. Derive no content. The staged `content_segments.json` must be the existing
   Ubuntu artifact.
4. Snapshot the current Windows destination when it exists.
5. Publish metadata, transcript source set, and content segments as one atomic
   episode transaction.
6. Re-open the destination and compare physical and semantic hashes with the
   Ubuntu source.
7. Write an idempotent episode receipt before advancing the cursor.

Re-running a completed item with unchanged source/destination hashes returns
`idempotent=true` and performs no write.

Gate per batch: every item has `promoted` or `idempotent`, no partial episode,
and the cursor points to the next exact queue rank.

### R111-S03 - Canonical source validation

After all batches:

1. Re-run `audit_gold_source_inventory` against `C:\MSF-data`.
2. Require 285/285 `ready_for_gold`, zero missing, zero invalid.
3. Compare the 111 promoted episodes against Ubuntu for metadata, original
   transcript, optional pt-BR transcript, and content segments.
4. Require transcript segment counts, order, timestamps, text, status, and
   content-segment hashes to match.
5. Confirm that no gold, audit, packet, export, or fingerprint file changed.

Gate: parity 111/111 and active Windows source readiness 285/285.

### R111-S04 - Repair the ongoing acquisition contract

1. Make source acquisition terminal only after both the Ubuntu canonical root
   and Windows accessibility mirror have validated receipts.
2. Keep gold execution on Ubuntu as required by `AGENTS.md`; the Windows mirror
   exists for project accessibility and fast source discovery, not as an
   alternate gold runtime.
3. Update the queue selector from direct root evidence, never from historical
   `source_status` alone.
4. Add a parity check to the weekly VTurb update: a newly completed transcript
   cannot become `source_complete` until the Windows mirror is synchronized.
5. Report root divergence as `mirror_pending`, not `transcript_missing`.

Gate: a fixture with valid Ubuntu source and absent Windows mirror is classified
as `mirror_pending`; after sync it becomes ready without ASR.

### R111-S05 - Final verification and closure

Run focused tests, `py_compile`, `git diff --check`, source inventory, manifest
hash validation, receipt validation, and a read-only protected-artifact diff.
Produce:

- `reconciliation_receipt.json` with 111 terminal results;
- `root_parity_report.json` with 285/285 readiness;
- `protected_artifact_diff.json` proving zero unrelated change;
- `process_learnings.md` with observed throughput and any anomalies.

No external editorial audit is needed because this epic copies and validates
source bytes; it does not make semantic gold judgments.

## Contingency route

Current evidence predicts zero acquisition work. If a source artifact becomes
invalid between plan and execution:

1. stop only that episode before destination write;
2. finish independent later episodes only after recording the blocked rank;
3. classify the item as `source_drift`, not as an automatic ASR request;
4. inspect the public transcript route in real Chrome before deciding absence;
5. use direct captions, Chrome transcript, and finally resumable ASR in that
   order, with a separate revision and provenance;
6. return to the blocked queue rank before declaring the epic complete.

## Expected duration

- preflight and frozen hashes: 5-10 minutes;
- eleven transactional batches: 15-30 minutes, dominated by filesystem copy
  and antivirus/OneDrive latency;
- full parity and closure: 5-10 minutes.

Expected total: 25-50 minutes with zero ASR. The prior estimate of roughly 42
hours applied to the old 36-item ASR residual before that Ubuntu backfill was
completed; it no longer applies to this 111-item mirror reconciliation.

## Completion criteria

- 111/111 manifest episodes terminal in queue order;
- Windows source inventory 285 ready, zero missing, zero invalid;
- exact source/destination parity for every promoted artifact;
- no retranscription of already-valid Ubuntu sources;
- no gold/editorial/protected artifact change;
- durable incremental mirror rule implemented and tested;
- no unresolved `mirror_pending` item.

