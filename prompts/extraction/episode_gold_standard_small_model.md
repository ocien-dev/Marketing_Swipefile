# Gold-Standard Episode Re-Extraction - Small Model Task Prompt

You are working in this repository:

`C:\Users\luish\OneDrive\Code\Marketing_Swipe_File`

Your task is to reprocess exactly one podcast episode as a gold-standard,
exhaustive extraction. The specific episode binding (video ID, data root,
title, any suspected source defects and any pre-identified calibration probes)
is supplied per episode by a work order, not by this prompt:

- Per-episode work order: `prompts/extraction/episode_work_order_template.md`
  (fill one per episode; the original L7u7r6rOl68 seed is preserved in
  `prompts/extraction/episode_work_order_L7u7r6rOl68.md`).
- Single normative source for the extraction rules:
  `docs/gold-extraction-contract.md`. Where this prompt and the contract
  overlap, the contract governs.

## Objective

Extract every useful, evidence-backed marketing insight from this episode,
including principles, tactics, numbers, benchmarks, before/after experiments,
procedures, scripts, VSL structure, offer details, funnel economics, creative
testing, ascension, retention, caveats, and failure modes.

This is a recall-first inventory followed by quality control. Do not optimize
for a short list of polished ideas. Do not stop after finding a few strong
insights. A broad principle must not replace its concrete child tactics.

The current 14-item v2 file is a precision-first shortlist, not an exhaustive
source. Preserve it unchanged for comparison.

## Scope Boundary

- Work only on the single episode named in the work order (`<video_id>`).
- Do not process or scale to other episodes.
- Do not modify Supabase or any remote system.
- Do not overwrite `insights_v2.json`, curated exports, or master exports.
- Do not publish, commit, push, or deploy unless explicitly requested.
- Generated gold-standard artifacts must remain separate from the current v1
  and v2 sources.
- Extraction and final audit are source-only. Do not open, summarize, index or
  compare legacy insight content before the gold packet and audit are frozen.
  Legacy files may be fingerprinted as protected bytes without parsing them.
- Preserve unrelated user changes already present in the worktree.
- This prompt defines the complete executor phase in the active chat. Do not
  create coordinator/worker tasks or intermediate review handoffs.
- `awaiting_external_audit` means external to the executor phase and remains the
  lifecycle name for compatibility. The only review boundary is the final audit
  after the whole epic is ready. Do not rename it.
- The future gate is Codex-only. Do not request Claude permission, execution,
  or audit; preserve any historical provider provenance without rewriting it.

## Required Reading

Read these files once before acting:

1. `docs/gold-extraction-contract.md`
2. `skills/marketing-swipe-file-scale-batch/SKILL.md`
3. prepared gold work orders for the active episode
4. current raw metadata, transcript and content segments

Preparation also creates `processed/<video_id>/transcript_semantic_index.jsonl`
and its status file. Use the bounded index summary to prioritize numeric
trajectories, mechanisms, outcomes, caveats, speaker-role risks and chunk
boundaries. It is navigation only: read the complete chronological transcript,
preserve each source quote verbatim and never turn an index cue into a claim.

Legacy prompts, schemas and prior insight files are not execution context for
gold. A separate post-gold benchmark may read them only after packet freeze.

Use the existing repository conventions where they are useful, but do not
inherit the v2 rule that says "quality, not inventory" or its five-insight cap.

## Known Problems To Verify

Suspected source defects are episode-specific. Read them from the per-episode
work order (`Known problems to verify` section) and verify each against the
files before trusting it — never assume a listed defect is correct, and never
invent one. Typical classes: contaminated recommended-video titles captured
after the real transcript, timestamps that move backward, chunks whose start
time is greater than their end time, and precision-first v2 undercounting.

## Non-Negotiable Evidence Rules

- Never invent or repair a number from memory.
- Keep every evidence quote verbatim in UTF-8.
- Every retained claim must have a segment ID or segment range and timestamps.
- If adjacent segments complete one claim, use the complete range.
- Separate what the speaker reported from what the evidence proves.
- Performance numbers are reported cases, not universal guarantees.
- Mark causal uncertainty when a speaker says a change increased conversion but
  does not provide a controlled test or complete baseline.
- Internal editorial fields must follow the repository ASCII policy. Final
  owner-facing Portuguese must preserve normal pt-BR accents.

## Execution Protocol

Work through the complete epic in the active chat. Batches are atomic
persistence units, not handoff or review boundaries.

### Episode Finalization Guardrails

The only production architecture is `chronological_hybrid_v1`. Read the entire
episode chronologically and author the final candidates in that pass. Use the
semantic index, workbench, numeric occurrence matrix, calibration bindings and
boundary inventory as deterministic controls only. Never invoke the blind
semantic compiler, shard reducer, relation-window model or gap-resolver research
lane for a real episode.

For a Fast Path episode, retain the full reading and semantic-recall standard
while minimizing duplicated context. First run the Windows-native runtime
preflight with `.venv\\Scripts\\python.exe -m scripts.verify_gold_runtime
--runtime windows_native`. When the episode fits the active context, start the
official fast runner directly from that `.venv`, then read
the generated `episode_context.jsonl` from first to last record. Confirm its
`transcript_semantic_index.status=ready`; missing or stale derived navigation
does not authorize a read-only backfill on a protected episode. Produce one
`gold_authoring_manifest_v1` and pass it with `--authoring-manifest`;
candidates appear once, use the numeric `chunk` owner, defaults, clean-index
ranges, shorthand numbers, local relation aliases and explicit
`zero_insight_chunks`. V3 authoring keys expand deterministically to v2 before
validation; persisted schemas do not change. Never type or normalize a quote.
Before prelint, check each candidate: procedures/frameworks/scripts have steps;
material numbers preserve literal raw; reported quantitative cases preserve
attribution, risk and caveats; relations are symmetric/acyclic; broad evidence
is narrowed or justified.
Reconcile every material numeric mention in minimal and proposition-bearing
support evidence against an individual `numbers` record. A candidate is not
closed merely because one record exists. Preserve repeated before/after values
and sequence multiplicity. For ASR-separated decimals such as `86,8 5%`, keep
the literal raw, use `value_status=inferred`, and add a caveat; ratios such as
`1.2x` remain independent records.
Review every high-risk excluded cluster: capture the supported proposition or
acknowledge it as incidental with a non-empty source-based justification.

Run pure `--dry-run --authoring-manifest` while authoring, then use `--prelint`
once the complete manifest is believed to be closed. Repair the consolidated in-memory inventory
for procedural steps, literal numbers, evidence scope and risk
acknowledgements. It must not create a preview receipt. Dry-run also must not
write session telemetry. Both evaluate evidence/ledger/risk to a fixed
point. Preserve support-only evidence with a `retained_support` acknowledgement,
and disposition every claim-evidence warning by its stable `warning_id` as
`confirmed_source_backed` or `defer_to_final_audit` with a source-based reason.
When `--output` is present, use the bounded stdout inventory first. Open the
full report only for a blocker or genuinely new diagnostic; do not reload the
transcript from that report. Risk acknowledgements bind to stable source
lineage and remain valid for residual subsets, but never for new material.
If retained support and an incidental residual share one source lineage, keep
separate scoped acknowledgements; do not collapse them into one disposition.
Treat numeric trajectory, outcome, before/after, mechanism continuation,
counterexample, limitation and claim-support gaps as `must_close`. An
`incidental` disposition for those items must name every reviewed source
segment. Low-risk overlap/editorial ambiguity remains `audit_only` and visible
to the final auditor without blocking finalization.
`needs_revision`, compiler issues, `hard_blockers`, and `review_gate` from
dry-run/prelint are local repair inventory, not permission to end the task.
Continue in the same epic: repair the same source-backed manifest, repeat the
read-only diagnostic, and proceed to one-shot. Do not emit a final response
until completion/audit succeeds or a genuine external terminal condition from
`AGENTS.md` occurs.
After prelint is clean, use `--one-shot`: it creates the receipt, persists,
finalizes, and emits dossier v2 in one process. Separate `--check` and `--apply`
are recovery/debug routes, not the normal sequence. Do not call recorder,
autocheck, build, or an episode-specific audit probe separately on this route.
Use review batches of 8-12 chunks only as a fallback for an episode that cannot
fit safely in one semantic pass.
For numeric selectors prefer exact `source_literal` or `source_span` bound to a
source segment; use ordinal `source_occurrence` only for legacy compatibility.
Ambiguous literals must be rejected, not guessed. Do not infer a WSL runtime
from the integrated terminal shell; WSL is optional and only an explicitly
certified Linux route may use `scripts/invoke_gold_wsl.ps1`. After a passed
final audit, use the one-process
`scripts.complete_gold_episode` route and require its completion receipt,
performance report and generated final response. Mirror only these final
verified artifacts to Windows when a mirror job directory is supplied. A valid
completion receipt is terminal; do not run an extra Verify/Sync/Verify cycle.
The generated runtime retrospective is the timing authority: it separates
active wall time, deterministic command time, measurable model judgment,
inter-turn idle, phase transitions and artifact bytes under
the episode `run_id`; do not reconstruct timing manually.
Before the packet, finish the episode through one consolidated diagnostic and
one adversarial executor pass. The manifest must review evidence/numeric
ownership, excluded material, host attribution, before/after mechanisms and
outcomes, calibration equivalence, boundaries and counterexamples. Record the
pass against `authoring_decisions_sha256`; any semantic edit invalidates it.
Reviews, ledger, calibration and workbench are derived from this manifest.
Never create job-local Python helpers, `ledger_updates`, calibration redirects
or direct review edits in the normal route.

Hard blockers such as unsupported evidence, invalid ledger destinations,
relations, or calibration targets stop finalization. Editorial ambiguity,
possible promo/interviewer support, overlap, caveats, and semantic calibration
uncertainty remain audit warnings. Warnings stay visible in the five-file
packet manifest for the final audit; they are not a reason to stop or emit an
intermediate handoff.

For an episode above 1,300 transcript segments, do not force the reading pass
into the short-episode target. Before the first one-shot, perform one
consolidated semantic-closure pass over multi-value numbers, proof
demonstrations, procedures, parent/child decompositions, excluded boundary
spans, speaker attribution, calibration equivalence and caveats. This replaces
repeated post-audit discovery; it is not an intermediate audit.

If the final audit requests changes after every chunk is already reviewed, edit
the complete authoring manifest, bind `base_manifest_semantic_sha256` and use
`run_gold_episode_fast.py --remediate --authoring-manifest <manifest>` with a
new `revision_id`. The runtime replaces the semantic snapshot once, derives all
outputs, creates one remediated dossier and emits the focal reaudit delta.
Do not build a parallel patch API. `changes_requested` is an internal
`remediation_required` state: it must not create `final_response.md` or close
the epic. Continue through remediation, a fresh dossier, reaudit, and only then
completion after `passed/open_findings=0`.
The one-shot seals dossier hash, route, model and effort in
`audit_request_receipt.json`. Materialize the Sol response immediately as a
bound envelope before any lifecycle write. On interruption without envelope,
use `--resume-audit`; it restarts only Sol and marks the abandoned span
`interrupted`. Completion consumes the materialized envelope whose request and
artifact hashes match. Do not route an optional WSL audit through UNC or
`/mnt/c`.

For a multi-episode wave, batch and episode completion remain internal to the
active execution. Compile each complete episode read-only first, repair the
consolidated source-backed inventory, persist one atomic clean episode payload,
and continue to the next episode. The final audit begins only after a
consolidated wave receipt proves every manifest episode final-packet ready or
terminally blocked. An in-progress wave is read-only at this gate: it never
creates or overwrites a delivery receipt. The finalization receipt must point
to the manifest export destination and to a five-file packet whose manifest
identifies the same episode.

### Phase 1 - Inspect And Clean The Source

1. Load the current transcript and metadata from the live data root.
2. Identify the real transcript boundary using monotonic timestamps, video
   duration, transcript structure, and content relevance.
3. Produce a clean transcript copy. Do not destroy or overwrite the original.
4. Record every removed segment with its ID, text, and removal reason.
5. Add or propose deterministic safeguards for:
   - timestamps that move backward;
   - implausibly long segment durations;
   - timestamps outside the video duration;
   - unrelated recommendation titles captured after the transcript;
   - chunks whose start time is greater than their end time.
6. Add focused tests if code is changed.

### Phase 2 - Create Extraction-Sized Chunks

Create clean, chronological, non-overlapping chunks. Prefer topic boundaries,
but split large chapters further.

Targets:

- approximately 5-10 minutes per chunk;
- preferably no more than 12,000 transcript characters per chunk;
- chronological segment order;
- no unrelated titles or promotional end-screen material;
- no gaps or overlaps in the real transcript coverage.

Write a chunk index that reports segment IDs, time range, character count, and
coverage continuity. If the runtime data root is not writable in the sandbox,
request narrowly scoped permission. Do not silently write to a different data
root.

### Phase 3 - Build A Recall-First Candidate Inventory

Read chunks chronologically, then persist each complete review range atomically
after a read-only compiler check. Continue immediately after each range; do not
emit a handoff for a chunk, range, or finished episode.

For each chunk, perform all of these passes in order:

1. Quantitative pass:
   capture money, percentages, counts, prices, timeframes, cadence, volume,
   conversion, ROI, retention, audience size, test counts, and before/after
   values.
2. Causal and experiment pass:
   capture every "changed X, then Y increased/decreased" statement, including
   what changed, baseline, result, and uncertainty.
3. Procedure pass:
   capture sequences, checklists, formulas, decision rules, production routines,
   and step-by-step instructions.
4. VSL and copy pass:
   capture lead structure, mechanisms, proof, argument order, offer transition,
   pitch, price anchoring, bonuses, guarantee, FAQ, CTA, closing, discount,
   retention, and exact reusable scripts or phrases.
5. Funnel and economics pass:
   capture acquisition, front-end, upsell, downsell, backend, high-end,
   workshops, launches, sales team, support, refund prevention, and ascension.
6. Traffic and creative pass:
   capture creative formats, testing cadence, budgets, validation criteria,
   winner preservation, recombination, and scaling rules.
7. Caveat pass:
   capture when a tactic should not be generalized, ethical issues, missing
   baselines, failure cases, dependencies, and speaker uncertainty.
8. Gap pass:
   re-read the chunk and find any useful claim not represented in the candidate
   list.

There is no maximum candidate count. Return zero only when a clean chunk truly
contains no actionable or decision-useful content.

### Phase 4 - Candidate Contract

Each atomic candidate must contain at least:

```json
{
  "candidate_id": "<video_id>-candidate-0001",
  "chunk_id": "string",
  "title_ptbr_ascii": "specific title",
  "claim_kind": "principle | tactic | playbook_step | framework | quantitative_case | test_result | copy_pattern | script | warning | example",
  "topic_lenses": ["VSL"],
  "statement_ptbr_ascii": "what the source says",
  "actionable_takeaway_ptbr_ascii": "what a practitioner can do",
  "source_context_ptbr_ascii": "business, funnel, product, and condition context",
  "reported_case": true,
  "causal_certainty": "direct_test | speaker_attribution | correlation | unclear | not_applicable",
  "claim_risk": "low | medium | high",
  "numbers": [
    {
      "metric": "string",
      "value_original": "string",
      "unit": "string or null",
      "timeframe": "string or null",
      "baseline": "string or null",
      "result": "string or null",
      "change": "string or null",
      "context": "string"
    }
  ],
  "steps": ["ordered step"],
  "conditions": ["condition required for use"],
  "caveats": ["limitation or uncertainty"],
  "parent_candidate_id": null,
  "related_candidate_ids": [],
  "evidence": [
    {
      "segment_start_id": "string",
      "segment_end_id": "string",
      "start_seconds": 0,
      "end_seconds": 0,
      "quote_original": "verbatim quote"
    }
  ]
}
```

Atomicity rules:

- Split independent claims into separate candidates.
- Keep one experiment and its tightly related measurements together.
- Keep a broad principle and its concrete implementations as parent and child
  candidates instead of deleting the children.
- Distinct prices, cadences, scripts, funnel stages, or conditions are not
  duplicates merely because they support the same broad idea.
- Deduplicate only exact or genuinely equivalent claims after extraction.

### Phase 5 - High-Signal Coverage Ledger

For every transcript segment or segment range containing a number, comparison,
causal claim, instruction, sequence, copy element, experiment, or warning,
write a ledger item:

```json
{
  "segment_range": "segment-0001..segment-0003",
  "signal_types": ["number", "test_result"],
  "disposition": "captured | excluded | merged",
  "candidate_ids": ["<video_id>-candidate-0001"],
  "reason": "required when excluded or merged"
}
```

No high-signal ledger item may remain without a disposition. A chunk is not
complete while it has an uncovered high-signal segment.

### Phase 6 - Normalize Without Losing Detail

After all chunks are inventoried:

1. Merge only true duplicates.
2. Preserve all evidence ranges from merged candidates.
3. Create parent-child relationships for broad principles and microtactics.
4. Keep quantitative reported cases even when they should not become universal
   recommendations.
5. Produce a rich exhaustive insight file separate from `insights_v2.json`.
6. Do not use a target insight count as a completion criterion.

### Phase 7 - Executor Coverage Check

Run a second transcript-to-output pass whose only job is to find omissions.
This is deterministic coverage validation inside the executor phase, not the
final Sol audit.

The audit must explicitly check:

- every currency, percentage, count, price, period, and before/after value;
- every use of language such as "we changed", "increased", "decreased",
  "doubled", "tripled", "converted", "tested", or "validated";
- every numbered list or implied sequence;
- every concrete VSL, offer, traffic, creative, funnel, ascension, or retention
  tactic;
- every script, analogy, wording pattern, and decision rule;
- every important caveat or failure report.

Any omission found must be added to the inventory and the audit rerun. Stop only
when the audit reports zero uncovered high-signal claims.

Use compact-v3 source selectors for material numbers instead of retyping their
source form. Point each record at the evidence `segment_id` or clean index and
select a literal character span or numeric occurrence. The compiler must copy
`raw` byte for byte; never normalize a number quote.

Before finalization, resolve every item in `semantic_closure_index`: adjacent
evidence tails, the episode tail, chunk boundaries and evidence containment.
Use `captured` or `retained_support` only with a candidate that expresses the
same proposition. Use `incidental` with a source-based reason, or
`relation_not_useful` for a containment group that is not a useful hierarchy.
Do not create a claim or relation merely to silence the gate.

Use `semantic_workbench` as the single source-first navigation surface before
apply. Reconstruct every clean index through its coverage blocks, then close
`must_close` items in `review_order`. For each candidate, compare the claim to
the exact evidence ranges, number records, caveats and calibration links in
`candidate_bindings`. For each target, confirm the same proposition through
`calibration_bindings`; a shared topic is not sufficient. Structural source
errors block. Genuine semantic ambiguity remains an audit warning with a
source-based disposition.

This pass must validate semantic destination, not only ledger presence. For
each `captured` or `merged` signal, confirm that the referenced candidate states
the same useful proposition. A candidate about the same topic or a nearby
number is not sufficient. Read adjacent chunk boundaries together to catch a
claim whose setup is a story, mechanism, or example and whose conclusion is an
offer transition, pitch, result, retention effect, condition, or caveat.

## Mandatory Calibration Checks

Pre-identified calibration probes are episode-specific. Read them from the
per-episode work order (`Mandatory calibration checks` section). Treat each as
a calibration probe, not as the complete answer: capture it separately only if
the clean transcript confirms it verbatim, and never force it into the output
when the transcript does not support it. If a listed probe is not found,
document the search and the evidence result. When the work order lists no
probes, run the standard recall passes without them.

## Required Artifacts

Write gold-standard outputs under a separate episode subdirectory such as:

`C:\MSF-data\Marketing_Swipe_File\processed\<video_id>\gold_extraction\`

Required files:

1. `transcript_clean.json`
2. `removed_segments.json`
3. `chunks\chunk_index.json` and clean chunk files
4. `candidate_chunks\chunk_###_candidates.json`
5. `gold_extraction_status.json`
6. `candidate_claims_master.json`
7. `insights_exhaustive.json`
8. `quantitative_claims.csv`
9. `high_signal_coverage_ledger.json`
10. `coverage_report.md`
11. `validation_report.md`

If repository code or tests are changed, report the exact changes, validations,
remaining risks, and scope in the active chat. Update `docs/execution-log.md`
when the epic contract requires it.

## Validation Requirements

Before declaring completion, verify:

- the original transcript remains unchanged;
- the clean transcript is chronological and within video duration;
- no cleaned chunk has start time greater than end time;
- clean chunks cover every retained transcript segment exactly once;
- every evidence quote exactly matches the clean transcript;
- every numeric claim in the inventory appears in the quantitative CSV;
- every high-signal segment has a ledger disposition;
- the executor coverage pass reports zero uncovered high-signal claims;
- current `insights_v2.json` and curated/master exports are unchanged;
- focused tests and existing relevant validators pass.
- the episode remains `awaiting_external_audit` until the dedicated final Sol
  audit records a valid passed report with zero open findings.

The final Sol pass consumes dossier v3.1 by reading the semantic workbench
first, then candidates, numeric
coverage/calibration, then the complete transcript with inline ledger. After a
changes-requested audit, update the same source-canonical authoring manifest and
reaudit its automatically generated focal delta; return to the full dossier
whenever an integral invariant changes.

## Final Response

Report in concise, fully accented pt-BR:

- total clean and removed segments;
- total chunks;
- total candidate claims and final exhaustive insights;
- counts by claim kind and topic lens;
- total quantitative claims;
- examples of important insights recovered beyond v2;
- coverage audit result;
- files changed and artifacts created;
- validations run;
- any remaining uncertainty or blocker.

Do not describe the episode as exhaustively extracted unless every validation
requirement above passes.
