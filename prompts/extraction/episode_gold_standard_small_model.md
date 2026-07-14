# Gold-Standard Episode Re-Extraction - Small Model Task Prompt

You are working in this repository:

`C:\Users\luish\OneDrive\Code\Marketing_Swipe_File`

Your task is to reprocess exactly one podcast episode as a gold-standard,
exhaustive extraction:

- YouTube video ID: `L7u7r6rOl68`
- Live data root: `C:\MSF-data\Marketing_Swipe_File`
- Episode title: `Lucrando Multiplos 7D/Mes Com Perpetuo White (Aos 21 Anos!) | Lucas Ramos - Segredos da Escala #140`

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

- Work only on episode `L7u7r6rOl68`.
- Do not process or scale to other episodes.
- Do not modify Supabase or any remote system.
- Do not overwrite `insights_v2.json`, curated exports, or master exports.
- Do not publish, commit, push, or deploy unless explicitly requested.
- Generated gold-standard artifacts must remain separate from the current v1
  and v2 sources.
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

1. `skills/marketing-swipe-file-extract-insights/SKILL.md`
2. `docs/insight-quality-checklist.md`
3. `prompts/extraction/base_insight_extraction_v2.md`
4. `scripts/collect_youtube_transcript_from_playwright_snapshot.py`
5. `scripts/create_extraction_chunks.py`
6. `schemas/insights_v2.schema.json`

Use the existing repository conventions where they are useful, but do not
inherit the v2 rule that says "quality, not inventory" or its five-insight cap.

## Known Problems To Verify

Do not assume these statements are correct without checking the files, but use
them as a focused starting point:

- The source transcript contains 1,980 segments.
- The first 1,941 segments appear to be the real episode.
- The final 39 segments appear to be unrelated recommended-video titles
  captured by the YouTube UI snapshot collector.
- Those contaminated segments entered several chunks and produced malformed or
  misleading time ranges.
- The current v2 extraction produced one insight in 14 chunks and zero in two
  chunks, despite allowing up to five.
- Existing validation measured schema validity, exact quotes, title uniqueness,
  and promo noise, but did not measure insight recall.

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

For a Fast Path episode, retain the full reading and semantic-recall standard
while minimizing duplicated context. When the episode fits the active context,
produce one complete episode payload and run `run_gold_episode_fast.py --check`.
Repair the complete in-memory inventory before the first write, then use one
`--apply` to persist and finalize. Use review batches of 8-12 chunks only as a
fallback for an episode that cannot fit safely in one semantic pass.
Before the packet, finish the episode through one consolidated diagnostic and
source-backed remediation. A post-persistence correction uses a transactional patch with a
non-empty `revision_id`, `revision_kind`, and `reason`, followed by one
read-only check and one atomic apply. Preserve assertions, provenance and
idempotence; do not create an artificial patch-count gate. Keep physical file
hashes for provenance, but compare parsed JSON semantically so CRLF and LF
alone do not create a false editorial delta.

Hard blockers such as unsupported evidence, invalid ledger destinations,
relations, or calibration targets stop finalization. Editorial ambiguity,
possible promo/interviewer support, overlap, caveats, and semantic calibration
uncertainty remain audit warnings. Warnings stay visible in the five-file
packet manifest for the final audit; they are not a reason to stop or emit an
intermediate handoff.

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
  "candidate_id": "L7u7r6rOl68-candidate-0001",
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
  "candidate_ids": ["L7u7r6rOl68-candidate-0001"],
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

This pass must validate semantic destination, not only ledger presence. For
each `captured` or `merged` signal, confirm that the referenced candidate states
the same useful proposition. A candidate about the same topic or a nearby
number is not sufficient. Read adjacent chunk boundaries together to catch a
claim whose setup is a story, mechanism, or example and whose conclusion is an
offer transition, pitch, result, retention effect, condition, or caveat.

## Mandatory Calibration Checks

The final inventory must capture these source claims separately if the clean
transcript confirms them. Treat them as calibration checks, not as the complete
answer:

- approximately 15,000 front-end buyers per month;
- approximately 10 VSL lead variants tested per month;
- one winning lead out of five in the cited scaled VSL case;
- a post-price bonus with a 60-second timer and its reported conversion effect;
- extending a VSL from approximately 18 to 25 minutes with about seven extra
  minutes of closing content;
- a delayed button with a reported 15-20 percent discount;
- the price movement from approximately BRL 200 to BRL 160;
- the report that about half of sales occurred at the discounted price;
- approximately 500 buyers entering per day;
- weekly workshop attendance and conversion figures;
- the business effect of 5, 10, or 15 percent conversion improvements at high
  volume.

Do not force these into the output if the transcript does not support them
verbatim. If any are not found, document the search and evidence result.

## Required Artifacts

Write gold-standard outputs under a separate episode subdirectory such as:

`C:\MSF-data\Marketing_Swipe_File\processed\L7u7r6rOl68\gold_extraction\`

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
