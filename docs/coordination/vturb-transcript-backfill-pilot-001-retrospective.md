# Retrospectiva do backfill de transcricoes VTurb - piloto 001

Data: 2026-07-16  
Estado: piloto interrompido de forma segura para analise e otimizacao  
Escopo: catalogo publico VTurb, fila de 163 videos e rotas de obtencao de transcricao

## Resultado executivo

O piloto provou tres coisas:

1. a fila e o orquestrador retomavel funcionam sem LLM e preservam a ordem de
   prioridade;
2. o gate de integridade evitou promover vinte transcricoes contaminadas por
   segmentos de um painel anterior;
3. a rota de ASR local e viavel, mas ainda nao possui telemetria nem benchmark
   quente suficientes para liberar 355,77 horas de backlog com previsibilidade.

O estado confirmado ao interromper o lote e:

| Medida | Antes do piloto | Depois do piloto |
| --- | ---: | ---: |
| Videos no catalogo | 163 | 163 |
| Transcricoes validas | 30 | 31 |
| Videos pendentes | 133 | 132 |
| Duracao pendente | 356,64 h | 355,77 h |
| Confirmados no Chrome sem painel e marcados para ASR | 0 | 4 |
| Confirmados no Chrome sem painel, ainda apenas em staging | 0 | 15 |
| Manifesto ainda nao verificado no Chrome | - | 113 |

Uma transcricao foi promovida: `AqzF_M2mM04`, prioridade 1. Ela possui 395
segmentos, 64.343 caracteres, cobertura 99,78%, zero warning e SHA-256
`3104f36b557dc76749d578365ba29582027c1684ef9e76624881b2e5902f7338`.

Nenhuma transcricao ASR integral foi promovida. O piloto ASR de
`p78Zv3_WCsM` permaneceu corretamente como `pending_asr` porque cobria somente
os primeiros 90 segundos.

## O que foi construido

- `scripts/backfill_vturb_transcripts.py`: inventario live, selecao na ordem da
  fila, lock, estado retomavel, ledger JSONL, staging, validacao e promocao
  atomica;
- rotas `metadata`, `direct`, `ui`, `browser` e `asr`, com ASR protegido por
  confirmacao previa no Chrome real;
- validacao de video ID, segmentos nao vazios, ordem monotonic, tamanho minimo,
  cobertura, hash e idioma;
- normalizacao para `processed/<video_id>/content_segments.json`;
- importacao de capturas do Chrome por staging, sem gravacao direta do processo
  Windows no data root Linux;
- estado em `input/vturb_transcript_backfill_state.json`, ledger em
  `logs/vturb_transcript_backfill.jsonl` e resumo em
  `exports/vturb_transcript_backfill_summary.json`;
- dependencia `yt-dlp`, cache local de audio e `faster-whisper` CPU/int8;
- dezenove testes focados verdes em 0,12 s no ultimo run;
- runbook da skill de transcricoes atualizado.

## Descoberta e saneamento do inventario

O primeiro scan encontrou 50 arquivos nao vazios, 46 arquivos vazios e 67
videos sem arquivo/metadata. A verificacao forte reprovou vinte dos cinquenta
nao vazios: os timestamps voltavam no fim, padrao compativel com segmentos do
painel anterior anexados ao video atual. Por isso, apenas trinta eram validos.

O custo observado do scan completo de 163 itens foi 3,8 s. O custo e pequeno e
nao e gargalo. A regra nova nao exclui nem sobrescreve o arquivo invalido antes
de existir substituicao validada.

## Tempos observados por etapa

Os tempos abaixo distinguem processo interno, wall-clock do comando e lacunas
sem instrumentacao. O ledger usa timestamps UTC com resolucao de um segundo.

| Etapa | Volume | Tempo observado | Resultado |
| --- | ---: | ---: | --- |
| Scan/inventario live | 163 videos | 3,8 s | 30 validos, 133 pendentes |
| Testes focados finais | 19 testes | 0,12 s de pytest | todos passaram |
| Instalacao de `yt-dlp` | 1 pacote | 3,2 s | versao 2026.7.4 |
| Legenda direta | 3 videos | ate 3 s no total | 0 capturas; retorno vazio validado |
| UI headless, falha `npx.cmd` | 5 videos | 2 s no bloco | 5 falhas globais repetidas |
| UI headless, Node 18 vs CLI atual | 5 videos | 7 s no bloco | 5 falhas globais repetidas |
| UI headless, CLI 0.0.60 | 5 videos | 12 s no bloco | 5 falhas `Unknown command` |
| Download Chromium/FFmpeg/headless shell | 301,3 MiB transferidos | 25,4 s | cache final Playwright 656 MiB |
| Inicio do Chromium | 1 probe | falha imediata | `libnspr4.so` ausente; sudo exige senha |
| Chrome real, quatro videos com reload | 4 videos | cerca de 52 s | 4 sem painel, cerca de 13 s/video |
| Chrome real, primeiro lote redundante | 5 videos | cerca de 63 s | 5 sem painel, 12,7 s/video |
| Chrome real, lote otimizado | 10 videos | cerca de 81 s | 10 sem painel, 8,1 s/video |
| Chrome real, quinze resultados persistidos | 15 videos | cerca de 144 s | media 9,6 s/video |
| Importacao/validacao da captura valida | 1 video | menor que 1 s no ledger | promovida atomicamente |
| ASR frio de 90 s | 1 video | 156,8 s | 37 segmentos, validacao passou |

O ledger cobriu 17m48s entre o primeiro evento (`04:17:58Z`) e o piloto ASR
(`04:35:46Z`), mas esse intervalo inclui diagnosticos e correcoes e nao inclui
todo o desenvolvimento anterior nem os lotes Chrome posteriores. Nao existe
timestamp canonico suficiente para atribuir cada minuto de engenharia; isso e
uma lacuna de telemetria, nao um numero a ser estimado.

## Custos de cache e disco

| Cache | Tamanho observado |
| --- | ---: |
| Modelo `large-v3-turbo` no data root | 1,7 GiB |
| Audio do piloto | 47 MiB |
| Playwright/Chromium | 656 MiB |
| Cache auxiliar Hugging Face | 352 KiB |

O cache de modelo e reutilizavel e deve reduzir o proximo ASR. O cache
Playwright nao gerou uma rota funcional no WSL atual e pode ser removido se a
decisao arquitetural abandonar o headless local.

## Analise criteriosa por rota

### Inventario e classificacao

Funcionou bem. A selecao preservou `episode_priority`, suporta IDs explicitos,
limite recente e status acionaveis. O custo de 3,8 s para 163 videos nao merece
otimizacao agressiva. A melhoria util e evitar reescan quando fila, state e
arquivos fonte mantiverem os mesmos hashes.

### Legenda direta

Teve zero yield no piloto, mas custou no maximo cerca de um segundo por video.
Ainda vale como primeira tentativa para videos novos, desde que exista timeout
curto e classificacao de erro. Economizar essa etapa inteira pouparia poucos
minutos no catalogo, enquanto uma unica captura bem-sucedida pode poupar horas
de ASR.

### UI headless no WSL

Foi o maior desperdicio evitavel do piloto. A mesma falha de infraestrutura foi
repetida por cinco videos em cada uma de tres configuracoes. A causa mudou, mas
todas eram detectaveis antes do primeiro episodio:

- PATH misto escolheu `npx.cmd` do Windows;
- CLI atual requer Node 20+;
- CLI antigo aceita Node 18, mas falha no protocolo atual;
- Chromium baixado nao encontra bibliotecas Linux;
- nao ha sudo nao interativo para instalar dependencias.

A rota nao deve fazer parte do default enquanto um probe unico nao abrir o
navegador, navegar para uma pagina e executar DOM read. Falha de capacidade
deve abrir circuit breaker para o run inteiro.

### Chrome real

Foi a unica rota de UI que produziu uma transcricao valida e tambem a unica
capaz de confirmar ausencia real antes do ASR. A remocao do reload redundante
reduziu o caso sem painel de 12,7 para 8,1 s/video, ganho observado de 36%.

O ponto fraco e a persistencia por lote. Quinze resultados foram salvos, mas um
lote seguinte de vinte foi interrompido antes do checkpoint e nao produziu
evidencia reutilizavel. O checkpoint precisa ocorrer depois de cada video.

### Validacao e promocao

Foi a etapa mais importante para qualidade e custou menos de um segundo no
caso promovido. Ela rejeitou arquivos vazios, cobertura baixa, ID divergente e
timestamps fora de ordem. Deve permanecer obrigatoria; reduzir esse gate teria
alto risco e ganho irrelevante.

### ASR local

O piloto frio passou, mas 156,8 s para 90 s nao representa throughput quente.
Nesse comando houve download do audio completo, download/load do modelo e
inferencia. Sem separar as fases, extrapolar para 355,77 h produziria uma
estimativa falsa.

O runner ja reutiliza uma instancia do modelo quando varios itens rodam na
mesma invocacao. Falta chunk retomavel, metricas de real-time factor, benchmark
de modelo/compute type e prefetch do proximo audio sem promover fora da ordem.

## O que nao foi concluido

- 113 itens do manifesto ainda nao foram verificados no Chrome;
- 15 ausencias confirmadas estao em staging, mas ainda nao foram marcadas no
  state Linux;
- quatro videos estao `pending_asr`; somente um tem piloto de 90 s;
- nenhuma transcricao ASR integral foi promovida;
- a fila gold nao foi reconstruida porque o backfill foi pausado;
- a rotina semanal ainda nao foi integrada ao novo runner;
- a rota headless continua bloqueada por capacidade do WSL.

## Decisao recomendada

Nao retomar o ASR integral antes de concluir P0 (telemetria e circuit breaker),
P1 (checkpoint Chrome por video) e o benchmark quente P2. Depois disso, concluir
a varredura Chrome na ordem da fila, importar todas as capturas validas em uma
wave e liberar ASR apenas para o residuo comprovado.

