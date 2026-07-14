# Wave 002 do MSF R20 — Épico E2

## Objetivo

Extrair um packet gold cego, íntegro e pronto para auditoria independente do
episódio `qj04cUeaRAw` — *Lucrando Múltiplos 7D/Mês com Perpétuo para Público
Frio*.

O episódio foi escolhido por complementar a Wave 002 com metodologia de
perpétuo para audiência fria. As fontes raw passaram no preflight com 1.609
segmentos; não existiam gold nem export próprio da wave antes do épico.

## Fontes e ownership

Somente leitura:

- `C:/MSF-data/Marketing_Swipe_File/raw/youtube/qj04cUeaRAw/metadata.json`;
- `C:/MSF-data/Marketing_Swipe_File/raw/youtube/qj04cUeaRAw/transcript_original.json`;
- `C:/MSF-data/Marketing_Swipe_File/processed/qj04cUeaRAw/content_segments.json`.

Escrita exclusiva do worker:

- `C:/MSF-data/Marketing_Swipe_File/processed/qj04cUeaRAw/gold_extraction`;
- `C:/MSF-data/Marketing_Swipe_File/exports/msf_r20_wave_002_qj04cUeaRAw`.

Não pertencem ao épico: código, testes, documentação, fila, auditorias,
outros episódios, v2/curated/pool/master, release, consolidação e Supabase.

## Stories internas do épico

| Story | Ação e resultado |
| --- | --- |
| E2-S01 — preflight | Registrar Git, confirmar runtime/caminhos/fingerprints e rodar o preflight raw read-only. Falha bloqueia antes de qualquer escrita. |
| E2-S02 — preparação e revisão | Preparar o gold e revisar todos os chunks cronologicamente. Cada review confirma leitura integral, candidatos atômicos, evidência literal, ledger, relações, conditions/caveats e steps quando aplicáveis. |
| E2-S03 — recall adversarial | Revisar o episódio para números, percentuais, preços, períodos, comparações, antes/depois, testes, scripts, passos, mudanças, condições, alertas, caveats e relações entre chunks. Todo sinal alto recebe destino semântico válido. |
| E2-S04 — autocheck editorial | Antes do readiness, estruturar todo número material com raw literal e tipagem coerente; manter texto editorial ASCII sem ? interno; não converter pergunta do entrevistador em insight independente. |
| E2-S05 — prontidão e packet | Rodar readiness sem escrita. Se passar, rodar um build com `--export-suffix msf_r20_wave_002_qj04cUeaRAw`, validar normalmente uma vez e confirmar packet cego em `awaiting_external_audit/pending_external`. |

## Critérios de aceite

- preflight raw e readiness passam sem escrita fora de seus caminhos normais;
- todos os chunks têm reviews completas e candidatos com IDs únicos;
- números materiais têm `numbers.raw` literal na minimal_quote, valores/unidades
  coerentes e status honesto de caso relatado;
- não há corrupção `letra?letra` em campos editoriais nem insight fundado só em
  fala do entrevistador;
- build, validador normal, ledger e calibração passam;
- status é `awaiting_external_audit` com `audit_status=pending_external`;
- o export explícito contém os cinco arquivos cegos e fingerprints protegidos
  permanecem iguais.

## Condições de parada

Pare com `blocked` em fonte inválida, lock/PermissionError, problema de runtime,
erro de readiness/build/validação, mudança de fingerprint ou necessidade de
escrever fora do ownership. Entregue inventário exato e não faça correção ou
segundo build sem nova story do coordenador. O worker não audita nem deriva
`complete/passed` neste épico.

## Remediação da auditoria E2-S06/E2-S07

O julgamento selado em
`.codex-work/msf-r20-coordinator-audits/qj04cUeaRAw_audit.json` está
`changes_requested` com três findings abertos. O worker somente o registra pelo
script determinístico; não pode editar esse JSON.

| Story | Escopo fechado |
| --- | --- |
| E2-S06 — registrar auditoria | Registrar uma vez o relatório selado. Não editar candidato ou packet nesta etapa. |
| E2-S07a — remover promo/bio | Remover G002 e G005, sem renumerar. Mudar 0005 para excluded/anecdote e 0020-0021 para excluded/promo no ledger. |
| E2-S07b — evidência afirmativa | Reescrever G017 para validação por custo de checkout e janela proporcional ao gasto, usando 0914-0921. Reescrever G023 para estabilidade de conta e evitar ajuste brusco, usando 1270-1271 e 1280-1281. Reescrever G024 para a janela 7-3-1, usando 1356, 1358 e 1362. Atualizar cada ledger correspondente de modo consistente. |
| E2-S07c — ano normalizado | Em G014, preservar raw `setembro de 25` e alterar apenas o valor normalizado do ano para 2025. |
| E2-S07d — rederivação | Rodar readiness uma vez; se passar, um build com o sufixo da Wave 002 e um validador normal. O packet permanece `awaiting_external_audit/pending_external` com três findings abertos. |

Para G017, só retenha números ligados à janela de teste e ao gasto. Para G023,
não use o case de faturamento como insight independente. Para G024, estruture
apenas os períodos 7 e 3 se eles permanecerem no claim/takeaway. Não crie valor,
caveat, condição ou evidência fora dos trechos autorizados.

Qualquer erro novo no readiness, builder ou validator encerra o épico sem
segunda correção. O próximo passo, se o packet for rederivado, é nova auditoria
independente do coordenador.

## Correção residual E2-S07e — literalidade numérica

O primeiro readiness da remediação encerrou corretamente antes do build: a
correção fechada deixou duas literalidades numéricas fora da `minimal_quote`.
Esta story é o único reparo autorizado antes de uma nova rederivação.

| Candidato | Alteração autorizada | Preservação obrigatória |
| --- | --- | --- |
| G017 | Acrescentar o segmento 0920 à evidência mínima, preservando o registro `raw` `2, 3, 4, 10 dias`, `min_value=2` e `max_value=10`. | Não alterar título, claim, takeaway, contexto, condições, ledger ou qualquer outro campo. |
| G024 | Trocar somente o `numbers.raw` para a grafia literal do segmento 1358 (`três`), preservando valor 3, unidade, papel e o restante do candidato. | Não alterar título, claim, takeaway, evidências, contexto, condições, ledger ou qualquer outro campo. |

Depois dessas duas alterações, executar uma vez o readiness. Se passar, executar
uma vez o build com o sufixo explícito da Wave 002 e uma vez o validador normal.
O resultado continua `awaiting_external_audit/pending_external` com os três
findings da auditoria inicial ainda abertos. Não registrar novamente o relatório
selado, não usar `--require-external-audit`, não editar outro candidato e não
repetir comando após erro.

## Correção residual E2-S07f — normalização ASCII de G024

O readiness de E2-S07e confirmou que a inclusão de 0920 resolveu G017. A única
falha restante é G024: o arquivo ainda contém `tr?s`, enquanto o contrato do
validador compara os campos estruturados também pela forma ASCII NFKD do quote
verbatim. Para a evidência literal `três` do segmento 1358, essa forma é
`tres`.

Esta story permite trocar exclusivamente `G024.numbers[1].raw` de `tr?s` para
`tres`. Não alterar valor 3, unidade, papel, status, título, claim, takeaway,
evidências, contexto, ledger, auditoria ou outro candidato. Depois, executar
uma vez o readiness; se ele passar, uma vez o build da Wave 002 e uma vez o
validador normal. O resultado continua pendente de auditoria, com os três
findings abertos. Não registrar a auditoria outra vez e não repetir comando
após erro.

## Remediação da reauditoria E2-S08 — framework completo de G024

A reauditoria selada em
`.codex-work/msf-r20-coordinator-audits/qj04cUeaRAw_reaudit_001.json` está
`changes_requested` com um finding aberto. QJ-001 e QJ-003 estão resolvidos; o
worker registra este novo relatório uma única vez, sem o editar.

| Story | Escopo fechado |
| --- | --- |
| E2-S08a — registrar reauditoria | Registrar uma vez o relatório selado de reauditoria. Não editar candidato ou packet nesta etapa. |
| E2-S08b — completar G024 | Reescrever somente G024 como regra de decisão 7-3-1 completa: 7 dias para período longo, 3 para tendência, dia atual para decisão; antes de desligar criativo com histórico bom em queda, reduzir verba proporcionalmente à perda e subir novamente após recuperação. A minimal_quote usa 1356, 1358, 1359, 1361 e 1363-1367; context_range vai de 1356 a 1367. Capturar esses segmentos no ledger para G024 e preservar os demais destinos. Reter e estruturar somente `7 dias`, `tres`, `50%, 60%, 70%` e `20%`, com valores, faixas, percentuais e status reportado coerentes. |
| E2-S08c — rederivação | Rodar readiness uma vez; se passar, um build com o sufixo da Wave 002 e um validador normal. O packet permanece `awaiting_external_audit/pending_external` com um finding aberto. |

Não criar ou remover candidatos, não alterar G014/G017/G023, não reabrir QJ-001
ou QJ-003 e não usar 1360, seus números de exemplo ou qualquer outro segmento
fora do inventário. Todo erro novo encerra a story sem segunda correção, build
ou validação.

## Fechamento E2-S09 — registro da reauditoria aprovada

A reauditoria selada em
`.codex-work/msf-r20-coordinator-audits/qj04cUeaRAw_reaudit_002.json` está
`passed`, tem `open_findings=0` e é de revisor separado do executor. O worker
somente a registra uma vez, sem editar candidatos, ledger ou packet. Em seguida
executa um build para derivar o gate e um único
`validate_gold_extraction --require-external-audit`.

O aceite exige `complete`, `audit_status=passed`, `open_audit_findings=0`, 23
IDs distintos, relatório válido, packet com cinco arquivos e fingerprints
protegidos inalterados. Falha no registro, build ou validação encerra o épico;
não há reparo editorial, novo export, release, consolidação ou Supabase nesta
story.

## Resultado do épico

E2 foi concluído com 23 candidatos, packet de cinco arquivos, auditoria de
coordenador aprovada e zero findings abertos. O estado final é
`complete/passed`; nenhum dado foi consolidado fora do gold, e não houve commit,
push, deploy ou Supabase.

## Próximo gate

Se o packet estiver pronto, o coordenador realiza a auditoria independente. Se
houver bloqueio, o coordenador planeja uma story corretiva limitada pelo
inventário retornado.
