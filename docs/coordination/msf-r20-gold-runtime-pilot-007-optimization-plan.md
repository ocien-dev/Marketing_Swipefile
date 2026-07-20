# MSF-R20 Gold Runtime Pilot 007 - Semantic Closure and Audit Acceleration

Status: validated_with_regressions
Base: retrospectiva de `p78Zv3_WCsM`

## Objetivo

Reduzir o wall time de episodios entre 700 e 1.300 segmentos sem remover leitura
integral, evidencia verbatim, recall adversarial, auditoria Sol ou gates
deterministas.

O plano deve prevenir, antes do primeiro packet, os tres findings do piloto 006
e reduzir uma remediacao equivalente de 21m45s para no maximo cinco minutos.

## Principios de qualidade

1. Transcript integral continua sendo fonte de verdade.
2. Heuristicas novas produzem superficies de revisao, nunca claims ou relacoes
   automaticas.
3. Quote e raw literal sao copiados da fonte; nao sao traduzidos nem
   normalizados.
4. Ledger e calibracao continuam derivados dos candidatos finais.
5. Um warning so fecha com disposicao e justificativa source-backed.
6. Auditoria delta pode acelerar reauditoria, mas a prova de invariantes cobre o
   packet inteiro.
7. O runtime usado por um episodio permanece imutavel ate seu receipt terminal.

## P0 - impedir os mesmos findings e o retrabalho caro

### OPT-007-P0-01 - Runtime congelado por run_id

No `StartEpisode`, vincular o job ao `execution_signature` e ao snapshot Linux
ja certificado.

- chamadas posteriores do mesmo run validam o snapshot de destino, nao mudam
  silenciosamente para uma versao nova;
- drift posterior no checkout Windows e registrado para o proximo run, sem
  invalidar a versao congelada atual;
- mutacao do snapshot Linux, manifest divergente ou receipt trocado continuam
  hard blockers;
- nenhuma sincronizacao e permitida entre packet inicial e completion;
- o cwd do processo substituido deve ser sempre o clone/snapshot Linux.

Arquivos:

- `scripts/sync_wsl_runtime.py`
- `scripts/run_gold_episode_fast.py`
- `scripts/invoke_gold_wsl.ps1`
- `tests/test_gold_fastpath.py`

### OPT-007-P0-02 - Payload source-canonical e repair scaffold

Estender compact v3 para reduzir redigitacao mecanica:

- numbers podem referenciar `segment_id` e span literal; o compilador copia
  `raw` byte a byte;
- o contexto entrega o objeto canonico de `audit_warning_dispositions` e os
  aliases aceitos, sem chave inventada;
- compiler/prelint retorna um `repair_scaffold` job-local com todos os erros,
  valores atuais, valores esperados e campos semanticos que ainda exigem
  julgamento;
- o scaffold nunca corrige claim, caveat, relacao ou disposition sozinho;
- um check local do mesmo compilador ocorre antes do unico preview oficial.

Meta: um preview oficial limpo; no maximo uma segunda chamada quando houver
decisao semantica nova.

Arquivos:

- `scripts/gold_review_compiler.py`
- `scripts/run_gold_episode_fast.py`
- prompt, contrato e skill gold
- `tests/test_gold_fastpath.py`

### OPT-007-P0-03 - Fechamento semantico de bordas e contencao

Adicionar ao autocheck uma superficie `semantic_closure_index` com:

1. **adjacent evidence tails:** janelas nao capturadas imediatamente antes ou
   depois da evidencia de cada candidato;
2. **episode tail:** toda unidade depois da ultima evidencia capturada;
3. **chunk boundaries:** janelas adjacentes entre chunks, mesmo quando nao ha
   signal de alto nivel;
4. **evidence containment groups:** candidato cuja evidencia minima esta
   contida na evidencia minima/suporte de outro;
5. **scope continuation:** enumeracoes ou formatos citados logo depois da
   proposicao capturada.

Cada item exige uma disposicao:

- `captured` com candidate ID;
- `retained_support` com candidate ID;
- `incidental` com justificativa;
- `relation_not_useful` com justificativa para grupos de contencao.

Itens sem disposicao formam `review_gate`, nao hard blocker estrutural. A
fixture do piloto 006 deve expor 763-770, 913-923 e G010/G011 antes do primeiro
packet.

Arquivos:

- `scripts/gold_review_autocheck.py`
- `scripts/run_gold_episode_fast.py`
- `scripts/gold_extraction_common.py`, somente para helpers puros
- `tests/test_gold_fastpath.py`

### OPT-007-P0-04 - Dossier Sol v3 de passagem unica

Reorganizar o dossier sem remover nenhuma fonte:

- header e mapa de navegacao;
- candidatos ordenados pelo primeiro clean index;
- numeric coverage, calibracao e grupos de relacao;
- transcript integral com disposition e candidate IDs inline por clean index;
- warnings e ledger detalhado sem duplicar texto do transcript;
- footer com hashes e prova de reconstrucao.

O mapa inicial inclui:

- janelas de fechamento semantico;
- candidatos com evidencia contida/sobreposta;
- indexes sem disposicao proximos de candidatos;
- candidatos numericos, procedurais e reported cases;
- fronteiras de chunk e fim do episodio.

O auditor continua lendo os 998 segmentos, mas cruza fonte, cobertura e destino
na mesma passagem. O validator deve reconstruir 100% do transcript, ledger,
candidatos e calibracoes a partir do dossier.

Arquivos:

- `scripts/gold_final_audit_bundle.py`
- `scripts/finalize_gold_episode.py`
- `tests/test_gold_fastpath.py`
- `tests/test_gold_pipeline.py`

### OPT-007-P0-05 - Scaffold audit-to-patch source-canonical

Criar uma rota read-only que recebe o audit final e produz um intent de
remediacao, nunca um patch autoaprovado.

- segment ranges do finding resolvem quotes diretamente do transcript;
- candidatos citados recebem asserts dos manual reviews atuais;
- inserts recebem chunk_id, evidence e proximo ID livre deterministicamente;
- relacoes propostas sao emitidas de forma simetrica;
- o modelo preenche apenas claim, takeaway, tipo, temas, caveats e decisao de
  merge/insert;
- o mesmo preview simula numeric scope, ledger, relacoes, calibracao e dossier;
- incidental numerico em suporte aparece no inventario antes do apply.

Meta: audit report ate dossier remediado em 3-5 minutos, com um preview e um
apply.

Arquivos:

- `scripts/gold_review_patch.py`
- `scripts/run_gold_episode_fast.py`
- novo modulo focado somente se mantiver o patch generico
- `tests/test_gold_fastpath.py`

## P1 - medir corretamente e encurtar a cauda terminal

### OPT-007-P1-01 - Spans semanticos explicitos

Adicionar eventos duraveis de inicio/fim para:

- `semantic_reading_and_authoring`;
- `prelint_repair`;
- `final_sol_audit`;
- `remediation_authoring`;
- `final_sol_reaudit`;
- `closeout`.

O relatorio separa `semantic_wall_ms`, runtime, transicao e idle desconhecido.
Nao inventar tokens nem tempo interno do modelo.

### OPT-007-P1-02 - Reauditoria delta com prova integral

Depois de `changes_requested`, gerar um dossier delta contendo:

- findings e required actions;
- candidatos e ranges afetados antes/depois;
- relacoes e ledger afetados;
- hashes integrais de transcript, candidatos nao afetados, calibracao, packet e
  fingerprints;
- resultado do validator normal.

O reauditor verifica cada finding no delta e confirma os invariantes do packet.
Uma divergencia de hash obriga usar novamente o dossier integral.

### OPT-007-P1-03 - Completion e fechamento deterministico

Quando a reauditoria retornar `passed/0`:

- registrar audit, build complete e validate require-audit no mesmo processo;
- espelhar receipt, performance e resumo uma vez;
- gerar automaticamente a tabela de tempos e links da retrospectiva;
- respeitar `additional_verify_required=false` e encerrar.

## Regressoes obrigatorias

1. `exec-after` sempre usa cwd Linux certificado.
2. Drift do checkout depois do StartEpisode nao troca o runtime do run atual.
3. Mutacao do snapshot Linux bloqueia antes de escrita.
4. Number raw por segment/span copia `70 people` literalmente.
5. Chave compacta desconhecida aparece no inventario completo.
6. Fixture inicial do piloto 006 sinaliza as caudas 763-770 e 913-923.
7. G010/G011 gera grupo de contencao de evidencia sem criar relacao automatica.
8. Disposicao incidental valida fecha uma cauda; justificativa vazia nao fecha.
9. Dossier v3 reconstrui transcript e ledger integralmente.
10. Transcript inline preserva texto UTF-8 byte a byte.
11. Scaffold audit-to-patch faz zero writes e usa asserts source-canonical.
12. `100%` incidental em suporte e visivel antes do apply, sem record fabricado.
13. Reauditoria delta e rejeitada quando qualquer invariante integral muda.
14. Complete/passed protegido continua read-only.
15. Packet final continua com exatamente cinco arquivos.
16. Spans semanticos mais runtime, transicao e idle reconciliam o wall total.

## Ordem de implementacao

1. Fixar as fixtures do packet inicial de `p78Zv3_WCsM` em dados sinteticos
   equivalentes, sem usar gold real nos testes.
2. Implementar P0-01 para congelar o ambiente do benchmark.
3. Implementar P0-03 e provar que os tres findings aparecem pre-packet.
4. Implementar P0-02 para reduzir os ciclos de autoria/prelint.
5. Implementar P0-04 e validar reconstruibilidade integral.
6. Implementar P0-05 e a simulacao completa de remediation.
7. Implementar P1-01, P1-02 e P1-03.
8. Atualizar contrato, prompt e skill de forma concisa.
9. Rodar suite gold, py_compile, quick_validate e `git diff --check`.
10. Selecionar o proximo episodio da fila, congelar runtime e executar um novo
    benchmark sem editar codigo/documentacao durante a janela.

## Criterios de aceite

- os tres findings do piloto 006 seriam visiveis antes do packet inicial;
- nenhum warning semantico vira correcao automatica;
- uma unica passagem de leitura continua cobrindo todo o transcript;
- prelint oficial chega limpo em uma chamada no fixture canonico;
- remediation equivalente usa um preview e um apply;
- runtime permanece na mesma execution signature ate completion;
- hard blockers, quote, numbers, relations, ledger, calibration e fingerprints
  mantem ou aumentam a cobertura atual;
- suite gold completa passa no Python 3.12 WSL;
- nenhum episodio gold real e alterado durante a implementacao;
- proximo benchmark termina `complete/passed/0` antes da resposta final.

## Orcamento do proximo benchmark

| Etapa | Meta |
| --- | ---: |
| StartEpisode | 5-10s |
| Leitura integral e payload | 6-8m |
| Fechamento semantico e prelint | 45-90s |
| One-shot e dossier | 5-15s |
| Auditoria Sol integral | 6-8m |
| Remediation, se necessaria | 3-5m |
| Reauditoria e completion | 45-75s |
| Fechamento documental | 1-2m |

Metas terminais:

- 13-18 minutos sem finding;
- 17-23 minutos com uma remediacao focal;
- zero finding repetido das classes adjacency recall, scope continuation ou
  evidence containment.

## Evidencia de implementacao

- runtime por job vinculado a receipt e `execution_signature`; drift posterior
  da fonte Windows nao troca o run e mutacao do snapshot Linux bloqueia;
- compact v3 copia `numbers.raw` por segmento/span ou ocorrencia e devolve
  `repair_scaffold` completo;
- autocheck publica `semantic_closure_index` e exige disposicoes explicitas na
  fast lane, sem criar claims ou relacoes;
- dossier Sol `3.0.0` usa ordem candidate-first, transcript integral com ledger
  inline e validacao de transcript, candidatos, ledger e calibracao;
- audit scaffold e reaudit delta sao read-only e source-canonical; drift de
  invariantes rejeita o delta;
- spans semanticos explicitos reconciliam o wall com runtime e gaps;
- contrato, prompt e skill foram sincronizados;
- 148 testes gold passaram no Python 3.12 WSL em temp Linux isolado.

## Resultado do benchmark real

- episodio: `beFYVzSv2bw`;
- escala: 1.989 segmentos, 20 chunks e 589 sinais;
- resultado terminal: `complete/passed/0`, 37 IDs unicos e packet exato de cinco
  arquivos;
- fingerprints protegidos: preservados;
- calibracao: `5/12`, minimo 3, status `pass`;
- wall ate o receipt terminal: `1h31m12s`;
- comandos deterministas registrados: `4,28s`;
- leitura e autoria: `13m05s`;
- reparo de prelint: `25m13s`;
- auditoria Sol inicial: `19m39s`;
- remediacao, reauditoria e completion: aproximadamente `29m53s`.

O piloto validou runtime congelado, patch source-canonical, dossier integral,
completion atomico e preservacao de qualidade, mas nao atingiu a meta de 18-30
minutos. O fechamento semantico gerou 80 superficies e o scaffold de remediacao
nao antecipou multiplicidade numerica por ocorrencia; a reauditoria delta tambem
rejeitou inserts validos como drift de invariantes e exigiu o dossier integral.
Esses tres pontos ficam registrados na retrospectiva e em `process-learnings`.
