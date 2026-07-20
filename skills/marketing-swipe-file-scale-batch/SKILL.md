---
name: marketing-swipe-file-scale-batch
description: Scale Marketing Swipe File podcast processing batches. Use when Codex needs to discover more VTurb YouTube episodes, append channel videos to the configured runtime queue, count fully processed videos, run the episode loop repeatedly, use Playwright transcript fallback, extract/classify/dedupe/audit insights, consolidate exports, and continue until a requested complete-video target such as 50 videos is reached.
---

# Marketing Swipe File Scale Batch

## Overview

Use this skill to move from one-off episode processing to a target-driven batch loop.

## Complete Video Definition

There are two distinct completion states. Do not conflate the legacy serving
pipeline with the parallel gold layer.

### Legacy processed

Count a video as legacy processed only when all of these exist and are
non-empty:

- `{dataRoot}/raw/youtube/{video_id}/metadata.json`
- `{dataRoot}/raw/youtube/{video_id}/transcript_original.json` with transcript segments
- `{dataRoot}/processed/{video_id}/content_segments.json`
- `{dataRoot}/processed/{video_id}/chunks/chunk_index.json`
- `{dataRoot}/processed/{video_id}/insights.json`

This state is enough for the frozen v2 serving pool. It is not a gold episode.

### Gold complete

Count a video as gold complete only when its separate
`{dataRoot}/processed/{video_id}/gold_extraction/` package has all of the
following:

- `transcript_clean.json`, `removed_segments.json`, and chronological chunks
  covering every clean segment exactly once;
- one explicit status for every work-order chunk, including a full-read
  zero-insight review when applicable;
- schema-valid `insights_exhaustive.json`, layered verbatim evidence, typed
  quantitative claims, and symmetric acyclic relations;
- `high_signal_coverage_ledger.json` with every signal captured, merged, or
  explicitly excluded;
- episode-discovered calibrations at or above the duration-proportional
  minimum, with required semantic coverage;
- zero open independent-audit findings and `gold_extraction_status.json` set
  to `complete`;
- matching protected fingerprints for `insights_v2.json`,
  `curated_insights.json`, and `insights_v2_master.json`.

`insights.json` alone never counts as gold complete. An episode with status
`awaiting_external_audit` is extraction-ready, but must not be included in a
gold batch total or any master export.

`awaiting_external_audit` is a compatibility name: the audit is external to the
executor phase. Execute the entire epic in the active chat without delegation
or intermediate review. After the complete epic gate, switch to a dedicated
final audit phase using `gpt-5.6-sol` with high reasoning or above. Validate the
finding contract, zero open findings, deterministic checks and protected
fingerprints before deriving `complete`. Future work needs no Claude permission,
execution, or audit; preserve historical providers only as recorded provenance.

## Gold Wave Workflow

Before starting a gold episode:

1. Record Git state and run one technical preflight for the explicit Python
   runtime, required modules, writable job-scoped temp path, data/export access,
   protected fingerprints, packet inputs, and tooling ownership.
2. Define a bounded wave with non-overlapping episode paths. The active chat
   executes the whole wave; ranges and episodes are internal units.
3. Reuse matching chunk reviews and signal inventories by hash. Reopen only
   changed chunks and adjacent context needed for semantic verification.
4. After normal chunk extraction and ledger completion, run an adversarial
   semantic-recall pass for numbers, comparisons, tests, changes, scripts,
   steps, conditions, warnings, caveats, and propositions spanning adjacent
   segments or chunks.
5. Confirm that each `captured` or `merged` ledger entry references a candidate
   expressing the same useful proposition. Topic proximity is not coverage.
6. Run deterministic validation before exporting the blind packet. A valid
   `changes_requested` audit may remain deterministic-pass; only the
   required-audit gate may derive `complete` from `passed` with zero findings.
7. Continue directly across chunks and episodes. Audit only after the
   consolidated wave gate confirms every expected episode is packet-ready or
   terminally blocked, then run the single final Sol audit.
8. Record per-episode metrics and begin expansion with a small wave. Increase
   batch size only after the finding profile remains acceptably low.

The pilot evidence and decisions are recorded in
`docs/coordination/msf-r20-pilot-retrospective.md`.

## Gold Fast Path

Use o Fast Path para ondas novas sem criar microgates ou delegacoes. Ele nao
substitui leitura integral, recall semantico ou a auditoria final unica.

A rota oficial e `chronological_hybrid_v1`: uma leitura cronologica integral,
autoria semantica principal, controles deterministas de risco e finalizacao
one-shot. Os scripts `gold_semantic_*` permanecem pesquisa read-only e nao sao
uma alternativa de producao, mesmo quando estiverem presentes no checkout.

Para executar um episodio, aplique primeiro a skill focada
`gold-episode-extraction`. Ela gera um brief deterministico de risco sobre o
prelint e sobre o dossier final, priorizando multiplicidade numerica,
trajetorias, mecanismos, before/after e outcomes. O brief e apenas navegacao:
o transcript e o dossier source-complete continuam obrigatorios.

1. Gere um manifesto com `mode=auto` por episodio e rode
   `scripts/run_gold_wave.py --manifest <arquivo> --data-root <raiz>` para
   classificar cada rota sem escrita.
2. `new_raw_episode` valida raw e, com `--execute`, prepara transcript, chunks,
   sinais, work orders compactos e o indice semantico derivado just-in-time.
   O indice fica em `processed/<video_id>/`, fora do gold, ligado ao hash da
   transcricao e com autoridade apenas de navegacao. O texto permanece uma
   unica vez nos chunks; work orders usam referencias de segmentos, sinais e
   calibracoes.
3. `resumable_incomplete_gold` reaproveita reviews com `input_hash` igual e
   informa somente chunks pendentes ou desatualizados. Nao reexecute review
   concluida sem uma causa registrada.
4. `protected_complete_read_only` nunca pode ser preparado, patchado ou
   reexportado pelo modo automatico. Reabra um episodio complete/passed somente
   com autorizacao explicita do owner e revisao de escopo.
5. Para escolher o proximo episodio, use o runner Windows-native depois de
   `scripts.verify_gold_runtime.py --runtime windows_native`; nao use comando
   shell interpolado. O runner gera selection receipt, request, IDs, hashes,
   contexto e manifesto para uma fonte completa sem gold existente. O bootstrap
   file-based permanece compativel para episodio ja escolhido. Use primeiro o resumo
   `transcript_semantic_index` para ordenar riscos, numeros e fronteiras, mas
   leia o contexto integral. Monte `payload_format=gold_episode_compact_v3`: candidatos uma
   unica vez, `chunk` numerico, defaults por episodio/tipo, ranges, numbers
   compactos, aliases locais de relacao e `zero_insight_chunks`. Para numeros,
   use `sid`/`si` com `sp` ou `sl`; prefira literal/span estavel e mantenha `so`
   apenas para compatibilidade. O compilador copia `raw` literalmente da
   evidencia e rejeita literal ambiguo. O compilador hidrata reviews, IDs,
   hashes e quotes verbatim.
6. Durante a autoria, use `run_gold_episode_fast.py --dry-run` para reunir o
   manifesto esparso sem receipt nem telemetria. Rode um `--prelint` oficial
   quando o payload estiver fechado para reunir em memoria
   steps procedurais, numeros/evidencia e o fixed point de ledger/risco sem
   criar receipt. Marque suporte indispensavel como `retained_support` e revise
   cada warning claim/evidence pelo `warning_id`, sem ocultar o warning. Com
   `--output`, consuma primeiro o stdout esparso limitado a 8 KB e abra o
   relatorio integral somente para erro novo. A lineage fonte de risk recall
   permanece estavel para residuos que sejam subconjuntos; material novo volta
   a ficar pendente. Suporte retido e residual incidental da mesma lineage usam
   acknowledgements escopados separados; vence o escopo mais especifico.
   Reconcilie cada mencao numerica material literal com um record em `numbers`;
   um record parcial nao encerra o candidato. Preserve multiplicidade em
   sequencias antes/depois. Decimal separado por ASR mantem raw literal,
   `value_status=inferred` e caveat; multiplicador permanece independente.
   Resolva tambem o `semantic_closure_index`: caudas adjacentes, fim do
   episodio, fronteiras, claim-support, counterexamples e contencao de
   evidencia. Feche `must_close` individualmente; `incidental` de risco alto
   exige os source segment IDs revisados. `audit_only` permanece no packet sem
   loop tecnico. Cada warning recebe `captured`/`retained_support` com candidate
   IDs, `incidental` justificado ou `relation_not_useful` para contencao; nunca
   crie claim para ocultar o gate.
   Quando
   o inventario estiver limpo, `--one-shot` e a rota padrao para preview,
   receipt, persistencia, finalizacao e dossier v3 em um processo. `--check` +
   `--apply` ficam somente para recovery/debug e continuam vinculados pelo mesmo
   payload/hash. Nao chame recorder/autocheck/build separadamente nessa rota.
   O prelint devolve um `gold_consolidated_repair_manifest` completo, separando
   reparo mecanico de decisao semantica. Use batches de 8-12 chunks somente quando o episodio nao couber com seguranca
   em uma unica passagem. Para correcao
   fechada posterior, gere primeiro `run_gold_episode_fast --audit-scaffold`
   para resolver ranges, quotes, chunks e asserts atuais; depois use
   `gold_review_patch.py --generate-source-asserts`,
   depois `--check --preview-receipt <arquivo>` e um unico `--apply` vinculado
   ao mesmo receipt. Asserts vem dos reviews fonte e excluem `legacy_*`; nao
   redigite valores UTF-8. Depois da auditoria final aceita,
   `complete_gold_episode.py` gera receipt, relatorio de performance, resumo,
   resposta final e `runtime_retrospective.md`; use `--mirror-job-dir` somente
   para a copia final verificada
   no checkout Windows. Receipt valido e autoridade terminal; nao execute uma
   sequencia adicional Verify/Sync/Verify. Use as metas 6-10m ate 700 segmentos,
   11-15m entre 701-1.300 e 18-30m acima de 1.300. Use a retrospectiva como
   autoridade para active wall, command time, model judgment, semantic spans,
   unattributed gaps, phase transitions e bytes; nao
   reconstrua tempos manualmente.
7. Para reauditoria focal, rode `gold_final_audit_bundle.py --reaudit-delta`
   com os dossiers antes/depois e o audit. Ele e somente leitura e rejeita
   qualquer drift de invariantes integrais. A primeira auditoria continua
   integral; o delta apenas acelera uma reauditoria posterior.
8. Defina `active_budget` no manifesto quando uma wave tiver carga relevante.
   O padrao admite 2.500 segmentos raw, 40 chunks ativos e tres episodios;
   episodios `protected_complete_read_only` e trabalho integralmente concluido
   nao consomem esse orcamento. O runner bloqueia excesso antes de escrever e
   produz faixas de revisao de 8-12 chunks.
9. Para uma correcao fechada, use revisoes identificadas por `revision_id`,
   `revision_kind` e `reason`; cada manifest exige `--check` sem escrita e um
   unico `--apply` atomico. Historicos `patch_window` antigos continuam apenas
   para leitura. Diagnosticos read-only podem ser repetidos.
10. Para episodio semanticamente completo, use
   `scripts/finalize_gold_episode.py`: autocheck, readiness, build, validacao
   normal e export do packet ocorrem nessa ordem. A mesma revisao pronta e
   idempotente; episodios `complete/passed` ficam read-only.
11. Transporte o audit por UTF-8 base64 para um arquivo job-local Linux com
   `record_gold_external_audit.py --envelope-output`; use `--check` nesse mesmo
   envelope para validar sem escrever o episodio. Compare packets por hash
   fisico e hash semantico JSON: CRLF/LF
   isolado e provenance de serializacao, nao mudanca editorial.
12. Ao fechar uma wave, use `run_gold_wave.py --wave-receipt <arquivo>`.
    `ready_for_audit` exige todos os episodios esperados; uma wave parcial
    permanece `in_progress`, e o comando nao cria nem sobrescreve recibo de
    entrega. Apenas `ready_for_audit` ou `terminally_blocked` final escrevem o
    recibo consolidado. Episodio `complete/passed` tambem precisa comprovar o
    packet esperado de cinco arquivos, sua identidade/hashes, auditoria
    passada sem findings e fingerprints iguais antes de contar como pronto.
    O mesmo vinculo entre `export_suffix`, receipt e `packet_manifest` vale
    para episodio pendente de auditoria; receipt nao pode apontar para packet
    de outro episodio.

## Aprendizado do Fluxo Gold

Ao fechar um epic ou wave, relate somente friccoes novas e acionaveis; nao
carregue narracao de sessao para outra tarefa. Para recorrencias gold:

- quando o ledger for derivado da evidencia do candidato, corrija a evidencia
  source-backed e rederive; nao fabrique `ledger_decisions` manuais;
- diferencie hash fisico de hash semantico JSON antes de tratar CRLF/LF como
  mudanca editorial;
- promova falha deterministica recorrente para autocheck, guard ou teste;
- mantenha regras gerais em AGENTS e esta skill apenas com
  heuristicas especificas da extracao gold.

## Batch Workflow

### Runtime canonico Windows

- Use a `.venv` do repositorio e o data root Windows ativo como runtime padrao.
  Execute `python -m scripts.verify_gold_runtime --runtime windows_native`
  antes de qualquer escrita gold.
- Mantenha o job-dir transitorio sob o data root `.tmp` ou em um diretorio
  explicitamente aprovado pelo epic. Nao misture jobs de episodios.
- Nao use `bash -lc`, pipes, redirecionamentos ou Python inline para encapsular
  o pipeline. Passe argumentos explicitos ao Python.
- WSL e opcional: so use `scripts/invoke_gold_wsl.ps1` quando uma distribuicao,
  clone, `.venv` e data root Linux tiverem sido certificados. A ausencia de
  Ubuntu nunca bloqueia a rota Windows.
- Na fast lane, a partida padrao certifica Python/paths/temp, selecao, preparo
  e contexto em um unico processo e um unico `run_id`.
- `StartEpisode` fixa receipt e `execution_signature` no job-dir. Mudanca
  posterior no checkout Windows vale somente para o proximo run; mutacao no
  snapshot Linux bloqueia o run atual. Nao sincronize entre packet e completion.
- Marque spans explicitos de leitura/autoria, prelint, auditoria Sol,
  remediacao, reauditoria e closeout. A retrospectiva reconcilia esses spans
  com runtime e gaps sem inventar tokens.
- Depois que o payload completo estiver limpo, prefira `--one-shot` para
  preview, apply, finalizador e bundle em um processo. Depois da auditoria
  final passada, use `scripts.complete_gold_episode` para registro, build de
  conclusao, validacao obrigatoria, receipt autoconsistente e resumo Markdown
  em um processo.
- Acoes `Fast` e `CompleteAudit` consomem o snapshot fixado no job e nao fazem
  sync. Sincronizacao pertence ao inicio de um novo run; se o snapshot Linux
  mudar durante o episodio, a paridade pinned bloqueia antes da escrita.
- Depois de `changes_requested` em episodio com reviews completos, use
  `run_gold_episode_fast.py --remediate --patch <manifest>` com nova revisao.
  A rota valida o estado composto, aplica uma vez, refinaliza e reemite o
  dossier; nao reentre no recorder compacto de chunks pendentes. Esse estado e
  `remediation_required`, nao terminal: nao gere resposta final antes da
  reauditoria `passed/open_findings=0` e do receipt de completion.
- Acima de 1.300 segmentos, reserve 18-30 minutos e faca uma unica passagem de
  fechamento semantico antes do primeiro packet. Nao comprima a leitura para
  perseguir SLA de episodio curto e depois pagar duas rodadas de reauditoria.
- A extracao e a auditoria gold sao source-only. Nao carregue conteudo de
  `insights_v2`, indices legados ou comparacoes antigas no contexto. Preserve
  apenas fingerprints. Comparacao com legado usa exclusivamente o benchmark
  read-only posterior ao packet congelado.
- Preserve quotes verbatim e o data root Windows durante a migracao. GitHub
  protege somente arquivos versionados; OneDrive pode guardar snapshot fechado,
  mas nao deve sincronizar o data root ativo.

1. Check status:
   `scripts/run_episode_batch.py --target-complete 50 --status-only`
2. Set the runtime data root when MSF-R03 external data is active:
   ```powershell
   $dataRoot = if ($env:MSF_DATA_DIR) { $env:MSF_DATA_DIR } else { "data" }
   ```
3. If the queue has too few videos, discover channel videos:
   `scripts/discover_vturb_youtube_videos.py --append --append-limit 40`
4. Run the target loop:
   `scripts/run_episode_batch.py --target-complete 50 --use-playwright-fallback`
5. If Playwright/NPM needs filesystem access outside the workspace, rerun the same command with approval rather than bypassing the fallback.
6. Use `--start-priority` and `--max-attempts` to continue in controlled cycles after known blocked videos.
7. Stop only when the target is reached, the queue is exhausted, or repeated Playwright/YouTube transcript failures make more progress impossible.

## Scripts

- `scripts/discover_vturb_youtube_videos.py`: reads the VTurb channel page, follows YouTube continuation tokens, writes `{dataRoot}/exports/vturb_channel_discovered_videos.csv`, and can append deduped URLs to `{dataRoot}/input/youtube_urls.csv`.
- `skills/marketing-swipe-file-youtube-transcripts`: preferred YouTube transcript fallback. Use the connected real Chrome UI first: expand the description, click the deep `Mostrar transcricao` button inside `ytd-video-description-transcript-section-renderer`, then read `transcript-segment-view-model` nodes from the `Neste video` panel. Use the legacy CLI script only when a real Chrome session is unavailable.
- `scripts/capture_youtube_transcript_with_playwright_cli.py`: older fallback wrapper. Do not use it for new transcript recovery until it matches the description-button flow in `marketing-swipe-file-youtube-transcripts`.
- `scripts/run_episode_batch.py`: supervises status, ingestion, Playwright fallback, transcript normalization, chunking, asset detection, insight extraction, taxonomy classification, dedupe, audit, summaries, and export consolidation.

## Rules

- Use the bundled Codex Python path when plain `python` is unreliable.
- Preserve raw data. Never fake transcript segments or manually mark a video complete.
- For YouTube transcript fallback, use `$marketing-swipe-file-youtube-transcripts` or its script before concluding a video is blocked.
- Prefer the main queue order by `episode_priority`; append newly discovered videos with increasing priority.
- Treat YouTube transcript failures as blocked state, not as successful extraction.
- IDs beginning with `-` must be passed as `--video-id=<id>` or through a full `--url`.
- Re-run `scripts/consolidate_exports.py` after batch processing.
- Keep raw and processed podcast data local and ignored by Git.
