# MSF-R20-GOLD-WAVE-ONE-SHOT-001 — Wave autônoma com auditoria única

Status: done — quality gate final aprovado
Owner: coordenador Codex
Worker: Extração Padrão-Ouro — gpt-5.6-terra/high
Dados reais durante este hardening: somente leitura

## Problema confirmado

O pipeline já protege escrita e packets, mas ainda falha cedo demais. Um acento,
alias de tema, enum inválido ou campo ausente interrompe o recorder e vira nova
delegação. Além disso, a ausência de um gate consolidado permitiu que checkpoints
de batch e episódios individuais voltassem ao coordenador. Isso contradiz o
objetivo da wave: cinco extrações autônomas e uma auditoria somente no final.

## Resultado esperado

Uma delegação de wave deve:

1. processar todos os episódios listados sem retorno intermediário;
2. compilar e validar cada batch antes da escrita;
3. corrigir automaticamente apenas diferenças mecânicas seguras;
4. devolver de uma só vez todos os erros semânticos restantes para correção local;
5. persistir cada batch de forma atômica, idempotente e verificável;
6. finalizar cada episódio sem packet provisório;
7. emitir WORKER_EVENT somente quando a wave inteira estiver pronta para a fase
   única de auditoria ou quando existir bloqueio externo terminal real.

## Stories

### OS-S01 — Compilador único de reviews

- Extrair do recorder uma função pura que compile payload + estado persistido.
- Normalizar automaticamente, sem tocar quotes verbatim:
  - ASCII/NFKD de `title`, `source_claim` e `takeaway_applicavel`, preservando
    caixa e reparando mojibake reconhecível;
  - themes por aliases canônicos fechados, preservando o original em subthemes;
  - defaults obrigatórios e aliases de enum explicitamente aprovados;
  - serialização e IDs resolvidos.
- Reunir todos os erros do batch em uma única resposta estruturada, com
  candidate_id, campo, categoria, evidência e correção esperada.
- `--check` deve ser read-only e poder ser repetido sem limite artificial.

### OS-S02 — Recorder idempotente e recuperável

- O recorder usa exatamente o compilador da story anterior; helper ad hoc de
  paridade deixa de ser necessário.
- Um batch limpo recebe assinatura semântica e receipt persistente.
- Repetição do mesmo payload já aplicado retorna `idempotent=true`, sem reescrita.
- Se a saída do processo se perder, uma verificação read-only do receipt e dos
  hashes determina se a operação concluiu.
- Falha atômica permite uma segunda rota materialmente diferente dentro do mesmo
  job; só duas falhas reais encerram o ramo.

### OS-S03 — Gate consolidado da wave

- Evoluir `run_gold_wave.py` ou criar um módulo focado para classificar a wave
  como `in_progress`, `ready_for_audit` ou `terminally_blocked`.
- `ready_for_audit` exige, para todos os episódios do manifesto:
  - todos os reviews e recall concluídos;
  - hard blockers zero;
  - receipt de finalização válido;
  - packet exato de cinco arquivos ou episódio já `complete/passed` protegido;
  - fingerprints preservados.
- Um episódio em progresso nunca pode produzir receipt de entrega da wave.
- Um episódio terminalmente bloqueado não impede o processamento dos demais.
- Gerar um receipt consolidado, com assinatura semântica e resultado por episódio.

### OS-S04 — Contrato de execução contínua

- Checkpoints de chunks ficam somente no chat/job-local do worker.
- Limite de contexto não é gate de coordenação; o worker preserva checkpoint e
  continua no mesmo job após compactação nativa quando ela ocorrer.
- Nenhum audit é registrado pelo worker e nenhum episódio individual é enviado
  ao coordenador durante a wave.
- Ao final, `send_message_to_thread` é a primeira ação de entrega e o recibo da
  ferramenta integra o fechamento do worker.

### OS-S05 — Regressões e prova de compatibilidade

Adicionar testes que provem:

- `frustração` vira `frustracao` somente na camada editorial;
- quote verbatim UTF-8 permanece byte-a-byte;
- tema alias e `reported_case` inválido são normalizados conforme tabela fechada;
- múltiplos erros são devolvidos juntos, não um por execução;
- batch aplicado e repetido é idempotente;
- perda de stdout é recuperável por receipt/hashes;
- wave 4/5 incompleta não passa o gate;
- wave 5/5 com packets válidos passa uma vez;
- warnings editoriais não bloqueiam; hard blockers reais bloqueiam;
- episódios `complete/passed` permanecem read-only;
- Waves 003, 004 e o checkpoint atual da 005 permanecem inalterados.

## Ownership do worker

- `scripts/gold_extraction_common.py`
- `scripts/record_gold_manual_reviews.py`
- `scripts/run_gold_wave.py`
- novo módulo de compilação/receipt/gate, se necessário
- `scripts/finalize_gold_episode.py` apenas se o gate consolidado exigir
- `tests/test_gold_fastpath.py`
- `tests/test_gold_pipeline.py`
- fixtures focadas
- `docs/gold-extraction-contract.md`
- `prompts/extraction/episode_gold_standard_small_model.md`
- `skills/marketing-swipe-file-scale-batch/SKILL.md`
- `.codex-work/worker-jobs/MSF-R20-GOLD-WAVE-ONE-SHOT-001`
- temp isolado do job em `C:/MSF-data/Marketing_Swipe_File/.tmp/`

## Fora de escopo

- alterar qualquer gold real, export ou auditoria;
- retomar Wave 005 durante o hardening;
- marcar episódios passed/complete;
- consolidar dados, Supabase, commit, push ou deploy;
- relaxar quote verbatim, números source-backed, relações ou fingerprints.

## Critérios de aceite

- suite focada e pipeline existentes aprovadas;
- compilação Python e `git diff --check` aprovados;
- nenhum dado real modificado;
- testes adversariais cobrem normalização, inventário completo, idempotência,
  recovery e gate 5/5;
- documentação, prompt e skill descrevem a wave como unidade de entrega;
- somente um WORKER_EVENT final com recibo inter-chat.

## Próximo gate

O coordenador revisa diff e testes uma vez. Se aprovado, a Wave 005 é retomada
em uma única delegação autônoma a partir de qoh chunk 011, seguida de wHdy e Bbh.
Não haverá auditoria até o gate consolidado dos cinco episódios.

## Quality gate 1 — 2026-07-14

A suíte declarada foi reproduzida (`69 passed`), a compilação em memória, a
validação da skill e `git diff --check` passaram, e as Waves 003–005 permaneceram
inalteradas em execução read-only. O gate, porém, abriu quatro findings
consolidados antes de liberar a Wave 005:

1. `OS-QG-001` — tema desconhecido é convertido silenciosamente em
   `business_model`; somente aliases fechados podem ser normalizados, e o valor
   desconhecido precisa aparecer no inventário estruturado.
2. `OS-QG-002` — uma wave `in_progress` grava `--wave-receipt`; recibo de entrega
   só pode existir para `ready_for_audit` ou `terminally_blocked` realmente final.
3. `OS-QG-003` — a rota protegida `complete/passed` passa mesmo sem packet; o gate
   deve provar packet exato, identidade do episódio/export, audit válido e
   fingerprints preservados.
4. `OS-QG-004` — candidato sem evidência retorna cedo e oculta erros independentes
   de enum, tema, título e campos; o compilador/CLI deve devolver o inventário
   estruturado completo numa única checagem, sem escrita.

Todos são corrigidos numa única segunda tentativa. Dados reais continuam somente
leitura e a Wave 005 permanece pausada até o quality gate final.

## Quality gate 2 — 2026-07-14

O coordenador reproduziu `73 passed`, compilação, skill e diff. `OS-QG-001`,
`OS-QG-002` e `OS-QG-004` foram resolvidos. A rota protegida de `OS-QG-003`
também passou nos probes de packet ausente, identidade trocada, audit inválido e
fingerprint divergente.

Permaneceu um único residual, `OS-QG-003b`: a rota
`awaiting_external_audit/pending_external` ainda confia no caminho do receipt e
não o compara ao `export_suffix` do manifesto nem à identidade do
`packet_manifest.json`. Uma fixture fez `pending-a` apontar para o packet válido
de `pending-b` e o gate retornou `ready_for_audit`. A segunda e última rodada
corretiva fica limitada a unificar a validação de identidade das rotas pending e
protected, sem alterar dados reais.

## Quality gate final — 2026-07-14

`OS-QG-003b` foi resolvido. O coordenador reproduziu `74 passed` e confirmou em
fixture isolada que um receipt de `pending-a` apontando para o packet de
`pending-b` deixa a wave `in_progress`, registra `packet_identity=false` e não
cria receipt. Restaurado o packet correto, o gate retorna `ready_for_audit` e
grava um único receipt terminal.

Compilação, skill e `git diff --check` passaram. A leitura real da Wave 005
preservou 509 arquivos sem qualquer diferença: zo e JF foram reconhecidos como
protegidos/prontos; qoh, wHdy e Bbh permaneceram em progresso. O hardening está
aprovado e a Wave 005 pode ser retomada pelo contrato one-shot.
