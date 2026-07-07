# Strategy Pack Loop

Goal: turn the local base into task-ready context for a consuming agent.

## Steps

1. Run `scripts/consolidate_exports.py`.
2. Explore with `scripts/search_insights.py`.
3. Generate the pack:
   `scripts/generate_strategy_pack.py --task <vsl|anuncios|oferta|quiz|webinar> --product "<produto>" --avatar "<avatar>" --market "<mercado>" --output-json data/exports/strategy_pack.json --output-md data/exports/strategy_pack.md`
4. Use `prompts/retrieval/strategy_pack_retrieval.md` if a model needs to reshape or rerank retrieved records.
5. Require final outputs to list `insight_id` values used.

## Done

- Strategy pack has priority insights, evidence, warnings, and open questions.
- Empty or weak packs are reported as a base maturity issue instead of being papered over.
