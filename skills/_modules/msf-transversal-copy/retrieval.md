# Retrieval Recipes For Transversal Copy Modules

Source layer: `curated_insights`

Data root:

```powershell
$dataRoot = if ($env:MSF_DATA_DIR) { $env:MSF_DATA_DIR } else { "data" }
```

## Mecanismo E Big Idea

```powershell
.\.venv\Scripts\python.exe scripts\search_insights.py --source curated --process-tags process-mecanismo-big-idea --limit 20
```

```powershell
.\.venv\Scripts\python.exe scripts\generate_strategy_pack.py --source curated --task vsl --process-tags process-mecanismo-big-idea --product "<product>" --avatar "<avatar>" --market "<market>" --limit 20 --output-json "$dataRoot\exports\strategy_pack_module_mecanismo_big_idea.json" --output-md "$dataRoot\exports\strategy_pack_module_mecanismo_big_idea.md"
```

## Prova E Depoimentos

```powershell
.\.venv\Scripts\python.exe scripts\search_insights.py --source curated --process-tags process-prova-depoimentos --limit 20
```

```powershell
.\.venv\Scripts\python.exe scripts\generate_strategy_pack.py --source curated --task oferta --process-tags process-prova-depoimentos --product "<product>" --avatar "<avatar>" --market "<market>" --limit 20 --output-json "$dataRoot\exports\strategy_pack_module_prova_depoimentos.json" --output-md "$dataRoot\exports\strategy_pack_module_prova_depoimentos.md"
```

## Combined Use In Process Skills

Use module tags together with the process skill's primary tag:

```powershell
.\.venv\Scripts\python.exe scripts\generate_strategy_pack.py --source curated --task oferta --process-tags process-construcao-oferta,process-mecanismo-big-idea,process-prova-depoimentos --product "<product>" --avatar "<avatar>" --market "<market>" --limit 20
```

Rules:

1. Keep the primary process tag as the main filter for the skill.
2. Add transversal tags only when the output needs belief, mechanism, proof,
   credibility, testimonials, or expert authority.
3. Preserve MMR/Jaccard diversity, episode cap, and thesis cap.
4. Cite the original `insight_id`; do not cite the module as if it were an
   evidence source.
5. If module and process skill conflict, prefer the curated insight evidence
   and flag the contradiction for review.
