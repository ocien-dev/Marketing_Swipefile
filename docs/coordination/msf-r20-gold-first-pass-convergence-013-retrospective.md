# MSF-R20 Gold First-Pass Convergence 013 - Implementacao e benchmark

Status: implemented_pending_final_sol_authorization
Data: 2026-07-18
Arquitetura: `chronological_hybrid_v1`
Escopo: HI-013-01, HI-013-02, regressao e benchmark real de dois episodios

## Resultado atual

As duas iniciativas de alto impacto foram implementadas. Os dois episodios
novos chegaram a packet source-complete com `hard_blockers=0`, calibracao
aprovada, uma unica persistencia/finalizacao e um unico dossier cada. O request
consolidado Sol/high esta selado com os hashes dos dois dossiers.

A fase final ainda nao foi executada. O runtime recusou, antes de qualquer
transmissao, enviar os dossiers locais privados ao servico externo do modelo
sem autorizacao explicita adicional do owner. Portanto o estado honesto dos
dois ramos permanece `awaiting_external_audit/pending_external`; nao ha alegacao
de `passed/0` ou `complete`.

## Implementacao entregue

### HI-013-01

- fechamento numerico P0 exige uma representacao material unica e tipada;
- escala ASR desconhecida so passa explicitamente, com raw e valor nulo;
- records opacos somados a records tipados sao rejeitados;
- `calibration_decisions` atravessa manifesto, payload, ledger, autocheck,
  build e dossier;
- duplicata equivalente de cold open deriva ledger `merged` sem poluir a
  evidencia do candidato canonico;
- o workbench reconhece os candidate IDs do ledger merged.

### HI-013-02

- remediacao substitui a revisao completa, sem conservar number rows removidas;
- impact closure inclui candidatos, ranges, ledger, numeros, calibracoes,
  warnings, relacoes e packet antes do commit;
- delta ou dossier integral e escolhido antes da escrita;
- stale envelope/base bloqueia com zero write;
- o veredito materializado fecha o span Sol atomicamente;
- o one-shot fecha a autoria ao ficar ready e uma fase nova fecha qualquer
  fase anterior no mesmo boundary, impedindo sobreposicao.

## Regressoes

- regressao dirigida 013: `15 passed`;
- regressao ampliada executada antes do benchmark: 315 casos existentes
  aprovados em grupos, contornando apenas a permissao do temp global do Windows;
- `py_compile`: aprovado;
- `git diff --check`: aprovado;
- validacao read-only dos dois dossiers protegidos da wave 007: aprovada;
- runtime canonico: Windows native, Python 3.12.13 e temp gravavel.

## Benchmark real

| Metrica | E01 `-46vMG3l8Jo` | E02 `0sB3ia6LIVM` |
| --- | ---: | ---: |
| Segmentos | 1.180 | 951 |
| Candidatos finais | 40 | 38 |
| Reviews | 21 | 18 |
| Leitura/autoria ate one-shot | 32m49,89s | 17m24,95s |
| One-shot total | 2,774s | 2,539s |
| Persistencia | 86,50ms | 74,91ms |
| Finalizer | 895,14ms | 787,17ms |
| Dossier | 471.229 B | 413.540 B |
| Writes/finalizers/builds/dossiers | 1/1/1/1 | 1/1/1/1 |
| Packet | 5/5 | 5/5 |
| Fingerprints before/after | iguais | iguais |

O wall desde o inicio do E01 ate o packet-ready do E02 foi 52m06,35s. O gate
consolidado foi aberto em 54m38,92s, dentro da borda inferior da meta de 55-75
minutos antes de contabilizar a auditoria final. As duas leituras foram
sequenciais; os spans job-local foram reconciliados aos timestamps factuais dos
eventos one-shot e nao se sobrepoem.

O runtime deterministico consumiu apenas 5,31s nos dois one-shots. O custo
continua concentrado em leitura/autoria e em reparos source-backed do primeiro
manifesto, nao em persistencia, finalizer ou dossier.

## Complexidade e convergencia

O ganho estrutural e material:

- wave 007: 3/2 remediacoes e 4/3 dossiers;
- benchmark 013 ate o gate Sol: 0/0 remediacoes e 1/1 dossier;
- arquivos job-local observados: 43 contra 109 na wave 007, reducao de 60,6%;
- nenhum manifesto/check numerado foi criado no repositorio;
- zero blocker numerico ou de calibracao depois do prelint aprovado.

Nem todo retrabalho desapareceu. O E01 exigiu oito prelint reports e o E02 sete
durante a autoria. Isso e muito inferior a remediar gold persistido e repetir
auditorias, mas mostra que a primeira composicao autoral ainda nao converge em
uma unica checagem. Nao foi criada nova iniciativa para mascarar esse custo: o
plano proibiu micro-otimizacao e o benchmark precisa primeiro receber o
veredito Sol para provar qualidade.

## Defeito encontrado no benchmark

Ao abrir o gate Sol, os spans de autoria continuavam abertos. O lifecycle foi
corrigido no contrato existente: o one-shot ready encerra autoria, o start de
uma nova fase fecha a anterior no mesmo timestamp e um start idempotente
reconcilia jobs antigos ao boundary ja registrado. Os dois jobs foram corrigidos
usando o `completed_at` factual do evento `apply_and_finalize`; nenhum gold,
packet, dossier ou fingerprint foi alterado.

## Gate pendente

Request consolidado:
`1121f2d96bbc09426792d396692dca2f00253a4eff938d2e4d1eaf2b3e344ed2`.

| Episodio | Physical SHA-256 | Semantic SHA-256 |
| --- | --- | --- |
| `-46vMG3l8Jo` | `f596e6a44e7e23f15ff682ff148be93be6f9c82757a0dee34a6bbeb247d19765` | `784a8f1d7d3982a94ed21e6e61a275c66b5ffb1183a1e5fd36cb6a8970bf6f7e` |
| `0sB3ia6LIVM` | `2b28e0a0288989a08f7bd7d973b7acb3d0a9617ff44e4e7cc7bba29490e51107` | `bb9225e2dee776379506a98f4e24524522bafd56cc2dfa4e64dafb1532276d70` |

A proxima acao indivisivel e autorizar explicitamente o envio desses dois
dossiers privados ao runtime externo `gpt-5.6-sol/high`. Apos o veredito, o
mesmo fluxo materializa os envelopes, remedeia no maximo uma vez se necessario,
executa o validador obrigatorio, deriva `complete/passed/0`, fecha o gate final
e atualiza esta retrospectiva.
