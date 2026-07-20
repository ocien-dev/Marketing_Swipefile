# Retrospectiva VTURB-TRANSCRIPT-BACKFILL-OPT-001

Data: 2026-07-16  
Estado: implementacao concluida; residual ASR retomavel permanece em execucao longa

## Resultado executivo

- catalogo: 163 videos;
- transcricoes validas: 31 -> 127;
- Chrome real: 128 itens, 94 capturas, 33 falhas terminais e 1 ausencia;
- ASR integral: `p78Zv3_WCsM`, 998 segmentos, cobertura 99,78%;
- residual: 36 episodios, 94,42 h de midia;
- gold: nao reconstruido, corretamente, porque o gate final ainda nao foi atingido;
- rotina semanal: automacao `atualizar-epis-dios-vturb` ativa nas quartas, 9h,
  com scan limitado aos cinco videos recentes.

## Tempos por etapa

| Etapa | Tempo/volume | Observacao |
| --- | ---: | --- |
| Preflight WSL | < 1 s no verificador | status pass, paths Linux-native |
| Probe headless real | 15,2 s | `system_library_missing`; circuit breaker aberto |
| Testes finais | 24 Python em 0,18 s; 3 Node em 0,13 s | todos verdes |
| Chrome principal | 75,1 min wall-clock | 165 tentativas; zero perda de checkpoint |
| Chrome p50 total | 23,86 s/video | p95 35,45 s |
| Navegacao Chrome | p50 9,08 s | soma 1.109,2 s |
| Expansao da descricao | p50 5,57 s | soma 727,9 s |
| Abertura do painel | p50 8,61 s | soma 1.302,4 s |
| Serializacao Chrome | p50 15,8 ms | 94 capturas, 28,21 MiB |
| Importacao WSL | 8,0 s | 94 capturas promovidas individualmente |
| Benchmark padrao 10 min | 380,1 s de inferencia | RTF 0,6335 |
| Benchmark `small` | 247,8 s | reprovado no gate literal |
| Benchmark batch 8 | 273,4 s + 9,4 s decode | reprovado no gate literal |
| Piloto ASR 120 s | 76,1 s | receipt valido; repeticao em 7,5 s |
| ASR integral p78 | 1.571,3 s | tres chunks; 58,6 min de midia |

## Gates e desvios

Passaram: probe global unico, circuit breaker, checkpoints atomicos, retomada,
manifest hash, ID atual, monotonicidade, importacao mista, chunks, overlap,
reuso de receipt, modelo unico por processo, ETA e rotina incremental.

A meta Chrome de p50 <= 5 s nao passou. O unico `no_ui` levou 11,5 s e o p50
global foi 23,86 s. A maior parte e custo inevitavel de navegacao/scroll/painel
na sessao real. Tentar remover essas esperas gerou falsos negativos nos videos
`AqzF_M2mM04` e `NiT0-ABoVnk`; por isso a latencia foi aceita.

O gate 163/163 ainda nao passou. O benchmark demonstrou que concluir o residual
com a qualidade aprovada demanda aproximadamente 42 horas de CPU no hardware
atual. Nao ha `nvidia-smi` no WSL. O residual permanece seguro e retomavel, sem
runner persistente, heartbeat ou automacao de autocontinuacao.

## Qualidade do benchmark

| Configuracao | RTF | Token recall | Numeros | Termos marketing | Decisao |
| --- | ---: | ---: | ---: | ---: | --- |
| large-v3-turbo padrao | 0,6335 | 100% | 100% | 100% | aprovado |
| small | 0,4130 | 40,19% | 50% | 66,67% | rejeitado |
| large-v3-turbo batch 8 | 0,4557 | 67,98% | 25% | 100% | rejeitado |

## Retomada

Executar no clone Linux, sem `--video-id`, preserva a ordem global e reutiliza
todos os receipts validos:

~~~text
.venv/bin/python -m scripts.backfill_vturb_transcripts \
  --data-root /home/luish/msf-data/Marketing_Swipe_File \
  --routes asr --allow-asr --asr-model large-v3-turbo \
  --asr-chunk-seconds 1200 --asr-overlap-seconds 2
~~~

Depois de 163/163 ou de bloqueios terminais documentados, reconstruir a fila
gold uma unica vez, validar fingerprints e contagens e somente entao fechar P3.
