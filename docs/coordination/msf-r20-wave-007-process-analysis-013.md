# MSF-R20 wave 007 - análise criteriosa do processo

Status: análise concluída
Data: 2026-07-18
Escopo: últimos quatro episódios usados para medir as simplificações 011/012,
com foco detalhado na wave 007
Arquitetura preservada: `chronological_hybrid_v1`

## Conclusão executiva

As melhorias 012 entregaram ganho real de tempo e integridade, mas não
entregaram convergência semântica na primeira passagem.

- O wall da wave caiu de **3h34m23s** no benchmark 011 para **2h01m09s** na
  wave 007: redução de **43,5%**.
- A média dos walls individuais caiu de **3h21m05s** para **1h45m32s**:
  redução de **47,5%**.
- A leitura/autoria média caiu apenas de **22m11s** para **20m01s**:
  redução de **9,8%**. Esse não foi o principal ganho.
- Os dossiers continuaram muito menores que os 910-931 KB anteriores:
  **578.270 B** e **480.002 B**, reduções de 36,4% e 48,4% contra os pares do
  benchmark 011.
- Source completeness, request consolidado, transação envelope-first, packet,
  fingerprints e completion funcionaram corretamente.
- Em contrapartida, a primeira passagem Sol encontrou **19 findings**, contra
  **5** no benchmark anterior: aumento de 3,8 vezes. Foram necessárias três
  remediações em `eCaODMtU5GY`, duas em `MiKloPf9-To` e quatro vereditos dentro
  da fase final de auditoria para chegar a zero.

Portanto, a resposta honesta é: **houve ganho estrutural substancial, mas parte
dele foi consumida por piora da qualidade semântica da primeira autoria e por
reparos que não substituíam integralmente o estado defeituoso**. Não faz sentido
adicionar mais gates, briefs ou telemetria. O próximo trabalho deve fechar duas
causas inteiras: semântica P0 antes do primeiro packet e remediação realmente
substitutiva/convergente.

## Base de evidência

Foram reconciliados:

- receipts de seleção, contexto, one-shot, remediação e completion dos dois
  jobs da wave 007;
- `episode_fast_session.json`, `episode_performance_report.json` e os dossiers
  inicial/remediados;
- relatórios Sol inicial e reauditorias 001, 002 e 003;
- manifests autorais e checks transitórios do workspace;
- retrospectivas do benchmark 011 e da Simplificação 012;
- implementação atual de `manifest_to_compact_payload()` e
  `build_reaudit_delta()`.

Os walls individuais se sobrepõem e não são somados. A primeira reauditoria de
cada episódio permaneceu aberta no lifecycle enquanto a remediação seguinte já
estava em curso; seus spans brutos, portanto, não são tratados como tempo ativo
adicional.

## Episódios e resultado final

| Wave | Episódio | Segmentos | Chunks | Candidatos finais | Resultado |
| --- | --- | ---: | ---: | ---: | --- |
| benchmark 011 | `jbFY16W5GTE` | 1.106 | 21 | 34 | `complete/passed/0` |
| benchmark 011 | `fBaX4ixKkFo` | 1.238 | 23 | 44 | `complete/passed/0` |
| wave 007 | `eCaODMtU5GY` | 1.079 | 21 | 56 | `complete/passed/0` |
| wave 007 | `MiKloPf9-To` | 1.051 | 19 | 50 | `complete/passed/0` |

Todos os quatro golds finais são válidos. A crítica é ao caminho percorrido,
não ao conteúdo persistido.

## Linha do tempo detalhada da wave 007

### 1. Seleção, preflight e contexto

| Episódio | Tempo ativo | Saída |
| --- | ---: | --- |
| `eCaODMtU5GY` | 0,85 s | seleção, fonte e contexto válidos |
| `MiKloPf9-To` | 9,51 s | seleção, fonte e contexto válidos |

Processo: consulta da fila apenas como prioridade, validação da fonte no data
root Windows ativo, identidade terminal, runtime e contexto cronológico.

Veredito: **ganho comprovado e etapa congelada**. Mesmo que fosse eliminada por
inteiro, economizaria menos de 11 segundos na wave.

### 2. Leitura cronológica e autoria inicial

| Episódio | Tempo | Candidatos no primeiro dossier | Candidatos finais |
| --- | ---: | ---: | ---: |
| `eCaODMtU5GY` | 28m55,58s | 55 | 56 |
| `MiKloPf9-To` | 11m05,58s | 51 | 50 |
| média | 20m00,58s | 53 | 53 |

Processo: leitura integral dos 21/19 chunks, composição de candidatos,
evidências, ledger, números, relações, caveats, reported attribution,
calibrações e recall adversarial.

Veredito: o tempo médio melhorou pouco e a variância foi grande. Mais
importante: o crescimento de candidatos parece excelente (+1 e -1), mas é uma
métrica enganosa. A maioria dos defeitos estava **dentro** dos candidatos já
existentes: números sem semântica, evidência que não sustentava a claim,
duplicata e atribuição. Não se deve reduzir a leitura; deve-se tornar o primeiro
estado semanticamente fechável.

### 3. Dry-runs, prelint e preparação

| Episódio | Dry-runs observados no job | Prelint oficial | Resultado estrutural |
| --- | ---: | ---: | --- |
| `eCaODMtU5GY` | 6 | 0,61 s | `hard_blockers=0` |
| `MiKloPf9-To` | 3 | 0,57 s | `hard_blockers=0` |

O runtime determinístico foi rápido, mas aceitou matrizes extensas em que raws
materiais continuavam como `count/value=null`. O prelint provou estrutura e
source completeness, não a correção econômica/quantitativa das ocorrências.

Veredito: **não há problema de CPU**. Criar outro prelint seria burocracia. A
correção deve fortalecer a invariante existente para que um número material
tenha semântica tipada ou ambiguidade ASR explícita antes de `ready`.

### 4. One-shot inicial

| Episódio | Total | Persist | Finalizer | Dossier |
| --- | ---: | ---: | ---: | ---: |
| `eCaODMtU5GY` | 3,24 s | 0,094 s | 0,943 s | 1,429 s |
| `MiKloPf9-To` | 3,04 s | 0,102 s | 0,924 s | 1,353 s |

Processo: preview hash-bound, apply, persistência, finalização, packet e dossier.

Veredito: **ganho comprovado e etapa congelada**. A redução adicional possível
é irrelevante frente às dezenas de minutos de julgamento.

### 5. Primeiro veredito da fase final Sol

| Episódio | Tempo | Findings |
| --- | ---: | ---: |
| `eCaODMtU5GY` | 12m55,50s | 9 |
| `MiKloPf9-To` | 12m56,35s | 10 |

Os dossiers foram despachados somente depois dos dois ramos prontos, como
previsto pela 012. A leitura consolidada levou cerca de 13 minutos de wall,
pois os episódios foram tratados de forma sobreposta.

Taxonomia dos 19 findings:

| Classe | Quantidade | Participação |
| --- | ---: | ---: |
| Semântica/cobertura/atribuição numérica | 10 | 52,6% |
| Claim, evidência e ledger | 4 | 21,1% |
| Source completeness e atribuição | 2 | 10,5% |
| Equivalência de calibração | 2 | 10,5% |
| Duplicata/relação | 1 | 5,3% |

Veredito: a Sol fez seu papel e evitou degradação da qualidade. O defeito foi
entregar a ela dez problemas quantitativos e duas calibrações que o contrato
autoral já deveria ter fechado.

### 6. Remediação 001

| Episódio | Autoria | Runtime transacional | Findings restantes |
| --- | ---: | ---: | ---: |
| `eCaODMtU5GY` | 22m44,83s | 5,77 s | 5 |
| `MiKloPf9-To` | 22m52,62s | 6,58 s | 3 |

A transação envelope-first funcionou: uma escrita de reviews, um finalizer, um
build e um dossier por episódio. Porém o helper de números enriqueceu alguns
records sem remover os records opacos originais. A auditoria recebeu as duas
representações e manteve findings. As decisões de calibração estavam no
manifesto, mas não se tornaram autoridade do payload final.

Dos oito findings restantes, seis ainda eram numéricos e dois eram de
calibração. Isto prova que a remediação 001 tratou sintomas, não substituiu a
matriz defeituosa inteira.

### 7. Remediação 002 e segundo veredito

| Episódio | Autoria | Runtime | Reauditoria 002 | Resultado |
| --- | ---: | ---: | ---: | --- |
| `eCaODMtU5GY` | 8m50,92s | 5,35 s | 6m06,50s | 1 finding |
| `MiKloPf9-To` | 9m10,37s | 7,97 s | 6m05,36s | `passed/0` |

As matrizes foram finalmente substituídas por ocorrências tipadas, com
multiplicidade e caveats. As calibrações foram fechadas por binding da
ocorrência duplicada do cold open ao candidato canônico.

Veredito: correção semanticamente adequada, mas tardia. O mesmo resultado
deveria ter sido exigido no primeiro prelint ou, no máximo, na primeira
remediação.

### 8. Remediação residual 003 e veredito final

| Episódio | Autoria | Runtime | Reauditoria 003 | Resultado |
| --- | ---: | ---: | ---: | --- |
| `eCaODMtU5GY` | 1m07,99s | 5,07 s | 4m03,62s | `passed/0` |
| `MiKloPf9-To` | não aplicável | não aplicável | 3m15,13s | invariância confirmada |

O residual era preciso: os raws ASR `r$ 2` e `10000` tinham escala desconhecida,
mas receberam valores concretos. A correção preservou os raws e definiu
`value/min/max=null`, papel e unidade desconhecida, sem apagar os records
válidos adjacentes.

O autocheck também precisou de uma exceção estreita para normalização ASR
inferida de `030` para 0,30%, exigindo raw literal, caveat e menção explícita a
ASR. A regressão foi adicionada e passou.

### 9. Completion

| Episódio | Tempo | Estado |
| --- | ---: | --- |
| `eCaODMtU5GY` | 0,20 s | `complete/passed/0` |
| `MiKloPf9-To` | 0,35 s | `complete/passed/0` |

Packet 5/5, fingerprints, audit envelope, terminal identity e receipts foram
validados. Veredito: **etapa congelada**.

## Reconciliação de tempo

| Medida | Benchmark 011 | Wave 007 | Variação |
| --- | ---: | ---: | ---: |
| Wall da wave | 3h34m23s | 2h01m09s | -43,5% |
| Média do wall individual | 3h21m05s | 1h45m32s | -47,5% |
| Média leitura/autoria | 22m11s | 20m01s | -9,8% |
| Primeiro veredito Sol | 38m19s de wave | ~13m de wave | -66,1% |
| Findings no primeiro veredito | 5 | 19 | +280% |
| Dossiers finais | 909.666/930.916 B | 578.270/480.002 B | -36,4%/-48,4% |

O wall menor é real. Ele veio principalmente de:

1. gate consolidado antes da Sol;
2. dossier deduplicado;
3. transações de 5-8 segundos;
4. eliminação dos gaps de aproximadamente duas horas do benchmark 011.

Não veio de melhor primeira autoria. A fase após o primeiro veredito ainda
consumiu aproximadamente uma hora de wall até o completion.

## Complexidade e burocracia observadas

| Superfície transitória | Benchmark 011 | Wave 007 | Leitura |
| --- | ---: | ---: | --- |
| Arquivos observados | 69 | 109 | +58,0% |
| Arquivos nos dois job dirs | 53 | 72 | mais dossiers/remediações |
| Arquivos repo-local da wave | 16 | 37 | versões de manifest/check e relatórios |
| Revisões de dossier | 3 por episódio | 4 e 3 | convergência não melhorou |

Os 109 arquivos da wave 007 ocupam cerca de 96 MiB somando jobs e `.tmp` do
workspace. Eles são transitórios e não contaminam o packet final, mas evidenciam
que a simplificação estrutural não reduziu a quantidade de tentativas. Houve
múltiplas versões numeradas de manifesto, dry-run e replacement-check.

A complexidade útil foi: dossier source-complete, envelope, hashes e
provenance. A complexidade improdutiva foi: manter records antigos enquanto se
adicionavam novos, tentar delta focal sem dependências fechadas, gerar novas
versões de manifesto para absorver warnings e deixar spans de auditoria abertos
depois do veredito.

## Veredito das melhorias recentes

| Melhoria | Evidência na wave 007 | Veredito |
| --- | --- | --- |
| Source-complete como autoridade de `ready` | zero unreviewed, ledger integral, zero hard blocker real | ganho forte; manter |
| Despacho consolidado N/N | dois dossiers prontos antes da Sol; ~13m de wall | ganho forte; manter |
| Dossier deduplicado | 480-578 KB contra 910-931 KB | ganho forte; manter, sem novo brief |
| Envelope-first transacional | remediações em 5-8s, sem write incoerente | ganho forte; manter |
| Warning IDs locais | não houve churn global equivalente ao benchmark 011 | ganho real, mas warnings ainda exigiram absorção |
| Reaudit delta | rejeitou mudanças dependentes fora do finding e caiu para dossier integral | ganho não comprovado nesta wave |
| Matriz numérica/prelint atual | 10 findings iniciais e 6/8 residuais numéricos | insuficiente; causa principal do retrabalho |
| Calibration decisions no manifesto | decisões não compiladas pelo payload; bindings tiveram de contaminar cobertura | autoridade incompleta |
| Telemetria de auditoria | spans 001 fecharam depois da remediação seguinte | medição não confiável nessa fronteira |
| Contagem de candidatos pós-apply | +1/-1, apesar de 19 findings | métrica inadequada para qualidade |

## O que não deve ser otimizado

- seleção, preflight, contexto, prelint runtime, one-shot e completion;
- Python, PowerShell, temp ou serialização;
- redução de transcript, chunks, candidatos ou leitura cronológica;
- modelo menor ou retirada da auditoria Sol/high;
- novo score, novo brief, novo helper por episódio, novo papel ou novo gate;
- mais campos de telemetria ou dashboards;
- meta rígida de tamanho de dossier que force omissão de fonte.

Essas ações ou economizariam segundos, ou aumentariam risco/complexidade.

## Melhorias com potencial substancial

Somente duas frentes passam o corte de eliminar uma classe inteira de falhas e
economizar pelo menos uma rodada relevante de remediação/auditoria.

### 1. Fechamento semântico P0 no contrato existente

Unificar, dentro da invariante source-complete já existente:

- todo raw numérico material deve terminar como ocorrência tipada
  (valor/faixa, unidade, papel, status, multiplicidade e caveat quando
  necessário), ambiguidade ASR explícita com valor nulo, ou exclusão incidental
  source-scoped;
- bloquear `count/value=null` quando o token participa de claim, comparação,
  teste, custo, resultado, threshold ou trajetória;
- bloquear duas representações da mesma ocorrência fonte;
- compilar `calibration_decisions` como autoridade do resultado derivado, em
  vez de usá-las apenas como check paralelo;
- exigir equivalência proposicional e fonte canônica para duplicatas, sem
  ampliar evidence ranges artificialmente.

Potencial: evitar os 10 findings numéricos, os 2 de calibração e os 6 findings
numéricos que sobreviveram à primeira remediação. Economia observável esperada:
20-40 minutos por episódio complexo e uma a duas leituras Sol por wave.

### 2. Remediação substitutiva e convergente

Usar o manifesto canônico como substituição total do candidato afetado:

- nunca fazer merge aditivo de number records;
- calcular antes do commit o fecho de dependências de candidato, ledger,
  calibração, warning, relação e packet;
- escolher delta focal ou dossier integral antes da escrita; não tentar delta
  que já viola invariantes conhecidas;
- manter apenas um manifesto canônico e, no máximo, um snapshot before/after;
- fechar o span de auditoria no momento do veredito e abrir outro apenas para a
  leitura seguinte, sem nova camada de telemetria.

Potencial: transformar as 2-3 remediações observadas em no máximo uma por
episódio, eliminar versões intermediárias e tornar a medição confiável. Economia
esperada: 15-30 minutos por episódio quando houver finding residual.

## Meta realista para o próximo benchmark

Para uma wave de dois episódios de aproximadamente 900-1.300 segmentos:

- `complete/passed/0` nos dois, sem reduzir a rubrica;
- primeiro veredito com no máximo 2 findings por episódio e zero finding das
  classes numérica/calibração quando o prelint tiver passado;
- no máximo uma remediação por episódio;
- no máximo dois dossiers por episódio: inicial e remediado;
- nenhum manifesto numerado fora do job canônico;
- spans sem sobreposição indevida e diferença de reconciliação inferior a 1%;
- wall alvo de **55-75 minutos** para a wave com até uma remediação por ramo.

O alvo é benchmark, não promessa. Se qualidade exigir mais leitura, a qualidade
prevalece. O ganho só será promovido se a próxima wave comprovar simultaneamente
tempo, convergência e `passed/0`.
