# MSF-R20 wave 007 - retrospectiva de execucao

Status: complete_passed_0
Data: 2026-07-18
Arquitetura: `chronological_hybrid_v1`
Escopo: 2 episodios novos

## Resultado

| Episodio | Segmentos | Chunks | Candidatos finais | Estado |
| --- | ---: | ---: | ---: | --- |
| `eCaODMtU5GY` | 1.079 | 21 | 56 | `complete/passed/0` |
| `MiKloPf9-To` | 1.051 | 19 | 50 | `complete/passed/0` |

A wave terminou com packet 5/5 valido nos dois episodios, calibracao `pass`,
fingerprints preservados, auditoria final consolidada `gpt-5.6-sol/high` e zero
findings. O gate final ficou `ready_for_audit` por compatibilidade nominal do
lifecycle, mas os dois ramos estao protegidos, completos e com audit valido.

## Tempos observados

O wall total da wave, do inicio do primeiro episodio ao completion do segundo,
foi aproximadamente **2h01m09s**. Os walls individuais registrados foram
**2h00m57s** para `eCaODMtU5GY` e **1h30m07s** para `MiKloPf9-To`; eles se
sobrepoem e nao devem ser somados.

| Etapa | `eCaODMtU5GY` | `MiKloPf9-To` |
| --- | ---: | ---: |
| Selecao e contexto deterministico | 0,85 s | 9,51 s |
| Leitura cronologica e autoria inicial | 28m55,58s | 11m05,58s |
| Prelint inicial | 0,61 s | 0,57 s |
| One-shot inicial | 3,24 s | 3,04 s |
| Auditoria Sol inicial | 12m55,50s | 12m56,35s |
| Autoria de remediacao 001 | 22m44,83s | 22m52,62s |
| Runtime de remediacao 001 | 5,77 s | 6,58 s |
| Autoria de remediacao 002 | 8m50,92s | 9m10,37s |
| Runtime de remediacao 002 | 5,35 s | 7,97 s |
| Autoria de remediacao 003 | 1m07,99s | nao aplicavel |
| Runtime de remediacao 003 | 5,07 s | nao aplicavel |
| Reauditoria Sol 002 | 6m06,50s | 6m05,36s |
| Reauditoria Sol 003 | 4m03,62s | 3m15,13s |
| Completion | 0,20 s | 0,35 s |

A primeira reauditoria foi encerrada no lifecycle somente depois de a
remediacao seguinte ja ter comecado. Por isso os spans brutos de 26m42,80s e
26m38,07s incluem sobreposicao e nao podem ser somados aos spans de autoria.
O veredito foi selado aproximadamente 11 minutos apos o inicio dessa leitura.
Essa limitacao de telemetria fica explicita; nenhum tempo sobreposto foi
atribuido duas vezes ao wall da wave.

## Evolucao dos findings

| Auditoria | `eCaODMtU5GY` | `MiKloPf9-To` |
| --- | ---: | ---: |
| Inicial | 9 | 10 |
| Reauditoria 001 | 5 | 3 |
| Reauditoria 002 | 1 | 0 |
| Reauditoria 003 | 0 | 0 |

Os findings concentraram-se em equivalencia de calibracao, cobertura numerica,
papel economico, multiplicidade de ocorrencias, evidencia/ledger e atribuicao.
O ultimo residuo era uma normalizacao indevida de dois tokens ASR de escala
desconhecida; os raws foram preservados e seus valores estruturados removidos.

## O que o metodo melhorou de fato

- Selecao, contexto, prelint, persistencia, finalizacao, dossier e completion
  ficaram na ordem de milissegundos ou poucos segundos.
- Cada remediacao foi uma transacao isolada por episodio, com uma escrita de
  reviews, um finalizer, um build e um dossier; nenhum packet intermediario foi
  entregue ao owner.
- O gate source-complete impediu persistencia com hard blockers, e a auditoria
  consolidada preservou hashes, packets e fingerprints em todas as rodadas.
- O fluxo nao parou em findings locais: reparou, revalidou e reauditou ate
  `passed/0`.

## Limites e defeitos encontrados

- O ganho estrutural nao eliminou o principal custo: julgamento semantico.
  Leitura, autoria, auditoria e remediacao dominaram quase todo o wall.
- A primeira autoria deixou matrizes numericas extensas como `count/value=null`
  e tratou calibragens duplicadas apenas no manifesto. A cobertura derivada
  continuou exigindo que a ocorrencia duplicada estivesse ligada a evidencia
  do candidato canonico.
- O helper inicial preservou records opacos ao enriquecer apenas alguns raws,
  o que gerou remediacao adicional. A correcao final substituiu as matrizes
  materiais por ocorrencias tipadas, com multiplicidade e caveats explicitos.
- O autocheck rejeitava uma correcao ASR semanticamente necessaria (`030` para
  0,30%) mesmo quando inferida e caveada. O runtime agora aceita apenas a
  excecao estreita em que o raw aparece literalmente no caveat, o status e
  `inferred` e o caveat identifica ASR; uma regressao dedicada foi adicionada.

## Validacoes finais

- auditoria final consolidada: `passed/0` nos dois episodios;
- gate: 2/2 packets validos, audit valid, fingerprints match;
- runtime `windows_native`: pass, Python 3.12.13, temp gravavel;
- regressao direcionada: 172 passed;
- suite completa: 304 passed em 18,63 s;
- `py_compile`: pass;
- commit, push e deploy: nao executados.

Artefatos principais:

- `C:\MSF-data\Marketing_Swipe_File\.tmp\MSF-R20-wave-007-E01\episode_completion_receipt.json`
- `C:\MSF-data\Marketing_Swipe_File\.tmp\MSF-R20-wave-007-E02\episode_completion_receipt.json`
- `.tmp/MSF-R20-wave-007-final-reaudit-003-report.md`
- `C:\MSF-data\Marketing_Swipe_File\.tmp\MSF-R20-wave-007-wave-gate-final.json`
