# MSF-R20 Gold Runtime Benchmark 011 - Retrospectiva dos dois episodios

Status: complete
Data: 2026-07-18
Episodios: `jbFY16W5GTE`, `fBaX4ixKkFo`
Arquitetura: `chronological_hybrid_v1`
Base de comparacao: Gold Runtime Pilot 011 `NiT0-ABoVnk`

## Conclusao executiva

Os dois episodios terminaram corretamente em `complete/passed`, com zero
finding aberto, 78 candidatos finais, calibracao aprovada, packets de cinco
arquivos e fingerprints protegidos preservados.

As melhorias recentes entregaram ganhos reais, mas nao validaram a otimizacao
ponta a ponta:

- o wall da wave caiu de 9h43m33s no piloto anterior para 3h34m23s, reducao de
  63,3%;
- a leitura/autoria media caiu de 34m51s para 22m11s, reducao de 36,3%;
- o crescimento depois do primeiro apply caiu de 89,3% para 13,3% e 12,8%;
- a superficie transitoria observada caiu de 182 arquivos em um episodio para
  69 arquivos somando os dois job dirs e o diretorio de benchmark;
- selecao/contexto, one-shot, reauditoria focal e completion ficaram em
  segundos ou poucos minutos.

Entretanto:

- a primeira Sol encontrou cinco findings major;
- os primeiros dossiers declaravam `hard_blockers=[]`, mas continham 427
  segmentos `unreviewed` e 183 segmentos em blocos `must_close`;
- a auditoria do primeiro episodio comecou antes do segundo episodio estar
  pronto, contrariando a auditoria final consolidada da wave;
- remediacao e reauditoria 02 consumiram cerca de 2h03m de wall da wave;
- edicoes locais regeneraram warning IDs e reabriram calibracoes nao afetadas;
- a rota de remediacao persistiu dossiers validos e somente depois falhou em
  `reaudit_delta` por ausencia de envelope materializado;
- os receipts contaram `remediations=0` e `patches=0`, apesar das remediacoes
  persistidas;
- 42,6% e 62,3% dos walls individuais ficaram como gap nao classificado;
- os dossiers finais ainda medem 910 KB e 931 KB e repetem navegacao, warnings,
  workbench, transcript e evidencia.

Veredito: a simplificacao reduziu materialmente a explosao de helpers,
candidatos e horas perdidas, mas ainda adiciona burocracia model-facing e
revalidacao global desnecessaria. O nucleo deve ser preservado; somente tres
mudancas estruturais de alto impacto justificam novo trabalho.

## Fontes de evidencia

- `episode_performance_report.json` e `episode_fast_session.json` dos dois job
  dirs;
- dossiers inicial, remediation-02 e remediation-03;
- auditoria Sol inicial, reauditoria 02 e reauditoria 03;
- receipts terminais e terminal identity;
- plano `msf-r20-gold-runtime-simplification-011-plan.md`;
- retrospectiva `msf-r20-gold-runtime-pilot-011-retrospective.md`.

Os tempos abaixo provem dos receipts e spans. Tempos sobrepostos nao sao
somados como wall da wave. Spans interrompidos e o span stale de prelint repair
nao sao tratados como compute valido.

## Resultado final de qualidade

| Controle | `jbFY16W5GTE` | `fBaX4ixKkFo` |
| --- | ---: | ---: |
| Segmentos | 1.106 | 1.238 |
| Chunks | 21 | 23 |
| Candidatos no primeiro apply | 30 | 39 |
| Candidatos finais | 34 | 44 |
| Crescimento pos-apply | 4 / 13,3% | 5 / 12,8% |
| Calibracao final | 9/16, `pass` | 11/16, `pass` |
| Ledger final | 1.106/1.106 | 1.238/1.238 |
| Auditoria final | `passed/0` | `passed/0` |
| Packet | cinco arquivos | cinco arquivos |
| Fingerprints | preservados | preservados |
| Lifecycle | `complete` | `complete` |

O resultado final e confiavel. A critica desta retrospectiva e ao caminho, nao
ao gold persistido.

## Linha do tempo detalhada

### Etapa 1 - selecao, preflight e contexto

| Episodio | Selecao | Preflight/contexto | Total ativo | Observacao |
| --- | ---: | ---: | ---: | --- |
| `jbFY16W5GTE` | 0,081s | 0,716s | 0,797s | Houve 11,684s de transicao antes da selecao. |
| `fBaX4ixKkFo` | 1,482s | 0,945s | 2,427s | Dentro do teto de 3s. |

Processo: consulta da identidade terminal, selecao pela fila apenas como ordem,
preflight Windows-native, validacao de fonte e emissao do contexto cronologico
compacto.

Julgamento: ganho comprovado. Nao e gargalo e nao deve receber nova
otimizacao.

### Etapa 2 - leitura cronologica e autoria inicial

| Episodio | Inicio UTC | Fim UTC | Tempo | Contexto |
| --- | --- | --- | ---: | ---: |
| `jbFY16W5GTE` | 12:16:54 | 12:41:18 | 24m23,2s | 260.350 bytes |
| `fBaX4ixKkFo` | 12:42:57 | 13:02:56 | 19m59,0s | 271.985 bytes |

Processo: leitura integral dos 21/23 chunks, composicao de candidatos atomicos,
source dispositions, numeros, caveats, relacoes, calibracao e adversarial
review no manifesto autoral.

Julgamento: o tempo atingiu a meta de 18-28 minutos e melhorou 36,3% contra o
piloto anterior. A qualidade da primeira passagem, porem, nao estava fechada:
30 candidatos viraram 34 e 39 viraram 44 depois da Sol. Reduzir leitura seria
degradar qualidade; a melhoria deve impedir que cobertura incompleta seja
chamada de pronta.

### Etapa 3 - prelint e preparacao do primeiro apply

| Episodio | Prelint ativo | Transicao ate one-shot | Candidatos | Report completo |
| --- | ---: | ---: | ---: | ---: |
| `jbFY16W5GTE` | 0,935s | 54,772s | 30 | 3.004.271 bytes |
| `fBaX4ixKkFo` | 0,735s | 16,496s | 39 | 2.641.486 bytes |

Processo: compilacao do manifesto, autocheck, matriz numerica, workbench,
calibracao, warnings e repair inventory.

Julgamento: o runtime e rapido, mas o gate semantico deu falso limpo. O
problema nao e CPU; e uma invariante ausente entre source dispositions,
`unreviewed`, `must_close` e `ready`. Reports de 2,6-3,0 MB tambem aumentam a
superficie de retomada, embora nao expliquem sozinhos o wall.

### Etapa 4 - one-shot inicial

| Episodio | Total | Persist | Finalizer | Dossier | Escritas de review |
| --- | ---: | ---: | ---: | ---: | ---: |
| `jbFY16W5GTE` | 4,925s | 0,068s | 1,510s | 2,303s | 1 |
| `fBaX4ixKkFo` | 4,064s | 0,080s | 1,496s | 1,669s | 1 |

Processo: preview hash-bound, apply, persistencia, build, finalizer, packet e
dossier.

Julgamento: ganho comprovado. Atomicidade e custo deterministico nao sao
gargalo. Preservar sem novas camadas.

### Etapa 5 - auditoria Sol inicial

O primeiro span abriu as 12:42:18, antes de `fBaX4ixKkFo` terminar autoria e
one-shot. O segundo span abriu as 13:03:18 e ambos fecharam por volta de
13:20:38.

| Medida | Valor |
| --- | ---: |
| Wall unico da wave | 38m19s |
| Span `jbFY16W5GTE` | 38m19s |
| Span `fBaX4ixKkFo` sobreposto | 17m20s |
| Findings | 5 major |

Os spans nao podem ser somados. A auditoria detectou:

- `jbFY16W5GTE`: 229 segmentos unreviewed, 100 must-close, warnings captured
  sem binding e tres conjuntos de erros numericos;
- `fBaX4ixKkFo`: 198 segmentos unreviewed, 83 must-close, retained support sem
  candidato e outcomes reportados descartados como incidentais.

Julgamento: a Sol preservou qualidade, mas foi usada cedo demais para descobrir
falhas deterministicas e de cobertura que deveriam bloquear o dossier. Isso
desperdicou a auditoria final e obrigou nova auditoria.

### Etapa 6 - primeira remediacao

Os spans de autoria de remediacao foram sobrepostos:

| Episodio | Span ativo | Checks/eventos pos-audit observados |
| --- | ---: | ---: |
| `jbFY16W5GTE` | 11m27,5s | 15 eventos no receipt antes do completion |
| `fBaX4ixKkFo` | 10m28,7s | 15 eventos no receipt antes do completion |

O wall entre o fim da auditoria inicial (13:20:38) e o resultado da reauditoria
02 (15:23:43) foi aproximadamente 2h03m05s. Apenas cerca de 11m28s formam a
uniao dos dois spans de autoria sobrepostos; o restante inclui checks,
correcoes, espera, gaps nao classificados e reauditoria.

Processo: completar source dispositions, criar nove candidatos adicionais,
corrigir bindings, warnings, numeros, calibracoes, regenerar packets e dossiers
e submeter novamente a Sol.

Julgamento: o manifesto unico reduziu a explosao de 67 candidatos do piloto
anterior para nove, mas warning IDs derivados do snapshot e revalidacao global
produziram muitos checks locais. A remediacao ainda nao e uma transacao unica.

### Etapa 7 - reauditoria 02 e correcao residual

A reauditoria 02 encontrou somente dois findings:

1. `jbFY16W5GTE`: warning dizia `captured` para G017, mas o ledger excluia o
   segmento 701;
2. `fBaX4ixKkFo`: G044 guardava duas vezes a mesma capacidade de 20 vagas.

Entre o relatorio da reauditoria 02 (15:23:43) e o ultimo dossier remediation-03
pronto (15:42:18) transcorreram cerca de 18m35s. Nesse periodo foram corrigidos:

- retained support source-backed para G017;
- validacao de calibracao de fonte duplicada sem link lexical artificial;
- `covered_explicit_duplicate` para repeticao oral numerica;
- tres warning decisions regeneradas;
- regressao dedicada e suite completa.

A rota de remediacao terminou `ready`, com `hard_blockers=0` e
`review_gate=0`, mas retornou erro depois da persistencia:
`materialized findings envelope is required before remediation`. Esse
comportamento e incorreto: uma precondicao nao pode falhar depois do commit.

### Etapa 8 - reauditoria final 03

| Episodio | Tempo | Dossier | Resultado |
| --- | ---: | ---: | --- |
| `jbFY16W5GTE` | 6m11,0s | 909.666 bytes | `passed/0` |
| `fBaX4ixKkFo` | 6m21,8s | 930.916 bytes | `passed/0` |

Wall unico da wave: cerca de 6m30s. Os hashes permaneceram inalterados.

Julgamento: a reauditoria focal e source-complete funciona. O ganho nao deve ser
generalizado para auditoria inicial, que ainda recebeu dossiers incompletos.

### Etapa 9 - completion

| Episodio | Completion | Resultado |
| --- | ---: | --- |
| `jbFY16W5GTE` | 0,167s | `complete/passed/0` |
| `fBaX4ixKkFo` | 0,384s | `complete/passed/0` |

Processo: registrar audit envelope, build terminal, validar packet e
fingerprints, gerar receipt, registrar terminal identity e avancar a fila.

Julgamento: ganho comprovado. Nao otimizar mais.

## Reconciliacao de wall e confiabilidade da medicao

| Classe | `jbFY16W5GTE` | `fBaX4ixKkFo` |
| --- | ---: | ---: |
| Wall do receipt | 3h34m01s | 3h08m10s |
| Comandos deterministas | 21,89s | 18,80s |
| Transicoes | 1m56,52s | 2m25,29s |
| Spans semanticos registrados | 1h20m20,9s | 1h47m45,9s |
| Gap nao classificado | 2h13m17,7s | 1h20m04,5s |
| Gap nao classificado / wall | 62,3% | 42,6% |
| Spans interrompidos excluidos | 9m26,7s | 9m34,2s |

O valor semantico de `fBaX4ixKkFo` inclui um span stale de `prelint_repair` de
53m04,4s. Removido esse erro, o tempo semantico confiavel cai para cerca de
54m09,7s. Portanto os receipts reconciliam matematicamente o wall, mas ainda nao
classificam operacionalmente a maior parte dele.

Os contadores tambem nao sao confiaveis para complexidade: ambos registram
`remediations=0` e `patches=0`; cada um registra apenas um finalizer e dois
builds, apesar dos dossiers remediation-02 e remediation-03 observados.

## Complexidade real

| Superficie | Piloto 011 anterior | Benchmark atual |
| --- | ---: | ---: |
| Episodios | 1 | 2 |
| Arquivos job-local | 182 | 28 + 25 |
| Arquivos repo-local do benchmark | incluido nos 182 | 16 |
| Total observado | 182 | 69 |
| Helpers Python por episodio | 27 | 0 |
| Crescimento pos-apply | 89,3% | 13,3% / 12,8% |
| Dossiers finais | 12 intermediarios | 3 revisoes por episodio |

Mesmo contando dois episodios, os artefatos cairam 62,1%. Em media por
episodio, a reducao e de aproximadamente 81,0%. Esse e um ganho estrutural
real. Ainda assim, 15 eventos pos-audit por episodio mostram que o trabalho
manual foi reduzido, nao eliminado.

## Anatomia dos dossiers finais

| Record type | `jbFY16W5GTE` | `fBaX4ixKkFo` |
| --- | ---: | ---: |
| Header | 415.744 B / 45,7% | 388.586 B / 41,7% |
| Transcript | 226.891 B / 24,9% | 247.275 B / 26,6% |
| Semantic workbench | 179.849 B / 19,8% | 193.167 B / 20,8% |
| Candidates | 43.993 B / 4,8% | 56.608 B / 6,1% |
| Numeric coverage | 29.681 B / 3,3% | 30.613 B / 3,3% |
| Ledger/calibracao/footer | 13.508 B / 1,5% | 14.667 B / 1,6% |

No header, `audit_navigation` e `audit_warnings` consomem 387 KB e 372 KB.
Header mais workbench representam 65,5% e 62,5% dos dossiers. Parte relevante
repete quotes, ranges, candidate IDs e decisoes que ja aparecem no transcript,
candidatos e workbench. A proxima reducao deve apagar duplicacao, nao criar
outro brief.

## As melhorias entregaram ganho ou burocracia?

| Melhoria | Evidencia | Veredito |
| --- | --- | --- |
| Identidade terminal e fila reconciliada | selecao correta, zero reprocesso duplicado | ganho forte; manter |
| Windows-native/preflight | 0,8-2,4s, zero falha | ganho comprovado; congelar |
| Manifesto autoral unico | nove candidatos pos-apply contra 67 antes; zero helper | ganho forte, ainda incompleto |
| One-shot | 4-5s e uma escrita inicial | ganho comprovado; congelar |
| Workbench/matriz numerica | ajudaram a fechar findings; primeiro dossier ainda falso-limpo | ganho parcial |
| Source dispositions exatas | dossiers finais 100% disposed | ganho forte implementado depois da primeira falha |
| Audit envelope/delta | reauditoria focal em 6m30s | ganho real, mas rota transacional ainda defeituosa |
| Warning IDs derivados | reabriram decisoes nao afetadas | burocracia regressiva |
| Telemetria atual | delta matematico zero | parcialmente util, operacionalmente enganosa |
| Dossier 3.1 | auditoria verificavel | qualidade preservada, superficie ainda duplicada |
| Mais gates/checks | 15 eventos pos-audit por episodio | sem retorno proporcional |

Conclusao: nao foi apenas complexidade. Houve reducoes grandes e mensuraveis.
Mas o pacote ainda falha onde mais custa: impedir falso-ready, remediar uma vez
e entregar uma unica superficie final para a Sol.

## Reducao de tempo por etapa sem degradar qualidade

| Etapa | Decisao |
| --- | --- |
| Selecao/preflight/contexto | Congelar. Ganho potencial adicional e irrelevante. |
| Leitura/autoria | Nao reduzir transcript nem leitura. Fazer a invariante source-complete bloquear falso-ready antes da Sol. |
| Prelint | Substituir falso-limpo por uma unica invariante deterministica; emitir somente repair inventory compacto ao modelo. |
| One-shot | Congelar. Nao adicionar preview, build ou finalizer. |
| Auditoria inicial | Despachar somente depois de todos os ramos `ready` e hashes congelados; remover duplicacao do dossier. |
| Remediacao | Uma transacao envelope-first, impact-scoped, com IDs locais estaveis e no maximo um rebuild. |
| Reauditoria | Manter delta focal com fallback integral automatico; nunca reler todo o episodio entre findings. |
| Completion | Congelar. Receipt terminal ja e autoridade suficiente. |
| Telemetria | Integrar contadores/spans a transacao existente e remover comandos manuais; nao criar novos campos. |

## Decisao final

Somente tres iniciativas justificam implementacao:

1. invariante source-complete antes de `ready`;
2. remediacao transacional local, envelope-first, com identidades estaveis;
3. uma unica superficie de auditoria deduplicada e despacho apenas no gate final
   da wave.

Nao implementar micro-otimizacao de Python, novo score de risco, novo papel,
novo chat, novo runner, mais campos de telemetria, reducao de transcript ou mais
um brief paralelo.
