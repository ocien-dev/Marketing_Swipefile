# MSF-R15 Output Contract Plan

Status: proposal only. No process skill files were edited in this task.

Date: 2026-07-08

## Scope

MSF-R15 proposes an additive output contract for the five approved process
skills:

- `skills/msf-process-construcao-oferta/`
- `skills/msf-process-copy-vsl/`
- `skills/msf-process-copy-anuncios/`
- `skills/msf-process-produto-low-ticket/`
- `skills/msf-process-quiz/`

The proposal also adds a checklist requirement for the transversal module
`transversal:mecanismo-big-idea`.

This plan does not reopen the blind gates. It changes the output shape and
grounding discipline that future skill runs must follow.

## Proposed Required Output Sections

Add these five sections to every final deliverable produced by the approved
process skills.

### 1. Evidence Binding

Every material claim should be marked as one of:

- `[insight:<id>]` when grounded in a curated insight.
- `[generic-practice]` when it is a general marketing practice not directly
  supported by the curated base.

Rules:

- Do not cite an insight unless the cited insight supports the sentence.
- Do not let generic practice masquerade as project-specific evidence.
- If curated insights are unavailable, the output must start with
  `SEM BASE - resposta nao fundamentada` and no `[insight:<id>]` claims may be
  invented.

### 2. Claim Fence

Every deliverable should state what cannot be promised.

Minimum fences:

- Money claims: no guaranteed income, ROI, revenue, profit, conversion lift, or
  scale promise without explicit proof and conditions.
- Health claims: no diagnosis, cure, treatment, body outcome, or safety claim
  beyond the evidence available.
- Esoteric claims: no certainty about fate, spiritual result, destiny, or
  supernatural causality.
- Platform claims: no guaranteed approval, account safety, CPM, CPC, CPA, or
  deliverability when platform behavior can change.

### 3. Proof Fit

For each core mechanism or promise, the deliverable should say how the claim can
be proven.

Examples:

- Demonstration proof: before/after, walkthrough, teardown, screen recording.
- Social proof: testimonial, case, review, customer quote, benchmark.
- Mechanism proof: causal explanation, data point, study, operational trace.
- Behavioral proof: click, reply, checkout, retention, activation, repeat use.

If a mechanism resists proof, mark it explicitly as proof-weak and reduce the
claim.

### 4. Testable Bet

Each deliverable should produce at least one falsifiable test.

Minimum fields:

- Hypothesis.
- Variant A and variant B.
- Primary metric.
- Failure signal.
- Minimum read condition.

The test must be specific enough that a future operator can tell whether the
idea survived or failed.

### 5. Coherence Check

When an output combines more than one mechanism, it must name the single belief
the audience is supposed to leave with.

Rules:

- Do not stack mechanisms that imply different causes for the same outcome.
- Do not combine proof types that point to different promises.
- If two mechanisms are useful but incoherent together, split them into
  separate angles, variants, or funnel steps.

## Mechanism Module Checklist

The transversal module `transversal:mecanismo-big-idea` should require the
consumer skill to answer:

- What belief does this mechanism need to create?
- What evidence supports that belief?
- What evidence would falsify or weaken that belief?
- What claim is outside the allowed fence?
- Does this mechanism conflict with another imported mechanism?
- Is the mechanism process-specific or transversal?

Process-specific logic remains in the skill, not in the transversal module. For
example: quiz segmentation, low-ticket pricing, CTA wording, bonus structure,
ad platform fit, and VSL lead shape stay in the process skill.

## Files To Change After Approval

If approved, the additive contract would touch:

- `skills/_templates/msf-process-skill/templates/output-template.md`
- `skills/_templates/msf-process-skill/skill.contract.json`
- `skills/_templates/msf-process-skill/rubric.md`
- Each approved skill's `templates/output-template.md`
- Each approved skill's `skill.contract.json`
- Each approved skill's `rubric.md`
- `skills/_modules/msf-transversal-copy/*` docs or contract file that defines
  the mechanism checklist

No skill edits were made in MSF-R15 before owner audit.

## Validation To Re-run After Approval

After implementing the additive sections, re-run:

- `scripts/validate_process_skill.py --require-done` for the five approved
  process skills.
- `scripts/validate_transversal_modules.py` for the transversal modules.
- Retrieval smoke test with `MSF_DATA_DIR` set to the external data root.
- Missing-curated smoke test proving outputs open with
  `SEM BASE - resposta nao fundamentada`.
- Encoding guard for generated outputs.

Blind S09 gates do not need to be reopened because this is an additive output
contract and not a change to the judged skill strategy, examples, or retrieval
evidence. Reopen a blind gate only if the actual strategic behavior of a skill
changes.

## Open Question: Curated Portability

The current curated base is local-only under `MSF_DATA_DIR`, usually:

`C:\MSF-data\Marketing_Swipe_File\exports\curated_insights.json`

This is correct for local Codex work after MSF-R03, but the agent layer needs a
portability decision before it can depend on curated insights:

- Keep curated local-only and require agents to run on the same machine with
  `MSF_DATA_DIR`.
- Export a versioned portable curated package without raw/local-only payloads.
- Move curated to a durable service or database after the local gates are
  stable.

Until that decision is made, agents must treat missing curated data as
`curated_unavailable` and open with `SEM BASE - resposta nao fundamentada`.
