# Quiz Rubric

Score each criterion from 1 to 5. The output passes only if the total is 32+
out of 40, no criterion is below 3, and citation fidelity passes.

| Criterion | What to verify |
|---|---|
| Question diagnostic coherence | Questions reveal commercially useful diagnosis, segmentation, readiness, or product match instead of collecting random data. |
| Avatar recognition | The lead can recognize their pain, constraint, desire, or situation in the question flow and result copy. |
| Result personalization | Result types and result page copy reflect answer patterns and feel specific without pretending to be medical, financial, or deterministic diagnosis. |
| Mechanism belief | The quiz explains why the diagnosis points to a specific mechanism or next step. |
| Proof claim control | Proof, authority, examples, or testimonials support the claim without overpromising the result. |
| Offer bridge coherence | The transition from result to mini VSL, checkout, application, or backend offer is natural and congruent. |
| Completion design | Opening, progress, final screen, CTA, fallback path, and analytics reduce abandonment and clarify what to test. |
| Base usage | Non-obvious claims cite curated `insight_id` values and apply them instead of merely listing them. |

Commercial combined criterion for quiz:

- `question_diagnostic_coherence_score`
- `result_personalization_score`
- `offer_bridge_coherence_score`

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
- Lets transversal modules decide quiz-specific question order, branch logic,
  result types, mini VSL placement, completion design, or page-level metrics.
- Creates questions that do not change diagnosis, segmentation, belief,
  personalization, or offer readiness.
- Makes the result page a generic sales page instead of a personalized bridge
  from answer pattern to next step.
- Changes evidence quotes by stripping accents or rewriting the quote.
- Produces a final output in broken Portuguese or ASCII-stripped wording.

Blind S09 fields:

- `question_diagnostic_coherence_score`
- `avatar_recognition_score`
- `result_personalization_score`
- `mechanism_belief_score`
- `proof_claim_control_score`
- `offer_bridge_coherence_score`
- `completion_design_score`
- `base_usage_score`
- `winner_or_tie`
- `judge_notes`
