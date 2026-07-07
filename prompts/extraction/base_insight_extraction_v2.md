# Marketing Swipe File Insight Extraction V2

You are extracting `raw_insights_v2` from one transcript chunk. The goal is quality, not inventory.

Return only JSON compatible with `schemas/insights_v2.schema.json`, or a chunk-level object with an `insights` array that can be merged by `scripts/extract_transcript_insights_llm.py`.

Rules:

- Maximum 5 insights per chunk.
- Prefer 0 insights over weak or generic insights.
- Each title must be specific to the transcript, not a reusable template.
- Reject promo-contaminated evidence: "inscreva-se", "assista tambem", hashtags, episode title lists, channel CTAs, sponsor boilerplate, or unrelated description links.
- Evidence must be a short exact quote from the chunk and must include `segment_id`, `chunk_id`, and timestamps.
- `canonical_title` and `title` can match in raw v2, but the title must be precise enough to survive retrieval.
- `specific_takeaway` should say the actionable lesson in one sentence.
- `when_to_use` and `when_not_to_use` should stop over-application.
- `claim_risk` is `high` for medical, financial, income, or strong performance claims without enough proof.
- `evidence_cleanliness` is `clean` only when the quote is readable and not promotional.
- `editorial_score` uses the working rubric: evidence 25, specificity 25, applicability 20, portability 15, novelty 10, cleanliness 5.

Output expectations:

- `extraction_method`: `llm_v2`
- `review_status`: `needs_review`
- `source_agent`: `codex_manual_llm_v2` for the Codex-first route
- `supporting_insight_ids`: empty unless you are explicitly extending a known prior insight
- `relations`: empty unless there is a clear relation to another insight in the same file
