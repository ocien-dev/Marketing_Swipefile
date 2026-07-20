# MSF-R20 Gold Semantic Compiler 002 - Short Pilot Retrospective

Status: archived_research_not_for_production
Episode: `AqzF_M2mM04`
Date: 2026-07-17

Canonical production route: `chronological_hybrid_v1`; this document is
historical benchmark evidence only.

## Decision

Do not replace the current gold workflow yet.  The blind shard architecture
proved that model wall time can fit comfortably below ten minutes, but its
first independent extraction was not quality-equivalent to the approved gold.
The two longer episodes remain prepared but were intentionally not submitted.

## Measured execution

- source: 395 segments and 17 approved candidates;
- extraction: seven concurrent `gpt-5.6-terra/high` calls;
- extraction wall: 88.821 seconds;
- final evaluation: one `gpt-5.6-sol/high` call;
- evaluation wall: 221.010 seconds;
- combined model wall: 309.831 seconds, or 5 minutes 9.831 seconds;
- adapter tokens: 162,414 input, 24,861 output, 3,922 reasoning output;
- judge tokens: 85,993 input, 11,650 output, 5,250 reasoning output;
- total reported: 248,407 input, 36,511 output, 9,172 reasoning output;
- tool-use events: zero in all eight calls;
- deterministic evidence errors: zero.

## Quality result

The adapter emitted 84 atoms for a 17-candidate gold reference.  Evidence
anchoring found at least one overlapping source segment for 16/17 approved
candidates.  This showed high recall pressure but excessive fragmentation.

The Sol judge reported:

- material recall: 0.8529;
- unsupported claims: 1;
- partial approved candidates: 3;
- number recall: 0.9444;
- procedure recall: 0.7500;
- caveat recall: 0.8947;
- relation recall: 0.1250;
- calibration recall: 0.6667;
- open findings: 6.

The deterministic exact-raw metric was lower, 0.6389, while semantic number
recall was 0.9444.  Exact string matching is useful as a warning but is too
strict to be the sole quality measure.  The final judge still found one real
numeric omission.

## Findings

1. The solo/short podcast-format experiment and its continuation rule were
   omitted completely.
2. The initial quantitative case retained 125% but lost 42% and the external
   verification proposition.
3. The image-generation procedure omitted its initial prompt/niche steps.
4. Seven leverage-point children were extracted, but the parent framework and
   its seven parent/child relations were not reconstructed.
5. The exact count of two textual headline variants was not preserved.
6. One atom specialized a generic automatic-test passage into an unsupported
   speed-test procedure.

## What worked

- Independent extraction was genuinely oracle-free at prompt time.
- Concurrent sharding reduced semantic reading to under 90 seconds.
- Segment-ID evidence eliminated fabricated quote text and made validation
  deterministic.
- The isolated transport produced structured outputs with no agent tools.
- One final evaluator separated harmless string variation from material loss.

## What must change before another paid benchmark

1. Add a global semantic reducer after shard extraction.  It must merge
   duplicate atoms, reconstruct episode-level frameworks, and resolve
   cross-shard relations before evaluation.
2. Add deterministic source inventories for every numeric occurrence and every
   prepared calibration target.  Shards must acknowledge each inventory item
   as captured, merged, or intentionally excluded.
3. Preserve prompt/interviewer material when it defines a transferable test or
   decision rule; do not discard it by speaker type alone.
4. Require procedures to prove all boundary steps, including setup steps in the
   preceding shard context.
5. Run a compact support verifier before the Sol judge to reject atom claims
   whose selected evidence does not contain their procedural specialization.
6. Reduce the judge packet by deterministic candidate-to-atom matching.  The
   judge consumed 221 seconds and 85,993 input tokens, more than twice the
   extraction wall.

## Safety verification

The three source hashes, five packet hashes, and two protected aggregate hashes
were rechecked against the approved completion receipt and remained identical.
No approved gold, packet, audit, status, or fingerprint changed.

## Artifacts

- `.codex-work/worker-jobs/MSF-R20-GOLD-SEMANTIC-COMPILER-002/results/AqzF_M2mM04/pilot_report.json`;
- `.codex-work/worker-jobs/MSF-R20-GOLD-SEMANTIC-COMPILER-002/results/AqzF_M2mM04/comparison_packet.json`;
- `.codex-work/worker-jobs/MSF-R20-GOLD-SEMANTIC-COMPILER-002/results/AqzF_M2mM04/judge_response.json`;
- `.codex-work/worker-jobs/MSF-R20-GOLD-SEMANTIC-COMPILER-002/results/AqzF_M2mM04/judge_invocation_report.json`;
- Linux canonical job: `/home/luish/.cache/msf/jobs/MSF-R20-GOLD-SEMANTIC-COMPILER-002`.
