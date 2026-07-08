# MSF-R12 Curated Insights Lot - 2026-07-07

- Source: `data\exports\insights_v2_master.json`
- Source insights: 207
- Curated insights: 125
- Excluded below score floor: 0
- Score floor: 50
- Cluster threshold: 0.62
- Cluster count in curated lot: 113
- Owner review sample: `data\exports\curated_insights_owner_review_sample_2026-07-07.csv`

## Score Distribution

- Min: 90
- Max: 100
- Average: 96.67
- 50-59: 0
- 60-69: 0
- 70-79: 0
- 80-89: 0
- 90-100: 125

## Priority Coverage

- Items with at least one first-wave process tag: 125
- process-construcao-oferta: 68
- process-copy-vsl: 51
- process-copy-anuncios: 18
- process-produto-low-ticket: 29
- process-quiz: 20
- process-mecanismo-big-idea: 30
- process-prova-depoimentos: 33

## Top Process Tags

- process-construcao-oferta: 68
- process-copy-vsl: 51
- process-precificacao: 36
- process-prova-depoimentos: 33
- process-mecanismo-big-idea: 30
- process-produto-low-ticket: 29
- process-arquitetura-funil: 23
- process-quiz: 20
- process-escada-produtos: 19
- process-copy-anuncios: 18
- process-estrategia-negocio: 16
- process-headlines-hooks: 16
- process-lancamento: 15
- process-pesquisa-avatar: 12
- process-teste-variacao-criativos: 10

## Human Review

- The owner review sample has 30 items with empty `owner_decision` and `owner_notes` columns.
- Owner review completed on 2026-07-07: the owner kept the sample decisions as filled, with no mass rejection.
- Gate R3 is approved after owner review and external technical review.

## Gate R3 Notes

- `editorial_score` is compressed in this first curated lot: min 90, median 97. Calibrate the scoring rubric with owner annotations before the next curated lot.
- `process-copy-anuncios` has 18 curated items. This is enough to start MSF-S, and later backfill should increase coverage.
- One title suffix boilerplate was flagged in the R13 technical review (`...em lateralizar`) and should be rewritten before the next pack refresh.
