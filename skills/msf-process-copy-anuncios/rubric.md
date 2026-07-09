# Copy Anuncios Rubric

Aligned with `docs/output-evaluation-rubric.md`.

Score each criterion from 1 to 5. The output passes only if the total is 32+
out of 40, no criterion is below 3, and citation fidelity passes.

| Criterion | What to verify |
|---|---|
| Hook strength | The first line, frame, headline, or search message can stop attention or capture qualified intent. |
| Angle clarity | The ad has one dominant idea instead of several disconnected promises. |
| Avatar fit | The language, pain, desire, and sophistication level match the intended buyer. |
| Proof or plausibility | The claim feels believable through proof, demonstration, mechanism, specificity, or claim-risk control. |
| Testability | The ad states a clear hypothesis and isolates what variable is being tested. |
| Platform fit | The copy and format fit the selected channel, placement, and traffic temperature. |
| Creative direction | Visual, edit, layout, or production notes are concrete enough for execution. |
| Base usage | Non-obvious claims cite curated `insight_id` values and apply them instead of merely listing them. |

Commercial combined criterion for ads:

- `hook_strength_score`
- `proof_or_plausibility_score`
- `testability_score`

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
- Lets transversal modules decide ad-specific hook, angle, platform fit,
  script shape, creative direction, CTA, or variation plan.
- Changes evidence quotes by stripping accents or rewriting the quote.
- Produces a final output in broken Portuguese or ASCII-stripped wording.

Blind S09 fields:

- `hook_strength_score`
- `angle_clarity_score`
- `avatar_fit_score`
- `proof_or_plausibility_score`
- `testability_score`
- `platform_fit_score`
- `creative_direction_score`
- `base_usage_score`
- `winner_or_tie`
- `judge_notes`
