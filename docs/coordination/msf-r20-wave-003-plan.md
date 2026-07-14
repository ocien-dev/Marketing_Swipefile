# Wave 003 do MSF R20 — épico de três episódios

## Objetivo

Produzir, em uma única delegação, três packets gold cegos e independentes para
auditoria do coordenador. O worker executa os episódios sequencialmente e entrega
um único evento final consolidado, reduzindo reconstrução de contexto e idas e
voltas entre chats.

## Episódios e ordem

| Ordem | Vídeo | Tema | Segmentos raw | Export |
| --- | --- | --- | ---: | --- |
| 1 | `VQJ_Y8E6Hw0` | Copy que gerou R$ 2,5 milhões por dia | 402 | `msf_r20_wave_003_VQJ_Y8E6Hw0` |
| 2 | `icryHLwikKw` | VSLs e US$ 1 bilhão em vendas | 405 | `msf_r20_wave_003_icryHLwikKw` |
| 3 | `4Ad8K3xIX4g` | Criação de três negócios milionários | 497 | `msf_r20_wave_003_4Ad8K3xIX4g` |

O coordenador já executou o preflight raw read-only nos três: todos passaram,
com metadata e transcript compatíveis. `content_segments.json` existe e não
havia diretório gold nem export da Wave 003 antes da delegação.

## Ownership

Somente leitura, por vídeo:

- `C:/MSF-data/Marketing_Swipe_File/raw/youtube/<video_id>/metadata.json`;
- `C:/MSF-data/Marketing_Swipe_File/raw/youtube/<video_id>/transcript_original.json`;
- `C:/MSF-data/Marketing_Swipe_File/processed/<video_id>/content_segments.json`.

Escrita exclusiva do worker:

- `C:/MSF-data/Marketing_Swipe_File/processed/<video_id>/gold_extraction`;
- `C:/MSF-data/Marketing_Swipe_File/exports/msf_r20_wave_003_<video_id>`.

Os três `<video_id>` autorizados são somente `VQJ_Y8E6Hw0`, `icryHLwikKw` e
`4Ad8K3xIX4g`. Código, testes, docs, fila, auditorias, outros episódios,
v2/curated/pool/master, release, consolidação e Supabase estão fora do escopo.

## Stories do épico

| Story | Trabalho |
| --- | --- |
| W3-S01 — preflight em lote | Registrar Git e confirmar runtime, fontes, destinos ausentes e fingerprints dos três episódios antes de qualquer escrita. Falha bloqueia somente o episódio afetado. |
| W3-S02 — extração sequencial | Para cada episódio na ordem, preparar gold, revisar todos os chunks cronologicamente e registrar candidatos atômicos, evidência literal, números, steps, condições, caveats, relações e ledger. Não reler review concluída sem causa concreta. |
| W3-S03 — recall e autocheck | Antes do readiness, fazer recall adversarial global e conferir números materiais, raw literal/ASCII NFKD, faixas, unidades, promo/biografia, fala do entrevistador, encoding e proposições entre chunks. |
| W3-S04 — prontidão com reparo limitado | Rodar um readiness diagnóstico. Se falhar apenas por itens determinísticos do output do episódio, corrigir todo o inventário exato uma vez e rodar um readiness final. Não alterar scripts/contratos. |
| W3-S05 — packet | Com readiness aprovado, rodar um único build com o sufixo explícito do episódio, um validador normal e confirmar o packet de cinco arquivos em `awaiting_external_audit/pending_external`. |
| W3-S06 — entrega consolidada | Enviar um único WORKER_EVENT final com status, artefatos, validações e bloqueios separados para os três episódios. |

## Orçamento de correção interna

O reparo limitado de W3-S04 pode corrigir o inventário completo retornado pelo
readiness quando se limitar a: `steps` ausentes, raw numérico/evidência literal,
tipagem ou faixa numérica, caractere editorial corrompido, referência de
segmento/evidência e integridade de IDs/ledger/relações do próprio episódio.

Erro de fonte, runtime, lock/PermissionError, fingerprint, schema/contrato,
script comum ou causa fora dessas categorias bloqueia somente aquele episódio.
Não há terceiro readiness, segundo build ou segundo validador. Um episódio
bloqueado não impede a continuação dos demais.

## Critérios de aceite por episódio

- todos os chunks têm review integral e IDs únicos;
- recall adversarial completo e todo sinal alto com destino semântico correto;
- números materiais estruturados e sustentados por evidência mínima;
- readiness final, build, validador normal, ledger e calibração passam;
- status `awaiting_external_audit`, `audit_status=pending_external`;
- export explícito contém exatamente os cinco arquivos cegos;
- fingerprints protegidos permanecem iguais.

O worker não audita seu output, não registra auditoria e não deriva
`complete/passed`. Depois do evento final, o coordenador audita cada packet
separadamente e faz quality gates sequenciais.

## Comunicação enxuta

O worker pode manter checkpoints no próprio chat, mas não envia eventos de
progresso ao coordenador. O coordenador encerra o turno após delegar e só retoma
com o WORKER_EVENT final de conclusão, bloqueio consolidado ou decisão material.

## Auditorias iniciais seladas

| Episódio | Parecer | Findings abertos | Focos |
| --- | --- | ---: | --- |
| `VQJ_Y8E6Hw0` | changes_requested | 3 | números, faixa de US$27-US$97 omitida e relações/merge |
| `icryHLwikKw` | changes_requested | 4 | quatro blocos de recall, números, G008 de encerramento/G007 corrompido e relações |
| `4Ad8K3xIX4g` | changes_requested | 4 | números, testes de closes/micro-leads, evidência de G010 e relações |

Os julgamentos estão em `.codex-work/msf-r20-coordinator-audits/<video_id>_audit.json`.
O worker os registra uma única vez e não os edita.

## Remediação consolidada W3-R01 a W3-R05

| Story | Trabalho fechado |
| --- | --- |
| W3-R01 — registrar auditorias | Registrar os três relatórios selados, na ordem dos episódios. Cada relatório permanece `changes_requested`; não derivar complete. |
| W3-R02 — corrigir VQJ | Executar exatamente os required_action de VQJ-001 a VQJ-003: números nos candidatos listados, novo candidato da faixa US$27-US$97 e relações/merge sem ciclos. |
| W3-R03 — corrigir icry | Executar ICRY-001 a ICRY-004: quatro candidatos de recall, números, remover G008/corrigir G007 e relações de hooks. |
| W3-R04 — corrigir 4Ad | Executar 4AD-001 a 4AD-004: números, candidatos de closes e micro-leads, reescrever G010 com 0473-0478 e relações. |
| W3-R05 — rederivar | Por episódio, rodar o novo autocheck de quatro inventários, readiness, build com sufixo Wave 003 e validador normal; entregar três packets pendentes para reauditoria. |

Depois das correções, cada episódio pode usar um readiness diagnóstico e um
reparo final apenas para erros literais/tipagem/relação surgidos dentro do
inventário auditado. Em seguida há no máximo um readiness final, um build e um
validador normal. Um ramo bloqueado não impede os demais. O worker envia somente
um evento final consolidado.

## Retomada W3-R06 após restauração de VQJ

Os três audits já foram registrados. A primeira tentativa de remediação aplicou
em VQJ os números, G024 e as relações, mas detectou uma sobrescrita acidental do
review do chunk 007 antes de qualquer gate. O worker restaurou esse review do
candidate chunk preservado e parou.

O coordenador confirmou em leitura: sete reviews completas, hashes/chunk IDs
coerentes, 24 candidatos únicos G001-G024, G021-G023 no chunk 007, números
auditados e relações parent/child simétricas. A restauração está aprovada.

Na retomada, não registrar auditorias novamente, não restaurar/regravar VQJ e
não repetir correções já aplicadas. Primeiro concluir autocheck, readiness,
build e validador de VQJ; depois executar as remediações ainda pendentes de icry
e 4Ad conforme W3-R03/W3-R04. Um único evento final consolidado permanece como
contrato de entrega.

## Escopo separado W3-R07 — somente icry e 4Ad

VQJ foi rederivado e reaudidado. G024 e a maior parte dos números/relações foram
resolvidos, mas a reauditoria `VQJ_Y8E6Hw0_reaudit_001.json` mantém dois resíduos:
números comparativos de G019 e relação G016→G015. VQJ fica fora de W3-R07 e não
pode ser editado nesta retomada.

W3-R07 contém somente as remediações ainda não iniciadas de `icryHLwikKw` e
`4Ad8K3xIX4g`, cujos audits iniciais já estão registrados. Não registrar audit,
não tocar VQJ e não executar finalização. Cada episódio segue seu required_action,
autocheck, readiness e um build/validador normal. Um evento final único traz os
dois resultados para reauditoria.

## Retomada W3-R08 — persistência em duas fases para ICRY

W3-R07 parou antes de qualquer escrita editorial. Ao tentar criar as relações
de ICRY no mesmo estado em memória usado para montar os novos candidatos, o
worker referenciou `icryHLwikKw-G011` antes de o novo ID existir no mapa e
recebeu `KeyError`. Os oito candidatos originais e os dois episódios foram
preservados; 4Ad não foi iniciado.

A retomada separa deliberadamente criação e relações:

1. criar e persistir G009-G012 nos reviews corretos, ainda sem relações novas;
2. reler os reviews persistidos, confirmar IDs/chunk/input_hash e reconstruir o
   mapa completo de candidatos a partir do disco;
3. somente então adicionar relações simétricas usando o mapa reconstruído e
   persistir apenas os reviews envolvidos;
4. aplicar as demais correções ICRY-002/003, executar autocheck e gates de ICRY;
5. depois processar 4AD-001..004 e seus gates sem compartilhar mapa/estado com
   ICRY.

Uma falha antes da persistência de uma fase não autoriza repetir a mesma fase
no mesmo processo. Falha de ICRY não impede iniciar 4Ad, desde que não exista
risco de persistência compartilhada. VQJ, auditorias, código, testes, docs e
fila permanecem fora do ownership do worker.

## Retomada W3-R09 — helpers compilados e 4Ad primeiro

W3-R08 também parou antes de qualquer escrita: a chamada usada para iniciar a
Fase A de ICRY tinha erro de sintaxe e o processo Python não chegou a abrir. É a
segunda devolução consecutiva sem artefato editorial novo nessa subtask.

Para evitar uma terceira repetição, W3-R09 não usa Python inline nem começa por
ICRY. O worker:

1. processa primeiro 4Ad em estado isolado;
2. cria helpers job-local em
   `.codex-work/worker-jobs/MSF-R20-WAVE-003-W3-R09/`, sem editar scripts do
   produto;
3. cada helper oferece `--check` read-only e `--apply`, é compilado com
   `py_compile`, executa todas as precondições em memória e só grava após o
   check passar;
4. usa helpers separados para 4Ad, ICRY Fase A e ICRY Fase B; a Fase B relê do
   disco e exige G011 no mapa antes de criar relações;
5. preserva os helpers como provenance local ignorado e não repete `--apply`.

O ownership adicional limita-se ao diretório job-local acima. A fila central,
docs, audits, scripts e testes continuam exclusivos do coordenador/read-only.
Se ICRY bloquear depois de 4Ad pronto, o evento final é parcial e preserva o
packet 4Ad para reauditoria.

## Retomada W3-R10 — seis literalidades 4Ad e ICRY isolado

W3-R09 produziu avanço material: o helper de 4Ad compilou, passou `--check` e
foi aplicado uma única vez. G011/G012, G010, números e relações auditadas foram
gravados; o readiness diagnóstico reteve somente seis raws não literais.

O inventário corretivo está fechado:

- G006 número 1: `21st VSL` para `21st VSSL`;
- G009 número 1: `7 million` para `7`, preservando valor/unidade e incluindo o
  segmento adjacente apenas se necessário ao contexto;
- G011 números 0/1/3: `five or six closes`, `four or five leads` e `60 bucks`;
- G012 número 0: `10-second`.

Um helper novo e separado corrige somente esses seis campos `raw` e, quando
necessário, amplia apenas a evidência contextual de G009. Depois roda o
readiness final de 4Ad, um build e um validador normal. O helper W3-R09 aplicado
não pode ser reutilizado.

Em seguida, ICRY continua com helpers A/B separados conforme W3-R09: primeiro
G009-G012 sem relações, depois releitura do disco, mapa reconstruído e demais
correções. O avanço material zera o contador de retornos sem progresso.

## Gate W3-R11 — concluir 4Ad e limpar ICRY

As reauditorias foram seladas antes da leitura de artefatos internos:

- `4Ad8K3xIX4g_reaudit_001.json`: `passed`, zero findings;
- `icryHLwikKw_reaudit_001.json`: `changes_requested`, um finding minor.

4Ad pode apenas registrar a reauditoria aprovada, rederivar `complete/passed` e
rodar o validador com auditoria exigida. Nenhum campo editorial ou packet muda.

ICRY registra a reauditoria `changes_requested` e aplica somente:

- G004: título com `as primeiras 200 palavras` e takeaway com `paragrafos`;
- G007: título com `humanos refinem`;
- G012: takeaway com `orcamento` em ASCII;
- caveats ASCII em G002, G006 e G011, preservando que são resultados/casos
  reportados e não garantias.

Um helper job-local novo compila, passa `--check` read-only e tem um único
`--apply`. Depois ICRY usa um readiness, um build, um validador normal e exporta
packet atualizado ainda em `awaiting_external_audit/pending_external` com um
finding registrado. O coordenador faz nova reauditoria; o worker não aprova
ICRY.

## Gate W3-R12 — concluir ICRY e corrigir resíduos VQJ

`icryHLwikKw_reaudit_002.json` foi selado `passed` com zero findings após a
limpeza de W3-R11. ICRY pode apenas registrar esse relatório, rederivar
`complete/passed` e rodar o validador com auditoria exigida, sem edição.

VQJ registra uma única vez `VQJ_Y8E6Hw0_reaudit_001.json`, ainda
`changes_requested/open_findings=2`, e aplica somente:

- G019: records reportados literais de upsell 2 para `10`, `12`, `15` e faixa
  10-15%; upsell 3 para `five percent` e faixa `five to seven percent`;
- G016 como parent de G015 e G015 como child de G016, de forma simétrica.

Um helper job-local novo compila, passa `--check` read-only e tem um único
`--apply`. Depois VQJ usa um readiness, um build, um validador normal e exporta
packet atualizado ainda pendente dos dois findings registrados. O coordenador
faz a reauditoria final; nenhum worker deriva passed para VQJ nesta etapa.

## Gate W3-R13 — registro final VQJ

`VQJ_Y8E6Hw0_reaudit_002.json` foi selado `passed` com zero findings. O worker
apenas registra esse relatório, rederiva `complete/passed` e roda o validador
com `--require-external-audit`. Não há edição de candidatos, reviews, ledger,
packet, helper, código ou docs.

O gate encerra a Wave 003 quando VQJ tiver 24 IDs, `complete/passed`, zero
findings, packet existente com cinco arquivos e quatro fingerprints iguais.
4Ad e ICRY já estão completos e permanecem read-only.

## Resultado final do épico

Quality gate independente aprovado em 2026-07-11:

| Episódio | IDs | Estado | Findings | Validador final | Fingerprints |
| --- | ---: | --- | ---: | --- | --- |
| `VQJ_Y8E6Hw0` | 24 | `complete/passed` | 0 | `--require-external-audit` pass | 4/4 iguais |
| `icryHLwikKw` | 11 | `complete/passed` | 0 | `--require-external-audit` pass | 4/4 iguais |
| `4Ad8K3xIX4g` | 12 | `complete/passed` | 0 | `--require-external-audit` pass | 4/4 iguais |

Os três relatórios finais têm revisor/thread separado do executor, rota Codex
de reauditoria cega e `open_findings=0`. Cada export contém exatamente os cinco
arquivos do packet. Nenhuma consolidação, Supabase, commit, push ou deploy foi
executado.
