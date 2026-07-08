# Output Evaluation Rubric

Use this rubric to compare outputs created without the Marketing Swipe File against outputs created with the base.

## Required Evidence

An output that claims to use the base must include:

- `insight_id` references.
- A short explanation of how each referenced insight influenced the output.
- Evidence quotes in the strategy pack or source notes.
- Warnings for weak or low-confidence insights.

## Language And Encoding

- Final human-facing outputs in Portuguese, including VSLs, ads, quizzes,
  emails, templates, and skill examples, must use full pt-BR accentuation and
  correct spelling.
- If a final pt-BR output has no accented characters and also shows ASCII
  stripping artifacts such as `contm`, `variaao`, `negcio`, `vdeo`,
  `contedo`, `vocs`, `fcil`, `possvel`, `nvel`, or `mtodo`, quality fails
  until corrected.
- If a final pt-BR output has no accented characters but no known stripping
  artifact, mark it `needs_revision` until full pt-BR accentuation is verified.
- Evidence quotes remain verbatim UTF-8 and should not be normalized for the
  evaluation report.
- Internal playbooks, ids, tags, repo docs, and editorial data may use ASCII
  only by Unicode NFKD transliteration, never by character deletion.

## VSL Criteria

Score each from 0 to 5:

- Clarity: the promise and next step are easy to understand.
- Curiosity: the lead creates tension without giving away the whole mechanism.
- Specificity: the script avoids generic claims and uses concrete stakes.
- Mechanism: the unique mechanism is clear and differentiated.
- Proof: claims are supported by proof, examples, or credible evidence.
- Objection handling: likely objections are named and answered.
- Offer bridge: the pitch connects naturally to the problem and mechanism.
- Base usage: the script cites and applies relevant `insight_id` values.

## Ad Criteria

Score each from 0 to 5:

- Hook strength: the first line or frame can stop attention.
- Angle clarity: the ad has one dominant idea.
- Avatar fit: the language matches the intended buyer.
- Proof or plausibility: the claim feels believable.
- Testability: the ad suggests a clear hypothesis.
- Platform fit: the script or briefing fits the intended channel.
- Creative direction: visual or production notes are actionable.
- Base usage: the ad cites and applies relevant `insight_id` values.

## Decision

- `pass`: score is 32+ out of 40 and every major claim has traceable support.
- `needs_revision`: score is 22-31 or evidence usage is shallow.
- `fail`: score is below 22, no `insight_id` is cited, or claims are not traceable.

When comparing before/after outputs, the Marketing Swipe File version should improve specificity, proof, mechanism, or angle quality without adding unsupported claims.
