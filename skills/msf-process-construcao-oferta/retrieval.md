# Retrieval Recipe

Source layer: `v2_master_pool`

Data root:

```powershell
$dataRoot = if ($env:MSF_DATA_DIR) { $env:MSF_DATA_DIR } else { "data" }
```

Primary process tag:

- `process-construcao-oferta`

Imported transversal module tags:

- `process-mecanismo-big-idea`
- `process-prova-depoimentos`

Use search while exploring:

```powershell
.\.venv\Scripts\python.exe scripts\search_insights.py --source pool --min-editorial-score 90 --process-tags process-construcao-oferta,process-mecanismo-big-idea,process-prova-depoimentos --query "<briefing terms>" --limit 20
```

Use strategy packs when producing an output:

```powershell
.\.venv\Scripts\python.exe scripts\generate_strategy_pack.py --source pool --min-editorial-score 90 --task construcao-oferta --process-tags process-construcao-oferta,process-mecanismo-big-idea,process-prova-depoimentos --product "<product>" --avatar "<avatar>" --market "<market>" --limit 20 --output-json "$dataRoot\exports\strategy_pack_construcao-oferta.json" --output-md "$dataRoot\exports\strategy_pack_construcao-oferta.md"
```

Selection rules:

1. Keep `process-construcao-oferta` as the primary filter and use transversal
   tags only to support promise logic, mechanism, proof, credibility, or claim
   risk.
2. Preserve MMR/Jaccard diversity, episode cap, and thesis cap from MSF-R11.
3. Prefer insights with strong offer operations: validation, stack, price,
   proof, backend, value ladder, or offer-to-funnel connection.
4. Pricing and anchoring logic belongs to this skill. It may be supported by
   offer insights that also carry `process-precificacao`, but do not import a
   separate pricing module unless the owner requests it.
5. Deduplicate evidence counts by unique `insight_id` across imported modules.
   Known overlap ids `zoChfFHnlOQ-v2-0008` and `mCaFyZpXJdE-v2-0011` count
   once.
6. Cite the original `insight_id` for every rule imported into the internal
   playbook. Do not cite a module as if it were evidence.
7. Keep quiz, low-ticket, CTA, pricing, bonus, guarantee, and value-ladder
   decisions inside this skill; transversal module claims stay at principle
   level.
8. `--min-editorial-score 90` is the current R16 floor recommendation for
   pool retrieval, pending owner approval; do not set a floor below 80 without
   owner approval.

Useful audit command for this skill:

```powershell
.\.venv\Scripts\python.exe scripts\validate_process_skill.py skills\msf-process-construcao-oferta
```

Transversal module recipes live in
`skills/_modules/msf-transversal-copy/retrieval.md`. Import those recipes by
reference; do not duplicate the shared module playbook in this skill.
