# MSF-R20-GOLD-PIPELINE-SIMPLIFICATION-001 — Finalização gold por episódio

Status: done — quality gate final aprovado
Worker: Extração Padrão-Ouro
Worker thread: `019f4c90-b9dc-7e32-8ff1-57f8896386d3`
Modelo/esforço: `gpt-5.6-terra/high`
Coordenador: `019f4ee6-a00e-7c90-97bc-5c1aae5c8551`

## Motivo

As fases finais do Fast Path ainda tratam alertas editoriais e detalhes de
persistência como gates de coordenação. Isso produziu várias delegações para o
mesmo episódio, limites artificiais de patches e packets rederivados antes da
auditoria. A Wave 005 fica pausada, sem perda do estado já persistido, enquanto
o contrato é simplificado.

## Resultado esperado

Entregar um fluxo no qual o coordenador delega o épico e só volta depois do
worker concluir os episódios. Por episódio, o worker faz extração integral,
diagnóstico consolidado, correções internas, validação final e um único packet.
O coordenador recebe apenas o resultado final e então executa a auditoria cega.

Fluxo alvo:

```text
transcrição -> extração integral -> diagnóstico consolidado
-> revisão source-backed -> validação determinística -> packet final
-> auditoria independente do coordenador
```

## Stories

### PS-S01 — Classificar bloqueios reais e alertas

Atualizar o autocheck para produzir, de forma determinística:

- `hard_blockers`: fonte/documento/schema inválido, quote ou número sem suporte,
  relação inválida, falha de escrita/rollback e fingerprint divergente;
- `audit_warnings`: promoção/entrevistador, sobreposição possível, ambiguidade
  editorial e equivalência semântica de calibração.

Preservar campos legados necessários para leitura histórica. Warnings isolados
não podem bloquear readiness, build ou export.

### PS-S02 — Trocar janelas de patch por revisões de episódio

Substituir o contrato novo de `patch_window`/limite de dois patches por
provenance de revisão: `revision_id`, `revision_kind` e motivo. A ferramenta
continua usando asserts, `--check`, escrita atômica, rollback e histórico
idempotente, mas não interrompe uma revisão por quantidade de patches.

Históricos e manifestos legados `pre_packet`/`post_packet` permanecem legíveis.
Não falsificar provenance nem reescrever receipts históricos.

### PS-S03 — Criar uma finalização única por episódio

Criar um entrypoint explícito, preferencialmente
`scripts/finalize_gold_episode.py`, e integrá-lo ao runner. Ele deve:

1. executar o autocheck consolidado;
2. parar sem packet somente diante de `hard_blockers`;
3. executar readiness final;
4. derivar artefatos finais e executar um build;
5. executar o validador normal;
6. exportar exatamente um packet de cinco arquivos para a revisão atual;
7. retornar warnings e um recibo idempotente de finalização.

Reexecução da mesma revisão pronta deve reconhecer o recibo e não duplicar
build/export nem alterar bytes sem necessidade. Um episódio bloqueado não deve
impedir outros episódios independentes do manifesto.

### PS-S04 — Derivar ledger e calibração dos candidatos finais

Manter ledger derivado das evidências finais dos candidatos, sem fabricar
decisões manuais. Recalcular o vínculo semântico da calibração depois da revisão
final. Referência inexistente, target duplicado ou segmento inválido é bloqueio;
equivalência semântica ambígua vira warning de auditoria. Claims não podem ser
reescritos apenas para encaixar em targets antecipados.

Os warnings determinísticos entram no `packet_manifest.json`, sem justificativa
ou raciocínio do worker, mantendo o packet cego com exatamente cinco arquivos.

### PS-S05 — Compatibilidade, testes e contrato operacional

Atualizar testes, `docs/gold-extraction-contract.md`, o prompt gold e a skill do
batch. A documentação deve dizer que:

- o episódio é a unidade de execução;
- o worker resolve bloqueios rotineiros dentro do épico;
- checkpoints ficam no próprio chat e não geram retorno intermediário;
- o coordenador só revisa depois do packet final ou de bloqueio terminal real;
- findings da auditoria formam uma única revisão corretiva consolidada.

## Ownership do worker

- `scripts/gold_review_autocheck.py`
- `scripts/gold_review_patch.py`
- `scripts/run_gold_wave.py`
- `scripts/build_gold_semantic_extraction.py`
- `scripts/gold_extraction_common.py`
- `scripts/record_gold_manual_reviews.py`, somente se necessário à revisão
- novo `scripts/finalize_gold_episode.py`
- `tests/test_gold_fastpath.py`
- `tests/test_gold_pipeline.py`
- novos fixtures/testes estritamente necessários
- `docs/gold-extraction-contract.md`
- `prompts/extraction/episode_gold_standard_small_model.md`
- `skills/marketing-swipe-file-scale-batch/SKILL.md`
- `.codex-work/worker-jobs/MSF-R20-GOLD-PIPELINE-SIMPLIFICATION-001`
- `C:\MSF-data\Marketing_Swipe_File\.tmp\MSF-R20-GOLD-PIPELINE-SIMPLIFICATION-001`
  apenas como basetemp descartável de testes

## Dados reais somente leitura

- toda a Wave 005, inclusive `zoChfFHnlOQ`;
- todos os exports e auditorias existentes;
- v2, curated, pool, master e fingerprints protegidos.

## Ações proibidas

- continuar ou corrigir a Wave 005 neste job;
- alterar candidates, reviews, ledger, calibrações ou packets reais;
- editar AGENTS.md, docs/agent-coordination.md, task-queue.md, queue.json ou
  docs/execution-log.md;
- apagar ou reescrever provenance histórico;
- marcar episódio real `passed/complete`;
- commit, push, deploy, consolidação ou Supabase.

## Critérios de aceite

1. Warnings editoriais isolados permitem finalização e continuam visíveis no
   manifest do packet.
2. Hard blocker impede qualquer packet novo e retorna inventário consolidado.
3. Não existe limite técnico por contagem de patches no novo contrato de
   revisão; asserts, atomicidade, rollback e idempotência permanecem.
4. Históricos legados continuam parseáveis.
5. Ledger e calibração finais são derivados dos candidatos finais; targets
   inválidos/duplicados bloqueiam e ambiguidade semântica apenas alerta.
6. Uma revisão pronta produz exatamente cinco arquivos; reexecução idempotente
   não reexporta nem duplica operação.
7. Runner multi-episódio isola bloqueios e consolida o resultado final.
8. Episódios `complete/passed` continuam estritamente read-only.
9. Testes focados e regressões existentes passam, `py_compile` passa e
   `git diff --check` passa.
10. Nenhum dado gold real, export, audit ou fingerprint é alterado.

Regressões mínimas obrigatórias:

- warning-only chega a packet;
- quote/número sem suporte bloqueia antes do packet;
- revisão aplica mais de duas escritas atômicas sem gate artificial;
- manifesto/histórico legado continua legível;
- calibração estrutural inválida bloqueia;
- calibração semanticamente ambígua alerta sem bloquear;
- mesma revisão finalizada duas vezes é idempotente;
- um episódio bloqueado não interrompe outro pronto no manifesto.

## Condições de parada

Parar somente por lock/PermissionError, risco de escrita real, incompatibilidade
de contrato que exija mudança material de schema público, teste que demonstre
perda de proteção ou ação indivisível sem progresso por 30 minutos. Falha
rotineira de implementação deve ser corrigida dentro deste épico, sem solicitar
revisão intermediária ao coordenador.

## Entrega

Enviar um único WORKER_EVENT final ao coordenador, com recibo real de
`send_message_to_thread`. Não enviar progresso. `completed` entrega o diff e as
validações; `blocked` é reservado às condições terminais acima.

## Gate seguinte

O coordenador revisará o diff, reproduzirá testes e fará o quality gate. Somente
depois da aprovação o coordenador criará a retomada da Wave 005 sob o fluxo novo.

## Brief pré-delegação conciso

Propósito: remover microgates das fases finais sem enfraquecer evidência,
atomicidade, fingerprints ou auditoria independente.
Execução: classificar blocker/warning, adotar revisões, criar finalizador único,
derivar ledger/calibração no final e cobrir com testes.
Escritas: somente scripts/testes/contrato/prompt/skill listados e temporários do
job.
Fora de escopo: qualquer dado real, Wave 005, auditoria, release ou master.
Parada: somente risco real, lock/permissão, contrato material ou proteção
violada.
Próximo gate: revisão independente do coordenador; Wave 005 continua pausada.

## Quality gate independente — rodada 1

Evento processado: `MSF-R20-GOLD-PIPELINE-SIMPLIFICATION-001-001`.

Validações reproduzidas pelo coordenador:

- `56 passed` em `tests/test_gold_fastpath.py` e `tests/test_gold_pipeline.py`;
- skill válida pelo `quick_validate.py`;
- `git diff --check` aprovado;
- três provas contratuais isoladas confirmaram as lacunas abaixo sem escrever
  em dados gold reais.

### Findings abertos

1. `PS-QG-001` — major — o recibo considera apenas `revision_id` e a existência
   de cinco JSONs. Uma review alterada depois da finalização ainda retorna
   `idempotent=true` e mantém packet obsoleto. O recibo deve vincular a revisão
   ao hash semântico das entradas finais e aos nomes/hashes exatos do packet.
2. `PS-QG-002` — major — a exportação copia os arquivos diretamente para o
   destino. Falha simulada na segunda cópia deixou um packet parcial com um
   arquivo. A publicação dos cinco arquivos deve ser transacional, com rollback
   do packet anterior ou ausência total de packet novo.
3. `PS-QG-003` — major — target de calibração com `quote_verbatim` inexistente
   no segmento referenciado passou pelo finalizador e foi exportado. A
   literalidade do quote de calibração deve ser hard blocker determinístico.
4. `PS-QG-004` — major — a heurística lexical de alinhamento entre claim e
   evidência está em `hard_blockers`. Como ela é semântica e sujeita a paráfrase,
   deve ser `audit_warning`; quote/evidência estrutural inexistente continua
   bloqueando pela validação determinística.

### Correção consolidada autorizada

A rodada corretiva pode alterar os scripts já delegados e, explicitamente,
`scripts/export_gold_audit_packet.py`. Este arquivo foi tocado na primeira
entrega fora da lista original de ownership; a expansão agora é registrada e
não autoriza qualquer outro arquivo. Devem ser adicionadas regressões específicas
para os quatro findings. Wave 005 e todo dado gold real permanecem read-only.

## Quality gate independente — rodada 2

Evento processado: `MSF-R20-GOLD-PIPELINE-SIMPLIFICATION-001-002`.

- O coordenador reproduziu `64 passed`.
- PS-QG-001..004 foram confirmados como resolvidos: mudança semântica conflita,
  export falho não deixa packet parcial, quote fabricado bloqueia e suspeita
  lexical não é hard blocker.
- A prova adicional de equivalência de formatação encontrou um único resíduo.

### Finding aberto

`PS-QG-005` — major — `_finalization_inputs()` calcula o hash semântico correto,
mas o recibo compara o objeto inteiro, que também contém hashes físicos de cada
entrada. Regravar a mesma review JSON trocando apenas LF por CRLF retorna
`conflict`, embora seu conteúdo semântico seja idêntico. Isso contradiz o
contrato de assinatura semântica e pode recriar loops de formatação.

### Correção final autorizada

Na decisão de idempotência das entradas, comparar somente a assinatura semântica
canônica. Hashes físicos das entradas podem permanecer no recibo como evidência,
mas não bloqueiam a mesma revisão. A integridade do packet continua exigindo os
hashes físico e semântico dos cinco arquivos. Adicionar regressão LF/CRLF e
preservar as regressões de mudança semântica real. Nenhum outro comportamento ou
arquivo está autorizado nesta rodada.

## Quality gate final

Evento processado: `MSF-R20-GOLD-PIPELINE-SIMPLIFICATION-001-003`.

- `65 passed` reproduzidos pelo coordenador em basetemp externo;
- mudança semântica real mantém `conflict`, enquanto LF/CRLF retorna
  `idempotent=true` sem escrita;
- falha de export não deixa packet parcial;
- quote de calibração não-verbatim bloqueia antes do packet;
- claim lexicalmente distante permanece warning e não gate;
- `py_compile`, skill, `git diff --check` e prova read-only das Waves 003/004/005
  aprovados.

Decisão: **approved**. O fluxo está liberado para retomar a Wave 005. Nenhum
commit, push, deploy, consolidação ou Supabase foi executado neste job.
