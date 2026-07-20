# MSF-R20 Gold Canonical Hybrid Architecture 001

Status: implemented
Production architecture: `chronological_hybrid_v1`
Date: 2026-07-17

## Decision

All new gold episodes use one full chronological semantic pass. Deterministic
artifacts guide and verify that pass but never replace it. The blind semantic
compiler experiments are archived read-only research because none reached the
quality gate.

## Canonical Flow

1. Start the certified Linux-native WSL runtime and select the next queue item.
2. Read the complete chronological context and use the semantic index only for
   navigation.
3. Author one atomic, source-backed episode payload.
4. Close the `semantic_workbench`, numeric occurrence matrix, calibration
   bindings, chunk boundaries and scoped risk dispositions.
5. Treat exact source/claim/type duplicates as a blocker requiring an explicit
   semantic decision; never auto-merge them.
6. Run the consolidated prelint until `hard_blockers=0`.
7. Persist and finalize once through `--one-shot`.
8. Run one final Sol audit on the source-complete dossier. Remediate its closed
   findings transactionally, then complete only after passed/zero findings.

## Promoted Controls

- source-first inventory of numeric occurrences;
- one source owner through the existing chunk/route map;
- explicit captured, retained-support or source-scoped incidental disposition;
- candidate/evidence/calibration bindings in the semantic workbench;
- exact duplicate detection without automatic semantic merge;
- local review of demonstrated closure gaps rather than a second broad scan.

## Archived Research

The following modules are not in the executable runtime signature:

- `scripts/gold_semantic_compiler.py`;
- `scripts/gold_semantic_adapter_benchmark.py`;
- `scripts/gold_semantic_global_reducer.py`;
- `scripts/gold_semantic_inventory.py`.

They may be used only by an explicitly authorized read-only research epic. They
must not read or write a live gold episode as part of normal processing.

## Acceptance

- context and bootstrap receipts identify `chronological_hybrid_v1`;
- exact candidate duplicates block pre-persistence;
- runtime sync classifies semantic-compiler modules as research-only;
- contract, prompt, AGENTS and both execution skills name the same route;
- focused and full gold regressions pass in WSL;
- no real gold data or packet changes during implementation.
