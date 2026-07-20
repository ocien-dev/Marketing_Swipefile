# MSF-R20 Gold Semantic Compiler 003

Status: archived_research_not_for_production
Production status: read_only_benchmark
Date: 2026-07-17

Canonical production route: `chronological_hybrid_v1`; see
`msf-r20-gold-canonical-hybrid-001-plan.md`.

## Objective

Close the quality gaps found by the short independent semantic-compiler pilot
without paying for the seven blind shard calls again. Reuse the 84 cached atoms
from `AqzF_M2mM04`, synthesize them globally, validate source support and rerun
only the compact final Sol evaluation.

## Changes

1. Build deterministic inventories for every source number and every prepared
   calibration target.
2. Add one blind global reducer that merges duplicate atoms, restores
   cross-shard frameworks and relations, captures uncovered inventory sources,
   and removes procedural specialization unsupported by evidence.
3. Require a disposition for every inventory item and validate literal numbers,
   evidence ownership, relation symmetry/acyclicity and procedure support.
4. Deterministically match approved candidates to reduced candidates only after
   reduction and send a compact packet to the Sol judge.
5. Compare quality, wall time and token use against pilot 002 while preserving
   all approved gold artifacts byte-for-byte.

## Acceptance

- reducer input contains no approved candidate IDs or candidate objects;
- cached blind shard responses are reused with zero new shard calls;
- numeric and calibration inventories are complete;
- deterministic reducer validation has zero hard errors;
- relation recall improves materially and unsupported claims reach zero;
- material recall reaches at least 0.98 with zero final findings;
- combined incremental reducer plus judge wall remains below ten minutes;
- source, packet, audit, status and protected fingerprints remain unchanged.

## Safety

All writes are job-local. The benchmark does not register an audit, rebuild an
episode or alter approved gold. Failure keeps the current production workflow
unchanged.

## Pilot result

The cached seven-shard output of `AqzF_M2mM04` was reduced globally by one
blind `gpt-5.6-terra/high` call and judged once by `gpt-5.6-sol/high`.
Deterministic validation passed after literal-number reconciliation. The global
reducer fixed the prior unsupported procedure and recovered the seven-point
framework relations, but did not recover all omitted source propositions.

The final quality gate remains failed: material recall reached `0.8824`,
unsupported claims reached `0`, relation recall reached `0.875`, calibration
recall reached `0.8889`, and five final findings remain. The architecture is
therefore not adopted for production. A future benchmark should inject compact
numeric/calibration/boundary inventories into the original parallel shard calls
instead of adding a full-episode model reducer afterwards.
