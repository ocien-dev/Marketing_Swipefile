# MSF-R20 Gold Runtime Pilot 008 - Plano de Otimizacao

Status: implemented; real benchmark pending
Base: retrospectiva de `eCaODMtU5GY`
Objetivo do proximo benchmark: reduzir o episodio de porte medio para 17-23
minutos sem finding, ou 22-30 minutos com uma remediacao focal, preservando a
qualidade terminal `complete/passed/0`.

## Principios inegociaveis

1. A leitura cronologica integral continua obrigatoria.
2. Quotes e raw literais nunca sao normalizados ou fabricados.
3. Heuristicas geram superficies de revisao, nunca candidatos, relacoes ou
   disposicoes automaticas.
4. Auditoria final permanece em `gpt-5.6-sol/high`, source-complete e unica.
5. Checks read-only, asserts, receipts, atomicidade e fingerprints permanecem.
6. O runtime gold continua Linux-native; nao ha fallback para Python Windows.
7. A meta de tempo nao autoriza reduzir recall, caveats ou cobertura numerica.

## P0 - eliminar os loops observados

### OPT-008-P0-01 - Fechamento semantico por risco e lineage

Substituir a lista plana de warnings por dois niveis:

- `must_close`: trajetoria numerica, outcome, before/after, comparador,
  counterexample, limitacao, continuacao de mecanismo, claim sem suporte e
  borda adjacente material;
- `audit_only`: promo/interviewer, proximidade lexical, sobreposicao incerta e
  ambiguidade editorial que nao afeta estrutura.

Requisitos:

- deduplicar superficies pelo mesmo lineage de candidato/range/proposicao;
- nunca permitir disposition em massa `incidental` para cluster com numero,
  resultado, mecanismo, proeminencia ou score de risco alto;
- item `must_close` exige candidato equivalente ou justificativa source-backed;
- categoria `audit_only` pode usar defer por grupo, mas continua visivel no
  packet e no dossier;
- target: no maximo 25 itens `must_close` e 60 grupos totais para episodio de
  700-1.300 segmentos.

Fixtures obrigatorias: trajetoria 2023/G049, comparador R$10 mil/G030,
demonstracao falha/G008 e sustentacao 10-12 meses/G038.

Arquivos candidatos:

- `scripts/gold_review_autocheck.py`;
- `scripts/run_gold_episode_fast.py`;
- `scripts/gold_extraction_common.py`, apenas helpers puros;
- `tests/test_gold_fastpath.py`.

### OPT-008-P0-02 - Matriz numerica e de trajetoria antes do prelint oficial

Gerar uma matriz candidato-ocorrencia a partir de evidencia minima, suporte e
janelas adjacentes:

- `segment_id`, literal, span, valor, min/max, unidade, periodo, role e status;
- correspondencia entre linguagem do claim e records estruturados;
- sequencias completas, comparadores, anos contextuais e before/after;
- deteccao de contradicao `raw`/value/unit, como `raw=30` com `value=2 minutes`;
- disposicao explicita `incidental`, `context`, `disputed_asr_not_claim` ou
  record estruturado.

O contexto compacto deve expor a matriz e o compilador deve emitir um unico
manifesto de reparo esparso. O prelint oficial so inicia quando compiler issues
e lacunas numericas materiais estiverem zerados.

Fixtures obrigatorias: G027 com R$6k -> R$2,5k, G039 `30` versus dois minutos,
G049 com ano 2023 e G008 com numero disputado por ASR.

### OPT-008-P0-03 - Fechamento claim/evidence e counterexample

Para cada candidato, comparar os elementos semanticos do `source_claim` com a
evidencia realmente anexada:

- atos, mecanismos, atores, condicoes, limitacoes e resultados;
- continuacoes nas proximas uma a tres unidades semanticas;
- negacao, caso falho, excecao ou caveat que limite a proposicao;
- itens mencionados no claim mas ausentes de minimal/support evidence.

O sistema deve sinalizar G027/612-616 e G008/187 antes do primeiro packet, sem
reescrever o claim automaticamente.

### OPT-008-P0-04 - Dry-run consolidado antes do primeiro preview oficial

Adicionar uma rota local pura que execute, em memoria:

1. compiler e vocabulario;
2. matriz numerica;
3. claim/evidence closure;
4. adjacency e counterexample closure;
5. ledger preview, relations e calibration structure;
6. deduplicacao e risk tiers.

Saida: um repair manifest unico, esparso e source-canonical. O apply permanece
proibido. Meta operacional:

- uma chamada oficial de prelint diagnostica;
- uma chamada limpa de confirmacao;
- no maximo uma terceira chamada se surgir decisao semantica genuinamente nova.

### OPT-008-P0-05 - Envelope de auditoria Linux-native

Eliminar transporte por UNC, `/mnt/c`, OneDrive, `C:\\tmp` ou codificacao ad hoc.

- o compositor de audit recebe o julgamento final e grava diretamente no job
  Linux por stdin/arquivo Linux-native;
- `record_gold_external_audit --check` consome o mesmo arquivo;
- o mirror Windows recebe o audit apenas depois do receipt terminal;
- registrar hashes fisico e semantico em ambos os destinos;
- target de transporte e validacao: menos de dois segundos.

Arquivos candidatos:

- `scripts/run_gold_episode_fast.py`;
- `scripts/complete_gold_episode.py`;
- `scripts/invoke_gold_wsl.ps1`, apenas launcher explicito se necessario;
- testes de integracao WSL com paths contendo OneDrive.

### OPT-008-P0-06 - Delta de reauditoria canonico

Corrigir a classe ainda aberta de invariantes:

- affected IDs = IDs explicitos do audit + diff real before/after + inserts cuja
  evidencia intersecta ranges do finding;
- inserts de findings sem `candidate_ids` devem ser afetados, nunca
  `unaffected_candidates`;
- fingerprints comparam os quatro mapas de conteudo e excluem `verified_at`;
- transcript imutavel compara apenas `clean_index`, `start`, `duration` e
  `text`; ledger derivado pode mudar nos ranges afetados;
- calibracao e candidatos nao afetados usam hash semantico, sem metadata de
  build/packet;
- o delta gera prova integral machine-verifiable e aciona dossier completo
  somente diante de divergencia real.

Fixture obrigatoria: remediacao completa de `eCaODMtU5GY`, incluindo novo G049,
deve passar sem helper customizado.

## P1 - acelerar auditoria e medir o trabalho real

### OPT-008-P1-01 - Spans semanticos obrigatorios

Instrumentar inicio/fim de:

- leitura e autoria inicial;
- reparo de prelint;
- auditoria Sol inicial;
- autoria de remediacao;
- reauditoria Sol;
- closeout.

O relatorio deve usar `unattributed_gap_ms` quando um span faltar, nunca chamar
esse intervalo de idle. Runtime de comandos, transicoes e wall semantico devem
reconciliar o total dentro de tolerancia de um segundo.

### OPT-008-P1-02 - Risk brief compacto e sem repeticao

Preservar o dossier integral, mas reorganizar a entrada da auditoria:

- mapa inicial ordenado por risco material;
- numeros, trajectories, before/after, counterexamples e claim-support primeiro;
- warnings dispostos agrupados por lineage, sem repetir texto do transcript;
- links por clean index para a unica passagem source-complete;
- risk brief menor que 50 KB; o atual tinha 136 KB.

Meta: auditoria Sol de episodio 700-1.300 segmentos em 6-8 minutos, mantendo a
capacidade de encontrar os seis findings deste piloto.

### OPT-008-P1-03 - Closeout guiado pelo receipt terminal

- quando completion receipt validar status, audit, packet, fingerprints e IDs,
  nao executar verificacao WSL adicional;
- gerar automaticamente a tabela de tempos e o esqueleto da retrospectiva;
- espelhar somente os artefatos finais uma vez;
- target de closeout posterior ao receipt: menos de 15 segundos.

## P2 - reduzir friccao autoral sem inventar semantica

### OPT-008-P2-01 - Scaffold de vocabulario fechado

Expor no contexto as opcoes canonicas proximas para themes desconhecidos, sem
fallback automatico. `storytelling`, `competitive_analysis`,
`affiliate_marketing` e `product_development` viram fixtures para sugestao
explicita e decisao humana.

### OPT-008-P2-02 - Referencia numerica estavel

Substituir ordinal fragil de `source_occurrence` por `segment_id` + span/literal
source-canonical. O compilador copia o `raw` e rejeita ambiguidade em vez de
selecionar ocorrencia aproximada.

## Ordem de implementacao

1. Congelar fixtures sinteticas equivalentes aos seis findings e aos dois
   falsos drifts de reauditoria.
2. Implementar P0-02 e P0-03; provar que os seis findings aparecem antes do
   packet.
3. Implementar P0-01 para reduzir o inventario sem esconder risco material.
4. Implementar P0-04 e limitar os previews oficiais a no maximo tres.
5. Implementar P0-06 e remover a necessidade do helper de invariantes.
6. Implementar P0-05 e provar round-trip Linux-native em path com OneDrive.
7. Implementar P1-01, P1-02 e P1-03.
8. Implementar P2-01/P2-02 somente depois dos gates de qualidade P0.
9. Atualizar contrato, prompt e skill de forma concisa.
10. Rodar suites gold completas, `py_compile`, quick validate da skill e
    `git diff --check` no WSL.
11. Executar o proximo episodio da fila sem editar runtime/documentacao durante
    a janela do benchmark.

## Regressoes obrigatorias

1. A trajetoria 13 ofertas/~10 sucessos/>R$1m gera `must_close`.
2. Comparador R$10 mil omitido bloqueia fechamento semantico.
3. `raw=30` com `value=2 minutes` e inconsistencia explicita.
4. Claim com atos ausentes da evidencia gera claim-support closure.
5. Counterexample adjacente nao capturado gera `must_close`.
6. Duracao 10-12 meses omitida aparece na matriz numerica.
7. Warning promo/interviewer genuino permanece `audit_only`.
8. Bulk disposition nao fecha cluster numerico de alto risco.
9. Dry-run consolidado faz zero writes e retorna inventario completo.
10. Audit envelope nasce no job Linux e o mirror ocorre depois do terminal.
11. Insert sem candidate ID explicito entra no affected set pelo range/diff.
12. `verified_at` nao invalida fingerprints de conteudo identico.
13. Ledger derivado pode mudar em ranges afetados sem simular transcript drift.
14. Spans mais runtime e transicoes reconciliam o wall total.
15. Risk brief reduzido ainda permite encontrar os seis findings do fixture.
16. Packet final continua com exatamente cinco arquivos e fingerprints 4/4.

## Criterios de aceite

- os seis findings do piloto 008 seriam apresentados como `must_close` antes do
  primeiro packet;
- nenhum warning de baixo risco e promovido a hard blocker;
- nenhum claim, relacao, numero ou disposition e criado automaticamente;
- no maximo tres prelints oficiais no benchmark real;
- transporte do audit menor que dois segundos e sem `/mnt/c`/UNC;
- reauditoria delta passa a fixture de insert G049 sem helper ad hoc;
- auditoria final continua Sol/high e source-complete;
- suite gold completa passa no WSL;
- nenhum episodio real e alterado durante a implementacao;
- proximo benchmark termina `complete/passed/0` antes da resposta final.

## Orcamento do proximo benchmark

| Etapa | Meta |
| --- | ---: |
| Start/contexto | 5-10s |
| Leitura integral e payload | 10-12m |
| Fechamento e prelint | 4-7m |
| One-shot e dossier | <5s |
| Auditoria Sol integral | 6-8m |
| Transporte do audit | <2s |
| Remediacao, se necessaria | 3-5m |
| Reauditoria e completion | 1-2m |
| Closeout posterior ao receipt | <15s |

Meta terminal: 17-23 minutos sem finding ou 22-30 minutos com uma remediacao
focal, sem regressao de recall, evidencia, numeros, ledger ou calibracao.

## Evidencia de implementacao

Implementado em 2026-07-17 sem leitura ou escrita de episodio real:

- risk tiers `must_close`/`audit_only`, lineage e source-scoped disposition;
- matriz numerica com adjacencias, trajetorias e coerencia `raw/value`;
- claim-support e counterexample closure antes do packet;
- `--dry-run` puro e manifesto consolidado de reparo;
- envelope de audit UTF-8/base64 materializado no job Linux;
- delta canonico com insert por range/diff e fingerprints sem metadata volatil;
- spans semanticos e gaps sem atribuicao separados de idle;
- risk brief por lineage, indice numerico compacto e limite de 50 KB;
- sugestoes fechadas de vocabulario e `source_literal` estavel.

Validacoes no clone Linux-native Ubuntu 24.04:

- 179 testes gold passaram;
- `py_compile` passou nos modulos alterados;
- `quick_validate` da skill retornou `Skill is valid!`;
- `git diff --check` passou;
- paridade Windows/Linux passou com zero conflitos.

O proximo gate e executar um episodio novo da fila como benchmark congelado,
sem editar runtime ou documentacao durante a janela medida.
