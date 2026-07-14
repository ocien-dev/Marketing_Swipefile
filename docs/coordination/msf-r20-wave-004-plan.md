# Wave 004 do MSF R20 — piloto real do Gold Fast Path

## Objetivo

Processar, em uma única delegação e de forma sequencial, os próximos três
episódios elegíveis da fila VTurb. Esta é a primeira wave real depois da
aprovação do Fast Path e deve produzir três packets cegos independentes com
menos repetição de contexto, sem reduzir a revisão integral, o recall semântico
ou a auditoria independente do coordenador.

## Episódios e ordem

Os episódios foram escolhidos pela menor `episode_priority` ainda elegível em
`input/youtube_urls.csv`, pulando fontes com `transcript_status` diferente de
`available` e episódios gold já concluídos.

| Ordem | Prioridade | Vídeo | Tema | Segmentos raw | Export |
| --- | ---: | --- | --- | ---: | --- |
| 1 | 4 | `yyoGeQp5yzM` | Como a Kiwify foi escalada | 1.142 | `msf_r20_wave_004_yyoGeQp5yzM` |
| 2 | 6 | `8WEvN5T7J0U` | Queima diária e mais de 500 milhões | 844 | `msf_r20_wave_004_8WEvN5T7J0U` |
| 3 | 8 | `v6luZ9KvmOI` | Funil de lucro infinito | 1.784 | `msf_r20_wave_004_v6luZ9KvmOI` |

O coordenador executou `--preflight-raw` somente leitura nos três episódios em
2026-07-13. Metadata e transcript passaram sem erros; `content_segments.json`
existe; os diretórios gold e os exports da Wave 004 ainda não existem.

Manifesto: `docs/coordination/msf-r20-wave-004-manifest.json`.

## Ownership

Leitura autorizada por episódio:

- `C:/MSF-data/Marketing_Swipe_File/raw/youtube/<video_id>/metadata.json`;
- `C:/MSF-data/Marketing_Swipe_File/raw/youtube/<video_id>/transcript_original.json`;
- `C:/MSF-data/Marketing_Swipe_File/processed/<video_id>/content_segments.json`;
- scripts e contratos gold/Fast Path necessários à execução, somente leitura;
- o plano e o manifesto desta wave, somente leitura.

Escrita exclusiva do worker:

- `C:/MSF-data/Marketing_Swipe_File/processed/<video_id>/gold_extraction`;
- `C:/MSF-data/Marketing_Swipe_File/exports/msf_r20_wave_004_<video_id>`;
- `.codex-work/worker-jobs/MSF-R20-WAVE-004/`, apenas para checkpoints,
  métricas e patches declarativos job-local.

Os únicos `<video_id>` autorizados são `yyoGeQp5yzM`, `8WEvN5T7J0U` e
`v6luZ9KvmOI`. O worker não edita código, testes, skills, docs, fila central,
auditorias do coordenador ou qualquer outro episódio.

## Stories do épico

| Story | Trabalho |
| --- | --- |
| W4-S01 — preflight e classificação | Registrar o Git antes da primeira escrita; confirmar runtime, temp do job, fontes, destinos ausentes, fingerprints e ownership. Rodar o manifesto em modo read-only e exigir `new_raw_episode` nos três. Um bloqueio afeta só o episódio correspondente. |
| W4-S02 — preparação Fast Path | Executar o runner aprovado para preparar cada episódio novo e gerar chunks, sinais, calibrações e work orders compactos. Não duplicar transcript em notas ou mensagens. |
| W4-S03 — revisão semântica integral | Na ordem definida, ler todos os chunks e registrar candidatos atômicos com evidência literal, números, steps, condições, caveats, risco, relações e ledger. Reviews válidas por hash são checkpoints retomáveis e não devem ser relidas sem causa concreta. |
| W4-S04 — recall adversarial e autocheck | Fazer releitura global dirigida por sinais altos, números, fronteiras e calibrações. Rodar o autocheck Fast Path e resolver ou justificar numbers, steps, calibrações, encoding, promo/entrevistador, relações, sinais altos e fronteiras. |
| W4-S05 — readiness com reparo fechado | Rodar um readiness diagnóstico por episódio. Se a falha estiver no inventário determinístico autorizado abaixo, criar patch declarativo com asserts, rodar `--check` e um único `--apply`; depois rodar um readiness final. |
| W4-S06 — packet | Para cada episódio pronto, executar um build, um validador normal e exportar exatamente os cinco arquivos cegos. O estado deve ficar `awaiting_external_audit/pending_external`. |
| W4-S07 — entrega consolidada | Enviar um único `WORKER_EVENT` final, com resultado, métricas, artefatos, validações e bloqueios separados por episódio. |

## Reparo interno permitido

Antes do primeiro packet, o reparo fechado pode corrigir somente itens listados
pelo readiness/autocheck do próprio episódio: `steps` ausentes, raw numérico e
evidência literal, tipagem/faixa numérica, encoding editorial, referência de
segmento, IDs, ledger e relações. O patch precisa ser declarativo, validar o
estado anterior, passar em `--check` e ter um único `--apply`.

Fonte ausente ou incompatível, runtime, lock/PermissionError, fingerprint,
schema/contrato, script comum ou erro fora dessas categorias bloqueia apenas o
episódio afetado. Não há terceiro readiness, segundo build ou segundo
validador. Um ramo bloqueado não impede os outros dois.

## Critérios de aceite por episódio

- preflight e rota `new_raw_episode` confirmados;
- todos os chunks têm review integral, hashes coerentes e IDs únicos;
- recall adversarial concluído e sinais altos com destino semanticamente útil;
- números materiais, steps, caveats e relações sustentados por evidência;
- autocheck sem pendência injustificada e readiness final `ready`;
- build e validador normal passam sem erros;
- status `awaiting_external_audit` e auditoria `pending_external`;
- export contém exatamente `packet_manifest.json`, `transcript_clean.json`,
  `insights_exhaustive.json`, `high_signal_coverage_ledger.json` e
  `calibration_tests.json`;
- fingerprints protegidos permanecem iguais;
- métricas Fast Path por episódio são registradas, incluindo tamanho compacto
  e checkpoints reaproveitados, sem alegar economia que não foi medida.

O worker não audita o próprio output, não registra auditoria e não deriva
`complete/passed`. O próximo gate é a auditoria cega sequencial do coordenador.

## Fora de escopo

- código, testes, scripts comuns, schemas, prompts, skills e contratos;
- auditorias seladas ou decisões do coordenador;
- episódios fora da lista;
- v2, curated, pool, master, consolidação gold e Supabase;
- commit, push, deploy ou qualquer release;
- recuperação de transcript por navegador ou serviço externo.

## Comunicação e parada

O worker mantém checkpoints no próprio chat, mas envia ao coordenador somente
um evento final `completed`, `blocked` ou `decision_required`. O coordenador
encerra o turno após delegar e não acompanha a execução. A mesma ação não deve
ser repetida pela quarta vez após três retornos sem progresso; uma ação única
sem avanço por 30 minutos deve ser substituída por caminho materialmente
diferente e seguro.

## EXECUTION BRIEF conciso

Executar agora a primeira wave real do Fast Path nos três episódios elegíveis
listados. Preparar e revisar cada um sequencialmente, fazer recall/autocheck,
usar no máximo um reparo declarativo fechado, gerar um packet cego de cinco
arquivos e preservar fingerprints. Alterar somente os três diretórios gold,
seus três exports e o diretório job-local. Não alterar código, docs, fila,
auditorias, outros episódios, bases consolidadas ou release. Parar o ramo em
caso de fonte, permissão, fingerprint, contrato ou erro fora do reparo
autorizado; continuar os demais. Entregar um único evento final. Depois, o
coordenador fará auditoria cega independente de cada packet.

## Retomada W4-R01 — checkpoint semântico após o chunk 014

O primeiro ciclo preparou corretamente os três episódios e parou antes de
qualquer readiness, build, validador ou packet. A conferência independente do
coordenador confirmou:

- `yyoGeQp5yzM` está em `awaiting_semantic_review/not_started`, com reviews
  completas e hashes presentes nos chunks 001–014;
- o estado real contém 34 candidatos únicos, apesar de o evento resumido ter
  informado 32; a contagem correta do disco e do chat do worker é 34;
- o runner read-only classifica o episódio como `resumable_incomplete_gold`,
  sem chunks stale ou inconsistentes, e lista apenas 015–021 como pendentes;
- `8WEvN5T7J0U` e `v6luZ9KvmOI` também estão retomáveis, preparados e sem
  reviews, build ou export;
- os três exports permanecem ausentes.

W4-R01 preserva integralmente os reviews 001–014 e não repete preparação.
Primeiro revisa 015–021 de `yyoGeQp5yzM`, faz recall global, autocheck e seus
gates até packet. Depois executa as stories já planejadas para `8WEvN5T7J0U` e
`v6luZ9KvmOI`, na ordem, sem misturar estados. O ownership, reparo interno,
critérios e proibições não mudam. A entrega continua sendo um único evento
final consolidado.

## Retomada W4-R02 — remediação auditada de yyo e conclusão dos pendentes

W4-R01 entregou um packet cego válido de `yyoGeQp5yzM`, iniciou
`8WEvN5T7J0U` com o chunk 001 persistido e manteve `v6luZ9KvmOI` preparado. A
auditoria independente inicial do coordenador foi selada em
`.codex-work/msf-r20-coordinator-audits/yyoGeQp5yzM_audit.json` como
`changes_requested`, com quatro findings abertos:

1. comparação quantitativa de captura de valor por cliente nos segmentos
   0121–0123;
2. mudança temporal do diferencial conforme gap e competição em 0327–0330;
3. arquitetura de reporte/span gerencial em 0783–0789;
4. script com IA para recuperar casos análogos em 0996–1003.

O worker deve primeiro registrar esse audit sem alterar o julgamento e aplicar
somente as correções exigidas, com candidatos atômicos ou ampliações que não
diluam candidatos existentes, números/caveats sustentados e ledger coerente.
Depois executa autocheck, readiness, um build, um validador normal e sincroniza
o packet de yyo para nova auditoria; o estado permanece
`awaiting_external_audit/pending_external`, nunca `complete/passed`.

Em seguida, preserva o review válido do chunk 001 de `8WEvN5T7J0U`, retoma no
chunk 002 e conclui todos os seus gates. Por último, revisa integralmente
`v6luZ9KvmOI` e conclui seus gates. Nenhum packet parcial pode ser gerado. Um
ramo bloqueado não impede os demais episódios independentes. O ownership e as
proibições do épico original permanecem inalterados.

### EXECUTION BRIEF conciso W4-R02

Corrigir as quatro lacunas auditadas de yyo e rederivar seu packet; depois
concluir sequencialmente 8WE a partir do chunk 002 e v6lu desde o início da
revisão. Alterar somente os três diretórios gold, seus exports e o diretório
job-local. Preservar reviews válidos, usar autocheck/readiness antes de um único
build e validador por episódio e manter fingerprints protegidos. Não alterar
o audit selado, código, testes, docs, fila, outros episódios, bases
consolidadas, Supabase ou release. Parar o ramo em lock, PermissionError,
fingerprint, fonte/contrato incompatível ou erro fora do reparo permitido;
continuar os outros ramos seguros. Entregar um único evento final separado por
episódio para nova auditoria do coordenador.

## Retomada W4-R03 — envelope de auditoria compatível

W4-R02 parou o ramo yyo antes de qualquer edição porque o registrador atual
exige `finding.segment_range` como array numérico `[inicio, fim]`, enquanto a
auditoria original selada usava uma descrição textual com IDs completos. O
julgamento original permanece imutável. O coordenador criou o envelope
`.codex-work/msf-r20-coordinator-audits/yyoGeQp5yzM_audit_envelope_001.json`,
que conserva status, quatro findings, evidências e ações, alterando apenas a
representação contratual dos ranges para os clean indexes `[120,122]`,
`[326,329]`, `[782,788]` e `[995,1002]`. O validador oficial do contrato
retornou zero erros.

No ramo 8WE, os chunks 001 e 002 estão completos, com hashes presentes, seis
IDs únicos e nenhum chunk stale ou inconsistente; a retomada começa no chunk
003. v6lu continua preparado e integralmente pendente. W4-R03 registra uma vez
o novo envelope de yyo, aplica somente YYO-001..004 e conclui seus gates;
depois conclui 8WE e v6lu conforme W4-R02. O ownership, os critérios e as
proibições não mudam.

### EXECUTION BRIEF conciso W4-R03

Usar somente o novo envelope compatível para registrar os quatro findings de
yyo, sem editar o audit original nem o envelope. Remediar os quatro itens e
rederivar o packet. Preservar os reviews 001–002 de 8WE, retomar no 003 e
concluir o episódio; depois concluir v6lu. Alterar somente os três diretórios
gold, exports e o diretório job-local. Não gerar packet parcial nem tocar
código, testes, docs, fila, bases consolidadas, Supabase ou release. Entregar
um único evento final separado por episódio para o quality gate do coordenador.

## Retomada W4-R04 — inserção sem substituir reviews existentes

W4-R03 registrou corretamente o envelope de yyo, mas o recorder recusou o
payload antes da escrita. A inspeção do coordenador confirmou que a relação
`G034↔G035` não está dangling: ela é simétrica nos reviews 014/015 e nos
derivados atuais. O erro surgiu porque o payload de remediação continha somente
o novo `G053` para o chunk 015; como o recorder substitui o review completo do
chunk, a simulação removeria `G035` e tornaria a relação inválida. A mesma rota
também descartaria candidatos existentes dos chunks 003, 007 e 020.

Portanto, é proibido remover ou alterar `G034↔G035` e é proibido reaplicar o
payload pelo recorder. W4-R04 deve usar `gold_review_patch` para inserir
`G051–G054` nos quatro reviews existentes, preservando integralmente seus
candidatos atuais. O manifesto precisa ter assertions completas:

- chunk 003: `G005,G006,G007`;
- chunk 007: `G014,G015,G016`;
- chunk 015: `G035`;
- chunk 020: `G046,G047,G048`;

Cada assertion também inclui `chunk_id` e `input_hash` atuais. Os candidatos
inseridos devem estar no formato final validado, com evidência derivada do
transcript. Em `G054`, `takeaway_applicavel` deve permanecer ASCII e o número
`2 minutos` deve usar `role=other`. O fluxo é: gerar manifesto job-local,
compilar eventual helper job-local, rodar `--check`, confirmar zero escrita e
um único `--apply`. Depois, verificar que os candidatos anteriores e a relação
G034/G035 são byte/semanticamente preservados antes dos gates yyo.

Com yyo rederivado, o worker retoma 8WE no chunk 003 e depois v6lu, mantendo o
restante do plano. Esse caminho materialmente diferente evita perda silenciosa
de candidatos e usa a inserção transacional criada pelo Fast Path.

### EXECUTION BRIEF conciso W4-R04

Não remover a relação G034/G035 nem usar o recorder de substituição. Inserir
G051–G054 com patch declarativo e assertions completas nos quatro reviews,
corrigindo apenas o ASCII e o role de G054; executar check e um apply. Confirmar
que todos os candidatos anteriores continuam iguais, rederivar yyo e então
concluir 8WE desde o chunk 003 e v6lu. Alterar somente gold/exports e o
diretório job-local; não tocar auditorias, código, docs, fila, bases
consolidadas, Supabase ou release. Entregar um único evento final.

## Retomada W4-R05 — concluir yyo e os dois episódios restantes

O packet remediado de `yyoGeQp5yzM` foi reauditado cegamente pelo coordenador.
Os quatro findings estão resolvidos em G051–G054; o relatório selado
`.codex-work/msf-r20-coordinator-audits/yyoGeQp5yzM_reaudit_001.json` passou
com `open_findings=0` e validou contra o contrato atual sem erros. A conferência
independente também confirmou 54 IDs, ledger dos quatro blocos, relações
simétricas, calibração pass, números literais, validador normal aprovado e
fingerprints protegidos iguais.

W4-R05 primeiro registra uma vez a reauditoria, executa um build derivado e um
validador com `--require-external-audit`; yyo deve terminar
`complete/passed/open_findings=0` sem edição editorial. Depois preserva os
reviews 001–002 de 8WE, retoma no chunk 003 e conclui 003–014, recall,
autocheck, readiness, build, validador e packet. Por último, conclui v6lu dos
chunks 001–031 pelos mesmos gates. Nenhum packet parcial é permitido.

### EXECUTION BRIEF conciso W4-R05

Registrar a reauditoria aprovada e derivar yyo para complete, sem alterar seus
candidatos. Retomar 8WE no chunk 003 e concluir seu packet; depois revisar e
concluir v6lu. Preservar reviews válidos e usar os limites de readiness/build
do plano. Alterar somente os três diretórios gold, seus exports e o diretório
job-local. Não tocar audit selado, código, testes, docs, fila, outros episódios,
bases consolidadas, Supabase ou release. Entregar um único evento final para o
quality gate da Wave 004.

## Retomada W4-R06 — somente 8WE e v6lu

O coordenador reproduziu o gate final de `yyoGeQp5yzM`: validador com auditoria
passou, estado é `complete/passed`, há 54 IDs únicos, zero finding aberto,
packet com cinco arquivos e fingerprints protegidos iguais. O runner agora
classifica yyo como `protected_complete_read_only`; nenhum trabalho futuro da
Wave 004 pode escrever nesse episódio.

`8WEvN5T7J0U` possui reviews completos e hashes válidos nos chunks 001–004,
com G001–G014 únicos. O runner não encontrou chunk stale ou inconsistente e
lista 005–014 como pendentes. `v6luZ9KvmOI` permanece preparado, com 001–031
pendentes. W4-R06 preserva yyo em leitura, retoma 8WE no chunk 005 e conclui
seus gates; depois revisa v6lu desde o chunk 001 e conclui seus gates. Packets
parciais continuam proibidos.

### EXECUTION BRIEF conciso W4-R06

Não tocar yyo. Preservar reviews 001–004 de 8WE, concluir 005–014, recall,
autocheck, readiness, build, validador e packet. Depois revisar v6lu 001–031 e
executar os mesmos gates. Alterar somente gold/exports de 8WE e v6lu e o
diretório job-local. Não tocar audits, código, testes, docs, fila, outros
episódios, bases consolidadas, Supabase ou release. Entregar um único evento
final com os dois resultados para auditoria independente.

## Retomada W4-R07 — 8WE a partir do chunk 007

W4-R06 preservou yyo e adicionou reviews completos nos chunks 005–006 de 8WE.
O coordenador confirmou seis reviews com hashes, 20 IDs únicos e nenhum chunk
stale ou inconsistente. A fronteira exata é 007; os chunks 007–014 permanecem
pendentes. v6lu continua preparado e não deve ser aberto até o packet integral
de 8WE.

W4-R07 preserva 001–006, conclui 007–014, recall/autocheck e todos os gates de
8WE. Somente depois de exportar o packet integral pode iniciar v6lu no chunk
001. Yyo continua protegido e read-only. Ownership, limites de reparo e
proibições permanecem iguais.

### EXECUTION BRIEF conciso W4-R07

Preservar os seis reviews e 20 candidatos atuais de 8WE; concluir 007–014 e
seus gates até packet integral. Só então iniciar v6lu 001–031. Não tocar yyo,
audits, código, testes, docs, fila, bases consolidadas, Supabase ou release.
Alterar apenas gold/exports de 8WE/v6lu e o diretório job-local. Entregar um
único evento final.

## Retomada W4-R08 — faixa final de 8WE

W4-R07 concluiu os chunks 007–008. O coordenador confirmou oito reviews
integrais com hashes, 25 IDs únicos, zero duplicidade e nenhum chunk stale ou
inconsistente. A faixa final pendente é 009–014. W4-R08 preserva 001–008,
conclui 009–014 e executa recall, autocheck, readiness, build, validador e
packet integral de 8WE. v6lu só pode começar depois desse packet. Yyo permanece
protegido. Todos os demais critérios e limites do plano continuam válidos.

### EXECUTION BRIEF conciso W4-R08

Preservar oito reviews e 25 IDs de 8WE; concluir 009–014 e todos os gates até o
packet integral. Só depois iniciar v6lu. Alterar apenas gold/exports de
8WE/v6lu e o diretório job-local. Não tocar yyo, audits, código, testes, docs,
fila, bases consolidadas, Supabase ou release. Entregar um único evento final.

## Retomada W4-R09 — fechar e auditar 8WE antes de v6lu

W4-R08 concluiu 009–010. O coordenador confirmou dez reviews integrais com
hashes, 33 IDs únicos e nenhuma inconsistência; restam 011–014. Para reduzir
troca de contexto e manter o gate por episódio, W4-R09 fica limitado a concluir
8WE, executar recall/autocheck e gerar seu packet integral. v6lu permanece
preparado e não será aberto nesta retomada; ele será delegado depois da
auditoria de 8WE. Yyo continua protegido.

### EXECUTION BRIEF conciso W4-R09

Preservar os dez reviews e 33 IDs de 8WE; concluir 011–014, recall, autocheck,
readiness, build, validador e packet integral. Não iniciar v6lu e não tocar
yyo. Alterar apenas gold/export de 8WE e o diretório job-local. Audits, código,
testes, docs, fila, bases consolidadas, Supabase e release ficam fora de escopo.
Entregar um único evento final para auditoria cega de 8WE.

## Retomada W4-R10 — chunk 014 e gates de 8WE

W4-R09 concluiu 011–013. O coordenador confirmou 13 reviews válidos, 39 IDs
únicos e somente o chunk 014 pendente, sem stale ou inconsistência. W4-R10
preserva 001–013, revisa 014 e executa recall, autocheck, readiness, eventual
reparo fechado, build, validador normal e packet integral. Yyo e v6lu continuam
somente leitura. O próximo gate é a auditoria cega do packet de 8WE.

### EXECUTION BRIEF conciso W4-R10

Preservar 13 reviews e 39 IDs; revisar apenas o chunk 014 e concluir todos os
gates de 8WE até packet integral. Não iniciar v6lu nem tocar yyo. Alterar apenas
gold/export de 8WE e o diretório job-local. Nenhum packet parcial, alteração de
audit/código/docs/fila, consolidação, Supabase ou release. Entregar um único
evento final.

## Remediação W4-R11 — auditoria cega inicial de 8WE

W4-R10 entregou o packet integral de `8WEvN5T7J0U` com 40 candidatos, validação
normal aprovada e fingerprints protegidos iguais. O coordenador auditou somente
os cinco arquivos cegos e selou `changes_requested` com dez findings em
`.codex-work/msf-r20-coordinator-audits/8WEvN5T7J0U_audit.json`.

W4-R11 registra esse audit uma única vez e aplica somente as correções fechadas:
remover a duplicata G001/G033; capturar os procedimentos e casos omitidos;
completar números; registrar relações; recalcular calibrações por unidade
semântica; e corrigir três grafias internas. O patch deve ser transacional,
validado primeiro em leitura e aplicado uma única vez. Depois executa autocheck,
readiness, um build, validador normal e reexporta o packet para reauditoria.
`yyoGeQp5yzM` e `v6luZ9KvmOI` permanecem somente leitura.

### EXECUTION BRIEF conciso W4-R11

Registrar o audit selado sem editá-lo; corrigir exclusivamente seus dez findings
no gold de 8WE; reexecutar autocheck, readiness, build, validador e packet cego.
Alterar somente gold/export de 8WE e o diretório job-local W4-R11. Não tocar yyo,
v6lu, código, testes, docs, fila, bases consolidadas, Supabase ou release.
Entregar um único evento final para reauditoria independente.

## Remediação W4-R12 — redirecionamento semântico das calibrações de 8WE

W4-R11 aplicou o patch transacional e rederivou o packet com 42 candidatos,
validação normal aprovada e fingerprints iguais. A revisão do coordenador
confirmou que as demais correções estão materialmente presentes, mas o finding
`MSF-R20-8WE-009` continua aberto: os targets 0001, 0003, 0012 e 0568 ainda são
`fail` independentes.

W4-R12 é a segunda e última rodada corretiva deste audit. Um helper job-local
edita somente `calibration_tests.json`: deduplica 0001/0003 no target já coberto
por G040, redireciona 0012 para a evidência de G033 e 0568 para a evidência de
G029, preservando provenance nos campos de deduplicação. Depois executa uma
readiness, um build, validador normal e packet. Os 42 candidatos e todos os
artefatos não relacionados à calibração permanecem imutáveis.

### EXECUTION BRIEF conciso W4-R12

Corrigir apenas as quatro calibrações por helper com check e apply único;
rederivar readiness, build, validador e packet. Não registrar ou editar audit,
não alterar candidatos, ledger, reviews, yyo, v6lu, código, testes, docs, fila,
bases consolidadas, Supabase ou release. Entregar um único evento final para
reauditoria.

## Contorno W4-R13 — aplicação por runtime global

O helper W4-R12 compilou e passou em `--check`, mas seu único `--apply` no
`.venv` ficou 30 minutos sem saída e foi interrompido. A conferência posterior
provou hash e mtime inalterados e ausência de receipt. O coordenador executou o
mesmo `--check` com o Python global confiável e obteve em 1,9 segundo o resultado
esperado de dez targets e hash final
`77E7F5DCF92A54381F7A18C62422536BAE0D458DE977D2C36E195D6BBA45E1B3`.

W4-R13 não repete o comando travado: usa o runtime global, com preflight de
acesso exclusivo ao arquivo, um único `--apply` e limite de dois minutos. Se
passar, executa uma readiness, um build, validador normal e packet. Se travar ou
qualquer precondição divergir, interrompe sem segunda tentativa.

### EXECUTION BRIEF conciso W4-R13

Usar o helper existente e imutável com o Python global em um único apply de até
dois minutos; confirmar o hash final esperado e então executar readiness, build,
validador e packet. Não alterar qualquer outro dado, audit, candidato, ledger,
review, código, docs, yyo ou v6lu. Sem segunda aplicação ou fallback no mesmo
turno.

## Continuação W4-R14 — gates após divergência apenas de formatação

O apply global de W4-R13 concluiu em 6,3 segundos e gravou os dez targets
planejados. O hash físico divergiu porque a escrita em modo texto no Windows
converteu as 252 quebras LF para CRLF. A verificação independente do coordenador
provou que o arquivo contém somente CRLF e que sua normalização para LF produz
exatamente o hash previsto pelo helper e pelo receipt:
`77E7F5DCF92A54381F7A18C62422536BAE0D458DE977D2C36E195D6BBA45E1B3`.
O hash físico CRLF é
`EA3144419DE9A2B2A475D2F772BA69B96FBB357DEA57B67B97240AD4101FDB74`.

Não há divergência semântica a corrigir nem restauração a fazer. W4-R14 não
autoriza nova escrita corretiva, execução do helper ou normalização. Ele apenas
confirma o inventário semântico atual e executa uma readiness, um build, um
validador normal e uma exportação do packet. O build pode rederivar os campos de
cobertura; a aceitação compara o objeto semântico, não o estilo de newline.

### EXECUTION BRIEF conciso W4-R14

Sem editar ou reaplicar qualquer dado, confirmar os dez targets e a provenance
dos quatro redirecionamentos; executar readiness, build, validador normal e
packet uma vez. Preservar os 42 candidatos, reviews, ledger e audit, além de yyo
e v6lu. Parar em qualquer erro sem fallback de escrita. Entregar um único evento
final para reauditoria independente do coordenador.

## Fechamento W4-R15 — registro da reauditoria aprovada de 8WE

W4-R14 rederivou o packet com 42 candidatos, dez calibrações semanticamente
distintas, validador normal aprovado e fingerprints 4/4. O coordenador auditou
somente os cinco arquivos cegos e selou
`.codex-work/msf-r20-coordinator-audits/8WEvN5T7J0U_reaudit_001.json` como
`passed/open_findings=0`; os dez findings anteriores estão `resolved` e o
contrato oficial do relatório retornou zero erros para o executor separado.

W4-R15 não contém correção editorial. O worker registra o relatório selado uma
única vez, executa um build para derivar `complete` e um validador com
`--require-external-audit`. Candidatos, reviews, ledger, calibrações, packet,
yyo e v6lu permanecem sem edição.

### EXECUTION BRIEF conciso W4-R15

Registrar exatamente o audit aprovado e imutável, executar um build e um
validador com auditoria exigida, e provar `complete/passed/open=0`, 42 IDs,
dez calibrações, packet com cinco arquivos e fingerprints 4/4. Sem qualquer
edição editorial, helper, código, docs, release, consolidação ou Supabase.

## Continuação W4-R16 — episódio integral v6lu

O quality gate final de 8WE passou: `complete/passed/open=0`, 42 IDs únicos,
dez calibrações distintas, relatório derivado idêntico à reauditoria selada,
revisor separado, validador com auditoria exigida aprovado, packet com cinco
arquivos e fingerprints 4/4. Yyo e 8WE são protegidos e ficam somente leitura.

O runner Fast Path classifica `v6luZ9KvmOI` como
`resumable_incomplete_gold`, com 31 chunks pendentes, zero stale e zero
inconsistente. W4-R16 executa o episódio inteiro como um único subjob: revisa
001–031 pelos work orders compactos, faz recall adversarial e os quatro
inventários do autocheck, usa no máximo um readiness diagnóstico e um reparo
fechado do inventário retornado, e então executa readiness final, um build, um
validador normal e um packet cego.

Checkpoints job-local são permitidos em fronteiras seguras, mas não geram
eventos de progresso ao coordenador e não autorizam packet parcial. O worker
envia um único evento final quando o packet integral estiver pronto ou quando
houver bloqueio técnico/material real.

### EXECUTION BRIEF conciso W4-R16

Concluir todos os 31 reviews de v6lu, recall/autocheck e gates, com correção
interna limitada ao inventário exato da readiness e um único packet cego.
Alterar somente gold/export/job-local de v6lu. Não tocar yyo, 8WE, código,
testes, docs, fila, auditorias, bases consolidadas, Supabase ou release.

## Continuação W4-R17 — lotes compactos 003–010 de v6lu

W4-R16 confirmou o preflight e persistiu reviews integrais 001–002, com três
IDs únicos. A interrupção ocorreu em fronteira segura, sem erro técnico e sem
packet parcial. O coordenador confirmou os dois arquivos, seus hashes e o
estado resumível: 003–031 pendentes, zero stale e zero inconsistente.

Para reduzir o custo de superfície, W4-R17 não volta a delegar o episódio
inteiro nesta rodada. Ele lê 003–010 usando os work orders compactos, monta os
reviews sem narração intermediária e faz somente duas persistências: um batch
atômico 003–006 e outro 007–010. Os reviews 001–002 são imutáveis. Readiness,
recall global, build, validador e packet ficam proibidos até 31/31.

### EXECUTION BRIEF conciso W4-R17

Revisar 003–010 em dois batches atômicos de quatro chunks, preservar 001–002 e
entregar checkpoint íntegro na fronteira 011. Não executar gates, packet,
auditoria ou outro episódio; yyo e 8WE permanecem protegidos.

## Continuação W4-R18 — lotes compactos 011–018 de v6lu

O padrão enxuto de W4-R17 funcionou: 003–010 foram revisados e persistidos em
dois batches atômicos, produzindo reviews 001–010 íntegros e 16 IDs únicos. O
chunk 005 foi corretamente registrado como zero-insight. Não houve gate ou
packet, e o runner lista 011–031 pendentes sem stale/inconsistência.

W4-R18 repete o mesmo desenho: batch 011–014 e batch 015–018, ambos atômicos,
com narração mínima. Reviews 001–010 são imutáveis. Gates e recall global
continuam reservados para depois de 31/31.

### EXECUTION BRIEF conciso W4-R18

Revisar 011–018 em dois batches atômicos de quatro chunks, preservar 001–010 e
entregar checkpoint íntegro na fronteira 019. Não executar gates, packet,
auditoria ou outro episódio; yyo e 8WE permanecem protegidos.

## Continuação W4-R19 — lotes compactos 019–026 de v6lu

W4-R18 concluiu 011–018 em dois batches atômicos. Há 18 reviews completos e
26 IDs únicos. O chunk 018 é zero-insight isoladamente, mas termina com uma
proposição parcial que precisa ser lida junto do início de 019.

W4-R19 revisa 019–022 e 023–026 em dois batches atômicos. Antes de fechar o
review 019, relê apenas a fronteira final de 018 e captura a proposição completa
em 019, com evidência dos dois lados, se ela tiver valor semântico. O review 018
não é regravado. Gates e recall global permanecem proibidos.

### EXECUTION BRIEF conciso W4-R19

Revisar 019–026 em dois batches de quatro, resolver explicitamente 018/019 sem
alterar o review 018 e entregar checkpoint na fronteira 027. Preservar 001–018,
yyo e 8WE; não executar gates, packet, auditoria ou outro episódio.

## Correção W4-R20 — payload G027 e retomada 019–026

O recorder rejeitou o Batch A antes de qualquer escrita. G027 continha o tema
livre `content_strategy` no array canônico e o raw `uma live por semana`, que
parafraseava a evidência em vez de copiá-la. O coordenador confirmou nos
segmentos 1040 e 1091 a forma literal `pelo menos uma live na semana` e definiu
`creative_strategy` como tema canônico coerente, ao lado de `audience_market`.

W4-R20 muda somente esses dois campos no payload job-local; nenhum outro campo
de G027 ou dos demais reviews pode mudar. Depois de validar, faz uma única nova
chamada atômica para 019–022. Batch B 023–026 só começa se Batch A persistir com
sucesso. Gates e packet continuam proibidos.

### EXECUTION BRIEF conciso W4-R20

Trocar apenas `content_strategy` por `creative_strategy` e o raw por `pelo
menos uma live na semana`; persistir 019–022 uma vez e, se passar, concluir
023–026. Preservar 001–018, yyo e 8WE; sem gates, packet ou auditoria.

## Fechamento W4-R21 — chunks 027–031, recall e packet de v6lu

W4-R20 aplicou exatamente as duas correções autorizadas e persistiu 019–026 em
dois batches atômicos. Há 26 reviews completos, 35 IDs únicos e apenas 027–031
pendentes. G027 usa temas canônicos, raw literal e evidência de 1040/1091. O
runner não encontra stale/inconsistência. O snapshot protegido existe no data
root e está 4/4 igual.

W4-R21 fecha 027–031 em um batch atômico e então executa a primeira releitura
global do episódio: recall adversarial e os quatro inventários do autocheck.
Uma correção atômica pode tratar somente o inventário fechado dessa revisão.
Depois, uma readiness diagnóstica pode produzir um inventário determinístico
adicional; somente esse inventário pode ser reparado antes da readiness final.
Com `ready`, executa um build, validador normal e o packet automático do build.

Não existe packet parcial. Yyo e 8WE são protegidos. O worker não registra
auditoria nem decide `passed/complete`; o próximo gate é a auditoria cega do
coordenador.

### EXECUTION BRIEF conciso W4-R21

Persistir 027–031, fechar recall/autocheck global, reparar apenas inventários
fechados, passar readiness/build/validador e gerar um packet de cinco arquivos.
Preservar yyo, 8WE, fontes protegidas, código, docs e auditorias.

## Remediação W4-R22 — seis findings cegos de v6lu

W4-R21 concluiu os 31 reviews e produziu um packet determinístico com 39
candidatos. O coordenador auditou somente os cinco arquivos cegos e selou
`v6luZ9KvmOI_audit.json` como `changes_requested/open_findings=6`. O contrato
oficial do audit passou sem erros. Depois do selo, o validador normal passou e
os quatro fingerprints protegidos foram confirmados iguais.

W4-R22 registra o audit selado uma vez e corrige somente seu inventário:
normalização de G003; números materiais e roles; destinação do bloco econômico
0835–0853; recall das continuações 1275–1721; cobertura semântica das
calibrações G027/G038; e relações do cluster G022/G024/G025. Um único patch
transacional declarativo deve aplicar candidatos, ledger, números, relações e
calibrações em conjunto, com `--check` read-only e uma aplicação. Candidatos
novos são permitidos apenas quando necessários para as proposições exigidas
pelo finding de recall.

Depois do patch, o worker faz autocheck focal, readiness final, um build e um
validador normal. O episódio deve continuar
`awaiting_external_audit/pending_external`, com os seis findings registrados;
o worker não resolve findings nem decide `passed/complete`. O build sincroniza
o packet de cinco arquivos para reauditoria independente.

### EXECUTION BRIEF conciso W4-R22

Registrar o audit selado e corrigir exatamente os seis findings de v6lu em um
patch transacional; passar readiness, build e validador normal e devolver um
packet novo ainda pendente. Alterar somente gold/export/job-local de v6lu.
Preservar yyo, 8WE, audit selado, código, testes, docs, fila, fontes, bases
consolidadas, Supabase e release.

## Pausa de processo após W4-R22

O evento `MSF-R20-WAVE-004-023` entregou o packet remediado de `v6luZ9KvmOI`
para reauditoria. Antes de o coordenador concluir esse gate, o owner determinou
que a lentidão ponta a ponta fosse corrigida.

A Wave 004 fica em `awaiting_coord_review`, sem nova edição de episódio. Yyo e
8WE continuam protegidos; o packet atual de v6lu permanece intacto. A
dependência temporária é `MSF-R20-GOLD-FASTPATH-002`, documentada em
`docs/coordination/msf-r20-gold-fastpath-002-plan.md`. Depois do quality gate
desse épico, o coordenador retomará a reauditoria de v6lu sem repetir a
remediação W4-R22.

## Remediação W4-R23 — dois resíduos da reauditoria de v6lu

O Fast Path 002 passou no quality gate independente. Na reauditoria do novo
packet de `v6luZ9KvmOI`, o coordenador encontrou dois resíduos e selou
`v6luZ9KvmOI_reaudit_001.json` como `changes_requested/open_findings=2`:

1. G014 registra `150 a 200 alunos` com unidade estruturada `leads`, e G024
   registra a conversão de `10 a 15%` com role `other`.
2. G041 afirma que testes indiscriminados quase levaram a operação ao prejuízo,
   mas sua evidência mínima não inclui os segmentos 1697–1702, que sustentam
   essa parte da proposição.

W4-R23 registra o audit selado uma vez e aplica um único patch declarativo com
asserts. O patch muda apenas: a unidade do número de G014 para uma unidade
compatível com alunos; o role da conversão de G024 para `result`; e a evidência
de G041 para incluir 1697–1702, destinando a G041 os sinais de ledger existentes
em 1698–1701. O texto e os demais campos dos candidatos permanecem iguais.

Depois do patch, o worker usa o Fast Path atual: autocheck focal, receipt
semântico corrente quando exigido, readiness, um build e o validador normal. O
novo packet continua `awaiting_external_audit/pending_external`, com os dois
findings abertos até a próxima reauditoria do coordenador. Yyo e 8WE ficam
protegidos e somente leitura.

### EXECUTION BRIEF conciso W4-R23

Registrar a reauditoria selada e corrigir somente a unidade de G014, o role de
G024 e o suporte/ledger de G041; passar pelo Fast Path e devolver novo packet de
v6lu ainda pendente. Alterar apenas gold/export/job-local de v6lu. Preservar
yyo, 8WE, código, testes, docs, fila, fontes, fingerprints e bases consolidadas.

## Correção de contrato W4-R24 — ledger derivado de G041

W4-R23 foi bloqueado antes da escrita. A verificação posterior confirmou que
os registros 1698–1701 existem no `high_signal_coverage_ledger.json` derivado,
mas não em `manual_reviews/*/ledger_decisions`. Isso é o comportamento canônico:
o builder recalcula o ledger como `captured` quando um segmento de sinal passa a
integrar a evidência de um candidato. Portanto, criar decisões manuais para
esses quatro registros seria redundante e poderia conflitar com o ledger final.

W4-R24 não registra novamente a auditoria e não altera `ledger_decisions`.
Ele aplica uma única vez o patch previamente delimitado: unidade de G014, role
de G024 e citações verbatim 1697–1702 em G041. Depois do build, valida que os
registros derivados 1698–1701 estão `captured` para G041. Esse é o caminho
materialmente diferente para encerrar o bloqueio, sem ampliar o escopo editorial.

### EXECUTION BRIEF conciso W4-R24

Não repetir o registro de auditoria nem criar ledger manual. Corrigir os três
campos autorizados e deixar o builder derivar a captura de G041; validar
1698–1701 como `captured` e devolver packet novo ainda pendente.

## Fechamento W4-R25 — registrar reauditoria aprovada de v6lu

W4-R24 aplicou o patch único sem decisões manuais de ledger. A reauditoria
packet-only `v6luZ9KvmOI_reaudit_002.json` encontrou os dois findings
resolvidos e foi selada como `passed/open_findings=0`: G014 usa `students`,
G024 usa `result` e G041 inclui 1697–1702, agora capturados pelo ledger
derivado. O check read-only do registrador oficial também passou.

W4-R25 não pode alterar dados editoriais. Registra o audit selado uma vez,
executa o build que deriva `complete`, roda o validador com
`--require-external-audit` e confirma o status, o packet e os quatro
fingerprints. Esse é o último gate determinístico de v6lu antes do quality gate
final da Wave 004.

### EXECUTION BRIEF conciso W4-R25

Registrar a reauditoria aprovada sem editar candidatos e derivar o complete;
passar no validador que exige auditoria e provar status, packet e fingerprints.

## Quality gate final — Wave 004 aprovada

O coordenador confirmou o evento 026 e reproduziu o validador de v6lu com
`--require-external-audit`: `pass/errors=[]`. V6lu está
`complete/passed/open_audit_findings=0`, com 41 IDs únicos, packet de cinco
arquivos e relatório de reauditoria 002 de revisor separado do executor.

O runner Fast Path em leitura pura classificou os três episódios como
`protected_complete_read_only`: yyo (54 candidatos), 8WE (42) e v6lu (41),
todos com `complete/passed/zero findings`. Os quatro hashes protegidos de v6lu
foram recalculados pelo coordenador e coincidem com o snapshot.

A Wave 004 está aprovada. Não foram executados commit, push, deploy,
consolidação gold ou Supabase.
