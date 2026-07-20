# Retrospectiva - Gold Runtime Pilot 006

Status: complete/passed/0

## Episodio e resultado

- video_id: `p78Zv3_WCsM`
- titulo: `Ele Fez 40MM De Dolares Em 12 Meses Com VSLs | Peter Kell - Segredos da Escala #065`
- duracao: 58m34s
- volume: 998 segmentos e 12 chunks
- primeira extracao: 12/12 reviews e 23 candidatos
- gold final: 12/12 reviews e 24 IDs unicos
- calibracao final: `pass`, 7 cobertas para minimo 3
- auditoria Sol inicial: `changes_requested`, tres findings
- reauditoria Sol: `passed`, zero findings abertos
- lifecycle terminal: `complete/passed/0`
- packet: cinco arquivos no export Linux esperado
- fingerprints protegidos: os tres arquivos existentes no snapshot permaneceram
  iguais antes/depois

Todo processamento gold que tocou o data root ocorreu no Ubuntu WSL 2. Nao
houve fallback para Python Windows nem escrita contra `C:\MSF-data`.

## Escopo e qualidade da medicao

O receipt terminal mediu **50m18,488s**, de 15:33:18.081Z a 16:23:36.569Z.
Esse e o tempo ate o estado gold terminal, nao todo o tempo visual posterior do
chat.

Duas superficies ficam fora desse numero:

1. a tentativa WSL anterior ao `StartEpisode`, que encontrou a identidade
   sandbox sem a distribuicao e revelou o problema de cwd do `exec-after`;
2. o fechamento posterior ao receipt, incluindo regressao focada, leitura das
   metricas e documentacao. A primeira gravacao documental ocorreu 4m56s apos
   o receipt terminal.

Os comandos deterministas instrumentados somaram **2,0505s**. O relatorio
classificou 48m42,879s como `inter_turn_idle_ms` e 1m33,493s como transicoes.
Isso nao significa que o modelo julgou o episodio em 23ms: o valor
`model_judgment_ms=23,41` cobre somente o interior dos eventos de comando. A
leitura, composicao, auditoria e autoria do patch ficaram nos gaps entre
eventos. A telemetria ainda nao atribui corretamente esse trabalho semantico.

## Linha do tempo detalhada

| Etapa | Janela UTC | Wall time | Runtime medido | Resultado |
| --- | --- | ---: | ---: | --- |
| Partida, selecao e contexto | 15:33:18-15:33:26 | 8,348s | 687,28ms | WSL certificado, episodio selecionado e contexto de 84.417 bytes |
| Leitura integral e composicao inicial | 15:33:26-15:43:49 | 10m22,838s | n/a | 998 segmentos lidos, 12 reviews e 23 candidatos em compact v3 |
| Fixed point de prelint | 15:43:49-15:47:33 | 3m43,965s | 318,43ms | quatro previews ate `prelint_clean`, hard blockers zero |
| Preview limpo ate packet inicial | 15:47:33-15:48:01 | 27,911s | 520,33ms | apply unico, finalizer, build, validator e dossier inicial |
| Auditoria Sol inicial | 15:48:01-16:00:01 | 12m00,545s | julgamento semantico | tres findings source-backed |
| Diagnostico e remediacao | 16:00:01-16:21:45 | 21m44,223s | 442,10ms registrados | runtime recertificado, manifesto corrigido e uma aplicacao focal |
| Reauditoria Sol | 16:21:45-16:22:52 | 1m06,285s | julgamento semantico | `passed/open_findings=0` |
| Completion | 16:22:52-16:23:36 | 44,418s | 82,36ms | audit registrado, build complete e require-audit pass |

O primeiro packet estruturalmente valido existiu em **14m43,063s**. Os
35m35,425s restantes vieram da fase de qualidade final, sobretudo auditoria e
remediacao.

## O que funcionou

1. **Partida certificada ficou rapida.** Selecao e contexto terminaram em menos
   de nove segundos, contra minutos nos pilotos anteriores.
2. **O runtime permaneceu Linux-native.** O erro de cwd foi identificado antes
   da primeira escrita e corrigido para o processo entrar no clone Linux antes
   de `execv`.
3. **Os gates impediram dados falsos.** O primeiro prelint recusou `70 pessoas`
   porque a fonte dizia literalmente `70 people`.
4. **A persistencia foi atomica e barata.** Apply, finalizer, build, validator e
   dossier consumiram 520ms de runtime e produziram packet exato de cinco
   arquivos.
5. **A auditoria Sol agregou qualidade real.** Os tres findings nao eram ruido:
   havia uma proposicao quantitativa omitida, uma generalizacao cross-format
   perdida e uma relacao semantica util ausente.
6. **A remediacao foi estreita.** G024 foi inserido, G014 foi ampliado e a
   relacao G010/G011 foi registrada sem alterar candidatos alheios.
7. **A reauditoria passou na primeira tentativa.** O resultado final preservou
   evidencias, ledger, calibracao, IDs, packet e fingerprints.
8. **O receipt terminal foi autoridade suficiente.** Depois de
   `complete/passed/0`, nenhuma nova verificacao gold foi necessaria.

## O que deu errado e causa confirmada

### 1. O `exec-after` podia importar o checkout Windows

O sincronizador executava o Python Linux, mas herdava o cwd montado do Windows.
Assim, imports relativos podiam resolver para `/mnt/c` em vez do clone Linux.
A correcao `os.chdir(destination_root)` e sua regressao foram implementadas
antes do `StartEpisode` medido.

### 2. Quatro ciclos de prelint foram evitaveis

Os ciclos foram causados por:

- raw numerico redigitado em portugues quando a fonte estava em ingles;
- disposicoes de warnings ainda ausentes;
- uso de uma chave compacta nao canonica antes de adotar
  `audit_warning_dispositions`;
- somente o quarto preview atingiu o fixed point limpo.

O compilador foi rapido; o custo de 3m44s veio da leitura do inventario,
edicao e nova chamada. Raw numerico e estruturas mecanicas devem ser derivados
da fonte, nao redigitados.

### 3. Dois gaps de recall estavam logo apos evidencia capturada

- G014 terminava em 762; a proposicao cross-format estava em 763-770.
- G020 terminava em 912; o teste de primeiro touchpoint estava em 913-923.

O ledger inicial deixava varios desses indexes sem disposicao e marcava apenas
alguns como `low_signal`. O signal inventory nao representava toda a unidade
semantica, portanto o autocheck estrutural nao podia encontrar sozinho o gap.
Faltou uma releitura obrigatoria das caudas adjacentes a cada evidencia e do fim
do episodio.

### 4. A relacao ausente era detectavel por contencao de evidencia

G010 usava 683-703 como suporte; G011 usava exatamente 683-703 como evidencia
minima. Ambos estavam capturados no ledger, mas sem parent/child. A heuristica
lexical de overlap nao e a superficie correta. O pre-packet precisa mostrar
grupos em que a evidencia minima de um candidato esta contida na evidencia de
outro e pedir decisao semantica explicita.

### 5. O dossier exigia correlacao manual entre superficies

O dossier tinha 172.745 bytes e era source-complete, mas apresentava:

- transcript sem disposition/candidate IDs inline;
- candidatos depois dos blocos de transcript;
- ledger agrupado em registros separados;
- warnings extensos antes da navegacao semantica mais util.

O auditor precisou cruzar transcript, candidatos e ledger em passagens
separadas. A leitura integral continua obrigatoria, mas a cobertura deve ficar
na mesma linha da fonte para evitar reler o episodio.

### 6. A remediacao levou 21m45s apesar de 442ms de runtime

O custo veio de tres retrabalhos:

1. autoria manual de helper e manifesto para converter findings em patch;
2. drift de cinco scripts no checkout depois do receipt, que invalidou a
   paridade e exigiu nova sincronizacao certificada;
3. o primeiro check incluiu a fala incidental `100%` no suporte de G014, que o
   gate numerico corretamente tratou como material; a evidencia precisou ser
   estreitada para 765-770.

O patch final foi correto, mas sua montagem deve ser source-canonical e o
runtime de um episodio precisa permanecer congelado ate o completion.

### 7. A telemetria nao mede fases semanticas

Como so comandos gravam eventos, leitura, autoria e auditoria aparecem como
idle. Isso ajuda a provar que Python nao e o gargalo, mas nao separa leitura de
payload, auditoria e design de remediation com precisao suficiente para novos
benchmarks.

## Reducao proposta por etapa

| Etapa | Atual | Meta realista | Mudanca sem degradar qualidade |
| --- | ---: | ---: | --- |
| Partida e contexto | 8,35s | 5-10s | manter StartEpisode, cwd Linux e runtime congelado por run_id |
| Leitura e payload | 10m23s | 6-8m | raw numerico source-canonical, matriz de candidatos por slab e template v3 ja canonico |
| Prelint | 3m44s | 45-90s | repair scaffold completo e um unico preview oficial depois do check local |
| Apply/finalizer | 28s wall | 5-15s | manter one-shot; eliminar transicao e stdout redundante |
| Auditoria Sol | 12m | 6-8m | dossier v3 com candidatos primeiro, cobertura inline e mapas de borda/relacao |
| Remediacao | 21m45s | 3-5m | scaffold audit-to-patch, asserts da fonte e snapshot de runtime imutavel |
| Reauditoria + completion | 1m51s | 45-75s | dossier delta dos findings mais prova integral de invariantes e completion encadeado |
| Fechamento documental | pelo menos 4m56s fora do receipt | 1-2m | retrospectiva deterministica e links derivados do receipt terminal |

Meta para episodio de 700-1.300 segmentos:

- **13-18 minutos** quando a primeira auditoria passa;
- **17-23 minutos** quando uma remediacao focal for necessaria;
- manter dez minutos como media do inventario, nao promessa para cada entrevista
  longa.

## Decisao

Manter WSL, leitura integral, compact v3, prelint, one-shot, auditoria Sol,
remediacao transacional e completion receipt. Nao reverter o fluxo.

O proximo passo e implementar
`msf-r20-gold-runtime-pilot-007-optimization-plan.md` e testar em um episodio
novo de porte comparavel, sem editar runtime ou documentacao durante a janela.
