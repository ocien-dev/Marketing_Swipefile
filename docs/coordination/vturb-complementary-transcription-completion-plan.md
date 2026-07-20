# Plano de conclusao das transcricoes complementares VTurb

Data do inventario: 2026-07-16

## Estado reconciliado

O export `vturb_academy_video_transcription_queue.csv` possui 212 referencias,
mas referencias nao equivalem a videos unicos. Depois de reconciliar a fila com
o data root ativo no Ubuntu WSL:

| Grupo | Referencias | Midias unicas / estado real |
| --- | ---: | --- |
| Academy com HLS interno | 33 | 33 transcripts nao vazios |
| Videos do Drive marcados como transcritos | 123 | 123 transcripts nao vazios |
| Episodios do YouTube | 18 | 16 videos unicos com transcript; 7 estados do CSV estao desatualizados |
| Video do Drive com transcript vazio | 1 | 1 pendencia real |
| Videos grandes ignorados pelo limite antigo | 2 | 2 pendencias reais |
| Paginas Academy sem HLS | 16 | paginas de material, fora do denominador de video |
| Links/ativos externos sem video direto | 17 | triagem de asset, nao transcript confirmado |
| Arquivos do Drive classificados como nao-video | 2 | asset, nao transcript confirmado |

O universo confirmado e de 175 videos unicos: 172 possuem transcript nao vazio
e 3 ainda precisam de resolucao. Isso representa cobertura nominal de 98,3%.
Entretanto, as 156 transcricoes de Academy/Drive foram geradas por
`faster_whisper:tiny` (131 inteiras e 25 por chunks HLS). Elas devem ser
consideradas transcricoes operacionais antigas, nao fonte gold definitiva.

O volume ASR ja inventariado e de 33,94 horas: 29,06 h em 33 aulas HLS e
4,88 h em 123 videos do Drive. A cobertura temporal mediana e 99,5%, mas 15
midias ficam abaixo de 90% e 6 abaixo de 60%; a maioria e composta por anuncios
curtos, nos quais silencio e trechos apenas visuais precisam ser distinguidos de
falha de reconhecimento.

Idiomas das 172 midias unicas utilizaveis hoje:

- 71 em portugues;
- 98 em ingles;
- 3 em espanhol.

Nenhuma das 101 fontes em ingles/espanhol possui ainda `transcript_pt_br.json`.
O volume estrangeiro corresponde a aproximadamente 3,97 horas de midia.

## Pendencias reais de video

1. `AD 11.mp4` - 726.028.602 bytes - Drive
   `15eJLgQmCh7Y6mkroQ89f7IZQOBZ3SvxR`.
2. `Aula Desafio 6 Low em 30.mp4` - 3.008.864.224 bytes - Drive
   `1ImdSwJ_i9-4SQNgspmhhQzpD152WWW1f`.
3. `AD-SEXUALIDADE3.mp4` - 105,6 s - Drive
   `14WgYCX9kuzn7UAAP13rLwE-BUPYIb5xz`; possui faixa AAC valida, mas o ASR tiny
   gerou zero segmentos.

O WSL possui aproximadamente 941 GB livres, portanto os dois downloads grandes
cabem com ampla margem.

## Plano de execucao

## Estrategia de modelo e esforco

O plano deve ser executado por lanes, sem manter o modelo mais caro ativo em
etapas deterministicas:

| Lane | Modelo Codex | Esforco | Escopo |
| --- | --- | --- | --- |
| Especificacao, hardening e implementacao | `gpt-5.6-terra` | medium | downloader retomavel, manifests, checkpoints, scripts e testes |
| Inventario, download, `ffprobe`, checksums e execucao de scripts | `gpt-5.6-luna` | light | trabalho repetivel com criterios fechados; ASR roda localmente sem tokens do modelo |
| Triagem de anomalias e revisao de fronteiras | `gpt-5.6-terra` | medium | casos vazios, baixa cobertura, idioma duvidoso e falhas de merge |
| Traducao longa em lotes | `gpt-5.6-luna` | medium | primeira passagem estruturada com a skill `traducao-longa` |
| Revisao semantica de lotes sinalizados | `gpt-5.6-terra` | medium | nomes, numeros, negacoes, CTAs, termos e continuidades suspeitas |
| Auditoria final unica | `gpt-5.6-sol` | high | gate final obrigatorio do repositorio e findings residuais |

Nao usar Max ou Ultra neste epico: o trabalho e sequencial por midia, o
`AGENTS.md` proibe delegacao normal e a maior parte do tempo pertence a
download/ASR local, nao a raciocinio do modelo.

### P0 - Reconciliar fila e proteger provenance

1. Regenerar a fila a partir dos arquivos reais e converter os 7 estados
   `youtube_in_main_queue_pending_transcript` para concluido.
2. Deduplicar referencias por `transcription_media_id`, mantendo a relacao
   muitos-para-um com as aulas que apontam para o mesmo video.
3. Preservar cada transcript tiny existente como versao historica antes de
   promover uma nova transcricao.
4. Separar explicitamente `video`, `no_speech`, `material_page` e `asset` para
   que documentos e mapas mentais nao inflem a pendencia de transcricao.

### P1 - Tornar o pipeline de Drive seguro para arquivos grandes

1. Adicionar download retomavel, arquivo parcial, tamanho esperado, SHA-256 e
   receipt ao `transcribe_academy_videos.py`.
2. Elevar o limite apenas para os dois IDs conhecidos, sem remover o guardrail
   global.
3. Depois do download, executar `ffprobe` e procurar primeiro legenda embutida.
   Se houver faixa textual, extrai-la antes de usar ASR.
4. Quando nao houver legenda, extrair audio local com `ffmpeg`, dividir em
   chunks de aproximadamente 20 minutos e manter checkpoints por chunk.
5. Mesclar timestamps com offset, remover apenas sobreposicoes de fronteira e
   validar duracao, hash e cobertura antes da promocao.

### P2 - Corrigir primeiro os casos de maior risco

1. Reprocessar `AD-SEXUALIDADE3.mp4` com `large-v3-turbo`, deteccao de idioma e
   uma segunda passagem sem VAD agressivo.
2. Se continuar vazio, verificar audivelmente uma amostra e classificar como
   `no_speech_validated` quando o audio nao contiver fala inteligivel.
3. Reprocessar em seguida as 15 midias com cobertura abaixo de 90%, com foco nas
   6 abaixo de 60%.
4. Usar um gate especifico para anuncios: cobertura temporal baixa nao e falha
   quando os trechos restantes forem musica, silencio ou demonstracao visual.

### P3 - Substituir o ASR tiny por fonte de qualidade

1. Reprocessar as 33 aulas HLS (29,06 h) com `large-v3-turbo`, mantendo chunks
   de 20 minutos e a variante HLS de menor resolucao/bitrate suficiente.
2. Reprocessar os 123 videos do Drive (4,88 h) com o mesmo modelo.
3. Priorizar na ordem: vazios/baixa cobertura, aulas longas, demais anuncios.
4. Comparar tiny versus large por idioma, numeros, nomes, repeticoes,
   alucinacoes em silencio e timestamps; promover apenas a versao large que
   passar o gate.
5. Nao usar ASR nos 16 episodios unicos do YouTube, pois eles ja possuem
   transcript obtido da fonte de legendas.

### P4 - Traduzir com o Codex, nunca com o YouTube

1. Recalcular os idiomas depois da promocao das transcricoes large.
2. Invocar a skill `traducao-longa` como contrato obrigatorio da etapa.
3. Antes do primeiro lote de cada familia tematica, criar um glossario de nomes,
   marcas, termos tecnicos, siglas e decisoes de registro; versionar o glossario
   junto ao job.
4. Para cada fonte nao portuguesa, manter `transcript_original.json` e gerar
   `transcript_pt_br.json` com o fluxo de unidades temporais e lotes do
   `codex_translate_transcripts.py`.
5. Dividir apenas em unidades semanticas completas. Nunca cortar uma frase,
   turno de falante ou bloco de timestamp no meio.
6. Preservar literalmente indices, timestamps, falantes, URLs, numeros, valores,
   nomes de produto e marcadores como `[musica]` ou `[inaudivel]`.
7. Traduzir sem resumir, expandir ou inventar; em copy, preservar progressao
   persuasiva, mecanismo, prova, objecoes e CTA sem aumentar promessas.
8. Validar cobertura um-para-um, sequencia, continuidade entre lotes, nomes,
   numeros, unidades, negacoes, CTAs e consistencia do glossario.
9. Registrar `provider=codex:faithful_translation`, a versao da skill/glossario
   e o SHA-256 exato da fonte.
10. Fazer o pipeline gold preferir pt-BR, preservando a fonte original como
    provenance protegida.

### P5 - Triar o que nao e video

1. Manter as 16 paginas Academy sem HLS fora do denominador de transcricao.
2. Registrar como assets os artigos, playbooks, mapas mentais e PDFs ja
   identificados.
3. Reabrir apenas quatro rotas que ainda podem esconder video: a landing page
   do Curso Low Ticket, o link curto `livecriativoshigao`, a referencia do Slack
   e a pasta do Drive de Vinicius Greco.
4. Se alguma rota revelar nova midia, gerar ID canonico e inclui-la na mesma
   fila P1-P4; caso contrario, fechar como asset nao transcrivivel.

### P6 - Consolidar e validar

1. Reconstruir chunks e `content_segments.json` somente a partir da fonte
   promovida.
2. Atualizar a fila, os exports e o resumo de aquisicao da Academy.
3. Rodar extracao de insights, taxonomia, consolidacao e auditoria somente
   depois que as transcricoes estiverem seladas.
4. Gate final: todos os 175 videos unicos em `source_complete` ou
   `no_speech_validated`; zero `transcribed_empty`, zero `skipped_over_limit`,
   zero estados YouTube desatualizados e todas as fontes nao portuguesas com
   traducao Codex pt-BR vinculada por hash.

## Estimativa operacional

- Reconciliacao e hardening do downloader: 1-2 horas.
- Download dos 3,74 GB pendentes: dependente da rede, esperado entre 20 e 90
  minutos com retomada.
- Reprocessamento das 33,94 h ja conhecidas em `large-v3-turbo`: cerca de 15-18
  horas no runtime CPU atual, executado de forma desacompanhada e retomavel.
- Os dois videos grandes acrescentarao tempo conforme a duracao aferida pelo
  `ffprobe` depois do download.
- Traducao Codex: aproximadamente 3,97 h de fonte estrangeira, em lotes
  deterministas e retomaveis.

O caminho recomendado e uma execucao desacompanhada de um a dois dias, com
checkpoint por arquivo/chunk e sem consumo de tokens durante download, audio,
ASR e validacoes deterministicas. Tokens ficam concentrados somente na traducao
Codex e, depois, na extracao gold.
