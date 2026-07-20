# MSF-R20 Gold Semantic Compiler 003 - Global Reducer Pilot

Status: archived_research_not_for_production
Episode: `AqzF_M2mM04`
Date: 2026-07-17

Canonical production route: `chronological_hybrid_v1`; this document is
historical benchmark evidence only.

## Decision

Do not adopt the global-reducer architecture yet. It solved a real structural
failure from the first independent benchmark, but it did not reach the required
quality threshold and it pushes a complete future run beyond the ten-minute
target.

## What improved

| Metric | Pilot 002 | Pilot 003 | Change |
| --- | ---: | ---: | ---: |
| Material recall | 0.8529 | 0.8824 | +0.0295 |
| Unsupported claims | 1 | 0 | -1 |
| Partial candidates | 3 | 2 | -1 |
| Number recall | 0.9444 | 0.9474 | +0.0030 |
| Procedure recall | 0.7500 | 0.8250 | +0.0750 |
| Caveat recall | 0.8947 | 0.9474 | +0.0527 |
| Relation recall | 0.1250 | 0.8750 | +0.7500 |
| Calibration recall | 0.6667 | 0.8889 | +0.2222 |
| Final findings | 6 | 5 | -1 |

The global reducer rebuilt the seven-point parent framework and removed the
unsupported speed-test specialization. It also preserved more procedure setup,
numbers and caveats. Its deterministic gates caught eight literal-number gaps;
the reconciler added six nearest proving segments without changing claims and
then passed with zero hard errors.

## Cost and latency

- cached shard calls reused: 7; new shard calls: 0;
- global Terra reducer: 319.688 seconds, 65,601 input, 17,575 output and
  2,539 reasoning tokens;
- compact Sol judge: 217.941 seconds, 65,519 input, 9,857 output and 7,591
  reasoning tokens;
- incremental rerun wall: 537.629 seconds, or 8 minutes 57.629 seconds;
- a future fresh run with the previous parallel shard wall would project to
  626.450 seconds, or 10 minutes 26.450 seconds;
- judge packet: 347,874 bytes to 237,387 bytes, a 31.8% reduction;
- judge input tokens: 85,993 to 65,519, a 23.8% reduction;
- judge wall: 221.010 to 217.941 seconds, a 1.4% reduction only.

The compact packet saves context, but Sol reasoning time remains dominated by
semantic comparison. The full-episode reducer is too expensive to be the main
quality repair mechanism.

## Remaining findings

1. The solo, shorter podcast-format experiment and its sharing/repeat rule are
   absent.
2. The 42% opening result and the full prints/profiles verification proposition
   are absent from the result bundle.
3. The personalized-autoplay procedure still omits the generator, niche-option
   and rights/coherence setup.
4. The personalized-autoplay child relation remains collapsed into its parent
   test candidate.
5. One distinct 40% occurrence is present in evidence but absent from the
   candidate number inventory.

## Next architecture to test

1. Attach compact numeric, calibration and boundary inventories to the original
   parallel shard request that owns each source segment. Require the shard to
   return captured, merged or excluded for each item.
2. Use deterministic merging for exact duplicates and a small relation-only
   pass over detected enumerations. Do not send every atom and source segment
   through a second full-episode semantic model.
3. Run a targeted gap resolver only for inventory items left unresolved after
   sharding. Its input must contain the item plus a local source window, never
   the whole episode or approved gold.
4. Keep the compact Sol packet, but include only candidate-linked numeric
   inventory entries and direct relation evidence.

This route should retain the meaningful relation/calibration improvements while
removing the 5m20s full reducer bottleneck. No approved gold, packet, audit,
status or protected fingerprint changed during this pilot.
