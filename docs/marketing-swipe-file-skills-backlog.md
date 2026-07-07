# Backlog De Skills De Processo - Marketing Swipe File (EPIC MSF-S)

Data de criacao: 2026-07-07

## 1. Objetivo

Transformar a base de insights em skills de processo de marketing (copy de
VSL, anuncios, oferta, quiz etc.) que alimentam agentes especializados, com
retroalimentacao continua conforme novos episodios e materiais entram no
pipeline.

Este documento complementa:

- `docs/marketing-swipe-file-remediation-backlog.md` (gates R1-R3)
- `docs/process-taxonomy.md` (vocabulario de processos)
- `docs/marketing-swipe-file-full-backlog.md` (series A-M; este epico detalha
  as camadas 6-8 do principio de execucao)

Regra de execucao: nenhuma tarefa MSF-S entra em uso antes dos gates R2 e R3.
A ordem continua sendo EPIC R2 (MSF-R09/MSF-R10), depois EPIC R3
(MSF-R11/MSF-R12/MSF-R13), e so entao MSF-S. Skill alimentada por base nao
curada reproduz o defeito v1. Agentes so depois de skills validadas
individualmente.

## 2. Anatomia de uma skill de processo

Cada skill e um diretorio `skills/msf-process-{slug}/` contendo:

1. `SKILL.md`: playbook do processo sintetizado dos insights curados
   (frameworks, principios, erros comuns), com citacao de `insight_id` em
   cada afirmacao nao-obvia (Artigo IV - No Invention).
2. `retrieval.md`: receita de retrieval - quais `process_tags` consome,
   filtros, como montar o pack de contexto para um briefing.
3. `templates/`: esqueletos de output (ex.: estrutura de VSL, matriz de
   angulos de anuncio).
4. `rubric.md`: rubrica de avaliacao especifica do processo, aplicada pelo
   avaliador LLM do MSF-R09.
5. `examples/`: 1+ exemplo real de briefing -> output aprovado.

Definition of Done de qualquer skill:

- Gerou output real a partir de briefing de teste.
- Output avaliado pelo avaliador honesto (R09) contra a rubrica propria.
- Output com skill vence ou empata com baseline sem skill em teste cego
  (metodo do MSF-R10, juiz externo ao gerador).
- Toda afirmacao do playbook rastreia a insight curado ou e marcada como
  pratica generica.

## 3. Selecao por densidade (medida em 2026-07-07)

Base v2 (207 insights, 15 episodios, 100% com process_tags):

| Processo | v2 | v1 (sinal futuro) |
|---|---|---|
| construcao-oferta | 102 | 580 |
| copy-vsl | 73 | 315 |
| prova-depoimentos | 54 | 282 |
| precificacao | 50 | 484 |
| mecanismo-big-idea | 46 | 205 |
| produto-low-ticket | 42 | 404 |
| arquitetura-funil | 39 | - |
| copy-anuncios | 31 | 364 |
| headlines-hooks | 27 | 201 |
| teste-variacao-criativos | 24 | 159 |
| quiz | 21 | 179 |

Primeira leva (densidade + prioridade do owner): copy-vsl,
construcao-oferta (absorve precificacao), copy-anuncios (absorve
headlines-hooks e teste-variacao), produto-low-ticket, quiz.

Adiadas por densidade insuficiente na v2 atual: trafego-meta,
trafego-google-youtube, video-anuncio, imagem-anuncio, copy-carta-vendas,
copy-email, seo. Entram na segunda leva apos backfill dos 508 chunks
restantes e processamento dos assets da academy (aulas de Facebook Ads,
criativos e videos brutos de anuncio cobrem exatamente esses processos).

## 4. Backlog

### MSF-S01 - Contrato e template de skill de processo

Prioridade: `P1`
Tipo: `skill`
Status: `blocked` (gate R3)

Escopo:

- Criar template de diretorio de skill (secao 2) e schema/checklist de
  validacao de skill.
- Definir formato da citacao de insight_id no playbook.

Aceite:

- Template instanciavel; checklist cobre o Definition of Done da secao 2.

Dependencias: gates R1 (done), R2, R3.

### MSF-S02 - Retrieval por process_tags

Prioridade: `P1`
Tipo: `script`
Status: `blocked` (gate R3)

Escopo:

- Estender `search_insights.py` e `generate_strategy_pack.py` com filtro
  `--process-tags`, consumindo `curated_insights` como fonte default.
- Manter penalidade de redundancia (MSF-R11) e cap por episodio.

Aceite:

- Pack gerado por processo contem apenas insights curados das tags pedidas,
  sem duplicacao dominante.

Dependencias: MSF-R11, MSF-R12.

### MSF-S03 - Skill: copy para VSL

Prioridade: `P1`
Tipo: `skill`
Status: `blocked`

Escopo: skill `msf-process-copy-vsl` conforme secao 2, consumindo
`process-copy-vsl` + modulos transversais (MSF-S08). Inclui leads, estrutura,
mecanismo, prova e CTA.

Aceite: Definition of Done da secao 2, incluindo teste cego contra baseline.

Dependencias: MSF-S01, MSF-S02.

### MSF-S04 - Skill: construcao de oferta

Prioridade: `P1`
Tipo: `skill`
Status: `blocked`

Escopo: skill `msf-process-construcao-oferta` (promessa, stack, bonus,
garantia, nome; absorve precificacao como capitulo do playbook).

Aceite: Definition of Done da secao 2.

Dependencias: MSF-S01, MSF-S02.

### MSF-S05 - Skill: copy para anuncios

Prioridade: `P1`
Tipo: `skill`
Status: `blocked`

Escopo: skill `msf-process-copy-anuncios` (hooks, angulos, scripts; absorve
headlines-hooks e teste-variacao-criativos como capitulos).

Aceite: Definition of Done da secao 2.

Dependencias: MSF-S01, MSF-S02.

### MSF-S06 - Skill: criacao de produto low ticket

Prioridade: `P1`
Tipo: `skill`
Status: `blocked`

Escopo: skill `msf-process-produto-low-ticket` (transformacao de entrada,
formato, esteira front-end -> backend).

Aceite: Definition of Done da secao 2.

Dependencias: MSF-S01, MSF-S02.

### MSF-S07 - Skill: criacao de quiz

Prioridade: `P1`
Tipo: `skill`
Status: `blocked`

Escopo: skill `msf-process-quiz` (perguntas, diagnostico, ponte para oferta,
fechamento de loops abertos).

Aceite: Definition of Done da secao 2.

Dependencias: MSF-S01, MSF-S02.

### MSF-S08 - Modulos transversais de copy

Prioridade: `P1`
Tipo: `skill`
Status: `blocked`

Escopo:

- `mecanismo-big-idea` e `prova-depoimentos` nao viram skills isoladas;
  viram modulos de retrieval compartilhados que as skills S03-S07 importam.

Aceite:

- Modulos consumidos por pelo menos duas skills da primeira leva sem
  duplicar conteudo de playbook.

Dependencias: MSF-S02.

### MSF-S09 - Validacao cega por skill

Prioridade: `P1`
Tipo: `qa`
Status: `blocked`

Escopo:

- Para cada skill da primeira leva: gerar output com e sem a skill (mesmo
  briefing, mesmo modelo), avaliar as cegas com o avaliador do MSF-R09 e a
  rubrica da skill. Juiz externo ao gerador.

Aceite:

- Cada skill aprovada individualmente; reprovadas voltam para iteracao de
  playbook/retrieval antes de uso.

Dependencias: MSF-R09, MSF-S03..S08.

### MSF-S10 - Agentes consumidores de skills

Prioridade: `P2`
Tipo: `agent`
Status: `blocked`

Escopo:

- Agentes especializados (copywriter de VSL, copywriter de anuncios,
  estrategista de oferta) que orquestram skills validadas. Somente apos S09.
- Gestao de trafego (Meta/Google) fica para quando houver skill de trafego
  (segunda leva) e ferramentas operacionais (MCP das plataformas).

Aceite:

- Agente produz output final usando skill + retrieval sem intervencao manual
  no meio, e o output passa na rubrica.

Dependencias: MSF-S09.

### MSF-S11 - Loop de retroalimentacao continua

Prioridade: `P2`
Tipo: `loop`
Status: `blocked`

Escopo:

- Formalizar o delta: novo episodio/asset -> pipeline v2 -> auditoria ->
  classificacao de process_tags -> curadoria delta -> refresh de packs e
  playbooks afetados (somente skills cujas tags receberam insights novos).
- Versionar playbooks para que refresh nao destrua ajustes manuais.

Aceite:

- Um episodio novo processado dispara atualizacao rastreavel apenas nas
  skills afetadas, com log do delta.

Dependencias: MSF-S03..S07, MSF-R14.

### MSF-S12 - Segunda leva de skills

Prioridade: `P2`
Tipo: `skill`
Status: `blocked`

Escopo:

- trafego-meta, trafego-google-youtube, video-anuncio, imagem-anuncio,
  copy-carta-vendas, copy-email, seo - conforme densidade pos-backfill e
  pos-assets da academy atingir massa critica (sugestao: 20+ insights
  curados por processo).

Aceite:

- Mesma anatomia e Definition of Done da primeira leva.

Dependencias: MSF-R14, MSF-R15, MSF-S09.

### MSF-S13 - Anotacoes de outcome de campo

Prioridade: `P3`
Tipo: `data`
Status: `blocked`

Escopo:

- Registrar resultados reais (copy que converteu, criativo vencedor, quiz
  com melhor completude) como evidencia de peso maior ligada aos insights
  usados, no schema reservado pelo MSF-R16.
- Outcome de campo passa a influenciar ranking de retrieval das skills.

Aceite:

- Pelo menos um ciclo real: output publicado -> resultado registrado ->
  ranking ajustado.

Dependencias: MSF-R16, MSF-S10.

## 5. Ordem executiva

1. Fechar EPIC R2 (MSF-R09/MSF-R10) e depois EPIC R3
   (MSF-R11/MSF-R12/MSF-R13), pre-requisito de tudo.
2. MSF-S01 + MSF-S02 (fundacao) -> MSF-S08 (modulos) -> S03..S07 em ordem de
   densidade: S04 (oferta), S03 (VSL), S05 (anuncios), S06 (low ticket),
   S07 (quiz).
3. MSF-S09 valida a leva; MSF-S10 cria agentes; MSF-S11 liga a
   retroalimentacao.
4. Segunda leva (S12) quando o backfill e os assets da academy elevarem a
   densidade dos processos adiados.
