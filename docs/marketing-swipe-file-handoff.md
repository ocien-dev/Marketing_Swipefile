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

1. `AGENTS.md`
2. `README.md`
3. `docs/agent-coordination.md`
4. `docs/coordination/msf-r20-codex-gate-migration.md`
5. `docs/marketing-swipe-file-prd.md`
6. `docs/marketing-swipe-file-architecture.md`
7. `docs/marketing-swipe-file-full-backlog.md`
8. `docs/marketing-swipe-file-remediation-backlog.md`
9. `docs/marketing-swipe-file-skills-backlog.md`
10. `docs/execution-log.md`
11. `docs/asset-acquisition-procedure.md`
12. `docs/insight-quality-checklist.md`
13. `docs/output-evaluation-rubric.md`

## Coordenacao E Gate MSF-R20

O R20 usa dois papeis: um worker executa dentro de ownership explicito e um
coordenador Codex separado planeja, audita, reproduz validacoes e decide o gate.
O worker nunca aprova o proprio output. A fila central e os docs de coordenacao
sao ownership exclusivo do coordenador.

O nome `awaiting_external_audit` permanece por compatibilidade e significa
externo a tarefa executora, nao externo ao Codex. Auditorias historicas do
Claude permanecem como provenance verdadeira. Auditorias futuras registram
thread, modelo, effort e rota do revisor Codex. Mesmo com gate verde, commit,
push, deploy, Supabase e consolidacao continuam proibidos sem liberacao do
owner.

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
- Consolidacao e review de MSF-R07/MSF-R08 com Gate R1 aprovado formalmente.
- 7 skills Codex locais.
- 5 loops operacionais locais.

Importante: Gate R1, Gate R2 e Gate R3 estao aprovados e registrados. Em 2026-07-07, MSF-R07 atingiu a cobertura emendada com 15 episodios completos e 246 chunks v2; MSF-R08 teve julgamento cego externo, remediacao do batch 006 e aprovacao formal do juiz externo. MSF-R09 tambem foi executado: `scripts/evaluate_output.py` agora separa `keyword_presence_check` do julgamento honesto, valida JSON por `schemas/output_evaluation.schema.json` e rebaixou os artefatos antigos para 30/40 `needs_revision` tanto em VSL quanto em ads. MSF-R10 foi julgado externamente e aprovado: `with_base_v2=14`, `baseline_no_base=0`, `tie=2`, com limitacao amostral de 1 briefing x 2 artefatos. MSF-R11/MSF-R12/MSF-R13 estao done; o owner manteve a amostra R12 conforme as indicacoes, e a revisao tecnica externa aprovou R3. MSF-S01/MSF-S02/MSF-S08 e a primeira leva de skills reais MSF-S03/MSF-S04/MSF-S05/MSF-S06/MSF-S07 estao done/approved. MSF-R03 tambem esta done: dados ignored/local-only sairam do OneDrive e vivem em `C:\MSF-data\Marketing_Swipe_File`. Nao iniciar backfill MSF-R14, Supabase, MCP ou agentes antes da ordem acordada; o proximo marco e MSF-R14 somente quando o owner mandar.

## Raiz De Dados Local

Scripts runtime leem e escrevem dados ignorados/local-only via `MSF_DATA_DIR`
quando a variavel existe; se nao existir, caem no `data/` local do repo:

```powershell
$env:MSF_DATA_DIR = "C:\MSF-data\Marketing_Swipe_File"
setx MSF_DATA_DIR "C:\MSF-data\Marketing_Swipe_File"
```

`data/processed/taxonomy_seed.json` fica como seed canonico rastreado no repo.
Nao criar junction para `data/`; a arvore mistura arquivos versionados e
artefatos ignorados. Apos MSF-R03, o repo `data/` deve conter 0 payload
ignored/local-only; apenas scaffolding tracked, filas leves tracked,
`taxonomy_seed.json` e artefatos S09 ja versionados permanecem no repo.

## Politica De Escrita Por Camada

Decisao do owner em 2026-07-07, motivada pela revisao da amostra R12 e pelo
bug corrigido no export do CSV de revisao:

- Camada interna: dados, ids, tags, titulos, takeaways, campos editoriais,
  docs do repo, playbooks internos e receitas de retrieval usam ASCII por
  transliteracao Unicode NFKD quando precisarem representar portugues sem
  acentos. Acento vira letra base (`variacao`, `contem`, `incrivel`). Nunca
  usar ASCII `errors=ignore` como delecao de caractere. Nao reescrever a base
  existente por causa desta regra; ela ja foi verificada como integra.
- Quotes de evidencia: sempre verbatim UTF-8 com acentos preservados, em
  qualquer arquivo. CSVs de revisao humana devem ser gravados como
  `utf-8-sig`.
- Outputs finais: VSL, anuncios, quizzes, emails, templates e exemplos de
  skill destinados a leitura humana devem sair em portugues com acentuacao
  completa e ortografia correta.
- Enforcement: o avaliador honesto de MSF-R09 deve reprovar qualidade quando
  um output final em pt-BR sai sem caracteres acentuados e com sinais de
  ASCII stripping ate correcao.
- Scans non-ASCII de repo ou lote se aplicam a camada interna. Eles nao devem
  conflitar com quotes verbatim nem com artefatos de output final em pt-BR
  pleno. A wordlist de delecao de acentos em `scripts/audit_insights_v2_text.py`
  vale para todo texto gerado como guarda permanente de regressao.

## Lote VTurb

Lista em runtime `input/youtube_urls.csv` sob `MSF_DATA_DIR`:

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
- `data/exports/generated_vsl_lowticket_evaluation.md`: score honesto 30/40, `needs_revision`; o 39/40 antigo era apenas proxy de keywords.
- `data/exports/generated_ads_lowticket_evaluation.md`: score honesto 30/40, `needs_revision`; o 37/40 antigo era apenas proxy de keywords.
- `data/exports/output_r10_blind_sample_2026-07-07.csv`: pacote cego R10 original.
- `data/exports/output_r10_blind_key_2026-07-07.json`: chave local ignorada do R10.
- `data/exports/output_r10_blind_sample_2026-07-07_judged.csv`: julgamento externo concluido.
- `docs/output-r10-blind-review-2026-07-07.md`: Gate R2 aprovado.
- `data/exports/curated_insights.json`: lote local R12 com 125 itens curados.
- `data/exports/curated_insights_owner_review_sample_2026-07-07.csv`: amostra de 30 itens para revisao humana do owner; regenerada em `utf-8-sig` com `evidence_quote` verbatim UTF-8 e decisoes do owner preservadas.
- `docs/curated-insights-r12-review-2026-07-07.md`: relatorio R12.
- `data/exports/strategy_pack_curated_vsl_lowticket_2026-07-07.json` e `data/exports/strategy_pack_curated_ads_lowticket_2026-07-07.json`: packs R13 a partir de curated.
- `docs/strategy-pack-r13-comparison-2026-07-07.md`: comparacao R13 e avaliacao honesta dos packs.
- `data/exports/acquisition_tasks_master.csv`: 13 tarefas de materiais complementares.

- `raw/**`, `processed/**`, `exports/**`, `logs/**`, `cache/**`, `input/youtube_urls.csv` e assets locais sao ignorados pelo Git por politica de dados quando estao sob a raiz runtime (`MSF_DATA_DIR` ou fallback repo `data/`). Eles existem localmente nesta maquina, mas nao devem ser assumidos como versionados.
- `data/input/academy_video_transcription_queue.csv` e `data/input/youtube_urls_academy_new.csv` sao filas leves rastreaveis no repo; exports `vturb_academy_*` continuam locais sob a raiz runtime.

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
- `scripts/create_process_skill.py`
- `scripts/validate_process_skill.py`
- `scripts/validate_transversal_modules.py`

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
Continue a partir do EPIC MSF-S: MSF-S01, MSF-S02 e MSF-S08 estao done. MSF-S08 aprovou os modulos transversais em skills/_modules/msf-transversal-copy/ e o relatorio de auditoria em docs/msf-s08-transversal-modules-review-2026-07-07.md. Proximo passo: MSF-S04, skill construcao-oferta, como primeira skill real. Nao inicie MSF-R14 backfill, Supabase ou MCP antes da ordem pos-R3 acordada; antes do backfill MSF-R14, reabra MSF-R03.
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
import sys
root = Path('.')
sys.path.insert(0, str(root / 'scripts'))
from msf_common import data_root
data = data_root()
json_paths = list(root.glob('schemas/*.json')) + list(data.glob('**/*.json'))
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
import sys
root = Path('.')
sys.path.insert(0, str(root / 'scripts'))
from msf_common import data_root
data = data_root()
rows = list(csv.DictReader((data / 'input/youtube_urls.csv').open(encoding='utf-8-sig')))
processed_count = 0
blocked = 0
transcript_insights = 0
for row in rows:
    video_id = row['youtube_url'].split('v=')[-1].split('&')[0]
    raw = data / 'raw/youtube' / video_id
    processed_dir = data / 'processed' / video_id
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

1. Instanciar MSF-S04, skill construcao-oferta, como primeira skill real da leva com `scripts/create_process_skill.py`.
2. Depois de S04 validar o pipeline skill -> retrieval -> rubrica -> teste cego, seguir S03 VSL, S05 anuncios, S06 low ticket e S07 quiz.
3. Incorporar as observacoes R3 nos proximos lotes: calibrar `editorial_score`, reescrever o titulo com sufixo `...em lateralizar`, e engordar `process-copy-anuncios` no backfill.
4. Antes do backfill MSF-R14 dos 508 chunks restantes, reabrir MSF-R03 como combinado.
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
- MSF-S01/MSF-S02/MSF-S08 estao done; MSF-S04 esta liberado como proxima skill real; MSF-S03/MSF-S05..S13 continuam pendentes/bloqueados por dependencias proprias.

## Observacoes Tecnicas

- `python` nao deve ser assumido no PATH; use `.\.venv\Scripts\python.exe`.
- O Python antigo do cache do Codex e apenas fallback; o runtime oficial do projeto e o `.venv`.
- `.playwright-cli/` esta ignorado no Git porque contem snapshots locais.
- `.pip-tmp/`, `.tmp/`, `.codex_deps/` e `.venv/` sao artefatos locais ignorados.
- Pacotes completos por episodio ficam grandes demais. Preferir sempre os packets chunkados.
- Dados brutos e processados sao locais e podem conter material privado/copyrighted; manter ignorados por Git.
- Se houver arquivo `transcript_fallback_needed.md` em um episodio ja processado, confira antes os arquivos `transcript_original.json`, `content_segments.json` e `chunks/chunk_index.json`; alguns marcadores antigos podem ter ficado presos por permissao do OneDrive.
