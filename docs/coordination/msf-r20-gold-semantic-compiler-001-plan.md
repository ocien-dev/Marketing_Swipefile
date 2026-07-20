# MSF-R20 Gold Semantic Compiler 001

Status: archived_research_not_for_production
Benchmark episode: `NiT0-ABoVnk`
Production status: prototype_read_only

Canonical production route: `chronological_hybrid_v1`; see
`msf-r20-gold-canonical-hybrid-001-plan.md`.

## Objective

Replace repeated, serial semantic rereads with a proof-carrying intermediate
representation.  The prototype must show that one episode can be divided into
independent semantic shards, reduced without information loss, audited through
a risk-targeted surface, and replayed from cache without touching approved gold.

This epic is a benchmark, not a production migration.  The approved episode,
packet, audit, fingerprints, and data root remain read-only.

## Architecture

1. Split the complete transcript into chronological shards with non-owning
   boundary context.  Every source segment belongs to exactly one shard core.
2. Compile each shard into typed semantic atoms.  An atom carries its claim,
   structured fields, source evidence, caveats, relations, and provenance.
3. Reduce atoms into one proof graph.  The reducer rejects duplicate IDs,
   missing evidence, non-verbatim evidence, asymmetric relations, and cycles.
4. Materialize final candidates, ledger links, and calibration bindings from
   the proof graph rather than authoring them as independent documents.
5. Build a risk-targeted final-audit plan containing all numeric, procedural,
   reported, caveated, related, calibrated, and warning-linked atoms plus a
   deterministic sample of the remaining atoms.
6. Cache each shard by source, context, adapter, prompt, and model signature.

## Stories

### GSC-S01 - Pure shard planner

- Preserve chronological order and source text byte-for-byte.
- Assign each segment to one and only one core.
- Add bounded context overlap without double ownership.
- Produce stable semantic hashes.

### GSC-S02 - Proof-carrying atoms and reducer

- Define an adapter-neutral atom contract.
- Validate source evidence before reduction.
- Derive the candidate projection and proof graph deterministically.
- Keep replay provenance visibly distinct from independent extraction.

### GSC-S03 - Semantic cache and parallel execution surface

- Cache by canonical input signature.
- Reuse a valid result without rewriting it.
- Support concurrent shard adapters without coordinator/worker messaging.
- Do not call a paid model in this prototype.

### GSC-S04 - Risk-targeted audit surface

- Include all structurally high-risk atoms and calibration bindings.
- Include source windows and a deterministic low-risk sample.
- Report byte and segment reduction relative to the complete dossier.
- Never claim that sampling alone proves full-audit equivalence.

### GSC-S05 - Read-only benchmark

- Use the final source-complete dossier of `NiT0-ABoVnk` as a frozen oracle.
- Prove lossless reducer/materializer behavior and cache reuse.
- Measure deterministic wall time and audit-surface reduction.
- Record that semantic quality remains unproven until a model independently
  compiles the shards without seeing the approved candidates.

## Acceptance

- all 1,087 transcript segments have exactly one shard owner;
- all 59 approved candidates survive the replay reducer unchanged;
- all proof links resolve to verbatim source segments;
- relations are symmetric and acyclic;
- calibration bindings resolve to existing atoms and distinct targets;
- a second identical run is served entirely from cache;
- the audit plan is materially smaller than the complete dossier;
- tests, `py_compile`, and `git diff --check` pass;
- no approved gold, packet, audit, status, or fingerprint changes;
- the result is labelled `mechanics_validated_semantics_pending` until an
  independent semantic adapter passes a blind comparison.

## Production gate

Production adoption requires a separate benchmark using real independent model
outputs on at least three completed episodes.  Required quality is non-inferior
material recall, zero unsupported claims, literal evidence, and no increase in
final-audit findings.  API concurrency or another paid model service requires
owner authorization before execution.

## Prototype result

The replay benchmark completed against `NiT0-ABoVnk`: 18 shards covered all
1,087 source segments exactly once, 59/59 candidates and 176 verbatim proof
edges survived reduction, and the warm run reused 18/18 cache entries without
rewriting them.  The risk-targeted surface used 164,407 bytes instead of the
844,579-byte dossier.  Oracle-free requests contain transcript source and the
atom contract but no approved candidate IDs.  See
`msf-r20-gold-semantic-compiler-001-retrospective.md` for limitations and the
independent-model adoption gate.

The same benchmark passed on the official Linux runtime: seven focused tests,
38.079 ms cold compile, 12.430 ms warm compile, and 105.614 ms total mechanics.
Runtime parity includes the compiler in the Linux execution signature, and the
approved episode's protected and packet hashes remained unchanged.
