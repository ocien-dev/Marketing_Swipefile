# MSF-R20 Gold Runtime Pilot 006 - Audit Closure Optimization Plan

Status: implemented_validated_preflight

## Objetivo

Reduzir o custo ativo de um episodio curto de aproximadamente 51 minutos para
9-13 minutos, impedir omissoes numericas parciais antes do primeiro packet e
garantir que `changes_requested` continue internamente ate remediation,
reauditoria e completion.

O proximo benchmark deve usar uma versao congelada do pipeline. Nenhum script,
prompt, skill, schema ou plano medido pode mudar entre a partida certificada e
o receipt terminal.

## P0 - Bloqueios antes do proximo episodio

### OPT-006-P0-01 - Fechamento numerico por candidato

Criar uma funcao pura compartilhada pelo prelint, autocheck, finalizer e dossier
que produza uma matriz por candidato:

- cada mencao numerica material literal na evidencia;
- segmento e contexto curto;
- record correspondente em `numbers`;
- base, periodo, papel, atribuicao e status de valor;
- disposicao explicita quando a mencao for incidental ou redundante;
- lacunas materiais nao resolvidas.

Regras:

- candidato com alguns `numbers` nao pode encerrar automaticamente a checagem;
- percentuais repetidos com bases diferentes permanecem registros distintos;
- cadeias antes/depois preservam inputs e outputs;
- multiplicadores como `1.2x` e percentuais com ASR separado como `86,8 5%`
  permanecem literais, com inferencia/caveat quando necessario;
- support evidence so exige record quando o numero pertence a mesma proposicao,
  a signal `number/test_result` ou a uma sequencia material usada no claim;
- artigos `um/uma`, anos incidentais e exemplos descartados continuam cobertos
  pelas protecoes contra falso positivo existentes.

Lacuna material deve ser `hard_blocker` antes do apply. Ambiguidade de ASR com
raw preservado e caveat continua `audit_warning`.

### OPT-006-P0-02 - Patch de audit baseado na fonte canonica

Adicionar gerador read-only de patch de remediation que:

- le os `manual_reviews` atuais;
- emite asserts somente para campos fonte;
- remove `legacy_*` e outros derivados;
- copia strings UTF-8 e quotes diretamente do JSON atual;
- gera diff semantico fechado por candidate/field;
- executa `--check` sem escrita e vincula `--apply` ao hash da previa.

Uma falha de assert deve devolver o estado atual necessario para regenerar o
mesmo patch, sem aproximacao textual e sem alterar gold.

### OPT-006-P0-03 - Estado terminal do epico

Formalizar no runner os estados:

`execution_ready -> final_audit -> remediation_required -> reaudit -> completion -> complete`

Requisitos:

- `changes_requested` nunca produz resposta final nem marca o epico concluido;
- findings viram inventario interno job-local e a execucao continua;
- somente receipt terminal `complete/passed/0` ou bloqueio externo real libera o
  fechamento no chat;
- `final_response.md` nao e gerado para estado intermediario;
- a reauditoria preserva os findings originais e registra sua resolucao.

### OPT-006-P0-04 - Paridade executavel separada de documentacao

Dividir a assinatura de runtime em:

- `execution_signature`: scripts, prompt, skill, schema, requirements e
  configuracoes que podem mudar a execucao;
- `documentation_signature`: planos, retrospectivas e logs.

Somente drift da assinatura executavel bloqueia gold write. Drift documental e
registrado no receipt e sincronizado depois do terminal. Qualquer mudanca na
assinatura executavel durante o episodio invalida o benchmark e exige nova
partida antes de escrita.

### OPT-006-P0-05 - Dossier como output imediato do finalizer

O mesmo processo que publica o packet deve:

- gerar o dossier final source-complete;
- validar sua reconstrucao contra candidatos, ledger e calibracao;
- gravar atomicamente no job Linux;
- espelhar o dossier verificado para Windows;
- retornar caminho, hashes e tamanho no stdout esparso.

Meta: menos de 15 segundos entre finalizer pronto e dossier disponivel para o
modelo Sol.

## P1 - Telemetria e custo de auditoria

### OPT-006-P1-01 - Spans ativos e intervalos ociosos

Substituir deltas entre eventos por spans com `started_at` e `completed_at`.
Registrar separadamente:

- `active_wall_ms`;
- `runtime_command_ms`;
- `model_judgment_ms` quando mensuravel;
- `inter_turn_idle_ms`;
- `phase_transition_ms`;
- contagens de prelint, apply, finalizer, build, audit e remediation.

O relatorio nao pode atribuir pausa entre turnos a `prelint` ou remediation.

### OPT-006-P1-02 - Matriz numerica no dossier Sol

Incluir no dossier, antes dos candidatos completos:

- resumo de cada candidato com numeros;
- mencoes materiais cobertas e sua correspondencia;
- cadeias antes/depois e calculos reportados;
- lacunas zero esperadas;
- warnings de ASR/atribuicao.

Isso reduz a procura manual do Sol sem ocultar transcript ou candidatos.

### OPT-006-P1-03 - Encerramento governado pelo receipt terminal

Quando `terminal=true` e `additional_verify_required=false`:

- nao executar novo WSL verify, validator ou build;
- validar localmente apenas o JSON espelhado, se necessario para exibir resumo;
- nao enumerar distros nem abrir diagnostico de ambiente pos-completion;
- encerrar com os dados do receipt canonico.

## Arquivos previstos

- `scripts/gold_review_autocheck.py`
- `scripts/gold_review_compiler.py`
- `scripts/run_gold_episode_fast.py`
- `scripts/finalize_gold_episode.py`
- `scripts/gold_final_audit_bundle.py`
- `scripts/gold_review_patch.py`
- `scripts/sync_wsl_runtime.py`
- `scripts/gold_runtime_sync_manifest.json`
- `scripts/complete_gold_episode.py`
- `tests/test_gold_fastpath.py`
- prompt e skill gold somente para refletir o fechamento numerico e o estado
  terminal

## Regressoes obrigatorias

1. Candidato com alguns records, mas percentual material omitido, bloqueia.
2. Sequencia 40%/35%/40% com bases distintas exige os tres records.
3. `86,8 5%` pode ser 86,85 somente com raw preservado, status inferred e
   caveat; `1.2x` continua independente.
4. Numero incidental em support evidence nao vira record automatico.
5. Artigos `um/uma` nao reabrem falsos positivos.
6. Patch assert ignora campos derivados e detecta mudanca real da fonte.
7. `changes_requested` nao gera `final_response.md` terminal.
8. Reauditoria passed/0 leva a uma unica completion.
9. Mudanca em plano nao invalida `execution_signature`.
10. Mudanca em script invalida a paridade antes da escrita.
11. Dossier fica disponivel e hash-bound no mesmo finalizer.
12. Pausa sintetica aparece em `inter_turn_idle_ms`, nao em prelint.
13. Receipt terminal impede verificacao adicional.

## Validacoes

- suite gold completa no Python 3.12 WSL;
- py_compile dos modulos alterados;
- quick_validate da skill, se alterada;
- `git diff --check`;
- dry-run do launcher direto sem `bash -lc`;
- prova de paridade executavel Windows/Linux;
- fixtures G004/G016 derivadas do episodio, sem escrever gold real;
- prova read-only de que episodes complete/passed permanecem imutaveis.

## Metas do proximo benchmark

| Etapa | Meta |
| --- | ---: |
| Partida certificada, selecao e contexto | 15-30s |
| Leitura integral e payload | 4-6m |
| Prelint/fixed point | 1-2m |
| Apply/finalizer/dossier | 15-30s |
| Auditoria Sol | 4-6m |
| Completion | menos de 30s |
| Remediation focal, se necessaria | ate 2m30s |

Aceite do piloto:

- sem remediation: 9-13 minutos ativos;
- com uma remediation focal: 12-16 minutos ativos;
- zero lacunas numericas materiais na primeira auditoria;
- nenhuma edicao de codigo/documentacao durante a janela medida;
- receipt final distingue tempo ativo e ocioso;
- episodio termina `complete/passed/0` antes da resposta final.

## Resultado da implementacao

- `OPT-006-P0-01`: matriz numerica compartilhada implementada no autocheck e
  dossier, com multiplicidade, record completo, atribuicao e tratamento de ASR.
- `OPT-006-P0-02`: gerador source-canonical, preview receipt e apply vinculado
  implementados no patch transacional.
- `OPT-006-P0-03`: `changes_requested` agora produz somente o estado job-local
  `remediation_required`; completion e resposta final continuam reservadas a
  `passed/open_findings=0`.
- `OPT-006-P0-04`: runtime parity separa assinaturas executavel e documental;
  o launcher direto nao enumera distribuicoes antes da invocacao contratada.
- `OPT-006-P0-05`: dossier `2.1.0` e gerado, validado e espelhado atomicamente
  pelo mesmo processo do finalizer.
- `OPT-006-P1-01`: eventos usam spans e separam active wall, comando,
  julgamento mensuravel, idle e transicao.
- `OPT-006-P1-02`: registros de cobertura numerica antecedem candidatos no
  dossier Sol.
- `OPT-006-P1-03`: receipt terminal declara
  `additional_verify_required=false` e preserva o encerramento sem novo gate.

## Evidencias de validacao

- `tests/test_gold_fastpath.py` + `tests/test_gold_pipeline.py`: 138 passed.
- `py_compile`: sete modulos centrais alterados aprovados no Python 3.12.
- `quick_validate.py`: skill gold valida.
- PowerShell AST e dry-run do launcher direto: pass, sem enumeracao de distro.
- `git diff --check`: pass; somente avisos preexistentes de line ending.
- Regressoes cobrem os 13 casos obrigatorios, inclusive fixtures equivalentes
  a G004/G016, paridade documental/executavel e pausa sintetica.

A prova operacional Windows/Linux e as metas de tempo pertencem ao proximo
episodio benchmark. Nenhum gold real foi lido, alterado, construido ou exportado
durante esta implementacao.

## Resultado operacional do piloto

O fluxo foi testado de ponta a ponta em `p78Zv3_WCsM`, com 998 segmentos e 12
chunks. A partida certificada selecionou e preparou o episodio em 699,08 ms no
runner; o launcher completo, incluindo sincronizacao e inicializacao WSL,
consumiu aproximadamente 8,38 s.

- revisao inicial: 12/12 reviews, 23 candidatos e `hard_blockers=0`;
- prelint: quatro previews read-only ate o fixed point, 97,12 ms no preview
  limpo;
- apply/finalizer/dossier: 520,33 ms, packet valido de cinco arquivos;
- auditoria final Sol: `changes_requested/3`, cobrindo um caso omitido de teste
  do primeiro touchpoint, ampliacao cross-format de G014 e relacao G010/G011;
- remediacao focal: uma aplicacao source-backed, 389,65 ms, elevando o total a
  24 candidatos;
- reauditoria final: `passed/open_findings=0`;
- completion: 82,36 ms, lifecycle `complete/passed/0`, validador com auditoria
  obrigatoria aprovado, packet com cinco arquivos e fingerprints preservados.

O tempo de ponta a ponta foi 50m18,49s. Os comandos deterministas registrados
somaram 2,05 s; 48m42,88s foram classificados como intervalos entre eventos e
1m33,49s como transicoes. Portanto, o gargalo remanescente e a leitura,
composicao e auditoria semantica, nao o runtime de persistencia ou validacao.

### Incidentes e correcoes

1. O `sync_wsl_runtime.py --exec-after` herdava o cwd montado do Windows e podia
   importar scripts de `/mnt/c` apesar de executar o Python Linux. O sincronizador
   agora muda para o clone Linux antes de `execv`; a regressao confirma o cwd.
2. Scripts executaveis mudaram no checkout durante a janela e invalidaram a
   paridade antes da remediacao. A escrita foi corretamente bloqueada; uma nova
   sincronizacao certificada renovou o receipt antes de continuar.
3. Evidencia de suporte de G014 incluia uma fala incidental `100%`, que o gate
   numerico tratou como material. A evidencia foi estreitada para a unidade
   source-backed correta antes da unica aplicacao.

### Avaliacao das metas

- partida, apply/finalizer, completion e seguranca WSL superaram as metas;
- prelint determinista ficou abaixo da meta, mas quatro ciclos editoriais ainda
  indicam oportunidade de consolidar o inventario antes do primeiro preview;
- a meta global de 12-16 minutos com remediacao nao foi atingida;
- o proximo ganho relevante deve reduzir a superficie autoral e permitir que a
  auditoria navegue candidatos, gaps e fronteiras prioritarias sem reler o
  dossier de forma linear, preservando a leitura integral source-backed.
