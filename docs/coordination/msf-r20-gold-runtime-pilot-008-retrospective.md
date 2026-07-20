# MSF-R20 Gold Runtime Pilot 008 - Retrospectiva

Status: complete
Episode: `eCaODMtU5GY`
Title: `A Estrutura De VSL Que Ja Vendeu +70MM Em 1 Ano | Elton Cipriano - Segredos da Escala #044`
Run: `start-20260716T211000479Z`

## Resultado terminal

- 1.079 segmentos limpos revisados integralmente em 21 chunks;
- 49 candidatos finais, todos com IDs unicos;
- 773 sinais reconciliados no ledger derivado;
- calibracao com 16 targets e status `pass`;
- auditoria Sol inicial encontrou seis falhas materiais;
- uma remediacao transacional corrigiu os seis findings;
- reauditoria final Sol `passed`, com zero findings abertos;
- lifecycle `complete`, `audit_status=passed`;
- validador com auditoria obrigatoria `pass/errors=[]`;
- packet com exatamente cinco arquivos;
- quatro fingerprints protegidos inalterados.

## Autoridades de tempo

O intervalo terminal vai de `2026-07-16T21:10:00.479981Z` a
`2026-07-16T22:17:51.697175Z`, totalizando **1h07m51,217s**.

As fontes usadas foram `episode_fast_session.json`,
`episode_performance_report.json`, receipts dos comandos e mtimes dos artefatos.
Os limites por artefato representam wall time entre marcos observaveis; eles nao
devem ser confundidos com tempo interno puro do modelo.

## Tempo por etapa

| Etapa | Inicio/fim observavel | Wall | O que ocorreu |
| --- | --- | ---: | --- |
| Selecao, preflight certificado e contexto | 21:10:00.480 -> 21:10:09.607 | **9,127s** | Selecao da fila, verificacao do runtime WSL, fontes, fingerprints e emissao do contexto compacto. |
| Leitura integral e autoria inicial | 21:10:09.607 -> 21:23:29.068 | **13m19,461s** | Leitura cronologica dos 1.079 segmentos; composicao de 21 reviews e 47 candidatos iniciais. |
| Diagnostico e reparo de prelint | 21:23:29.113 -> 21:52:56.184 | **29m27,071s** | Dez prelints, fechamento numerico, aliases, evidencias, risk recall e 224 disposicoes canonicas de warning. |
| Transicao ate o one-shot | 21:52:56.184 -> 21:53:39.973 | **43,789s** | Preparacao da invocacao final depois do preview limpo. |
| Persistencia, finalizer, build, validator e dossier | 21:53:39.973 -> 21:53:41.509 | **1,536s** | One-shot deterministico e packet inicial. |
| Auditoria Sol inicial | 21:53:41.509 -> 22:03:21.757 | **9m40,248s** | Leitura adversarial do dossier source-complete e registro de seis findings. |
| Transporte e validacao do audit no Linux | 22:03:21.757 -> 22:06:28.360 | **3m06,604s** | Tentativas UNC, `/mnt/c` e `C:\\tmp`; transferencia final por conteudo codificado. |
| Scaffold, autoria e apply da remediacao | 22:06:28.360 -> 22:12:23.039 | **5m54,679s** | Geracao do patch, um check bloqueado com inventario numerico completo, correcao e apply unico bem-sucedido. |
| Reauditoria, prova de invariantes e completion | 22:12:23.039 -> 22:17:51.693 | **5m28,654s** | Delta oficial rejeitado, prova integral corrigida, reauditoria Sol, registro do audit e completion. |
| **Total terminal** | 21:10:00.480 -> 22:17:51.697 | **1h07m51,217s** | Receipt terminal `complete/passed/0`. |

Os comandos deterministas somaram apenas **6,588s** de runtime e **6,768s** de
wall de ferramenta. A telemetria classificou **65m50,715s** como
`inter_turn_idle_ms`, mas `semantic_spans=[]`; portanto esse valor e, na
realidade, wall sem atribuicao entre leitura, autoria, julgamento, navegacao e
orquestracao. Nao ha evidencia para chama-lo de ociosidade.

## O que foi feito

### 1. Selecao e preparacao

O seletor usou a fila persistente e abriu o episodio sem pesquisa manual. O
runtime ativo permaneceu 100% Linux-native: clone, virtualenv, data root, temp e
job principal no WSL. Nao houve falha de inicializacao, quoting, PowerShell ou
paridade nessa etapa.

### 2. Leitura e payload inicial

Foram produzidos 21 reviews completos e 47 candidatos iniciais. O payload
compacto preservou quotes e ranges source-backed. A leitura integral ficou em
13m19s, dentro de uma faixa razoavel para 1.079 segmentos, mas ainda acima da
meta de 10-12 minutos proposta para esse porte.

### 3. Dez ciclos de prelint

Os ciclos evoluiram assim:

1. 13 issues de compiler: quatro themes fora do vocabulario, ocorrencias
   numericas invalidas, `raw` ausente e unidades invalidas;
2. evidencia de G044 nao sustentava seu `raw` numerico;
3. autocheck com 112 blockers numericos e 11 clusters de risk recall;
4. role numerico invalido em G037;
5. autocheck com 22 blockers e tres clusters, ja com 48 candidatos;
6. tres blockers numericos;
7. dois blockers numericos;
8. review gate com 80 superficies e zero hard blocker;
9. review gate com 79 superficies e zero hard blocker;
10. prelint limpo.

O inventario final tinha 230 linhas, canonicalizadas em 224 warning IDs. Tres
helpers job-local (`refine_episode_payload.py`,
`close_prelint_residuals.py` e `dispose_audit_warnings.py`) concentraram a
maior parte da autoria. O custo nao foi computacional: os dez prelints consumiram
segundos; a interpretacao e a reescrita manual consumiram 29m27s.

### 4. One-shot inicial

Com o estado limpo, persistencia, finalizer, build, validador e dossier levaram
1,536s. Esta etapa confirmou que o runtime e os gates deterministas nao sao o
gargalo atual.

### 5. Auditoria Sol inicial

O Sol revisou o dossier de 811 KB e encontrou seis falhas reais:

1. omissao da trajetoria de 2023: 13 ofertas, cerca de 10 sucessos e patamar de
   mais de R$1 milhao, corrigida com o novo G049;
2. G030 omitia o comparador de R$10 mil;
3. G039 registrava `value=2 minutes` para um `raw=30`;
4. G027 afirmava autoedicao, reducao de elenco e gravacao em casa sem incluir
   612-616 na evidencia;
5. G038 omitia os 10-12 meses de vendas sustentadas em sete digitos;
6. G008 omitia o caso de demonstracao que falhou e sua incerteza de
   atribuicao/ASR.

Esses findings elevaram materialmente a qualidade. A auditoria final Sol nao
deve ser removida ou rebaixada; o objetivo e impedir que classes ja conhecidas
cheguem ate ela.

### 6. Remediacao

O primeiro check bloqueou corretamente antes de escrever porque a evidencia
ampliada introduziu numeros ainda nao estruturados: `50` em G008, a sequencia
R$6k -> R$5k -> R$4k -> R$3k -> R$2,5k em G027 e o ano 2023 em G049. O patch
final estruturou ou caveatou cada ocorrencia e foi aplicado atomicamente uma
unica vez.

### 7. Reauditoria e completion

O delta oficial rejeitou o estado correto por duas causas de implementacao:

- G049 era insert de um finding sem `candidate_ids`, por isso nao entrou no
  conjunto de candidatos afetados;
- o agregado de fingerprints incluiu `verified_at`, embora os quatro mapas
  `before/after` fossem identicos.

A primeira prova alternativa tambem comparou o bloco de transcript do dossier,
que contem campos de ledger derivados, como se fosse a fonte imutavel. A prova
correta comparou apenas `clean_index`, `start`, `duration` e `text`, confirmou
43 candidatos nao afetados identicos, calibracao preservada e fingerprints
4/4. A reauditoria entao passou e a completion terminou em 110,64 ms, com cerca
de dois segundos adicionais para artefatos finais.

## O que funcionou

1. **WSL:** start e contexto em 9,127s, sem PowerShell indevido, sem quoting e
   sem fallback para Windows.
2. **Qualidade final:** os seis findings foram materialmente corrigidos e o
   episodio terminou `complete/passed/0`.
3. **Atomicidade:** checks falhos fizeram zero writes; houve um unico apply
   efetivo da remediacao.
4. **Auditoria Sol:** encontrou omissoes de recall, numero e evidencia que os
   gates mecanicos nao deveriam autoaprovar.
5. **Runtime deterministico:** one-shot, build, validators e completion foram
   sub-segundo ou quase sub-segundo.

## O que falhou ou custou demais

1. **Fechamento semantico volumoso:** 224 warnings receberam disposicao quase
   individual, embora poucos fossem riscos materiais.
2. **Bulk disposition insegura:** um cluster numerico de 2023 foi marcado como
   incidental/contextual e reapareceu como finding G049.
3. **Matriz numerica tardia:** comparadores, sequencias e inconsistencias entre
   `raw`, valor e unidade foram descobertos em ondas sucessivas.
4. **Suporte de claim incompleto:** o compilador nao fechou automaticamente a
   diferenca entre o texto de G027 e os atos realmente citados na evidencia.
5. **Counterexample fora do foco:** a demonstracao falha de G008 estava na
   vizinhanca semantica, mas nao entrou no candidato nem em caveat antes do
   packet.
6. **Transporte cruzado:** 3m06s foram gastos apenas para mover o audit do
   mirror Windows para o job Linux.
7. **Delta fragil:** a classe registrada no piloto 007 voltou a exigir prova ad
   hoc e leitura adicional.
8. **Telemetria incompleta:** os spans semanticos previstos nao foram usados;
   65m50s ficaram rotulados de forma enganosa como idle.

## Como reduzir sem degradar qualidade

| Etapa | Atual | Meta segura | Mudanca proposta | Protecao de qualidade |
| --- | ---: | ---: | --- | --- |
| Start/contexto | 9,127s | 5-10s | Manter rota atual; nenhuma reengenharia. | Verificador WSL e fingerprints continuam obrigatorios. |
| Leitura/payload | 13m19s | 10-12m | Entregar matriz de numeros, adjacencias e vocabulary scaffold junto ao contexto compacto. | Leitura integral continua obrigatoria; nenhum claim automatico. |
| Prelint/reparo | 29m27s | 4-7m | Separar `must_close` de `audit_only`, deduplicar por lineage e produzir um unico repair manifest. | Toda trajetoria, resultado, before/after, counterexample e claim support permanece item-level. |
| One-shot | 1,536s | <5s | Manter. | Mesmos asserts, receipt e atomicidade. |
| Auditoria Sol | 9m40s | 6-8m | Risk map menor e ordenado, sem repeticao de 224 warnings; dossier continua source-complete. | Sol/high e transcript integral permanecem. |
| Transporte audit | 3m06s | <2s | Gravar o envelope diretamente no job Linux e espelhar somente depois do receipt. | Hash fisico/semantico e `--check` permanecem. |
| Remediacao | 5m55s | 3-5m | Scaffold inclui todas as ocorrencias numericas introduzidas pela nova evidencia. | Check completo antes do apply; nenhuma correcao automatica de claim. |
| Reaudit/completion | 5m29s | 1-2m | Corrigir delta canonico e confiar no receipt terminal. | Fallback integral somente quando um invariante real divergir. |

Meta para proximo episodio comparavel:

- **17-23 minutos** quando a auditoria inicial passa;
- **22-30 minutos** com uma remediacao focal;
- no maximo tres chamadas oficiais de prelint;
- nenhum helper ad hoc de invariantes;
- zero finding repetido das classes numerica, adjacency/counterexample e
  claim/evidence support.

## Diagnostico sobre WSL

A arquitetura WSL deve ser preservada. Ela nao causou a lentidao principal e
nao deve ser revertida. O erro foi de fronteira de artefatos: o audit nasceu no
mirror Windows e precisou voltar ao Linux. A solucao e Linux-native end-to-end
para artefatos transitorios, com espelhamento apenas apos o receipt terminal.

## Autoridades

- session: `/home/luish/.cache/msf/jobs/start-20260716T211000479Z/episode_fast_session.json`;
- performance: `/home/luish/.cache/msf/jobs/start-20260716T211000479Z/episode_performance_report.json`;
- job mirror: `.codex-work/worker-jobs/MSF-R20-GOLD-RUNTIME-PILOT-008`;
- audit inicial: `.codex-work/worker-jobs/MSF-R20-GOLD-RUNTIME-PILOT-008/final_audit_sol.json`;
- reauditoria: `.codex-work/worker-jobs/MSF-R20-GOLD-RUNTIME-PILOT-008/final_reaudit_sol_001.json`;
- packet: `/home/luish/msf-data/Marketing_Swipe_File/exports/msf_r20_gold_runtime_pilot_008_eCaODMtU5GY`.
