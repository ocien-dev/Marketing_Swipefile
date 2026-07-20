# MSF-R20 Gold Runtime Pilot 011 - Retrospectiva criteriosa

Status: complete
Episode: `NiT0-ABoVnk`
Run ID: `MSF-R20-gold-next-NiT0-ABoVnk-f3321e2ba8`
Architecture: `chronological_hybrid_v1`
Runtime: Windows native
Period: 2026-07-18 00:53:24Z to 10:36:58Z

## Conclusao executiva

O episodio terminou corretamente em `complete/passed`, com zero finding aberto,
142 candidatos unicos, calibracao 12/16 `pass`, packet exato de cinco arquivos
e fingerprints protegidos preservados.

O resultado final tem qualidade melhor e recall mais amplo que o primeiro
packet. Entretanto, o processo operacional falhou no objetivo de tempo e
simplicidade:

- wall total: 9h43m33,4s;
- comandos deterministas: 40,73s;
- leitura e autoria inicial: 34m51,3s;
- reauditoria registrada: 8h06m59,2s, contaminada por espera, interrupcao e
  perda de uma execucao Sol durante troca de modelo;
- 182 arquivos job-local, incluindo 27 helpers Python;
- 9 finalizers, 6 builds e 5 audit bundles;
- 12 dossiers intermediarios entre revisoes 012 e 050;
- primeiro apply com 75 candidatos; final com 142, aumento de 67 candidatos ou
  89,3% depois de auditorias e remediacoes.

O runtime nao foi o gargalo. O custo veio de tres causas:

1. o primeiro payload nao fechou classes de erro que o workbench prometia
   antecipar;
2. a remediacao virou uma API manual paralela ao pipeline oficial;
3. a auditoria nao produziu um envelope duravel antes de uma interrupcao de
   modelo, fazendo a reauditoria permanecer aberta por horas.

Veredito: as melhorias recentes entregaram ganhos reais de prelint, auditoria
inicial, recall e protecao transacional, mas o pacote OPT-010 falhou no
benchmark end-to-end. Parte relevante apenas deslocou a complexidade do runtime
para a camada model-facing e para helpers job-local.

## Fontes de evidencia

- `.codex-work/runs/gold-NiT0-ABoVnk-20260717/episode_completion_receipt.json`;
- `.codex-work/runs/gold-NiT0-ABoVnk-20260717/episode_performance_report.json`;
- `.codex-work/runs/gold-NiT0-ABoVnk-20260717/episode_fast_session.json`;
- `.codex-work/runs/gold-NiT0-ABoVnk-20260717/runtime_retrospective.md`;
- dossiers 012, 013, 015, 017, 019, 022, 027, 034, 037, 043 e 050;
- `audit_037_changes_requested.json`, `final_reaudit_delta_050.jsonl` e
  `audit_passed_050.json`;
- `msf-r20-gold-runtime-pilot-009-retrospective.md` e sua analise de
  otimizacao como baseline comparavel.

## Resultado de qualidade

| Controle | Resultado final |
| --- | --- |
| Lifecycle | `complete` |
| Auditoria | `passed`, zero findings abertos |
| Candidatos | 142 unicos |
| Calibracao | 12/16 cobertos; minimo 4; sem duplicata de target |
| Transcript | 1.087 segmentos |
| Ledger | 1.087 entradas; 765 captured, 140 merged, 182 excluded |
| Packet | cinco arquivos canonicos |
| Fingerprints protegidos | preservados |
| Validacao obrigatoria | `pass`, zero erro |

Os 142 candidatos nao provam qualidade isoladamente, mas o crescimento de 75
para 142, combinado com findings Sol fechados e auditoria final aprovada,
confirma que o primeiro packet tinha recall e atomicidade insuficientes.

## Linha do tempo reconciliada

### Wall e spans semanticos

| Etapa | Inicio UTC | Fim UTC | Tempo medido | Observacao |
| --- | --- | --- | ---: | --- |
| Selecao | 00:53:24.871 | 00:53:24.913 | 0,04s | 283 elegiveis; 1.087 segmentos selecionados. |
| Preflight e contexto | 00:53:24.917 | 00:53:47.328 | 1,01s ativos | Duas geracoes; 21,40s de transicao entre elas. |
| Leitura cronologica e autoria inicial | 00:53:25.897 | 01:28:17.222 | 34m51,3s | Contexto de 292.064 bytes. |
| Previews deterministas | eventos ate 01:38:17 |  | 5,08s ativos | Quatro previews contabilizados. |
| Prelints deterministas | eventos ate 01:37:07 |  | 2,22s ativos | Tres prelints oficiais. |
| Reparo semantico de prelint | 01:28:18.713 | 01:38:16.335 | 2m05,7s | Tres spans; houve gaps entre spans. |
| Apply, build, finalizer e dossier inicial | 01:38:33.561 | 01:38:38.063 | 4,50s | Primeiro apply com 75 candidatos. |
| Auditoria Sol integral inicial | 01:38:38.094 | 01:48:21.986 | 9m43,9s | Encontrou problemas materiais. |
| Autoria da primeira remediacao | 01:48:22.001 | 01:58:57.766 | 10m35,8s | Mais lenta que no piloto 009. |
| Comandos pos-auditoria | eventos ate 03:06:35 |  | 27,21s ativos | Multiplicaram finalizers, builds e dossiers. |
| Reauditoria Sol registrada | 02:29:57.992 | 10:36:57.169 | 8h06m59,2s | Span inclui espera, interrupcoes e uma execucao perdida; nao representa compute Sol. |
| Completion terminal | 10:36:57.171 | 10:36:58.004 | 0,83s | Audit registrado, build final, validator e fila avancada. |
| Closeout semantico | 10:36:58.015 | 10:36:58.031 | 0,02s | Artefatos de fechamento. |

### Reconciliacao do wall

| Classe | Tempo | Participacao aproximada |
| --- | ---: | ---: |
| Spans semanticos | 9h04m15,9s | 93,2% |
| Comandos deterministas | 40,7s | 0,1% |
| Transicoes entre eventos | 3m34,3s | 0,6% |
| Gap nao classificado | 38m36,6s | 6,6% |
| Total reconciliado | 9h43m33,4s | 100% |

Os percentuais se sobrepoem levemente por arredondamento e pela reconciliacao
entre eventos e spans. O receipt fecha com delta zero.

## O que foi feito no processamento

### 1. Selecao e preflight

O seletor escolheu `NiT0-ABoVnk`, confirmou 1.087 segmentos, carregou contexto
compacto e tres slabs e registrou o timer do epico. Nao houve problema de
Python, temp, quoting, data root ou permissao.

### 2. Leitura e composicao

O transcript foi lido cronologicamente. A composicao inicial gerou 46
candidatos; a fase de fechamento elevou a carga para 75 antes do primeiro
apply. O `semantic_workbench`, a matriz numerica e os blocos de closure foram
usados como navegacao e controle.

### 3. Preview e prelint

Foram executados quatro previews e tres prelints. O trabalho semantico de
reparo levou 2m05,7s, enquanto os comandos consumiram poucos segundos. O ganho
em relacao ao piloto 009 foi real: 6m18,7s caiu para 2m05,7s, reducao de 66,8%.

### 4. Primeiro apply e finalizacao

O primeiro apply persistiu uma vez e gerou build, finalizer e dossier em 4,50s.
Esse trecho comprovou novamente que one-shot, atomicidade, packet e hashes nao
sao o gargalo.

### 5. Auditorias e remediacoes

A auditoria integral e as revisoes seguintes encontraram classes materiais:

- claim e evidence cobrindo proposicoes diferentes;
- suporte contextual marcado como captured/merged;
- blocos materiais excluidos como low signal, anecdote ou fala do host;
- calibracoes ligadas por proximidade tematica, nao equivalencia;
- duplicacao e ownership incorreto de numeros;
- unidade, periodo e funcao numerica incompletos;
- fala de transicao do host incorporada ao claim;
- fragmentacao de ISO 27001 e resultados mensais;
- evidencia atomica e steps desalinhados.

As revisoes chegaram a `remediation-050`. O episodio terminou com mais 67
candidatos que o primeiro apply. A correcao foi source-backed e a qualidade
final passou, mas o caminho normal deixou de ser one-shot na pratica.

### 6. Contorno terminal

A execucao Sol integral que deveria emitir o veredito foi perdida durante uma
troca de modelo. O contorno foi materializar o audit 037, gerar um delta
verificavel 037 -> 050 e executar reauditoria focal sobre seis findings e seus
invariantes. A Sol fechou F037-01 a F037-06, confirmou fingerprints, ledger fora
do escopo e packet e retornou `passed`. O completion encerrou em 0,83s.

## Comparacao com o piloto 009

O piloto 009 documentou o mesmo ID em uma execucao anterior com 59 candidatos,
calibracao 5/16 e 74m26,5s. O receipt atual e a fonte de verdade da execucao
analisada; a coexistencia das duas conclusoes tambem revela que identidade
terminal entre data roots/receipts/fila precisa ser reconciliada antes de nova
selecao.

| Etapa | Piloto 009 | Piloto 011 | Variacao | Julgamento |
| --- | ---: | ---: | ---: | --- |
| Selecao e contexto | 1,38s | 1,05s ativos | melhora pequena | Estavel; nao otimizar mais. |
| Leitura/autoria | ate 36m16,8s no intervalo | 34m51,3s medidos | comparavel, ganho pequeno | Telemetria melhor; tempo ainda alto. |
| Reparo de prelint | 6m18,7s | 2m05,7s | -66,8% | Ganho forte. |
| Auditoria integral | 16m48,2s | 9m43,9s | -42,1% | Ganho real, ainda com findings conhecidos. |
| Autoria da remediacao | 6m32,2s | 10m35,8s | +62,1% | Regressao. |
| Total | 74m26,5s | 583m33,4s | +683,9%; 7,84x | Falha do benchmark. |
| Candidatos finais | 59 | 142 | +140,7% | Recall maior; superficie muito maior. |
| Calibracoes cobertas | 5/16 | 12/16 | +140% | Ganho de qualidade. |
| Helpers Python job-local | 7 reportados | 27 | +285,7% | Complexidade piorou. |

## Julgamento das melhorias recentes

| Melhoria | Evidencia atual | Veredito | Decisao |
| --- | --- | --- | --- |
| Windows native e preflight | Cerca de 1s ativo, zero falha de runtime | ganho comprovado | Congelar. |
| Risk tiers, fixed point e matriz numerica | Reparo de prelint caiu 66,8% | ganho forte | Manter o nucleo. |
| One-shot e receipt terminal | Apply/finalizacao em segundos, hashes preservados | ganho comprovado | Manter e voltar a tornar obrigatorio na pratica. |
| Workbench source-first | Ajudou cobertura; primeiro packet ainda omitiu classes conhecidas | ganho parcial | Substituir a interface fragmentada por um manifesto unico. |
| Dossier 3.1/two-layer | Auditoria caiu 42,1%; dossier cresceu para 1,19 MB | ganho parcial | Manter prova integral; reduzir somente a entrada primaria. |
| Audit-to-patch scaffold | Remediacao subiu 62,1%; 27 helpers foram criados | benchmark reprovado | Substituir por transacao oficial unica. |
| Delta de reauditoria | Contorno final fechou seis findings sem reextrair | ganho forte | Promover como rota unica pos-finding. |
| Telemetria semantica | Isolou leitura, mas marcou 8h de espera como reauditoria e contou zero patches/remediacoes | ganho parcial e enganoso | Corrigir estados, nao adicionar mais spans. |
| Mais heuristicas/gates | Classes conhecidas ainda chegaram a Sol | sem retorno proporcional | Nao adicionar. |

## Complexidade adicionada

- 182 arquivos no job-dir;
- 137 JSON, 14 JSONL e 27 helpers Python;
- 12 dossiers de auditoria;
- 34 artefatos classificados como patch ou helper de patch;
- 27 artefatos de calibracao;
- 19 artefatos de ledger;
- 9 finalizers, 6 builds e 5 audit bundles;
- telemetria final registra `patches=0` e `remediations=0`, contrariando os
  artefatos e a execucao observada;
- contexto model-facing permaneceu em 292 KB;
- prelint completo ficou em 2,63 MB;
- dossier inicial ficou em 1,19 MB, acima dos 893 KB do piloto 009.

Esse inventario nao e apenas armazenamento. Ele aumenta escolhas, releituras,
risco de aplicar manifest stale e custo de retomar apos interrupcao.

## Causas-raiz

### CR-01 - Duas fontes de decisao

Os candidatos eram a fonte semantica, mas ledger e calibracao foram corrigidos
tambem por patches pos-build. Cada rebuild recriava derivados e exigia nova
aplicacao. A solucao e uma unica fonte autoral antes do build.

### CR-02 - Workbench amplo, nao executavel

O workbench mostrou riscos, mas a decisao source-backed continuou espalhada
entre payload, helpers, review patches, ledger rebind e redirects. Ele reduziu
triagem, nao eliminou a API manual.

### CR-03 - Auditoria descobriu erros ja conhecidos

As fixtures OPT-010 cobriam evidence drift, numeros, produto e calibracao, mas
o primeiro packet ainda falhou nessas classes. Teste verde de fixture nao
provou que a superficie model-facing levava o executor a fechar o inventario.

### CR-04 - Auditoria sem commit duravel de veredito

O modelo Sol terminou ou foi interrompido sem envelope materializado. O span
ficou aberto e a troca de modelo perdeu o resultado. O audit precisa ser o
primeiro artefato duravel da fase, ligado ao hash do dossier.

### CR-05 - Identidade terminal dividida

O mesmo episodio aparece como completo no piloto 009 e foi processado na fila
atual. A explicacao plausivel e a transicao de data root/runtime, mas o seletor
nao pode depender somente do estado local da fila. Source hash, arquitetura,
completion receipt e data root canonico precisam formar uma identidade unica.

## O que deve ser preservado

- leitura cronologica integral;
- `chronological_hybrid_v1`;
- source quotes verbatim;
- risk tiers e `must_close` versus `audit_only`;
- matriz numerica e checagem raw/value/unit;
- preview receipt ligado ao apply;
- persistencia atomica e packet de cinco arquivos;
- auditoria final Sol/high;
- reauditoria focal por delta com invariantes;
- fingerprints e completion receipt terminal.

## O que deve ser removido do caminho normal

- helper Python especifico por episodio;
- ledger rebind como patch semantico separado;
- redirect de calibracao reaplicado depois de cada build;
- finalizer e dossier gerados antes de o manifesto autoral estar fechado;
- mais de uma taxonomia model-facing para cobertura/closure/binding;
- auditoria reiniciada do zero depois de finding;
- spans que permanecem abertos atraves de interrupcao ou troca de modelo;
- otimizacao adicional de Python, shell ou preflight sem evidencia de gargalo.

## Decisao

O proximo trabalho nao deve ser OPT-010 incremental. Deve substituir a camada
manual por um manifesto semantico autoritativo e apagar caminhos paralelos.
Somente as quatro mudancas de alto impacto do plano
`MSF-R20-GOLD-RUNTIME-SIMPLIFICATION-011` devem entrar.

