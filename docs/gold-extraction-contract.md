# Gold Extraction Contract

Status: MSF-R20 Phase A

## Purpose

The gold layer is a parallel, evidence-first editorial record. It does not
replace or write to the frozen v2 serving pool. A future owner-approved
migration will map gold candidates into v2 deliberately.

## Route

The supported R20 route is `codex_manual_no_paid_api`. Deterministic tooling
prepares transcript cleanup, chunks, signal inventory, calibrations, work
orders, validation, checkpoints, and audit packets. Codex reads and reviews
each work order. No paid model client is called by the tooling.

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

The compatibility name means external to the executor task. Future R20 audits
are performed by a separate Codex coordinator; historical provider provenance
is retained verbatim. A current report must preserve reviewer identity,
`reviewer_thread_id`, `reviewer_model`, `reasoning_effort`, `audit_route`,
timestamp, status, summary, findings, and open-finding count.

Every finding validates its ID, severity (`critical`, `major`, or `minor`),
status (`open` or `resolved`), category, segment range, candidate IDs, summary,
evidence, and required action. `passed` with any open finding is invalid. The
build derives audit state from a valid `editorial_audit_report.json`; it cannot
accept `passed` as a free assertion. `complete` additionally requires a reviewer
separate from the executor, deterministic validation, and unchanged protected
fingerprints.
