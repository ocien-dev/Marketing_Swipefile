# MSF-R20 Gold Runtime Pilot 010 - Plano de Otimizacao

Status: implemented; benchmark with a new episode pending
Base: analise do piloto 009 `NiT0-ABoVnk`
Escopo: reduzir autoria e auditoria sem adicionar gates ou mudar o schema gold

## Objetivo

Consolidar as melhorias que provaram valor e remover a camada manual que
consumiu o ganho do prelint. O proximo benchmark de 900-1.300 segmentos deve
terminar em 20-27 minutos sem finding ou 25-34 minutos com uma remediacao focal,
preservando `complete/passed/0` e a auditoria final Sol/high.

## Principios

1. Manter WSL, fila persistente, one-shot, atomicidade e receipt terminal.
2. Manter leitura cronologica integral e auditoria final source-complete.
3. Nao adicionar readiness, checkpoint, helper ou review intermediaria.
4. Heuristicas apenas priorizam; nao criam claims, numeros ou relacoes.
5. O primeiro packet deve melhorar semanticamente, nao apenas passar gates.
6. Medir leitura e composicao diretamente, sem inferir pelo gap.

## P0 - alto potencial

### OPT-010-P0-01 - Workbench de cobertura source-first

Gerar uma unica visao compacta antes da autoria com:

- todos os blocos cronologicos e seu estado `covered`, `merged`, `excluded` ou
  `unreviewed`;
- blocos materiais ainda sem candidato, priorizando economia, preco, trial,
  produto/roadmap, valor percebido, PMF, before/after, resultado e caveat;
- fronteiras e caudas adjacentes relevantes;
- link curto para a fonte canonica, sem repetir transcript.

O workbench substitui listas separadas de signal inventory, risk recall e
adjacency. Deve sinalizar os blocos 884-909, 957-972 e 987-993 do piloto 009
antes do primeiro apply.

Meta: ate 120 superficies, no maximo 30 `must_review`, artefato menor que 120
KB e zero perda de clean indexes.

### OPT-010-P0-02 - Binding claim/evidence/calibration

Para cada candidato, gerar uma linha canonica:

`candidate -> claim atoms -> evidence ranges -> numbers -> caveats -> targets`.

Bloquear apenas defeitos estruturais:

- claim atom sem evidencia;
- evidence range que aponta para outra proposicao;
- numero material da evidencia sem record ou disposition;
- target semanticamente equivalente ainda desligado;
- target ligado a candidato que nao expressa a mesma proposicao.

Ambiguidade real continua warning de auditoria. Fixtures obrigatorias: G049,
G051, G052 e calibration 989 do piloto 009.

### OPT-010-P0-03 - Payload e repair manifest unicos

Eliminar helpers job-local por fase. O runner deve produzir:

1. um payload autoral compacto;
2. um unico repair manifest esparso, se necessario;
3. um receipt de preview limpo consumido pelo apply.

O full prelint permanece persistido para depuracao, mas o workbench usado pelo
modelo deve ficar abaixo de 150 KB. Nenhum fluxo normal pode exigir scripts
como `refine_payload.py`, `close_residual.py` ou `close_warning_gate.py`.

### OPT-010-P0-04 - Dossier de auditoria em duas camadas

Preservar o dossier integral como prova, mas entregar ao Sol primeiro:

- indice de cobertura completo;
- tabela claim/evidence/number/caveat/calibration;
- blocos de risco nao cobertos;
- warnings agrupados por lineage;
- hashes e gates finais.

A segunda camada fornece janelas source-complete por clean index sem reabrir
arquivos ou repetir derivados. O mapa principal deve ficar entre 100 e 150 KB.

Meta: auditoria inicial de episodio medio em 6-9 minutos e capacidade de
reproduzir os cinco findings do piloto 009.

### OPT-010-P0-05 - Compilador audit-to-patch oficial

Transformar findings selados e fonte atual em scaffold transacional com:

- asserts copiados byte a byte do estado atual;
- quotes, ranges e raw source-canonical;
- matriz numerica completa do novo escopo de evidencia;
- inserts detectados por finding range;
- redirects de calibracao com target e candidato validados;
- preview do diff semantico antes do apply.

O compilador nao decide a correcao nem aplica automaticamente. Ele elimina
redigitacao, raw stale e helpers `build_audit_remediation.py` e
`check_remediation.py`.

Meta: autoria e check da remediacao em 2-4 minutos, uma aplicacao e nenhum
helper especifico do episodio.

### OPT-010-P0-06 - Telemetria de autoria sem burocracia

Adicionar marcadores automaticos, nao comandos extras, para:

- inicio/fim da leitura cronologica;
- composicao inicial;
- reparo de prelint;
- auditoria;
- autoria de remediacao;
- reauditoria;
- closeout.

O receipt deve reconciliar runtime, spans e gap nao classificado em ate um
segundo. Gap nao classificado acima de 10% do wall invalida apenas o benchmark,
nao o gold.

## P1 - somente depois de P0 verde

### OPT-010-P1-01 - Reuso do mapa semantico

O mesmo mapa source-first deve alimentar autoria, prelint, dossier e
remediacao. Recomputacoes podem atualizar hashes e estados, mas nao gerar uma
segunda taxonomia ou novos IDs de lineage.

### OPT-010-P1-02 - Orcamento de artefatos

- contexto model-facing: <= 180 KB;
- workbench de fechamento: <= 120 KB;
- resumo de prelint em stdout: <= 8 KB;
- mapa principal de auditoria: <= 150 KB;
- full reports e dossier integral continuam disponiveis fora da entrada
  primaria do modelo.

O limite nunca remove transcript, evidence ou ledger da prova persistida.

## Implementacao

1. Congelar fixtures equivalentes aos cinco findings do piloto 009.
2. Implementar o workbench de cobertura e provar reconstrucao de todos os
   clean indexes.
3. Implementar binding claim/evidence/calibration e as quatro fixtures.
4. Integrar o workbench ao payload compacto e ao dry-run existente.
5. Substituir os helpers de fechamento pelo repair manifest oficial unico.
6. Implementar o dossier em duas camadas e reproduzir os cinco findings.
7. Implementar o compilador audit-to-patch com check read-only e diff.
8. Adicionar spans automaticos e limites de artefatos.
9. Atualizar contrato, prompt e skill sem duplicar regras.
10. Rodar suites gold, `py_compile`, quick validate e `git diff --check` no WSL.
11. Executar um episodio novo de 900-1.300 segmentos com runtime congelado.

## Regressoes obrigatorias

1. Comparacao economica 884-888 aparece como bloco material nao coberto.
2. G049 incompleto sinaliza trial, capacidade e ciclo comercial ausentes.
3. G051 ligado a 948-949 falha por proposicao diferente de 957-965.
4. G052 ligado a evidencia antifraude falha para a proposicao de PMF.
5. Target 989 reconhece G052 e rejeita candidato apenas tematicamente proximo.
6. Warning promo/interviewer nao vira blocker.
7. Workbench reconstrui 100% dos clean indexes sem repetir transcript.
8. Payload limpo aplica com o mesmo receipt do preview.
9. Audit-to-patch copia raw e asserts atuais byte a byte.
10. Finding sem candidate ID inclui insert pelo range e diff.
11. Dossier em duas camadas permite reproduzir os cinco findings.
12. Packet continua com cinco arquivos e fingerprints iguais.

## Criterios de aceite

- os cinco findings do piloto 009 aparecem antes do primeiro packet nas
  fixtures;
- no maximo dois prelints oficiais no benchmark;
- nenhum helper Python especifico do episodio no caminho normal;
- contexto e mapas respeitam os orcamentos sem perder source completeness;
- auditoria inicial em 6-9 minutos para episodio medio;
- remediacao focal em 2-4 minutos;
- gap nao classificado menor que 10% do wall;
- `complete/passed/0`, packet 5 e fingerprints preservados;
- nenhum novo gate ou checkpoint operacional.

## Decisao de go/no-go

Implementar P0 tem alto potencial porque ataca 63% do wall semanticamente
classificado do piloto 009: auditoria inicial, autoria da remediacao e reparo de
prelint. P1 so entra se P0 reproduzir os cinco findings em fixture e reduzir a
superficie model-facing. Caso contrario, manter o pipeline atual e nao ampliar
a complexidade.

## Resultado da implementacao

- `semantic_workbench` agora reconstrui a fonte em blocos cronologicos,
  prioriza lacunas economicas/produto/resultado e vincula candidatos e targets.
- Prelint, brief e dossier 3.1 consomem a mesma taxonomia e o dossier integral
  continua source-complete.
- O scaffold audit-to-patch inclui ocorrencias numericas, evidencia/ranges,
  asserts de reviews e calibracoes e um unico template transacional.
- `StartEpisode` inicia automaticamente o span combinado
  `semantic_reading_and_authoring`; o prelint encerra a medicao existente.
- Ambiguidade semantica continua warning; somente defeitos estruturais ou itens
  materiais sem destino entram no fechamento obrigatorio.
- Validacao WSL: 163 testes passaram, `py_compile`, quick validate da skill e
  `git diff --check` passaram.
- O alvo de minutos e os orcamentos em episodio real permanecem como criterio
  do proximo benchmark; esta implementacao nao os declara atingidos sem prova.
