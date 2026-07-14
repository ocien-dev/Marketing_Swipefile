# MSF-R20-GOLD-FASTPATH-002 — otimização ponta a ponta

## Objetivo

Reduzir tempo, tokens e retornos por episódio, medindo o fluxo completo e não
apenas o tamanho dos work orders. Este épico corrige os gargalos observados na
Wave 004 antes de retomar a reauditoria pendente de `v6luZ9KvmOI`.

O padrão-ouro, a leitura integral e a auditoria independente permanecem. A
otimização deve remover fragmentação e falhas mecânicas, não reduzir cobertura.

## Diagnóstico que orienta o trabalho

- A Wave 003 teve 24 chunks e 1.284 segmentos limpos; a Wave 004 teve 66 chunks
  e 3.652 segmentos limpos. Três episódios não representam uma carga fixa.
- A redução de 66%–69% medida no Fast Path 001 era de bytes dos work orders,
  não de consumo ponta a ponta.
- Checkpoints seguros viraram retornos ao coordenador, embora não fossem
  bloqueios reais.
- O autocheck não antecipou equivalência semântica de ledger/calibração,
  coerência completa dos números, relações e suporte editorial.
- Limites de uma única tentativa para diagnósticos read-only transformaram
  correções pequenas em novas delegações.
- Helpers específicos, contrato de audit e diferenças CRLF/LF criaram rodadas
  sem ganho editorial.

## Stories

| Story | Resultado esperado |
| --- | --- |
| O1 — orçamento real da wave | O runner calcula carga ativa por segmentos e chunks, exclui episódios protegidos e bloqueia antes de escrita um manifesto acima do orçamento declarado. O manifesto deixa de usar somente quantidade de episódios como escala. |
| O2 — execução contínua por faixas | A unidade recomendada passa a ser uma faixa de 8–12 chunks. Escritas podem continuar em batches atômicos menores, mas checkpoint normal fica local e não encerra o job nem gera evento final. |
| O3 — pré-auditoria semântica | O autocheck estrito passa a inventariar alinhamento claim/evidência, números materiais e seus campos, ledger captured/merged sem equivalência, calibrações sem a mesma proposição, suporte exclusivo de entrevistador/promo, relações e caveats. Heurística incerta deve pedir revisão dirigida, não fabricar correção. |
| O4 — janela corretiva interna | Antes do primeiro packet, o worker pode executar diagnósticos read-only quantas vezes forem necessárias e até dois patches declarativos distintos, cada um com `--check` e uma aplicação. Só há um build final. Erro fora do inventário continua bloqueando. |
| O5 — patch e auditoria genéricos | O patch declarativo passa a cobrir redirecionamento de calibração com asserts e escrita atômica. O registrador de audit ganha modo `--check` sem escrita. Hashes usados como gate devem distinguir hash físico de hash semântico para não tratar CRLF/LF como mudança de dados. |
| O6 — métricas ponta a ponta | O runner/receipt registra carga ativa, chunks revisados e pendentes, candidatos, batches, patches, builds, auditorias e tempo por etapa quando mensurável. Tokens só são declarados quando a superfície fornecer número confiável. |
| O7 — regressões e contrato | Fixtures reproduzem os tipos de falha vistos em yyo, 8WE e v6lu. Testes existentes continuam passando. Skill e prompt passam a refletir orçamento por carga, faixas maiores, pré-auditoria e janela corretiva. |

## Orçamento padrão

Para novas waves, o manifesto precisa declarar orçamento. O padrão inicial é:

- até 2.500 segmentos raw ativos;
- até 40 chunks ativos estimados ou preparados;
- até três episódios, desde que os dois limites anteriores também passem.

O runner deve reportar a carga e bloquear antes de escrever quando qualquer
limite for excedido. Episódios `complete/passed` e partes já concluídas de uma
retomada não entram na carga ativa. O owner ou coordenador pode autorizar outro
orçamento em plano posterior, sem mudar o padrão global silenciosamente.

## Fluxo otimizado esperado

1. planejar a wave por carga e executar preflight read-only;
2. preparar somente episódios dentro do orçamento;
3. revisar continuamente em faixas de 8–12 chunks, mantendo batches de escrita
   atômicos quando necessário;
4. gravar checkpoint local, mas continuar o mesmo job se não houver bloqueio;
5. executar pré-auditoria semântica e reunir todo o inventário antes de editar;
6. aplicar no máximo dois manifests declarativos novos, cada um uma única vez;
7. repetir apenas diagnósticos read-only até `ready`;
8. executar um build final, um validador normal e gerar o packet;
9. enviar um único `WORKER_EVENT` final;
10. parar para auditoria independente do coordenador.

## Ownership do worker

Arquivos permitidos:

- `scripts/run_gold_wave.py`;
- `scripts/gold_review_autocheck.py`;
- `scripts/gold_review_patch.py`;
- `scripts/gold_reaudit_delta.py`;
- `scripts/record_gold_external_audit.py`;
- `scripts/reprocess_gold_episode.py`;
- `scripts/record_gold_manual_reviews.py`;
- `scripts/build_gold_semantic_extraction.py`;
- `scripts/gold_extraction_common.py`;
- testes e fixtures gold sob `tests/`;
- `prompts/extraction/episode_gold_standard_small_model.md`;
- `skills/marketing-swipe-file-scale-batch/SKILL.md`.

Os diretórios gold, exports e auditorias reais de todas as waves são somente
leitura neste épico. O worker não edita AGENTS.md, fila, este plano,
`docs/agent-coordination.md` ou `docs/execution-log.md`.

## Critérios de aceite

- manifesto acima do orçamento é rejeitado antes de qualquer escrita;
- episódios protegidos e trabalho já concluído não inflam a carga ativa;
- planejamento retorna faixas de 8–12 chunks e não converte checkpoint normal
  em bloqueio ou evento final;
- pré-auditoria detecta fixtures sintéticas equivalentes às lacunas de números,
  ledger, calibração, relações e suporte editorial vistas na Wave 004;
- diagnósticos read-only podem ser repetidos sem novo job;
- terceiro patch pré-packet é rejeitado, e os dois permitidos continuam
  atômicos, protegidos por asserts e não reaplicáveis;
- calibrações podem ser redirecionadas pelo patch genérico sem helper Python;
- `record_gold_external_audit --check` valida o envelope e não escreve;
- comparação semântica não acusa CRLF/LF como mudança de conteúdo;
- métricas reportam carga e contadores ponta a ponta sem alegar tokens ausentes;
- suíte Fast Path/gold, `py_compile` e `git diff --check` passam;
- runner read-only preserva Wave 003 e Wave 004; nenhum gold, export, audit ou
  fingerprint real muda.

## Condições de parada

Pare em mudança de schema público, quebra de compatibilidade, escrita em dados
reais, lock/PermissionError, teste que mostre perda de cobertura ou necessidade
de ampliar o ownership. Não instalar dependência nova sem decisão. Uma ação
única parada por 30 minutos deve usar caminho materialmente diferente.

## Gate seguinte

O coordenador revisará o diff e reproduzirá testes, orçamento, fixtures
semânticas e proteção read-only. Somente com o Fast Path 002 aprovado a Wave
004 volta à reauditoria de `v6luZ9KvmOI`.

## EXECUTION BRIEF conciso

Corrigir o Fast Path para otimizar o fluxo inteiro: planejar por carga, trabalhar
em faixas maiores sem devolver checkpoints normais, antecipar problemas
semânticos, permitir uma janela interna de dois patches, eliminar helpers de
calibração/audit e medir contadores reais. Alterar somente scripts, testes,
fixtures, prompt e skill listados. Tratar todos os dados reais como somente
leitura. Entregar um único evento final com diff, testes, métricas e prova de
que Wave 003 e Wave 004 permaneceram inalteradas.

## Quality gate — rodada 1

O evento `MSF-R20-GOLD-FASTPATH-002-001` foi confirmado no chat do worker. O
coordenador reproduziu 50 testes, `py_compile`, `git diff --check`, os runners
read-only das Waves 003/004 e os seis hashes de status. A proteção passou, mas
o gate funcional permanece `changes_requested` pelos findings abaixo.

### FP2-001 — carga ativa de retomadas está incorreta

Uma retomada soma todos os segmentos raw do episódio, mesmo quando só um chunk
está pendente. Chunks stale entram em `active_episodes`, mas não em
`active_chunks` nem nas faixas. Uma wave acima do orçamento também bloqueia
rotas não protegidas que não participam da carga ativa.

Correção exigida: para episódios preparados, contar segmentos e chunks da união
`pending + stale`; excluir trabalho concluído; planejar ambos; bloquear apenas
rotas ativas que contribuíram para o excesso. Adicionar regressões de retomada
grande com um chunk pendente e de rota stale-only.

### FP2-002 — pré-auditoria não sustenta o gate semântico

Os campos novos não são lidos por `_strict_autocheck_errors` nem pelo exit code
`--strict`. Ledger automático não é inspecionado; o código verifica apenas
decisões manuais e usa campos que não existem no candidato persistido. Claim e
calibração passam com uma única palavra compartilhada, mesmo quando omitem a
proposição numérica. Qualquer presença de linguagem de entrevistador marca o
candidato como sustentado somente por entrevistador, mesmo com fala direta do
convidado.

Correção exigida: separar erros determinísticos de itens `review_required`, dar
IDs estáveis e exigir um receipt compacto e atualizado para toda decisão
heurística antes do build. O receipt deve registrar `corrected` ou `incidental`
com justificativa e hash do relatório. Inspecionar a prévia do ledger automático,
preservar âncoras numéricas em claim/calibração e marcar `interviewer_only`
somente quando todo o suporte for desse tipo. O runner e `--strict` não podem
prosseguir com item sem resolução. Adicionar fixture de “mesmo tópico, resultado
numérico ausente”.

### FP2-003 — redirecionamento de calibração aceita estado inválido

O patch aceita `semantic_candidate_ids` inexistentes e não revalida segmentos,
targets duplicados ou cobertura depois da alteração.

Correção exigida: limitar campos editáveis, validar candidatos e segmentos
contra o estado final, rejeitar targets duplicados e executar a validação de
calibração antes do batch atômico. Testes precisam provar rejeição sem escrita.

### FP2-004 — métricas nomeiam presença como contagem

`review_batches` é quantidade de reviews, enquanto `builds` e `audits` são
booleans derivados da presença de arquivos. Isso não mede batches, builds ou
rodadas de auditoria.

Correção exigida: registrar eventos idempotentes num receipt interno do Fast
Path quando recorder, patch, build e audit executarem. Quando histórico não
existir, reportar `not_available`, nunca inferir uma contagem falsa. Manter
compatibilidade e não tocar em dados reais durante os testes.

### EXECUTION BRIEF conciso — correção 1/2

Corrigir somente FP2-001 a FP2-004 e adicionar as regressões adversariais.
Preservar as partes já aprovadas: orçamento pré-escrita, faixas 8–12, dois
patches, audit `--check`, hashes físico/semântico e proteção read-only. Não tocar
em dados reais, docs do coordenador ou Wave 004. Entregar um único evento final.

## Quality gate — rodada 2

O evento `MSF-R20-GOLD-FASTPATH-002-002` foi confirmado no chat do worker, que
está inativo. O coordenador reproduziu 55 testes, `py_compile`, `git diff
--check` e os runners read-only das Waves 003/004. Os seis hashes de status
permaneceram iguais. As correções de carga, redirects e métricas passaram seus
casos direcionados.

O gate continua `changes_requested` por um único resíduo de FP2-002. O
autocheck ainda procura `minimal_segment_ids` e `support_segment_ids` diretamente
no candidato persistido; esses campos só existem no draft e são convertidos em
`evidence.minimal_quote` e `evidence.support_segments` pelo recorder. Em dados
reais de v6lu, isso produziu 1.166 falsos itens de `automatic_ledger_preview` e
1.967 itens `review_required`, apesar de os candidatos terem citações válidas.
O receipt poderia apenas mascarar esse resultado, portanto o gate semântico não
é aceitável.

### FP2-002b — resolver IDs de evidência no formato persistido

Correção exigida: centralizar a leitura de `segment_id` a partir de
`evidence.minimal_quote` e `evidence.support_segments`, e usar essa mesma fonte
nas verificações de ledger manual e da prévia do ledger automático. Preservar
compatibilidade com drafts legados que ainda tenham os dois arrays antigos.
Adicionar regressões que provem: (1) candidato persistido já sustentado não vira
falso `automatic_ledger_preview`; (2) ledger captured aponta corretamente para
o candidato; e (3) um sinal realmente não coberto continua em
`review_required`. Não alterar dados reais nem criar receipts reais.

### EXECUTION BRIEF conciso — correção 2/2

Corrigir somente a resolução de IDs de evidência persistida no autocheck e os
testes associados. Não mudar orçamento, patch, calibração, métricas, prompt,
skill, dados reais ou docs do coordenador. A aprovação depende da regressão
gold completa, de um caso adversarial de ledger automático e da prova read-only
das Waves 003/004. Esta é a segunda e última rodada corretiva prevista; nova
falha material será escalada ao owner.

## Quality gate — rodada 3 e decisão necessária

O evento `MSF-R20-GOLD-FASTPATH-002-003` foi confirmado no chat do worker, que
está inativo. O coordenador reproduziu 56 testes, `py_compile` e
`git diff --check`. Os três novos testes de formato persistido passaram.

Em v6lu somente leitura, a correção reduziu o falso inventário de 1.166 para
779 itens, mas não tornou o gate utilizável: os 779 itens restantes são os
mesmos 779 segmentos que o ledger final já classifica como `excluded/low_signal`.
O autocheck inclui cada um em `automatic_ledger_preview` e em
`review_required`; por consequência, produz 1.580 pendências (1.558 de
high-signal) e exigiria receipt manual para exclusões já justificadas. Isso
contraria O3/O4 e volta a elevar custo e tokens em vez de reduzir loops.

### FP2-002c — exclusões finais legítimas precisam encerrar a prévia

Uma correção tecnicamente direta seria comparar a prévia automática com a
decisão final por segmento: `captured/merged` exige candidato semanticamente
equivalente; `excluded` com `reason_code` válido não vira pendência; ausência
de decisão ou destino inválido continua `review_required`. Ela requer uma
terceira rodada depois do limite de duas correções e muda a interpretação
operacional do gate semântico, portanto depende de autorização explícita do
owner.

## DECISION REQUIRED

**job_id:** `MSF-R20-GOLD-FASTPATH-002`

**Contexto:** 56 testes e as correções de formato persistido passam, mas o caso
real de v6lu mantém 779 falsos positivos porque exclusões legítimas não são
reconhecidas pela prévia de ledger.

**Por que é material:** uma terceira rodada excede a política de duas correções;
aceitar o estado atual exige 1.580 disposições no receipt e elimina a economia
de tokens; dispensar o Fast Path altera a estratégia de retomada da Wave 004.

**Opção A — recomendada:** autorizar uma terceira e última correção limitada a
FP2-002c, com regressões de exclusão válida, ausência de decisão e destino
captured inválido. Mantém o Fast Path e reduz a carga real.

**Opção B:** aprovar o Fast Path como está e tratar os 779 `low_signal` como
disposições manuais no receipt. Preserva o código atual, mas cria alto custo e
loop operacional.

**Opção C:** encerrar o Fast Path 002 como não aprovado e retomar a Wave 004
com o fluxo anterior, sem usar esse autocheck como gate. Evita nova alteração,
mas não entrega a otimização solicitada.

**Pausado:** reauditoria cega de v6lu. **Trabalhos independentes:** nenhum.

## Decisão do owner — Opção A autorizada

O owner autorizou uma terceira e última correção limitada a FP2-002c. Ela não
altera o objetivo do Fast Path: apenas ensina a prévia semântica a reconhecer
que uma exclusão final já validada encerra aquele segmento. A reauditoria de
v6lu continua pausada e todos os dados reais seguem somente leitura.

### EXECUTION BRIEF conciso — FP2-002c

Corrigir somente a reconciliação entre a prévia do autocheck e o ledger final
por `segment_id`. Para `captured/merged`, manter exigência de candidato com
evidência semanticamente correspondente. Para `excluded`, aceitar apenas
`reason_code` válido e, se `duplicate_of`, referência final válida. Ausência de
decisão, referência inválida ou destino captured/merged sem evidência deve
continuar `review_required`. Criar regressões para exclusão válida, exclusão
inválida e captured sem evidência. Não escrever em episódios, exports, packets,
auditorias ou fingerprints; não criar receipt. Reproduzir a suíte gold completa,
compilar e provar runners das Waves 003/004 em leitura pura. Este é o último
reparo autorizado: qualquer finding material novo volta ao owner.

## Quality gate final — aprovado

O worker concluiu FP2-002c no próprio chat, mas o pytest local terminou com
`PermissionError` no basetemp do job e a notificação `WORKER_EVENT` não foi
enviada. Quando o owner pediu status, o coordenador confirmou o turno final e
executou uma rota materialmente diferente em
`C:\MSF-data\Marketing_Swipe_File\.tmp\msf-r20-fastpath-002-coord-gate-r4`.

O quality gate reproduziu 59 testes, `py_compile`, `git diff --check`, os
runners read-only das Waves 003/004 e os seis hashes de status. Em v6lu, o
autocheck passou de 779 falsos previews para zero: `automatic_ledger_preview=0`,
`high_signals_without_direct_destination=0` e `ledger_semantic_alignment=0`.
Restaram 22 itens heurísticos legítimos para revisão dirigida (21 overlaps e
uma calibração), sem inflação do ledger. Os quatro fingerprints protegidos de
v6lu foram recalculados e permaneceram iguais ao snapshot.

Decisão: `approved`. Fast Path 002 está liberado para uso; a Wave 004 pode
retomar a reauditoria cega do packet já entregue de v6lu. Nenhum dado real,
export, audit ou fingerprint foi escrito durante este épico.
