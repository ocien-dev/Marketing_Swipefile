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

Keep durable checkpoints or handoffs at safe boundaries, especially after a
job, recording job ID, state, decisions, artifacts, validations, blockers, and
next action. Never copy secrets or ignored local data. A checkpoint is useful
for continuity but is not a precondition for starting the next job.

Do not attempt preventive context compaction through App Server calls, CLI
helpers, scripts, hooks, automations, slash-command messages, or worker
rotation. Do not block a new job because of context percentage and do not mark
the designated worker retired or exhausted. Keep the same coordinator and the
same designated worker.

Codex may compact context automatically when it reaches its own native limit.
Do not claim manual, preventive, or automatic compaction unless the real Codex
interface or event confirms it. If native compaction occurs, reread
`AGENTS.md`, the active checkpoint/handoff, the queue, and the job instructions
before continuing.
