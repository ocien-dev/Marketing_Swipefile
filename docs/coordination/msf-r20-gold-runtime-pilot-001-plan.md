# MSF-R20-GOLD-RUNTIME-PILOT-001

Status: completed
Execution: direct in the active chat
Runtime: Windows authoring checkout with verified Ubuntu 24.04 WSL mirror
Scope: one episode, `E9nZMgzzxz4`

## Objective

Validate the P0/P1 runtime-convergence flow on one new real episode from source
through deterministic completion and the single final Sol audit. The run uses
one runtime parity receipt, one compact context, one complete payload, one
one-shot apply/finalizer process and one post-audit completion process.

## Selected episode

- `video_id`: `E9nZMgzzxz4`
- title: `Criando Video de Vendas de 8 Digitos Na Pratica | Tiago Filemon - Segredos da Escala #002`
- duration: 9,242 seconds
- source segments: 1,180
- transcript status: `available`
- initial gold/export state: absent
- revision: `runtime-pilot-E9nZMgzzxz4-final-001`
- export: `msf_r20_gold_runtime_pilot_001_E9nZMgzzxz4`
- Linux job root: `/home/luish/.cache/msf/jobs/MSF-R20-GOLD-RUNTIME-PILOT-001`

## Source baseline

| File | SHA-256 | Bytes |
| --- | --- | ---: |
| `metadata.json` | `0E3023441FE9B9190C6F3E7A2ED4179AEF6F4634C25008FBDAED261A9963E028` | 1,937 |
| `transcript_original.json` | `DE27942ECF5AB72B36F56D6167FE4FD72C9BCC8B3FD03362A78ECCE180414B56` | 322,511 |
| `content_segments.json` | `FD7708C020630F2CE687E3018F514EC956552DF13E415EA703CCF4E95ACBEADB` | 659,745 |

## Required flow

1. Verify Windows/Linux runtime parity and Linux-native Python/data/temp.
2. Prepare gold once and generate one three-slab source-only context.
3. Read all chunks chronologically and compose one complete source-backed
   payload, including explicit zero-insight reviews.
4. Resolve the full compiler/autocheck inventory before the first episode
   write, then run `--one-shot` once.
5. Freeze the five-file packet and compact audit bundle.
6. Run one final `gpt-5.6-sol/high` audit. If it opens findings, use one closed
   remediation revision and one focal reaudit.
7. Register the accepted audit and derive `complete/passed` with the required
   audit validator.

## Acceptance

- Runtime parity remains valid and no nested shell is used for gold commands.
- All chunks are reviewed with unique source-backed candidates.
- `hard_blockers=0`, packet has exactly five files and fingerprints are equal.
- Final audit passes with zero open findings.
- Final lifecycle is `complete/passed`.
- Telemetry records non-negative elapsed time, operation counts, WSL launches
  and model-facing bytes.
- No legacy insight content is read before the frozen post-gold benchmark.

## Prohibited

- Windows Python or Windows data writes for gold.
- Legacy extraction content in extraction or audit context.
- Intermediate audits, subagents, other chats or provisional packets.
- Commit, push, deploy, consolidation or Supabase.

## Result

- Runtime: Ubuntu 24.04 WSL, Linux-native Python, data, repo mirror and temp.
- Runtime parity: passed before every gold command.
- Prepared source: 1,160 clean segments, 22 chunks and 830 signals.
- Review: 22/22 chunks, including two explicit zero-insight reviews.
- Final extraction: 44 unique source-backed candidates.
- Calibration: pass, 8/16 covered with minimum 4 and no duplicate targets.
- Packet: exactly the five blind files required by the contract.
- Final audit: `gpt-5.6-sol/high`, passed with zero open findings after two
  source-backed remediation revisions.
- Final lifecycle: `complete`, `audit_status=passed`, zero open findings.
- Protected fingerprints: 4/4 unchanged.

## Measured execution

- Reading-context generation: 23.39 ms and 312,477 model-facing bytes.
- Initial one-shot deterministic pipeline: 453.84 ms.
- Post-audit deterministic completion: 146.21 ms.
- End-to-end wall time from context start through accepted audit: 47 minutes
  39.95 seconds.
- Four successful canonical launcher invocations: context, clean preview,
  one-shot finalization and accepted-audit completion.
- Writes in the initial route: one review write operation, one finalizer, one
  build and one audit bundle.
- Full gold regression: 102 tests passed in 1.77 seconds.

These timings measure code execution, not the semantic reading and final Sol
audit. The test confirms that WSL and deterministic gates are no longer the
dominant cost; model reading, recall and audit remediation remain the primary
wall-clock work.

## Learnings

1. The launcher must set the Linux working directory explicitly with
   `wsl.exe --cd`; otherwise inherited Windows cwd can import the `/mnt/c`
   checkout even when Linux Python is selected.
2. The runtime sync manifest must include itself, otherwise parity can validate
   an obsolete copy of the manifest in the Linux mirror.
3. PowerShell is only the Windows-side process launcher. All gold Python and
   data writes ran in WSL. Native-command argument arrays must be passed through
   the named `-CommandArguments` parameter; nested command strings remain
   prohibited.
4. The restricted execution token can hide per-user WSL distro registration
   even though `Ubuntu-24.04` is installed for `luish`. The approved user-context
   launcher is therefore required; this is not a Windows-Python fallback.
5. The single final audit remained valuable: it found three genuine recall
   gaps. Two were resolved in one remediation, and the remaining numeric
   completeness issue required a second focal correction before the final pass.

Detailed retrospective and next optimization stories:
`docs/coordination/msf-r20-gold-runtime-pilot-001-retrospective.md`.
