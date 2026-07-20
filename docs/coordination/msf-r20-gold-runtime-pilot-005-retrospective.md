# Retrospectiva - Gold Runtime Pilot 005

Status: complete/passed/0

## Episodio e resultado

- video_id: `AqzF_M2mM04`
- titulo: `Dobrando A Conversao De Um Video De Vendas Na Pratica`
- categoria da fila: `VSL`
- duracao: 3.149 segundos
- volume: 395 segmentos, 9 chunks, 356 sinais e 12 calibracoes
- gold final: 9/9 reviews, 17 IDs unicos e calibracao `pass` em 9/12
- packet: cinco arquivos, vinculado ao episodio correto
- auditoria final: `gpt-5.6-sol/high`, `passed`, zero findings abertos
- lifecycle terminal: `complete/passed/0`
- fingerprints protegidos: os tres arquivos existentes no snapshot ficaram
  iguais antes/depois

O processamento gold permaneceu no Ubuntu WSL 2. Nao houve fallback para o
Python Windows nem leitura da extracao legada. O episodio terminou somente
depois da correcao dos dois findings numericos, reauditoria e completion com
validacao obrigatoria.

## Fontes da medicao

A linha do tempo foi reconstruida de:

- `episode_performance_report.json` e `episode_completion_receipt.json`;
- eventos UTC de `episode_fast_session.json`;
- timestamps UTC dos payloads, dossiers, audits e receipts job-local;
- metricas internas dos comandos WSL.

Ha tres numeros diferentes e todos precisam ser distinguidos:

1. **Janela observada completa:** 8h31m32,382s, da primeira acao WSL ao receipt
   terminal.
2. **Intervalos sem execucao:** 7h40m32,732s, formados por uma pausa de
   7h15m41,770s e outra de 24m50,962s.
3. **Janelas com atividade observavel:** aproximadamente 50m59,644s.

O receipt iniciado na selecao mede 8h24m31,759s e nao inclui os 7m04s de
verify/sync iniciais. Os comandos deterministas instrumentados somaram apenas
15,815s. Portanto, nem 8h31m nem 15,8s representam sozinhos o custo real: o
primeiro inclui inatividade; o segundo exclui leitura, julgamento e
orquestracao.

## Linha do tempo detalhada

| Etapa | Janela wall | Comando instrumentado | Resultado |
| --- | ---: | ---: | --- |
| Verify, sync, preflight, selecao e contexto | 7m04,534s | segundos; selecao 80ms e contexto 135ms | runtime Linux certificado, episodio rank 1 e contexto de 83.123 bytes |
| Leitura integral e payload inicial | 8m06,527s | n/a | 9 chunks lidos e 16 candidatos compostos |
| Tres prelints e primeiro fixed point | 10m02,761s | 146,89ms | framework corrigido, recall ampliado e 17 candidatos |
| Intervalo sem execucao | 7h15m41,770s | 0 | implementacao do proprio fluxo e retomada posterior; nao e custo de extracao |
| Retomada e dois prelints finais | 5m52,231s | 230,68ms | `prelint_clean`, hard blockers zero, calibracao 9/12 |
| Apply, finalizer, build e bundle inicial | 34,945s | 475,61ms | uma persistencia atomica, packet 5 e validator normal `pass` |
| Transicao ate o dossier ficar disponivel para auditoria | 8m14,126s | bundle interno 110,78ms | dossier de 129.547 bytes espelhado |
| Auditoria Sol inicial | 6m37,754s | julgamento semantico | `changes_requested`, dois findings numericos reais |
| Intervalo entre audit e retomada da correcao | 24m50,962s | 0 | o fluxo encerrou indevidamente antes da remediation |
| Patch focal e rederivacao do dossier | 2m36,926s | 14,745s | somente G004 e G016 alterados; outros 15 candidatos intactos |
| Reauditoria Sol | 48,464s | julgamento semantico | `passed`, zero findings |
| Registro, build complete e validate require-audit | 1m01,376s | 81,93ms | `complete/passed/0`, receipt terminal |

Somando somente as janelas ativas, o episodio consumiu cerca de **50m59,6s**.
O nucleo determinista representou aproximadamente 0,52% desse tempo ativo. O
gargalo principal continuou em leitura, composicao, transicoes entre fases e
loops de julgamento, nao em Python, build ou validacao.

## O que funcionou

1. A fila escolheu o episodio em 80ms e o contexto integral saiu em 135ms.
2. O runtime gold ficou Linux-native e os fingerprints permaneceram intactos.
3. O compilador bloqueou `framework` sem `steps` antes da persistencia.
4. O fixed point consolidou 17 candidatos, relacoes e calibracao 9/12.
5. A escrita inicial foi atomica: nove reviews em uma operacao.
6. O packet inicial ja era estruturalmente valido e o validator passou.
7. A auditoria Sol encontrou duas omissoes materiais que os gates mecanicos nao
   detectavam. O uso de Sol agregou qualidade real.
8. A remediation foi estreita e source-backed. A comparacao dos dossiers
   mostrou mudanca somente em G004, G016, header e footer.
9. A reauditoria passou na primeira tentativa e o completion receipt confirmou
   status, auditoria, packet, candidatos, calibracao e fingerprints.

## O que deu errado e por que

### 1. O benchmark misturou duas versoes do pipeline

O episodio comecou antes de todas as otimizacoes P0/P1 estarem no clone Linux.
Durante a pausa longa, scripts centrais foram modificados e sincronizados. O
resultado final e valido, mas o tempo nao e um benchmark limpo de uma versao
congelada. Isso tambem provocou verificacoes extras de paridade.

### 2. O autocheck detectava ausencia total, nao completude parcial de numeros

G004 e G016 ja tinham `numbers`, entao o gate nao perguntou se todos os numeros
materiais da evidencia estavam representados.

- G004 manteve na evidencia `86,8 5%` e `1.2x`, mas estruturou somente os outros
  valores do teste.
- G016 estruturou os faturamentos R$100 mil, R$140 mil, R$189 mil e R$264 mil,
  mas omitiu os inputs literais 40%, 35% e 40%.

O audit Sol foi correto. A falha estava na granularidade do fechamento numerico
pre-packet.

### 3. Cinco prelints consumiram quase 16 minutos de wall time

Os cinco comandos somaram menos de 0,4 segundo de computacao. O custo veio de
ler saidas, corrigir payload, recompor evidencia e reler o inventario. O fixed
point reduziu falsos loops, mas ainda nao incluiu uma matriz de fechamento de
todos os numeros materiais por candidato.

### 4. O dossier levou 8m14s para entrar na fase de auditoria

O bundle foi gerado em 111ms, mas o artefato espelhado so ficou disponivel oito
minutos depois. Isso foi transicao/orquestracao, nao custo de serializacao. O
dossier precisa ser o output imediato do mesmo comando que finaliza o packet.

### 5. `changes_requested` foi tratado como fim de turno

A auditoria terminou com dois findings, mas o episodio ficou parado ate nova
ordem do owner. Pelo contrato do projeto, remediation, reauditoria e completion
fazem parte do mesmo epico. O sistema so pode produzir fechamento terminal com
receipt `complete/passed/0` ou bloqueio externo real.

### 6. O primeiro assert da remediation usou campos derivados

O manifesto comparou `numbers` contendo campos `legacy_*` derivados com a fonte
manual, e o `--check` falhou sem escrita. O manifesto correto precisou ser
reconstruido a partir do JSON fonte canonico. A geracao de asserts deve remover
campos derivados automaticamente.

### 7. Uma mudanca documental invalidou a paridade de runtime

A atualizacao de status do plano alterou a assinatura de paridade e bloqueou a
primeira rota de remediation, embora nenhum executavel tivesse mudado. A
assinatura que autoriza gold write deve cobrir codigo, prompt, skill, schema e
dependencias executaveis; drift documental deve ser registrado separadamente.

### 8. A telemetria atribuiu inatividade a fases ativas

O relatorio agregou 7h21m em `prelint` e 41m57s em
`post_audit_remediation`, porque mediu o delta ate o evento seguinte. Isso
mistura pausa entre turnos com trabalho. Cada fase precisa de `started_at` e
`completed_at`, alem de uma categoria separada `inter_turn_idle`.

### 9. A checagem WSL posterior ao receipt terminal era desnecessaria

Depois do completion, o receipt ja declarou `terminal=true` e
`additional_verify_required=false`. Uma tentativa read-only posterior encontrou
o Windows atual sem distro visivel. Isso nao invalida a execucao concluida e nao
deve abrir nova investigacao: o receipt espelhado e a autoridade terminal.

## Reducao proposta por etapa

| Etapa | Atual ativo | Meta | Mudanca principal |
| --- | ---: | ---: | --- |
| Partida, paridade, selecao e contexto | 7m04s | 15-30s | congelar assinatura executavel e usar uma unica partida certificada |
| Leitura e payload inicial | 8m07s | 4-6m | compact v3, checklist por tipo e inventario numerico adjacente ao slab |
| Cinco prelints/fixed point | 15m55s | 1-2m | fechamento numerico completo e um unico inventario esparso estavel |
| Apply/finalizer/build | 35s | 10-20s | manter a operacao one-shot atual e reduzir apenas launcher/output |
| Transicao ao dossier | 8m14s | menos de 15s | retornar e espelhar dossier no mesmo processo do finalizer |
| Auditoria Sol inicial | 6m38s | 4-6m | dossier com matriz numerica fechada e ordem de leitura fixa |
| Remediation, reauditoria e completion | 4m27s | 0 quando prevenida; ate 2m30s se necessaria | patch fonte canonico e continuidade automatica dentro do mesmo epico |
| Fechamento adicional | 0 terminal; houve tentativa extra | 0 | respeitar `additional_verify_required=false` |

Meta para episodio de ate 500 segmentos, com runtime congelado:

- **9-13 minutos** quando a primeira auditoria passa;
- **12-16 minutos** quando uma remediation focal ainda for necessaria.

A meta de 6-10 minutos continua sendo objetivo de longo prazo, mas nao deve ser
declarada atingida enquanto leitura integral e auditoria Sol consumirem juntas
mais de oito minutos.

## Decisao

Manter WSL, fila persistente, compact v3, fixed point, one-shot, dossier integral,
auditoria final Sol, patch transacional e completion receipt. Nao reverter essas
partes.

Antes do proximo episodio, implementar o plano
`msf-r20-gold-runtime-pilot-006-optimization-plan.md`, congelar a versao do
pipeline e executar um benchmark limpo sem edicao de codigo ou documentacao
durante a janela medida.

