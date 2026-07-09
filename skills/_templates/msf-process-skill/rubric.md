# Process Skill Rubric

Score each criterion from 1 to 5. The output passes only if the total is 32+
out of 40, no criterion is below 3, and citation fidelity passes.

| Criterion | What to verify |
|---|---|
| Process fit | The output solves the requested process, not a generic marketing task. |
| Evidence use | Important claims cite pool `insight_id` values from the retrieval pack. |
| Citation fidelity | Cited insights genuinely support the claim made in the output. |
| Operational specificity | The output contains concrete steps, decisions, examples, or copy, not vague advice. |
| Strategic coherence | The output is coherent with the product, avatar, market, and constraints. |
| Reuse of process patterns | The output applies the process-specific playbook rather than merely quoting insights. |
| Risk handling | High-risk claims are qualified, scoped, or converted into tests. |
| Final-output quality | The final asset is usable in pt-BR with full accents and professional wording. |

Output contract checks:

- Evidence binding: material claims are marked with `[insight:<id>]` or `[generic-practice]`, and unavailable retrieval data triggers `SEM BASE - resposta nao fundamentada`.
- Claim fence: money, health, esoteric, platform, and other high-risk claims state what cannot be promised.
- Proof fit: each core claim or mechanism names the proof type or is marked proof-weak and reduced.
- Testable bet: the output includes a falsifiable hypothesis, variants, metric, failure signal, and minimum read condition.
- Coherence check: when more than one mechanism is combined, the output names one belief and flags conflicts.

Hard fails:

- Uses insights outside the retrieval pool as if they were grounded.
- Omits `insight_id` citations for non-obvious playbook claims.
- Changes evidence quotes by stripping accents or rewriting the quote.
- Produces a final output in broken Portuguese or ASCII-stripped wording.
