# MSF-R20 Gold Runtime Simplification 011 - Plano de implementacao

Status: phase_5_complete_benchmark_failed_time_and_complexity_acceptance
Owner: chat ativo
Base: retrospectiva do piloto 011 `NiT0-ABoVnk`
Scope: reduzir wall e apagar complexidade sem alterar o schema gold publico

## Objetivo

Reduzir um episodio de 900-1.300 segmentos para:

- 25-40 minutos quando o primeiro packet passar sem finding;
- 35-50 minutos quando houver uma remediacao focal;
- no maximo uma transacao semantica inicial e uma transacao pos-auditoria;
- zero helper Python especifico do episodio no caminho normal;
- `complete/passed/0`, packet de cinco arquivos e fingerprints preservados.

O plano nao adiciona gates. Ele substitui caminhos paralelos por uma fonte
autoral unica e torna duravel a fronteira de auditoria.

## Guardrails

- manter leitura cronologica integral;
- manter auditoria final Sol/high source-complete;
- manter ambiguidade editorial como warning;
- nao impor limite de candidatos;
- nao auto-criar, auto-mesclar ou auto-excluir proposicoes;
- nao alterar o schema persistido;
- nao reabrir WSL como arquitetura canonica;
- nao criar coordenador, worker, heartbeat, runner ou checkpoint de chat;
- nao otimizar runtime deterministico antes de reduzir a camada semantica.

## Mudancas aprovadas por alto potencial

### HI-01 - Identidade terminal canonica antes da selecao

Problema eliminado: reprocessar episodio ja completo em outro receipt/data root
ou confiar em `source_status` historico da fila.

Implementacao:

1. Definir `terminal_identity` por:
   - `episode_video_id`;
   - hash semantico da fonte gold usada;
   - arquitetura `chronological_hybrid_v1`;
   - schema gold;
   - audit status e completion receipt.
2. Fazer o seletor consultar o data root Windows ativo e o registry terminal
   reconciliado, nao somente a fila.
3. Recusar nova extracao quando existir `complete/passed` compativel, salvo
   `--explicit-reprocess` com motivo e novo run ID.
4. Reconciliar uma unica vez receipts WSL historicos com o registry Windows,
   sem copiar raw, packet ou gold automaticamente.

Por que e alto impacto: pode evitar 100% de um processamento duplicado. O custo
determinista esperado e sub-segundo.

Criterios de aceite:

- fixture com estado de fila stale e receipt terminal atual nao e selecionada;
- fonte/hash divergente continua elegivel para reprocesso explicito;
- fila permanece apenas ordenacao;
- nenhum dado gold e migrado ou sobrescrito pelo check.

### HI-02 - Manifesto semantico autoritativo unico

Problema eliminado: payload + review patch + ledger rebind + calibracao
pos-build + helpers especificos disputando autoridade.

Implementacao:

1. Criar um `gold_authoring_manifest` esparso e job-local contendo somente
   decisoes do modelo:
   - candidatos e atomos do claim;
   - evidencia minimal/support por clean index;
   - numeros com literal, unidade, periodo e funcao;
   - caveats, steps, conditions e relations;
   - disposition source-scoped de blocos nao capturados;
   - decisao de calibracao target -> candidato ou `none`.
2. Compilar desse manifesto, em memoria e deterministicamente:
   - reviews por chunk;
   - ledger completo;
   - calibration tests;
   - workbench;
   - payload de persistencia.
3. Proibir no caminho normal:
   - `ledger_updates` manuais;
   - calibracao corrigida depois do build;
   - helper Python gerado pelo modelo;
   - escrita direta em review individual.
4. Usar o mesmo manifesto no preview, apply, remediation e delta.

Por que e alto impacto: elimina a causa dos 27 helpers, 34 artefatos de patch,
rebinds e redirects repetidos. Mantem o schema final e reduz escolhas.

Criterios de aceite:

- episodio limpo: 1 preview, 1 apply, 1 build, 1 finalizer e 1 dossier;
- episodio com finding: adicionar no maximo 1 patch do manifesto, 1 build, 1
  finalizer e 1 delta;
- zero helper `.py` especifico do episodio;
- zero patch de ledger ou calibracao pos-build;
- ledger e calibracao rederivados do mesmo hash do manifesto;
- manifest stale falha antes de qualquer escrita.

### HI-03 - Passagem adversarial do executor dentro da autoria

Problema eliminado: enviar para a Sol erros ja conhecidos e pagar remediacao
depois do packet.

Esta nao e uma auditoria intermediaria. E o fechamento final da mesma autoria,
antes do unico apply.

Implementacao:

1. Depois da leitura cronologica, gerar uma unica view compacta do manifesto:
   `source block -> candidate -> claim atoms -> evidence -> numbers -> caveats -> calibration`.
2. Executar uma passagem adversarial unica, nesta ordem:
   - ownership de evidencia e numeros;
   - blocos materiais excluidos;
   - fala do host versus entrevistado;
   - before/after, mecanismos, outcomes e caveats;
   - targets de calibracao por equivalencia, nao tema;
   - fronteiras adjacentes e counterexamples.
3. Congelar como regressao os findings F019 e F037 do piloto 011.
4. Editar o mesmo manifesto e executar no maximo dois prelints oficiais.

Por que e alto impacto: 67 candidatos foram adicionados depois do primeiro
apply. Cinco a dez minutos antes do packet podem evitar dezenas de minutos de
remediacao e uma reauditoria.

Criterios de aceite:

- F019 e F037 sao detectados em fixture antes do apply;
- nenhum target apenas tematico passa como calibrado;
- numero de support de outra proposicao nao entra no candidato;
- bloco high-risk nao pode ser incidental sem source scope;
- primeiro dossier de dois pilotos consecutivos tem zero finding das classes
  congeladas;
- no maximo dois prelints; warnings editoriais nao viram blockers.

### HI-04 - Auditoria duravel e reauditoria delta obrigatoria

Problema eliminado: perder o veredito Sol, manter span aberto por horas e
reiniciar leitura integral apos findings.

Implementacao:

1. Antes da fase Sol, selar dossier hash, audit route, modelo e effort em um
   `audit_request_receipt` job-local.
2. A primeira acao apos o retorno Sol deve validar e materializar o envelope
   de auditoria no job-dir. Nenhuma outra operacao ocorre antes disso.
3. Se o chat/modelo for interrompido sem envelope:
   - marcar o span como `interrupted`, nao ativo;
   - preservar request e dossier hash;
   - reiniciar somente a fase Sol, nunca extracao/build.
4. Se houver findings:
   - compilar um unico patch do manifesto;
   - gerar delta com invariantes;
   - fazer reauditoria focal obrigatoria;
   - usar dossier integral apenas se o delta falhar.
5. O completion consome exatamente o envelope materializado e o hash selado.

Por que e alto impacto: o piloto perdeu mais de oito horas no span de
reauditoria. O delta final provou que a recuperacao focal funciona.

Criterios de aceite:

- interrupcao de modelo nao perde dossier, audit request ou findings;
- span interrompido nao conta como compute/auditoria ativa;
- retomada sem finding reinicia somente a auditoria;
- retomada pos-finding usa delta em ate cinco minutos, quando invariantes
  passam;
- envelope e completion referenciam o mesmo dossier semantic hash;
- zero auditoria intermediaria e zero novo checkpoint do chat.

## Remocoes obrigatorias

O plano so e considerado implementado se remover complexidade:

- descontinuar helpers job-local do fluxo normal;
- descontinuar patch de ledger separado;
- descontinuar patch de calibracao pos-build;
- descontinuar dossiers intermediarios sem solicitacao da auditoria;
- descontinuar reexecucao de finalizer para diagnostico editorial;
- descontinuar taxonomias model-facing paralelas ao manifesto;
- descontinuar contador de patch/remediation que nao recebe eventos reais.

Full reports podem continuar para debug, mas nao entram na entrada primaria do
modelo nem criam decisao adicional.

## Sequencia de implementacao

### Estado da implementacao em 2026-07-18

- Fases 1 a 4 implementadas no runtime Windows nativo.
- HI-01: registry terminal central e identidade por episodio reconciliam fonte,
  arquitetura, schema, audit e completion antes da selecao; reprocesso de fonte
  alterada exige motivo explicito.
- HI-02: `gold_authoring_manifest_v1` virou a autoridade interna unica; preview,
  apply e remediacao vinculam o mesmo hash, enquanto ledger, calibracao e
  payload persistido sao derivados deterministicamente.
- HI-03: a view adversarial cobre ownership, exclusoes, host/entrevistado,
  claims/caveats, calibracao por equivalencia, fronteiras e counterexamples; as
  falhas F019 e F037 possuem regressoes pre-write.
- HI-04: request e envelope de auditoria sao duraveis e hash-bound; retomada
  reinicia apenas Sol, spans interrompidos ficam fora do tempo semantico ativo,
  remediacao substitui o manifesto uma vez e produz delta ou fallback automatico
  para o dossier integral.
- Rotas legadas permanecem apenas como compatibilidade de fixtures e dados
  historicos, nao como caminho normal documentado.
- Fase 5 foi executada em `jbFY16W5GTE` e `fBaX4ixKkFo`. Os dois episodios
  terminaram `complete/passed/0`, mas as metas de wall e complexidade nao foram
  atingidas. O benchmark valida o nucleo deterministico e reprova a otimizacao
  ponta a ponta; os resultados reais estao registrados abaixo.

Evidencia deterministica: 167 testes focados, 222 testes gold ampliados e 287
testes da suite completa aprovados; `py_compile`, preflight Windows nativo e
validacao estatica aprovados.
Nenhum episodio real ou dado gold foi alterado nesta implementacao.

### Fase 1 - Impedir desperdicio integral

1. Implementar `terminal_identity` e regressao de fila stale.
2. Reconciliar registry terminal Windows versus receipts historicos.
3. Validar read-only no proximo seletor.

Gate: nenhum episodio terminal compativel pode ser selecionado.

### Fase 2 - Substituir a API manual

1. Definir schema interno do manifesto sem alterar schema gold.
2. Compilar reviews, ledger e calibracao em memoria.
3. Fazer preview/apply consumirem o mesmo hash.
4. Remover rotas job-local de ledger/calibration patch do fluxo normal.

Gate: fixtures gold existentes passam e um episodio fixture exige zero helper.

### Fase 3 - Elevar a qualidade do primeiro packet

1. Materializar F019/F037 como regressao.
2. Integrar a passagem adversarial ao fechamento da autoria.
3. Provar no maximo dois prelints e nenhuma escrita com blocker.

Gate: todas as classes conhecidas falham antes do apply.

### Fase 4 - Tornar auditoria retomavel

1. Criar audit request receipt e envelope-first persistence.
2. Registrar estados `running`, `interrupted` e `completed` sem heartbeat.
3. Integrar audit finding -> manifest patch -> delta.
4. Testar interrupcao antes e depois do veredito.

Gate: a recuperacao nao repete extracao, build ou dossier integral valido.

### Fase 5 - Benchmark real congelado

Executar dois episodios novos de 900-1.300 segmentos com assinatura de runtime
congelada. Nao modificar o pipeline entre os dois, salvo defeito de qualidade.

Resultado em 2026-07-18: fase concluida com aceite funcional e rejeicao das
metas de tempo/complexidade.

| Medida | `jbFY16W5GTE` | `fBaX4ixKkFo` | Resultado |
| --- | ---: | ---: | --- |
| Segmentos / chunks | 1.106 / 21 | 1.238 / 23 | dentro da faixa |
| Selecao + contexto | 0,80s | 2,43s | passou `<=3s` |
| Leitura e autoria | 24m23s | 19m59s | passou `18-28m` |
| Prelint inicial | 0,91s | 0,72s | passou no custo deterministico |
| One-shot inicial | 4,93s | 4,06s | passou `<=10s` |
| Auditoria inicial instrumentada | 38m19s | 17m20s | E1 contaminado por sobreposicao/espera; E2 acima de 10m |
| Autoria de remediacao | 11m28s | 10m29s | acima da meta de 5-10m |
| Reauditoria final 03 | 6m11s | 6m22s | passou `6-10m` |
| Completion | 0,17s | 0,38s | passou `<=2s` |
| Wall por receipt | 3h34m01s | 3h08m10s | reprovou `35-50m` |
| Gap nao classificado | 2h13m18s | 1h20m05s | reprovou `<10%` |

O wall da wave, do inicio do primeiro receipt ao complete do segundo, foi
aproximadamente 3h34m23s. As duas execucoes se sobrepoem; por isso os walls por
episodio nao devem ser somados.

Qualidade final:

- `jbFY16W5GTE`: 34 candidatos, 1.106/1.106 indexes reconstruidos,
  calibracao `pass`, auditoria Sol/high `passed`, zero findings;
- `fBaX4ixKkFo`: 44 candidatos, 1.238/1.238 indexes reconstruidos,
  calibracao `pass`, auditoria Sol/high `passed`, zero findings;
- ambos: packet de cinco arquivos, fingerprints preservados, terminal identity
  registrada e `additional_verify_required=false`.

Defeitos de qualidade que autorizaram mudanca entre os dois ramos:

1. calibracao de fonte duplicada exigia link semantico derivado mesmo quando a
   duplicata, a fonte canonica e o anchor numerico estavam explicitamente
   declarados; a validacao agora prova os ranges fonte/candidato diretamente;
2. repeticao oral de um numero consumia outro record de mesmo valor; o runtime
   agora aceita `covered_explicit_duplicate` somente com caveat humana estrita
   `source duplicate` + `not a second observation`, sem criar observacao falsa;
3. uma warning `captured` podia contradizer ledger/evidencia; o episodio foi
   corrigido para `retained_support` com justificativa source-backed.

Diagnostico de complexidade:

- houve 2 e 3 prelints registrados, dentro/um acima do limite;
- os receipts contam um finalizer inicial e dois builds, mas as remediacoes
  persistidas nao foram contadas (`remediations=0`, `patches=0`), logo a
  telemetria de complexidade continua inexata;
- mudancas pequenas alteraram warning IDs e reabriram gates de calibracao,
  gerando varios checks locais; isto confirma que IDs derivados continuam
  acoplados demais ao snapshot completo;
- spans interrompidos foram corretamente excluidos do tempo ativo, mas um span
  stale de `prelint_repair` acumulou 53m04s no segundo episodio e os gaps
  continuaram muito acima do limite.

Decisao: manter os ganhos comprovados de identidade terminal, manifesto unico,
one-shot, reauditoria retomavel e as duas correcoes de integridade acima. Nao
promover novas heuristicas, gates ou camadas. A proxima melhoria somente deve
ser aberta se remover uma causa estrutural inteira: estabilizar IDs de warnings
contra edicoes semanticas locais e fazer a remediacao transacional substituir
o snapshot sem reabrir calibracoes nao afetadas, com contadores honestos.

## Orcamento por etapa

| Etapa | Piloto 011 | Meta de aceite |
| --- | ---: | ---: |
| Selecao/preflight/contexto | 1,05s ativos | <= 3s |
| Leitura e autoria | 34m51s | 18-28m |
| Passagem adversarial + prelint | 2m06s de repair, fora autoria | 4-7m totais |
| Apply/build/finalizer/dossier | 4,50s inicial; repetido varias vezes | <= 10s e uma vez |
| Auditoria integral | 9m44s | 6-10m |
| Remediacao + delta, se houver | 10m36s + horas de espera | 5-10m |
| Completion | 0,83s | <= 2s |
| Total sem finding | 9h43m observado | 25-40m |
| Total com uma remediacao | 9h43m observado | 35-50m |

As metas exigem dois pilotos consecutivos. Nao sacrificar leitura ou auditoria
para cumprir teto.

## Indicadores de complexidade

| Indicador | Piloto 011 | Limite de aceite |
| --- | ---: | ---: |
| Helpers Python especificos | 27 | 0 |
| Dossiers | 12 | 1 sem finding; 2 com finding |
| Finalizers | 9 | 1 sem finding; 2 com finding |
| Builds | 6 | 1 sem finding; 2 com finding |
| Audit bundles | 5 | 1 dossier + 1 delta opcional |
| Prelints oficiais | 3 | <= 2 |
| Contagem patches/remediations | 0/0 incorreto | igual aos eventos reais |
| Gap nao classificado | 38m36s | < 10% do wall |

## Validacoes obrigatorias

- regressao completa de F019 e F037;
- reconstruir 100% dos clean indexes;
- quotes verbatim iguais;
- numeric raw/value/unit/period/role coerentes;
- ledger e calibracao derivados do manifesto;
- preview receipt e apply com mesmo hash;
- zero write em blocker;
- packet de cinco arquivos;
- fingerprints preservados;
- audit Sol/high, passed e zero finding;
- `py_compile`, suite gold e `git diff --check`;
- nenhum dado real alterado durante a implementacao, antes do benchmark.

## Go/no-go

Go somente para HI-01 a HI-04. Nao abrir stories para:

- mais heuristicas de risco;
- mais campos de telemetria sem consumidor;
- otimizar Python, PowerShell, temp ou preflight;
- novo compilador semantico cego;
- reduzir transcript, candidatos ou auditoria;
- criar novo gate, papel, chat ou runner;
- melhorar cosmeticamente stdout sem remover uma decisao.

Se o manifesto unico nao eliminar helpers e derivados pos-build em fixture, o
plano e `no-go`; nao se adiciona outra camada por cima.
