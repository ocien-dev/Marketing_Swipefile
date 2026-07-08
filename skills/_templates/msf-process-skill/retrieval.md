# Retrieval Recipe

Source layer: `curated_insights`

Data root:

```powershell
$dataRoot = if ($env:MSF_DATA_DIR) { $env:MSF_DATA_DIR } else { "data" }
```

Process tags:

- __PROCESS_TAGS_INLINE__

Use search while exploring:

```powershell
.\.venv\Scripts\python.exe scripts\search_insights.py --source curated --process-tags __PROCESS_TAGS_CSV__ --query "<briefing terms>" --limit 20
```

Use strategy packs when producing an output:

```powershell
.\.venv\Scripts\python.exe scripts\generate_strategy_pack.py --source curated --task __SLUG__ --process-tags __PROCESS_TAGS_CSV__ --product "<product>" --avatar "<avatar>" --market "<market>" --limit 20 --output-json "$dataRoot\exports\strategy_pack___SLUG__.json" --output-md "$dataRoot\exports\strategy_pack___SLUG__.md"
```

Selection rules:

1. Keep only insights that contain at least one requested `process_tag`.
2. Preserve MMR/Jaccard diversity and the episode cap from MSF-R11.
3. Prefer higher `editorial_score`, strong evidence, and specific operational
   takeaways.
4. Use transversal tags only when they support the primary process output.
5. Deduplicate evidence counts by `insight_id` across imported modules. Known
   overlap ids `zoChfFHnlOQ-v2-0008` and `mCaFyZpXJdE-v2-0011` count once.
6. Cite the `insight_id` for any rule imported into the playbook.
7. Keep quiz, low-ticket, CTA, and other process-specific logic in the process
   skill; transversal module claims stay at principle level.

Transversal module recipes live in
`skills/_modules/msf-transversal-copy/retrieval.md`. Import those recipes by
reference; do not duplicate the shared module playbook in this skill.
