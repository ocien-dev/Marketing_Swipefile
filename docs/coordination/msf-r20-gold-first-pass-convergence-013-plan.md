# MSF-R20 Gold First-Pass Convergence 013 - Plano de implementação

Status: implemented_pending_final_sol_authorization
Owner: chat ativo
Base: `msf-r20-wave-007-process-analysis-013.md`
Arquitetura: `chronological_hybrid_v1`
Escopo: eliminar retrabalho semântico P0 e remediações aditivas sem novo gate,
brief, helper, papel ou schema público

## Objetivo

Fazer o primeiro packet chegar à fase final Sol com números e calibrações já
semanticamente fechados e, se houver finding residual, resolvê-lo em uma única
substituição transacional.

Meta observacional para uma wave de dois episódios de 900-1.300 segmentos:

- 55-75 minutos de wall com até uma remediação por episódio;
- no máximo 2 findings por episódio no primeiro veredito;
- zero finding numérico ou de calibração depois de prelint aprovado;
- no máximo uma remediação e dois dossiers por episódio;
- `complete/passed/0`, packet 5/5 e fingerprints preservados.

## Causas confirmadas

1. Dez dos 19 findings iniciais da wave 007 eram numéricos.
2. Seis dos oito findings restantes depois da remediação 001 continuavam
   numéricos.
3. O prelint aceitou raws materiais como `count/value=null`.
4. O helper de remediação adicionou records tipados sem retirar records opacos.
5. `calibration_decisions` existe e é validado no manifesto, mas
   `manifest_to_compact_payload()` não o inclui no payload compilado.
6. Duplicatas do cold open precisaram ser incorporadas à evidência/ledger do
   candidato para fazer a cobertura derivada passar.
7. O delta focal foi rejeitado quando ledger ou candidatos dependentes mudaram
   fora do range literal do finding; o fallback integral só foi escolhido
   depois da tentativa.
8. Spans da primeira reauditoria ficaram abertos durante a remediação seguinte.
9. A wave produziu 109 arquivos transitórios e 4/3 revisões de dossier.

## Princípios

- fortalecer funções e contratos existentes; não criar outro gate;
- o manifesto é a única fonte autoral;
- fonte verbatim nunca é normalizada;
- número material não pode passar como token opaco;
- ambiguidade ASR é estado válido quando explícita, nunca valor inventado;
- remediação substitui o estado afetado, nunca acumula versões semânticas;
- dependências são fechadas antes da escrita;
- auditoria Sol/high e leitura cronológica integral permanecem obrigatórias;
- toda adição deve remover uma tentativa, uma rota ou uma representação
  paralela.

## HI-013-01 - Fechamento semântico P0 na invariante existente

### Causas eliminadas

- `count/value=null` em ocorrência material;
- raw com escala desconhecida recebendo valor concreto;
- duplicação de records opacos e tipados para a mesma ocorrência;
- decisão de calibração autoral sem efeito no resultado derivado;
- evidência ampliada apenas para satisfazer cobertura de duplicata.

### Implementação

1. Estender a função source-complete compartilhada por prelint, finalizer e
   dossier. Para cada ocorrência numérica material exigir exatamente uma das
   disposições:
   - ocorrência tipada com raw, valor/faixa, unidade, papel, status,
     multiplicidade e caveat quando inferida/atribuída;
   - ocorrência ASR explicitamente ambígua, raw preservado e valor/faixa nulos;
   - exclusão incidental source-scoped com justificativa.
2. Classificar como material, no contrato já existente, ocorrências ligadas a
   claim, comparação, custo, preço, orçamento, resultado, threshold, teste,
   período, ratio, escala, passo ou trajetória. Não criar score novo.
3. Rejeitar:
   - `unit_kind=count` por fallback quando a fonte expressa moeda, percentual,
     ratio, tempo ou multiplicidade;
   - valor não nulo quando caveat declara escala ASR desconhecida;
   - duas linhas com a mesma identidade de ocorrência fonte e funções
     incompatíveis;
   - raw material sem papel semântico.
4. Levar `calibration_decisions` pelo compilador do manifesto até a derivação
   final. A decisão só prevalece quando provar:
   - target real e fonte canônica existentes;
   - equivalência proposicional explícita;
   - anchor literal compatível;
   - candidate e source lineage atuais.
5. Representar duplicata como decisão de calibração e ledger `merged`, sem
   obrigar que o cold open vire minimal/support evidence do candidato canônico.
6. Remover a validação paralela que deixa a decisão no manifesto sem efeito no
   payload. Deve existir uma única autoridade derivada.
7. Emitir no repair inventory existente somente as ocorrências P0 abertas; não
   criar report, brief ou arquivo adicional.

### Critérios de aceite

- fixtures iniciais da wave 007 reproduzem os 10 findings numéricos e falham
  antes do primeiro write;
- fixtures finais dos dois episódios passam sem alteração semântica;
- `030` -> 0,30% passa somente com raw, status inferido e caveat ASR explícita;
- `r$ 2`/`10000` com escala desconhecida passam apenas com valor/faixa nulos;
- records tipados mais originals opacos da remediação 001 falham;
- decisões válidas das calibrações do cold open derivam `pass` sem ampliar
  evidence ranges;
- decisão de equivalência falsa continua bloqueada;
- nenhum schema gold público é alterado.

### Impacto mínimo exigido

Eliminar integralmente findings numéricos e de calibração do primeiro veredito
em uma reprodução defeituosa e evitar pelo menos uma remediação/auditoria na
wave congelada. Se isso não for demonstrado, a iniciativa não é promovida.

## HI-013-02 - Remediação substitutiva, dependency-closed e mensurável

### Causas eliminadas

- merge aditivo de number records;
- warning/calibration/ledger corrigidos em versões sucessivas;
- tentativa de delta focal conhecida como insuficiente;
- múltiplos manifests numerados e replacement-checks por episódio;
- span de auditoria aberto durante trabalho de outra fase.

### Implementação

1. Tornar a revisão completa do candidato afetado a unidade de substituição.
   O manifesto entrega a matriz final; o compilador não preserva rows anteriores
   ausentes da nova matriz.
2. Derivar antes do commit um impact closure com:
   - candidatos alterados;
   - source ranges minimal/support;
   - ledger rows afetadas;
   - ocorrências numéricas;
   - calibrações;
   - warnings;
   - relações e packet derivado.
3. Validar o closure contra o dossier before. Mudança dependente é incorporada
   ao scope; mudança não dependente bloqueia antes da escrita.
4. Decidir antes do commit:
   - delta focal quando todas as mudanças estão dentro do closure; ou
   - dossier integral quando o closure atravessa invariantes globais.
   Não executar uma tentativa de delta que já será rejeitada.
5. Em uma chamada existente: validar envelope/base, compilar manifesto,
   substituir reviews, rederivar ledger/calibração, finalizar, gerar um dossier
   e emitir o request escolhido.
6. Manter apenas `gold_authoring_manifest.json` no job. Para provenance,
   preservar no máximo o hash/snapshot before dentro do receipt transacional;
   não criar `v2`, `v3`, `pre` ou `replacement-check` repo-local.
7. Fechar o span de auditoria atomicamente quando o veredito é materializado.
   Uma nova leitura abre um novo span. Reusar os campos atuais; não adicionar
   dashboard ou comando manual.
8. Se houver falha posterior ao commit, o receipt declara exatamente o estado
   persistido e a rota de retomada sem repetir a escrita.

### Critérios de aceite

- fixture da remediação 001 não conserva records opacos removidos do manifesto;
- um finding numérico gera uma substituição, um finalizer, um build e um
  dossier;
- ledger/calibração/warning dependentes entram no closure sem causar
  `ledger_outside_findings` ou `changed_candidates_outside_findings` tardio;
- mudança realmente global escolhe dossier integral antes do commit;
- envelope/base stale causa zero write;
- no máximo um manifesto canônico e dois dossiers por episódio no caso com uma
  remediação;
- spans não se sobrepõem entre audit e authoring; reconciliação do wall difere
  menos de 1%;
- packets, fingerprints e historical provenance permanecem imutáveis durante
  a auditoria.

### Impacto mínimo exigido

Reduzir a reprodução da wave 007 de 3/2 remediações para no máximo uma por
episódio e remover pelo menos 50% dos artefatos transitórios não finais. Caso
contrário, a mudança deve ser revertida em vez de receber nova camada.

## Ordem de implementação

### Fase 0 - Baseline congelado

1. Congelar como fixtures somente as superfícies necessárias dos dossiers
   inicial, remediation-001 e final da wave 007.
2. Registrar hashes, 19/8/1/0 findings, number records e calibrações.
3. Criar testes que reproduzam as falhas sem copiar raw, packet ou transcript
   para o repositório.

Gate: zero escrita em gold real.

### Fase 1 - HI-013-01

Implementar fechamento numérico e autoridade de calibração na invariante
existente; apagar a validação paralela substituída.

Gate: fixtures defeituosas bloqueiam antes do write e fixtures finais passam.

### Fase 2 - HI-013-02

Implementar replacement semântico, impact closure, escolha antecipada de delta
ou dossier integral e fechamento atômico do span.

Gate: uma remediação, um commit, um finalizer, um dossier e medição reconciliada.

### Fase 3 - Regressão integral

- `py_compile` dos módulos alterados;
- suites dirigidas de manifest, prelint, source completeness, numeric coverage,
  calibration, remediation, delta, lifecycle e terminal identity;
- suite completa;
- `git diff --check`;
- validação read-only dos packets finais da wave 007.

Gate: zero regressão e zero escrita nos episódios protegidos.

### Fase 4 - Benchmark novo de dois episódios

Executar dois episódios novos, sequenciais e isolados, sem mudar código entre
eles salvo defeito de qualidade confirmado. Só iniciar a fase final Sol quando
os dois ramos estiverem source-complete e com hashes congelados.

Gate final:

- `complete/passed/0` nos dois;
- zero finding numérico/calibração após prelint aprovado;
- no máximo 2 findings por episódio no primeiro veredito;
- no máximo uma remediação e dois dossiers por episódio;
- nenhum manifest/check numerado repo-local;
- spans reconciliados com erro inferior a 1%;
- wall de 55-75 minutos para a wave com até uma remediação por ramo;
- packets 5/5 e fingerprints preservados.

## Go/no-go

Go somente para HI-013-01 e HI-013-02. Não iniciar uma terceira iniciativa
durante este épico.

No-go para:

- novo compilador semântico, inventário, score ou adaptador;
- novo brief, gate, helper, runner, papel, chat ou heartbeat;
- micro-otimização de seleção, Python, temp, PowerShell, prelint runtime,
  one-shot ou completion;
- reduzir transcript, chunks, candidatos, quotes ou auditoria Sol;
- novo campo de telemetria sem apagar uma medição/manual state existente;
- alterar schema público, master, curated, Supabase, commit, push ou deploy.

## Critério de encerramento

O épico termina apenas depois da implementação, regressão integral e benchmark
de dois episódios. Ganho de tempo sem `passed/0`, ou `passed/0` obtido com mais
camadas/artefatos, não conta como melhoria.
