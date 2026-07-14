# MSF-R20-GOLD-FASTPATH-004 — Overlap semântico, não palavras genéricas

Status: awaiting_worker
Worker: Extração Padrão-Ouro (`019f4c90-b9dc-7e32-8ff1-57f8896386d3`)
Modelo/esforço: `gpt-5.6-terra/high`
Coordenador: `019f4ee6-a00e-7c90-97bc-5c1aae5c8551`

## Problema confirmado

Após a correção do ledger pré-build, o autocheck de `zoChfFHnlOQ` tem 54 itens
reais para inspeção, mas 53 são `overlap` produzidos por palavras genéricas dos
títulos, por exemplo `com`, `de`, `antes` e `VSL`. O detector atual usa todos
os tokens alfanuméricos e transforma semelhança lexical superficial em gate
semântico. Isso não é um conflito editorial e gera receipt manual desnecessário.

## Objetivo

Fazer a detecção de overlap considerar somente termos de conteúdo, usando a
mesma normalização de palavras significativas já existente no autocheck. Um
overlap continua pendente quando houver sobreposição material sem relação
parent/child; palavras funcionais ou siglas isoladas não bastam.

## Stories

### FP4-S01 — Ajuste limitado

1. Registrar `git status --short --branch`.
2. Alterar somente `scripts/gold_review_autocheck.py` na heurística de overlap.
3. Não alterar regras de números, calibração, ledger, entrevista/promo, receipt
   ou dados reais.

### FP4-S02 — Regressões

Adicionar somente testes em `tests/test_gold_fastpath.py` para provar que:

1. palavras genéricas e siglas curtas não criam overlap;
2. três termos de conteúdo compartilhados sem relação continuam pendência;
3. uma relação parent/child válida continua encerrando o overlap;
4. o caso read-only de `zoChfFHnlOQ` preserva os alertas numéricos, de
   calibração e de evidência enquanto reduz somente o ruído de overlap.

### FP4-S03 — Validação

Executar testes focados em temp isolado, compilação sem escrita de `.pyc`,
`git diff --check` e autocheck read-only de `zoChfFHnlOQ`. Não gerar receipt,
patch, readiness, build, validador, export, audit ou alteração em dados reais.

## Ownership do worker

- `scripts/gold_review_autocheck.py`;
- `tests/test_gold_fastpath.py`;
- `.codex-work/worker-jobs/MSF-R20-GOLD-FASTPATH-004`.

## Critérios de aceite

- somente a heurística de overlap e testes relacionados mudam;
- sobreposição semântica verdadeira continua detectada;
- dados reais permanecem somente leitura;
- o diagnóstico residual de `zoChfFHnlOQ` deixa explícito o inventário
  editorial que ainda exige remediação.

## Condições de parada

- lock/PermissionError;
- teste que revele regressão fora da heurística;
- necessidade de mudar contrato, schema ou dados reais;
- qualquer escrita fora do ownership.

## Brief pré-delegação conciso

Propósito: remover ruído de overlap antes da correção editorial.
Escritas: um script e seus testes; Wave 005 somente leitura.
Saída: sobreposição lexical genérica deixa de virar gate; gaps reais continuam.
Fora de escopo: ledger, dados, packet, auditoria e release.
Próximo gate: coordenador planeja a remediação editorial residual.
