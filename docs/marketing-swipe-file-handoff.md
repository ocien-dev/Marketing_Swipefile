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
5. `docs/execution-log.md`
6. `docs/asset-acquisition-procedure.md`
7. `docs/insight-quality-checklist.md`

## Estado Atual

Ja existe uma fundacao local funcional:

- Estrutura do projeto.
- Schemas JSON.
- Taxonomia seed.
- Fixtures.
- Coleta de metadata do YouTube.
- Coleta direta de transcript quando o endpoint responde.
- Fallback Playwright para transcript visivel na UI do YouTube.
- Normalizacao de transcript em segmentos.
- Deteccao de materiais complementares.
- Registro e processamento de assets locais.
- Processamento de PDF, DOCX, XLSX, PPTX, CSV, TXT, Markdown e HTML simples.
- Prompts base e especializados de extracao.
- Preparacao de extraction packets.
- Chunking por capitulos para episodios longos.
- Preparacao em lote de extraction packets por chunk.
- Auditoria local de insights.

## Primeiro Episodio Piloto

Video:

```text
https://www.youtube.com/watch?v=mCaFyZpXJdE
```

Titulo:

```text
Low Ticket: Absolutamente Tudo Para Escalar 100K/Dia! | Davi, Kaue e Slender - SDE #159
```

Status local:

- Metadata coletada em `data/raw/youtube/mCaFyZpXJdE/metadata.json`.
- Endpoint direto de captions falhou/retornou vazio.
- Transcricao coletada pela UI do YouTube usando Playwright.
- Transcricao final salva em `data/raw/youtube/mCaFyZpXJdE/transcript_original.json`.
- 2,706 segmentos normalizados em `data/processed/mCaFyZpXJdE/content_segments.json`.
- 21 chunks criados em `data/processed/mCaFyZpXJdE/chunks/`.
- 126 packets chunkados gerados em `data/processed/mCaFyZpXJdE/chunked_extraction_packets/`.
- Nenhum material complementar acionavel foi detectado neste episodio depois da correcao contra falsos positivos.

Observacao importante:

- `data/raw/**`, `data/processed/**`, `data/input/youtube_urls.csv` e assets locais sao ignorados pelo Git por politica de dados. Eles existem localmente nesta maquina, mas nao devem ser assumidos como versionados.

## Scripts Principais

Coleta e normalizacao:

- `scripts/collect_youtube_metadata.py`
- `scripts/collect_youtube_transcript.py`
- `scripts/collect_youtube_transcript_from_playwright_snapshot.py`
- `scripts/normalize_transcript.py`
- `scripts/create_extraction_chunks.py`

Materiais complementares:

- `scripts/detect_assets.py`
- `scripts/register_assets.py`
- `scripts/process_asset.py`

Extracao e qualidade:

- `scripts/prepare_extraction_packet.py`
- `scripts/prepare_chunked_extraction_packets.py`
- `scripts/audit_insights.py`

Helpers:

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

## Como Retomar No Proximo Chat

Comece com este briefing:

```text
Estou no projeto Marketing Swipe File em C:\Users\luish\OneDrive\Code\Marketing_Swipe_File.
Leia docs/marketing-swipe-file-handoff.md, README.md, docs/execution-log.md e docs/marketing-swipe-file-full-backlog.md.
Continue a partir do episodio mCaFyZpXJdE. O proximo passo e extrair insights dos chunked extraction packets e consolidar os melhores insights para VSL, anuncios, oferta, funil, copy e operacao.
```

Use este Python local, porque `python` pode nao estar no PATH:

```powershell
& 'C:\Users\luish\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
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
'@ | & 'C:\Users\luish\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -
```

Conferir contagens do episodio piloto:

```powershell
@'
from pathlib import Path
import json
transcript = json.loads(Path('data/raw/youtube/mCaFyZpXJdE/transcript_original.json').read_text(encoding='utf-8'))
segments = json.loads(Path('data/processed/mCaFyZpXJdE/content_segments.json').read_text(encoding='utf-8'))
chunks = json.loads(Path('data/processed/mCaFyZpXJdE/chunks/chunk_index.json').read_text(encoding='utf-8'))
packet_count = len(list(Path('data/processed/mCaFyZpXJdE/chunked_extraction_packets').glob('*/*.md')))
print('transcript_segments', len(transcript['segments']))
print('content_segments', len(segments['segments']))
print('chunks', len(chunks['chunks']))
print('chunk_segments', sum(chunk['segment_count'] for chunk in chunks['chunks']))
print('largest_chunk_chars', max(chunk['char_count'] for chunk in chunks['chunks']))
print('chunked_packets', packet_count)
'@ | & 'C:\Users\luish\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -
```

Resultado esperado:

```text
transcript_segments 2706
content_segments 2706
chunks 21
chunk_segments 2706
largest_chunk_chars 49947
chunked_packets 126
```

## Playwright Fallback Para Transcricao

Quando `collect_youtube_transcript.py` gerar transcript vazio, mas a UI do YouTube tiver transcricao:

1. Abrir o video com Playwright.
2. Expandir a descricao.
3. Clicar em `Mostrar transcricao`.
4. Gerar snapshot.
5. Extrair a transcricao do snapshot.

Comando de extracao a partir de snapshot ja capturado:

```powershell
& 'C:\Users\luish\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\collect_youtube_transcript_from_playwright_snapshot.py --snapshot .playwright-cli\page-YYYY-MM-DDTHH-MM-SS.yml --metadata data\raw\youtube\VIDEO_ID\metadata.json --output data\raw\youtube\VIDEO_ID\transcript_original.json
```

Depois:

```powershell
& 'C:\Users\luish\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\normalize_transcript.py --input data\raw\youtube\VIDEO_ID\transcript_original.json --output data\processed\VIDEO_ID\content_segments.json
```

## Pipeline Para Novo Episodio

1. Adicionar URL em `data/input/youtube_urls.csv`.

2. Coletar metadata:

```powershell
& 'C:\Users\luish\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\collect_youtube_metadata.py --csv data\input\youtube_urls.csv --output-root data\raw\youtube
```

3. Coletar transcricao direta:

```powershell
& 'C:\Users\luish\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\collect_youtube_transcript.py --metadata data\raw\youtube\VIDEO_ID\metadata.json --output-root data\raw\youtube
```

4. Se falhar, usar o fallback Playwright descrito acima.

5. Normalizar transcript:

```powershell
& 'C:\Users\luish\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\normalize_transcript.py --input data\raw\youtube\VIDEO_ID\transcript_original.json --output data\processed\VIDEO_ID\content_segments.json
```

6. Criar chunks:

```powershell
& 'C:\Users\luish\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\create_extraction_chunks.py --segments data\processed\VIDEO_ID\content_segments.json --metadata data\raw\youtube\VIDEO_ID\metadata.json --output-dir data\processed\VIDEO_ID\chunks --max-chars 50000
```

7. Detectar materiais complementares:

```powershell
& 'C:\Users\luish\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\detect_assets.py --metadata data\raw\youtube\VIDEO_ID\metadata.json --segments data\processed\VIDEO_ID\content_segments.json --output-dir data\processed\VIDEO_ID
```

8. Gerar packets chunkados:

```powershell
& 'C:\Users\luish\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\prepare_chunked_extraction_packets.py --chunk-index data\processed\VIDEO_ID\chunks\chunk_index.json --metadata data\raw\youtube\VIDEO_ID\metadata.json --extractors vsl,ads,offer,funnel,copy,ops --output-dir data\processed\VIDEO_ID\chunked_extraction_packets --insights-dir data\processed\VIDEO_ID\chunked_insights
```

## Proximos Passos Recomendados

Prioridade imediata:

1. Criar um loop de extracao Codex para processar `chunked_extraction_packets`.
2. Comecar com `vsl`, `offer`, `funnel` e `ads`, porque sao os mais ligados ao objetivo do MVP.
3. Salvar outputs por chunk em `data/processed/mCaFyZpXJdE/chunked_insights/{extractor}/`.
4. Criar consolidacao local dos insights por episodio.
5. Implementar MSF-E04 deduplicacao local.
6. Implementar MSF-E05 classificacao taxonomica.
7. Implementar MSF-E06 resumo por episodio.
8. Depois criar a primeira skill Codex: `marketing-swipe-file-ingest-youtube`.

Segundo bloco:

1. Criar mais 4 URLs piloto do VTurb para fechar MSF-B01.
2. Rodar pipeline completo nos 5 episodios piloto.
3. Medir qualidade dos insights e ajustar prompts.
4. So depois disso iniciar Supabase/MCP.

## Itens Ainda Faltando

Backlog aberto de maior importancia:

- MSF-B01: lista inicial ainda so tem 1 episodio real; faltam pelo menos 4 para o aceite original.
- MSF-B05: logs estruturados de ingestao em `data/logs/`.
- MSF-C04: fila geral de materiais pendentes.
- MSF-C05: regras de valor esperado para materiais complementares.
- MSF-D06: OCR/imagens com texto.
- MSF-E04: deduplicacao local.
- MSF-E05: classificacao taxonomica.
- MSF-E06: resumo por episodio e asset.
- Skills Codex ainda nao foram criadas.
- Loops Codex ainda nao foram criados.
- Supabase ainda nao foi criado.
- MCP ainda nao foi criado.
- Agentes especializados ainda nao foram criados.

## Observacoes Tecnicas

- `python` nao deve ser assumido no PATH; use o Python completo listado acima.
- `git status` falhou neste workspace com `fatal: not a git repository`, apesar de existir contexto de projeto. Nao use status Git como fonte confiavel ate isso ser resolvido.
- `.playwright-cli/` esta ignorado no Git porque contem snapshots locais.
- Pacotes completos por episodio ficam grandes demais. Preferir sempre os packets chunkados.
- Dados brutos e processados sao locais e podem conter material privado/copyrighted; manter ignorados por Git.

