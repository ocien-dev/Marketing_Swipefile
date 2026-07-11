# Worker contract template

Every worker message must explicitly set the supported worker model and high
reasoning, then fill this contract.

```text
coordinator_thread_id:
job_id:
worker_thread_id:
model: gpt-5.6-terra
thinking: high

OBJECTIVE:
DEPENDENCIES:
OWNERSHIP:
ACCEPTANCE CRITERIA:
ALLOWED FILES:
PROHIBITED FILES:
PROHIBITED ACTIONS:
INTEGRATION PATH:

EVENT DELIVERY:
Send WORKER_EVENT to the coordinator and publish the full result in the worker
task. Deduplicate by event_id/job_id.

CONTEXT HYGIENE:
After every substantial turn, check context usage when visible. Above 30%, or
on any truncation warning, first checkpoint job_id, state, decisions, artifacts,
validations, blockers, and next action in the coordinator-defined handoff/log.
Do not include secrets or ignored local data. Compact only at a safe boundary,
never during writes, Git, deploy, migration, or transaction. After compaction,
reread AGENTS.md, checkpoint/handoff, queue, and this job. Compaction changes no
scope, ownership, acceptance criteria, queue order, or gate.
If metric/command is unavailable programmatically, do not claim success. Send:
WORKER_EVENT
event_type: COMPACTION_REQUIRED
threshold: >30%
checkpoint: <file>
status: awaiting_surface_action

COMPACTION_REQUIRED is an open operational gate. Do not accept another
substantial job and do not treat an inter-task alias as successful without
evidence. The coordinator keeps this same worker, confirms it is idle with a
durable checkpoint, sends isolated `/compactar`, falls back to isolated
`/compact`, and verifies the source task. If both are plain messages, remain
`awaiting_compaction`; no successor worker is created.

FINAL DELIVERY:
STATUS: completed | blocked
SUMMARY:
ARTIFACTS:
VALIDATIONS:
BLOCKERS:
NEXT ACTION:
```
