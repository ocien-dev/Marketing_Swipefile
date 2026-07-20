# MSF-R20 Gold Semantic Compiler 001 - Retrospective

Status: archived_research_not_for_production
Episode: `NiT0-ABoVnk`
Date: 2026-07-17

Canonical production route: `chronological_hybrid_v1`; this document is
historical benchmark evidence only.

## Result

The read-only prototype validated the mechanical architecture against the final
source-complete dossier of the last audited episode.  It did not call a model
and therefore does not claim independent semantic quality.

Measured result:

- 1,087 source segments;
- 18 chronological shards at eight-worker concurrency;
- 1,087 core assignments, with exactly one owner per segment;
- 59/59 approved candidates reproduced byte-semantically;
- 176 verbatim candidate-to-source proof edges;
- zero reducer or evidence errors;
- cold deterministic compile on the official Linux runtime: 38.079 ms;
- warm deterministic compile on the official Linux runtime: 12.430 ms;
- complete Linux benchmark: 105.614 ms;
- warm cache: 18 hits, zero misses, zero cache rewrites;
- complete dossier: 844,579 bytes;
- targeted audit surface: 164,407 bytes;
- byte reduction: 80.53%;
- source-segment reduction: 83.99%.

The audit plan still selected all 59 candidates because the approved candidates
carry caveats, numbers, procedures, calibration bindings, or warnings.  The
meaningful reduction came from source localization: only 174 of 1,087 segments
were needed beside those candidates.

The focused Linux suite passed `7/7` tests in 0.08 seconds.  Runtime parity
synchronized five files without conflict and now tracks 25 execution files,
including `scripts/gold_semantic_compiler.py`.

## What was proved

- transcript sharding can preserve strict chronological ownership;
- boundary overlap does not duplicate semantic ownership;
- proof-carrying atoms can recreate the approved candidate projection without
  losing evidence or provenance;
- a cache keyed by source and compiler signatures is idempotent;
- the reducer can reject non-verbatim evidence, asymmetric relations, duplicate
  atoms, missing sources, and cycles;
- a risk-targeted dossier can be about five times smaller than the current
  source-complete dossier;
- oracle-free shard requests can be generated without candidate IDs or approved
  gold content.

## What was not proved

- no independent model interpreted the shards;
- semantic recall, unsupported-claim rate, and final Sol finding rate were not
  measured;
- the 4-8 minute target remains an architectural feasibility range, not an
  observed end-to-end result;
- WSL was hidden inside the managed sandbox but available through the approved
  direct route.  Its environment verifier passed with Linux-native repository,
  data root, temp, and virtualenv.  The benchmark itself still used only the
  frozen job-local dossier and did not write the active data root.
- the three protected source hashes and all five packet hashes were rechecked
  against the approved completion receipt and remained byte-for-byte equal.

With 18 shards and eight concurrent workers, the semantic extraction needs
three parallel batches.  At 30, 60, or 90 seconds per model call, extraction
would take approximately 90, 180, or 270 seconds before reduction and audit.
These are scenarios, not measured model latencies.

## Decision

The architecture has enough mechanical evidence to continue, but it must not
replace the current production path yet.  The next gate is an independent blind
adapter benchmark on three completed episodes.  The adapter must see only
`shard_requests.jsonl`; the approved candidates remain hidden until scoring.

Production adoption requires:

1. material recall non-inferior to the approved gold;
2. zero unsupported claims and non-verbatim evidence;
3. number, procedure, caveat, relation, and calibration recall non-inferior;
4. no increase in final Sol findings;
5. observed end-to-end wall time below ten minutes on the standard episode band.

## Artifacts

Windows mirror:

- `.codex-work/worker-jobs/MSF-R20-GOLD-SEMANTIC-COMPILER-001/NiT0-ABoVnk-v3/benchmark_report.json`;
- `.codex-work/worker-jobs/MSF-R20-GOLD-SEMANTIC-COMPILER-001/NiT0-ABoVnk-v3/shard_requests.jsonl`;
- `.codex-work/worker-jobs/MSF-R20-GOLD-SEMANTIC-COMPILER-001/NiT0-ABoVnk-v3/semantic_atoms.jsonl`;
- `.codex-work/worker-jobs/MSF-R20-GOLD-SEMANTIC-COMPILER-001/NiT0-ABoVnk-v3/proof_graph.json`;
- `.codex-work/worker-jobs/MSF-R20-GOLD-SEMANTIC-COMPILER-001/NiT0-ABoVnk-v3/risk_targeted_audit_plan.json`.

Official Linux runtime:

- `/home/luish/.cache/msf/jobs/MSF-R20-GOLD-SEMANTIC-COMPILER-001/NiT0-ABoVnk-linux`;
- `/home/luish/.cache/msf/runtime-parity/latest.json`.
