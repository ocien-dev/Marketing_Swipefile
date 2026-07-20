# MSF-R20 Gold Semantic Compiler 004

Status: archived_research_not_for_production
Production status: read_only_benchmark
Date: 2026-07-17

## Objective

Replace the full-episode global reducer from pilot 003 with source-routed
inventory coverage at the original blind shard stage.

## Design

1. Build numeric, calibration and boundary inventories only from transcript and
   calibration source locations, never approved candidates.
2. Route every item to exactly one core shard by its anchor segment.
3. Require a `captured`, `merged` or source-grounded `excluded` disposition
   referencing local atoms when applicable.
4. Dedupe only exact claim/evidence/type duplicates deterministically.
5. Build a compact relation-only window for nearby framework or enumeration
   boundaries, rather than asking a full-episode reducer to infer relations.
6. Create local source windows only for invalid or missing dispositions.

## Expected Benefit

The seven original parallel calls retain their bounded wall time. A future
model rerun should avoid the prior 319.688-second full reducer and invoke a
resolver only for demonstrated gaps. This is a testable architecture change,
not a production adoption claim; a new blind benchmark and final Sol judgment
remain required before adoption.

## Benchmark Result

The read-only benchmark on `AqzF_M2mM04` completed with seven Terra shard
calls and one final Sol audit. The routed inventory closed with zero unresolved
dispositions, so no targeted gap calls were needed. However, the final audit
found three material issues: one omitted format test, one unsupported
attribution joining two cases, and one missing causal caveat.

The shard wall time was 151.58 seconds, but the final Sol audit took 259.41
seconds. The combined model wall time therefore did not establish the intended
speed improvement, and the adoption gate rejected the architecture:
`material_recall=0.8824`, `unsupported_claim_count=1`, and
`open_finding_count=3`. The relation-window diagnostic also produced 29
windows, too broad to add as a routine second model pass. Keep this lane as a
research artifact; do not route production gold episodes through it yet.

Final architecture decision: do not continue this branch as the production
extractor. Its proven deterministic controls were promoted into
`chronological_hybrid_v1`; shard generation, reducers and relation/gap model
passes remain archived read-only research.
