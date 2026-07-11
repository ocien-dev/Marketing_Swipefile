# MSF coordination task queue

Central human-readable queue. Only the coordinator edits this file; workers
report events but never change queue state.

Production status: `pre_production`. Release gates are separate. The coordinator
approved the commit gate after quality review; execution is pending. Push remains
pending commit execution, and deploy requires an identified non-production
destination. The worker job has no release authority.

Worker context status: `Extração Padrão-Ouro`
(`019f4c90-b9dc-7e32-8ff1-57f8896386d3`) completed its job with the owner
observing 68% context usage. Its `COMPACTION_REQUIRED` gate is open. The same
worker remains designated, but any next substantial job requires the separate
pre-compaction gate and is blocked as `awaiting_compaction` until verified.

| Job | Worker | Scope | Status | Last event | Gate |
| --- | --- | --- | --- | --- | --- |
| `MSF-R20-GATE-001` | `Extração Padrão-Ouro` (`019f4c90-b9dc-7e32-8ff1-57f8896386d3`, `gpt-5.6-terra/high`) | Gate hardening plus correction and packet rebuild for the four pending R20 episodes | `approved` | `MSF-R20-GATE-001-004` (`completed`, confirmed in worker task) | approved |

## Context checkpoint — 2026-07-11 final gate

- Job: `MSF-R20-GATE-001` is coordinator-approved; ownership and acceptance
  criteria were preserved.
- Decisions: all four reaudits passed with zero open findings; build completion
  derived from valid separate-reviewer reports; pre-production release gates
  remain separate.
- Artifacts: four sealed initial audits, four passed reaudits, coordination
  docs/queue, and protected fingerprint snapshot.
- Validation: 18 isolated pure tests passed; five temp-directory cases were
  blocked by OneDrive permissions, while the worker passed all 23. The
  coordinator independently ran deterministic validation before and after audit
  registration for all four real episode directories; all passed.
- Blockers: none for the quality gate. A pre-compaction gate remains required
  before any new substantial worker job.
- Next action: execute only the independently approved release gates; no gold
  consolidation, Supabase, or deploy without a functional destination gate.
- Context: platform context compaction occurred and the coordinator reread
  `AGENTS.md`, this checkpoint, and the operational queue. No slash-command
  success is claimed.

Native-surface correction: aliases sent between tasks may be plain messages and
do not prove compaction. Before future work, the coordinator must test isolated
`/compactar`, then isolated `/compact`, verify the source task, and proceed only
on real evidence or owner UI confirmation. The same worker is retained; no
successor is created.

## Processing rule

Results are verified in the worker thread, then reviewed sequentially. A
`completed` event is only a delivery signal, never approval. Safety, blockers,
and `decision_required` events take priority; completed jobs otherwise follow
dependency order and `completed_at` FIFO.
