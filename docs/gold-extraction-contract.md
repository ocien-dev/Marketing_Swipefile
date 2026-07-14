# Gold Extraction Contract

Status: MSF-R20 Phase A

## Purpose

The gold layer is a parallel, evidence-first editorial record. It does not
replace or write to the frozen v2 serving pool. A future owner-approved
migration will map gold candidates into v2 deliberately.

## Route

The supported R20 route is `codex_manual_no_paid_api`. Deterministic tooling
prepares transcript cleanup, chunks, signal inventory, calibrations, work
orders, validation, and audit packets. Codex reads and reviews
each work order. No paid model client is called by the tooling.

## Job Preflight

Before episode writes, record `git status --short --branch` and verify once:

- the explicit Python runtime and required modules;
- a writable, job-scoped temporary directory when tests use filesystem
  fixtures;
- read/write access only to the active episode and export paths;
- the protected-fingerprint snapshot;
- packet input availability and JSON parseability;
- ownership of every script or contract required to reach the requested
  lifecycle.

If acceptance depends on a tooling change outside episode ownership, split it
into an explicit tooling subjob before editorial work. Do not repair lifecycle
state manually or broaden ownership implicitly.

## Document Contract

`schemas/gold_insights.schema.json` defines `schema_version: 1.0.0`.
Each candidate contains a stable `candidate_id`, its chunk, a source claim,
an applicable takeaway, reported-case and causality labels, caveats, steps,
canonical themes, free subthemes, existing `process-*` tags, normalized
numbers, layered evidence, and parent-child relations.

The v2 compatibility mapping is embedded in every gold document. It is
descriptive only: gold output stays in `gold_extraction` until an explicit
migration design is approved.

## Canonical Themes

The closed list is:

- `audience_market`, `business_model`, `copywriting`, `copy_vsl`
- `creative_strategy`, `conversion_optimization`, `delivery_support`
- `funnel_architecture`, `launch_campaign`, `offer_pricing`
- `operations_management`, `paid_traffic`, `product_strategy`
- `retention_ascension`, `sales_relationship`, `testing_measurement`
- `unit_economics`

Specific concepts remain in `subthemes`; operational retrieval remains in the
existing `process_tags` taxonomy. Legacy free themes are mapped at ingestion
and preserved as subthemes, not silently discarded.

## Numbers And Evidence

Every number records `raw`, `value`, `min_value`, `max_value`, `unit_kind`,
`period`, `role`, and `value_status`; denominator and attribution window are
optional. Transcript performance figures default to `reported` and are never
quietly corrected from memory.

## Preflight For Future Gold Jobs

Before creating or updating a gold extraction, the executor must read
`raw/youtube/<video_id>/metadata.json` and `transcript_original.json`. The
metadata video ID must match the active episode and the transcript must be
available. These raw files are mandatory read-only inputs to the preparation
path; a missing or mismatched input is a blocking preflight result, never a
reason to substitute a processed file silently.

Use `scripts/reprocess_gold_episode.py --preflight-raw` before any preparation
write. This mode is read-only. It also rejects a present
`metadata.transcript_status` or `transcript_original.transcript_status` other
than `available`, even if transcript segments are present.

Before the final build, use
`scripts/build_gold_semantic_extraction.py --check-readiness`. This mode is
also read-only and must pass before the normal builder writes status or exports
a blind packet. It detects deterministic review/candidate defects such as a
procedural insight without `steps`. An optional `--export-suffix` on the normal
builder writes the awaiting-audit packet to the requested suffix; omission
preserves `msf_r20_piloto_<video_id>`.

Evidence has three layers: `minimal_quote` directly supports the claim,
`context_range` preserves the surrounding span, and `support_segments` holds
related numbers, conditions, or caveats. Every quote is regenerated from the
clean transcript and must match it verbatim in UTF-8.

## Resume And Audit States

Each work order stores a chunk input hash. The status file stores an explicit
chunk state, review hash, attempts, and candidate count. A matching completed
review is reused on rerun; a changed transcript or review reopens only that
chunk. Filesystem locks or permission failures return a paused state and must
be resolved before continuation.

`awaiting_external_audit` is not complete. Only a package with all chunks
reviewed, a fully destined ledger, passing calibrations, a valid schema, and
an independent audit with zero open findings can use `complete`.

The compatibility name means external to the executor phase. Future R20 audits
run only once, after the full epic is ready, in a dedicated `gpt-5.6-sol`
review phase with reasoning `high` or above. No coordinator/worker delegation
or Claude permission, execution, or review is required. Historical provider
provenance is retained verbatim. A current report must preserve reviewer identity,
`reviewer_thread_id`, `reviewer_model`, `reasoning_effort`, `audit_route`,
timestamp, status, summary, findings, and open-finding count.

Every finding validates its ID, severity (`critical`, `major`, or `minor`),
status (`open` or `resolved`), category, segment range, candidate IDs, summary,
evidence, and required action. `passed` with any open finding is invalid. The
build derives audit state from a valid `editorial_audit_report.json`; it cannot
accept `passed` as a free assertion. `complete` additionally requires a reviewer
recorded in a dedicated final Sol review phase, deterministic validation, and
unchanged protected fingerprints. The same thread may be used when audit route,
model and reasoning provenance prove that final phase.
For same-thread final review, use `audit_route: final_model_review`,
`reviewer_model: gpt-5.6-sol`, and `reasoning_effort: high` or above.

## Executor Pre-Audit Recall Gate

Before exporting the blind packet, run a second adversarial semantic pass after
all chunks and ledger dispositions are complete. It must search numbers,
percentages, prices, periods, comparisons, before/after results, tests, changes,
scripts, steps, conditions, warnings, caveats, and cross-segment relationships.

Ledger presence is not semantic recall. Every `captured` or `merged` entry must
reference a candidate that expresses the same useful proposition supported by
the segment. A broad topic match, nearby number, or candidate from the same
chunk is insufficient. Check adjacent chunk pairs for claims that begin as a
story or mechanism and resolve as an offer, pitch, result, retention effect,
condition, or caveat. Reopen affected reviews until this pass reports zero
unrepresented useful propositions.

Normal deterministic validation may pass for a valid `changes_requested`
audit with open findings. Required-audit validation and `complete` additionally
require a valid `passed` report with zero open findings.

## Episode Finalization

The episode is the isolated execution unit. After all chunk reviews are
present, the active chat runs one consolidated diagnostic and resolves routine,
source-backed defects before creating its packet. No intermediate review or
handoff occurs.

`gold_review_autocheck.py` classifies deterministic defects as
`hard_blockers` and editorial uncertainty as `audit_warnings`. Unsupported
quotes or numbers, invalid relations, invalid ledger destinations, and invalid
or duplicate calibration targets are hard blockers. Possible promo or
interviewer language, candidate overlap, reported-case caveats, and semantic
calibration ambiguity are audit warnings. A warning is visible in the packet
manifest but does not suppress finalization by itself.

Use `scripts/finalize_gold_episode.py` for a semantically complete episode. It
runs the autocheck, readiness, build, normal validation, and only then exports
the five-file packet. The finalization receipt makes a repeated
`revision_id` idempotent only when the canonical final-input signature and the
exact five packet filenames plus semantic and physical hashes still match. A
changed review, source input, missing/extra/renamed packet file, or packet hash
change is a deterministic receipt conflict; use a new revision after an
authorized correction. A `complete/passed` episode remains read-only.

Packet publication stages all five files outside the live destination and then
swaps the directory atomically. A failed stage preserves the prior packet byte
for byte, or leaves no packet when none existed. Status metadata is updated
only after the complete packet is published.

### Ten-Minute Fast Lane

When the complete episode fits the active context, prefer one episode payload
over several persisted chunk batches. Run:

```text
python -m scripts.run_gold_episode_fast --video-id <id> --data-root <root> \
  --input <complete-review-payload.json> --check
python -m scripts.run_gold_episode_fast --video-id <id> --data-root <root> \
  --input <complete-review-payload.json> --apply \
  --revision-id <revision> --export-suffix <suffix>
```

The check compiles every proposed review and runs the final autocheck against
the composed candidate state in memory. It does not write the episode or
export. Apply is refused while that preview has compiler issues or hard
blockers. A clean apply uses one atomic recorder transaction and invokes the
finalizer once. Recorder and finalizer receipts make a lost-output retry
idempotent.

The command reports measured milliseconds for compile, autocheck, persistence,
finalization, and total execution. These metrics describe the current command;
they must not be extrapolated into invented historical time or token usage.
For an episode too large for one semantic pass, use the existing chunk-batch
fallback, but still consolidate diagnostics before any corrective write.

## One-Shot Wave Delivery

For a multi-episode wave, the active chat continues until every manifest episode
is packet-ready or terminally blocked. Prefer one complete episode transaction;
chunk batches are a large-episode fallback and remain internal persistence
units, not review boundaries. `record_gold_manual_reviews.py --check` uses the same pure compiler
as apply: it repairs only approved mechanical editorial representations,
preserves transcript quotes verbatim, returns every batch issue together, and
writes nothing. A successful batch records its semantic signature and review
hashes, so the same payload can be recovered idempotently after lost stdout.

`run_gold_wave.py --wave-receipt <path>` writes a deterministic consolidated
delivery receipt only for terminal `ready_for_audit` or `terminally_blocked`
waves. An `in_progress` evaluation remains read-only and never creates or
overwrites a receipt. `ready_for_audit` requires every expected manifest
episode to have a valid five-file finalization receipt or to be independently
protected as `complete/passed`. The protected route also proves the manifest
export destination, exact packet names and hashes, packet video identity,
valid passed audit with zero findings, and matching protected fingerprints. A
pending-audit finalization receipt is bound to that same manifest export
destination and packet video identity; it cannot point at another episode's
otherwise valid packet. A
partial 4/5 wave remains `in_progress`; the single final Sol audit starts only
after the full wave gate.

Patch manifests use non-empty `revision_id`, `revision_kind`, and `reason` for
new revisions. Assertions, read-only `--check`, atomic `--apply`, rollback,
and history remain mandatory. Historical `patch_window` manifests remain
readable, but no patch-count quota is imposed on a revision.

## WSL Runtime Contract

Gold extraction runs by default on Ubuntu 24.04 under WSL 2. The repository,
`MSF_DATA_DIR`, `TMPDIR`, and `.venv` must be Linux-native paths and must not
live under `/mnt/c`. This keeps recorder transactions, packet staging, and
`os.replace` operations on one filesystem and avoids OneDrive/NTFS lock and
latency behavior.

The Windows data root remains a rollback source during migration and is never
deleted by bootstrap or verification commands. Migration is copy-only until a
path, size, and SHA-256 inventory proves equivalence. GitHub stores versioned
code and contracts; it does not store raw sources, ignored gold state, packets,
audits, or receipts. Supabase is not a backup mechanism for this filesystem.

Use `scripts/bootstrap_wsl.sh` to create the Linux virtualenv and install
requirements. Use `scripts/verify_wsl_environment.py` for the read-only runtime
gate before any gold write.
