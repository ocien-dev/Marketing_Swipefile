# Plano VTURB-TRANSCRIPT-BACKFILL-OPT-001

Estado: implementado; execucao ASR residual retomavel em andamento  
Base: `vturb-transcript-backfill-pilot-001-retrospective.md`  
Objetivo: reduzir wall-clock e repeticao sem enfraquecer integridade, ordem da
fila ou a exigencia de Chrome real antes do ASR.

## Metas

| Metrica | Baseline | Meta |
| --- | ---: | ---: |
| Falhas globais repetidas por video | 15 no piloto | 0 depois do primeiro probe |
| Chrome sem painel | 8,1 s/video no melhor lote | <= 5,0 s/video p50 |
| Perda de progresso por interrupcao | ate um lote inteiro | 0 videos concluídos |
| Promocao/validacao | < 1 s/video | manter < 1 s/video |
| Telemetria ASR | apenas rota total | 100% download/load/inference/validation |
| ASR quente | desconhecido | benchmark e ETA com erro <= 20% |
| Uso de LLM para transcrever | zero | manter zero |

## P0 - Capacidade e telemetria

### OPT-T01 - Capability preflight e circuit breaker

Implementar em `backfill_vturb_transcripts.py` um probe por run:

1. resolver executaveis nativos;
2. validar Node/CLI/engine;
3. abrir navegador e executar DOM read em pagina neutra;
4. classificar `path_mixed`, `node_engine`, `cli_protocol`, `browser_missing` e
   `system_library_missing`;
5. desabilitar a rota UI para todos os itens quando a causa for global.

Gate: teste prova que cinco itens geram um unico probe e zero tentativas UI
quando a capacidade falha.

### OPT-T02 - Timing canonico por fase

Adicionar `run_id`, `attempt_id`, `started_at`, `finished_at`, `duration_ms`,
`phase`, `cache_hit`, `bytes`, `media_seconds`, `segments`, `coverage` e
`error_class` ao ledger. Usar UTC entre processos e monotonic apenas dentro de
um processo.

Fases minimas: inventory, metadata, direct, browser_navigation,
description_expand, transcript_panel, browser_serialize, audio_download,
model_load, inference, validation, promotion e gold_rebuild.

Gate: soma das fases reconcilia com a rota em margem de 2% e nenhum evento fica
sem `run_id`.

### OPT-T03 - Corrigir a declaracao da rota headless

Remover o pin 0.0.60 como rota executavel. Escolher uma das alternativas apos
probe controlado:

- fornecer runtime Linux autocontido Node 22 + Chromium + bibliotecas no cache;
- anexar a um Chrome real suportado;
- manter headless desativado e usar o conector Chrome somente para verificacao.

Gate: uma captura real completa com ID, ordem e cobertura validos; caso
contrario, a rota permanece explicitamente `unavailable`.

## P1 - Chrome retomavel e eficiente

### OPT-T04 - Checkpoint atomico por video

Depois de cada video, gravar imediatamente:

- `<video_id>.json` quando capturado;
- JSONL com `captured`, `no_ui`, `failed` ou `retryable`;
- cursor e hash do manifesto;
- tempos de navegacao, descricao, painel e serializacao.

Na retomada, pular resultados cujo hash do catalogo e arquivo de staging
continuem validos.

Gate: interromper depois do terceiro item de uma wave de dez e provar que a
retomada inicia no quarto sem repetir os tres primeiros.

### OPT-T05 - Espera orientada a estado

Substituir o sleep fixo de 3,5 s por espera em um sinal especifico: heading do
video atual mais botao `...mais` ou descricao pronta. Remover reload default;
recarregar apenas em erro classificado como `retryable_loading`.

Gate: p50 <= 5,0 s para `no_ui`, zero falso negativo no conjunto de regressao
com `AqzF_M2mM04` e videos sem painel confirmados.

### OPT-T06 - Importacao WSL por wave

Importar todos os arquivos Chrome de uma wave em uma unica invocacao WSL,
validar individualmente e promover em ordem de prioridade. Um arquivo invalido
nao bloqueia os demais, mas nunca muda a ordem de selecao gold.

Gate: wave mista com captura valida, ID divergente, stale tail e ausencia;
somente a captura valida e promovida.

## P2 - Benchmark e pipeline ASR

### OPT-T07 - Benchmark quente de 10 minutos

Usar um audio ja em cache e medir separadamente:

- load frio e load quente;
- inferencia de 10 min;
- real-time factor;
- memoria de pico;
- qualidade em trecho amostrado.

Comparar pelo menos `large-v3-turbo` CPU/int8 e uma alternativa menor aprovada.
A qualidade e gate: nomes, numeros e termos de marketing nao podem degradar de
forma material.

Gate: escolher configuracao com ETA do backlog e intervalo de confianca; nao
liberar full run sem essa decisao.

### OPT-T08 - Chunks retomaveis

Dividir audio longo em chunks de 20-30 min com pequena sobreposicao, salvar
receipt por chunk e reconciliar timestamps na montagem. Validar cobertura sem
duplicar texto na fronteira.

Gate: interrupcao no chunk 3 retoma no chunk 3; output final mantem ordem,
cobertura >= 98% e nenhuma fronteira duplicada.

### OPT-T09 - Reuso e prefetch controlado

Manter um processo ASR por wave para carregar o modelo uma vez. Enquanto o item
N transcreve, permitir download do N+1, mas persistir/promover somente na ordem
da fila. Limitar concorrencia de CPU para evitar oversubscription.

Gate: benchmark mostra ganho de wall-clock sem alterar a ordem dos receipts e
sem elevar falhas ou memoria acima do limite definido.

### OPT-T10 - ETA adaptativo

Depois de cada chunk, recalcular throughput quente por duracao e atualizar ETA
por prioridade/categoria. Nao usar o piloto frio de 90 s como taxa do backlog.

Gate: ETA final de uma wave difere no maximo 20% do observado.

## P3 - Integracao e rotina semanal

### OPT-T11 - Fechamento do backfill

Executar na ordem:

1. retomar os 113 itens Chrome ainda nao verificados;
2. importar capturas validas;
3. marcar ausencias reais;
4. executar ASR por waves retomaveis;
5. atingir 163/163 validos ou documentar bloqueio terminal por item;
6. reconstruir fila gold uma unica vez ao final;
7. validar fingerprints e contagens.

### OPT-T12 - Quarta-feira incremental

Depois da varredura dos cinco videos recentes:

1. adicionar somente IDs novos na fila classificada;
2. rodar direct com timeout curto;
3. usar o capability preflight uma vez;
4. verificar Chrome real quando necessario;
5. encaminhar ausencia confirmada ao ASR retomavel;
6. reconstruir gold apenas quando houver nova transcricao valida.

Gate: simulacao com cinco videos, dois novos, um com painel e um sem painel;
nenhum ID duplicado e ordem de prioridade preservada.

## Sequencia de implementacao

| Ordem | Stories | Dependencia | Saida |
| ---: | --- | --- | --- |
| 1 | T01-T03 | nenhuma | rotas com capacidade explicita e timing |
| 2 | T04-T06 | P0 | Chrome retomavel e importacao por wave |
| 3 | T07 | cache atual | modelo/compute type escolhidos |
| 4 | T08-T10 | T07 | ASR retomavel com ETA |
| 5 | T11 | P1 e P2 | catalogo concluido |
| 6 | T12 | T11 | rotina semanal integrada |

## Condicoes de parada

- divergencia de video ID, ordem ou fingerprint;
- duas rotas atomicas materialmente diferentes falhando no mesmo item;
- CAPTCHA, login ou permissao do Chrome que exija intervencao do usuario;
- cache/modelo sem espaco suficiente;
- benchmark de qualidade abaixo do gate;
- operacao de sistema que exija sudo, credencial ou mudanca irreversivel.

## Resultado de implementacao - 2026-07-16

| Bloco | Resultado |
| --- | --- |
| P0 | 24 testes Python e 3 testes Node verdes; um probe global; headless explicitamente `unavailable/system_library_missing` |
| P1 | 128 itens inspecionados no Chrome real; 94 capturas, 33 falhas terminais e 1 ausencia; 165 eventos atomicos; cursor final zero |
| P1 importacao | 94 capturas promovidas em 8 s; catalogo passou de 31 para 125 validos, depois 126 com a captura de regressao de `NiT0-ABoVnk` |
| P2 benchmark | `large-v3-turbo` RTF 0,6335; `small` reprovado por 40,19% de token recall e 50% de retencao de numeros |
| P2 batch | batch size 8 reprovado: token recall 67,98% e retencao de numeros 25% |
| P2 retomada | piloto de 120 s levou 76,1 s; repeticao reutilizou receipt e encerrou em 7,5 s |
| P3 piloto integral | `p78Zv3_WCsM` promovido com 998 segmentos e cobertura 99,78%; tres chunks em 1.571,3 s |
| Estado atual | 127/163 validos; 36 `pending_asr`; 94,42 h de midia; ETA quente aproximado de 42 h |
| P3 gold | corretamente adiado ate 163/163 ou bloqueios terminais documentados |
| P3 semanal | automacao `atualizar-epis-dios-vturb` atualizada para quarta-feira, scan dos cinco recentes e pipeline incremental completo |

A meta de p50 <= 5 s para `no_ui` nao foi atingida. O unico `no_ui` levou
11,5 s e o p50 global do Chrome foi 23,86 s; navegacao, expansao e abertura do
painel dominam o custo. A limitacao foi aceita porque remover esses estados
produziu falso negativo em `AqzF_M2mM04` e `NiT0-ABoVnk`.

Retomada canonica do residual, sempre no WSL e em ordem de prioridade:

~~~text
.venv/bin/python -m scripts.backfill_vturb_transcripts \
  --data-root /home/luish/msf-data/Marketing_Swipe_File \
  --routes asr --allow-asr --asr-model large-v3-turbo \
  --asr-chunk-seconds 1200 --asr-overlap-seconds 2
~~~
