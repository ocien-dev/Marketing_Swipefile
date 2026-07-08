# Retrieval Recipe

Source layer: `curated_insights`

Primary process tag:

- `process-produto-low-ticket`

Imported transversal module tags:

- `process-mecanismo-big-idea`
- `process-prova-depoimentos`

Use search while exploring:

```powershell
.\.venv\Scripts\python.exe -B scripts\search_insights.py --source curated --process-tags process-produto-low-ticket,process-mecanismo-big-idea,process-prova-depoimentos --query "<briefing terms>" --limit 20
```

Use strategy packs when producing an output:

```powershell
.\.venv\Scripts\python.exe -B scripts\generate_strategy_pack.py --source curated --task oferta --process-tags process-produto-low-ticket,process-mecanismo-big-idea,process-prova-depoimentos --product "<product>" --avatar "<avatar>" --market "<market>" --asset-type "low-ticket-product" --query "<briefing terms>" --limit 20 --output-json data/exports/strategy_pack_lowticket.json --output-md data/exports/strategy_pack_lowticket.md
```

Selection rules:

1. Keep `process-produto-low-ticket` as the primary filter and use transversal
   tags only to support mechanism, belief, proof, credibility, testimonial
   logic, or claim-risk control.
2. Preserve MMR/Jaccard diversity, episode cap, and thesis cap from MSF-R11.
3. Prefer insights with strong low-ticket operations: entry transformation,
   simplified promise, recut from a larger product, price-value fit,
   consumability, validation budget, creative/offer test, backend bridge, or
   product ladder.
4. If a process-specific choice is about entry transformation, delivery format,
   scope, consumability, price, backend ascension, product ladder, checkout
   promise, or validation plan, keep that logic inside this skill.
5. Deduplicate evidence counts by `insight_id` across imported modules. Known
   overlap ids `zoChfFHnlOQ-v2-0008` and `mCaFyZpXJdE-v2-0011` count once.
6. Cite the original `insight_id` for every rule imported into the internal
   playbook. Do not cite a module as if it were evidence.
7. Do not import separate offer, quiz, VSL, pricing, or ads modules unless the
   owner requests it; this skill can use insights carrying those tags only when
   they also support low-ticket product decisions.

Useful audit command for this skill:

```powershell
.\.venv\Scripts\python.exe -B scripts\validate_process_skill.py skills\msf-process-produto-low-ticket
```

Transversal module recipes live in
`skills/_modules/msf-transversal-copy/retrieval.md`. Import those recipes by
reference; do not duplicate the shared module playbook in this skill.
