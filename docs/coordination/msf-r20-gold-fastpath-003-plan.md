# MSF-R20-GOLD-FASTPATH-003 — Ledger automático antes do packet

Status: awaiting_worker
Worker: Extração Padrão-Ouro (`019f4c90-b9dc-7e32-8ff1-57f8896386d3`)
Modelo/esforço: `gpt-5.6-terra/high`
Coordenador: `019f4ee6-a00e-7c90-97bc-5c1aae5c8551`

## Problema confirmado

Em `zoChfFHnlOQ`, depois de 39 reviews completos e antes do build, o autocheck
produziu 3.063 itens `review_required`: 3.009 são sinais altos sem decisão de
ledger. A causa é técnica: nesse estágio não há ledger derivado final, e
`gold_review_autocheck.py` consulta apenas `ledger_decisions` manuais em vez de
aplicar em memória `ledger_for_signals()`, a mesma regra determinística usada
no build. Isso não é um inventário editorial honesto e não pode ser resolvido
por milhares de disposições ou receipts manuais.

## Objetivo

Fazer a prévia read-only do autocheck usar o ledger automático em memória
quando o ledger final ainda não existir. A prévia deve reconhecer:

- `captured`/`merged` somente quando o candidato cita o mesmo segmento;
- `excluded` somente com `reason_code` válido, incluindo `duplicate_of` válido;
- ausência de decisão, destino inválido e evidência ausente como pendências
  reais.

O trabalho não altera reviews, dados gold, exports, auditorias, snapshots ou
fingerprints.

## Stories

### FP3-S01 — Correção determinística do autocheck

1. Registrar `git status --short --branch`.
2. Ajustar somente `scripts/gold_review_autocheck.py` para derivar o ledger em
   memória com `ledger_for_signals()` se o ledger persistido ainda for pending.
3. Preservar o ledger persistido como fonte de verdade quando ele já contiver
   disposições finais.

### FP3-S02 — Regressões focadas

Adicionar apenas os testes necessários em `tests/test_gold_fastpath.py` para
provar que:

1. evidência persistida vira `captured` na prévia antes do build;
2. exclusão automática válida não vira `review_required`;
3. destino captured inválido, ausência de decisão ou exclusão inválida continuam
   pendentes;
4. o caso `zoChfFHnlOQ` em leitura pura reduz a inflação de ledger sem mascarar
   números, calibrações, evidência editorial ou suporte de entrevistador/promo.

### FP3-S03 — Validação e entrega

1. Executar a suíte focada em temp isolado, `py_compile` e `git diff --check`.
2. Executar o autocheck de `zoChfFHnlOQ` apenas em leitura e relatar os totais
   por categoria antes/depois.
3. Não iniciar patch editorial, readiness, build, validador ou export da Wave
   005. O coordenador decide a remediação editorial somente sobre o inventário
   remanescente.

## Ownership do worker

- `scripts/gold_review_autocheck.py`;
- `tests/test_gold_fastpath.py`;
- `.codex-work/worker-jobs/MSF-R20-GOLD-FASTPATH-003`.

Leitura permitida: estado de `zoChfFHnlOQ`, fixtures, scripts de suporte e
manifesto Wave 005. Dados reais, exports, auditorias, documentação, fila,
schemas, prompts e demais scripts são somente leitura.

## Critérios de aceite

- nenhum dado real alterado;
- testes direcionados aprovados;
- autocheck preserva pendências reais e remove somente a inflação causada pela
  ausência de ledger derivado antes do build;
- diagnóstico read-only de `zoChfFHnlOQ` atualizado e reproduzível;
- Wave 005 continua bloqueada até o inventário editorial remanescente ser
  planejado pelo coordenador.

## Condições de parada

- lock/PermissionError;
- falha de teste não explicada;
- necessidade de alterar schema, contrato público ou dados reais;
- qualquer mudança fora dos dois arquivos de ownership.

## Brief pré-delegação conciso

Propósito: remover falso bloqueio de ledger do autocheck antes do build.
Escritas: um script e seus testes; dados reais somente leitura.
Saída: regressões e diagnóstico real menor, mas sem mascarar gaps editoriais.
Fora de escopo: patch de episódio, build, packet, auditoria e release.
Próximo gate: coordenador lê o inventário residual e planeja a remediação gold.
