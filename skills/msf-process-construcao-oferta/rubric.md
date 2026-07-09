# Construcao De Oferta Rubric

Score each criterion from 1 to 5. The output passes only if the total is 32+
out of 40, no criterion is below 3, and citation fidelity passes.

| Criterion | What to verify |
|---|---|
| Offer fit | The output solves offer construction, not generic copy, product, or funnel advice. |
| Promise and avatar fit | The promise is specific, believable, scoped to the avatar, and tied to a real buyer pain. |
| Mechanism and belief bridge | The offer explains why the result is possible and why the next action follows logically. |
| Stack and delivery logic | Core deliverable, bonuses, guarantee, and implementation aids each have a clear job. |
| Pricing and anchoring logic | Price, value comparison, risk reversal, and margin assumptions are explicit or flagged as unknown. |
| Proof and claim control | Proof is placed at the claim it supports; risky claims are qualified instead of amplified. |
| Funnel and backend coherence | The offer connects to CTA, checkout/application path, validation loop, and next monetization step. |
| Evidence fidelity and usability | Non-obvious claims cite curated `insight_id` values, citations support the claims, and the final output is usable in pt-BR. |

Output contract checks:

- Evidence binding: material claims are marked with `[insight:<id>]` or `[generic-practice]`, and unavailable curated data triggers `SEM BASE - resposta nao fundamentada`.
- Claim fence: money, health, esoteric, platform, and other high-risk claims state what cannot be promised.
- Proof fit: each core claim or mechanism names the proof type or is marked proof-weak and reduced.
- Testable bet: the output includes a falsifiable hypothesis, variants, metric, failure signal, and minimum read condition.
- Coherence check: when more than one mechanism is combined, the output names one belief and flags conflicts.

Hard fails:

- Uses non-curated insights as if they were curated.
- Omits `insight_id` citations for non-obvious playbook claims.
- Counts the same `insight_id` twice across imported modules, especially
  `zoChfFHnlOQ-v2-0008` or `mCaFyZpXJdE-v2-0011`.
- Lets transversal modules decide pricing, bonuses, guarantee, CTA, or value
  ladder instead of keeping that logic in this skill.
- Changes evidence quotes by stripping accents or rewriting the quote.
- Produces a final output in broken Portuguese or ASCII-stripped wording.

Blind S09 fields:

- `offer_fit_score`
- `promise_avatar_fit_score`
- `mechanism_belief_bridge_score`
- `stack_delivery_logic_score`
- `pricing_anchoring_logic_score`
- `proof_claim_control_score`
- `funnel_backend_coherence_score`
- `evidence_usability_score`
- `winner_or_tie`
- `judge_notes`
