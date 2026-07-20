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
`raw/youtube/<video_id>/metadata.json` and `transcript_original.json`. When the
source language is not Portuguese, `transcript_original.json` remains immutable
as provenance and `transcript_pt_br.json` is the preferred semantic source for
normalization and gold extraction. Both files participate in protected
fingerprints. The
metadata video ID must match the active episode and the transcript must be
available. These raw files are mandatory read-only inputs to the preparation
path; a missing or mismatched input is a blocking preflight result, never a
reason to substitute a processed file silently.

### Canonical source materialization

Source acquisition is complete only after the active data root contains all
three canonical artifacts for the episode: `raw/youtube/<video_id>/metadata.json`,
`raw/youtube/<video_id>/transcript_original.json` with status `available` and
non-empty segments, and `processed/<video_id>/content_segments.json`. A staging
directory, cache, job-local receipt, historical queue status, or previous gold
record is not evidence that the active root is ready. The backfill flow may
derive missing `content_segments.json` only from an already-valid raw transcript;
it must never promote a missing, empty, or unavailable transcript as ready.

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

## Derived Transcript Semantic Index

Preparation creates two disposable navigation artifacts beside, not inside,
`gold_extraction`:

- `processed/<video_id>/transcript_semantic_index.jsonl`;
- `processed/<video_id>/transcript_semantic_index_status.json`.

The index is generated just in time from the current `transcript_clean.json`
source, before semantic authoring begins. Its status binds the exact source
semantic hash, algorithm version, segment count, unit count, and physical plus
semantic hashes of the JSONL. An identical source reuses the artifact without
rewriting it; source or algorithm drift marks it stale and preparation replaces
it atomically.

Each navigation unit is chronological and stores exact source segment IDs,
clean-index range, timestamps, per-segment verbatim text, literal numeric
occurrences, deterministic risk cues, conservative speaker role, chunk links,
and adjacent-unit links. `unknown` is preferred to an invented speaker role.
The compact Fast Lane context exposes only a bounded navigation summary; the
transcript text still appears once in its canonical chronological records.

This index has `navigation_only` authority. It may prioritize numeric
trajectories, mechanisms, procedures, outcomes, caveats, promo/interviewer
surfaces, and chunk boundaries, but it never creates a claim, evidence quote,
ledger decision, calibration result, or audit disposition. The active reviewer
must still read the complete transcript and run prelint, recall, finalization,
and the final dossier audit. A read-only context load never backfills a missing
index, especially for a protected `complete/passed` episode.

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
`changes_requested` transitions to the job-local nonterminal state
`remediation_required`; it does not write `final_response.md` or a completion
receipt. The same epic continues through source-backed remediation, a fresh
dossier, reaudit, and completion.

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

When the complete episode fits the active context, prefer one authoritative
`gold_authoring_manifest_v1`
over several persisted chunk batches. Start the epic timer before runtime sync,
select the next source-complete unprepared episode and bootstrap its compact
context in one certified WSL process:

```text
scripts/invoke_gold_wsl.ps1 -Action StartEpisode
python -m scripts.run_gold_episode_fast --bootstrap-request <request.json> \
  --runtime-parity-receipt <receipt> --runtime-manifest <manifest>
python -m scripts.run_gold_episode_fast --video-id <id> --data-root <root> \
  --context --slabs 3 --job-dir <linux-native-job-dir>
python -m scripts.run_gold_episode_fast --video-id <id> --data-root <root> \
  --authoring-manifest <gold-authoring-manifest.json> --prelint \
  --job-dir <linux-native-job-dir>
python -m scripts.run_gold_episode_fast --video-id <id> --data-root <root> \
  --authoring-manifest <gold-authoring-manifest.json> --one-shot \
  --revision-id <revision> --export-suffix <suffix> \
  --job-dir <linux-native-job-dir>
```

This is the canonical `chronological_hybrid_v1` route. The model reads the
complete transcript chronologically and authors the episode once. Deterministic
number, calibration, boundary, evidence and risk inventories constrain recall;
they do not generate or replace semantic claims. `--check` plus `--apply`
remain recovery/debug commands only.

`--select-next` considers only source-complete episodes without an existing
`gold_extraction`, applies the configured segment band, chooses the episode
nearest the target size, and writes `selection_receipt.json`, source hashes,
`bootstrap_request.json`, stable revision/export identifiers, compact context
and the run manifest. The canonical launcher is the repository `.venv` on
Windows. Before selection it runs `scripts.verify_gold_runtime.py --runtime
windows_native`, which verifies Python 3.12 from the repository virtualenv,
repository/data/temp paths, required commands and a writable temp root. One
`run_id` covers every startup phase. Historical WSL launchers are optional
recovery tooling only and cannot block a Windows-native episode.

For routine runs, `SelectBootstrap` supplies the durable
`docs/coordination/gold-episode-priority-queue.json`. The queue is generated
only when the inventory changes, classifies titles in this priority order:
VSL, Copy, Anuncios, Funil, Quiz, Escala, Perpetuo, Lancamento, Experts,
Afiliado, Nutra and Outros. The recurrent `Segredos da Escala #...` channel suffix is
removed before classification. Episodes are shortest-first inside each group.
The selector reads the first still-unprepared entry and hashes only that
episode's three source files; it does not rescan or reclassify the library at
startup.

Selection reconciles every queued ID against the active Windows data root and
the terminal identity registry. A terminal identity binds video ID, semantic
source hash, `chronological_hybrid_v1`, gold schema, passed audit and completion
receipt. Queue cursor history never certifies completion. A compatible terminal
identity is skipped even when the cursor is stale; a changed source requires
`--explicit-reprocess` plus a non-empty reason. Historical WSL completion
receipts may be reconciled read-only with `scripts.gold_terminal_identity`; the
operation imports identity metadata only and never copies raw, packet or gold
data.

### Single authoring authority

`gold_authoring_manifest_v1` contains only model decisions: candidates,
source-scoped dispositions, risk acknowledgements, warning dispositions and a
calibration decision of candidate equivalence or `none` for every target. The
runtime deterministically expands it to compact v3 and derives reviews, ledger,
calibration coverage, workbench and persisted payload. The preview receipt and
apply bind the same manifest hash. `ledger_updates`, calibration redirects,
direct review writes and episode-specific Python helpers are forbidden in the
normal route; historical formats remain readable for recovery only.

Before apply, the same executor completes one adversarial authoring pass over
evidence/numeric ownership, excluded material, host attribution, before/after
mechanisms and outcomes, calibration proposition equivalence, boundaries and
counterexamples. Its receipt binds `authoring_decisions_sha256`; any semantic
edit makes the pass stale. This is part of authoring, not an intermediate
audit. F019/F037 regression classes must fail before persistence.

#### Compact authoring v4

`source_dispositions` is a per-segment enumeration that, on real episodes, is
dominated by two boilerplate shapes: one `captured` template whose
`candidate_ids` are exactly the candidates whose evidence covers the segment,
and one default `excluded` template repeated for every low-signal segment.
Writing all of them by hand is pure model-facing boilerplate: on a 5,289
segment episode it is about 1.6 MB of the 1.8 MB manifest, while the actual
candidates are under 80 KB.

Compact authoring v4 lets the model author only the semantic minority. Set
`"compaction": "v4"` and provide, instead of the full `source_dispositions`
list:

- `segment_count` and `chunk_ranges` (`[chunk_number, first_clean_index,
  last_clean_index]`, the same boundaries already in the reading context);
- `captured_disposition` (`reason_code` + `reason` template, authored once);
- `default_source_disposition` (`disposition` + `reason_code` + `reason` for
  the low-signal default, authored once);
- `source_disposition_exceptions`: only segments that deviate from those two
  shapes (for example an excluded segment with a specific reason, or a merged
  segment), each with its `index` and full fields.

`audit_warning_dispositions` and `risk_recall_acknowledgements` may be given
in interned form (`{"justification_table": {...}, "items": [{...,
"justification_ref": "j0"}]}`) so an identical justification is stored once.

The runtime expands v4 to the full v1 manifest **before** any hash,
validation, or compact-v3 derivation. `captured` dispositions are rebuilt from
candidate evidence ranges (sorted `candidate_ids`), every non-exception segment
takes the declared default, and interned justifications are dereferenced. The
expansion is deterministic and lossless: `authoring_decisions_sha256`,
`semantic_sha256`, the derived ledger, calibration, workbench and dossier bytes
are identical to a hand-written full manifest. Persisted schemas do not change,
and the full-manifest form remains fully accepted for compatibility.

### Retired Blind Semantic-Compiler Research Lane

The blind semantic compiler is not a production route. Four read-only pilots
failed the adoption gate: the best result still had 88.24% material recall, one
unsupported attribution and three open final-audit findings. Its modules are
kept only to preserve research provenance and are excluded from the executable
runtime signature. Do not use shards, a global reducer, relation windows or a
gap resolver while processing a real gold episode.

The useful controls were promoted into `chronological_hybrid_v1`: source-first
numeric inventory, calibration and boundary bindings, scoped risk dispositions
and exact-duplicate detection. Production candidates still come from one full
chronological semantic pass. A future benchmark may reopen the research lane
only with explicit owner authorization and may not write gold state.

Refresh the queue only after ingesting new source episodes or intentionally
changing the classification policy:

```bash
python -m scripts.gold_episode_priority \
  --data-root "$MSF_DATA_DIR" \
  --json-output docs/coordination/gold-episode-priority-queue.json \
  --markdown-output docs/coordination/gold-episode-priority-queue.md
```

`--dry-run` is the pure consolidated diagnostic: it writes neither gold,
preview receipt nor job-session telemetry. `--prelint` uses the same compiler
and composed-state diagnostics in memory while recording the measured phase,
but creates no clean-preview receipt and does not count as the official check.
Both return one sparse `gold_consolidated_repair_manifest` containing compiler
issues, numeric occurrence/trajectory defects, claim-support gaps,
counterexamples, risk tiers and evidence-scope warnings so the first official
`--check` can be clean.

`needs_revision` is a nonterminal diagnostic result. It exits successfully and
must expose `terminal=false`, `continue_required=true`, a
`workflow_disposition`, and the next local action. `diagnostic_stage` records
where the inventory was produced; `stopped_at` stays empty because the epic did
not stop. The executor must repair the current source-backed payload and repeat
the read-only diagnostic in the same turn. A prelint `hard_blocker` blocks only
write/finalization, not the active epic, and never authorizes an incomplete
final response. Only the external terminal conditions in `AGENTS.md` may stop
the epic before packet and final audit.

With `--output`, stdout is a bounded summary of at most 8 KB containing counts,
blockers, gates, warnings, calibration and pending acknowledgement stubs. The
complete diagnostic exists only at the declared output path.

The check compiles every proposed review and runs the final autocheck against
the composed candidate state in memory. It does not write the episode or
export. A clean check writes only `clean_preview_receipt.json` in the transient
job directory. Apply requires that exact receipt and rejects a changed payload,
prepared source, revision, export destination, or composed review set before
the recorder writes. The finalizer verifies the same receipt against the
persisted reviews and recorder receipt.

When the payload is already believed to be clean, `--one-shot` performs the
same preview, writes its receipt, persists once, finalizes, and emits
`final_audit_dossier.jsonl` in one Python process and therefore one direct WSL
invocation. It never bypasses the compiler or autocheck. The public packet
continues to contain exactly five files; the source-complete audit dossier stays
job-local and is self-verifying.

The optional `payload_format=gold_episode_compact_v1` removes repeated model
boilerplate. Payload- or review-level `candidate_defaults` are inherited;
`id`, `claim`, `takeaway`, `minimal`, and `support` expand to their canonical
fields. Evidence selectors may use `{"range": [start_clean_index,
end_clean_index]}`. The compiler still derives every quote verbatim from the
transcript and never normalizes quoted text.

`payload_format=gold_episode_compact_v3` is the preferred authoring format. It
adds short authoring-only keys, episode/type defaults, compact evidence ranges
and numbers, and local relation aliases. The compiler deterministically
expands v3 to v2 before canonical validation, stable ID assignment and review
hydration. Persisted schemas do not change and verbatim quotes are still
derived only from transcript segments. V2 remains accepted for compatibility.

For v3 candidates, use the context checklist before prelint: procedures,
frameworks and scripts need explicit steps; material numbers need literal raw
text; reported quantitative cases need honest attribution/risk/caveats;
relations must be symmetric and acyclic; broad evidence needs atomic ranges or
a source-backed reason.
Every material numeric mention is reconciled separately against `numbers`.
Partial capture does not close the candidate, repeated before/after values keep
their multiplicity, and ASR-separated decimals retain literal raw with
`value_status=inferred` plus a caveat. Support-only incidental numbers remain
audit warnings unless they belong to the retained proposition.

The compatible model input is `payload_format=gold_episode_compact_v2`.
Candidates live once at episode level, identify their owning chunk with the
numeric `chunk` field, and may omit candidate ids. The compiler assigns stable
ids, hydrates canonical reviews and hashes, creates explicit reviews for
`zero_insight_chunks`, and resolves clean-index selectors back to exact
transcript quotes. Exact canonical segment ids take precedence over aliases.

Before packet creation, autocheck scores contiguous excluded signal spans.
High-risk spans remain model-review items, never automatic candidates. Compact
v2 drafts must capture the proposition or include a
`risk_recall_acknowledgements` item with `disposition=incidental` and a
non-empty source-based justification.

The compact context includes a deterministic `semantic_route_map` and baseline
`risk_recall_index` before the transcript rows. Prelint evaluates a read-only
fixed point: current candidate evidence, the ledger that those candidates would
derive, and risk clusters exposed if support-only evidence were removed. Each
cluster keeps a stable source lineage (`source_cluster_id`, original segment
IDs and source semantic hash) plus the current residual IDs/hash. A disposition
may be reused only for a residual subset of the same source cluster; newly
exposed material remains pending. When one source cluster contains both
retained support and an incidental residual, acknowledgements carry their
reviewed segment scope and the most specific matching scope wins.
Support-only coverage therefore needs an explicit `retained_support`
acknowledgement before apply. Every `claim_evidence_alignment` warning also
receives a stable `warning_id` and must be dispositioned as
`confirmed_source_backed` or `defer_to_final_audit`, with a non-empty
source-based justification. The warning remains visible and non-blocking.

Normal CLI output is a sparse recall view: unresolved signals, numeric gaps,
calibration defects, questionable exclusions, boundaries, overlaps, and audit
warnings. Use `--full-output` only for deterministic debugging. Do not create a
separate full recall matrix or episode-specific audit probe.

The job session records UTC wall-clock elapsed time from the outer launcher
before runtime sync through generated closeout, across separate WSL invocations,
and uses a monotonic clock only inside each process. It durably counts
selections, context generations, prelints, checks, applies, review writes,
finalizers, builds, audit bundles, audit registrations and required-audit
validations. Elapsed time must never be negative. The command also reports
measured milliseconds for each deterministic phase. These metrics describe the current command;
they must not be extrapolated into invented historical time or token usage.
Terminal completion also writes `runtime_retrospective.md`, separating phase
active wall time, measured command time, measurable model judgment,
inter-turn idle, phase transitions and bytes of
context, payload, prelint report and audit dossier under the same `run_id`.
For an episode too large for one semantic pass, use the existing chunk-batch
fallback, but still consolidate diagnostics before any corrective write.

### Runtime parity and source-only policy

The Windows checkout is the authoring source and the Linux-native checkout is a
complete Git clone plus a verified mirror of the current tracked and untracked
worktree. Before a real WSL gold command, run `scripts/invoke_gold_wsl.ps1`.
The parity receipt records independent `execution_signature` and
`documentation_signature` values. Only execution drift blocks a gold write;
documentation drift remains visible and is synchronized outside the measured
episode window.
Action `Clone` creates the Linux-native clone once; `StartEpisode` captures the
epic start before sync and selects plus bootstraps in one Linux process;
new-run `Sync`, `StartEpisode`, `SelectBootstrap`, and `Bootstrap` actions sync
the complete Git inventory declared by `scripts/gold_runtime_sync_manifest.json`,
never delete destination files, block bilateral drift, and reuse an unchanged
parity receipt without rewriting it. `Fast` and `CompleteAudit` consume the
job-pinned snapshot without synchronizing it. Action `Bootstrap` accepts one JSON request
and writes the compact context and run manifest in one Linux process. The
launcher passes an argument array directly to `wsl.exe --exec`; nested
shell parsing, `bash -lc`, pipes and inline shell programs are not part of the
gold route. WSL startup or parity failure stops that invocation; there is no
Python Windows fallback.

Extraction and final audit are source-only. They may read raw metadata,
transcript, content segments, prepared work orders and current gold state.
Legacy `insights_v2` content, old-insight indexes and pre-gold comparisons are
forbidden in model payloads; protected legacy files are hashed without parsing.
After the packet is frozen, `scripts/benchmark_gold_vs_legacy.py` is the
separate explicit read-only research route.

Finalization always derives the preview ledger from current reviews and
candidates, even when an older packet ledger exists. After a passed final
audit, `scripts.complete_gold_episode.py` performs audit registration, the
completion build and required-audit validation in one Linux process. With a
job directory it also writes `episode_completion_receipt.json`,
`completion_summary.md`, `episode_performance_report.json` and a generated
`final_response.md`. An optional final-only mirror copies those verified
artifacts and the session receipt to the Windows job directory atomically. The receipt binds lifecycle, accepted audit, source
hashes, candidates, calibration, exact packet identity, protected fingerprints
and measured metrics from selection through generated response, and validates
itself before closeout. A valid receipt is terminal authority: it records
`additional_verify_required=false`, so no post-completion Verify/Sync/Verify
sequence runs unless the receipt itself fails or a protected source changes.
It also records the performance band: 6-10 minutes up to 700 segments, 11-15
minutes for 701-1,300, and 18-30 minutes above 1,300.

After a final audit requests changes to an already fully reviewed episode, edit
the same complete authoring manifest and bind its prior semantic hash. Use the
canonical complete-review lane:

```text
python -m scripts.run_gold_episode_fast --video-id <id> --data-root <root> \
  --remediate --authoring-manifest <gold-authoring-manifest.json> \
  --revision-id <new-revision> \
  --export-suffix <suffix> --job-dir <linux-native-job-dir>
```

The command validates the complete semantic snapshot in memory, replaces the
reviews once, rederives ledger/calibration, re-finalizes, writes one remediated
dossier and emits a focal reaudit delta. It never compiles a zero-draft payload,
never applies separate ledger/calibration patches and never calls the initial
pending-chunk recorder. Historical `--patch` remains readable only as a legacy
recovery route.

For episodes above 1,300 segments, preserve the proportional 18-30 minute band
and perform one consolidated semantic-closure pass before the first one-shot.
It checks multi-value numbers, demonstrations and procedures, relation
hierarchies, excluded boundary spans, speaker attribution, calibration and
caveats. This is executor recall, not an intermediate audit.

The final audit surface is dossier schema `3.1.0`. Candidates are ordered by
their first source index, then numeric coverage and calibration precede the
source pass. Transcript rows remain source-complete and verbatim and carry the
derived ledger disposition and candidate destinations inline. Detailed ledger
groups remain independently reconstructible. The header navigates warnings,
the shared semantic workbench, semantic-closure windows, evidence-containment groups, numeric candidates,
calibration links, chunk boundaries and the episode tail. The validator
reconstructs transcript, candidates, ledger and calibration from the dossier;
UTF-8 transcript text is never normalized. Historical dossier `2.1.0` remains
readable.

The autocheck emits one `semantic_workbench` shared by authoring, prelint and
final audit. Its chronological coverage blocks reconstruct every clean index
once and label it `covered`, `merged`, `excluded` or `unreviewed`. Candidate
bindings connect claim terms, exact evidence ranges, number/caveat counts and
calibration targets; calibration bindings expose source intersections and
candidate suggestions without deciding semantic equivalence. Structural source
defects remain hard blockers. Proposition ambiguity remains a reviewed warning.
The source-complete dossier is still authoritative; the workbench is its first
navigation layer and never replaces verbatim transcript rows.

### Frozen runtime and source-canonical authoring

`StartEpisode` pins the certified runtime receipt and execution signature in
the Linux-native job directory. Later Windows-checkout drift belongs to the
next run and does not replace the active runtime. A changed Linux snapshot,
receipt/binding mismatch or execution-signature mismatch blocks before a gold
write. Completion validates the same pinned snapshot; do not synchronize a new
runtime between initial packet and terminal completion.

Compact v3 number records may select `source_segment_id`/`source_clean_index`
and either a character `source_span`, exact `source_literal`, or legacy numeric
`source_occurrence`. Prefer `source_literal`; the compiler copies `raw`
byte-for-byte only when the literal is unique, and requires a span when it is
ambiguous. Authoring selectors are removed before persistence. Unknown themes
remain compiler issues, but the closed vocabulary may expose explicit nearby
suggestions without applying them. Prelint returns one repair manifest with
every current value, expectation and field that still requires semantic
judgment. It never writes a claim, caveat, relation or warning disposition
automatically.

### Semantic closure and final reaudit

Before the first packet, compact fast-lane episodes review a
`semantic_closure_index` covering adjacent evidence tails, the episode tail,
chunk boundaries, claim-support gaps, counterexamples and
evidence-containment groups. Lineage deduplication separates `must_close`
(numeric trajectory, outcome, before/after, mechanism continuation,
counterexample, limitation or unsupported claim element) from `audit_only`
(low-risk overlap/editorial ambiguity). `must_close` is a review gate, not a
generated insight: `captured`/`retained_support` needs candidate IDs and an
`incidental` decision needs a justification plus the exact reviewed source
segment IDs. `audit_only` remains visible to the final auditor without
blocking the executor.

After a final audit requests changes, `run_gold_episode_fast --audit-scaffold`
resolves finding ranges to verbatim transcript segments, source numeric
occurrences, owning review assertions, affected calibration target assertions,
next candidate IDs and current source-canonical candidate asserts without
changing gold. It also emits a single empty transactional patch template; the
model supplies only the semantic updates. After remediation,
`gold_final_audit_bundle --reaudit-delta` emits only
the affected candidates/findings plus integral hashes for transcript,
unaffected candidates, out-of-scope ledger, calibration when unaffected,
packet snapshots and protected fingerprints. Any invariant drift rejects the
delta and requires the full dossier again. The affected set is the union of
explicit audit IDs, the actual candidate diff and inserted candidates whose
evidence intersects a finding range. Transcript invariants contain only source
columns; ledger changes are allowed only inside finding ranges; fingerprint
content excludes volatile verification timestamps.

Before Sol starts, the runtime writes `audit_request_receipt.json` binding the
dossier or focal delta hash, `final_model_review`, `gpt-5.6-sol` and effort
`high` or above. The first post-model operation validates and atomically
materializes a request-bound envelope without writing episode audit state. The
same envelope is consumed by completion. If no envelope exists after an
interruption, `--resume-audit` validates the sealed artifact, marks the old span
`interrupted` and restarts only the Sol phase; extraction, build and dossier are
never repeated. Interrupted spans remain provenance but are excluded from
active semantic time.

Session telemetry starts `semantic_reading_and_authoring` automatically after a
certified episode bootstrap and closes it at prelint. It also uses explicit
start/end spans for
prelint repair, final Sol audit, remediation, reaudit and closeout. Reports
separate semantic wall time, deterministic runtime and phase transitions.
Missing spans are reported as `unattributed_gap_ms`, never mislabeled as idle,
and the wall reconciliation must remain within one second. Terminal completion
generates the timing table and retrospective directly from the validated
receipt; no additional Verify/Sync/Verify closeout is allowed.

The source-complete dossier remains the audit authority. Its deterministic
risk brief is navigation only, groups repeated warnings by lineage, keeps a
compact numeric candidate index, includes only risky numeric detail rows and
must remain below 50 KB for the normal 700-1,300 segment band.

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

## Runtime Contract

Gold extraction runs by default on the Windows-native repository `.venv` and
the external Windows data root. Fast-lane jobs live under the data-root `.tmp`
directory unless an explicit job directory is provided. This is the only
production route a new chat may assume.

WSL 2 remains an opt-in experiment, never a fallback requirement. It must be
selected explicitly with `MSF_GOLD_RUNTIME=wsl_linux` only after a registered
distribution and Linux-native repo/data/temp paths pass
`scripts.verify_gold_runtime.py`. Historical WSL paths, receipts and plans do
not establish that a current machine has Ubuntu installed.

GitHub stores versioned code and contracts; it does not store raw sources,
ignored gold state, packets, audits, or receipts. Supabase is not a backup
mechanism for this filesystem.
