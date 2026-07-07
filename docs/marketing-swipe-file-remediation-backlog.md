# Backlog De Remediacao - Marketing Swipe File

Data de criacao: 2026-07-06

## 1. Objetivo deste backlog

Este backlog corrige os problemas estruturais identificados na auditoria de 2026-07-06, antes de escalar volume (110 episodios restantes, KiwiCast, Hotmart Cast) ou subir Supabase/MCP.

Diagnostico resumido da auditoria:

1. A extracao de insights em `scripts/extract_transcript_insights.py` e heuristica por regras fixas de keywords. Os 1.223 insights consolidados sao ~30 templates repetidos com evidencias diferentes. O teto de conhecimento da base e o conjunto de regras, nao o conteudo dos episodios. Os prompts LLM de `prompts/extraction/` existem mas nunca rodaram em escala sobre os packets chunkados.
2. A avaliacao de outputs em `scripts/evaluate_output.py` mede presenca de keywords, nao qualidade. Os scores 39/40 e 37/40 sao circulares: gerador e avaliador compartilham vocabulario. Nao provam valor.
3. O ranking de `scripts/generate_strategy_pack.py` nao penaliza redundancia. Com 656 insights vindos de titulos 100+ vezes repetidos, o top-N tende a repetir o mesmo template.
4. Riscos operacionais: ~41 arquivos sem commit, projeto dentro do OneDrive com locks ja observados, dependencia do Python do cache do Codex, docs em drift (scripts academy fora do handoff).

Regra de execucao deste backlog: nao processar novos episodios em lote e nao iniciar Supabase/MCP antes de fechar os gates R1 e R2 abaixo.

Este documento complementa:

- `docs/marketing-swipe-file-full-backlog.md`
- `docs/insight-quality-review-2026-07-04.md`
- `docs/marketing-swipe-file-handoff.md`

## 2. Convencoes

Mesmas convencoes do backlog mestre: prioridades `P0`-`P3`, status `not_started`/`in_progress`/`blocked`/`done`/`deferred`, tipos `product`/`data`/`script`/`prompt`/`skill`/`loop`/`database`/`qa`/`ops`.

Serie de IDs: `MSF-R` (remediacao). As series A-M do backlog mestre continuam validas.

## 3. Ordem executiva e gates

### Bloco R0 - Estabilizacao operacional (fazer primeiro, tudo P0)

MSF-R01, MSF-R02, MSF-R03, MSF-R04.

Gate de saida R0:

- Trabalho versionado em Git.
- Pipeline roda com Python proprio do projeto.
- Handoff reflete o estado real do repositorio.

### Bloco R1 - Extracao LLM real (nucleo da remediacao)

MSF-R05, MSF-R06, MSF-R07, MSF-R08.

Gate de saida R1:

- Amostra pareada v1 vs v2 revisada mostra v2 superior em especificidade e fidelidade a evidencia.
- Menos de 10% dos insights v2 com titulo repetido 5+ vezes.

### Bloco R2 - Avaliacao honesta

MSF-R09, MSF-R10.

Gate de saida R2:

- Output gerado com a base vence ou empata com baseline sem base em avaliacao cega.
- Se perder, tratar como sinal de que a base ainda nao paga o proprio custo; voltar ao R1 antes de escalar.

### Bloco R3 - Retrieval e curadoria

MSF-R11, MSF-R12, MSF-R13.

Gate de saida R3:

- Strategy packs regenerados a partir de `curated_insights` sem duplicacao dominante no top-N.

### Bloco R4 - Escala e proximas camadas (somente apos gates R1-R3)

MSF-R14, MSF-R15, MSF-R16.

## 4. Backlog

## EPIC R0 - Estabilizacao operacional

### MSF-R01 - Commitar todo o trabalho pendente

Prioridade: `P0`
Tipo: `ops`
Status: `not_started`

Escopo:

- Revisar os ~41 arquivos modificados/untracked (`git status`).
- Confirmar que nada em `data/raw/`, `data/processed/`, `data/input/assets/` ou exports sensiveis entra no commit; ajustar `.gitignore` se necessario.
- Atencao: `data/input/academy_video_transcription_queue.csv` e `data/input/youtube_urls_academy_new.csv` aparecem como untracked; decidir explicitamente se sao rastreaveis (contem apenas URLs/fila) ou se devem ser ignorados pela politica de dados locais.
- Commitar em blocos logicos com mensagens convencionais: scripts, skills, loops, prompts, docs.

Aceite:

- `git status` limpo exceto dados locais intencionalmente ignorados.
- Nenhum transcript bruto, asset privado ou export com material copyrighted versionado.

Dependencias:

- Nenhuma.

### MSF-R02 - Criar ambiente Python proprio do projeto

Prioridade: `P0`
Tipo: `ops`
Status: `not_started`

Escopo:

- Criar venv do projeto (ex.: `.venv/`) com Python instalado na maquina, removendo a dependencia de `C:\Users\luish\.cache\codex-runtimes\...` (cache e descartavel; atualizacao do Codex pode quebrar o pipeline).
- Gerar `requirements.txt` com as dependencias reais dos scripts: `pdfplumber`, `python-docx`, `openpyxl`, `python-pptx` e o que mais os imports revelarem.
- Adicionar `.venv/` ao `.gitignore`.
- Atualizar `README.md` e `docs/marketing-swipe-file-handoff.md` com o novo comando de ativacao, mantendo o caminho antigo documentado como fallback.

Aceite:

- `scripts/run_episode_pipeline.py --video-id <id_ja_processado> --skip-metadata --skip-transcript` roda com o venv novo.
- Validacao rapida do handoff (parse de JSONs + compile de scripts) roda com o venv novo.

Dependencias:

- MSF-R01.

### MSF-R03 - Tirar dados do alcance do sync do OneDrive

Prioridade: `P1`
Tipo: `ops`
Status: `not_started`

Escopo:

- O handoff ja registra marcadores presos por permissao do OneDrive. Milhares de JSONs pequenos em `data/` causam locks e conflitos de sync.
- Opcao A (preferida): mover `data/raw/`, `data/processed/` e `data/exports/` para um diretorio fora do OneDrive (ex.: `C:\msf-data\`) e apontar os scripts via variavel de ambiente ou constante em `scripts/msf_common.py`.
- Opcao B: marcar as pastas de dados como excluidas do sync do OneDrive.
- Se a Opcao A for escolhida, validar que todos os scripts usam raiz configuravel e nao caminhos relativos hardcoded.

Aceite:

- Pipeline completo roda com dados no novo local.
- Nenhum arquivo `transcript_fallback_needed.md` fantasma ou erro de permissao em rodada completa de validacao.

Dependencias:

- MSF-R02.

### MSF-R04 - Sincronizar documentacao com o estado real

Prioridade: `P0`
Tipo: `ops`
Status: `not_started`

Escopo:

- Adicionar ao handoff e ao README: `scripts/transcribe_academy_hls.py`, `scripts/transcribe_academy_videos.py`, `scripts/capture_youtube_transcript_with_playwright_cli.py`, filas `data/input/academy_video_transcription_queue.csv` e `data/input/youtube_urls_academy_new.csv`, e os exports `vturb_academy_*`.
- Registrar este backlog de remediacao na lista de docs canonicos do handoff e do README.
- Atualizar `docs/execution-log.md` com a auditoria de 2026-07-06 e a decisao de pausar escala ate os gates R1/R2.

Aceite:

- Um chat novo consegue retomar o projeto apenas com o handoff, sem descobrir scripts por acidente.

Dependencias:

- MSF-R01.

## EPIC R1 - Extracao LLM real (v2)

### MSF-R05 - Definir contrato raw_insights_v2

Prioridade: `P0`
Tipo: `data`
Status: `done`

Escopo:

- Criar `schemas/insights_v2.schema.json` incorporando os campos recomendados na quality review de 2026-07-04:
  - `canonical_title`, `specific_takeaway`, `use_case`, `when_to_use`, `when_not_to_use`, `claim_risk`, `evidence_cleanliness`, `cluster_id`, `supporting_insight_ids`, `editorial_score`.
- Manter compatibilidade com os campos atuais (`insight_id`, `evidence`, `themes`, `applicability`, `confidence_score`, locators) para nao quebrar consolidacao e busca.
- Definir dois niveis desde ja: `raw_insights_v2` (saida direta da extracao LLM) e `curated_insights` (pos-curadoria, ver MSF-R12).
- Adicionar campo `extraction_method` com valores `heuristic_v1` e `llm_v2` para permitir coexistencia e comparacao.
- Criar exemplo valido em `schemas/examples/`.

Aceite:

- Schema parseia, exemplo valida contra o schema.
- Base v1 permanece intocada e utilizavel durante a transicao.

Execucao 2026-07-07:

- Criado `schemas/insights_v2.schema.json` para `raw_insights_v2` e `curated_insights`.
- Criado `schemas/examples/insights_v2.example.json`.
- Criado `scripts/validate_insights_v2.py` e adicionada dependencia `jsonschema` em `requirements.txt`.
- Validacao executada: `scripts/validate_insights_v2.py schemas/examples/insights_v2.example.json` retornou `VALID`.
- Base v1 ficou intacta; os pilotos v2 foram gravados em `data/processed/**`, que continua ignorado pelo Git.

Dependencias:

- MSF-R01.

### MSF-R06 - Pipeline de extracao LLM sobre packets chunkados

Prioridade: `P0`
Tipo: `script`
Status: `done`

Escopo:

- Os insumos ja existem: extraction packets chunkados em `data/processed/{video_id}/chunks/` e prompts em `prompts/extraction/` (base + especializados).
- Implementar a extracao LLM por chunk gerando `data/processed/{video_id}/insights_v2.json` conforme o schema de MSF-R05.
- Duas rotas de execucao aceitas, escolher conforme acesso disponivel:
  - Rota A (preferida para escala): script `scripts/extract_transcript_insights_llm.py` chamando API de LLM com chave em `.env` (nunca commitada), com retry, controle de custo por episodio e cache de chunks ja extraidos (idempotente por hash do chunk).
  - Rota B (Codex-first, sem API): loop operacional em que o proprio Codex processa cada packet com o prompt e grava a saida validada contra o schema; atualizar `loops/episode-processing.md` e a skill `marketing-swipe-file-extract-insights` para este fluxo.
- Requisitos de qualidade embutidos no prompt/fluxo, vindos da quality review:
  - Titulo especifico proibido de ser generico ("Expert real aumenta autoridade" nao passa; a tese precisa vir do trecho).
  - Quote limpa: rejeitar evidencia contendo "inscreva-se", "assista tambem", hashtags, titulos de outros episodios e blocos promocionais.
  - Maximo de N insights por chunk (sugerido: 5) para forcar selecao, nao inventario.
  - Cada insight referencia locator do chunk de origem.
- Validar saida contra o schema antes de gravar; saida invalida vai para fila de reprocesso, nao para a base.

Aceite:

- Rodar em 2 episodios piloto ja processados gera `insights_v2.json` valido, com titulos especificos e sem os templates da v1.
- Reprocessar o mesmo episodio nao duplica insights (idempotencia).
- Custo/esforco por episodio registrado no execution log.

Execucao 2026-07-07:

- Escolhida Rota B (Codex-first), sem API externa e sem custo de API.
- Criado `prompts/extraction/base_insight_extraction_v2.md`.
- Criado `scripts/extract_transcript_insights_llm.py` para preparar packets Codex, combinar outputs por chunk e validar o `insights_v2.json` final.
- Atualizados `loops/episode-processing.md` e `skills/marketing-swipe-file-extract-insights/SKILL.md` com o fluxo v2.
- Piloto executado em `mCaFyZpXJdE` e `TOW0sWhPaZw`: 4 insights v2 validos por episodio, 8 no total, cobrindo 4 chunks.
- Reprocessamento com `run_id` e `generated_at` fixos preservou os mesmos hashes dos arquivos finais, provando que o combine sobrescreve sem duplicar.
- Quotes do piloto foram conferidas contra os segmentos locais: 8/8 evidencias bateram com os textos de origem.

Dependencias:

- MSF-R05.

### MSF-R07 - Rodar extracao v2 nos 50 episodios completos

Prioridade: `P0`
Tipo: `data`
Status: `in_progress`

Escopo:

- Executar o pipeline de MSF-R06 nos 50 episodios com chunks prontos.
- Atualizar `scripts/consolidate_exports.py` para gerar `data/exports/insights_v2_master.json` separado do master v1.
- Registrar por episodio: numero de insights v2, distribuicao de titulos, tempo/custo.

Aceite:

- 50 episodios com `insights_v2.json` valido.
- `insights_v2_master.json` consolidado.
- Nenhum titulo com mais de 5% de repeticao na base v2 (na v1, um unico titulo tinha 135 ocorrencias).

Dependencias:

- MSF-R06.

Execucao parcial 2026-07-07:

- Atualizado `scripts/consolidate_exports.py` para gerar exports v2 separados:
  - `data/exports/insights_v2_master.json`
  - `data/exports/insights_v2_master.csv`
  - `data/exports/insights_v2_status.json`
  - `data/exports/insights_v2_episode_status.csv`
  - `data/exports/insights_v2_title_distribution.csv`
- A consolidacao preserva o master v1 e valida cada `insights_v2.json` contra `schemas/insights_v2.schema.json` antes de incluir no master v2.
- Rodada local atual: 8 insights v2 validos em 2 episodios (`mCaFyZpXJdE` e `TOW0sWhPaZw`), 0 arquivos v2 invalidos, nenhuma repeticao de titulo v2 acima de 5% com contagem >1.
- `data/exports/insights_v2_status.json` registra `gate_r1_ready=false`, porque a cobertura segue 2/50 episodios alvo.

### MSF-R08 - Comparacao amostral v1 vs v2

Prioridade: `P0`
Tipo: `qa`
Status: `blocked`

Escopo:

- Amostrar 40 pares comparaveis (mesmo episodio/chunk) entre v1 e v2.
- Avaliar cada par nos criterios da quality review: especificidade da tese, fidelidade a evidencia, aplicabilidade operacional, limpeza de quote.
- Gerar `docs/insight-v1-vs-v2-review-<data>.md` no formato da review de 2026-07-04.
- Decidir formalmente: v2 substitui v1 como fonte para retrieval/strategy packs, ou v1 continua e a v2 precisa de nova iteracao de prompt.

Aceite:

- Documento de comparacao com veredito explicito e exemplos.
- Gate R1 declarado como aprovado ou reprovado no execution log.

Dependencias:

- MSF-R07.

Execucao parcial 2026-07-07:

- Criado `scripts/generate_insight_v1_v2_review.py` para gerar uma review pareada v1/v2 sem copiar quotes brutas para docs versionados.
- Gerado `docs/insight-v1-vs-v2-review-2026-07-07.md` com 8 pares piloto a partir dos 2 episodios v2 existentes.
- Resultado piloto: v2 e direcionalmente superior em especificidade, locators de evidencia e campos operacionais.
- Gate R1 nao foi declarado; R08 completo continua bloqueado por MSF-R07 ate haver cobertura v2 nos 50 episodios alvo e amostra de 40 pares comparaveis.

## EPIC R2 - Avaliacao honesta de outputs

### MSF-R09 - Substituir avaliacao por keywords por avaliacao LLM com rubrica

Prioridade: `P0`
Tipo: `script`
Status: `not_started`

Escopo:

- `scripts/evaluate_output.py` hoje da nota 5 a criterio com 3 keywords presentes; isso mede vocabulario, nao qualidade.
- Implementar avaliacao LLM-as-judge aplicando a rubrica real de `docs/output-evaluation-rubric.md`, mesmo esquema de rotas A/B de MSF-R06.
- O avaliador recebe: o output, o briefing e os insight_ids citados com suas evidencias, e deve verificar se as citacoes sao fieis (anti-alucinacao de referencia).
- Manter o score por keywords apenas como check secundario barato, renomeado para deixar claro que e proxy (`keyword_presence_check`), nunca como nota final.
- Regerar as avaliacoes dos artefatos de prova existentes (`generated_vsl_lowticket.md`, `generated_ads_lowticket.md`) e comparar com os 39/40 e 37/40 antigos.

Aceite:

- Nova avaliacao produz notas com justificativa por criterio e verificacao de fidelidade das citacoes.
- Docs e handoff atualizados para nao citar os scores antigos como prova de valor.

Dependencias:

- MSF-R01. Pode rodar em paralelo com EPIC R1.

### MSF-R10 - Teste cego contra baseline sem base

Prioridade: `P1`
Tipo: `qa`
Status: `not_started`

Escopo:

- Gerar, para o mesmo briefing (low ticket ja usado como prova): (a) VSL/ads usando strategy pack da base v2; (b) VSL/ads sem acesso a base (mesmo modelo, mesmo briefing).
- Avaliar os pares as cegas com o avaliador de MSF-R09, sem identificar qual usou a base.
- Este e o gate de Release 1 do backlog mestre ("output com base e igual ou melhor que output sem base") que nunca foi executado de fato.

Aceite:

- Resultado documentado em `docs/`.
- Se a base nao vencer, abrir iteracao de prompt/curadoria antes de qualquer escala.

Dependencias:

- MSF-R08, MSF-R09.

## EPIC R3 - Retrieval e curadoria

### MSF-R11 - Penalidade de redundancia no strategy pack

Prioridade: `P1`
Tipo: `script`
Status: `not_started`

Escopo:

- Em `scripts/generate_strategy_pack.py`, aplicar selecao estilo MMR: ao montar o top-N, penalizar candidatos com similaridade Jaccard alta com itens ja selecionados (funcao `jaccard` ja existe em `scripts/msf_common.py`).
- Adicionar parametro `--diversity-weight` com default sensato (sugerido: 0.3).
- Adicionar cap por episodio de origem (ex.: maximo 3 insights do mesmo video no top-20) para evitar pack dominado por um episodio.

Aceite:

- Strategy pack regenerado nao contem dois itens com a mesma tese no top-10.
- Teste com fixture demonstrando que duplicatas proximas sao suprimidas.

Dependencias:

- MSF-R07 (para rodar sobre a v2; a implementacao pode comecar antes usando v1).

### MSF-R12 - Clusterizacao e primeiro lote de curated_insights

Prioridade: `P1`
Tipo: `data`
Status: `not_started`

Escopo:

- Clusterizar a base v2 por similaridade (Jaccard sobre tokens como primeiro corte; embeddings ficam para MSF-R16).
- Gerar o primeiro lote de 100-150 `curated_insights` priorizando temas de VSL e anuncios (os que alimentam os strategy packs), conforme recomendado na quality review.
- Preencher os campos editoriais do schema v2: `canonical_title`, `when_to_use`, `when_not_to_use`, `claim_risk`, `editorial_score` com a regua 0-100 da review (evidencia 25, especificidade 25, aplicabilidade 20, portabilidade 15, novidade 10, limpeza 5).
- Curadoria pode ser LLM-assistida, mas o lote inicial passa por revisao humana amostral (minimo 30 itens).

Aceite:

- `data/exports/curated_insights.json` com 100-150 itens validos.
- Distribuicao de `editorial_score` registrada; itens abaixo de 50 nao entram.

Dependencias:

- MSF-R08.

### MSF-R13 - Regerar strategy packs com curated_insights

Prioridade: `P1`
Tipo: `qa`
Status: `not_started`

Escopo:

- Apontar `generate_strategy_pack.py` para `curated_insights` (flag `--source curated`).
- Regenerar packs de VSL e ads e comparar lado a lado com os packs antigos.
- Documentar a comparacao (expectativa da review: menos volume, mais qualidade por item).

Aceite:

- Packs novos gerados e avaliados com o avaliador de MSF-R09.
- Decisao registrada: curated vira fonte default dos packs ou nao.

Dependencias:

- MSF-R11, MSF-R12.

## EPIC R4 - Escala e proximas camadas (bloqueado pelos gates R1-R3)

### MSF-R14 - Retomar escala de episodios com pipeline v2

Prioridade: `P2`
Tipo: `data`
Status: `blocked`

Escopo:

- Somente apos gates R1 e R2 aprovados.
- Processar os 110 episodios VTurb restantes com o pipeline v2 (metadata, transcript com fallback Playwright, chunks, extracao LLM).
- Retentar os 6 videos bloqueados conhecidos (`YfI0CjI_XaE`, `Rz1Y7fhXGFI`, `0DlzYLUmKcU`, `wJincuVXxxc`, `FV-KR1eEbCw`, `sVUrU9gvxyk`); se o transcript da UI continuar indisponivel, avaliar transcricao de audio local (base ja existe em `scripts/transcribe_academy_hls.py`).
- Registrar motivo de falha por video automaticamente (item ja recomendado no handoff).

Aceite:

- Cobertura VTurb reportada com numeros reais (completos, bloqueados por motivo).
- Consolidacao v2 atualizada.

Dependencias:

- Gates R1 e R2 aprovados.

### MSF-R15 - Triagem das tarefas de materiais complementares

Prioridade: `P2`
Tipo: `data`
Status: `not_started`

Escopo:

- Triar as 13 tarefas de `data/exports/acquisition_tasks_master.csv`: obter, descartar com motivo, ou adiar.
- Processar os materiais obtidos com `scripts/run_asset_pipeline.py` e extrair insights v2 deles.
- Respeitar a politica de dados locais para material de area de membros.

Aceite:

- Nenhuma tarefa sem decisao registrada.
- Assets obtidos processados e consolidados na base v2.

Dependencias:

- MSF-R06.

### MSF-R16 - Decisao e desenho do Supabase (raw/curated + pgvector)

Prioridade: `P2`
Tipo: `database`
Status: `blocked`

Escopo:

- Somente apos gate R3: nao industrializar formato instavel.
- Desenhar schema com dois niveis desde o inicio: `raw_insights` e `curated_insights`, espelhando o contrato v2.
- Incluir `pgvector` para busca semantica de insights e evidencias (a busca por keywords degrada com a base crescendo).
- Importadores idempotentes a partir dos exports locais.
- RLS e politicas definidas antes de expor qualquer API, conforme Definition of Done do backlog mestre.

Aceite:

- Schema versionado em migrations.
- Import dos exports v2 completo e idempotente.
- Uma query semantica real retornando insights com evidencia sem ler arquivos locais.

Dependencias:

- Gate R3 aprovado.

## 5. Resumo de prioridades para o Codex

Ordem de ataque sugerida, em sessoes:

1. Sessao 1: MSF-R01, MSF-R02, MSF-R04 (estabilizacao; R03 se sobrar tempo).
2. Sessao 2: MSF-R05, MSF-R06 (contrato v2 + pipeline LLM, piloto em 2 episodios) - done em 2026-07-07.
3. Sessao 3: MSF-R07, MSF-R08 (extracao v2 nos 50 + comparacao; declarar gate R1) - proximo.
4. Sessao 4: MSF-R09, MSF-R10 (avaliacao honesta + teste cego; declarar gate R2).
5. Sessao 5: MSF-R11, MSF-R12, MSF-R13 (diversidade + curadoria + packs novos; declarar gate R3).
6. Depois: MSF-R14, MSF-R15, MSF-R16 conforme gates.

Regras permanentes durante a remediacao:

- Nao escalar novos episodios antes do gate R1.
- Nao citar os scores antigos 39/40 e 37/40 como prova de valor.
- Toda saida LLM validada contra schema antes de entrar na base.
- Atualizar `docs/execution-log.md` ao fim de cada sessao, como ja e pratica do projeto.
