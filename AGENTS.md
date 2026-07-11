# Marketing Swipe File agent protocol

This repository uses a coordinator/worker quality-gate model for gold-standard
extraction work.

## Roles

- The coordinator plans work, owns the central queue, performs independent
  audits, reviews diffs and tests, and decides the quality gate.
- A worker implements or processes only its delegated ownership. A worker must
  never approve its own output.
- The default R20 worker runs with `gpt-5.6-terra` and `high` reasoning. The
  coordinator audit is a separate task.

`awaiting_external_audit` remains the compatibility lifecycle name. Here,
`external` means external to the executor task, not external to Codex.

## Safety and repository state

Before any write, record `git status --short --branch` and preserve all existing
modified and untracked files. Do not use destructive reset, checkout, clean, or
equivalent operations. Do not force through OneDrive locks or permission errors.

The owner has declared `production_status=pre_production`. Gold consolidation
and Supabase remain prohibited without their own functional gates. Destructive
history operations and publication of local/ignored data remain prohibited.

For the current implementation job, do not commit, push, or deploy unless the
coordinator sends a later explicit gate instruction. At project level,
pre-production commit, push, and deploy may be approved and executed
autonomously by the coordinator only after their separate gates pass.

- do not consolidate gold into v2/curated/pool/master or start Supabase without
  a separate functional gate;
- preserve historical audit provenance, including historical Claude records;
- do not write outside delegated ownership;
- do not edit concurrently overlapping files or episode export directories.

## Delegation contract

Every worker job must state `coordinator_thread_id`, a unique `job_id`,
`worker_thread_id`, model/effort, ownership, acceptance criteria, allowed files,
and prohibited actions.

On material progress, completion, blocking, or a needed decision, the worker
must both publish in its own task and send this event to the coordinator:

```text
WORKER_EVENT
event_id: <job_id>-<sequence>
job_id:
worker_thread_id:
event_type: completed | blocked | decision_required | progress
status:
summary:
artifacts:
validations:
blockers:
decision_needed:
next_action:
```

The coordinator independently polls the worker task, confirms every event in
the source task, and deduplicates transitions by `event_id` and `job_id`.

## Durable queue and ownership

Only the coordinator edits:

- `.codex-work/coordination/queue.json`;
- `docs/coordination/task-queue.md`;
- `AGENTS.md`;
- `docs/agent-coordination.md`;
- `docs/execution-log.md`.

Allowed queue states are `queued`, `running`, `awaiting_worker`,
`awaiting_coord_review`, `changes_requested`, `awaiting_owner_decision`,
`approved`, `done`, and `blocked`.

Independent workers may run in parallel only with non-overlapping ownership and
explicit dependencies/integration. Shared scripts and contracts are
single-writer. Concurrent code edits require separate worktrees. When overlap is
uncertain, use one worker.

## Quality gate

A worker `completed` event is a delivery signal, not approval. The coordinator
must confirm the worker task, inspect artifacts and ownership, reproduce
appropriate validations, and decide `approved`, `changes_requested`, or
`blocked`. Use at most two correction rounds before escalating to the owner,
unless the owner authorizes more.

An episode may become `complete` only from a valid audit report by a reviewer
separate from the executor, with `status=passed`, zero open findings,
deterministic validation passing, and protected fingerprints unchanged.

## Owner decision gate

Continue autonomously for routine, reversible, documented choices. Pause the
affected branch as `awaiting_owner_decision` for material scope, architecture,
schema/public-contract, source-of-truth, data migration/deletion, compatibility,
security/privacy, paid service, external action, production, commit/push/deploy,
irreversible action, or a material precision/cost/time/coverage tradeoff.

Independent jobs may continue while one branch awaits a decision. A decision
request must provide context, materiality, options and impacts, a coordinator
recommendation, paused work, and independent work that continues.

## Pre-production release gates

Only the owner can change `production_status` to `production`. While status is
`pre_production`, the coordinator may autonomously grant and execute, in order:

1. `APROVADO PARA COMMIT`;
2. `APROVADO PARA PUSH`;
3. `APROVADO PARA DEPLOY`.

One gate never implies the next. Each requires approved in-project scope,
worker evidence, coordinator quality gate, proportional passing tests, no open
critical/major findings, inspected diff, queue/Markdown record, rollback or
reversal strategy, and no credential exposure. Deploy additionally requires an
identified preview/staging/pre-production destination that is not plausibly
production.

A worker may run any release action only after a later explicit coordinator
message states job ID, granted gate, exact scope, branch/destination, authorized
command/action, and required post-action validation. Never include release
actions silently in implementation work. Do not force-push, destructively
rebase/reset, alter remote history, publish ignored/local data or `C:\MSF-data`,
or treat data consolidation as deploy.

When the owner explicitly declares production, record
`production_status=production` and require owner authorization separately for
every commit, push, and deploy. Analysis, local implementation, tests, and
quality gating remain autonomous.

## Context hygiene

After every substantial execution or turn, check the Codex context-window
indicator when the surface exposes it. Above 30 percent, first write a durable
checkpoint containing job ID, state, decisions, artifacts, validations,
blockers, and next action in the queue/handoff and, when applicable,
`docs/execution-log.md`. Never copy secrets or ignored local data.

Compact only at a safe boundary, never during a write, Git operation, deploy,
migration, or transaction. Use `/Compactar` or `/compact` only when the surface
provides it. After compaction, reread `AGENTS.md`, the active checkpoint/handoff,
the queue, and the job instructions. Compaction never changes job ID,
ownership, acceptance criteria, queue order, or gate state.

If the exact metric or command is not programmatically available, do not claim
success. Preserve the checkpoint and emit:

```text
WORKER_EVENT or COORD_EVENT
event_type: COMPACTION_REQUIRED
threshold: >30%
checkpoint: <file>
status: awaiting_surface_action
```

Treat a context/truncation warning as above threshold even without a visible
percentage. `COMPACTION_REQUIRED` is an open operational gate, not a warning.
The affected worker receives no new substantial job until the pre-compaction
gate succeeds.

Slash commands are native surface actions. Sending `/Compactar` or `/compact`
through inter-task messaging only sends text and must never be reported as
compaction.

Keep using the designated worker task. Before any next substantial job, the
coordinator must run a separate pre-compaction gate: confirm the worker is idle
and has a durable checkpoint; send isolated `/compactar`; if it does not work,
send isolated `/compact`; then verify the real result in the worker task. Never
combine either alias with work instructions. Release the job only with evidence
of real compaction or owner confirmation from the UI. If both aliases are plain
messages, set `awaiting_compaction`, send no substantial work, and do not create
a successor worker.

If the coordinator's own UI/context exceeds 30 percent and no native
compaction is available, it must checkpoint fully, set
`awaiting_owner_surface_action`, and ask the owner to compact in the UI or
create/authorize a new coordinator.
