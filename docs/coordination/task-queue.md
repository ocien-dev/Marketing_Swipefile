# MSF coordination task queue

Central human-readable queue. Only the coordinator edits this file; workers
report events but never change queue state.

Production status: `pre_production`. Release gates are separate. Commit gate was
executed as `3d224f7`; post-commit validation passed. Push is approved for
`main -> origin/main` and pending execution. Deploy has no gate because no
non-production destination was identified. The worker job has no release
authority.

Worker context status: `Extração Padrão-Ouro`
(`019f4c90-b9dc-7e32-8ff1-57f8896386d3`) remains the designated worker and is
idle. There is no context gate: new work is not blocked by percentage, no
preventive compaction is attempted, and no successor worker is created.

| Job | Worker | Scope | Status | Last event | Gate |
| --- | --- | --- | --- | --- | --- |
| `MSF-R20-GATE-001` | `Extração Padrão-Ouro` (`019f4c90-b9dc-7e32-8ff1-57f8896386d3`, `gpt-5.6-terra/high`) | Gate hardening plus correction and packet rebuild for the four pending R20 episodes | `done` | `MSF-R20-GATE-001-004` (`completed`, confirmed in worker task) | approved |

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
- Blockers: none for the quality gate or current worker context.
- Next action: execute only the independently approved release gates; no gold
  consolidation, Supabase, or deploy without a functional destination gate.
- Context: durable checkpoint preserved. No manual, preventive, or automatic
  compaction is claimed.

Context policy: keep the same coordinator and worker. Do not use App Server,
CLI, scripts, hooks, automations, slash messages, or rotation for preventive
compaction, and do not block new work by context percentage. Codex may compact
automatically only at its own native limit; no compaction is claimed without a
real Codex interface or event.

## Processing rule

Results are verified in the worker thread, then reviewed sequentially. A
`completed` event is only a delivery signal, never approval. Safety, blockers,
and `decision_required` events take priority; completed jobs otherwise follow
dependency order and `completed_at` FIFO.
