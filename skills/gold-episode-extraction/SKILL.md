---
name: gold-episode-extraction
description: Executa a extracao padrao-ouro de episodios do Marketing Swipe File com leitura cronologica integral, fechamento semantico orientado por risco, matriz de ocorrencias numericas, prelint enxuto, finalizacao one-shot e auditoria final Sol unica. Use quando Codex precisar selecionar, revisar, corrigir, finalizar, auditar ou remediar um episodio gold, especialmente quando houver muitos semantic-closure warnings, numeros repetidos, sequencias, before/after, resultados reportados ou dossiers longos.
---

# Gold Episode Extraction

## Objetivo

Concluir cada episodio gold com uma passagem semantica principal e uma auditoria
final unica, usando os artefatos deterministas do projeto para concentrar o
julgamento nas superficies com maior risco. O brief de risco orienta a leitura;
ele nunca substitui transcript, evidencia verbatim, prelint ou dossier integral.

## Fluxo

1. Ler `AGENTS.md`, o plano ativo e o contrato gold. Executar o preflight
   `scripts.verify_gold_runtime.py` antes de qualquer operacao sobre o data
   root. O runtime canonico e Windows-native; WSL so vale quando selecionado e
   certificado explicitamente.
2. Confirmar que `transcript_semantic_index_status.json` esta `ready` e ligado
   ao hash atual do transcript. Consumir `transcript_semantic_index` do contexto
   compacto como mapa de navegacao: priorizar unidades `high`, numeros,
   mecanismos, outcomes, caveats e fronteiras, sem pular a leitura cronologica.
   Indice ausente/stale em contexto read-only nao autoriza backfill ou escrita.
3. Iniciar pela fast lane oficial e ler todos os chunks pendentes em ordem.
   Compor candidatos atomicos e source-backed no unico
   `gold_authoring_manifest_v1`, sem consultar extracoes legadas. Nao criar
   helper Python, patch separado de ledger ou redirect de calibracao.
4. Usar o `semantic_workbench` como superficie source-first comum. Confirmar que
   seus blocos reconstroem todos os clean indexes, fechar `must_close` por risco
   e revisar os bindings candidato-claim-evidencia-numero-caveat-calibracao.
   Ambiguidade semantica fica warning; identidade/evidencia invalida bloqueia.
5. Antes do primeiro prelint, fechar nesta ordem:
   - resultados com numeros ou percentuais;
   - trajetorias, before/after e valores intermediarios;
   - mecanismos acompanhados de sequencia, duracao ou condicao;
   - outcomes reportados, inclusive exemplos sem magnitude;
   - steps, caveats, atribuicao e fronteiras;
   - caudas genericas ja cobertas, por ultimo.
6. Durante a autoria, executar `--dry-run --authoring-manifest` para obter o
   inventario e a `adversarial_authoring_view` sem gold, receipt ou telemetria.
   Revisar as seis categorias obrigatorias, decidir cada calibracao por
   equivalencia de proposicao ou `none` e gravar `adversarial_review` ligado ao
   hash das decisoes. Quando o manifesto parecer fechado, executar um prelint
   oficial com `--output`. Gerar o brief compacto:

   ```bash
   python skills/gold-episode-extraction/scripts/build_gold_risk_brief.py \
     --input PRELINT.json --output semantic-risk-brief.json
   ```

7. Consumir `review_order` do maior para o menor risco. Fechar primeiro itens
   `must_close`; `audit_only` permanece visivel sem criar loop. Usar
   `numeric_occurrence_matrix` para conferir multiplicidade e `raw` literal.
   Nao transformar `potential_multiplicity_gap` em erro automatico: confirmar a
   proposicao e a fala fonte.
8. Corrigir todo o inventario no mesmo manifesto source-backed e repetir somente checks read-only
   ate o prelint ficar limpo. Persistir e finalizar pela rota one-shot oficial.
   `needs_revision`, issues do compilador, `hard_blockers` e `review_gate` sao
   inventario local nao terminal. Eles bloqueiam a escrita, nao o epico. Quando
   `continue_required=true`, consumir `workflow_disposition` e `next_action`,
   corrigir no mesmo turno e nao emitir resposta final.
9. Gerar o brief do dossier final:

   ```bash
   python skills/gold-episode-extraction/scripts/build_gold_risk_brief.py \
     --input final_audit_dossier.jsonl --output audit-risk-brief.json
   ```

10. Confirmar que o one-shot emitiu `audit_request_receipt.json`. Na fase Sol,
   ler primeiro o brief/workbench, depois o dossier source-complete uma unica
   vez. Auditar atomicidade, recall, numeros, sequencias, resultados, caveats,
   atribuicao, relacoes, ledger, calibracao e fronteiras. Nao aprovar por
   ausencia de alerta lexical.
11. Materializar o envelope Sol antes de qualquer outra operacao. Se houver
    findings, editar o mesmo manifesto com `base_manifest_semantic_sha256`,
    persistir uma unica substituicao transacional e reauditar obrigatoriamente
    o delta focal quando seus invariantes forem validos. Caso contrario, usar o
    dossier integral. Em interrupcao sem envelope, usar `--resume-audit`; nunca
    repetir extracao, build ou dossier valido.
12. Derivar `complete` somente apos auditoria final passada, zero findings,
    validador obrigatorio e fingerprints preservados.

Esta skill executa somente `chronological_hybrid_v1`. O compilador semantico
cego, shards, reducer global, janelas de relacao e gap resolver estao arquivados
como pesquisa read-only e nao podem ser usados em episodio real. Os controles
uteis dessa pesquisa ja estao incorporados ao contexto, workbench, matriz
numerica, bindings de calibracao, fechamento de fronteiras e deteccao de
duplicatas exatas desta rota.

## Regras de decisao

- Tratar o brief como indice de navegacao, nao como nova fonte de verdade.
- Tratar `transcript_semantic_index` da mesma forma: ele organiza a busca por
  risco e fronteira, mas o transcript cronologico continua obrigatorio.
- Preservar quotes verbatim byte a byte; normalizar apenas campos editoriais.
- Nunca mesclar automaticamente candidatos duplicados; duplicata exata bloqueia
  para merge ou separacao source-backed deliberada.
- Para numeros, preferir `segment_id` + `source_literal` ou `source_span`;
  rejeitar literal ambiguo e manter `source_occurrence` apenas como legado.
- Estruturar uma ocorrencia numerica por funcao semantica quando a sequencia
  depender da multiplicidade. Nao duplicar records por mera repeticao oral.
- Manter exemplos e outcomes como atribuicao reportada quando faltarem baseline,
  amostra, magnitude ou verificacao independente.
- Agrupar caudas incidentais somente quando a mesma proposicao e a mesma lineage
  ja tiverem sido verificadas. Material novo sempre volta para revisao.
- Exigir source scope completo ao chamar item numerico/outcome/counterexample de
  incidental; nunca usar disposition em massa para risco alto.
- Nao reduzir a auditoria final a `review_order`: fazer a passagem integral pelo
  dossier depois de inspecionar os riscos prioritarios.
- Nunca encerrar em prelint ou check apenas porque existe inventario reparavel.
  Encerrar incompleto somente por uma condicao terminal externa de `AGENTS.md`.
- Gravar o audit no job-dir nativo do runtime validado. Espelhamentos sao
  necessarios somente quando uma rota WSL opcional tiver sido selecionada.
- Tratar fila como ordenacao. Antes de selecionar, reconciliar o hash da fonte
  ativa com terminal identity, receipt e registry; reprocesso de fonte alterada
  exige flag e motivo explicitos.

## Rubrica

Ler [references/risk-rubric.md](references/risk-rubric.md) antes de alterar a
heuristica, interpretar um score ou classificar uma superficie como incidental.

## Validacao

Antes de encerrar, confirmar:

- todos os chunks possuem review atual;
- indice semantico atual, integro e ligado ao hash do transcript preparado;
- `hard_blockers=0` e warnings permanecem visiveis;
- matriz numerica conferida para candidatos quantitativos;
- ledger e calibracao derivam dos candidatos finais;
- manifesto, preview e apply possuem o mesmo hash; zero helper job-local;
- audit request, envelope e completion referenciam o mesmo artefato selado;
- packet possui exatamente cinco arquivos;
- auditoria final Sol e validador obrigatorio passam;
- fingerprints protegidos permanecem iguais;
- tempos do episodio provem do receipt, sem atribuir espera a prelint/auditoria.
