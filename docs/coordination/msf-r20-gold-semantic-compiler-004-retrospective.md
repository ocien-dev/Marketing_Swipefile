# MSF-R20 Gold Semantic Compiler 004 Retrospective

Date: 2026-07-17
Episode: `AqzF_M2mM04`
Mode: read-only blind benchmark; no gold data, status, export, packet, audit,
or fingerprint was modified.

## Result

Decision: **do not adopt yet**.

Final disposition: **archived as research**. The production route is
`chronological_hybrid_v1`; only the deterministic controls described below were
promoted.

The source-routed risk inventory was useful as a deterministic control. Seven
Terra shards gave every numeric, calibration, and boundary item one local
owner. All required dispositions closed, leaving zero targeted gap calls.
That removes the most expensive failure mode of the preceding design: a
full-episode reducer invoked only to discover missing coverage.

The output still did not meet the quality gate. The blind Sol audit found three
open findings: an omitted test of the short solo format, an atom that combined
two differently attributed success cases, and a causal caveat missing from the
R$ 830,000 case.

## Timings

| Stage | Time |
| --- | ---: |
| Terra blind shards, seven parallel calls | 151.58 s |
| Targeted gap calls | 0 s (none required) |
| Sol final audit | 259.41 s |
| Combined external-model wall time | 410.99 s |

The relation diagnostic produced 29 local windows. They were intentionally not
sent to a model because this would reintroduce an unbounded second pass.

## Quality

| Metric | Result |
| --- | ---: |
| Material recall | 0.8824 |
| Unsupported claims | 1 |
| Partial items | 1 |
| Number recall | 1.0000 |
| Procedure recall | 0.8750 |
| Caveat recall | 0.8889 |
| Relation recall | 1.0000 |
| Calibration recall | 0.7500 |
| Open final-audit findings | 3 |

## Learning

The inventory improves deterministic coverage, particularly for numbers and
relations, but a disposition requirement is not enough to protect semantic
atomicity, attribution, and causal caveats. It also increased shard wall time
relative to the previous blind-shard pilot, because the risk context enlarged
each request. A production version must compress the inventory to only
high-risk anchors and add deterministic checks for cross-case attribution and
simultaneous-change caveats before the Sol audit. Relation windows must be
deduplicated and thresholded before any model route is considered.

Artifacts: `.codex-work/worker-jobs/MSF-R20-GOLD-SEMANTIC-COMPILER-004/results/AqzF_M2mM04/`.
