# MSF-R20 Gold Runtime Pilot 005 - Optimization Plan

Status: implemented_validated_complete
Base de teste: `AqzF_M2mM04`

## Objetivo

Reduzir o custo fixo de episodios curtos sem enfraquecer leitura integral,
evidencia verbatim, numeros, relacoes, recall, calibracao, fingerprints ou a
auditoria final unica.

O episodio base permanece preparado, sem reviews persistidos. Depois da
implementacao, ele sera retomado do payload job-local, recompilado e finalizado
como teste real do fluxo novo.

## P0 - eliminar latencia e loops antes do apply

### OPT-005-P0-01 - Partida certificada unica

Criar uma rota `StartEpisode` no launcher/runner que, em uma unica invocacao:

1. sincroniza o runtime somente se o receipt estiver stale;
2. confirma `uname`, Python 3.12, paths Linux-native e comandos obrigatorios;
3. valida paridade e fingerprints;
4. seleciona o primeiro item elegivel da fila;
5. prepara o episodio e gera contexto, manifest e session receipt.

Nao executar `Verify -> Sync -> uname -> Python -> verifier -> SelectBootstrap`
como seis partidas independentes. O receipt precisa registrar cada subfase e o
timer deve iniciar antes do sync.

Meta: 10 segundos warm e 20 segundos com sync de poucos arquivos.

Arquivos provaveis:

- `scripts/invoke_gold_wsl.ps1`
- `scripts/sync_wsl_runtime.py`
- `scripts/verify_wsl_environment.py`
- `scripts/run_gold_episode_fast.py`
- `tests/test_gold_fastpath.py`

### OPT-005-P0-02 - Lineage estavel do risk recall

Vincular cada cluster residual ao cluster fonte preparado por:

- `source_cluster_id` estavel;
- conjunto original de segment IDs;
- `residual_segment_ids` depois da cobertura;
- hash semantico da unidade fonte;
- exclusion reasons do residual.

Uma disposicao continua valida quando o residual e subconjunto do cluster
revisado, conserva a mesma natureza incidental e nao revela nova proposicao
material. Captura parcial nao pode esconder numeros ou claims novos; nesse caso
o residual continua pendente com evidencia explicita.

O prelint deve calcular o fixed point internamente antes de responder. Uma
ampliacao de evidencia como 93-100 nao pode exigir que o modelo reaprove a mesma
promocao sob um ID novo.

Regressoes obrigatorias:

1. `risk-294617...` e seu residual 86-92 compartilham lineage e uma unica
   disposicao incidental;
2. capturar 266-269 mantem 270-280 como residual promocional da mesma lineage;
3. um numero material novo no residual nao herda disposicao incidental;
4. quotes e ledger continuam source-backed.

Arquivos provaveis:

- `scripts/run_gold_episode_fast.py`
- `scripts/gold_review_autocheck.py`
- `scripts/gold_extraction_common.py`, somente se a identidade comum precisar
  de helper puro
- `tests/test_gold_fastpath.py`

### OPT-005-P0-03 - Diagnostico esparso no stdout

Quando `--output` for informado:

- gravar o relatorio integral somente no arquivo;
- imprimir no stdout no maximo status, stopped_at, candidate/review counts,
  hard blockers com ID/range/reason, review gates, warnings, calibracao,
  metrics e path do relatorio;
- limitar o resumo a 8 KB;
- oferecer um bloco compacto de acknowledgements pendentes pronto para ser
  incorporado ao payload, sem transcript repetido.

O relatorio integral continua disponivel para auditoria e debugging, mas nao
consome a janela principal do modelo.

Meta: menos de 2.000 tokens de retorno por prelint e uma unica leitura do
relatorio completo somente quando o resumo indicar erro novo.

## P1 - reduzir composicao e fechamento

### OPT-005-P1-01 - Payload autoral compacto v3

Adicionar `gold_episode_compact_v3` como formato de entrada, expandido pelo
compilador para o contrato atual. O schema persistido nao muda.

O formato deve permitir:

- chaves curtas apenas no artefato autoral;
- defaults por episodio e por tipo;
- ranges compactos;
- shorthand de numbers com expansao deterministica;
- relacoes declaradas por aliases locais e resolvidas para candidate IDs;
- caveats, conditions e steps sem repeticao de campos vazios;
- quotes sempre derivadas do transcript, nunca redigitadas.

Meta no fixture atual: reduzir o payload de 31,6 KB para 12-18 KB e a composicao
de 7m07s para 3m30s-5m.

Arquivos provaveis:

- `scripts/gold_review_compiler.py`
- `scripts/run_gold_episode_fast.py`
- prompt gold e contrato tecnico
- skill gold
- `tests/test_gold_fastpath.py`

### OPT-005-P1-02 - Checklist autoral por tipo

O contexto deve trazer uma tabela curta de requisitos:

- `framework`, `playbook_step` e `script` exigem steps;
- casos quantitativos exigem attribution, risk e caveat quando aplicavel;
- relacoes precisam ser simetricas e aciclicas;
- numero material precisa de raw literal;
- evidencias amplas precisam de ranges atomicos ou justificativa.

O compilador continua sendo autoridade. A tabela apenas evita erros previsiveis
como G009 sem steps antes da primeira chamada.

### OPT-005-P1-03 - Telemetria e retrospectiva automatica

O mesmo run_id deve cobrir sync, verify, selecao, leitura, payload, prelint,
one-shot, auditoria, remediation e completion.

Adicionar ao receipt terminal:

- tempo wall por fase;
- tempo interno dos comandos;
- bytes de contexto, payload, prelint e dossier;
- contagem de candidatos, prelints, remediations e warnings;
- diferenca entre runtime e tempo de julgamento;
- resumo Markdown gerado deterministicamente.

Depois de `complete/passed`, nao reconstruir tempos manualmente nem executar
verificacoes redundantes quando o receipt terminal ja for valido.

## Ordem de implementacao

1. P0-03, porque reduz imediatamente tokens e torna os testes seguintes claros.
2. P0-02, porque elimina o loop que ainda bloqueia o episodio atual.
3. P0-01, porque remove sete minutos antes da selecao.
4. P1-01 e P1-02, para reduzir o custo autoral.
5. P1-03, para medir o proximo teste sem lacunas.
6. Retomar `AqzF_M2mM04`, executar prelint limpo, one-shot, auditoria final
   unica e completion.

## Criterios de aceite

- uma unica chamada inicia runtime certificado e episodio selecionado;
- nenhum fallback para Python ou data root Windows;
- o payload atual produz inventario estavel depois de ampliacao de evidencia;
- stdout de prelint menor que 8 KB com full report preservado no output;
- compact v3 reconstrui exatamente o mesmo draft persistivel que compact v2;
- quote bytes, candidate IDs, numbers, relations, ledger e calibration mantem
  a semantica atual;
- testes Fast Path e pipeline passam;
- py_compile, PowerShell parser, skill quick_validate e `git diff --check`
  passam;
- fixture real e dados gold ficam read-only durante a implementacao;
- no teste final, `AqzF_M2mM04` chega a `complete/passed` com packet de cinco
  arquivos, fingerprints iguais e auditoria final unica.

## Orcamento de desempenho

Para episodio de ate 500 segmentos:

| Fase | Budget |
| --- | ---: |
| Partida certificada e selecao | 10-20s |
| Leitura e payload compacto | 3m30s-5m |
| Prelint/fixed point | 30-60s |
| One-shot deterministico | menos de 30s |
| Auditoria final | 2m30s-4m |
| Completion | 30-60s |

Total esperado sem remediation: 7-10 minutos. Uma remediation semantica curta
pode elevar o total para 9-13 minutos.

## Evidencia de implementacao

- regressao gold completa: 129 testes aprovados no WSL;
- preflight real: Ubuntu 24.04, Python 3.12 da `.venv`, paths Linux-native,
  comandos obrigatorios e temp gravavel;
- parser PowerShell, AST dos modulos, skill quick_validate e diff check passam;
- prelint real do episodio-base: `prelint_clean`, 17 candidatos, calibracao
  9/12, zero blockers e stdout de 3.737 bytes;
- one-shot real: uma persistencia, um finalizer, um build, validacao normal
  `pass`, packet de cinco arquivos e dossier final gerado;
- auditoria final unica em `gpt-5.6-sol/high`: envelope valido em modo
  read-only, inicialmente com `changes_requested` e dois findings numericos;
- remediation focal aplicada em uma revisao transacional: somente G004 e G016
  mudaram; G004 passou a estruturar 86,85% e 1,2x com caveat de ASR, e G016
  passou a estruturar os tres lifts literais de 40%/35%/40%;
- comparacao dos dossiers confirmou transcript, ledger, calibracao, relacoes e
  os outros 15 candidatos inalterados;
- reauditoria final em `gpt-5.6-sol/high`: `passed`, zero findings abertos;
- completion deterministica: `complete/passed/0`, 17 IDs unicos, calibracao
  `pass` com 9 targets cobertos, validacao com auditoria obrigatoria `pass` e
  receipt terminal sem verificacao adicional pendente;
- packet final com exatamente cinco arquivos e os tres fingerprints protegidos
  existentes no snapshot iguais antes/depois; proximo gate: nenhum.
