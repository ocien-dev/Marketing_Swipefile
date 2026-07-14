# MSF-R20-GOLD-FASTPATH-001 — pipeline gold rápido e unificado

## Objetivo

Reduzir tempo, consumo de tokens e ciclos corretivos da extração padrão-ouro
sem enfraquecer a leitura integral inicial, o recall semântico, o packet cego ou
a auditoria independente do coordenador.

O Fast Path será um único pipeline com duas entradas compatíveis:

1. **episódio novo**: começa nas fontes raw e percorre todo o fluxo até o packet;
2. **episódio retomável**: detecta o último checkpoint válido, reaproveita
   artefatos por hash e executa somente o trabalho pendente.

Não haverá um segundo processo paralelo para episódios novos. O orquestrador
usará `mode=auto` e registrará qual rota foi escolhida antes de qualquer escrita.
Gold já `complete/passed` será read-only por padrão e só poderá ser reaberto por
job corretivo explícito do coordenador.

## Por que este épico vem antes da próxima wave

Nos três episódios da Wave 003, os work orders ficaram entre 39% e 54% maiores
que o transcript limpo porque repetem texto em segmentos, sinais e calibrações.
Também houve retrabalho por validação tardia de números, steps, encoding e
relações, além de helpers descartáveis, `KeyError`, `SyntaxError` e persistência
parcial. O épico transforma essas tarefas mecânicas em ferramentas reutilizáveis
antes de ampliar novamente a escala.

## Rotas de entrada

### Rota A — episódio novo

Um episódio é novo quando não existe `processed/<video_id>/gold_extraction`.
Antes de escrever, o pipeline deve:

1. validar `raw/youtube/<video_id>/metadata.json` e
   `transcript_original.json` em modo read-only;
2. confirmar vídeo, disponibilidade da transcrição, runtime, temp do job,
   ownership e fingerprints protegidos;
3. preparar transcript limpo, chunks, sinais, calibrações e work orders
   compactos;
4. exigir leitura integral de todos os chunks e reviews persistentes;
5. gerar autocheck e recall dirigido;
6. executar readiness, build, validador normal e export do packet;
7. parar em `awaiting_external_audit/pending_external` para auditoria separada.

### Rota B — episódio retomável

Um episódio é retomável quando existe gold incompleto e seus hashes/provenance
são coerentes. O pipeline deve:

1. ler status, hashes, reviews, auditoria e artefatos existentes sem escrever;
2. reutilizar reviews concluídas cujo `input_hash` continua igual;
3. reabrir somente chunks alterados, findings explícitos e fronteiras adjacentes
   necessárias para validação semântica;
4. continuar do primeiro gate realmente pendente;
5. impedir repetição de audit, patch ou build já registrado;
6. bloquear estado parcial inconsistente com diagnóstico exato, sem tentar
   conserto silencioso.

### Estados protegidos

- `complete/passed`: read-only em `mode=auto`;
- pacote com audit `changes_requested`: pode ser retomado somente com finding e
  ownership explícitos;
- hashes divergentes, provenance ausente ou artefatos contraditórios: `blocked`,
  sem sobrescrita;
- lifecycle legado válido continua legível e compatível.

## Stories do épico

| Story | Resultado esperado |
| --- | --- |
| F1 — baseline e métricas | Medir bytes dos work orders, tempo por etapa, gates, correções e reauditorias. Tokens só são registrados quando a superfície fornecer valor confiável. |
| F2 — work order compacto | Texto aparece uma única vez; sinais e calibrações referenciam IDs. A representação preserva ordem, tempos, segment IDs e leitura integral. Meta: pelo menos 25% menos bytes nos fixtures da Wave 003. |
| F3 — recorder com validação antecipada | `record_gold_manual_reviews.py` valida schema, evidência, números literais, faixas, steps, encoding e IDs antes de persistir. Falha não deixa review parcial. |
| F4 — patch transacional | Novo comando declarativo oferece `--check` read-only e `--apply` único, verifica hashes/valores anteriores, insere todos os candidatos antes de resolver relações e grava atomicamente somente após validação completa. |
| F5 — autocheck e recall dirigido | Relatório compacto lista números ausentes/não literais, steps, calibrações, relações, sobreposição, promo/entrevistador, encoding, sinais altos sem cobertura provável e fronteiras de chunk. A primeira leitura continua integral; a segunda passagem usa esse inventário dirigido. |
| F6 — orquestrador unificado | Novo runner recebe manifesto multi-episódio com `mode=auto`, detecta novo/retomável/protegido, executa gates sequencialmente por episódio e mantém estado/export isolados. Um ramo bloqueado não impede episódios independentes. |
| F7 — delta de reauditoria | Comparar packet anterior e novo, mostrando candidatos, evidências, ledger, números e relações afetados. A primeira auditoria permanece integral e cega; reauditorias podem focar o delta mais os gates determinísticos. |
| F8 — testes, skill e documentação | Cobrir as duas rotas, compatibilidade legada, atomicidade, proteção de complete e métricas. Atualizar skill/contrato em pt-BR somente depois dos testes. |

## Ferramentas previstas

Os nomes podem ser ajustados durante a implementação sem mudar o contrato:

- `scripts/run_gold_wave.py`;
- `scripts/gold_review_autocheck.py`;
- `scripts/gold_review_patch.py`;
- `scripts/gold_reaudit_delta.py`;
- alterações compatíveis em `reprocess_gold_episode.py`,
  `record_gold_manual_reviews.py`, `build_gold_semantic_extraction.py` e helpers
  comuns;
- testes focados sob `tests/`.

Não será criado MCP nesta fase. O problema é local e determinístico; adicionar
um servidor MCP aumentaria manutenção e superfície de falha sem reduzir a
leitura semântica. Uma interface MCP só será reconsiderada depois de o CLI
estabilizar e se houver necessidade real de UI ou integração externa.

## Fluxo esperado do worker em episódios novos

1. receber manifesto com IDs e sufixos de export;
2. executar preflight de todos os episódios sem escrita;
3. para cada episódio novo, preparar work orders compactos;
4. ler integralmente cada chunk uma única vez e registrar reviews validadas;
5. executar autocheck/recall dirigido e resolver ou justificar o inventário;
6. executar readiness diagnóstico e, quando permitido, um reparo fechado;
7. executar readiness final, um build e um validador normal;
8. entregar um packet independente de cinco arquivos por episódio;
9. enviar um único `WORKER_EVENT` final consolidado;
10. parar para auditoria independente do coordenador.

## Fluxo esperado em retomadas e correções

1. detectar hashes e último gate concluído;
2. gerar delta e inventário fechado;
3. aplicar correções pelo patch transacional, nunca por Python inline;
4. reabrir somente o escopo afetado e seu contexto adjacente;
5. rederivar uma vez e produzir delta de reauditoria;
6. preservar auditorias seladas e impedir aprovação pelo executor.

## Critérios de aceite

- os mesmos comandos aceitam episódios novos e retomáveis por `mode=auto`;
- episódio novo com raw válido chega ao primeiro packet sem processo paralelo;
- episódio incompleto reaproveita reviews por hash e não relê chunks imutáveis;
- episódio `complete/passed` não é alterado automaticamente;
- work orders dos fixtures Wave 003 ficam pelo menos 25% menores, sem perda de
  texto, IDs, ordem ou targets necessários à revisão;
- recorder e patch não deixam escrita parcial em falha;
- relações com IDs novos são resolvidas somente depois da inserção de todos os
  candidatos;
- problemas determinísticos de numbers, steps, faixas, encoding e simetria são
  detectados antes do build;
- primeira auditoria continua integral/cega e revisor permanece separado;
- delta de reauditoria não modifica packet nem julgamento;
- testes focados e regressão gold passam em temp externo gravável;
- fixtures e episódios aprovados usados na validação permanecem read-only;
- fingerprints protegidos permanecem iguais;
- nenhuma consolidação, Supabase, commit, push ou deploy ocorre neste épico.

## Métricas de sucesso

Metas iniciais, a validar com dados reais:

- redução mínima de 25% nos bytes dos work orders;
- redução da quantidade de gates corretivos determinísticos por episódio;
- nenhuma remediação por Python inline ou helper descartável;
- no máximo uma entrega inicial e uma remediação por episódio antes da decisão
  do owner, salvo finding semântico novo;
- registrar tempo por etapa e número de chunks/candidatos/findings;
- buscar redução total de 35% a 55% no consumo por episódio sem tratá-la como
  promessa antes da medição.

## Ownership planejado do worker

Somente depois de delegação explícita:

- scripts gold mencionados neste plano;
- novos scripts Fast Path;
- testes gold focados;
- `skills/marketing-swipe-file-scale-batch/SKILL.md` após aprovação funcional;
- fixtures criados exclusivamente sob `tests/`.

O worker não editará `AGENTS.md`, fila central, este plano,
`docs/agent-coordination.md` ou `docs/execution-log.md`. Dados reais e exports
ficam read-only durante o desenvolvimento; um piloto novo exigirá épico
posterior com IDs e ownership próprios.

## Condições de parada

Pare sem forçar em lock/PermissionError, divergência de provenance, risco de
alterar gold aprovado, necessidade de mudar schema público/compatibilidade,
teste que revele perda de conteúdo ou qualquer escrita fora do ownership.
Depois de três retornos sem progresso, usar caminho materialmente diferente.
Uma ação única parada por 30 minutos deve ser substituída por outro comando ou
caminho, conforme o protocolo do projeto.

## Gate seguinte

Este documento apenas planeja o épico. Antes da futura delegação, o coordenador
publicará o `EXECUTION BRIEF — MSF-R20-GOLD-FASTPATH-001` em pt-BR simples,
confirmará ownership exclusivo e atualizará a fila para `awaiting_worker`.
Depois da entrega, o coordenador revisará diff, testes, métricas e
compatibilidade. Só então uma nova wave de episódios poderá usar o Fast Path.

## Quality gate — rodada 1

O worker entregou F1-F8 e a suíte declarada passou com 36 testes. O coordenador
reproduziu os 36 testes, compilou os oito módulos, confirmou `git diff --check`
e executou o runner em modo read-only sobre a Wave 003. Os três episódios foram
corretamente classificados como protegidos, e as métricas estimaram redução de
66,98%, 69,26% e 66,17% nos work orders compactos.

O gate permanece `changes_requested` pelos seguintes findings:

1. `FP-001` — o runner apenas prepara episódio novo e, para retomável, retorna
   `skipped_until_semantic_gate`; ele ainda não orquestra autocheck, readiness,
   build e validação quando as reviews já estão completas.
2. `FP-002` — um diretório `gold_extraction` parcial sem status é classificado
   como episódio novo. Deve bloquear como checkpoint inconsistente, sem chamar
   preparação ou sobrescrever artefatos.
3. `FP-003` — o recorder valida somente os candidatos do payload atual. Deve
   validar contra reviews persistidas não substituídas, detectar IDs duplicados
   globais e aceitar relações válidas entre chunks gravados separadamente sem
   perder atomicidade.
4. `FP-004` — o patch transacional não suporta remoção de candidato nem edição
   de `ledger_decisions`, operações necessárias nas remediações reais que ele
   pretende substituir.
5. `FP-005` — o autocheck chamado `promo_or_interviewer` só procura linguagem
   promocional. Deve também sinalizar padrões de pergunta/restatement do
   entrevistador e testar números materiais escritos por extenso.
6. `FP-006` — o delta compara apenas parte dos campos de candidato e ledger e
   não verifica manifesto/transcript. Mudanças em type, themes, risk, contexto,
   signal_types, ranges ou transcript podem ficar invisíveis. O delta deve
   reportar qualquer mudança material e rejeitar IDs duplicados.

A rodada corretiva deve adicionar testes de regressão específicos para os seis
findings. Dados reais permanecem read-only. Esta é a primeira de no máximo duas
rodadas corretivas antes de eventual escalada ao owner.

## Quality gate — rodada 2

O coordenador reproduziu 40 testes, compilou os cinco módulos corrigidos,
reexecutou o runner read-only da Wave 003 e confirmou os doze fingerprints
protegidos atuais. FP-001, FP-002, FP-003, FP-005 e FP-006 estão resolvidos.

FP-004 permanece parcialmente aberto:

1. `removals[].assert` e `ledger_updates[].assert` são opcionais no código. Uma
   remoção ou substituição de ledger pode ser aplicada sem precondição do estado
   anterior, contrariando o contrato de patch protegido;
2. a validação de `ledger_decisions` não verifica disposição, IDs de candidatos
   para `captured/merged`, referências após remoção ou duplicidade de segmento.
   Assim, um patch pode persistir ledger apontando para candidato removido e só
   falhar posteriormente no build;
3. o help de `run_gold_wave --execute` ainda afirma que nunca escreve gold
   retomável, embora a nova implementação execute gates e build nesse caso.

A correção 2/2 é limitada a esses três pontos e suas regressões. Ela deve exigir
precondições explícitas, validar o ledger contra o conjunto final antes do batch
e sincronizar a ajuda da CLI. Se o próximo gate ainda encontrar falha material,
o coordenador pausa e escala ao owner conforme o limite de duas rodadas.

## Resultado final

Quality gate independente aprovado em 2026-07-12:

- F1-F8 concluídos;
- FP-001 a FP-006 resolvidos;
- 46 testes gold/fast-path reproduzidos pelo coordenador;
- módulos compilados e `git diff --check` aprovado;
- help do runner sincronizado;
- runner Wave 003 classificou VQJ, ICRY e 4Ad como
  `protected_complete_read_only` sem escrita;
- redução estimada dos work orders: 66,98%, 69,26% e 66,17%;
- fingerprints protegidos atuais: 4/4 em cada episódio, 12/12 no total;
- nenhum dado real, export, audit, v2/curated/master ou fingerprint foi alterado.

Decisão: **APROVADO FUNCIONALMENTE — Fast Path liberado para a próxima wave**.
O uso em episódios reais continua exigindo novo épico com IDs, ownership,
EXECUTION BRIEF e auditoria independente do packet. Nenhum commit, push, deploy,
consolidação ou Supabase foi executado neste épico.
