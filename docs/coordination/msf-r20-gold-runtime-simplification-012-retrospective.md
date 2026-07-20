# MSF-R20 Gold Runtime Simplification 012 - Retrospectiva de implementacao

Status: complete_passed_0
Data: 2026-07-18
Escopo real: `jbFY16W5GTE`, `fBaX4ixKkFo`
Arquitetura: `chronological_hybrid_v1`

## Resultado executivo

As tres causas estruturais aprovadas foram removidas sem criar novo brief,
runner, papel humano ou fonte de verdade:

1. `ready` agora depende de uma invariante source-complete compartilhada.
2. remediacao valida o envelope e o dossier anterior antes de qualquer write.
3. a Sol recebe um dossier unico deduplicado e um request consolidado N/N.

O gold persistido dos dois episodios permaneceu `complete/passed/0`, com 34 e
44 candidatos. A validacao foi read-only sobre os packets e dados finais; os
dossiers novos ficaram no job transitório do benchmark dentro do workspace.

## Evidencia por iniciativa

### HI-012-01 - source complete

- O workbench precisa reconstruir todos os clean indexes como covered, merged
  ou excluded e reportar zero unreviewed.
- Must-close sem review source-scoped bloqueia o dossier.
- Cobertura numerica material e calibracao entram no mesmo veredito.
- Prelint, finalizer e dossier chamam a mesma funcao.
- A regressao de 427 segmentos unreviewed bloqueia deterministicamente.

### HI-012-02 - envelope first

- Request, envelope, episode identity, artifact identity e dossier anterior
  sao checados antes da compilacao e da persistencia.
- Envelope ausente retorna `writes_gold=false`, zero review write, zero build e
  zero finalizer.
- `--audit-input` e materializado no boundary correto.
- Warning identity usa categoria, source range, candidate e proposition
  fingerprint; alteracao em outro candidato nao muda o ID local.
- O delta inclui impact set de candidatos, ranges, warnings, calibracoes,
  numeros e relacoes dependentes.
- Dossier invalido depois de commit registra `persisted_and_finalized` e manda
  reparar somente a geracao, sem repetir o gold write.

### HI-012-03 - superficie unica e request consolidado

- `audit_navigation` foi removido.
- Workbench, warnings e risk recall foram convertidos em colunas mais rows,
  referenciando transcript e candidatos existentes.
- Justificativas identicas sao armazenadas uma vez e usadas por referencia.
- Transcript literal, candidatos completos, cobertura numerica, calibracao,
  ledger, fingerprints e packet snapshot permanecem no mesmo JSONL.
- Request parcial falha antes de write; dois ramos ready geram um unico request
  com hashes fisicos e semanticos congelados.

## Benchmark congelado real

| Episodio | Dossier anterior | Dossier 012 | Reducao | Validacao |
| --- | ---: | ---: | ---: | --- |
| `jbFY16W5GTE` | 909.666 B | 457.810 B | 49,67% | structural pass; semantic changes requested |
| `fBaX4ixKkFo` | 930.916 B | 491.827 B | 47,17% | structural pass; semantic changes requested |

Hashes congelados no request consolidado:

- `jbFY16W5GTE`: physical `e55568cd...ff88e578`, semantic
  `1b243827...ee1645a`.
- `fBaX4ixKkFo`: physical `8cf5bedf...f28dc894`, semantic
  `1df890e1...2e8b6da`.

O despacho consolidado usa `gpt-5.6-sol/high` e somente foi criado depois dos
dois dossiers passarem a validacao e reportarem zero unreviewed.

## Validacoes

- runtime Windows native: pass, Python 3.12.13, temp gravavel;
- compilacao dos modulos alterados: pass;
- regressao dirigida: 159 passed;
- suite completa: 301 passed em 28,42 s;
- `git diff --check`: pass;
- dossier validator: pass nos dois episodios;
- tamanho maximo de 500.000 bytes: pass nos dois episodios;
- dados gold e packets persistidos: nenhuma escrita;
- commit, push e deploy: nao executados.

## Limite honesto da medicao

Esta implementacao valida as causas estruturais, o comportamento transacional
e a reducao model-facing usando os dois fixtures reais congelados. Ela nao
reprocessa episodios protegidos nem inventa tempo de leitura/autoria. Por isso,
os SLAs de 25-40 e 35-50 minutos continuam como criterio observacional para o
proximo episodio novo, com a telemetria corrigida desde o primeiro comando.

## Auditoria final Sol/high

A auditoria consolidada levou aproximadamente nove minutos e retornou cinco
findings. O finding de warning IDs duplicados pertencia ao runtime 012, foi
corrigido, testado e fechado em reauditoria focal de aproximadamente dois
minutos. Permanecem quatro findings semanticos nos golds protegidos:

1. bindings/minimal evidence invalidos em candidatos de `jbFY16W5GTE`;
2. `fBaX4ixKkFo-G043` sem a faixa substantiva vinculada;
3. `jbFY16W5GTE-G024` com extrapolacao alem da fonte;
4. `fBaX4ixKkFo-G013` como reported case sem caveat.

Reabrir esses episodios `complete/passed` altera provenance protegida e nao foi
inferido como autorizacao da implementacao de runtime. O relatorio completo esta
em `msf-r20-gold-runtime-simplification-012-final-audit.md`.

## Veredito

As mudancas de runtime removem burocracia e classes inteiras de retrabalho: falso-ready,
erro de envelope pos-commit, churn global de warning e duplicacao do dossier.
Nao foram adicionadas heuristicas semanticas, novo compilador, novo brief ou
runner. O ganho substancial comprovado nesta fase e a reducao de 47-50% da
superficie final, alem do bloqueio antecipado das falhas que custaram a primeira
auditoria e a remediacao do benchmark 011. O codigo e o benchmark estrutural
passaram; o gate terminal da wave permanece `changes_requested/4`, sem falsa
declaracao de `complete`.

## Adendo final - remediacao owner-authorized

O estado acima registra honestamente a primeira auditoria e permanece como
provenance historica. Depois dela, o owner autorizou explicitamente a revisao
dos golds protegidos. A remediacao fechou os quatro findings source-backed sem
alterar fontes protegidas nem apagar auditorias ou identidades anteriores.

| Episodio | Transacao | Persist | Finalize | Candidatos | Resultado |
| --- | ---: | ---: | ---: | ---: | --- |
| `jbFY16W5GTE` | 4.874,61 ms | 79,05 ms | 1.014,42 ms | 34 | `complete/passed/0` |
| `fBaX4ixKkFo` | 4.024,33 ms | 74,97 ms | 916,54 ms | 44 | `complete/passed/0` |

Cada episodio exigiu uma unica escrita de reviews, um build, um finalizer e um
dossier. A Sol/high fez a auditoria source-complete consolidada e retornou
`passed/0` sem finding novo.

Durante o fechamento apareceu um defeito de lifecycle relevante: a primeira
rederivacao podia reutilizar o audit `passed` do snapshot anterior. O runtime
agora permite forcar `pending_external` em nova finalizacao semantica, arquiva
o audit anterior byte a byte e substitui a identidade terminal somente quando
a revisao autorizada referencia a identidade anterior. Replays protegidos
comuns permanecem idempotentes.

Validacao final: `303 passed`, `py_compile`, `git diff --check`, runtime Windows
native, packets 5/5, fingerprints iguais e completion receipts sem erro.
