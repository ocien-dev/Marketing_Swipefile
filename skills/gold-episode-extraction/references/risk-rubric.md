# Rubrica de risco semantico gold

Use esta ordem para navegar o prelint e o dossier. O score e uma prioridade de
leitura, nao um julgamento automatico de erro.

| Prioridade | Superficie | Pergunta de verificacao |
| --- | --- | --- |
| P0 | `numeric_result` | O resultado, baseline, unidade, periodo e atribuicao estao estruturados? |
| P0 | `numeric_trajectory` | Todos os valores intermediarios e mudancas de unidade foram preservados? |
| P0 | `mechanism_sequence` | Ordem, duracao, condicao e outcome do mecanismo estao completos? |
| P0 | `before_after` | Antes, depois, comparador e caveat pertencem a mesma proposicao? |
| P1 | `reported_outcome` | O outcome foi capturado sem virar causalidade universal? |
| P1 | `numeric_sequence` | A multiplicidade exige records separados ou e apenas repeticao oral? |
| P1 | `claim_evidence_alignment` | A evidencia sustenta a proposicao, nao apenas o tema? |
| P1 | `counterexample` | Caso falho, negacao ou excecao limita a proposicao capturada? |
| P1 | `limitation` | A condicao ou ressalva altera a aplicabilidade do insight? |
| P2 | `chunk_boundary` | A fronteira completa uma proposicao iniciada no chunk adjacente? |
| P3 | `generic_tail` | Existe material novo ou apenas transicao/restatement ja coberto? |

## Evidencia minima para encerrar uma superficie

- indexes ou segment IDs fonte;
- texto verbatim suficiente para reconstruir a proposicao;
- candidato que expressa a mesma proposicao, quando capturada/merged;
- justificativa concreta quando incidental;
- em `must_close`, `source_segment_ids` cobrindo integralmente o range revisado;
- records numericos com `raw`, unidade, periodo, role e status coerentes;
- caveat de atribuicao para casos e outcomes reportados.

## O que nao fazer

- Nao criar candidato para esconder warning.
- Nao fechar em massa trajetoria, outcome, mecanismo, counterexample ou claim gap.
- Nao chamar proximidade tematica de cobertura.
- Nao inferir magnitude, baseline ou causalidade ausentes.
- Nao agrupar valores de funcoes diferentes num unico record.
- Nao reler todo o dossier entre cada finding; use ranges e matriz para navegar,
  preservando uma passagem integral unica na auditoria final.
