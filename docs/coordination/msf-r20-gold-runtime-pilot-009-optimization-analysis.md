# MSF-R20 Gold Runtime Pilot 009 - Analise de Otimizacao

Status: complete
Episode: `NiT0-ABoVnk`
Comparison baseline: pilot 008, `eCaODMtU5GY`

## Conclusao executiva

As melhorias OPT-008 entregaram ganho tecnico real, mas nao reduziram o tempo
end-to-end. O piloto 009 terminou em 1h14m26,5s, contra 1h07m51,2s no piloto
008: aumento de 6m35,3s, ou 9,7%.

O ganho mais forte foi no fechamento/prelint: 29m27s caiu para cerca de 6m19s,
reducao de 78,6%, e os ciclos oficiais cairam de dez para tres. Selecao e
contexto tambem cairam de 9,1s para 1,4s. Esses ganhos provam que risk tiers,
matriz numerica, fixed point e one-shot devem ser preservados.

O ganho foi consumido por duas frentes semanticas:

- o intervalo entre contexto e primeiro prelint chegou a 36m16,8s, sem spans
  suficientes para separar leitura, composicao, helpers e pausas;
- a auditoria inicial subiu de 9m40,2s para 16m48,2s e ainda encontrou cinco
  findings materiais.

Portanto, a resposta e mista: houve menos burocracia deterministica e menos
loops de prelint, mas a superficie autoral e de auditoria ficou mais complexa.
Nao e correto reverter o nucleo novo; e necessario consolidar a camada
semantica e eliminar helpers e artefatos intermediarios volumosos.

## Resultado de qualidade

O episodio terminou `complete/passed/0`, com 21 reviews, 59 candidatos unicos,
calibracao `pass`, packet de cinco arquivos e fingerprints preservados. A
auditoria inicial encontrou cinco lacunas reais:

1. mecanica e numeros do trial product-led em G049;
2. comparacao economica de KYC manual versus automatizado;
3. evidencia incorreta em G051;
4. contraste omitido entre lift de headline e utilidade valorizada;
5. evidencia e calibracao de PMF em G052.

A auditoria continuou indispensavel: sem ela, o packet teria sido
estruturalmente valido, mas semanticamente incompleto. O problema nao e a
existencia da auditoria, e sim o custo para navegar a superficie e o fato de
classes conhecidas de recall/evidencia/calibracao ainda chegarem ate ela.

## Tempo por etapa

| Etapa | Piloto 008 | Piloto 009 | Variacao | Diagnostico |
| --- | ---: | ---: | ---: | --- |
| Selecao, preflight e contexto | 9,13s | 1,38s | -84,9% | Ganho real; manter. |
| Leitura e composicao inicial | 13m19s | ate 36m16,8s no intervalo observavel | nao comparavel com precisao | O piloto 009 nao marcou o span; o intervalo inclui trabalho e gaps. |
| Fechamento e prelint | 29m27s | 6m18,7s | -78,6% | Principal ganho do OPT-008. |
| Apply, build e dossier | 1,54s | 1,59s | +0,05s | Estavel e irrelevante no total. |
| Auditoria Sol inicial | 9m40s | 16m48s | +73,8% | Principal regressao medida. |
| Transporte do audit | 3m07s | sem fase material separada | eliminada como gargalo | A copia ainda existe, mas voltou a segundos. |
| Autoria e apply da remediacao | 5m55s | 6m34,7s | +11,3% | Scaffold ajudou, mas helpers e raw ASR ainda criaram retrabalho. |
| Reauditoria e completion | 5m29s | 4m09,4s | -24,1% | Ganho real; preservar delta focal. |
| Total | 1h07m51s | 1h14m27s | +9,7% | O ganho do prelint foi absorvido por autoria e auditoria. |

## Reconciliacao do piloto 009

- wall terminal: 74m26,5s;
- comandos deterministas: 7,27s;
- spans semanticos registrados: 33m46,5s;
- gap nao classificado: 40m32,6s;
- leitura/composicao ocorreu no gap inicial de 36m16,8s, mas nao pode receber
  esse tempo integral sem inventar atribuicao;
- o completion receipt reconciliou o total sem chamar o gap de idle.

O resultado confirma novamente que otimizar Python, build ou WSL nao reduzira
materialmente o wall. O custo esta no trabalho semantico e na navegacao de
artefatos.

## O que melhorou de verdade

### 1. Risk tiers e fixed point

Os ciclos de prelint cairam de dez para tres e os reparos de 29m27s para
6m16,8s. `must_close` versus `audit_only`, lineage e a matriz numerica
eliminaram grande parte da disposicao repetitiva observada no piloto 008.

### 2. Runtime e one-shot

Selecao, contexto, checks, persistencia, builds, dossiers e completion somaram
poucos segundos. Nao houve falha de WSL, quoting, cwd, Python Windows ou
fallback. Essa arquitetura deve permanecer congelada.

### 3. Reauditoria focal

A reauditoria caiu para 4m09s e verificou apenas findings, efeitos do patch e
invariantes. O packet final preservou qualidade e provenance.

### 4. Telemetria

Pela primeira vez os spans de prelint, auditoria, remediacao e reauditoria
ficaram separados de runtime e gaps. A medicao ainda e incompleta, mas deixou
de atribuir todo o wall a comandos ou idle.

## O que acrescentou complexidade sem retorno proporcional

### 1. Muitos helpers job-local

Antes do packet foram usados `refine_payload.py`, `close_residual.py`,
`finalize_preinput.py` e `close_warning_gate.py`. Na auditoria/remediacao foram
usados `audit_dossier_extract.py`, `build_audit_remediation.py` e
`check_remediation.py`. Eles resolveram o episodio, mas representam uma API
manual paralela ao pipeline oficial.

### 2. Artefatos grandes

O contexto teve 292 KB, o prelint completo 2,71 MB e o dossier inicial 893 KB.
O risk brief ficou em 50 KB, mas ainda apontou para um dossier grande e 187
superficies de risco. A reducao de stdout nao reduziu na mesma proporcao a
navegacao semantica.

### 3. Indice semantico amplo demais

O indice ajudou a ordenar riscos e numeros, mas nao destacou suficientemente
os blocos de produto no fim do episodio: economia de KYC, trial product-led,
feedback de clientes, valor percebido e PMF. Ele funcionou como navegador de
evidencia, nao como redutor confiavel de tempo.

### 4. Scaffold de remediacao ainda fragil

Dois checks read-only foram necessarios porque o raw aproximado de ASR e o
escopo numerico nao correspondiam integralmente a fonte persistida. Nao houve
escrita indevida, mas a autoria continuou manual e cara.

### 5. Calibracao estrutural versus semantica

O primeiro packet passava com 4/16, mas um target de PMF semanticamente coberto
continuava `fail`. O minimo contratual evita insuficiencia estrutural, mas nao
prova que todos os targets equivalentes foram ligados corretamente.

## Julgamento das melhorias OPT-008

| Melhoria | Julgamento | Decisao |
| --- | --- | --- |
| WSL Linux-native | ganho comprovado | manter sem alteracao |
| Selecao/fila persistente | ganho comprovado | manter |
| Risk tiers e fixed point | ganho forte | manter e simplificar a saida |
| Matriz numerica | ganho parcial | ampliar para cobertura de proposicao e produto |
| Claim/evidence closure | ganho parcial | tornar binding por range obrigatorio |
| Dry-run consolidado | ganho forte | manter, com um unico artefato compacto |
| Risk brief | ganho insuficiente | redesenhar como workbench de cobertura |
| Delta de reauditoria | ganho comprovado | manter |
| Scaffold de remediacao | ganho insuficiente | substituir por compilador oficial audit-to-patch |
| Mais gates/checkpoints | sem potencial | nao adicionar |

## Metas realistas para o proximo episodio comparavel

| Etapa | Piloto 009 | Meta segura |
| --- | ---: | ---: |
| Selecao e contexto | 1,38s | <= 3s |
| Leitura e payload | nao isolado; intervalo 36m17s | 12-16m |
| Fechamento/prelint | 6m19s | 3-5m |
| One-shot/dossier | 1,59s | <= 3s |
| Auditoria inicial | 16m48s | 6-9m |
| Remediacao focal | 6m35s | 2-4m |
| Reauditoria/completion | 4m09s | 2-3m |
| Total sem finding | 74m27s observado | 20-27m |
| Total com remediacao | 74m27s observado | 25-34m |

Uma meta de dez minutos para entrevistas de aproximadamente 1.100 segmentos
nao e segura sem degradar leitura e auditoria. O objetivo de alto potencial e
reduzir a metade do tempo atual, mantendo a auditoria final e elevando a
qualidade do primeiro packet.
