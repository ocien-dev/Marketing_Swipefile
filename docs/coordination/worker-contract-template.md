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
At the end of a job, preserve a checkpoint with job_id, state, decisions,
artifacts, validations, blockers, and next action. Do not include secrets or
ignored local data. A checkpoint is recommended, not a precondition for the
next job.

Do not attempt preventive compaction through App Server calls, CLI helpers,
scripts, hooks, automations, slash-command messages, or worker rotation. Do not
block work because of context percentage and do not mark this worker retired or
exhausted. Codex may compact automatically at its own native limit; claim no
compaction without a real Codex interface or event. After native compaction,
reread AGENTS.md, checkpoint/handoff, queue, and this job.

FINAL DELIVERY:
STATUS: completed | blocked
SUMMARY:
ARTIFACTS:
VALIDATIONS:
BLOCKERS:
NEXT ACTION:
```
