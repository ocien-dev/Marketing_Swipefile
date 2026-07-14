# Plano enxuto de épicos e stories da wave 001 do MSF R20

## Objetivo

Este plano substitui a execução contínua por micro-checkpoints na wave 001.
Mantém a separação obrigatória entre coordenador/worker e os gates gold, mas
usa um épico documentado por vez: planejar, executar suas stories internas,
revisar no coordenador e então decidir o próximo épico. Aplica-se primeiro a
mCaFyZpXJdE e somente depois a TOW0sWhPaZw.

O coordenador continua em gpt-5.6-terra/xhigh; o executor designado continua em
gpt-5.6-terra/high. É uma redução de processo e contexto, não redução de
modelo nem de qualidade.

## Regras operacionais

- Cada turno do worker executa um épico deste documento. As stories internas
  são concluídas em ordem, sem ida e volta ao coordenador entre elas.
- O worker lê somente o plano do épico e o contexto adicional da delegação. Ele
  não começa outro épico nem episódio automaticamente.
- O épico relata apenas artefatos materiais, validações, bloqueios e próximo
  épico não executado. Comentário genérico de progresso não é necessário.
- O coordenador confirma o resultado do épico no chat do worker, confere
  ownership e evidência, registra o gate na fila durável e só então delega o
  próximo épico.
- Uma story de correção é limitada a 12 candidatos listados ou 8 chunks. Quando
  a story seguinte já estiver especificada, o worker continua no épico; causa
  nova e desconhecida para para revisão do coordenador.
- Falha repetida segue as regras existentes de três retornos sem progresso e de
  30 minutos por ação indivisível.

## Épico E1 — estabilizar mCaFyZpXJdE

| Story | Status | Resultado e fronteira |
| --- | --- | --- |
| E1-S01 — checkpoint seguro de reparo | complete | Preservar e verificar o reparo numérico concluído em 025-036. O evento MSF-R20-WAVE-001-016 é a entrega do worker. |
| E1-S02 — diagnóstico determinístico de pendências | complete | O builder retornou 18 erros de raw ausente em 13 candidatos (G058, G059, G060, G061, G063, G066, G068, G069, G070, G071, G073, G075 e G076), com 79 candidatos e calibração aprovada. Não houve correção, export ou segundo build. |
| E1-S03-a — correção residual conhecida | complete | Os 13 candidatos autorizados foram corrigidos sem criar, mesclar ou excluir candidatos. |
| E1-S04 — prontidão do pacote | complete | Build final e validador normal passaram; packet cego foi exportado em awaiting_external_audit/pending_external com 79 candidatos, ledger 2.106 e calibração 10/7 pass. |
| E1-S05 — gate cego independente | changes_requested | A auditoria selada `mCaFyZpXJdE_audit.json` abriu o finding major `MSF-R20-MCA-001`: quatro `numbers.raw` perderam acentos e não são verbatim. Integridade, quotes, ledger, calibração, relações e editorial passaram. |
| E1-S06 — reparo literal de números | complete | As quatro strings em G009, G035 e G042 foram corrigidas literalmente, sem alterar IDs, valores, unidades, candidatos ou auditoria selada; o packet foi reconstruído e validado normalmente. |
| E1-S07 — nova auditoria independente | complete/passed | `mCaFyZpXJdE_reaudit_001.json` fechou `MSF-R20-MCA-001` como resolved; o packet passou com zero finding aberto e fingerprints protegidos iguais. |
| E1-S08 — registrar auditoria aprovada e concluir | complete/passed | E1-S08-b registrou `_reaudit_002.json`, derivou `complete/passed` e passou na validação com `--require-external-audit`; há 79 candidatos, zero finding aberto e cinco fingerprints protegidos iguais. |

### Evidência e segurança de E1

- O ownership de dados fica apenas no diretório
  mCaFyZpXJdE/gold_extraction e no diretório de export da wave.
- Nenhuma escrita em v2, curated, pool, master, release, Supabase ou provenance
  de auditoria pertence a uma story do executor.
- Os fingerprints protegidos de
  .codex-work/coordination/msf-r20-wave-001-protected-before.json precisam
  permanecer iguais em E1-S04 e E1-S05.

## Épico E2 — extrair TOW0sWhPaZw

O épico E2 só pode começar depois que E1 estiver `complete/passed` e receber seu
próprio brief de execução.

| Story | Status | Resultado e fronteira |
| --- | --- | --- |
| E2-S01 — preflight e mapa de revisão | delegated — retomada autorizada | O preflight inicial parou porque o preparador requer raw metadata/transcript. A fonte raw canônica foi confirmada; retomar apenas com leitura de `raw/youtube/TOW0sWhPaZw/metadata.json` e `transcript_original.json`, depois produzir o mapa determinístico. |
| E2-S02 — revisão cronológica completa | delegated | Revisar todos os chunks do episódio em grupos locais de até oito, com checkpoints no chat do worker, mas sem retorno intermediário ao coordenador. Verificar fronteiras adjacentes e registrar todos os candidatos em reviews. |
| E2-S03 — recall semântico adversarial | delegated | Depois da revisão completa, buscar números, comparações, testes, passos, condições, alertas, caveats e relações divididas; destinar cada sinal alto a candidato ou exclusão válida. |
| E2-S04 — build diagnóstico | complete / changes_requested | O build único confirmou calibração aprovada e encontrou 31 candidatos procedurais sem `steps`; não houve correção, build final, validação ou export. |
| E2-S04a — integridade procedural | delegated | Para a lista fechada de 31 candidatos, adicionar somente passos sustentados pelo claim e pelas citações existentes. Não reclassificar, criar, excluir, mesclar, renumerar ou mudar evidência, números, relações, títulos, condições ou caveats. |
| E2-S04b — prontidão do packet | queued | Depois de E2-S04a, rodar o build final uma vez, o validador normal uma vez e exportar packet cego em awaiting_external_audit/pending_external. |
| E2-S05 — gate independente do coordenador | complete/passed | A reauditoria selada `TOW0sWhPaZw_reaudit_001.json` fechou `MSF-R20-TOW-001` como resolved: o packet sincronizado usa `Meça`, tem 72 IDs e fingerprints protegidos iguais. |
| E2-S06 — reparo literal de encoding | complete | O relatório changes_requested foi registrado e o gold corrigiu somente `Me?a` → `Meça` em G072; build e validação normal passaram. |
| E2-S06a — sincronizar packet da wave | complete | `export_gold_audit_packet.py` sincronizou explicitamente os cinco arquivos atuais do gold para o sufixo da wave, sem build, validação ou edição de insight. |
| E2-S07 — registrar auditoria aprovada e concluir | complete/passed | `_reaudit_001.json` foi registrado; o builder derivou `complete/passed` e a validação com `--require-external-audit` passou com 72 IDs e zero finding aberto. |

## Brief simples obrigatório antes da delegação de E1

**Rascunho de planejamento — não autoriza execução.** Ao liberar o épico E1, o
coordenador publicará este mesmo conteúdo na conversa imediatamente antes de
enviar a tarefa ao worker:

- **Por que agora:** fechar mCaFyZpXJdE até um packet cego válido, usando os
  reparos numéricos já feitos e sem iniciar o segundo episódio.
- **O que o worker fará, em ordem:** corrigirá somente o inventário conhecido
  de 13 candidatos (G058, G059, G060, G061, G063, G066, G068, G069, G070,
  G071, G073, G075 e G076); rodará o builder uma vez final; se passar, rodará a
  validação normal e exportará um único packet cego.
- **O que poderá alterar:** apenas
  processed/mCaFyZpXJdE/gold_extraction e o export
  msf_r20_wave_001_mCaFyZpXJdE.
- **O que entregará:** estado awaiting_external_audit/pending_external, 79
  candidatos distintos, validação normal aprovada, ledger/calibração aprovados,
  cinco arquivos cegos e fingerprints protegidos iguais.
- **O que não fará:** não auditará, não marcará complete/passed, não tocará
  TOW0sWhPaZw, v1/v2/curated/master, código, documentação, release,
  consolidação ou Supabase.
- **Quando para:** se houver lock/PermissionError, uma causa nova, candidato
  fora do inventário conhecido ou erro no build final. Nesses casos, o worker
  entrega a lista exata e o coordenador decide o próximo passo. Se o packet
  ficar pronto, o coordenador faz a auditoria cega independente.

## Ponto atual para retomar

E1 está `complete/passed`: o registrador aceitou `_reaudit_002.json` com zero
finding aberto, o builder derivou o estado final e o validador exigido passou.
O coordenador confirmou 79 candidatos distintos e cinco fingerprints protegidos
iguais ao snapshot. E2 concluiu preflight, 35 reviews, recall e build
diagnóstico, reparou a integridade de `steps`, validou normalmente e exportou o
packet. A reauditoria fechou `MSF-R20-TOW-001` e o packet sincronizado passou.
E2-S07 registrou o julgamento aprovado e derivou `complete/passed`. A wave 001
está concluída: E1 (`mCaFyZpXJdE`) e E2 (`TOW0sWhPaZw`) passam, sem finding
aberto e com fingerprints protegidos iguais ao snapshot.

## Contrato de execução do E2

- Fontes de leitura esperadas: `raw/youtube/TOW0sWhPaZw/metadata.json`,
  `raw/youtube/TOW0sWhPaZw/transcript_original.json` e
  `processed/TOW0sWhPaZw/content_segments.json`. O raw foi confirmado como do
  vídeo correto, com transcrição disponível de 2.108 segmentos; a pasta gold e
  o export isolado estavam ausentes no preflight do coordenador.
- O worker pode escrever somente `processed/TOW0sWhPaZw/gold_extraction` e
  `exports/msf_r20_wave_001_TOW0sWhPaZw`; as três fontes acima são somente
  leitura.
- Uma falha de build só permite um reparo no mesmo épico quando for erro objetivo
  de número/evidência em até 12 candidatos. A exceção registrada é E2-S04a:
  preencher `steps` somente para os 31 IDs do inventário procedural, com base em
  claims e citações já existentes. Acima desse limite, ou em qualquer outro
  erro, o worker para com inventário exato e evento `blocked`.
- O output de sucesso é um packet cego de exatamente cinco arquivos em
  `awaiting_external_audit/pending_external`. Auditoria, conclusão, dados
  consolidados e o episódio `mCaFyZpXJdE` continuam fora do ownership do worker.

### Inventário fechado de E2-S04a

`G007`, `G008`, `G010`, `G011`, `G012`, `G015`, `G016`, `G018`, `G019`,
`G027`, `G028`, `G031`, `G032`, `G035`, `G040`, `G044`, `G046`, `G048`,
`G049`, `G050`, `G052`, `G053`, `G057`, `G059`, `G061`, `G063`, `G065`,
`G067`, `G068`, `G069` e `G071`.

### Finding de auditoria E2: MSF-R20-TOW-001 (resolvido)

- Escopo: somente `TOW0sWhPaZw-G072.takeaway_applicavel`.
- Correção literal: `Me?a` → `Meça`.
- Não pode mudar citações, evidências, números, steps, relações, tipo, título,
  candidate ID, ledger, calibração ou qualquer outro insight.
- A reauditoria confirmou `Meça`, sem a forma corrompida, e selou `passed` com
  `open_findings=0`. A conclusão depende apenas do registro determinístico do
  relatório aprovado.
- O packet da wave deve ser produzido explicitamente com
  `export_gold_audit_packet.py --suffix msf_r20_wave_001_TOW0sWhPaZw`; o
  builder preserva o caminho de compatibilidade `msf_r20_piloto_TOW0sWhPaZw`.

## Brief simples obrigatório antes de delegar E1-S06

**Rascunho de planejamento — não autoriza execução.** Antes de enviar a story,
o coordenador publicará este conteúdo na conversa:

- **Por que agora:** corrigir o único finding aberto do E1 sem ampliar o
  episódio, o inventário ou a interpretação editorial.
- **O que o worker fará, em ordem:** trocará somente `6 7 milhoes` por `6 7
  milhões` e `2 milhoes` por `2 milhões` em G009; `umas 10 variacoes` por
  `umas 10 variações` em G035; e `10 bibliotecas de anuncio` por `10
  bibliotecas de anúncio` em G042. Depois rodará o builder uma vez, a
  validação normal uma vez e exportará um packet cego.
- **O que poderá alterar:** apenas
  `processed/mCaFyZpXJdE/gold_extraction` e o export
  `msf_r20_wave_001_mCaFyZpXJdE`.
- **O que entregará:** os mesmos 79 candidatos e lifecycle
  `awaiting_external_audit/pending_external`, com validação normal aprovada,
  packet de cinco arquivos e fingerprints protegidos iguais.
- **O que não fará:** não editará a auditoria selada, não criará, mesclará,
  excluirá ou renumerará candidato, não tocará em TOW0sWhPaZw, v1/v2,
  curated/master, código, documentação, release, consolidação ou Supabase.
- **Quando para:** se houver lock/PermissionError, erro novo no builder ou
  diferença fora dos quatro strings. Nesses casos, relata a evidência e o
  coordenador decide. Se o packet ficar pronto, o coordenador faz E1-S07.

## Brief simples obrigatório antes de delegar E1-S08

**Rascunho de planejamento — não autoriza execução.** Antes de enviar a story,
o coordenador publicará este conteúdo na conversa:

- **Por que agora:** a reauditoria independente passou; falta somente registrar
  esse julgamento por script para que o lifecycle derive `complete/passed`.
- **O que o worker fará, em ordem:** registrará
  `mCaFyZpXJdE_reaudit_002.json` com `record_gold_external_audit`, rodará o
  builder uma vez, validará uma vez com `--require-external-audit` e confirmará
  status, zero findings, candidate IDs e fingerprints.
- **O que poderá alterar:** somente
  `processed/mCaFyZpXJdE/gold_extraction` e seu export da wave; o JSON de
  reauditoria é apenas leitura.
- **O que entregará:** `complete`, `audit_status=passed`, zero findings
  abertos, validação final aprovada e fingerprints protegidos iguais.
- **O que não fará:** não mudará o julgamento selado, candidatos, evidência,
  TOW0sWhPaZw, código, documentação, fila, release, consolidação ou Supabase.
- **Quando para:** em lock/PermissionError, rejeição do relatório pelo script,
  falha do builder ou da validação final. Nesses casos, não corrige dados e
  reporta a causa; se concluir, o coordenador fecha o Epic E1.

## E1-S08-b — registro com envelope de auditoria compatível

O coordenador selou `mCaFyZpXJdE_reaudit_002.json` a partir do julgamento
aprovado em `_reaudit_001.json`. As alterações são de contrato: acrescentar
`audit_route=codex_coordinator_blind_reaudit_after_worker_correction`,
`open_findings=0` e normalizar `segment_range` para a faixa numérica `[322,
1724]`. O finding resolvido, evidências, reviewer, data, status e conclusão do
julgamento permanecem idênticos.

O worker somente lê esse novo relatório, executa o registrador uma vez, o
builder uma vez e o validador com `--require-external-audit` uma vez. Ele não
edita o relatório, candidatos, evidências, relações, código, documentação, E2,
camadas consolidadas ou serviços externos. Lock/PermissionError, rejeição do
relatório, falha de build ou falha de validação encerram a story com evento
`blocked`; qualquer resultado aprovado retorna em um único evento `completed`.
