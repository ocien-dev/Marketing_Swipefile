# MSF-R20 Gold Manifest Compaction 001 - Retrospectiva

Status: implemented_tested
Data: 2026-07-20
Arquitetura: `chronological_hybrid_v1`
Autoria: Claude (worker Opus 4.8), a pedido explicito do owner.

## Motivacao

Analise externa das superficies de tokens em `MSF-R20-wave-009-E01`
(`yhjZTeFNMHk`, 5.289 segmentos) e no benchmark 013 mostrou que o gargalo de
tokens nao esta na leitura da transcricao (399 KB, ja colunar) nem nos
candidatos (o conteudo semantico real, ~77 KB), mas no que o modelo *escreve*:

| Superficie do `gold_authoring_manifest.json` | Bytes | Natureza |
| --- | ---: | --- |
| Total (semantico) | 1.783.583 | output do modelo |
| `source_dispositions` | 1.600.181 (90%) | 5.289 objetos, 3 combinacoes unicas |
| `audit_warning_dispositions` | 98.358 | 153 itens, 10 justificativas unicas |
| `candidates` | 76.972 (3,5%) | o unico conteudo que exige julgamento |

As 5.289 disposicoes colapsam em: 3.069 `captured` (candidate_ids derivaveis das
evidence ranges), 2.219 `excluded/low_signal` com razao boilerplate identica, e
1 exclusao com razao especifica.

## Implementacao entregue

### Compact authoring v4 (`scripts/gold_authoring_manifest.py`)

O modelo passa a autorar apenas a minoria semantica. Com `"compaction": "v4"`:

- `captured` deixa de ser escrito: o runtime o deriva das evidence ranges dos
  candidatos (candidate_ids ordenados) na expansao.
- `default_source_disposition` declara uma vez o template `excluded/low_signal`;
  todo segmento que nao e captured nem excecao herda o default.
- `source_disposition_exceptions` lista apenas segmentos que fogem das duas
  formas (ex.: exclusao com razao especifica, merged).
- `audit_warning_dispositions` e `risk_recall_acknowledgements` aceitam forma
  interned (`justification_table` + `items` com `justification_ref`), mesmo
  padrao ja aplicado ao dossier no 012 (HI-012-03).

A expansao (`expand_compact_v4`) roda em `normalize_authoring_input` **antes** de
qualquer hash, validacao ou derivacao do payload compact-v3 - mesmo precedente
do v3->v2. O caminho do manifesto completo permanece 100% inalterado quando
`compaction` nao esta presente.

### Prova de equivalencia (lossless)

Teste sintetico commitado: `tests/test_gold_manifest_compaction.py` (7 casos)
prova round-trip byte-identico das dispositions, warnings e risk acks, hashes
identicos via `normalize_authoring_input`, payload de build identico, e caminho
do manifesto completo intacto.

Prova adicional contra o fixture real de 2,2 MB do `wave-009-E01` (fora do
repositorio por higiene de dados):

| Metrica | Manifesto completo | Compact v4 |
| --- | ---: | ---: |
| Output do modelo (bytes semanticos) | 1.783.583 | 162.341 |
| Reducao | - | **90,9%** |
| Excecoes listadas | 5.289 dispositions | 1 |
| `authoring_decisions_sha256` | igual | igual |
| `semantic_sha256` | igual | igual |
| Payload de build (compact v3) | igual | igual (byte a byte) |

### Regressao

- suite completa: `329 passed` (322 previos + 7 novos), zero regressao;
- `py_compile` de `gold_authoring_manifest.py`: OK;
- JSON do sync manifest: valido;
- `git diff --check` nos arquivos alterados: sem erros.

### Leitura fixa - prompt de-L7-izado

O prompt canonico `episode_gold_standard_small_model.md` carregava o binding
especifico do episodio L7u7r6rOl68 (ID, titulo, "Known Problems", "Mandatory
Calibration Checks") relido todo episodio. Movido para work orders por episodio:

- `prompts/extraction/episode_work_order_template.md` (template reusavel);
- `prompts/extraction/episode_work_order_L7u7r6rOl68.md` (provenance do L7,
  verbatim);
- o prompt aponta `docs/gold-extraction-contract.md` como fonte normativa unica
  onde ha sobreposicao. Nenhuma regra reusavel foi removida - apenas o conteudo
  especifico do episodio saiu do prompt.

Novos arquivos adicionados a `scripts/gold_runtime_sync_manifest.json` para a
referencia resolver no runtime Linux.

## Fora de escopo (follow-up especificado, nao implementado)

- **Item 2 - convergencia do prelint (checklist inline por chunk).** O benchmark
  013 exigiu 8/7 prelints por episodio. Promover os tres defeitos mais
  frequentes (procedures sem steps, numeros sem raw literal, reported case sem
  caveat) para checklist inline no `episode_context` reduziria iteracoes.
  Deliberadamente nao implementado: mudaria o runtime de 3.225 linhas de um jeito
  que nao pode ser validado sem reprocessar um episodio real (autoria manual do
  Codex, sem API paga). Deve ser feito e medido pelo Codex no proximo episodio
  novo, com meta observacional <=2 prelints, sem forcar.
- **Dedup completo prompt<->contrato.** So o binding do L7 foi extraido. O merge
  regra-a-regra das ~486 linhas reusaveis do prompt contra as ~650 do contrato
  foi evitado nesta mudanca porque um merge errado dropa um guardrail de
  qualidade. Requer o mapeamento rule-by-rule que o contrato exige.

## Nota de integracao

Esta mudanca foi implementada e commitada pelo lado Claude a pedido explicito do
owner. Ela pousou junto com o working tree de WIP nao-committado do lado Codex
(reescrita do contrato, fast runner, docs de coordenacao), porque
`gold_authoring_manifest.py` era um arquivo untracked do Codex e as edicoes do
compact v4 sao inseparaveis dele. O owner autorizou explicitamente o commit
conjunto. Nenhum episodio `complete/passed`, pool v2/master, dado real de
insight/transcript ou API paga foi tocado.
