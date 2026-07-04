# Backlog - MVP do Marketing Swipe File

## 1. Objetivo do MVP

Processar 20 episodios do VTurb, detectar materiais complementares mencionados, extrair insights acionaveis em nivel estrategico, tatico e operacional, e provar que a base melhora a capacidade dos agentes de criar:

- uma copy de VSL completa;
- 3 variacoes de lead;
- anuncios baseados nos insights extraidos;
- referencias de VSL encontradas pela propria base;
- alertas sobre PDFs, docs, planilhas, templates ou swipes que precisam ser obtidos manualmente.

## 2. Marco 0 - Preparacao

### M0.1 Criar estrutura de pastas

Criar:

```text
data/input/
data/input/assets/
data/raw/youtube/
data/raw/assets/
data/processed/
data/processed/assets/
data/exports/
data/logs/
prompts/extraction/
prompts/retrieval/
prompts/assets/
scripts/
skills/
loops/
docs/
```

Aceite:

- Pastas existem.
- README explica fluxo MVP do Marketing Swipe File.

### M0.2 Criar lista inicial de episodios

Criar `data/input/youtube_urls.csv`.

Campos:

- `source_priority`
- `channel_name`
- `youtube_url`
- `episode_priority`
- `notes`

Aceite:

- Pelo menos 5 episodios piloto do VTurb cadastrados.
- Ordem de processamento clara.

### M0.3 Definir taxonomia seed

Criar `data/processed/taxonomy_seed.json`.

Temas iniciais:

- anuncios
- criativos
- hooks
- VSL
- gestao
- ofertas
- estrategias
- trafego pago
- funil
- checkout
- escala
- produto
- copy
- prova social
- avatar
- preco
- retencao
- webinar
- quiz
- low ticket
- high ticket
- lancamento
- perpetuo
- framework
- template
- swipe
- planilha
- checklist

Aceite:

- Taxonomia possui temas, subtemas, tipos de fonte e papeis de agentes iniciais.

## 3. Marco 1 - Ingestao, transcricao e materiais complementares

### M1.1 Script de ingestao de metadados

Criar script que recebe URL e gera:

```text
data/raw/youtube/{video_id}/metadata.json
```

Campos minimos:

- video_id
- url
- channel_name
- title
- description
- duration
- published_at
- collected_at

Aceite:

- Script roda para 1 URL.
- Script nao duplica episodio ja coletado.

### M1.2 Script de coleta de transcricao do YouTube

Criar script que tenta obter transcricao automatica.

Saida:

```text
data/raw/youtube/{video_id}/transcript_original.json
```

Aceite:

- Preserva timestamps.
- Se nao houver transcricao, cria status `transcript_missing`.
- Nao apaga metadados.

### M1.3 Normalizador de transcricao

Criar script que gera:

```text
data/processed/{video_id}/content_segments.json
```

Campos:

- segment_id
- source_kind
- start_seconds
- end_seconds
- text_original
- language

Aceite:

- Segmentos com tamanho adequado para analise por agente.
- Ordem e timestamps preservados.

### M1.4 Detector de materiais complementares

Criar prompt/script que analisa descricao e transcricao para detectar:

- PDFs;
- docs;
- planilhas;
- slides;
- templates;
- prompts;
- swipes;
- checklists;
- areas de membros;
- instrucoes de comentario;
- instrucoes de direct;
- palavras-chave.

Saidas:

```text
data/processed/{video_id}/referenced_assets.json
data/processed/{video_id}/acquisition_tasks.json
```

Aceite:

- Cada material detectado possui trecho/timestamp de evidencia.
- Cada material que depende do usuario possui instrucao clara.
- Status inicial correto: `needs_user_action`, `download_public_file`, `unavailable` ou `discarded`.

### M1.5 Alerta de acao manual para o usuario

Gerar resumo dos materiais que precisam ser obtidos.

Saida:

```text
data/processed/{video_id}/manual_actions.md
```

Aceite:

- O arquivo diz exatamente o que o usuario precisa fazer.
- Inclui episodio, timestamp, trecho e procedimento sugerido.

## 4. Marco 2 - Processamento de arquivos complementares

### M2.1 Convencao para inserir arquivos obtidos

Definir que o usuario coloca arquivos em:

```text
data/input/assets/{video_id}/
```

Aceite:

- Documento explica como nomear arquivos.
- Arquivo pode ser vinculado a uma tarefa de aquisicao.

### M2.2 Processador de PDFs e documentos

Criar fluxo para extrair texto de:

- PDF;
- DOCX;
- Google Docs exportado;
- TXT/Markdown;
- HTML salvo.

Saida:

```text
data/processed/assets/{asset_id}/content_segments.json
```

Aceite:

- Segmentos preservam pagina/secao quando existir.
- Arquivo bruto e preservado.

### M2.3 Processador de planilhas

Criar fluxo para extrair estrutura de:

- XLSX;
- CSV;
- Google Sheets exportado.

Aceite:

- Preserva abas, headers e ranges relevantes.
- Detecta modelos, calculadoras, tabelas de oferta, funil ou criativos.

### M2.4 Processador de slides e imagens

Criar fluxo para extrair conteudo de:

- PPTX;
- Google Slides exportado;
- imagens com texto, se necessario.

Aceite:

- Preserva numero do slide ou referencia visual.
- Marca conteudo extraido com baixa confianca quando OCR for incerto.

## 5. Marco 3 - Extracao de insights

### M3.1 Prompt base de extracao

Criar `prompts/extraction/base_insight_extraction.md`.

Deve instruir o agente a extrair:

- insight atomico;
- nivel: estrategico, tatico ou operacional;
- tipo de insight;
- temas;
- aplicabilidade;
- evidencia;
- confianca;
- tipo de fonte: transcricao, descricao, comentario ou material complementar;
- possiveis relacoes;
- versao PT-BR quando o trecho original nao estiver em portugues.

Aceite:

- Prompt gera JSON valido.
- Cada insight exige evidencia.

### M3.2 Prompts especializados

Criar prompts:

```text
prompts/extraction/copy_extractor.md
prompts/extraction/vsl_extractor.md
prompts/extraction/ads_extractor.md
prompts/extraction/offer_extractor.md
prompts/extraction/funnel_extractor.md
prompts/extraction/ops_extractor.md
prompts/extraction/asset_extractor.md
```

Aceite:

- Cada prompt foca em um tipo de inteligencia.
- `asset_extractor.md` trata frameworks, templates, planilhas, checklists e copies completas.
- Todos usam o mesmo formato de saida.

### M3.3 Template de saida de insights

Definir schema JSON para:

```text
data/processed/{video_id}/insights.json
data/processed/assets/{asset_id}/insights.json
```

Campos minimos:

- insight_id
- episode_video_id
- asset_id
- source_kind
- title
- insight_original
- insight_ptbr
- level
- insight_type
- themes
- applicability
- evidence
- confidence_score
- source_agent
- dedupe_key

Aceite:

- Schema documentado.
- Insights podem ser importados depois para Supabase.

### M3.4 Processar 3 episodios piloto

Rodar pipeline em 3 episodios do VTurb.

Aceite:

- Pelo menos 75 insights no total.
- Evidencia presente em pelo menos 90% dos insights.
- Materiais complementares detectados quando mencionados.
- Taxonomia ajustada com aprendizados reais.

## 6. Marco 4 - Base consultavel local

### M4.1 Consolidar insights

Criar script que junta todos os `insights.json` em:

```text
data/exports/insights_master.json
data/exports/insights_master.csv
```

Aceite:

- Sem duplicatas obvias por `dedupe_key`.
- Inclui episodio, fonte e material complementar quando existir.

### M4.2 Consolidar fila de materiais

Criar export:

```text
data/exports/acquisition_tasks_master.csv
```

Aceite:

- Lista todos os materiais pendentes.
- Inclui instrucao de obtencao e prioridade.

### M4.3 Busca textual e por filtros

Criar script de busca local.

Filtros:

- tema
- nivel
- insight_type
- canal
- episodio
- source_kind
- asset_type
- aplicabilidade
- confianca minima

Aceite:

- Consulta por `VSL` retorna insights relevantes.
- Consulta por `hooks` retorna evidencias.
- Consulta por `source_kind=asset` retorna apenas materiais complementares.

### M4.4 Prompt de retrieval para agentes

Criar `prompts/retrieval/strategy_pack_retrieval.md`.

Entrada:

- tarefa
- produto
- avatar
- nicho
- ativo desejado

Saida:

- insights prioritarios
- evidencias
- frameworks
- materiais complementares relevantes
- riscos
- sugestoes de uso

Aceite:

- Um agente consegue montar pacote para VSL usando a base.

## 7. Marco 5 - Skills Codex

### M5.1 Criar skill de ingestao

Criar skill `marketing-swipe-file-ingest`.

Responsabilidade:

- Processar URLs.
- Coletar metadados.
- Coletar transcricao.
- Preparar artefatos iniciais.

Aceite:

- Skill possui `SKILL.md` enxuto.
- Usa scripts quando houver operacao deterministica.
- Foi testada em pelo menos 1 episodio.

### M5.2 Criar skill de deteccao de materiais

Criar skill `marketing-swipe-file-detect-assets`.

Responsabilidade:

- Detectar materiais complementares.
- Criar `referenced_assets.json`.
- Criar `acquisition_tasks.json`.
- Gerar `manual_actions.md`.

Aceite:

- Detecta pelo menos um caso simulado de PDF por keyword/direct.
- Nao inventa arquivo quando nao ha evidencia.

### M5.3 Criar skill de processamento de assets

Criar skill `marketing-swipe-file-process-assets`.

Responsabilidade:

- Processar PDF, DOCX, XLSX, CSV, PPTX e HTML salvo.
- Gerar segmentos normalizados.

Aceite:

- Processa pelo menos um arquivo de teste.
- Mantem evidencia por pagina, aba, celula ou slide.

### M5.4 Criar skill de extracao e retrieval

Criar skills:

- `marketing-swipe-file-extract-insights`
- `marketing-swipe-file-retrieve`
- `marketing-swipe-file-quality-review`

Aceite:

- Cada skill tem fronteira clara.
- Cada skill foi validada antes de ser usada em loop.

## 8. Marco 6 - Loops Codex

### M6.1 Loop de processamento de episodio

Compor:

1. `marketing-swipe-file-ingest`
2. `marketing-swipe-file-detect-assets`
3. `marketing-swipe-file-extract-insights`
4. `marketing-swipe-file-quality-review`

Aceite:

- Roda em episodio piloto.
- Produz logs.
- Produz insights e tarefas manuais.

### M6.2 Loop de processamento de material complementar

Compor:

1. `marketing-swipe-file-process-assets`
2. `marketing-swipe-file-extract-insights`
3. `marketing-swipe-file-quality-review`

Aceite:

- Roda em arquivo obtido pelo usuario.
- Produz insights vinculados ao episodio.

### M6.3 Loop de criacao de output

Compor:

1. `marketing-swipe-file-retrieve`
2. agente de VSL ou anuncios
3. registro de insights usados
4. avaliacao de qualidade

Aceite:

- Output final lista referencias usadas.
- Avaliacao compara output com e sem base.

## 9. Marco 7 - Primeiro teste de valor

### M7.1 Processar 20 episodios VTurb

Aceite:

- 20 episodios processados.
- Pelo menos 500 insights atomicos.
- Materiais complementares detectados e status atribuidos.
- Pelo menos 90% dos insights usados em outputs com evidencia.

### M7.2 Criar VSL com base na inteligencia

Usar agente de VSL para criar:

- estrategia;
- VSL completa;
- 3 variacoes de lead;
- lista de referencias usadas.

Aceite:

- Output referencia insights por id.
- Leads sao avaliados por clareza, curiosidade, promessa, mecanismo e fit.

### M7.3 Criar anuncios com base na inteligencia

Usar agente de anuncios para criar:

- 10 hooks;
- 10 scripts curtos;
- 5 briefings de imagem/video;
- hipoteses de teste.

Aceite:

- Cada anuncio possui justificativa estrategica.
- Cada justificativa referencia insights da base.

## 10. Marco 8 - Supabase

### M8.1 Criar projeto Supabase

Criar novo projeto Supabase para o Marketing Swipe File.

Aceite:

- Projeto criado.
- Variaveis de ambiente documentadas localmente.
- Nenhuma chave sensivel commitada.

### M8.2 Criar schema SQL

Tabelas:

- sources
- episodes
- referenced_assets
- acquisition_tasks
- assets
- content_segments
- insights
- insight_evidence
- taxonomy_terms
- insight_tags
- insight_relations
- generated_artifacts
- artifact_insights

Aceite:

- Migration criada.
- Chaves primarias e estrangeiras definidas.
- Indices minimos criados.
- RLS considerada antes de expor API.

### M8.3 Importador para Supabase

Criar script que importa `insights_master.json` e `acquisition_tasks_master.csv`.

Aceite:

- Importacao idempotente.
- Reexecucao nao duplica episodios, assets nem insights.
- Logs indicam inseridos, atualizados e ignorados.

### M8.4 Busca em Supabase

Criar consultas SQL ou RPCs para:

- buscar insights;
- buscar evidencias;
- buscar por episodio;
- buscar por material complementar;
- buscar por tema;
- montar strategy pack simples.

Aceite:

- Consultas retornam dados com evidencia.

## 11. Marco 9 - MCP

### M9.1 Definir contrato MCP

Ferramentas:

- `search_insights`
- `get_insight`
- `get_evidence`
- `search_episodes`
- `search_assets`
- `get_strategy_pack`
- `get_vsl_references`
- `get_ad_references`
- `record_artifact_usage`

Aceite:

- Contratos documentados com parametros e respostas.

### M9.2 Implementar MCP server

Criar server conectando ao Supabase.

Aceite:

- Agente externo consegue chamar `search_insights`.
- Resposta inclui evidencias.
- Erros retornam mensagens claras.

### M9.3 Testar com agentes consumidores

Testar:

- agente de VSL;
- agente de anuncios;
- agente CMO;
- agente gestor de projetos.

Aceite:

- Cada agente consegue recuperar contexto sem ler arquivos diretamente.

## 12. Definicao de pronto do MVP

O MVP esta pronto quando:

- 20 episodios VTurb foram processados.
- A base contem pelo menos 500 insights atomicos.
- Materiais complementares foram detectados e registrados.
- Pelo menos alguns arquivos obtidos foram processados, se existirem.
- Insights possuem fonte, episodio e evidencia.
- E possivel buscar por tema, fonte e tarefa.
- Um agente gera VSL completa com 3 leads usando referencias da base.
- Um agente gera anuncios usando referencias da base.
- Existe decisao clara sobre migrar para Supabase/MCP na fase seguinte.

## 13. Proximas tarefas imediatas para Codex

1. Criar estrutura de pastas do MVP.
2. Criar `youtube_urls.csv` com os primeiros episodios VTurb.
3. Implementar ingestao de metadados.
4. Implementar coleta de transcricao automatica.
5. Implementar detector de materiais complementares.
6. Criar formato de `manual_actions.md`.
7. Criar prompts de extracao.
8. Processar 3 episodios piloto.
9. Revisar qualidade dos insights.
10. Ajustar taxonomia.
11. Criar primeiras skills atomicas.
12. Processar ate 20 episodios.
13. Rodar teste de criacao de VSL e anuncios.

