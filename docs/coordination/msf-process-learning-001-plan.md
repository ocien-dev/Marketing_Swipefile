# MSF-PROCESS-LEARNING-001 — Aprendizado contínuo e encerramento claro

Status: done
Owner: coordenador Codex
Data: 2026-07-13

## Objetivo

Incorporar uma esteira enxuta de aprendizado do processo, visibilidade de
pendências e encerramento de épicos sem criar um depósito genérico de erros ou
aumentar o contexto da skill gold.

## Stories

1. Criar o registro canônico de aprendizados e sua regra de promoção.
2. Atualizar o protocolo global e a coordenação detalhada.
3. Permitir relato opcional e concreto de aprendizado no contrato do worker.
4. Adicionar somente heurísticas gold comprovadas à skill de escala.
5. Registrar o épico na fila e no execution log.
6. Validar Markdown, JSON, skill e diff sem tocar em dados gold.

## Ownership

- `AGENTS.md`
- `docs/agent-coordination.md`
- `docs/coordination/process-learnings.md`
- `docs/coordination/worker-contract-template.md`
- `docs/coordination/msf-process-learning-001-plan.md`
- `docs/coordination/task-queue.md`
- `docs/execution-log.md`
- `.codex-work/coordination/queue.json`
- `skills/marketing-swipe-file-scale-batch/SKILL.md`

## Fora de escopo

- dados em `C:\MSF-data`;
- scripts, testes e contratos do pipeline gold;
- packets, auditorias, exports, fingerprints ou consolidação;
- commit, push, deploy e Supabase;
- nova delegação ao worker.

## Critérios de aceite

- ocorrências isoladas não viram automaticamente regras globais;
- a terceira recorrência confirmada exige prevenção ou caminho alternativo;
- falhas determinísticas preferem script/teste a documentação repetida;
- o worker apenas relata; o coordenador promove e edita registros centrais;
- pendência do owner e próximo passo autônomo ficam separados;
- `SESSÃO FINALIZADA` tem condição objetiva;
- skill permanece concisa e específica da extração gold;
- JSON da fila, frontmatter da skill e `git diff --check` passam.

## Resultado

- Registro canônico criado com quatro prevenções já comprovadas no fluxo gold.
- Promoção por recorrência e exceção por risco crítico documentadas.
- Relato opcional `process_learnings` adicionado sem ampliar a autoridade do
  worker sobre arquivos centrais.
- Pendência do owner, próximo passo autônomo, bloqueio e encerramento passaram
  a ter significados separados.
- Nenhum dado gold, packet, audit, export ou script do pipeline foi alterado.

## Validações

- fila JSON parseável e job IDs únicos;
- skill validada por `quick_validate.py` e mantida com 175 linhas;
- fences Markdown balanceadas;
- `git diff --check` sem erro, apenas avisos preexistentes de LF/CRLF.
