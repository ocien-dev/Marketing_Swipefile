# Backlog De Remediacao - Marketing Swipe File

Data de criacao: 2026-07-06

## 1. Objetivo deste backlog

Este backlog corrige os problemas estruturais identificados na auditoria de 2026-07-06, antes de escalar volume (110 episodios restantes, KiwiCast, Hotmart Cast) ou subir Supabase/MCP.

Diagnostico resumido da auditoria:

1. A extracao de insights em `scripts/extract_transcript_insights.py` e heuristica por regras fixas de keywords. Os 1.223 insights consolidados sao ~30 templates repetidos com evidencias diferentes. O teto de conhecimento da base e o conjunto de regras, nao o conteudo dos episodios. Os prompts LLM de `prompts/extraction/` existem mas nunca rodaram em escala sobre os packets chunkados.
2. A avaliacao de outputs em `scripts/evaluate_output.py` mede presenca de keywords, nao qualidade. Os scores 39/40 e 37/40 sao circulares: gerador e avaliador compartilham vocabulario. Nao provam valor.
3. O ranking de `scripts/generate_strategy_pack.py` nao penaliza redundancia. Com 656 insights vindos de titulos 100+ vezes repetidos, o top-N tende a repetir o mesmo template.
4. Riscos operacionais: ~41 arquivos sem commit, projeto dentro do OneDrive com locks ja observados, dependencia do Python do cache do Codex, docs em drift (scripts academy fora do handoff).

Regra de execucao deste backlog apos Gate R1: nao processar o backfill MSF-R14 antes de reabrir MSF-R03 e concluir R2; nao iniciar Supabase/MCP antes de fechar R3.

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
- Emenda de aceite do MSF-R07, registrada em 2026-07-07: para a Rota B Codex-first sem API, Gate R1 exige 15-20 episodios completos por chunk, aproximadamente 225-300 chunks, priorizando episodios cujos insights alimentam os strategy packs de VSL/ads e os episodios ja iniciados (`TOW0sWhPaZw`, `mCaFyZpXJdE`). A cobertura dos 50 episodios passa a ser trabalho continuo pos-gate em MSF-R14. Motivo: decisao do owner de nao usar API; gate por amostra representativa em vez de cobertura total.
- Gate R1 declarado APROVADO em 2026-07-07 pelo juiz externo, apos verificacao independente da remediacao do batch 006.

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
Status: `done`

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

Execucao 2026-07-07:

- Trabalho pendente da Sessao 1 revisado e commitado em blocos logicos.
- Politica de dados reforcada em `.gitignore`; `data/raw/**`, `data/processed/**`, `data/exports/**`, assets privados e midias seguem fora do Git.
- Filas leves da Academy foram mantidas como rastreaveis quando aplicavel.
- Validado `git status` limpo apos os commits, exceto dados locais intencionalmente ignorados.

### MSF-R02 - Criar ambiente Python proprio do projeto

Prioridade: `P0`
Tipo: `ops`
Status: `done`

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

Execucao 2026-07-07:

- Criado e validado `.venv` do projeto com Python local.
- `requirements.txt` atualizado com dependencias reais do pipeline, incluindo processamento de PDF/DOCX/XLSX/PPTX, transcricao e validacao JSON.
- `.venv/` e `.pip-tmp/` mantidos ignorados pelo Git.
- `pip check`, imports principais, pipeline smoke e validacoes de JSON/scripts rodaram com o venv do projeto.

### MSF-R03 - Tirar dados do alcance do sync do OneDrive

Prioridade: `P1`
Tipo: `ops`
Status: `deferred`

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

Execucao 2026-07-07:

- A migracao real de `data/raw/`, `data/processed/` e `data/exports/` para fora do OneDrive nao foi executada.
- Risco permanece documentado: o workspace e o Git estao funcionais, mas OneDrive ainda pode causar locks/permissoes em `.git`, `.pyc`, temp e milhares de JSONs pequenos.
- Mitigacao aplicada nesta etapa: manter dados e exports ignorados pelo Git e usar validacao em memoria quando `py_compile`/`.pyc` bater em permissao.
- Reabrir antes de escala pesada ou automacao longa.

### MSF-R04 - Sincronizar documentacao com o estado real

Prioridade: `P0`
Tipo: `ops`
Status: `done`

Escopo:

- Adicionar ao handoff e ao README: `scripts/transcribe_academy_hls.py`, `scripts/transcribe_academy_videos.py`, `scripts/capture_youtube_transcript_with_playwright_cli.py`, filas `data/input/academy_video_transcription_queue.csv` e `data/input/youtube_urls_academy_new.csv`, e os exports `vturb_academy_*`.
- Registrar este backlog de remediacao na lista de docs canonicos do handoff e do README.
- Atualizar `docs/execution-log.md` com a auditoria de 2026-07-06 e a decisao de pausar escala ate os gates R1/R2.

Aceite:

- Um chat novo consegue retomar o projeto apenas com o handoff, sem descobrir scripts por acidente.

Dependencias:

- MSF-R01.

Execucao 2026-07-07:

- README, handoff e execution log atualizados com `.venv`, comandos de retomada, backlog de remediacao, scripts da Academy e guardrails R1/R2.
- Handoff registra o estado real de 50 episodios completos, exports locais, Academy, MSF-R05/MSF-R06 e a sequencia de retomada.
- `docs/execution-log.md` passou a registrar a auditoria de 2026-07-06 e a pausa de escala/Supabase ate os gates R1/R2.

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
Status: `done`

Escopo:

- Executar o pipeline de MSF-R06 nos 50 episodios com chunks prontos.
- Atualizar `scripts/consolidate_exports.py` para gerar `data/exports/insights_v2_master.json` separado do master v1.
- Registrar por episodio: numero de insights v2, distribuicao de titulos, tempo/custo.

Aceite:

- Emenda de aceite 2026-07-07: Gate R1 passa a exigir 15-20 episodios completos por chunk (~225-300 chunks), com prioridade para episodios que alimentam os strategy packs de VSL/ads e para os ja iniciados (`TOW0sWhPaZw`, `mCaFyZpXJdE`).
- Cobertura dos 50 episodios completos deixa de ser bloqueio do Gate R1 e vira trabalho continuo pos-gate em MSF-R14.
- Motivo da emenda: decisao do owner de permanecer na Rota B Codex-first, sem API; gate por amostra representativa em vez de cobertura total.
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
- `data/exports/insights_v2_status.json` agora mede cobertura por episodio e por chunk para impedir aceite de episodio meio-extraido.
- Rodada local atual: 13 insights v2 validos em 2 episodios alvo (`mCaFyZpXJdE` e `TOW0sWhPaZw`), 0 arquivos v2 invalidos, 0/50 episodios totalmente extraidos em v2, 6/754 chunks alvo extraidos, nenhuma repeticao de titulo v2 acima de 5% com contagem >1.
- `data/exports/insights_v2_status.json` registra `gate_r1_ready=false`.

Execucao 2026-07-07 - emenda Rota B e lote de calibracao:

- Emenda de aceite registrada: Gate R1 por amostra representativa de 15-20 episodios completos por chunk (~225-300 chunks), nao mais cobertura total dos 50 episodios.
- `scripts/consolidate_exports.py` agora separa o alvo continuo de 50 episodios da cobertura minima do gate emendado (`r07_gate_min_complete_episodes=15`, `r07_gate_max_complete_episodes=20`, `r07_gate_route=codex_manual_no_api`).
- `mCaFyZpXJdE` completado em v2: 21/21 chunks, 24 insights v2.
- `TOW0sWhPaZw` completado em v2: 20/20 chunks, 18 insights v2.
- Rodada local apos consolidacao: 42 insights v2 validos em 2 episodios alvo, 0 arquivos v2 invalidos, 2/50 episodios totalmente extraidos em v2, 41/754 chunks alvo extraidos, `gate_r1_ready=false`.
- Throughput real da sessao: 35 chunks novos processados, 29 insights novos adicionados, 2 episodios fechados por chunk. Estimativa calibrada ate o gate emendado: mais 6-8 sessoes nesse ritmo para atingir 15-20 episodios completos, variando conforme tamanho dos episodios.

Execucao 2026-07-07 - lote seguinte Rota B:

- Revisao externa aprovou o lote anterior: 42/42 titulos unicos, `claim_risk` distribuido e gate emendado instrumentado.
- Protocolo ajustado: sessoes R07 devem usar `.\.venv\Scripts\python.exe -B` ou `PYTHONDONTWRITEBYTECODE=1` para eliminar erro de permissao de `.pyc` do OneDrive.
- `yyoGeQp5yzM` completado em v2: 16/16 chunks, 12 insights v2.
- `aSFAve1klsc` completado em v2: 11/11 chunks, 10 insights v2.
- Rodada local apos consolidacao: 64 insights v2 validos, 64/64 titulos unicos, `claim_risk` distribuido (`low=25`, `medium=35`, `high=4`), 0 arquivos v2 invalidos, 4/50 episodios totalmente extraidos em v2, 68/754 chunks alvo extraidos, `gate_r1_ready=false`.
- Throughput real da sessao: 27 chunks novos processados, 22 insights novos adicionados, 2 episodios fechados por chunk. Estimativa calibrada ate o gate emendado: mais 5-7 sessoes para atingir 15-20 episodios completos, variando conforme tamanho dos proximos episodios.
- Lembrete operacional registrado pelo owner: reabrir MSF-R03 entre o Gate R1 e o backfill dos chunks restantes.

Execucao 2026-07-07 - micro-fixes e lote Rota B posterior:

- Revisao externa aprovou o lote anterior: 64/64 titulos unicos e `claim_risk` distribuido.
- Micro-fixes de encoding aplicados nos dados v2 locais e nos `llm_v2_outputs` de origem: `confian?a` -> `confianca`, campos editoriais de `TOW0sWhPaZw-v2-0004` normalizados para ASCII e demais artefatos `?`/non-ASCII encontrados no mesmo scan corrigidos.
- Criado `scripts/audit_insights_v2_text.py` para auditar campos editoriais v2 (`canonical_title`, `specific_takeaway`, `use_case`, `when_to_use`, `when_not_to_use`) contra non-ASCII e `?` orfao; protocolo R07 atualizado para rodar o auditor apos cada lote.
- Auditor passou em 104 arquivos v2 locais (episodios finais + chunk outputs).
- `8WEvN5T7J0U` completado em v2: 14/14 chunks, 10 insights v2.
- `L7u7r6rOl68` completado em v2: 16/16 chunks, 14 insights v2.
- Rodada local apos consolidacao: 88 insights v2 validos, 88/88 titulos unicos, `claim_risk` distribuido (`low=33`, `medium=51`, `high=4`), 0 arquivos v2 invalidos, 6/50 episodios totalmente extraidos em v2, 98/754 chunks alvo extraidos, `gate_r1_ready=false`.
- Throughput real da sessao: 30 chunks novos processados, 24 insights novos adicionados, 2 episodios fechados por chunk. Estimativa calibrada ate o gate emendado: mais 4-6 sessoes para atingir 15-20 episodios completos, variando conforme tamanho dos proximos episodios.

Execucao 2026-07-07 - cobertura emendada atingida:

- Revisao externa aprovou o lote anterior: 88/88 titulos unicos, zero residuo de encoding e densidade por episodio saudavel.
- Com `scripts/audit_insights_v2_text.py` no protocolo, revisao externa por lote fica suspensa.
- Episodios completados em autonomia ate o ponto de parada do gate: `v6luZ9KvmOI`, `zoChfFHnlOQ`, `qj04cUeaRAw`, `cL3FuW8bAMA`, `JF2oC44lBG8`, `qohJceyapS0`, `YcqJ_vrjf-g`, `wHdyTM-nVqg`, `BbhJn8NXRso`.
- Rodada local apos consolidacao: 209 insights v2 validos, 0 arquivos v2 invalidos, 15/50 episodios totalmente extraidos em v2, 246/754 chunks alvo extraidos, `gate_r1_ready=true`.
- Cobertura emendada do MSF-R07 atingida: 15 episodios completos e 246 chunks, dentro da faixa esperada de 225-300 chunks.
- Throughput real da sessao: 148 chunks novos processados, 121 insights novos adicionados, 9 episodios fechados por chunk. API cost: `$0`; tempo operacional: 1 sessao Codex autonoma.
- Extracao R07 deve parar aqui ate o julgamento cego externo. A cobertura continua dos 50 episodios permanece em MSF-R14, com MSF-R03 a reabrir antes do backfill pos-gate.
- Decisao formal 2026-07-07: MSF-R07 fechado como `done` apos Gate R1 aprovado pelo juiz externo; cobertura restante passa a MSF-R14, com MSF-R03 a reabrir antes do backfill dos 508 chunks restantes.

### MSF-R08 - Comparacao amostral v1 vs v2

Prioridade: `P0`
Tipo: `qa`
Status: `done`

Escopo:

- Amostrar 40 pares comparaveis (mesmo episodio/chunk) entre v1 e v2.
- Avaliar cada par nos criterios da quality review: especificidade da tese, fidelidade a evidencia, aplicabilidade operacional, limpeza de quote.
- Gerar `docs/insight-v1-vs-v2-review-<data>.md` no formato da review de 2026-07-04.
- Decidir formalmente: v2 substitui v1 como fonte para retrieval/strategy packs, ou v1 continua e a v2 precisa de nova iteracao de prompt.

Aceite:

- Documento de comparacao com veredito explicito e exemplos.
- Relatorio de score desanonimizado produzido; decisao formal de Gate R1 registrada no execution log somente apos as investigacoes pre-gate e aceite do owner.

Dependencias:

- MSF-R07.

Execucao parcial 2026-07-07:

- Criado `scripts/generate_insight_v1_v2_review.py` para gerar uma review pareada v1/v2 sem copiar quotes brutas para docs versionados.
- Corrigido em 2026-07-07: o primeiro harness automatico era tautologico, porque `criterion_winners` so podia retornar `v2` ou `tie` e usava campos auto-declarados do v2.
- O script agora prepara `data/exports/insight_v1_v2_blind_sample_<data>.csv` com ordem A/B randomizada e `data/exports/insight_v1_v2_blind_key_<data>.json` para desanonimizacao local posterior.
- O julgamento deve preencher `judgment_*` com `A`, `B` ou `tie` sem acesso aos rotulos; depois `--mode score` desanonimiza e computa v1/tie/v2.
- A limpeza de quote usa o mesmo detector de ruido para ambos os lados, sem aceitar `evidence_strength` ou `evidence_cleanliness` como prova a favor do v2.
- Gerado `docs/insight-v1-vs-v2-review-2026-07-07.md` como pendente de julgamento cego, com 8 pares piloto a partir dos 2 episodios v2 existentes.
- Gate R1 nao foi declarado; R08 completo continua bloqueado por MSF-R07 ate haver cobertura v2 na amostra emendada, cobertura completa de chunks nos episodios escolhidos e amostra de 40 pares comparaveis preparada para julgamento cego externo.
- Emenda 2026-07-07: quando a cobertura emendada do MSF-R07 for atingida, gerar a amostra cega de 40 pares com `--mode prepare` e parar. O julgamento cego permanece externo ao Codex.

Execucao 2026-07-07 - amostra cega preparada:

- Apos MSF-R07 atingir 15 episodios completos, gerada amostra cega de 40 pares com `scripts/generate_insight_v1_v2_review.py --mode prepare --date 2026-07-07 --seed 20260707 --sample-size 40 --target-pairs 40 --target-episodes 15`.
- Saidas locais ignoradas: `data/exports/insight_v1_v2_blind_sample_2026-07-07.csv` e `data/exports/insight_v1_v2_blind_key_2026-07-07.json`.
- `docs/insight-v1-vs-v2-review-2026-07-07.md` atualizado como pendente de julgamento cego externo.
- `--mode score` nao foi executado. Gate R1 fica pendente do juiz externo e da decisao formal do owner.

Execucao 2026-07-07 - julgamento cego pontuado e remediacao pre-gate:

- Julgamento cego externo concluido em `data/exports/insight_v1_v2_blind_sample_2026-07-07_judged.csv`: 40/40 pares e 160/160 celulas preenchidas.
- Rodado `scripts/generate_insight_v1_v2_review.py --mode score --judgments data/exports/insight_v1_v2_blind_sample_2026-07-07_judged.csv`; relatorio desanonimizado atualizado em `docs/insight-v1-vs-v2-review-2026-07-07.md`.
- Resultado por criterio: specificity `v2=24`, `tie=14`, `v1=2`; evidence_fidelity `v2=19`, `tie=10`, `v1=11`; applicability `v2=39`, `tie=1`, `v1=0`; quote_cleanliness `v2=4`, `tie=18`, `v1=18`.
- Ressalva registrada: applicability deve ser lido com desconto porque a divisao cega foi `A=21`, `B=18`, `tie=1` e o lado com campos operacionais vence quase por estrutura; specificity e evidence_fidelity sao os criterios decisivos.
- Investigacao obrigatoria confirmou duplicacao de `specific_takeaway` no batch 006, incluindo o cluster Bbh/JF2 apontado pelo juiz. A regressao veio de takeaways genericos reutilizados enquanto os titulos eram sufixados por capitulo.
- Batch 006 remediado nos `llm_v2_outputs` de origem e recombinado: Bbh/JF2 tiveram janelas de evidencia alargadas ou limpas, `qohJceyapS0-v2-0002` foi removido como pitch, `qj04cUeaRAw-v2-0001` foi reancorado em evidencia substantiva, e os takeaways repetidos restantes foram diferenciados.
- `scripts/audit_insights_v2_text.py` agora falha em `specific_takeaway` duplicado normalizado, alem de non-ASCII e `?` orfao; `scripts/generate_insight_v1_v2_review.py` ganhou padroes de ruido para pitch de imersao/treinamento, intro e `espero que voces gostem`.
- Validacao final: 15/15 arquivos v2 validos, `scripts/audit_insights_v2_text.py` passou em 261 arquivos, quote check passou em 207/207 evidencias com 0 noise hits, consolidacao reportou 207 insights v2 e 246 chunks completos.
- Gate R1 permaneceu nao declarado nessa etapa ate decisao formal do owner/juiz externo sobre o score e as remediacoes pre-gate.

Execucao 2026-07-07 - decisao formal Gate R1:

- Gate R1 declarado APROVADO pelo juiz externo em 2026-07-07, apos verificacao independente da remediacao do batch 006.
- Verificacao independente confirmou 0 `specific_takeaway` duplicados normalizados e janelas de evidencia corrigidas.
- Ressalvas do parecer registradas no relatorio: `quote_cleanliness` venceu para v1 no snapshot julgado e a causa foi remediada depois; `applicability` deve ser lida com desconto estrutural; placar e piso sao pre-remediacao; v1 venceu 11 celulas de fidelidade, sinal de instrumento honesto.
- MSF-R07 e MSF-R08 ficam `done`. Proxima sessao: EPIC R2 com MSF-R09 (avaliador LLM com rubrica e verificacao de fidelidade de citacoes), depois MSF-R10 (teste cego contra baseline sem base usando v2 como fonte; julgamento externo).

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
- Para servir a primeira leva do EPIC MSF-S, priorizar explicitamente as tags `process-construcao-oferta`, `process-copy-vsl`, `process-copy-anuncios`, `process-produto-low-ticket` e `process-quiz`, mais os modulos transversais `process-mecanismo-big-idea` e `process-prova-depoimentos`.
- Preencher os campos editoriais do schema v2: `canonical_title`, `when_to_use`, `when_not_to_use`, `claim_risk`, `editorial_score` com a regua 0-100 da review (evidencia 25, especificidade 25, aplicabilidade 20, portabilidade 15, novidade 10, limpeza 5).
- Preencher `process_tags` em todo `curated_insight` com ids validos `process-*` da taxonomia de processos; minimo 1 tag valida por insight curado, sem tag generica de fallback.
- Curadoria pode ser LLM-assistida, mas o lote inicial passa por revisao humana amostral (minimo 30 itens).

Aceite:

- `data/exports/curated_insights.json` com 100-150 itens validos.
- Cada item curado tem pelo menos 1 `process_tag` valida e referenciada no `taxonomy_seed.json`.
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
- Absorver a cobertura continua dos 50 episodios completos que deixou de ser requisito bloqueante do Gate R1 pela emenda de aceite do MSF-R07 em 2026-07-07.
- Antes do backfill pos-gate dos chunks restantes, reabrir MSF-R03 para reduzir risco de locks/permissoes do OneDrive.
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
- Incluir tabela de processos baseada nos ids `process-*` do `taxonomy_seed.json`, com FK a partir dos insights curados ou tabela de ligacao equivalente para tags multiprocessos.
- Reservar tabela/campos para anotacoes de outcome ligadas a insights usados em outputs, permitindo registrar resultado observado, contexto, fonte e data sem sobrescrever o insight original.
- Incluir `pgvector` para busca semantica de insights e evidencias (a busca por keywords degrada com a base crescendo).
- Importadores idempotentes a partir dos exports locais.
- RLS e politicas definidas antes de expor qualquer API, conforme Definition of Done do backlog mestre.

Aceite:

- Schema versionado em migrations.
- Tabela de processos e FKs/relacionamentos de `process_tags` cobertos por migration e import idempotente.
- Estrutura de outcome annotations versionada e ligada aos insights usados.
- Import dos exports v2 completo e idempotente.
- Uma query semantica real retornando insights com evidencia sem ler arquivos locais.

Dependencias:

- Gate R3 aprovado.

## 5. Resumo de prioridades para o Codex

Ordem de ataque sugerida, em sessoes:

1. Sessao 1: MSF-R01, MSF-R02, MSF-R04 (estabilizacao; R03 se sobrar tempo).
2. Sessao 2: MSF-R05, MSF-R06 (contrato v2 + pipeline LLM, piloto em 2 episodios) - done em 2026-07-07.
3. Sessao 3: MSF-R07 e MSF-R08 done; Gate R1 aprovado em 2026-07-07 apos julgamento cego externo e verificacao independente da remediacao do batch 006.
4. Sessao 4: MSF-R09, MSF-R10 (avaliacao honesta + teste cego; declarar gate R2).
5. Sessao 5: MSF-R11, MSF-R12, MSF-R13 (diversidade + curadoria + packs novos; declarar gate R3).
6. Depois: MSF-R14, MSF-R15, MSF-R16 conforme gates.

Regras permanentes durante a remediacao:

- Nao iniciar o backfill MSF-R14 dos 508 chunks restantes antes de reabrir MSF-R03 e concluir a sequencia R2 acordada.
- Nao citar os scores antigos 39/40 e 37/40 como prova de valor.
- Toda saida LLM validada contra schema antes de entrar na base.
- Atualizar `docs/execution-log.md` ao fim de cada sessao, como ja e pratica do projeto.
