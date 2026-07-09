# Retrieval Recipe

Source layer: `v2_master_pool`

Data root:

```powershell
$dataRoot = if ($env:MSF_DATA_DIR) { $env:MSF_DATA_DIR } else { "data" }
```

Primary process tag:

- `process-copy-vsl`

Imported transversal module tags:

- `process-mecanismo-big-idea`
- `process-prova-depoimentos`

Use search while exploring:

```powershell
.\.venv\Scripts\python.exe -B scripts\search_insights.py --source pool --min-editorial-score 90 --process-tags process-copy-vsl,process-mecanismo-big-idea,process-prova-depoimentos --query "<briefing terms>" --limit 20
```

Use strategy packs when producing an output:

```powershell
.\.venv\Scripts\python.exe -B scripts\generate_strategy_pack.py --source pool --min-editorial-score 90 --task vsl --process-tags process-copy-vsl,process-mecanismo-big-idea,process-prova-depoimentos --product "<product>" --avatar "<avatar>" --market "<market>" --asset-type "vsl" --query "<briefing terms>" --limit 20 --output-json "$dataRoot\exports\strategy_pack_vsl.json" --output-md "$dataRoot\exports\strategy_pack_vsl.md"
```

Selection rules:

1. Keep `process-copy-vsl` as the primary filter and use transversal tags only
   to support one belief, mechanism, proof, credibility, or claim-risk control.
2. Preserve MMR/Jaccard diversity, episode cap, and thesis cap from MSF-R11.
3. Prefer insights with strong VSL operations: lead, story, one belief,
   mechanism, proof, objection handling, offer bridge, CTA, retention, or VSL
   testing.
4. If a process-specific choice is about lead, video structure, proof
   placement, objection handling, offer bridge, CTA, or retention, keep that
   logic inside this skill.
5. Deduplicate evidence counts by `insight_id` across imported modules. Known
   overlap ids `zoChfFHnlOQ-v2-0008` and `mCaFyZpXJdE-v2-0011` count once.
6. Cite the original `insight_id` for every rule imported into the internal
   playbook. Do not cite a module as if it were evidence.
7. Do not import separate offer, quiz, or pricing modules unless the owner
   requests it; this skill can use insights carrying those tags only when they
   also support VSL copy decisions.
8. `--min-editorial-score 90` is the current R16 floor recommendation for
   pool retrieval, pending owner approval; do not set a floor below 80 without
   owner approval.

Useful audit command for this skill:

```powershell
.\.venv\Scripts\python.exe -B scripts\validate_process_skill.py skills\msf-process-copy-vsl
```

Transversal module recipes live in
`skills/_modules/msf-transversal-copy/retrieval.md`. Import those recipes by
reference; do not duplicate the shared module playbook in this skill.
