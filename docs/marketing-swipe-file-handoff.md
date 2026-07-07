# Marketing Swipe File - Handoff

Este documento e o ponto de retomada para continuar o projeto em outro chat do Codex sem depender do historico da conversa.

## Objetivo Do Projeto

Marketing Swipe File e um sistema Codex-first para transformar podcasts de negocios digitais em inteligencia acionavel de marketing de resposta direta.

Fontes priorizadas:

1. VTurb.
2. KiwiCast.
3. Hotmart Cast.
4. Fontes derivadas descobertas depois.

Uso principal:

- Agentes de IA consultando a base para gerar estrategias, VSLs, anuncios, quizzes, ofertas, funis e outputs operacionais.
- Consulta manual depois, inicialmente sem UI sofisticada.

Principio de execucao:

1. Scripts locais e contratos.
2. Prompts.
3. Skills Codex.
4. Loops Codex.
5. Supabase.
6. MCP.
7. Agentes especializados.
8. UI e automacao.

Nao criar agentes autonomos antes dos scripts, prompts, skills e loops estarem validados em episodios reais.

## Docs Canonicos

Leia nesta ordem:

1. `README.md`
2. `docs/marketing-swipe-file-prd.md`
3. `docs/marketing-swipe-file-architecture.md`
4. `docs/marketing-swipe-file-full-backlog.md`
5. `docs/marketing-swipe-file-remediation-backlog.md`
6. `docs/execution-log.md`
7. `docs/asset-acquisition-procedure.md`
8. `docs/insight-quality-checklist.md`
9. `docs/output-evaluation-rubric.md`

## Estado Atual Em 2026-07-07

Ja existe um MVP local operavel em arquivos:

- Estrutura do projeto.
- Schemas JSON.
- Taxonomia seed.
- Fixtures.
- Coleta de metadata do YouTube.
- Coleta direta de transcript quando o endpoint responde.
- Fallback Playwright DOM-first para transcript visivel na UI do YouTube.
- Normalizacao de transcript em segmentos.
- Deteccao de materiais complementares.
- Registro e processamento de assets locais.
- Processamento de PDF, DOCX, XLSX, PPTX, CSV, TXT, Markdown e HTML simples.
- Prompts base e especializados de extracao.
- Preparacao de extraction packets.
- Chunking por capitulos para episodios longos.
- Preparacao em lote de extraction packets por chunk.
- Auditoria local de insights.
- Extracao heuristica de insights profundos a partir dos chunks de transcricao.
- Dedupe local, classificacao taxonomica, resumos, master exports, busca, strategy packs e avaliacao de outputs.
- Transcricao de videos e aulas VTurb Academy por MP4/Drive e HLS.
- Ambiente Python proprio do projeto em `.venv`, com dependencias em `requirements.txt`.
- Contrato `raw_insights_v2` e piloto Codex-first de MSF-R05/MSF-R06.
- Consolidacao e review piloto para MSF-R07/MSF-R08, ainda sem Gate R1 declarado.
- 7 skills Codex locais.
- 5 loops operacionais locais.

Importante: a base ja saiu do nivel de candidatos de descricao e atingiu o gate local de escala solicitado. Em 2026-07-07, `.\.venv\Scripts\python.exe scripts\run_episode_batch.py --target-complete 50 --status-only` valida 160 URLs listadas, 50 videos completos, 50 com transcript e 50 com chunks. Os exports consolidados atuais tem 253 registros de episodios, 46 assets, 1.406 insights e 13 tarefas de aquisicao. MSF-R05/MSF-R06 tambem estao feitos em piloto local: `mCaFyZpXJdE` e `TOW0sWhPaZw` possuem `insights_v2.json` validos e ignorados em `data/processed/**`, com 4 insights v2 cada. MSF-R07 agora gera `data/exports/insights_v2_master.json`, `insights_v2_status.json`, `insights_v2_episode_status.csv` e `insights_v2_title_distribution.csv`, mas a cobertura ainda e 2/50 episodios alvo. MSF-R08 tem uma review piloto em `docs/insight-v1-vs-v2-review-2026-07-07.md`; Gate R1 nao foi declarado. Antes de usar como base final de producao, siga o backlog de remediacao: nao escalar novos episodios nem iniciar Supabase/MCP antes dos gates R1 e R2.

## Lote VTurb

Lista em `data/input/youtube_urls.csv`:

- 160 URLs VTurb listadas.
- 96 episodios com metadata coletada.
- 50 episodios com transcript, segmentos, chunks e insights.
- 110 episodios ainda sem o gate completo; destes, varios tem metadata mas seguem bloqueados ou ainda nao tentados em transcript.

Bloqueados em transcript ja observados entre os primeiros lotes:

- `YfI0CjI_XaE`
- `Rz1Y7fhXGFI`
- `0DlzYLUmKcU`
- `wJincuVXxxc`
- `FV-KR1eEbCw`
- `sVUrU9gvxyk`

Artefatos de prova:

- `data/exports/strategy_pack_vsl.md`
- `data/exports/strategy_pack_ads.md`
- `data/exports/generated_vsl_lowticket.md`
- `data/exports/generated_ads_lowticket.md`
- `data/exports/generated_vsl_lowticket_evaluation.md`: 39/40, `pass`.
- `data/exports/generated_ads_lowticket_evaluation.md`: 37/40, `pass`.
- `data/exports/acquisition_tasks_master.csv`: 13 tarefas de materiais complementares.

- `data/raw/**`, `data/processed/**`, `data/input/youtube_urls.csv` e assets locais sao ignorados pelo Git por politica de dados. Eles existem localmente nesta maquina, mas nao devem ser assumidos como versionados.
- `data/input/academy_video_transcription_queue.csv` e `data/input/youtube_urls_academy_new.csv` sao filas leves rastreaveis; exports `vturb_academy_*` continuam locais em `data/exports/**`.

## Scripts Principais

Coleta e normalizacao:

- `scripts/collect_youtube_metadata.py`
- `scripts/collect_youtube_transcript.py`
- `scripts/collect_youtube_transcript_from_playwright_snapshot.py`
- `scripts/capture_youtube_transcript_with_playwright_cli.py`
- `scripts/discover_vturb_youtube_videos.py`
- `scripts/normalize_transcript.py`
- `scripts/create_extraction_chunks.py`
- `scripts/run_episode_pipeline.py`
- `scripts/run_episode_batch.py`
- `scripts/transcribe_academy_videos.py`
- `scripts/transcribe_academy_hls.py`

Materiais complementares:

- `scripts/detect_assets.py`
- `scripts/register_assets.py`
- `scripts/process_asset.py`
- `scripts/run_asset_pipeline.py`

Extracao e qualidade:

- `scripts/prepare_extraction_packet.py`
- `scripts/prepare_chunked_extraction_packets.py`
- `scripts/extract_description_insights.py`
- `scripts/extract_transcript_insights.py`
- `scripts/extract_transcript_insights_llm.py`
- `scripts/validate_insights_v2.py`
- `scripts/classify_taxonomy.py`
- `scripts/dedupe_insights.py`
- `scripts/audit_insights.py`
- `scripts/generate_summaries.py`

Busca e outputs:

- `scripts/consolidate_exports.py`
- `scripts/search_insights.py`
- `scripts/generate_strategy_pack.py`
- `scripts/evaluate_output.py`

Helpers:

- `scripts/msf_common.py`
- `scripts/youtube_common.py`

## Prompts De Extracao

Base:

- `prompts/extraction/base_insight_extraction.md`

Especializados:

- `prompts/extraction/vsl_extractor.md`
- `prompts/extraction/ads_extractor.md`
- `prompts/extraction/offer_extractor.md`
- `prompts/extraction/funnel_extractor.md`
- `prompts/extraction/copy_extractor.md`
- `prompts/extraction/ops_extractor.md`
- `prompts/extraction/asset_extractor.md`
- `prompts/extraction/base_insight_extraction_v2.md`

Retrieval:

- `prompts/retrieval/strategy_pack_retrieval.md`

## Skills Codex

- `skills/marketing-swipe-file-ingest/`
- `skills/marketing-swipe-file-detect-assets/`
- `skills/marketing-swipe-file-process-assets/`
- `skills/marketing-swipe-file-extract-insights/`
- `skills/marketing-swipe-file-retrieve/`
- `skills/marketing-swipe-file-quality-review/`
- `skills/marketing-swipe-file-scale-batch/`

## Loops Operacionais

- `loops/episode-processing.md`
- `loops/asset-processing.md`
- `loops/strategy-pack.md`
- `loops/output-evaluation.md`
- `loops/batch-scaling.md`

## Como Retomar No Proximo Chat

Comece com este briefing:

```text
Estou no projeto Marketing Swipe File em C:\Users\luish\OneDrive\Code\Marketing_Swipe_File.
Leia docs/marketing-swipe-file-handoff.md, README.md, docs/execution-log.md e docs/marketing-swipe-file-full-backlog.md.
Continue a partir da remediacao local: MSF-R05/MSF-R06 ja criaram o contrato `raw_insights_v2` e um piloto Codex-first em 2 episodios. MSF-R07/MSF-R08 ja tem consolidacao v2 e review piloto, mas Gate R1 nao foi declarado porque a cobertura v2 ainda e 2/50 episodios alvo. Nao escale novos episodios nem inicie Supabase/MCP antes dos gates R1/R2. O proximo passo e extrair v2 real nos episodios alvo restantes, rodar `scripts/consolidate_exports.py`, revisar `data/exports/insights_v2_status.json` e so entao refazer a comparacao v1/v2.
```

Use este Python local, porque `python` pode nao estar no PATH:

```powershell
.\.venv\Scripts\python.exe
```

Validacao rapida:

```powershell
@'
from pathlib import Path
import json
root = Path('.')
json_paths = list(root.glob('schemas/*.json')) + list(root.glob('data/**/*.json'))
for path in json_paths:
    with path.open('r', encoding='utf-8') as f:
        json.load(f)
print(f'Parsed {len(json_paths)} JSON files')
script_paths = sorted(root.glob('scripts/*.py'))
for path in script_paths:
    source = path.read_text(encoding='utf-8')
    compile(source, str(path), 'exec')
print(f'Compiled {len(script_paths)} Python scripts in memory')
'@ | & .\.venv\Scripts\python.exe -
```

Conferir status do lote:

```powershell
@'
from pathlib import Path
import csv
import json
root = Path('.')
rows = list(csv.DictReader((root / 'data/input/youtube_urls.csv').open(encoding='utf-8-sig')))
processed_count = 0
blocked = 0
transcript_insights = 0
for row in rows:
    video_id = row['youtube_url'].split('v=')[-1].split('&')[0]
    raw = root / 'data/raw/youtube' / video_id
    processed_dir = root / 'data/processed' / video_id
    transcript_count = 0
    if (raw / 'transcript_original.json').exists():
        transcript = json.loads((raw / 'transcript_original.json').read_text(encoding='utf-8'))
        transcript_count = len(transcript.get('segments', []))
    chunk_count = 0
    if (processed_dir / 'chunks/chunk_index.json').exists():
        chunks = json.loads((processed_dir / 'chunks/chunk_index.json').read_text(encoding='utf-8'))
        chunk_count = len(chunks.get('chunks', []))
    insight_count = 0
    if (processed_dir / 'description_insights.json').exists():
        insights = json.loads((processed_dir / 'description_insights.json').read_text(encoding='utf-8'))
        insight_count = len(insights.get('insights', []))
    transcript_insight_count = 0
    if (processed_dir / 'insights.json').exists():
        insights = json.loads((processed_dir / 'insights.json').read_text(encoding='utf-8'))
        transcript_insight_count = len(insights.get('insights', []))
    if transcript_count and chunk_count:
        processed_count += 1
        transcript_insights += transcript_insight_count
    else:
        blocked += 1
    print(video_id, 'segments', transcript_count, 'chunks', chunk_count, 'transcript_insights', transcript_insight_count, 'description_insights', insight_count)
print('processed_with_chunks', processed_count)
print('blocked_or_empty', blocked)
print('transcript_insights', transcript_insights)
'@ | & .\.venv\Scripts\python.exe -
```

Resultado esperado:

```text
processed_with_chunks 50
blocked_or_empty 110
transcript_insights 1198
```

## Playwright Fallback Para Transcricao

Quando `collect_youtube_transcript.py` gerar transcript vazio, mas a UI do YouTube tiver transcricao, use primeiro o capturador automatizado:

```powershell
.\.venv\Scripts\python.exe scripts\capture_youtube_transcript_with_playwright_cli.py --url https://www.youtube.com/watch?v=VIDEO_ID --output data\raw\youtube\VIDEO_ID\transcript_original.json
```

O capturador usa Playwright CLI via `npx`, expande a descricao, clica `Mostrar transcricao`, le os elementos DOM atuais (`transcript-segment-view-model`) e so cai para snapshot quando necessario. Em Windows, se `npx` precisar escrever no cache global do npm, rode com aprovacao fora do sandbox.

Fluxo manual legado, caso seja necessario:

1. Abrir o video com Playwright.
2. Expandir a descricao.
3. Clicar em `Mostrar transcricao`.
4. Gerar snapshot.
5. Extrair a transcricao do snapshot.

Comando de extracao a partir de snapshot ja capturado:

```powershell
.\.venv\Scripts\python.exe scripts\collect_youtube_transcript_from_playwright_snapshot.py --snapshot .playwright-cli\page-YYYY-MM-DDTHH-MM-SS.yml --metadata data\raw\youtube\VIDEO_ID\metadata.json --output data\raw\youtube\VIDEO_ID\transcript_original.json
```

Depois:

```powershell
.\.venv\Scripts\python.exe scripts\normalize_transcript.py --input data\raw\youtube\VIDEO_ID\transcript_original.json --output data\processed\VIDEO_ID\content_segments.json
```

## Pipeline Para Novo Episodio

```powershell
.\.venv\Scripts\python.exe scripts\run_episode_pipeline.py --url <youtube_url>
```

Processar por video_id ja coletado:

```powershell
.\.venv\Scripts\python.exe scripts\run_episode_pipeline.py --video-id <video_id>
```

Se o transcript direto falhar, usar o fallback Playwright descrito acima e depois rerodar:

```powershell
.\.venv\Scripts\python.exe scripts\run_episode_pipeline.py --video-id VIDEO_ID --skip-metadata --skip-transcript
```

## Pipeline De Escala Em Lote

```powershell
.\.venv\Scripts\python.exe scripts\discover_vturb_youtube_videos.py --append --append-limit 100
.\.venv\Scripts\python.exe scripts\run_episode_batch.py --target-complete 50 --use-playwright-fallback
.\.venv\Scripts\python.exe scripts\consolidate_exports.py
```

Use `--start-priority` para pular blocos ja tentados e `--max-attempts` para rodar em ciclos controlados.

## Proximos Passos Recomendados

Prioridade imediata:

1. Executar MSF-R07: rodar o fluxo v2 nos 50 episodios completos e gerar `data/exports/insights_v2_master.json`.
2. Reexecutar `scripts/consolidate_exports.py` e conferir `data/exports/insights_v2_status.json`; o Gate R1 so pode ser avaliado quando a cobertura chegar a 50/50.
3. Executar MSF-R08 completo: comparar amostra pareada de 40 itens v1 vs v2 e declarar o gate R1.
4. Depois seguir para MSF-R09/MSF-R10: avaliacao honesta e teste cego.
5. So depois voltar a escala, Supabase/MCP, triagem ampla de assets e ranking de strategy packs.

Segundo bloco:

1. Retentar videos bloqueados se for importante cobrir episodios especificos.
2. Melhorar a captura DOM para registrar automaticamente o motivo de falha por video.

## Itens Ainda Faltando

Para a Release 1 completa ainda faltam:

- Revisao humana amostral de insights de alto uso.
- Triage/obtencao dos materiais complementares pendentes.
- Retry posterior dos videos bloqueados, se forem estrategicamente importantes.
- Processamento de materiais complementares reais.
- MSF-D06: OCR/imagens com texto.
- Supabase ainda nao foi criado.
- MCP ainda nao foi criado.
- Agentes especializados ainda nao foram criados.

## Observacoes Tecnicas

- `python` nao deve ser assumido no PATH; use `.\.venv\Scripts\python.exe`.
- O Python antigo do cache do Codex e apenas fallback; o runtime oficial do projeto e o `.venv`.
- `.playwright-cli/` esta ignorado no Git porque contem snapshots locais.
- `.pip-tmp/`, `.tmp/`, `.codex_deps/` e `.venv/` sao artefatos locais ignorados.
- Pacotes completos por episodio ficam grandes demais. Preferir sempre os packets chunkados.
- Dados brutos e processados sao locais e podem conter material privado/copyrighted; manter ignorados por Git.
- Se houver arquivo `transcript_fallback_needed.md` em um episodio ja processado, confira antes os arquivos `transcript_original.json`, `content_segments.json` e `chunks/chunk_index.json`; alguns marcadores antigos podem ter ficado presos por permissao do OneDrive.
