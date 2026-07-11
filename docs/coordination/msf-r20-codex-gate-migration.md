# MSF-R20 Codex gate migration

## Decision

Future R20 gold-extraction audits use a Codex coordinator task that is separate
from the executor task. Historical Claude audits remain true provenance and are
not deleted, renamed, or rewritten.

The compatibility lifecycle `awaiting_external_audit` remains unchanged.
`External` now means external to the executor task. It does not require a
non-Codex provider.

## Independence boundary

For an initial blind judgment, the coordinator reads only the exported packet:
`packet_manifest.json`, `transcript_clean.json`, `insights_exhaustive.json`,
`high_signal_coverage_ledger.json`, and `calibration_tests.json`. Before sealing
that judgment it does not read the worker history, manual reviews, audit report,
validation report, or dedupe decision queue. The audit is blind to generation
history and internal decisions, but not blind to episode identity or style.

Initial sealed judgments live under
`.codex-work/msf-r20-coordinator-audits/<video_id>_audit.json`. Workers may read
the findings for correction but must never edit these files or approve their own
output.

## Valid audit provenance

A current audit report preserves:

- reviewer identity and coordinator task ID;
- reviewer model and reasoning effort;
- audit route and timestamp;
- status, summary, findings, and open-finding count.

Every finding validates its ID, severity, status, category, segment range,
candidate IDs, summary, evidence, and required action. `status=passed` is invalid
with any open finding. The reviewer must be separate from the executor.

The build cannot accept `passed` as an unverified free argument. It derives the
gate from a valid `editorial_audit_report.json`. `complete` additionally requires
zero open findings, deterministic validation, and unchanged protected
fingerprints. Old lifecycle values and historical reports remain readable.

## Coordination controls

Jobs follow the redundant event/polling protocol and durable queue described in
`AGENTS.md` and `docs/agent-coordination.md`. The coordinator alone owns queue
state and the final gate. A worker completion is reviewed sequentially and may
be approved, returned for correction, or blocked. Correction is limited to two
rounds before owner escalation unless explicitly extended.

## Pre-production release status

The owner has set `production_status=pre_production` until an explicit later
declaration. Commit, push, and deploy are separate coordinator gates and may be
granted autonomously only after worker evidence, independent quality review,
passing proportional validations, no open critical/major findings, inspected
diff, durable records, rollback planning, and credential safety.

Deploy additionally requires an identified non-production destination. A worker
needs a later explicit coordinator instruction for each release action. No
force push, destructive history change, local-data publication, or silent
release is allowed. Gold consolidation and Supabase are not release actions and
still require separate functional authorization.

Only the owner may change the status to `production`. That transition revokes
autonomous commit/push/deploy and restores separate owner approval for each.

## Context continuity

Coordinator and worker preserve durable checkpoints at safe job boundaries
with job state, decisions, artifacts, validations, blockers, and next action.
These checkpoints support continuity but are not a gate for new work.

Preventive compaction is prohibited: do not use App Server calls, CLI helpers,
scripts, hooks, automations, slash-command messages, or worker rotation. Do not
block work at any context percentage. Keep the same coordinator and the same
designated worker; neither is retired or replaced for context reasons.

The App Server experiment reported a completed internal item but did not reduce
the context window displayed by the Codex app, which remained at 68 percent.
Therefore it is not accepted as compaction evidence and must not be repeated as
a preventive workflow.

Codex may compact automatically when it reaches its own native limit. No manual,
preventive, or automatic compaction is claimed without confirmation in the real
Codex interface or event. After native compaction, reread `AGENTS.md`, the
active checkpoint, queue, and job. Compaction changes neither audit
independence, job identity, ownership, acceptance criteria, queue order,
provenance, nor release gates.
