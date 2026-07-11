# Agent coordination

## Operating model

Marketing Swipe File uses a coordinator as planner, independent auditor, queue
owner, integrator, and quality gate. Workers are bounded executors. A worker
never judges or approves its own output.

The coordinator currently uses task
`019f4ee6-a00e-7c90-97bc-5c1aae5c8551`. The default gold-extraction worker is
`Extração Padrão-Ouro`, task `019f4c90-b9dc-7e32-8ff1-57f8896386d3`, and every
new execution message must explicitly set `gpt-5.6-terra/high`.

## Job record

Each job records:

- unique job ID, title, priority, dependencies, and timestamps;
- worker task, model, and reasoning effort;
- exclusive ownership and prohibited files/actions;
- artifact paths, validation summary, last event ID, and gate decision.

Operational state lives in ignored `.codex-work/coordination/queue.json`. The
human-readable audit trail lives in `docs/coordination/task-queue.md`. Only the
coordinator edits either queue.

Allowed states are `queued`, `running`, `awaiting_worker`,
`awaiting_coord_review`, `changes_requested`, `awaiting_owner_decision`,
`approved`, `done`, and `blocked`.

## Redundant delivery and monitoring

Delegations include the coordinator/worker task IDs, job ID, ownership,
acceptance criteria, allowed files, prohibited actions, and the `WORKER_EVENT`
schema in `AGENTS.md`.

The worker sends events to the coordinator and also publishes its complete
result in its own task. The coordinator additionally reads the worker task,
tracks the last processed turn/event, confirms notifications against the task,
and processes an idle completion even if no event arrived. Duplicate pushes and
polls never repeat a transition or correction.

When a worker runs beyond the current coordinator turn, a heartbeat may resume
the coordinator and poll the durable queue. The heartbeat stops when no active
jobs remain. If notification fails, polling continues; if polling is delayed,
notification continues; if both fail temporarily, the queue plus heartbeat is
the recovery path.

## Scheduling and parallelism

Up to three Terra/high workers may run only when tasks are truly independent,
ownership is non-overlapping, dependencies and integration are explicit, and
parallelism has a real benefit. Concurrent repository code changes use separate
worktrees and one writer per exclusive file set.

Coordinator-owned files are never delegated: `AGENTS.md`, this document,
`docs/coordination/task-queue.md`, and `docs/execution-log.md`. Shared scripts,
schemas, contracts, exports, and master destinations are single-writer. Different
episodes may run concurrently only when no shared export/master is written.

If multiple jobs complete together, process: safety/blocking/decision events,
then dependencies that unblock jobs, then remaining completions by
`completed_at` FIFO. Perform each quality gate sequentially and never mix job
evidence.

## Quality gate and correction loop

For every delivered result, the coordinator:

1. confirms the output in the worker task;
2. reads artifacts and checks diff/ownership;
3. reproduces validations proportional to risk;
4. evaluates acceptance criteria;
5. records `approved`, `changes_requested`, or `blocked`.

At most two correction rounds are used before owner escalation unless the owner
authorizes more. Artifacts from a failed worker are preserved; reassignment must
not duplicate already completed actions.

## Owner decisions and failure tolerance

Routine, reversible, low-impact technical choices proceed autonomously when the
scope and path are documented. The affected branch pauses for owner decision
when a choice materially changes scope, architecture, schema/public contract,
source of truth, data, compatibility, privacy/security, cost, production,
external action, or the balance between precision, cost, time, and coverage.

The overall flow stops only when all redundant paths fail, a material owner
decision is required, damage risk exists, locks/permissions repeat, or no safe
progress remains. Independent jobs continue while another branch is paused.

## Pre-production release policy

Current `production_status` is `pre_production`; only an explicit owner statement
can change it to `production`. In pre-production the coordinator can grant and
execute `APROVADO PARA COMMIT`, `APROVADO PARA PUSH`, and `APROVADO PARA
DEPLOY` autonomously, but as three separate sequential gates.

Each gate requires worker delivery, coordinator review, proportional passing
validation, no open critical/major finding, inspected diff, durable records,
reversal strategy, and credential safety. Push requires a successful commit
gate. Deploy requires an identified destination confirmed as preview, staging,
pre-production, or otherwise not declared production. Authorization is not an
obligation; no deploy is invented when no destination exists.

Workers receive release authority only through a later explicit coordinator
instruction containing job ID, gate, exact scope, branch/destination,
command/action, and post-action validation. Force push, destructive history
changes, remote deletion, ignored/local data publication, and gold consolidation
without a distinct functional gate remain forbidden.

If a destination may already be production, pause for owner classification. If
the owner later declares production, autonomous commit/push/deploy authority is
revoked and each action requires separate owner approval.

## Context hygiene and compaction

At safe job boundaries, preserve a durable checkpoint with job ID, state,
decisions, artifacts, validations, blockers, and next action. Update
`docs/execution-log.md` when it is a project decision or completed execution
record. Checkpoints are recommended for continuity, not required to start the
next job.

Do not attempt preventive context compaction through App Server calls, CLI
helpers, scripts, hooks, automations, slash-command messages, or worker
rotation. Context percentage does not block new work. Keep the same coordinator
and the same `Extração Padrão-Ouro` worker; never mark it retired or exhausted
for context reasons.

Codex may compact automatically only when it reaches its own native limit. Do
not claim manual, preventive, or automatic compaction without a real Codex
interface or event. After a native compaction, reread `AGENTS.md`, the active
checkpoint/handoff, the queue, and the job instructions. Compaction does not
change job identity, ownership, acceptance criteria, queue order, or gate state.
