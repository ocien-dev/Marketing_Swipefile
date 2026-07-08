# Produto Low Ticket Rubric

Score each criterion from 1 to 5. The output passes only if the total is 32+
out of 40, no criterion is below 3, and citation fidelity passes.

| Criterion | What to verify |
|---|---|
| Entry transformation clarity | The product promises one small, concrete, believable entry transformation. |
| Avatar promise fit | The promise, language, sophistication level, and urgency fit the intended buyer. |
| Scope consumability | The delivery format, modules, length, assets, and support level feel easy to consume at low ticket. |
| Price-value coherence | The price band, value anchor, conversion logic, and perceived effort fit the scope. |
| Mechanism belief | The output explains why this smaller product can create the entry transformation now. |
| Proof claim control | Proof, authority, and testimonials support the claim without overpromising results. |
| Backend ascension bridge | The front product naturally qualifies the buyer for backend, upsell, recurrence, or high-end offer. |
| Base usage | Non-obvious claims cite curated `insight_id` values and apply them instead of merely listing them. |

Commercial combined criterion for low ticket:

- `entry_transformation_clarity_score`
- `price_value_coherence_score`
- `backend_ascension_bridge_score`

Hard fails:

- Uses non-curated insights as if they were curated.
- Omits `insight_id` citations for non-obvious playbook claims.
- Counts the same `insight_id` twice across imported modules, especially
  `zoChfFHnlOQ-v2-0008` or `mCaFyZpXJdE-v2-0011`.
- Lets transversal modules decide low-ticket-specific transformation, format,
  scope, price-value fit, consumability, backend bridge, or validation plan.
- Treats low ticket as an isolated cheap product with no acquisition or backend
  logic when the briefing requires a business model.
- Changes evidence quotes by stripping accents or rewriting the quote.
- Produces a final output in broken Portuguese or ASCII-stripped wording.

Blind S09 fields:

- `entry_transformation_clarity_score`
- `avatar_promise_fit_score`
- `scope_consumability_score`
- `price_value_coherence_score`
- `mechanism_belief_score`
- `proof_claim_control_score`
- `backend_ascension_bridge_score`
- `base_usage_score`
- `winner_or_tie`
- `judge_notes`
