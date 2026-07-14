# Épico de hardening antes da próxima wave R20

## Objetivo

Eliminar três fontes de retrabalho observadas na Wave 001 sem alterar gold
existente, camadas consolidadas ou compatibilidade do fluxo atual.

## Escopo

| Story | Resultado esperado |
| --- | --- |
| H1 — sufixo de export explícito | `build_gold_semantic_extraction.py` aceita um sufixo opcional de export. Sem argumento, preserva `msf_r20_piloto_<video_id>`; com argumento, exporta somente para o sufixo solicitado. |
| H2 — preflight raw read-only | O caminho de preparação expõe uma checagem sem escrita para `metadata.json` e `transcript_original.json`, com erro claro para fonte ausente, vídeo incompatível ou transcrição indisponível. Quando existir no metadata, `transcript_status` precisa ser `available`; segmentos no transcript não anulam esse bloqueio. |
| H3 — prontidão antes do build | O builder expõe modo sem escrita que verifica as reviews/candidatos e falha antes do build final para `steps` ausentes ou outra integridade determinística. |
| H4 — testes e compatibilidade | Testes cobrem sufixo explícito, fallback legado, preflight raw e modo de prontidão; testes existentes continuam passando. |

## Ownership do worker

Permitido apenas:

- `scripts/build_gold_semantic_extraction.py`;
- `scripts/reprocess_gold_episode.py`;
- `scripts/gold_extraction_common.py`, se necessário para reutilização mínima;
- `tests/test_gold_pipeline.py` e testes diretamente criados para este épico.

Proibido: dados de episódio, `C:\MSF-data`, exports reais, documentos de
coordenação, AGENTS, fila, auditorias, v2/curated/master, release e Supabase.

## Critérios de aceite

- O sufixo explícito cria o packet no destino pedido; a ausência dele preserva o
  destino legado.
- A checagem raw não escreve e identifica de forma determinística cada input
  ausente ou incompatível, incluindo `metadata.transcript_status` diferente de
  `available` quando esse campo existir.
- A checagem de prontidão não escreve, não exporta e detecta candidato
  procedural sem `steps` antes do build final.
- Não há regressão nos testes gold focados; nenhum dado real ou fingerprint
  protegido é modificado.

## Condições de parada

Pare com `blocked` em lock/PermissionError, falha de teste sem causa local
clara, proposta de mudança incompatível, necessidade de mudar dados reais ou
qualquer alteração fora do ownership. Depois de três retornos sem progresso, o
coordenador define alternativa em vez de repetir a mesma instrução.

## Resultado validado

O hardening foi concluído e aprovado pelo coordenador em 2026-07-11:

- H1 preserva o sufixo legado e aceita um destino explícito de packet;
- H2 é read-only e bloqueia fonte raw ausente, vídeo incompatível, transcript
  indisponível e `metadata.transcript_status` diferente de `available`;
- H3 é read-only e antecipa a falha de integridade, inclusive `steps` ausentes
  em candidatos procedurais;
- H4 passou em 16 testes focados, reproduzidos independentemente pelo
  coordenador. `git diff --check` também passou.

Nenhum dado real, export de episódio, fingerprint protegido, commit, push,
deploy, consolidação ou operação Supabase foi realizado neste épico.
