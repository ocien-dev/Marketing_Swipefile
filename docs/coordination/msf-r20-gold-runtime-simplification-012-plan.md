# MSF-R20 Gold Runtime Simplification 012 - Plano de implementacao

Status: complete_passed_0
Owner: chat ativo
Base: `msf-r20-gold-runtime-benchmark-011-retrospective.md`
Escopo: remover falso-ready, revalidacao global e duplicacao da auditoria sem
alterar o schema gold publico ou reduzir leitura/auditoria

## Objetivo

Reduzir o processamento de um episodio de 900-1.300 segmentos para:

- 25-40 minutos quando a primeira auditoria passa;
- 35-50 minutos com uma remediacao source-backed;
- 55-75 minutos para uma wave de dois episodios sem finding;
- 70-90 minutos para uma wave de dois episodios com uma remediacao.

Esses valores sao criterios de benchmark, nao promessa. Qualidade continua
prioritaria: transcript integral, quotes verbatim, numeros, ledger, calibracao,
fingerprints e auditoria Sol/high permanecem obrigatorios.

## Problemas confirmados

1. O primeiro dossier foi marcado pronto com 427 segmentos unreviewed e 183
   segmentos must-close entre os dois episodios.
2. A auditoria do primeiro ramo iniciou antes de toda a wave estar pronta.
3. Cinco findings major obrigaram aproximadamente 2h03m de remediacao e
   reauditoria 02.
4. Edicoes locais regeneraram warning IDs e reabriram calibracoes nao afetadas.
5. A remediacao gravou estado valido e falhou depois do commit por ausencia de
   envelope.
6. Quinze eventos pos-audit por episodio contrastam com contadores finais
   `remediations=0` e `patches=0`.
7. Header mais workbench ocupam 62,5-65,5% dos dossiers de 910-931 KB.

## Principios

- corrigir invariantes existentes, nao criar novos papeis ou gates humanos;
- apagar rotas e copias paralelas antes de adicionar abstracoes;
- IDs dependem da fonte/proposicao local, nao do snapshot global;
- precondicao falha antes de qualquer escrita;
- derivado e recompilado do manifesto; nunca recebe patch autoral paralelo;
- auditoria final somente depois do gate consolidado da wave;
- telemetria nasce do commit existente; nao exige comando manual adicional;
- nenhuma mudanca no schema gold publico.

## HI-012-01 - Tornar `ready` realmente source-complete

### Causa eliminada

O finalizer e o dossier aceitaram `hard_blockers=[]` mesmo com source
dispositions incompletas, segmentos unreviewed e blocos must-close abertos.

### Implementacao

1. Criar uma unica funcao canonica `source_complete_invariants()` consumida por
   prelint, finalizer e dossier.
2. A funcao recebe explicitamente os IDs/ranges esperados do transcript atual e
   exige:
   - exatamente uma disposition por clean index;
   - zero `unreviewed`;
   - zero must-close sem decisao source-scoped;
   - captured/retained support sempre com candidato da mesma proposicao;
   - incidental sempre com source scope e justificativa;
   - numeric coverage `pass` para todo candidato quantitativo;
   - calibracao derivada compativel com a decisao autoral.
3. Remover caminhos que inferem cobertura a partir de lista vazia, warning
   agregado ou `hard_blockers=[]` isolado.
4. Impedir `awaiting_external_audit` e emissao de dossier quando qualquer
   invariante falhar. O resultado continua `terminal=false` e
   `continue_required=true`.
5. O repair inventory deve retornar somente os itens abertos, com source ranges
   e candidate IDs, sem duplicar o report completo.

### Impacto esperado

Evitar a classe inteira dos cinco findings iniciais e eliminar a primeira
auditoria desperdicada mais a remediacao de cobertura. Potencial observado:
60-120 minutos por wave.

### Criterios de aceite

- fixtures que reproduzem 229/198 unreviewed falham antes de qualquer write;
- warning `captured` ou `retained_support` sem candidate binding falha;
- outcome reportado sem controle permanece capturavel com attribution/caveat,
  nunca vira incidental automaticamente;
- 100% dos clean indexes sao reconstruidos a partir do manifesto;
- episodio limpo continua com um prelint oficial e um one-shot;
- nenhuma mudanca no schema persistido.

## HI-012-02 - Remediacao envelope-first, local e transacional

### Causas eliminadas

- warning IDs globais mudam com edicao nao relacionada;
- calibracoes nao afetadas sao reabertas;
- precondicao de envelope falha depois da persistencia;
- varios checks, rebuilds e finalizers representam uma remediacao;
- contadores e spans nao refletem o commit real.

### Implementacao

1. Redefinir warning identity com hash de:
   `category + source_segment_ids/range + candidate_id + proposition fingerprint`.
   Campos de outros candidatos, ordem global e timestamps ficam fora.
2. Persistir no manifesto a identidade local de entrada da decisao. Reusar a
   decision somente quando esse input local permanecer igual.
3. Derivar um impact set fechado a partir dos findings:
   candidatos, source ranges, numeros, warnings, calibracoes e relacoes
   diretamente dependentes.
4. Validar e materializar o audit envelope antes de abrir a transacao. Envelope
   ausente ou stale causa zero write.
5. Executar em uma chamada:
   - validate envelope/base hash;
   - compilar manifesto completo;
   - validar somente o impact set e invariantes globais obrigatorias;
   - persistir reviews afetados;
   - rederivar ledger/calibracao;
   - executar um build/finalizer;
   - emitir dossier focal ou fallback integral;
   - fechar span e incrementar contadores no mesmo commit receipt.
6. Remover os comandos manuais de start/end para remediacao e os contadores
   inferidos de eventos. O receipt transacional e a unica autoridade.
7. Se o delta falhar invariantes, emitir automaticamente request para o dossier
   integral; nunca retornar erro depois de um packet valido sem indicar que o
   commit ocorreu.

### Impacto esperado

Reduzir 15 eventos pos-audit por episodio para no maximo dois comandos
(check/commit), eliminar warning churn e transformar 10-20 minutos de autoria
mais dezenas de minutos de gaps em uma remediacao unica de 5-10 minutos.

### Criterios de aceite

- editar G044 nao muda warning IDs de G012/G014/G020;
- calibracao fora do impact set mantem decision e hash local;
- envelope ausente produz zero write, zero build e zero finalizer;
- finding corrigido produz exatamente uma remediacao, um build, um finalizer e
  um dossier/delta;
- receipt registra `remediations=1`, `patches=1` ou substituicao equivalente e
  os mesmos numeros aparecem no session report;
- nenhuma falha ocorre depois do commit sem um receipt que declare o estado
  persistido e a proxima acao;
- spans interrompidos nunca contam como ativos; nao existe span stale aberto.

## HI-012-03 - Uma superficie de auditoria e despacho final da wave

### Causas eliminadas

- a Sol recebe transcript, navigation, warnings e workbench com evidencias
  repetidas;
- o primeiro audit iniciou antes do segundo ramo estar pronto;
- auditoria final vira auditoria intermediaria e precisa ser repetida.

### Implementacao

1. Manter um unico JSONL source-complete. Nao criar novo brief paralelo.
2. Preservar transcript integral, candidatos, numeros, ledger, calibracao,
   fingerprints e gates.
3. Remover do header:
   - copia integral de `audit_navigation` quando os mesmos ranges existem no
     workbench;
   - quotes e claims duplicados dentro de warnings.
4. Representar warning por referencia compacta:
   `warning_id`, categoria, candidate IDs, segment/range IDs, disposition e
   justificativa. A fonte verbatim e resolvida no transcript/candidato do mesmo
   dossier.
5. Manter somente um workbench ordenado pela rubrica P0-P3, com referencias,
   nao copias da fonte.
6. O audit request consolidado so pode ser emitido quando todos os episodios do
   escopo estiverem `ready`, os hashes dos dossiers estiverem congelados e o
   gate da wave reconstruir 100% dos indexes.
7. Uma auditoria Sol/high le o workbench e faz uma passagem integral no mesmo
   dossier. Findings posteriores usam o delta da HI-012-02.

### Impacto esperado

Reduzir dossiers de 910-931 KB para no maximo 500 KB sem remover fonte e
reduzir a auditoria inicial de 38m19s por wave para 12-20 minutos.

### Criterios de aceite

- dossier `<=500 KB` em ambos os fixtures reais;
- transcript e quotes byte-identicos;
- todos os findings da auditoria inicial do benchmark 011 continuam
  detectaveis no fixture defeituoso;
- zero evidencia aparece em duas superficies model-facing diferentes;
- audit request antes do gate N/N falha read-only;
- dois episodios prontos geram um request consolidado e uma auditoria final;
- hash de dossier permanece imutavel durante a Sol.

## Ordem de implementacao

### Fase 0 - Baseline e protecao

1. Congelar fixtures dos dossiers inicial, remediation-02 e remediation-03.
2. Registrar hashes, findings e contagens atuais.
3. Criar regressao que exige os cinco findings no fixture inicial e zero no
   fixture final.

Gate: nenhuma alteracao de dado real.

### Fase 1 - HI-012-01

Implementar a invariante source-complete e apagar caminhos false-clean.

Gate: fixtures iniciais bloqueiam antes do write; fixtures finais passam.

### Fase 2 - HI-012-02

Implementar identidade local, impact set e transacao envelope-first. Remover
rotas/counters manuais substituidos.

Gate: uma remediacao, um commit, um build, um finalizer e contadores exatos.

### Fase 3 - HI-012-03

Deduplicar o dossier existente e vincular o audit request ao gate consolidado.

Gate: dossier `<=500 KB`, source-complete e findings preservados.

### Fase 4 - Benchmark congelado

Executar dois episodios consecutivos de 900-1.300 segmentos. Nao alterar codigo
entre eles, salvo defeito de qualidade confirmado.

Gate final:

- `complete/passed/0` nos dois;
- zero candidato/material adicionado por classe ja coberta pela invariante;
- crescimento pos-primeiro apply `<=5%`;
- no maximo dois prelints oficiais;
- um finalizer/build/dossier sem finding; dois com uma remediacao;
- warning IDs nao afetados 100% estaveis;
- contadores iguais aos receipts de commit;
- gap nao classificado `<10%`;
- auditoria inicial `<=10m` por episodio ou `<=20m` por wave de dois;
- wall `25-40m` sem finding e `35-50m` com uma remediacao;
- `py_compile`, suite completa, `git diff --check`, packets e fingerprints
  aprovados.

## Fora de escopo

- nova heuristica de risco;
- novo compilador semantico;
- novo brief, helper, papel, chat, runner ou heartbeat;
- reduzir transcript, chunks, candidatos ou auditoria integral;
- micro-otimizar Python, temp, PowerShell, selecao, one-shot ou completion;
- adicionar campos de telemetria sem remover um comando/manual state;
- alterar schema gold publico, Supabase, master ou curated.

## Go/no-go

Go apenas para HI-012-01, HI-012-02 e HI-012-03. Qualquer proposta adicional
precisa demonstrar eliminacao de uma causa estrutural inteira e economia
esperada de pelo menos 10 minutos por episodio ou 20% da superficie
model-facing, sem novo papel ou fonte de verdade.

## Resultado da implementacao - 2026-07-18

- HI-012-01: `source_complete_invariant_issues()` passou a ser consumida por
  prelint, finalizer e dossier. Segmento `unreviewed`, reconstrucao incompleta,
  must-close sem review, numero material ausente ou calibracao reprovada
  impedem ready/dossier.
- HI-012-02: o envelope, request, episodio, artifact hash e dossier anterior
  agora sao validados antes do primeiro write. O CLI materializa `--audit-input`
  antes da remediacao; warning IDs usam identidade local e preservam fallback
  de provenance; o delta registra impact set fechado; falha posterior ao commit
  registra `commit_state` e proxima acao.
- HI-012-03: removido `audit_navigation`; warnings, risk recall e workbench
  usam tabelas de referencias; justificativas repetidas sao internadas uma vez.
  O request consolidado falha read-only se qualquer ramo nao estiver ready e
  sela os hashes de todos os dossiers N/N.
- Benchmark congelado real: `jbFY16W5GTE` caiu de 909.666 para 457.810 bytes
  (-49,67%); `fBaX4ixKkFo` caiu de 930.916 para 491.827 bytes (-47,17%).
  Ambos validaram source, candidatos, numeros, ledger, calibracao, packet e
  fingerprints sem erro e ficaram abaixo de 500.000 bytes.
- Validacao automatizada: `py_compile`, `git diff --check` e suite completa
  `301 passed`.
- A auditoria final unica `gpt-5.6-sol/high` aprovou integridade, compactacao
  e deduplicacao do runtime, mas manteve quatro findings semanticos nos golds
  protegidos usados como fixtures. Portanto o codigo esta implementado e o
  benchmark estrutural passou, mas o gate final `passed/0` nao foi derivado.
- Os SLAs de wall end-to-end permanecem criterio para o proximo episodio novo;
  o benchmark congelado comprova as invariantes e a reducao de superficie, nao
  simula leitura/autoria humana nem atribui a elas tempo artificial.

## Fechamento da remediacao autorizada - 2026-07-18

- O owner autorizou explicitamente reabrir os dois golds protegidos. A revisao
  preservou identidades terminais e auditorias anteriores em historico imutavel.
- `jbFY16W5GTE`: F012-01/F012-03 corrigidos em uma transacao de 4.874,61 ms,
  com 34 candidatos, `hard_blockers=0`, uma escrita de reviews, um build, um
  finalizer e um dossier.
- `fBaX4ixKkFo`: F012-02/F012-04 corrigidos em uma transacao de 4.024,33 ms,
  com 44 candidatos, `hard_blockers=0`, uma escrita de reviews, um build, um
  finalizer e um dossier.
- A auditoria final unica `gpt-5.6-sol/high`, fase
  `/root/final_sol_remediation_012`, revisou os dois dossiers integralmente e
  retornou `passed/0`, sem findings novos.
- Ambos terminaram `complete/passed/0`, packets de cinco arquivos,
  fingerprints preservados e receipts terminais validos. O gate consolidado
  final aprovou os dois ramos protegidos, semantic hash
  `d0810ef1260891716c4f04d8c675498064d755ddbfd3c40e44f344ae980a8a22`.
- Validacao final: runtime Windows native, `py_compile`, `git diff --check` e
  suite completa `303 passed`.
