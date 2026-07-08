# Backlog De Skills De Processo - Marketing Swipe File (EPIC MSF-S)

Data de criacao: 2026-07-07

## 1. Objetivo

Transformar a base de insights em skills de processo de marketing (copy de
VSL, anuncios, oferta, quiz etc.) que alimentam agentes especializados, com
retroalimentacao continua conforme novos episodios e materiais entram no
pipeline.

Este documento complementa:

- `docs/marketing-swipe-file-remediation-backlog.md` (gates R1-R3)
- `docs/process-taxonomy.md` (vocabulario de processos)
- `docs/marketing-swipe-file-full-backlog.md` (series A-M; este epico detalha
  as camadas 6-8 do principio de execucao)

Regra de execucao: gates R2 e R3 estao aprovados em 2026-07-07, entao EPIC
MSF-S esta destravado. MSF-S01, MSF-S02, MSF-S03, MSF-S04, MSF-S05, MSF-S06 e
MSF-S08 estao done; MSF-S07 esta done/approved. A primeira leva de 5 skills
esta fechada: S03, S04, S05, S06 e S07 foram aprovadas por seus gates S09.
Skill alimentada por base nao curada reproduz o defeito v1; usar
`curated_insights` como fonte candidata/default. Agentes so depois de skills
validadas individualmente.

## 2. Anatomia de uma skill de processo

Cada skill e um diretorio `skills/msf-process-{slug}/` contendo:

1. `SKILL.md`: playbook do processo sintetizado dos insights curados
   (frameworks, principios, erros comuns), com citacao de `insight_id` em
   cada afirmacao nao-obvia (Artigo IV - No Invention).
2. `retrieval.md`: receita de retrieval - quais `process_tags` consome,
   filtros, como montar o pack de contexto para um briefing.
3. `templates/`: esqueletos de output (ex.: estrutura de VSL, matriz de
   angulos de anuncio).
4. `rubric.md`: rubrica de avaliacao especifica do processo, aplicada pelo
   avaliador LLM do MSF-R09.
5. `examples/`: 1+ exemplo real de briefing -> output aprovado.

Politica de escrita por camada:

- Camada interna: dados, ids, tags, titulos, takeaways, campos editoriais,
  docs do repo, playbooks internos e receitas de retrieval usam ASCII por
  transliteracao Unicode NFKD quando precisarem representar portugues sem
  acentos. Acento vira letra base (`variacao`, `contem`, `incrivel`). Nunca
  usar ASCII `errors=ignore` como delecao de caractere. A base existente nao
  deve ser reescrita por causa desta regra; ela ja foi verificada como integra.
- Quotes de evidencia: sempre verbatim UTF-8, com acentos preservados, em
  qualquer arquivo. CSVs voltados a revisao humana devem ser gravados como
  `utf-8-sig`.
- Outputs finais: VSL, anuncios, quizzes, emails, templates e exemplos de
  skill destinados a leitura humana devem sair em portugues com acentuacao
  completa e ortografia correta.
- Scans non-ASCII de repo ou lote so se aplicam a camada interna. Eles nao
  devem reprovar quotes verbatim nem artefatos de output final em pt-BR pleno.
- A wordlist de delecao de acentos em `scripts/audit_insights_v2_text.py`
  vale para todo texto gerado como guarda permanente de regressao.

Definition of Done de qualquer skill:

- Gerou output real a partir de briefing de teste.
- Output avaliado pelo avaliador honesto (R09) contra a rubrica propria.
- Output com skill vence ou empata com baseline sem skill em teste cego
  (metodo do MSF-R10, juiz externo ao gerador).
- Toda afirmacao do playbook rastreia a insight curado ou e marcada como
  pratica generica.

## 3. Selecao por densidade (medida em 2026-07-07)

Base v2 (207 insights, 15 episodios, 100% com process_tags):

| Processo | v2 | v1 (sinal futuro) |
|---|---|---|
| construcao-oferta | 102 | 580 |
| copy-vsl | 73 | 315 |
| prova-depoimentos | 54 | 282 |
| precificacao | 50 | 484 |
| mecanismo-big-idea | 46 | 205 |
| produto-low-ticket | 42 | 404 |
| arquitetura-funil | 39 | - |
| copy-anuncios | 31 | 364 |
| headlines-hooks | 27 | 201 |
| teste-variacao-criativos | 24 | 159 |
| quiz | 21 | 179 |

Primeira leva (densidade + prioridade do owner): copy-vsl,
construcao-oferta (absorve precificacao), copy-anuncios (absorve
headlines-hooks e teste-variacao), produto-low-ticket, quiz.

Adiadas por densidade insuficiente na v2 atual: trafego-meta,
trafego-google-youtube, video-anuncio, imagem-anuncio, copy-carta-vendas,
copy-email, seo. Entram na segunda leva apos backfill dos 508 chunks
restantes e processamento dos assets da academy (aulas de Facebook Ads,
criativos e videos brutos de anuncio cobrem exatamente esses processos).

## 4. Backlog

### MSF-S01 - Contrato e template de skill de processo

Prioridade: `P1`
Tipo: `skill`
Status: `done`

Escopo:

- Criar template de diretorio de skill (secao 2) e schema/checklist de
  validacao de skill.
- Definir formato da citacao de insight_id no playbook.
- Declarar no contrato/template a politica de escrita por camada: playbook
  interno ASCII por NFKD, quotes verbatim UTF-8 e templates/exemplos de output
  em pt-BR pleno com acentuacao correta.

Aceite:

- Template instanciavel; checklist cobre o Definition of Done da secao 2.
- Contrato de skill impede ASCII stripping e separa claramente playbook
  interno, evidencia e output final.

Dependencias: gates R1, R2 e R3 aprovados.

Execucao 2026-07-07:

- Criado template instanciavel em `skills/_templates/msf-process-skill/` com
  `SKILL.md`, `retrieval.md`, `rubric.md`, `skill.contract.json`, `templates/`,
  `examples/` e `agents/openai.yaml`.
- Criado `schemas/msf_process_skill_contract.schema.json`.
- Criado `scripts/create_process_skill.py` para instanciar
  `skills/msf-process-{slug}/` a partir do template, validando `process_tags`
  contra `data/processed/taxonomy_seed.json`.
- Criado `scripts/validate_process_skill.py` para validar contrato, arquivos
  obrigatorios, frontmatter, tags, marcadores de citacao, politica de escrita
  interna e checklist; `--require-done` exige todos os itens da DoD como `pass`.
- Teste adicionado: `tests/test_process_skill_contract.py`.

### MSF-S02 - Retrieval por process_tags

Prioridade: `P1`
Tipo: `script`
Status: `done`

Escopo:

- Estender `search_insights.py` e `generate_strategy_pack.py` com filtro
  `--process-tags`, consumindo `curated_insights` como fonte default.
- Manter penalidade de redundancia (MSF-R11) e cap por episodio.

Aceite:

- Pack gerado por processo contem apenas insights curados das tags pedidas,
  sem duplicacao dominante.

Dependencias: MSF-R11, MSF-R12.

Execucao 2026-07-07:

- `scripts/search_insights.py` agora usa `curated_insights` como fonte default
  via `--source curated`, preservando override por `--master` e fontes
  `raw`/`v1`/`v2`.
- `scripts/search_insights.py` e `scripts/generate_strategy_pack.py` aceitam
  `--process-tags` com lista ou CSV e `--process-tag-mode any|all`.
- `scripts/generate_strategy_pack.py` usa `curated` como fonte default,
  registra `process_tag_filter` no JSON do pack e preserva MMR/Jaccard,
  `--episode-cap` e `--thesis-cap`.
- Helpers compartilhados em `scripts/msf_common.py` normalizam e comparam
  `process_tags` sem alterar quotes de evidencia.
- Skill local `skills/marketing-swipe-file-retrieve/` atualizada com exemplos
  de retrieval por `process_tags`.
- Teste adicionado: `tests/test_process_tag_retrieval.py`.

### MSF-S03 - Skill: copy para VSL

Prioridade: `P1`
Tipo: `skill`
Status: `done`

Escopo: skill `msf-process-copy-vsl` conforme secao 2, consumindo
`process-copy-vsl` + modulos transversais (MSF-S08). Inclui leads, estrutura,
mecanismo, prova e CTA.

Aceite: Definition of Done da secao 2, incluindo teste cego contra baseline.

Dependencias: MSF-S01, MSF-S02, MSF-S08, MSF-S09 parcial S04.

Liberacao 2026-07-08:

- MSF-S04 passou no S09 e validou o pipeline skill -> retrieval -> rubrica ->
  teste cego para a primeira skill real.
- S03 foi liberada como a proxima skill real; S05-S07 seguiriam blocked ate S03
  passar pelo proprio S09.

Execucao 2026-07-08:

- Criada `skills/msf-process-copy-vsl/` via
  `scripts/create_process_skill.py`.
- Preenchidos os 8 arquivos da anatomia: `SKILL.md`,
  `skill.contract.json`, `retrieval.md`, `rubric.md`,
  `templates/output-template.md`, `examples/briefing.md`,
  `examples/output-approved.md` e `agents/openai.yaml`.
- Retrieval usa `curated_insights` com `process-copy-vsl`,
  `process-mecanismo-big-idea` e `process-prova-depoimentos`.
- `module_inheritance_policy` aplicada: dedupe por `insight_id` entre modulos
  e logica especifica de VSL mantida na skill.
- Rubrica alinhada a `docs/output-evaluation-rubric.md`; criterio comercial
  combinado de VSL = `mechanism_belief_score`, `proof_score` e
  `objection_handling_score`.
- Amostra cega S09 VSL preparada com 4 pares variados em
  `data/exports/output_s09_vsl_blind_sample_2026-07-08.csv`; chave separada em
  `data/exports/output_s09_vsl_blind_key_2026-07-08.json`.
- Sem veredito S09 nesta execucao; julgamento permanece externo.

Apuracao S09 2026-07-08:

- Relatorio: `docs/msf-s09-vsl-gate-result-2026-07-08.md`.
- Julgamento externo em
  `data/exports/output_s09_vsl_blind_sample_2026-07-08_judged.csv`.
- Chave aberta somente depois do julgamento cego:
  `data/exports/output_s09_vsl_blind_key_2026-07-08.json`.
- Resultado por par: com skill 4, sem skill 0, empates 0.
- Resultado por criterio: com skill 26, sem skill 0, empates 6.
- Nucleo comercial combinado (`mechanism_belief_score`, `proof_score`,
  `objection_handling_score`): com skill 10 celulas, sem skill 0, empates 2;
  com skill venceu o nucleo nos 4 pares.
- Veredito final: `PASS`. O S09 VSL teve PASS comercial (com skill venceu 4/4
  pares, 26 criterios contra 0, 6 empates; nucleo comercial 10-0-2).
- O `CONCERNS` inicial foi resolvido: auditoria externa reconfirmou que a copia
  corrigida altera um unico caractere (`cansa?o` -> `cansaco`) sem reescrita de
  copy, preservando o julgamento cego. A raiz foi corrigida com
  `transliterate_ascii` NFKD em `scripts/msf_common.py` e guard
  `orphan_question_mark` em `scripts/audit_insights_v2_text.py`.
- Skill `msf-process-copy-vsl` aprovada; MSF-S05 liberado como proxima skill
  real. MSF-S06/MSF-S07 seguem blocked ate S05 passar pelo proprio S09.

### MSF-S04 - Skill: construcao de oferta

Prioridade: `P1`
Tipo: `skill`
Status: `done`

Escopo: skill `msf-process-construcao-oferta` (promessa, stack, bonus,
garantia, nome; absorve precificacao como capitulo do playbook).

Aceite: Definition of Done da secao 2.

Dependencias: MSF-S01, MSF-S02, MSF-S08.

Liberacao 2026-07-07:

- MSF-S08 aprovado em auditoria externa; S04 e a primeira skill real da leva.
- Deve importar `transversal:mecanismo-big-idea` e
  `transversal:prova-depoimentos` por referencia quando aplicavel.
- Deve deduplicar contagem de evidencia por `insight_id` ao importar ambos os
  modulos, especialmente `zoChfFHnlOQ-v2-0008` e `mCaFyZpXJdE-v2-0011`.
- Logica especifica de oferta, preco, stack, bonus, garantia e CTA fica na
  skill S04; os modulos transversais ficam no nivel de principio.

Execucao 2026-07-08:

- Criada `skills/msf-process-construcao-oferta/` via
  `scripts/create_process_skill.py`.
- Preenchidos os 8 arquivos da anatomia: `SKILL.md`,
  `skill.contract.json`, `retrieval.md`, `rubric.md`,
  `templates/output-template.md`, `examples/briefing.md`,
  `examples/output-approved.md` e `agents/openai.yaml`.
- Retrieval usa `curated_insights` com `process-construcao-oferta`,
  `process-mecanismo-big-idea` e `process-prova-depoimentos`.
- `module_inheritance_policy` aplicada: dedupe por `insight_id` entre modulos
  e logica especifica de oferta mantida na skill.
- Amostra cega S09 preparada com 3 pares variados em
  `data/exports/output_s09_blind_sample_2026-07-08.csv`; chave separada em
  `data/exports/output_s09_blind_key_2026-07-08.json`.
- Sem veredito S09 nesta execucao; julgamento permanece externo.

Apuracao S09 2026-07-08:

- Relatorio: `docs/msf-s09-offer-gate-result-2026-07-08.md`.
- Chave aberta somente depois do julgamento cego:
  `data/exports/output_s09_blind_key_2026-07-08.json`.
- Julgamento externo em
  `data/exports/output_s09_blind_sample_2026-07-08_judged.csv`.
- Resultado por par: com skill 3, sem skill 0, empates 0.
- Resultado por criterio: com skill 24, sem skill 0, empates 0.
- Criterio comercial combinado (`mechanism_belief_bridge`,
  `pricing_anchoring`, `proof_claim_control`): com skill 3, sem skill 0,
  empates 0.
- Auditoria externa independente confirmou o PASS, a resolucao das 12 citacoes
  para curated real com tag `process-construcao-oferta`, No Invention e a
  politica de dedupe dos ids de overlap.
- Veredito: PASS. `msf-process-construcao-oferta` aprovado.

### MSF-S05 - Skill: copy para anuncios

Prioridade: `P1`
Tipo: `skill`
Status: `done`

Escopo: skill `msf-process-copy-anuncios` (hooks, angulos, scripts; absorve
headlines-hooks e teste-variacao-criativos como capitulos).

Aceite: Definition of Done da secao 2.

Dependencias: MSF-S01, MSF-S02, MSF-S03 aprovado por S09 VSL.

Execucao 2026-07-08:

- Criada `skills/msf-process-copy-anuncios/` via
  `scripts/create_process_skill.py`.
- Preenchidos os 8 arquivos da anatomia: `SKILL.md`,
  `skill.contract.json`, `retrieval.md`, `rubric.md`,
  `templates/output-template.md`, `examples/briefing.md`,
  `examples/output-approved.md` e `agents/openai.yaml`.
- Retrieval usa `curated_insights` com `process-copy-anuncios`,
  `process-mecanismo-big-idea` e `process-prova-depoimentos`.
- `module_inheritance_policy` aplicada: dedupe por `insight_id` entre modulos
  e logica especifica de anuncio mantida na skill.
- Rubrica alinhada a `docs/output-evaluation-rubric.md`; criterio comercial
  combinado de anuncios = `hook_strength_score`,
  `proof_or_plausibility_score` e `testability_score`.
- Amostra cega S09 Ads preparada com 4 pares variados em
  `data/exports/output_s09_ads_blind_sample_2026-07-08.csv`; chave separada em
  `data/exports/output_s09_ads_blind_key_2026-07-08.json`.
- Briefings cobrem Meta feed imagem, Reels/short video, Google Search e Google
  Display retargeting, com baselines honestos.
- Guard `orphan_question_mark` nos 4 outputs com skill passou com 0 achados; os
  outputs com skill preservam acentuacao pt-BR.
- Sem veredito S09 nesta execucao; julgamento permanece externo.

Apuracao S09 2026-07-08:

- Relatorio: `docs/msf-s09-ads-gate-result-2026-07-08.md`.
- Julgamento externo em
  `data/exports/output_s09_ads_blind_sample_2026-07-08_judged.csv`.
- Chave aberta somente depois do julgamento cego:
  `data/exports/output_s09_ads_blind_key_2026-07-08.json`.
- Resultado por par: com skill 4, sem skill 0, empates 0.
- Resultado por criterio: com skill 30, sem skill 0, empates 2.
- Nucleo comercial combinado (`hook_strength_score`,
  `proof_or_plausibility_score`, `testability_score`): com skill 12 celulas,
  sem skill 0, empates 0; com skill venceu o nucleo nos 4 pares.
- Guard `orphan_question_mark` nos outputs com skill passou com 0 achados; os
  non-ASCII encontrados sao acentos normais de output final pt-BR, nao defeito
  de encoding.
- Veredito final: `PASS`. Skill `msf-process-copy-anuncios` aprovada.
- MSF-S06 liberado como proxima skill real; naquele momento, MSF-S07 seguia
  blocked ate S06 passar pelo proprio S09.

### MSF-S06 - Skill: criacao de produto low ticket

Prioridade: `P1`
Tipo: `skill`
Status: `done`

Escopo: skill `msf-process-produto-low-ticket` (transformacao de entrada,
formato, esteira front-end -> backend).

Aceite: Definition of Done da secao 2.

Dependencias: MSF-S01, MSF-S02, MSF-S05 aprovado por S09 Ads.

Execucao 2026-07-08:

- Criada `skills/msf-process-produto-low-ticket/` via
  `scripts/create_process_skill.py`.
- Preenchidos os 8 arquivos da anatomia: `SKILL.md`,
  `skill.contract.json`, `retrieval.md`, `rubric.md`,
  `templates/output-template.md`, `examples/briefing.md`,
  `examples/output-approved.md` e `agents/openai.yaml`.
- Retrieval usa `curated_insights` com `process-produto-low-ticket`,
  `process-mecanismo-big-idea` e `process-prova-depoimentos`.
- `module_inheritance_policy` aplicada: dedupe por `insight_id` entre modulos
  e logica especifica de produto low ticket mantida na skill.
- Rubrica definida com 8 criterios: `entry_transformation_clarity_score`,
  `avatar_promise_fit_score`, `scope_consumability_score`,
  `price_value_coherence_score`, `mechanism_belief_score`,
  `proof_claim_control_score`, `backend_ascension_bridge_score` e
  `base_usage_score`.
- Criterio comercial combinado de low ticket =
  `entry_transformation_clarity_score`, `price_value_coherence_score` e
  `backend_ascension_bridge_score`.
- Amostra cega S09 Low Ticket preparada com 4 pares variados em
  `data/exports/output_s09_lowticket_blind_sample_2026-07-08.csv`; chave
  separada em
  `data/exports/output_s09_lowticket_blind_key_2026-07-08.json`.
- Briefings cobrem desafio pago, ebook/mini-curso, template/kit e workshop
  gravado, com baselines honestos.
- Guard `orphan_question_mark` nos 4 outputs com skill passou com 0 achados; os
  outputs com skill preservam acentuacao pt-BR.
- Sem veredito S09 nesta execucao; julgamento permanece externo.

Apuracao S09 2026-07-08:

- Relatorio: `docs/msf-s09-lowticket-gate-result-2026-07-08.md`.
- Julgamento externo em
  `data/exports/output_s09_lowticket_blind_sample_2026-07-08_judged.csv`.
- Chave aberta somente depois do julgamento cego:
  `data/exports/output_s09_lowticket_blind_key_2026-07-08.json`.
- Resultado por par: com skill 4, sem skill 0, empates 0.
- Resultado por criterio: com skill 31, sem skill 0, empates 1.
- Nucleo comercial combinado (`entry_transformation_clarity_score`,
  `price_value_coherence_score`, `backend_ascension_bridge_score`): com skill
  12 celulas, sem skill 0, empates 0; com skill venceu o nucleo nos 4 pares.
- Guard `orphan_question_mark` nos outputs com skill passou com 0 achados; os
  non-ASCII encontrados sao acentos normais de output final pt-BR, nao defeito
  de encoding.
- No Invention da chave passou: 13 citacoes unicas resolvem para
  `curated_insights` real e carregam `process-produto-low-ticket`.
- Veredito final: `PASS`. Skill `msf-process-produto-low-ticket` aprovada.
- MSF-S07 liberado como ultima skill real da primeira leva.

### MSF-S07 - Skill: criacao de quiz

Prioridade: `P1`
Tipo: `skill`
Status: `done`

Escopo: skill `msf-process-quiz` (perguntas, diagnostico, ponte para oferta,
fechamento de loops abertos).

Aceite: Definition of Done da secao 2.

Dependencias: MSF-S01, MSF-S02, MSF-S06 aprovado por S09 Low Ticket.

Execucao 2026-07-08:

- Criada `skills/msf-process-quiz/` via `scripts/create_process_skill.py`.
- Preenchidos os 8 arquivos da anatomia: `SKILL.md`,
  `skill.contract.json`, `retrieval.md`, `rubric.md`,
  `templates/output-template.md`, `examples/briefing.md`,
  `examples/output-approved.md` e `agents/openai.yaml`.
- Retrieval usa `curated_insights` com `process-quiz`,
  `process-mecanismo-big-idea` e `process-prova-depoimentos`.
- `module_inheritance_policy` aplicada: dedupe por `insight_id` entre modulos
  e logica especifica de quiz mantida na skill.
- Rubrica definida com 8 criterios: `question_diagnostic_coherence_score`,
  `avatar_recognition_score`, `result_personalization_score`,
  `mechanism_belief_score`, `proof_claim_control_score`,
  `offer_bridge_coherence_score`, `completion_design_score` e
  `base_usage_score`.
- Criterio comercial combinado de quiz =
  `question_diagnostic_coherence_score`, `result_personalization_score` e
  `offer_bridge_coherence_score`.
- Amostra cega S09 Quiz preparada com 4 pares variados em
  `data/exports/output_s09_quiz_blind_sample_2026-07-08.csv`; chave separada em
  `data/exports/output_s09_quiz_blind_key_2026-07-08.json`.
- Briefings cobrem diagnostico de problema, segmentacao de avatar,
  prontidao/readiness e match de produto, com baselines honestos.
- Guard inicial `orphan_question_mark` nos 4 outputs com skill passou com 0
  achados; a apuracao S09 posterior endureceu o detector e encontrou o
  artefato `obje??o` no output com skill do par 002.
- No Invention do playbook passou: 17 citacoes unicas resolvem para
  `curated_insights` real e carregam `process-quiz`.
- No Invention da chave S09 passou: 18 citacoes unicas dos outputs com skill
  resolvem para `curated_insights` real e carregam `process-quiz`.
- Sem veredito S09 nesta execucao; julgamento permanece externo.
- Status movido para `ready_for_owner_audit`; `blind_baseline_test` segue
  `pending` ate o julgamento cego.

Apuracao S09 Quiz 2026-07-08:

- Julgamento cego travado em
  `data/exports/output_s09_quiz_blind_sample_2026-07-08_judged.csv`.
- Chave aberta apos julgamento: pares 001/003 usam A=com skill e 002/004 usam
  B=com skill.
- Resultado comercial: com skill venceu 4/4 pares, 32/32 criterios e 12/12
  celulas do nucleo comercial; sem skill venceu 0 e houve 0 empates.
- No Invention da chave passou: 30 usos de citacao, 18 `insight_id` unicos,
  todos resolvem para `curated_insights` real e carregam `process-quiz`.
- Guard endurecido em `scripts/msf_common.py` pega `obje??o` e `Prot?tipo` sem
  reprovar `?` legitimo de fim de pergunta; regressao adicionada em
  `tests/test_msf_common_encoding.py`.
- `S09-QUIZ-002`, output B/com skill, continha `obje??o`. Rastreamento apontou
  corrupcao a montante em dados locais ignorados (`curated_insights` /
  `data/processed`) que a skill herdou pela strategy pack path.
- Copia corrigida para reconfirmacao:
  `data/exports/output_s09_quiz_blind_sample_2026-07-08_encoding_fixed.csv`.
  Diff localizado: `obje??o` -> `objecao` no output com skill do par 002 e
  `Prot?tipo` -> `Prototipo` no baseline do par 003; sem reescrita de copy.
- Scan final da copia corrigida: 0 mojibake nos 4 outputs com skill e 0 nos 8
  outputs totais.
- Veredito documentado em
  `docs/msf-s09-quiz-gate-result-2026-07-08.md`: PASS comercial, mas
  `CONCERNS` ate reconfirmacao externa. MSF-S07 continua
  `ready_for_owner_audit`, skill nao aprovada, `blind_baseline_test` pendente.

Reconfirmacao externa 2026-07-08:

- Auditoria externa independente reconfirmou o PASS de S07: com skill venceu
  4/4 pares, 32/32 criterios e 12/12 celulas comerciais.
- O `CONCERNS` de encoding foi resolvido por correcao de encoding na raiz,
  guard endurecido e reconfirmacao externa da copia corrigida.
- A copia corrigida altera apenas dois tokens mojibake:
  `obje??o` -> `objecao` no output com skill do par 002 e
  `Prot?tipo` -> `Prototipo` no baseline do par 003; nenhuma copy foi
  reescrita.
- Guard endurecido pega os dois artefatos, ignora `?` legitimo de fim de
  pergunta e encontra 0 mojibake na copia corrigida.
- No Invention reconfirmado: 18/18 citacoes unicas resolvem para
  `curated_insights` real e carregam `process-quiz`.
- `blind_baseline_test` marcado como `pass`; skill `msf-process-quiz`
  aprovada; MSF-S07 fechado como `done`.

### MSF-S08 - Modulos transversais de copy

Prioridade: `P1`
Tipo: `skill`
Status: `done`

Escopo:

- `mecanismo-big-idea` e `prova-depoimentos` nao viram skills isoladas;
  viram modulos de retrieval compartilhados que as skills S03-S07 importam.

Aceite:

- Modulos consumidos por pelo menos duas skills da primeira leva sem
  duplicar conteudo de playbook.

Dependencias: MSF-S02.

Execucao 2026-07-07:

- Criado o conjunto compartilhado em `skills/_modules/msf-transversal-copy/`;
  os modulos nao sao skills isoladas.
- Criados `transversal:mecanismo-big-idea` e
  `transversal:prova-depoimentos`, cada um ligado ao `process_tag`
  correspondente e declarado como consumivel por S03-S07.
- Criado `schemas/msf_transversal_module_contract.schema.json`.
- Criado `scripts/validate_transversal_modules.py` para validar contrato,
  arquivos obrigatorios, tags ativas, citacoes, placeholders, ASCII interno e
  consumo por pelo menos duas skills.
- Criado `docs/msf-s08-transversal-modules-review-2026-07-07.md` como pacote
  de auditoria do owner.
- Auditoria externa aprovada em 2026-07-07: 17 citacoes resolvem para
  `curated_insights` real, carregam a tag declarada, No Invention passa e as
  fronteiras de mecanismo/prova estao corretas.
- Contrato/template de skill atualizado com restricoes herdadas: deduplicar
  contagem de evidencia por `insight_id` entre modulos e manter logica
  processo-especifica dentro da skill.

### MSF-S09 - Validacao cega por skill

Prioridade: `P1`
Tipo: `qa`
Status: `done`

Escopo:

- Para cada skill da primeira leva: gerar output com e sem a skill (mesmo
  briefing, mesmo modelo), avaliar as cegas com o avaliador do MSF-R09 e a
  rubrica da skill. Juiz externo ao gerador.

Aceite:

- Cada skill aprovada individualmente; reprovadas voltam para iteracao de
  playbook/retrieval antes de uso.

Dependencias: MSF-R09, MSF-S03..S08.

Execucao parcial 2026-07-08:

- S09 preparado apenas para MSF-S04, com CSV cego sem vazamento de origem e
  campos da rubrica de oferta em branco para juiz externo.
- S04 aprovado: com skill venceu 3/3 pares, 24/24 criterios e 3/3 criterios
  comerciais combinados.
- Auditoria externa independente confirmou o PASS de S04, citacoes validas e
  dedupe respeitado.
- S03 foi liberado como proxima skill real depois de S04.
- Depois do PASS de S03, S05 foi liberado; S06/S07 continuam blocked ate S05
  passar pelo proprio S09.
- Para S03 em diante, variar mais os briefings (N > 3 quando viavel) e, se
  possivel, alternar quem redige o baseline sem-skill.
- S09 VSL para S03 preparado com 4 pares, CSV cego sem vazamento de origem e
  campos da rubrica de VSL em branco para juiz externo.
- S09 VSL aprovado como `PASS`: com skill venceu 4/4 pares, 26/32 criterios e
  10/12 celulas comerciais, com 6 empates e 0 perdas.
- O `CONCERNS` de encoding foi resolvido por correcao de raiz
  (`transliterate_ascii` NFKD + guard `orphan_question_mark`) e reconfirmacao
  externa da copia corrigida, que mudou apenas `cansa?o` para `cansaco`.
- S03 esta done/approved; S05 e a proxima skill real. S06/S07 seguem blocked ate
  S05 passar pelo proprio S09.
- S09 Ads para S05 preparado com 4 pares, CSV cego sem vazamento de origem e
  campos da rubrica de anuncios em branco para juiz externo.
- S09 Ads aprovado como `PASS`: com skill venceu 4/4 pares, 30/32 criterios e
  12/12 celulas comerciais, com 2 empates e 0 perdas.
- S05 esta done/approved; S06 virou a proxima skill real; naquele momento, S07
  seguia blocked ate S06 passar pelo proprio S09.
- S09 Low Ticket para S06 preparado com 4 pares, CSV cego sem vazamento de
  origem e campos da rubrica de low ticket em branco para juiz externo.
- S09 Low Ticket aprovado como `PASS`: com skill venceu 4/4 pares, 31/32
  criterios e 12/12 celulas comerciais, com 1 empate e 0 perdas.
- S06 esta done/approved; S07 e a ultima skill real da primeira leva.
- S09 Quiz para S07 preparado com 4 pares, CSV cego sem vazamento de origem e
  campos da rubrica de quiz em branco para juiz externo.
- S09 Quiz apurado como PASS comercial: com skill venceu 4/4 pares, 32/32
  criterios e 12/12 celulas comerciais, com 0 empates e 0 perdas.
- O guard de encoding foi endurecido para pegar `obje??o` e `Prot?tipo`; a
  copia `_encoding_fixed.csv` tem 0 mojibake nos outputs com skill.
- S07 aprovado apos reconfirmacao externa: `CONCERNS` resolvido, skill
  `msf-process-quiz` approved, `blind_baseline_test` passou.
- Primeira leva fechada: S04 oferta, S03 VSL, S05 anuncios, S06 low ticket e
  S07 quiz estao todas done/approved.

### MSF-S10 - Agentes consumidores de skills

Prioridade: `P2`
Tipo: `agent`
Status: `ready_for_planning`

Escopo:

- Agentes especializados (copywriter de VSL, copywriter de anuncios,
  estrategista de oferta) que orquestram skills validadas. Somente apos S09.
- Gestao de trafego (Meta/Google) fica para quando houver skill de trafego
  (segunda leva) e ferramentas operacionais (MCP das plataformas).

Aceite:

- Agente produz output final usando skill + retrieval sem intervencao manual
  no meio, e o output passa na rubrica.

Dependencias: MSF-S09.

Nota de sequenciamento 2026-07-08:

- As 5 skills da primeira leva estao validadas individualmente e podem ser
  consumidas pela camada de agentes quando o owner iniciar esse marco.
- Nao iniciar agentes ainda; antes do MSF-R14/backfill, reabrir MSF-R03 para
  tratar dados fora do OneDrive conforme a ordem executiva.

### MSF-S11 - Loop de retroalimentacao continua

Prioridade: `P2`
Tipo: `loop`
Status: `blocked`

Escopo:

- Formalizar o delta: novo episodio/asset -> pipeline v2 -> auditoria ->
  classificacao de process_tags -> curadoria delta -> refresh de packs e
  playbooks afetados (somente skills cujas tags receberam insights novos).
- Versionar playbooks para que refresh nao destrua ajustes manuais.

Aceite:

- Um episodio novo processado dispara atualizacao rastreavel apenas nas
  skills afetadas, com log do delta.

Dependencias: MSF-S03..S07, MSF-R14.

### MSF-S12 - Segunda leva de skills

Prioridade: `P2`
Tipo: `skill`
Status: `blocked`

Escopo:

- trafego-meta, trafego-google-youtube, video-anuncio, imagem-anuncio,
  copy-carta-vendas, copy-email, seo - conforme densidade pos-backfill e
  pos-assets da academy atingir massa critica (sugestao: 20+ insights
  curados por processo).

Aceite:

- Mesma anatomia e Definition of Done da primeira leva.

Dependencias: MSF-R14, MSF-R15, MSF-S09.

### MSF-S13 - Anotacoes de outcome de campo

Prioridade: `P3`
Tipo: `data`
Status: `blocked`

Escopo:

- Registrar resultados reais (copy que converteu, criativo vencedor, quiz
  com melhor completude) como evidencia de peso maior ligada aos insights
  usados, no schema reservado pelo MSF-R16.
- Outcome de campo passa a influenciar ranking de retrieval das skills.

Aceite:

- Pelo menos um ciclo real: output publicado -> resultado registrado ->
  ranking ajustado.

Dependencias: MSF-R16, MSF-S10.

## 5. Ordem executiva

1. Gates R2 e R3 estao aprovados; MSF-S01 + MSF-S02 (fundacao) estao done.
2. Primeira leva fechada: MSF-S04, MSF-S03, MSF-S05, MSF-S06 e MSF-S07 estao
   aprovados por S09 e suas skills estao approved.
3. Proximo marco ready para planejamento: reabrir MSF-R03 (dados fora do
   OneDrive) antes de MSF-R14/backfill dos chunks restantes.
4. Marco seguinte ready para planejamento: camada de agentes consumidores das
   5 skills validadas. Nao iniciar ate o owner mandar o proximo passo.
5. MSF-S10 cria agentes; MSF-S11 liga a
   retroalimentacao.
6. Segunda leva (S12) quando o backfill e os assets da academy elevarem a
   densidade dos processos adiados.
