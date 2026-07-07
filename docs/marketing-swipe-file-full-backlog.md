# Backlog Mestre - Marketing Swipe File

## 1. Objetivo deste backlog

Este backlog organiza a execucao completa do Marketing Swipe File, do MVP local em Codex ate Supabase, MCP, agentes especializados, automacao, UI e inteligencia composta.

Este documento complementa:

- `docs/marketing-swipe-file-prd.md`
- `docs/marketing-swipe-file-architecture.md`
- `docs/marketing-swipe-file-mvp-backlog.md`

Regra de execucao: nao criar agentes autonomos antes de validar scripts, prompts, skills e loops em exemplos reais. O sistema deve evoluir por evidencia, nao por imaginacao de arquitetura.

## 2. Convencoes

### Prioridades

- `P0`: necessario para o MVP ou para evitar retrabalho estrutural.
- `P1`: necessario para a primeira versao completa.
- `P2`: melhora relevante apos prova de valor.
- `P3`: expansao, escala ou refinamento.

### Status

- `not_started`
- `in_progress`
- `blocked`
- `done`
- `deferred`

### Tipos

- `product`
- `data`
- `script`
- `prompt`
- `skill`
- `loop`
- `agent`
- `database`
- `mcp`
- `ui`
- `qa`
- `ops`

### Definition of Done geral

- Entregavel criado no repositorio ou ambiente definido.
- Entrada, saida e erros documentados.
- Criterios de aceite atendidos.
- Validado em pelo menos um exemplo real ou fixture representativa.
- Sem chaves sensiveis commitadas.
- Se gerar insight, manter evidencia rastreavel.
- Se tocar Supabase, validar schema, RLS quando aplicavel e pelo menos uma query real.

## 3. Roadmap executivo

### Release 0 - Fundacao operacional

Objetivo: deixar o projeto pronto para executar sem depender da conversa.

Saida esperada:

- Estrutura de pastas.
- Contratos JSON.
- Taxonomia seed.
- Prompts iniciais.
- Procedimento de ingestao manual.

Gate de saida:

- Codex consegue processar 1 episodio piloto com artefatos intermediarios consistentes.

### Release 1 - MVP local Codex-first

Objetivo: processar 20 episodios VTurb, detectar materiais complementares e gerar outputs melhores usando a base.

Saida esperada:

- 20 episodios processados.
- Pelo menos 500 insights atomicos.
- Fila de materiais complementares.
- Busca local por filtros.
- VSL com 3 leads e anuncios usando referencias.

Gate de saida:

- Output com base e avaliado como igual ou melhor que output sem base.

### Release 2 - Skills e loops Codex

Objetivo: transformar processos repetiveis em skills e loops validados.

Saida esperada:

- Skills atomicas.
- Loops de episodio, asset, extraction, retrieval e output.
- Logs e criterios de qualidade.

Gate de saida:

- Um novo episodio consegue ser processado por loop com pouca reexplicacao.

### Release 3 - Supabase como fonte de verdade

Objetivo: migrar de arquivos locais para banco estruturado, mantendo importacao idempotente e rastreabilidade.

Saida esperada:

- Projeto Supabase.
- Schema versionado.
- Importadores.
- Busca SQL/full-text.
- Politicas de seguranca definidas antes de expor API.

Gate de saida:

- Queries retornam insights, evidencias, episodios e assets sem ler arquivos locais.

### Release 4 - MCP para agentes

Objetivo: expor o Marketing Swipe File como ferramenta padronizada para agentes.

Saida esperada:

- MCP server.
- Ferramentas de busca e strategy packs.
- Registro de uso de insights.
- Testes com agentes consumidores.

Gate de saida:

- Agente de VSL e agente de anuncios usam MCP para recuperar contexto e criar output com referencias.

### Release 5 - Agentes especializados

Objetivo: criar agentes produtores, consumidores e avaliadores usando skills, loops e MCP.

Saida esperada:

- Producer agents.
- Consumer agents.
- Evaluator agents.
- Protocolos de briefing, output e avaliacao.

Gate de saida:

- Agentes conseguem operar em fluxo completo com intervencao humana apenas em aprovacoes e materiais manuais.

### Release 6 - Automacao, UI e escala

Objetivo: monitorar canais, processar lotes, permitir consulta humana visual e escalar fontes.

Saida esperada:

- Monitoramento VTurb, KiwiCast e Hotmart Cast.
- UI de busca e revisao.
- Grafo de conceitos.
- Painel de qualidade.

Gate de saida:

- Usuario consegue consultar, revisar, aprovar e acionar agentes via interface.

### Release 7 - Inteligencia composta

Objetivo: transformar insights atomicos em playbooks, padroes, estrategias compostas e memoria de mercado.

Saida esperada:

- Grafo de estrategia.
- Playbooks por nicho/ativo/funil.
- Deteccao de padroes e contradicoes.
- Sistema de feedback de performance.

Gate de saida:

- Base sugere estrategias compostas e explica quais evidencias sustentam cada recomendacao.

## 4. Backlog por epicos

## EPIC A - Fundacao do projeto

### MSF-A01 - Criar estrutura base do repositorio

Prioridade: `P0`
Tipo: `ops`
Status: `done`

Escopo:

- Criar diretorios `data/`, `prompts/`, `scripts/`, `skills/`, `loops/`, `docs/`, `tests/`.
- Criar `.gitignore` para dados brutos, arquivos grandes, credenciais e exports sensiveis.
- Criar README operacional do projeto.

Aceite:

- Estrutura existe.
- README explica fluxo local.
- Dados sensiveis e arquivos brutos nao entram por acidente no Git.

Dependencias:

- Nenhuma.

### MSF-A02 - Definir contratos JSON locais

Prioridade: `P0`
Tipo: `data`
Status: `done`

Escopo:

- Definir schemas para `metadata.json`, `transcript_original.json`, `content_segments.json`, `referenced_assets.json`, `acquisition_tasks.json`, `insights.json`, `episode_summary.md` e `asset_summary.md`.
- Documentar campos obrigatorios e opcionais.
- Incluir exemplos minimos.

Aceite:

- Cada contrato tem exemplo valido.
- Todos os scripts futuros podem validar contra esses contratos.
- Contratos contemplam episodio, asset, evidencia e idioma.

Dependencias:

- MSF-A01.

### MSF-A03 - Criar taxonomia seed

Prioridade: `P0`
Tipo: `data`
Status: `done`

Escopo:

- Criar `data/processed/taxonomy_seed.json`.
- Incluir temas, subtemas, tipos de fonte, asset types, agent roles, funnel stages e insight types.
- Incluir politica de expansao: quando criar novo termo, quando reutilizar existente.

Aceite:

- Taxonomia cobre VSL, anuncios, oferta, copy, funil, quiz, gestao, produto e materials complementares.
- Taxonomia e versionada.
- Existe campo para sinonimos.

Dependencias:

- MSF-A02.

### MSF-A04 - Criar fixtures de teste

Prioridade: `P0`
Tipo: `qa`
Status: `done`

Escopo:

- Criar fixtures pequenas simulando transcricao, descricao com PDF citado, planilha simples, PDF de exemplo e insight extraido.
- Usar conteudo ficticio ou publico simples para nao depender de dados reais no teste.

Aceite:

- Scripts e prompts conseguem ser testados sem baixar episodio real.
- Fixtures cobrem pelo menos transcricao, material complementar e insight.

Dependencias:

- MSF-A02.

## EPIC B - Ingestao YouTube e transcricao

### MSF-B01 - Criar lista inicial de episodios VTurb

Prioridade: `P0`
Tipo: `data`
Status: `done`

Escopo:

- Criar `data/input/youtube_urls.csv`.
- Preencher os primeiros episodios piloto do VTurb.
- Incluir prioridade e notas.

Aceite:

- Pelo menos 5 episodios piloto.
- Campos seguem contrato.
- Ordem de processamento clara.
- 5 episodios piloto reais foram adicionados em `data/input/youtube_urls.csv`.

Dependencias:

- MSF-A01.

### MSF-B02 - Implementar extracao de video_id e metadados

Prioridade: `P0`
Tipo: `script`
Status: `done`

Escopo:

- Criar script para receber URL e gerar `data/raw/youtube/{video_id}/metadata.json`.
- Capturar video_id, canal, titulo, descricao, duracao, data de publicacao quando disponivel e data de coleta.
- Evitar duplicacao.

Aceite:

- Roda com uma URL do VTurb.
- Gera metadata valido.
- Reexecucao nao duplica.

Dependencias:

- MSF-A02, MSF-B01.

### MSF-B03 - Implementar coleta de transcricao automatica

Prioridade: `P0`
Tipo: `script`
Status: `done`

Escopo:

- Coletar transcricao automatica do YouTube quando disponivel.
- Usar fallback por snapshot Playwright quando o endpoint direto falhar mas a UI mostrar transcricao.
- Preservar timestamps, idioma e texto original.
- Marcar `transcript_missing` quando nao houver transcricao.

Aceite:

- Gera `transcript_original.json`.
- Preserva timestamps.
- Extrai transcricao via UI para videos em que `timedtext` falha.
- Falhas sao registradas sem quebrar todo o pipeline.

Dependencias:

- MSF-B02.

### MSF-B04 - Normalizar transcricao em segmentos

Prioridade: `P0`
Tipo: `script`
Status: `done`

Escopo:

- Transformar transcricao em `content_segments.json`.
- Definir tamanho de segmento adequado para extracao por agente.
- Manter start/end seconds.

Aceite:

- Segmentos ficam em ordem.
- Segmentos mantem evidencia suficiente para auditoria.
- Segmentos longos sao divididos sem perder contexto.

Dependencias:

- MSF-B03.

### MSF-B05 - Criar logs de ingestao

Prioridade: `P1`
Tipo: `ops`
Status: `done`

Escopo:

- Registrar inicio, fim, status, erros e contagens por episodio.
- Criar resumo por lote.

Aceite:

- Cada processamento gera log em `data/logs/`.
- Logs ajudam a retomar falhas.
- `scripts/run_episode_pipeline.py` gera arquivos `.jsonl` por execucao.

Dependencias:

- MSF-B02, MSF-B03, MSF-B04.

## EPIC C - Deteccao e aquisicao de materiais complementares

### MSF-C01 - Criar prompt de deteccao de materiais

Prioridade: `P0`
Tipo: `prompt`
Status: `done`

Escopo:

- Criar prompt para analisar descricao e segmentos de transcricao.
- Detectar PDFs, docs, planilhas, slides, templates, prompts, swipes, areas de membros, direct e comentarios com keyword.
- Exigir evidencia por trecho/timestamp.

Aceite:

- Prompt nao inventa material sem evidencia.
- Prompt gera JSON valido.
- Prompt diferencia material publico, manual e indisponivel.

Dependencias:

- MSF-A02, MSF-B04.

### MSF-C02 - Implementar detector local de materiais

Prioridade: `P0`
Tipo: `script`
Status: `done`

Escopo:

- Gerar `referenced_assets.json`.
- Gerar `acquisition_tasks.json`.
- Gerar `manual_actions.md`.
- Usar heuristicas simples + prompt quando necessario.

Aceite:

- Detecta exemplos de direct, comentario e link na descricao.
- Cria tarefa manual objetiva.
- Cada tarefa tem status e prioridade.

Dependencias:

- MSF-C01.

### MSF-C03 - Criar procedimento de insercao de assets pelo usuario

Prioridade: `P0`
Tipo: `ops`
Status: `done`

Escopo:

- Definir pasta `data/input/assets/{video_id}/`.
- Definir convencao de nomes.
- Definir como vincular arquivo a `acquisition_task`.
- Documentar procedimento para direct, comentario, area de membros e download publico.

Aceite:

- Usuario sabe onde colocar arquivos.
- O sistema consegue associar arquivo ao episodio/material detectado.

Dependencias:

- MSF-C02.

### MSF-C04 - Consolidar fila geral de materiais pendentes

Prioridade: `P1`
Tipo: `script`
Status: `done`

Escopo:

- Unificar todas as tarefas em `data/exports/acquisition_tasks_master.csv`.
- Ordenar por prioridade, fonte e potencial de valor.

Aceite:

- Lista mostra exatamente o que precisa ser obtido.
- Tarefas possuem link para episodio, timestamp e instrucao.
- `data/exports/acquisition_tasks_master.csv` consolida a fila atual.

Dependencias:

- MSF-C02.

### MSF-C05 - Criar regras de valor esperado para materiais

Prioridade: `P1`
Tipo: `product`
Status: `done`

Escopo:

- Classificar material esperado por potencial: copy completa, framework, template, planilha, checklist, exemplo, slide.
- Definir prioridade com base em potencial e facilidade de obtencao.

Aceite:

- Fila consegue priorizar materiais mais ricos.
- Materiais com "copy completa" ou "template" sobem na fila.
- Existem heuristicas iniciais de valor esperado; ainda falta calibrar com mais materiais reais.

Dependencias:

- MSF-C04.

## EPIC D - Processamento de arquivos complementares

### MSF-D01 - Implementar registro de asset obtido

Prioridade: `P0`
Tipo: `script`
Status: `done`

Escopo:

- Ler arquivos em `data/input/assets/{video_id}/`.
- Calcular checksum.
- Criar `data/raw/assets/{asset_id}/metadata.json`.
- Copiar/preservar original em `data/raw/assets/{asset_id}/original_file`.

Aceite:

- Arquivo e preservado.
- Checksum evita duplicacao.
- Asset fica vinculado a episodio e tarefa quando possivel.

Dependencias:

- MSF-C03.

### MSF-D02 - Processar PDFs

Prioridade: `P0`
Tipo: `script`
Status: `done`

Escopo:

- Extrair texto por pagina.
- Preservar numero de pagina.
- Marcar baixa confianca quando extracao falhar ou parecer OCR ruim.

Aceite:

- Gera `content_segments.json` com page_number.
- Segmentos mantem texto suficiente para evidencia.

Dependencias:

- MSF-D01.

### MSF-D03 - Processar DOCX e textos

Prioridade: `P0`
Tipo: `script`
Status: `done`

Escopo:

- Extrair paragrafos, headings e tabelas simples de DOCX.
- Processar TXT/Markdown/HTML salvo.

Aceite:

- Preserva estrutura basica.
- Gera segmentos com section_title quando possivel.

Dependencias:

- MSF-D01.

### MSF-D04 - Processar planilhas

Prioridade: `P1`
Tipo: `script`
Status: `done`

Escopo:

- Extrair abas, headers, ranges e tabelas relevantes.
- Detectar modelos, calculadoras, tabelas de oferta, funil e criativos.

Aceite:

- Gera segmentos por aba/range.
- Evidencia aponta para sheet_name e cell_range.

Dependencias:

- MSF-D01.

### MSF-D05 - Processar slides

Prioridade: `P1`
Tipo: `script`
Status: `done`

Escopo:

- Extrair texto por slide.
- Preservar slide_number.
- Detectar estruturas de aula, pitch, funil ou framework.

Aceite:

- Gera segmentos por slide.
- Evidencia aponta para slide_number.

Dependencias:

- MSF-D01.

### MSF-D06 - Processar imagens com texto

Prioridade: `P2`
Tipo: `script`
Status: `not_started`

Escopo:

- Aplicar OCR quando houver imagem rica.
- Marcar confianca de OCR.
- Preservar referencia visual.

Aceite:

- OCR incerto nao vira insight de alta confianca.
- Evidencia menciona arquivo e area/descricao.

Dependencias:

- MSF-D01.

## EPIC E - Extracao de insights

### MSF-E01 - Criar prompt base de extracao

Prioridade: `P0`
Tipo: `prompt`
Status: `done`

Escopo:

- Extrair insights atomicos.
- Exigir nivel, tipo, temas, aplicabilidade, evidencia, confianca e dedupe_key.
- Suportar fonte `transcript`, `description`, `comment` e `asset`.

Aceite:

- Gera JSON valido.
- Nao aceita insight sem evidencia.
- Funciona em segmento de transcricao e segmento de asset.

Dependencias:

- MSF-A02, MSF-A03, MSF-B04.

### MSF-E02 - Criar extratores especializados

Prioridade: `P0`
Tipo: `prompt`
Status: `done`

Escopo:

- Criar prompts para copy, VSL, anuncios, oferta, funil, ops, produto e assets.
- Todos seguem o mesmo schema.

Aceite:

- Cada extrator tem foco claro.
- Asset extractor detecta frameworks, templates, planilhas, checklists e copies completas.

Dependencias:

- MSF-E01.

### MSF-E03 - Implementar runner de extracao local

Prioridade: `P0`
Tipo: `script`
Status: `done`

Escopo:

- Ler segmentos.
- Aceitar segmentos completos ou chunks por capitulo.
- Aplicar prompt/extrator selecionado via Codex workflow manual ou semi-automatizado.
- Salvar `insights.json`.
- Permitir reprocessamento por extrator.
- Gerar pacotes em lote para todos os chunks e extratores selecionados.

Aceite:

- Processa 1 episodio piloto.
- Gera pacotes de extracao por chunk para episodios longos.
- Processa 1 asset piloto.
- Gera pacote por chunk sem exigir comando manual repetitivo.
- Mantem source_agent e dedupe_key.

Dependencias:

- MSF-E02, MSF-D02.

### MSF-E04 - Implementar deduplicacao local

Prioridade: `P0`
Tipo: `script`
Status: `done`

Escopo:

- Deduplicar por `dedupe_key`, fonte e similaridade textual simples.
- Manter relacao `similar_to` quando insights forem parecidos mas nao duplicados.

Aceite:

- Reprocessamento nao duplica insights obvios.
- Duplicatas ficam registradas ou descartadas com log.
- `scripts/dedupe_insights.py` implementa dedupe deterministico local.

Dependencias:

- MSF-E03.

### MSF-E05 - Implementar classificacao taxonomica

Prioridade: `P1`
Tipo: `prompt`
Status: `in_progress`

Escopo:

- Classificar insights usando taxonomia seed.
- Sugerir novos termos com justificativa.
- Evitar crescimento descontrolado.

Aceite:

- Insights recebem temas e subtemas.
- Novos termos entram como sugestao, nao como verdade automatica sem log.
- `scripts/classify_taxonomy.py` classifica temas/aplicabilidade com heuristicas; sugestao governada de novos termos ainda precisa evoluir.

Dependencias:

- MSF-E03, MSF-A03.

### MSF-E06 - Criar gerador de resumo por episodio e por asset

Prioridade: `P1`
Tipo: `script`
Status: `done`

Escopo:

- Gerar `episode_summary.md` e `asset_summary.md`.
- Incluir top insights, materiais detectados, lacunas e proximas acoes.

Aceite:

- Resumos ajudam revisao humana.
- Cada resumo referencia arquivos de origem.
- `scripts/generate_summaries.py` gera resumos locais de episodios e assets.

Dependencias:

- MSF-E03.

## EPIC F - Qualidade, auditoria e avaliacao

### MSF-F01 - Criar checklist de qualidade de insight

Prioridade: `P0`
Tipo: `qa`
Status: `done`

Escopo:

- Definir criterios: evidencia, especificidade, utilidade, aplicabilidade, nao alucinacao, granularidade.
- Criar escala de avaliacao.

Aceite:

- Checklist pode ser aplicado por agente ou humano.
- Insights sem evidencia sao reprovados ou marcados como hipotese.

Dependencias:

- MSF-E01.

### MSF-F02 - Implementar auditoria local de insights

Prioridade: `P0`
Tipo: `script`
Status: `done`

Escopo:

- Validar JSON.
- Verificar campos obrigatorios.
- Verificar evidencia.
- Gerar relatorio de problemas.

Aceite:

- Relatorio mostra insights sem evidencia, sem tema, sem aplicabilidade ou com baixa confianca.

Dependencias:

- MSF-E03, MSF-F01.

### MSF-F03 - Criar avaliacao de outputs com e sem base

Prioridade: `P0`
Tipo: `qa`
Status: `done`

Escopo:

- Definir rubrica para VSL, leads e anuncios.
- Comparar output gerado sem Marketing Swipe File vs com Marketing Swipe File.

Aceite:

- Rubrica inclui clareza, especificidade, curiosidade, mecanismo, prova, fit com avatar e forca comercial.
- Resultado registra quais insights sustentaram melhoria.
- `docs/output-evaluation-rubric.md` e `scripts/evaluate_output.py` foram criados e usados em VSL/anuncios.

Dependencias:

- MSF-E03.

### MSF-F04 - Criar amostragem de revisao humana

Prioridade: `P1`
Tipo: `qa`
Status: `not_started`

Escopo:

- Selecionar amostra de insights por episodio, por asset e por tipo.
- Gerar arquivo de revisao para o usuario.

Aceite:

- Usuario consegue revisar sem abrir todos os arquivos.
- Feedback pode ser reinserido na base.

Dependencias:

- MSF-F02.

## EPIC G - Base consultavel local

### MSF-G01 - Consolidar master exports

Prioridade: `P0`
Tipo: `script`
Status: `done`

Escopo:

- Gerar `insights_master.json`, `insights_master.csv`, `episodes_master.json`, `assets_master.json`, `acquisition_tasks_master.csv`.

Aceite:

- Exports incluem todos os ids necessarios.
- Sem duplicatas obvias.
- `scripts/consolidate_exports.py` gera os master exports locais.

Dependencias:

- MSF-E04, MSF-C04.

### MSF-G02 - Implementar busca local por filtros

Prioridade: `P0`
Tipo: `script`
Status: `done`

Escopo:

- Buscar por tema, fonte, episodio, asset, nivel, insight_type, aplicabilidade e confianca.

Aceite:

- Consulta por VSL retorna insights de VSL.
- Consulta por source_kind asset retorna materiais complementares.
- `scripts/search_insights.py` aceita filtros estruturados.

Dependencias:

- MSF-G01.

### MSF-G03 - Implementar busca textual local

Prioridade: `P0`
Tipo: `script`
Status: `done`

Escopo:

- Buscar texto em titulo, insight, evidencia, tags e resumo.
- Permitir exportar resultados para strategy pack.

Aceite:

- Busca por "lead", "mecanismo", "oferta" e "quiz" retorna resultados relevantes.
- `scripts/search_insights.py` tambem executa busca textual em insights e evidencias.

Dependencias:

- MSF-G01.

### MSF-G04 - Criar strategy pack retrieval local

Prioridade: `P0`
Tipo: `prompt`
Status: `done`

Escopo:

- Dada uma tarefa, montar pacote com insights, evidencias, frameworks, warnings e lacunas.
- Suportar VSL, anuncios, quiz, webinar e oferta.

Aceite:

- Strategy pack inclui referencias por id.
- Pacote diferencia video e material complementar.
- `scripts/generate_strategy_pack.py` e `prompts/retrieval/strategy_pack_retrieval.md` geram packs locais.

Dependencias:

- MSF-G02, MSF-G03.

## EPIC H - Prova de valor MVP

### MSF-H01 - Processar 3 episodios piloto VTurb

Prioridade: `P0`
Tipo: `qa`
Status: `done`

Escopo:

- Rodar ingestao, transcricao, asset detection, extracao, dedupe, auditoria e busca.

Aceite:

- Pelo menos 75 insights.
- Evidencia em pelo menos 90%.
- Materiais detectados quando mencionados.
- 4 episodios foram processados com transcript/chunks.
- 143 insights profundos de transcricao foram gerados e auditados.

Dependencias:

- MSF-G04, MSF-F02.

### MSF-H02 - Ajustar pipeline apos pilotos

Prioridade: `P0`
Tipo: `product`
Status: `done`

Escopo:

- Revisar erros, lacunas, redundancias, prompts e taxonomia.
- Atualizar contratos se necessario antes de escalar para 20 episodios.

Aceite:

- Lista de ajustes aplicada.
- Pipeline foi usado para escalar o lote local para 21 episodios processados.
- Ajustes de detector, exports, busca, avaliacao, fallback Playwright e extracao profunda foram aplicados.

Dependencias:

- MSF-H01.

### MSF-H03 - Processar 20 episodios VTurb

Prioridade: `P0`
Tipo: `data`
Status: `done`

Escopo:

- Processar 20 episodios.
- Consolidar insights e tarefas de assets.

Aceite:

- Pelo menos 500 insights atomicos.
- Materiais complementares detectados e com status.
- Exports master atualizados.
- Gate atingido em 2026-07-04: 21 episodios com transcript/chunks, 610 insights consolidados e 11 tarefas de materiais complementares.

Dependencias:

- MSF-H02.

### MSF-H04 - Criar VSL com 3 leads usando a base

Prioridade: `P0`
Tipo: `qa`
Status: `done`

Escopo:

- Gerar strategy pack para uma VSL.
- Criar VSL completa e 3 leads.
- Registrar insights usados.

Aceite:

- Output referencia insights por id.
- Avaliacao mostra se ficou igual ou melhor que baseline sem base.
- VSL atualizada para usar insights de transcricao. O score antigo `pass` com 39/40 foi reclassificado em MSF-R09 como `keyword_presence_check` apenas; a avaliacao honesta posterior deu 30/40, `needs_revision`.

Dependencias:

- MSF-H03, MSF-F03.

### MSF-H05 - Criar anuncios usando a base

Prioridade: `P0`
Tipo: `qa`
Status: `done`

Escopo:

- Gerar 10 hooks, 10 scripts curtos, 5 briefings de imagem/video e hipoteses de teste.
- Registrar insights usados.

Aceite:

- Cada anuncio tem justificativa estrategica.
- Cada justificativa aponta para evidencia.
- Pacote de anuncios atualizado para usar insights de transcricao. O score antigo `pass` com 37/40 foi reclassificado em MSF-R09 como `keyword_presence_check` apenas; a avaliacao honesta posterior deu 30/40, `needs_revision`.

Dependencias:

- MSF-H03, MSF-F03.

## EPIC I - Skills Codex

### MSF-I01 - Criar skill `marketing-swipe-file-ingest`

Prioridade: `P0`
Tipo: `skill`
Status: `done`

Escopo:

- Encapsular ingestao, metadata, transcript e segmentation.
- Referenciar scripts e contratos.

Aceite:

- `SKILL.md` e enxuto.
- Skill foi testada com 1 episodio.
- Nao carrega documentacao desnecessaria.
- Criada em `skills/marketing-swipe-file-ingest/`.

Dependencias:

- MSF-H02.

### MSF-I02 - Criar skill `marketing-swipe-file-detect-assets`

Prioridade: `P0`
Tipo: `skill`
Status: `done`

Escopo:

- Encapsular deteccao de assets e geracao de tarefas manuais.

Aceite:

- Detecta caso simulado de direct/keyword.
- Nao inventa asset sem evidencia.
- Criada em `skills/marketing-swipe-file-detect-assets/`.

Dependencias:

- MSF-C02, MSF-H02.

### MSF-I03 - Criar skill `marketing-swipe-file-process-assets`

Prioridade: `P0`
Tipo: `skill`
Status: `done`

Escopo:

- Encapsular processamento de PDF, DOCX, XLSX, CSV, PPTX, HTML e texto.

Aceite:

- Processa ao menos 1 PDF e 1 planilha fixture ou real.
- Mantem evidencia por pagina/aba/range.
- Criada em `skills/marketing-swipe-file-process-assets/`.

Dependencias:

- MSF-D02, MSF-D04.

### MSF-I04 - Criar skill `marketing-swipe-file-extract-insights`

Prioridade: `P0`
Tipo: `skill`
Status: `done`

Escopo:

- Encapsular extratores, dedupe e saida de insights.

Aceite:

- Roda sobre segmento de transcricao e asset.
- Gera insights auditaveis.
- Criada em `skills/marketing-swipe-file-extract-insights/`.

Dependencias:

- MSF-E04, MSF-F02.

### MSF-I05 - Criar skill `marketing-swipe-file-retrieve`

Prioridade: `P1`
Tipo: `skill`
Status: `done`

Escopo:

- Encapsular busca local e geracao de strategy pack.

Aceite:

- Retorna strategy pack para VSL e anuncios.
- Inclui referencias e evidencias.
- Criada em `skills/marketing-swipe-file-retrieve/`.

Dependencias:

- MSF-G04.

### MSF-I06 - Criar skill `marketing-swipe-file-quality-review`

Prioridade: `P1`
Tipo: `skill`
Status: `done`

Escopo:

- Encapsular auditoria de insights e outputs.

Aceite:

- Gera relatorio de problemas.
- Reprova insights sem evidencia.
- Criada em `skills/marketing-swipe-file-quality-review/`.

Dependencias:

- MSF-F02, MSF-F03.

### MSF-I07 - Criar skill `marketing-swipe-file-output-eval`

Prioridade: `P2`
Tipo: `skill`
Status: `in_progress`

Escopo:

- Encapsular comparacao de outputs com e sem base.

Aceite:

- Produz score e justificativa.
- Lista insights que melhoraram output.

Dependencias:

- MSF-F03.

## EPIC J - Loops operacionais

### MSF-J01 - Loop de processamento de episodio

Prioridade: `P0`
Tipo: `loop`
Status: `in_progress`

Escopo:

- Compor ingest, detect-assets, extract-insights e quality-review.

Aceite:

- Processa 1 episodio novo com pouca reexplicacao.
- Gera logs, insights e tarefas manuais.
- `loops/episode-processing.md` e `scripts/run_episode_pipeline.py` existem; falta completar a extracao profunda dentro do loop.

Dependencias:

- MSF-I01, MSF-I02, MSF-I04, MSF-I06.

### MSF-J02 - Loop de processamento de material complementar

Prioridade: `P0`
Tipo: `loop`
Status: `in_progress`

Escopo:

- Compor process-assets, extract-insights e quality-review.

Aceite:

- Processa arquivo obtido.
- Vincula insights ao episodio e asset.
- `loops/asset-processing.md` e `scripts/run_asset_pipeline.py` existem; falta validar com material real obtido do piloto.

Dependencias:

- MSF-I03, MSF-I04, MSF-I06.

### MSF-J03 - Loop de retrieval para strategy pack

Prioridade: `P1`
Tipo: `loop`
Status: `done`

Escopo:

- Compor retrieve, filtros, evidence pack e output de contexto.

Aceite:

- Gera strategy pack para VSL, anuncios e quiz.
- `loops/strategy-pack.md` foi criado e validado em VSL/anuncios.

Dependencias:

- MSF-I05.

### MSF-J04 - Loop de criacao e avaliacao de output

Prioridade: `P1`
Tipo: `loop`
Status: `in_progress`

Escopo:

- Strategy pack -> agente consumidor -> output -> registro de insights -> avaliacao.

Aceite:

- Output final lista referencias.
- Avaliacao fica persistida.
- `loops/output-evaluation.md` existe e ja persistiu avaliacoes de VSL/anuncios; falta comparar contra baseline sem base em volume maior.

Dependencias:

- MSF-J03, MSF-I07.

### MSF-J05 - Loop de reprocessamento

Prioridade: `P2`
Tipo: `loop`
Status: `not_started`

Escopo:

- Reprocessar episodio ou asset quando prompts/taxonomia melhorarem.
- Evitar duplicacao.

Aceite:

- Reprocessamento cria nova versao ou atualiza com log.
- Insights antigos nao somem sem rastreio.

Dependencias:

- MSF-J01, MSF-J02.

## EPIC K - Supabase e persistencia estruturada

### MSF-K01 - Preparar decisao de arquitetura Supabase

Prioridade: `P0`
Tipo: `database`
Status: `not_started`

Escopo:

- Confirmar projeto novo.
- Definir schemas expostos vs privados.
- Revisar changelog/docs atuais do Supabase antes de implementar.
- Definir politica inicial de RLS e chaves.

Aceite:

- Decisao documentada.
- Nenhuma tabela publica fica sem plano de RLS.
- Nenhuma chave sensivel entra no repo.

Dependencias:

- MSF-H03.

### MSF-K02 - Criar projeto Supabase

Prioridade: `P1`
Tipo: `database`
Status: `not_started`

Escopo:

- Criar projeto Supabase.
- Documentar variaveis locais.
- Configurar ambiente sem commitar secrets.

Aceite:

- Projeto acessivel.
- `.env.example` criado sem segredos.

Dependencias:

- MSF-K01.

### MSF-K03 - Criar schema inicial

Prioridade: `P1`
Tipo: `database`
Status: `not_started`

Escopo:

- Criar tabelas `sources`, `episodes`, `referenced_assets`, `acquisition_tasks`, `assets`, `content_segments`, `insights`, `insight_evidence`, `taxonomy_terms`, `insight_tags`, `insight_relations`, `generated_artifacts`, `artifact_insights`.
- Criar constraints, FKs e indices.
- Usar fluxo de migracao recomendado apos iterar schema.

Aceite:

- Schema carrega sem erro.
- Chaves e indices minimos existem.
- Queries basicas funcionam.

Dependencias:

- MSF-K02.

### MSF-K04 - Implementar RLS e politicas iniciais

Prioridade: `P1`
Tipo: `database`
Status: `not_started`

Escopo:

- Ativar RLS em tabelas expostas.
- Criar politicas de leitura/escrita coerentes com uso pessoal inicial.
- Evitar `auth.role()` e politicas amplas sem ownership se houver multiusuario.

Aceite:

- RLS habilitado onde aplicavel.
- Nenhuma tabela exposta fica aberta por acidente.
- Testes de acesso basicos documentados.

Dependencias:

- MSF-K03.

### MSF-K05 - Criar importador local -> Supabase

Prioridade: `P1`
Tipo: `script`
Status: `not_started`

Escopo:

- Importar master exports para Supabase.
- Idempotencia por ids, video_id, checksum e dedupe_key.
- Logar inseridos, atualizados, ignorados e erros.

Aceite:

- Importa lote de teste.
- Reexecucao nao duplica.
- Falha parcial nao corrompe base.

Dependencias:

- MSF-K03.

### MSF-K06 - Criar consultas/RPCs de busca estruturada

Prioridade: `P1`
Tipo: `database`
Status: `not_started`

Escopo:

- Buscar insights, evidencias, episodios, assets, tarefas e strategy packs simples.

Aceite:

- Queries retornam evidencia junto do insight.
- Filtros por tema, fonte, asset e confianca funcionam.

Dependencias:

- MSF-K05.

### MSF-K07 - Implementar full-text search

Prioridade: `P1`
Tipo: `database`
Status: `not_started`

Escopo:

- Criar colunas/indices para busca textual em insights, evidencias e segmentos.

Aceite:

- Busca por termos comerciais retorna resultados relevantes.
- Performance aceitavel para base inicial.

Dependencias:

- MSF-K06.

### MSF-K08 - Implementar pgvector e embeddings

Prioridade: `P2`
Tipo: `database`
Status: `not_started`

Escopo:

- Habilitar pgvector quando custo/API for aprovado.
- Criar embeddings para insights, segmentos e assets.
- Criar busca hibrida: filtros + full-text + vetor.

Aceite:

- Busca semantica retorna resultados melhores que texto puro em testes definidos.
- Custos sao documentados.

Dependencias:

- MSF-K07.

## EPIC L - MCP server

### MSF-L01 - Definir contrato MCP

Prioridade: `P1`
Tipo: `mcp`
Status: `not_started`

Escopo:

- Definir ferramentas, parametros, respostas e erros.
- Incluir `search_insights`, `get_insight`, `get_evidence`, `search_episodes`, `search_assets`, `get_strategy_pack`, `record_artifact_usage`.

Aceite:

- Contrato cobre agentes de VSL e anuncios.
- Respostas sempre incluem evidencia quando relevante.

Dependencias:

- MSF-K06.

### MSF-L02 - Implementar MCP server

Prioridade: `P1`
Tipo: `mcp`
Status: `not_started`

Escopo:

- Criar server conectado ao Supabase.
- Implementar ferramentas principais.
- Configurar ambiente local.

Aceite:

- Ferramentas respondem com dados reais.
- Erros sao claros.
- Nenhuma service key exposta para cliente indevido.

Dependencias:

- MSF-L01.

### MSF-L03 - Testar MCP com agentes consumidores

Prioridade: `P1`
Tipo: `qa`
Status: `not_started`

Escopo:

- Testar agente de VSL, anuncios, CMO e gestor de projetos.

Aceite:

- Agentes conseguem consultar sem ler arquivos locais.
- Outputs registram insights usados.

Dependencias:

- MSF-L02.

### MSF-L04 - Instrumentar uso do MCP

Prioridade: `P2`
Tipo: `ops`
Status: `not_started`

Escopo:

- Logar chamadas, filtros, resultados retornados, agente consumidor e artefato gerado.

Aceite:

- Da para saber quais ferramentas e insights sao mais usados.

Dependencias:

- MSF-L02.

## EPIC M - Agentes especializados

### MSF-M01 - Definir protocolo comum de agente consumidor

Prioridade: `P1`
Tipo: `agent`
Status: `not_started`

Escopo:

- Definir formato de briefing, consulta, strategy pack, output e referencias usadas.

Aceite:

- Qualquer agente consumidor usa o mesmo padrao de citacao de insights.

Dependencias:

- MSF-J04 ou MSF-L03.

### MSF-M02 - Criar agente Copy Strategist

Prioridade: `P1`
Tipo: `agent`
Status: `not_started`

Escopo:

- Interpretar tarefa, buscar estrategia, montar big idea, mecanismo, promessa e mapa de objecoes.

Aceite:

- Produz estrategia com referencias.
- Indica lacunas de pesquisa.

Dependencias:

- MSF-M01.

### MSF-M03 - Criar agente Copywriter de VSL

Prioridade: `P1`
Tipo: `agent`
Status: `not_started`

Escopo:

- Criar VSL, leads, mecanismos, provas, transicoes e CTA usando strategy pack.

Aceite:

- Gera VSL com 3 leads.
- Referencia insights usados.

Dependencias:

- MSF-M02.

### MSF-M04 - Criar agente Copywriter de Anuncios

Prioridade: `P1`
Tipo: `agent`
Status: `not_started`

Escopo:

- Criar hooks, scripts curtos, angulos e briefings de criativos.

Aceite:

- Gera pacote de anuncios com hipoteses de teste e evidencias.

Dependencias:

- MSF-M01.

### MSF-M05 - Criar agente Copywriter de Quiz

Prioridade: `P2`
Tipo: `agent`
Status: `not_started`

Escopo:

- Criar estrategia de quiz, perguntas, resultados e pontes para oferta.

Aceite:

- Quiz referencia insights de avatar, oferta e mecanismo.

Dependencias:

- MSF-M01.

### MSF-M06 - Criar agentes executivos

Prioridade: `P2`
Tipo: `agent`
Status: `not_started`

Escopo:

- CEO, CMO, COO, Head de Produto, Head de Lancamentos e Gestor de Projetos.

Aceite:

- Cada agente tem papel, entradas, saidas e criterios de qualidade.
- Cada um usa Marketing Swipe File como base, nao como enfeite.

Dependencias:

- MSF-M01.

### MSF-M07 - Criar agentes avaliadores

Prioridade: `P2`
Tipo: `agent`
Status: `not_started`

Escopo:

- Avaliar VSL, anuncios, quizzes, ofertas e strategy packs.

Aceite:

- Avaliacao aponta pontos fortes, riscos e evidencias.
- Avaliador detecta quando output nao usou a base.

Dependencias:

- MSF-F03, MSF-M01.

## EPIC N - Automacao de fontes

### MSF-N01 - Mapear canais e prioridade de processamento

Prioridade: `P1`
Tipo: `product`
Status: `not_started`

Escopo:

- VTurb primeiro, depois KiwiCast, Hotmart Cast e fontes derivadas.
- Definir criterio para "zerar" canal.

Aceite:

- Existe lista de canais, ids, prioridades e status.

Dependencias:

- MSF-H03.

### MSF-N02 - Implementar monitoramento de novos episodios

Prioridade: `P2`
Tipo: `script`
Status: `not_started`

Escopo:

- Detectar novos videos por canal via metodo definido.
- Adicionar a fila de ingestao.

Aceite:

- Novo episodio aparece em fila sem duplicar.

Dependencias:

- MSF-N01.

### MSF-N03 - Implementar processamento em lote

Prioridade: `P2`
Tipo: `script`
Status: `not_started`

Escopo:

- Rodar pipeline para N episodios.
- Retomar falhas.
- Controlar taxa e logs.

Aceite:

- Lote interrompido pode ser retomado.
- Falhas por episodio nao derrubam lote inteiro.

Dependencias:

- MSF-J01.

### MSF-N04 - Criar rotina de reprocessamento periodico

Prioridade: `P3`
Tipo: `ops`
Status: `not_started`

Escopo:

- Reprocessar com prompts melhores ou nova taxonomia.
- Comparar antes/depois.

Aceite:

- Versoes ficam rastreaveis.

Dependencias:

- MSF-J05.

## EPIC O - UI humana

### MSF-O01 - Definir UX da UI

Prioridade: `P2`
Tipo: `product`
Status: `not_started`

Escopo:

- Definir telas para busca, episodio, asset, insight, fila manual, strategy pack e outputs.
- Priorizar uso utilitario, denso e escaneavel.

Aceite:

- Fluxos principais documentados.
- UI nao tenta substituir agentes no inicio.

Dependencias:

- MSF-K06.

### MSF-O02 - Criar dashboard de busca e filtros

Prioridade: `P2`
Tipo: `ui`
Status: `not_started`

Escopo:

- Buscar insights por texto, filtros e fonte.
- Abrir evidencia.

Aceite:

- Usuario encontra insights de VSL, anuncios e assets em poucos cliques.

Dependencias:

- MSF-O01.

### MSF-O03 - Criar tela de episodio

Prioridade: `P2`
Tipo: `ui`
Status: `not_started`

Escopo:

- Mostrar metadata, transcricao, materiais detectados, insights e resumo.

Aceite:

- Episodio mostra status completo de processamento.

Dependencias:

- MSF-O02.

### MSF-O04 - Criar tela de material complementar

Prioridade: `P2`
Tipo: `ui`
Status: `not_started`

Escopo:

- Mostrar asset, status, texto extraido, insights e evidencia.

Aceite:

- Usuario entende valor do material sem abrir o arquivo original.

Dependencias:

- MSF-O02.

### MSF-O05 - Criar fila de acoes manuais

Prioridade: `P2`
Tipo: `ui`
Status: `not_started`

Escopo:

- Listar materiais pendentes.
- Mostrar instrucao para obter arquivo.
- Permitir marcar obtido, indisponivel ou descartado.

Aceite:

- Usuario sabe exatamente qual direct/comentario/area de membros precisa acionar.

Dependencias:

- MSF-O02.

### MSF-O06 - Criar tela de strategy pack

Prioridade: `P3`
Tipo: `ui`
Status: `not_started`

Escopo:

- Permitir montar contexto para VSL, anuncios, quiz, oferta e webinar.

Aceite:

- UI gera pacote que agentes conseguem usar.

Dependencias:

- MSF-O02, MSF-L02.

## EPIC P - Grafo, playbooks e inteligencia composta

### MSF-P01 - Implementar relacoes entre insights

Prioridade: `P2`
Tipo: `data`
Status: `not_started`

Escopo:

- Criar `supports`, `contradicts`, `extends`, `example_of`, `similar_to`, `depends_on`, `part_of`, `applies_to`.

Aceite:

- Insights relacionados aparecem em busca e strategy pack.

Dependencias:

- MSF-E05, MSF-K03.

### MSF-P02 - Criar detector de padroes recorrentes

Prioridade: `P2`
Tipo: `prompt`
Status: `not_started`

Escopo:

- Identificar padroes por tema, fonte, convidado, nicho, ativo e etapa do funil.

Aceite:

- Sistema gera relatorio de padroes recorrentes com evidencias.

Dependencias:

- MSF-P01.

### MSF-P03 - Criar playbooks por ativo

Prioridade: `P2`
Tipo: `data`
Status: `not_started`

Escopo:

- Playbooks para VSL, anuncios, quiz, webinar, oferta, funil e low ticket.

Aceite:

- Playbook tem passos, exemplos, evidencias e aplicabilidade.

Dependencias:

- MSF-P02.

### MSF-P04 - Criar playbooks por nicho

Prioridade: `P3`
Tipo: `data`
Status: `not_started`

Escopo:

- Playbooks por infoproduto, SaaS, e-commerce, encapsulado, high ticket, local e outros.

Aceite:

- Playbook diferencia o que muda por nicho.

Dependencias:

- MSF-P03.

### MSF-P05 - Criar comparador de estrategias

Prioridade: `P3`
Tipo: `agent`
Status: `not_started`

Escopo:

- Comparar duas estrategias usando evidencias da base.

Aceite:

- Comparacao explica tradeoffs e quando usar cada estrategia.

Dependencias:

- MSF-P03.

## EPIC Q - Operacao, seguranca e governanca

### MSF-Q01 - Criar politica de dados e arquivos

Prioridade: `P1`
Tipo: `ops`
Status: `not_started`

Escopo:

- Definir o que fica no Git, local, Supabase Storage ou fora do repo.
- Definir tratamento para arquivos de area de membros ou materiais privados.

Aceite:

- Arquivos sensiveis nao sao commitados.
- Existe criterio para materiais privados.

Dependencias:

- MSF-D01.

### MSF-Q02 - Criar estrategia de backup e export

Prioridade: `P1`
Tipo: `ops`
Status: `not_started`

Escopo:

- Exportar banco, JSON/CSV e assets.
- Definir frequencia.

Aceite:

- Base pode ser restaurada.
- Exports nao vazam segredos.

Dependencias:

- MSF-K05.

### MSF-Q03 - Criar observabilidade

Prioridade: `P2`
Tipo: `ops`
Status: `not_started`

Escopo:

- Medir episodios processados, insights gerados, taxa de evidencia, assets pendentes, outputs gerados e falhas.

Aceite:

- Existe painel ou relatorio operacional.

Dependencias:

- MSF-B05, MSF-K05.

### MSF-Q04 - Criar governanca de taxonomia

Prioridade: `P2`
Tipo: `product`
Status: `not_started`

Escopo:

- Aprovar, mesclar, renomear e depreciar termos.
- Evitar sinonimos duplicados.

Aceite:

- Novos termos entram com status.
- Existe fluxo de revisao.

Dependencias:

- MSF-E05.

### MSF-Q05 - Criar runbook de incidentes

Prioridade: `P3`
Tipo: `ops`
Status: `not_started`

Escopo:

- Falha de transcricao, asset indisponivel, importacao quebrada, MCP fora, Supabase inacessivel, output sem evidencia.

Aceite:

- Cada incidente tem diagnostico e proxima acao.

Dependencias:

- MSF-L02, MSF-K05.

## 5. Ordem recomendada para execucao inicial

1. MSF-A01
2. MSF-A02
3. MSF-A03
4. MSF-A04
5. MSF-B01
6. MSF-B02
7. MSF-B03
8. MSF-B04
9. MSF-C01
10. MSF-C02
11. MSF-C03
12. MSF-D01
13. MSF-D02
14. MSF-D03
15. MSF-E01
16. MSF-E02
17. MSF-E03
18. MSF-E04
19. MSF-F01
20. MSF-F02
21. MSF-G01
22. MSF-G02
23. MSF-G03
24. MSF-G04
25. MSF-H01
26. MSF-H02
27. MSF-H03
28. MSF-H04
29. MSF-H05

Depois do MVP validado, seguir para:

1. MSF-I01 a MSF-I07
2. MSF-J01 a MSF-J05
3. MSF-K01 a MSF-K08
4. MSF-L01 a MSF-L04
5. MSF-M01 a MSF-M07
6. MSF-N01 a MSF-N04
7. MSF-O01 a MSF-O06
8. MSF-P01 a MSF-P05
9. MSF-Q01 a MSF-Q05

## 6. Marcos de decisao

### Gate 1 - Depois de 3 episodios piloto

Decidir:

- Prompts estao extraindo insights bons?
- Taxonomia precisa mudar?
- Detector de materiais esta confiavel?
- Vale processar os 20 episodios agora?

### Gate 2 - Depois de 20 episodios VTurb

Decidir:

- A base melhora VSL e anuncios?
- Quais materiais complementares valem perseguir primeiro?
- Quais skills devem ser criadas primeiro?
- Supabase deve entrar agora ou apos mais iteracao local?

### Gate 3 - Depois das skills e loops

Decidir:

- Loops estao estaveis o suficiente para agentes?
- O que deve virar MCP?
- Quais agentes consumidores tem maior ROI?

### Gate 4 - Depois do Supabase

Decidir:

- Busca SQL/full-text resolve ou embeddings sao necessarios?
- MCP deve ser local, remoto ou ambos?
- UI humana ja agrega valor ou ainda e cedo?

### Gate 5 - Depois dos primeiros agentes

Decidir:

- Quais outputs realmente melhoraram?
- Quais agentes devem ser expandidos?
- Quais playbooks surgiram da base?
