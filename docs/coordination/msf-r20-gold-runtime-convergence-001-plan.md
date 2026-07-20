# MSF-R20-GOLD-RUNTIME-CONVERGENCE-001

Status: completed; P0/P1 validated on real episode `E9nZMgzzxz4`
Execution unit: one direct epic in the active chat
Runtime target: Windows Codex agent with Linux-native WSL gold execution

## Objective

Remove the avoidable runtime and context costs observed in the second Sol
pilot before another real episode is processed. The epic makes Windows/WSL
code parity deterministic, eliminates nested shell quoting, fixes post-review
derived-state handling and telemetry, and removes legacy extraction content
from the gold model context without deleting rollback data prematurely.

## Confirmed evidence

- Windows and Linux currently match for the nine central P0/P1 files.
- The matching state is not committed: the active runtime diff contains 908
  insertions and 52 removals beyond the remote baseline.
- No versioned runtime sync manifest or parity receipt exists.
- WSL user `luish`, default-user configuration and systemd are healthy.
- Direct WSL commands succeed; failures occurred in nested `bash -lc` quoting.
- The pilot took 1,884.3 seconds. Deterministic checks/builds were sub-second
  internally, while semantic work and recovery dominated elapsed time.
- The previous derived ledger blocked finalization after reviews changed.
- Cross-process monotonic telemetry produced negative elapsed values.
- Legacy episode extractions total 4.9 MiB and still feed active downstream
  masters/curation; storage is not the performance problem.

## Decisions

1. Keep the Codex app agent on Windows so project/chat history remains intact.
2. Keep repository runtime, virtualenv, data and temp Linux-native in WSL.
3. Treat the Windows checkout as the authoring view and the Linux checkout as a
   verified runtime mirror, never as an independently edited source.
4. Do not require a commit for every local experiment, but never start a gold
   write without a runtime parity receipt.
5. Gold extraction and gold audit are source-only: raw metadata, transcript,
   content segments, prepared work orders and current gold state. Legacy
   `insights_v2` content is forbidden as model context.
6. Keep legacy files frozen until downstream migration is complete. Deletion
   is a separate irreversible owner gate.

## P0 - Required before the next episode

### RC-S01 - Versioned runtime synchronization and parity gate

- Add an explicit allowlist covering runtime scripts, schemas, prompt, skill,
  tests and contracts required by gold execution.
- Add a no-delete sync command from the Windows checkout to the Linux runtime
  mirror. It must copy only allowlisted files and preserve unrelated state.
- Detect bilateral drift. If a Linux allowlisted file differs from both the
  prior sync receipt and current Windows source, stop rather than overwrite.
- Generate a parity receipt with branch, HEAD, dirty allowlist, physical hashes
  on both sides, Python/venv identity and timestamp.
- Make preflight reject a missing, stale or unequal parity receipt before any
  gold write.
- Add regression proving that an unsynced P0/P1 file blocks execution.

### RC-S02 - Direct WSL launcher without nested shell

- Add one versioned Windows launcher that invokes only:
  `wsl.exe --distribution Ubuntu-24.04 --user luish --exec <binary> <args>`.
- Pass arguments as an array. Do not use `Invoke-Expression`, `bash -lc`, shell
  variables, command substitution, pipes, redirects, `jq`, `sed` or inline
  Python.
- Move multi-step deterministic orchestration into a Linux Python CLI using
  JSON input/output files and explicit `--output` paths.
- Cover adversarial arguments containing spaces, quotes, `$`, parentheses,
  pipes, accents and backslashes.
- Record command, exit code, start/end UTC and stderr in one invocation receipt.

### RC-S03 - Rederive stale outputs after review changes

- Bind derived ledger/calibration state to the composed review semantic hash.
- When reviews change, finalizer autocheck must derive ledger from current
  candidates in memory and ignore a prior packet ledger as decision authority.
- Preserve the old derived file only as rollback provenance during transaction;
  publish the newly derived ledger atomically with the packet.
- Add regression: finalize packet, change source-backed review evidence, then
  refinalize under a new revision without manual ledger deletion or extra apply.

### RC-S04 - Cross-process telemetry

- Use UTC wall-clock anchors for elapsed time across WSL invocations.
- Use monotonic clocks only for durations inside one process.
- Durably count context generations, checks, applies, changed reviews,
  finalizers, builds, audit judgments, audit registrations and WSL launches.
- Never report negative elapsed values; validator rejects inconsistent receipts.

### RC-S05 - Source-only gold policy

- Remove legacy-insight helpers from the normal gold route.
- Add a guard that records hashes for protected legacy files without loading
  their JSON content into the extraction or audit context.
- Update prompt, skill and contract: do not compare old versus gold before the
  final packet and audit are frozen.
- Add a separate read-only post-gold benchmark command for quality research.
- Test that opening `insights_v2.json` content during gold execution fails the
  policy gate while fingerprinting it remains allowed.

## P1 - Time and context reduction

### RC-S06 - One deterministic Linux session per episode

- Generate context once.
- After the complete payload is ready and locally corrected, use one Linux
  process for preview, atomic apply, finalizer and audit-bundle generation.
- After audit, use one Linux process for accepted audit registration,
  deterministic completion build and required-audit validation.
- Do not launch WSL for `jq`, `grep`, file copying or ad hoc inspection; expose
  structured inspection through the Python CLI.

### RC-S07 - Smaller source context

- Keep the primary model context to clean text, IDs, chunk boundaries and the
  sparse deterministic inventory.
- Retrieve exact quote objects only for selected evidence ranges.
- Do not materialize duplicate transcript matrices, old-insight indexes or full
  autocheck reports unless a blocker requests them.
- Record bytes actually exposed to the model separately from disk artifacts.

### RC-S08 - Audit efficiency

- Freeze one packet and one compact audit bundle.
- Run a single final audit against source plus packet, not old extraction.
- If findings exist, produce one closed remediation inventory and focal reaudit.
- Fix deterministic packet/ledger refresh in code so audit correction never
  requires manual derived-file movement.

## Legacy migration policy

Do not delete old extraction files in this epic.

Phase 1, immediate:

- stop reading legacy content during gold extraction/audit;
- preserve hashes and active downstream behavior.

Phase 2, after full gold coverage:

- build a gold master and gold curated layer;
- switch retrieval, strategy packs and citation validation to gold;
- compare outputs and prove no active consumer depends on v2.

Phase 3, owner-approved irreversible gate:

- create a private compressed archive plus file/hash manifest;
- verify restore on a sample;
- remove legacy files from the active data root only after rollback and
  downstream validation pass.

GitHub and Supabase are not substitutes for the private data archive.

## Performance budget for the next pilot

| Phase | Target |
| --- | ---: |
| Runtime sync, parity and preflight | 30 s |
| Context generation and retrieval | 15 s |
| Full semantic read and composition | 6-8 min |
| Compiler corrections | 60 s |
| Apply, finalizer and packet | 30 s |
| Final audit | 2 min |
| Expected total | 10-12 min |

Ten minutes remains a stretch target for a two-hour episode. Quality rules do
not weaken to meet the clock; the first acceptance target is a repeatable
12-minute path with zero avoidable recovery.

## Acceptance criteria

- Windows/Linux runtime allowlist hashes match before every gold write.
- P0/P1 regressions pass from the Linux mirror and are present in the parity
  receipt.
- No gold command uses `bash -lc` or nested shell parsing.
- Quoting adversarial tests pass.
- Review changes automatically invalidate and rebuild derived ledger state.
- Cross-process elapsed and operation counts are accurate and non-negative.
- Gold extraction/audit does not read legacy insight content.
- Legacy files, masters and curated exports remain byte-identical.
- One comparable episode completes `complete/passed` with packet 5,
  fingerprints unchanged and no manual derived-file repair.
- WSL command count and model-facing bytes are lower than pilot 002.
- Focused tests, full gold regression, py_compile and `git diff --check` pass.

## Out of scope

- processing another episode before P0 acceptance;
- deleting or migrating legacy data;
- changing public gold schema;
- weakening recall, evidence, numbers, relations, ledger or calibration;
- subagents or other chats;
- commit, push, deploy, consolidation or Supabase.

## Next action

Use the converged WSL route for the next single-episode gold epic. Keep the
single final Sol audit, but improve the source-reading recall pass before the
first packet: the runtime pilot proved that deterministic execution is already
sub-second while semantic reading and two audit remediations dominate elapsed
time. Do not start a multi-episode wave until another episode confirms fewer
post-audit corrections.

## Implementation result - 2026-07-15

P0 completed:

- RC-S01: versioned allowlist, no-delete sync, bilateral drift detection,
  physical hash parity and signed receipt with branch, HEAD, dirty allowlist
  and Linux venv identity.
- RC-S02: direct PowerShell launcher using `wsl.exe --exec` argument arrays;
  adversarial argument dry-run preserved spaces, quotes, dollar signs,
  parentheses and pipes literally.
- RC-S03: finalizer autocheck now ignores prior derived ledger authority and
  rederives from current reviews/candidates before build.
- RC-S04: durable UTC wall-clock session telemetry and operation counters;
  monotonic time remains process-local.
- RC-S05: legacy-content payload guard, model-context byte accounting and a
  separate explicit post-gold read-only benchmark command.

P1 completed:

- RC-S06: existing `--one-shot` is now the documented required executor route;
  `scripts.complete_gold_episode.py` adds the one-process accepted-audit route.
- RC-S07: context records exact model-facing bytes and forbids legacy indexes
  or comparison matrices.
- RC-S08: packet ledger refresh is deterministic and the final compact audit
  bundle remains job-local.

Validation evidence:

- focused P0/P1 regressions: 7 passed;
- complete gold regression: 99 passed before final route tests, then expanded
  to 101 tests for the final run;
- Linux py_compile passed for all new/changed runtime modules;
- runtime parity verification returned `status=pass`, `copies=[]`,
  `conflicts=[]`;
- PowerShell launcher dry-run showed literal adversarial arguments and no
  nested shell;
- no real gold, export, packet, audit or fingerprint was written.

## Controlled pilot result - 2026-07-15

- Episode `E9nZMgzzxz4` completed with 22/22 reviews and 44 unique candidates.
- Final lifecycle is `complete/passed`, with zero open findings.
- Packet contains exactly five files; protected fingerprints are equal 4/4.
- Calibration passed at 8/16 against minimum 4, with no duplicate targets.
- Full gold regression expanded to 102 passing tests.
- The canonical launcher used WSL-native Python, repo mirror, data and temp.
- Deterministic one-shot execution took 453.84 ms and accepted-audit
  completion took 146.21 ms; end-to-end wall time was 47 minutes 39.95 seconds.
- The only final Sol audit found three genuine recall gaps. Two remediation
  revisions were required before the focal reaudit passed.
- The pilot therefore closes P0/P1 runtime convergence, but does not yet meet
  the 10-12 minute semantic throughput target.
