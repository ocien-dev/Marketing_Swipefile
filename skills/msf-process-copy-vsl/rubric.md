# Copy VSL Rubric

Aligned with `docs/output-evaluation-rubric.md`.

Score each criterion from 1 to 5. The output passes only if the total is 32+
out of 40, no criterion is below 3, and citation fidelity passes.

| Criterion | What to verify |
|---|---|
| Clarity | The promise, viewer problem, next step, and script flow are easy to understand. |
| Curiosity | The lead creates tension and an open loop without revealing the whole mechanism too early. |
| Specificity | The VSL uses concrete stakes, avatar language, and product context instead of generic claims. |
| Mechanism and belief | The one belief and mechanism explain why the result is possible and why the offer follows. |
| Proof | Claims are supported by proof, expert story, demonstration, testimonial logic, or credible evidence. |
| Objection handling | Likely objections are named and answered before they block the offer bridge. |
| Offer bridge | The pitch connects naturally to the problem, mechanism, product logic, and CTA. |
| Base usage | Non-obvious claims cite curated `insight_id` values and apply them instead of merely listing them. |

Commercial combined criterion for VSL:

- `mechanism_belief_score`
- `proof_score`
- `objection_handling_score`

Hard fails:

- Uses non-curated insights as if they were curated.
- Omits `insight_id` citations for non-obvious playbook claims.
- Counts the same `insight_id` twice across imported modules, especially
  `zoChfFHnlOQ-v2-0008` or `mCaFyZpXJdE-v2-0011`.
- Lets transversal modules decide VSL-specific lead, structure, proof
  placement, objection handling, offer bridge, CTA, or retention testing.
- Changes evidence quotes by stripping accents or rewriting the quote.
- Produces a final output in broken Portuguese or ASCII-stripped wording.

Blind S09 fields:

- `clarity_score`
- `curiosity_score`
- `specificity_score`
- `mechanism_belief_score`
- `proof_score`
- `objection_handling_score`
- `offer_bridge_score`
- `base_usage_score`
- `winner_or_tie`
- `judge_notes`
