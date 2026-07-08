# Retrieval Recipe

Source layer: `curated_insights`

Primary process tag:

- `process-quiz`

Imported transversal module tags:

- `process-mecanismo-big-idea`
- `process-prova-depoimentos`

Use search while exploring:

```powershell
.\.venv\Scripts\python.exe -B scripts\search_insights.py --source curated --process-tags process-quiz,process-mecanismo-big-idea,process-prova-depoimentos --query "<briefing terms>" --limit 20
```

Use strategy packs when producing an output:

```powershell
.\.venv\Scripts\python.exe -B scripts\generate_strategy_pack.py --source curated --task quiz --process-tags process-quiz,process-mecanismo-big-idea,process-prova-depoimentos --product "<product>" --avatar "<avatar>" --market "<market>" --asset-type "quiz-funnel" --query "<briefing terms>" --limit 20 --output-json data/exports/strategy_pack_quiz.json --output-md data/exports/strategy_pack_quiz.md
```

Selection rules:

1. Keep `process-quiz` as the primary filter and use transversal tags only to
   support mechanism, belief, proof, credibility, testimonial logic, or
   claim-risk control.
2. Preserve MMR/Jaccard diversity, episode cap, and thesis cap from MSF-R11.
3. Prefer insights with strong quiz operations: first question, diagnostic
   sequence, self-recognition, result personalization, mechanism congruence,
   mini VSL placement, offer bridge, completion/drop-off metrics, or backend
   ascension.
4. If a process-specific choice is about question order, answer options,
   segmentation, result type, result copy, quiz-to-offer bridge, completion
   page, mini VSL placement, or page-level analytics, keep that logic inside
   this skill.
5. Deduplicate evidence counts by `insight_id` across imported modules. Known
   overlap ids `zoChfFHnlOQ-v2-0008` and `mCaFyZpXJdE-v2-0011` count once.
6. Cite the `insight_id` for any rule imported into the playbook.
7. Do not import separate offer, low-ticket, VSL, pricing, or ads modules
   unless the owner requests it; this skill can use insights carrying those
   tags only when they also support quiz decisions.

Useful audit command for this skill:

```powershell
.\.venv\Scripts\python.exe -B scripts\validate_process_skill.py skills\msf-process-quiz
```

Transversal module recipes live in
`skills/_modules/msf-transversal-copy/retrieval.md`. Import those recipes by
reference; do not duplicate the shared module playbook in this skill.
