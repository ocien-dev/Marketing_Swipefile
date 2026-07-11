# MSF-R20 Pilot Plan

Date: 2026-07-10
Route: Codex manual semantic review, no paid API

## Episode Selection

| Video ID | Purpose | Reason |
| --- | --- | --- |
| `awbrqeqq-io` | Short episode | 42.5 minutes and 341 segments; validates overhead and zero-insight handling on compact source material. |
| `cL3FuW8bAMA` | Long VSL episode | 212.6 minutes and 1,846 segments; validates long-form review, VSL evidence, and resume checkpoints. |
| `35uL_nCmZ0k` | Technical methodology | 87.4 minutes and 688 segments on direct-response campaigns; tests dense procedural and framework extraction. |
| `aSFAve1klsc` | Narrative business case | 166.2 minutes and 1,242 segments; tests the boundary between biography, reported case, and reusable operational insight. |
| `_hXmiIEac6w` | Noisier transcript | 166.0 minutes, 1,531 segments, and 3.3 percent short segments; tests cleanup and evidence discipline under transcript noise. |

Academy material is deliberately excluded. It needs a separate source-specific
wave and must not be mixed into YouTube podcast acceptance metrics.

## Pilot Acceptance State

Each episode is prepared and manually reviewed chunk by chunk. Its blind audit
packet is exported after deterministic validation. It remains
`awaiting_external_audit` until a separate Codex coordinator task returns a
valid independent audit with zero open findings. The coordinator must not be the
executor, and the report preserves reviewer task, model, effort, and audit
route. `External` is the compatibility name for external to the executor task;
it is not a provider requirement. Historical Claude audits remain unchanged.
No pilot artifact can update v2, curated, or master exports.
