# Insight Quality Checklist

Use this checklist to review insights extracted for Marketing Swipe File.

## Required

- Has at least one evidence item.
- Evidence quote is exact and not paraphrased.
- Evidence has a locator: segment id, timestamp, asset id, page, sheet/range, slide, or episode id.
- Insight is atomic: one idea, principle, tactic, warning, example, or framework.
- Insight is actionable for at least one agent role.
- Level is correct: `strategic`, `tactical`, or `operational`.
- Insight type is specific enough.
- Themes match the taxonomy where possible.
- Confidence score is justified by the evidence.
- Dedupe key is stable, lowercase, ASCII, and meaning-based.

## Reject Or Mark Needs Review

- No evidence.
- Generic motivational advice.
- Summary without tactical or strategic value.
- Unsupported performance claim.
- Quote with no useful interpretation.
- Duplicate of an existing insight.
- Overly broad insight that should be split.
- Advice that only makes sense outside the stated source context.

## Confidence Guidance

- `0.80-1.00`: strong direct evidence and clear applicability.
- `0.60-0.79`: useful but needs some interpretation or context.
- `0.40-0.59`: plausible but weak, vague, or incomplete.
- `0.00-0.39`: do not use in final outputs unless explicitly marked as hypothesis.

## Evidence Strength

- `strong`: source directly states or demonstrates the insight.
- `medium`: source strongly implies it, but some synthesis is needed.
- `weak`: source is vague or partial; use only as hypothesis.

## Human Review Questions

- Would this help create better copy, ads, VSLs, quizzes, offers, funnels, product decisions, or operations?
- Can another agent use this without watching the episode?
- Is the evidence enough to prevent hallucination?
- Is the insight specific enough to retrieve later?

