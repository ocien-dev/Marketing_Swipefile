# Retrospectiva — Gold Runtime Pilot 004

## Episodio

- `academyhls-861b5d3a-0b6e-4547-971e-750a33985306`
- `Assertividade na Criacao de VSLs - Felipe Ferreira - 05/12/2024`
- categoria da fila: `VSL`
- duracao: 6.833 segundos
- 2.349 segmentos, 25 chunks e 643 sinais preparados

O seletor percorreu a fila persistente e escolheu o primeiro episodio com fonte
completa. Os quatro itens anteriores estavam sem fonte disponivel. A selecao e o
bootstrap levaram cerca de 19,5 segundos; o bootstrap deterministico isolado
levou aproximadamente 298 ms.

## Resultado gold

- 25/25 reviews integrais
- 43 candidate IDs unicos
- autocheck final com `hard_blockers=0`
- calibracao `pass`, 3/3 acima do minimo
- packet com exatamente cinco arquivos
- fingerprints protegidos 4/4 iguais
- auditoria final `gpt-5.6-sol/high`: `passed`, `open_findings=0`
- lifecycle final: `complete/passed`

## O que funcionou

1. A fila eliminou a analise manual de selecao; apenas validou a primeira fonte
   realmente disponivel.
2. O runtime Linux executou compilacao, recorder, autocheck, finalizador, build e
   validadores em centenas de milissegundos ou poucos segundos por chamada.
3. O autocheck bloqueou um numero material ausente depois de ampliar a evidencia
   de G015 e permitiu corrigir isso antes do packet definitivo.
4. A auditoria Sol encontrou problemas semanticos reais que os gates
   deterministas nao capturam: recall, hierarquia, modelagem de numeros e
   equivalencia claim/evidence.
5. O dossier final ficou abaixo de 250 KB mesmo incluindo transcript, 43
   candidatos, calibracoes e as 1.396 entradas de ledger agrupadas.

## O que falhou

1. O primeiro dossier declarava o ledger, mas nao trazia suas entradas. Isso
   inviabilizou a auditoria semantica e exigiu corrigir o gerador compartilhado.
2. O launcher PowerShell aceitou argumentos soltos como parametros posicionais.
   A interface foi endurecida para exigir `-CommandArguments` explicito.
3. O formato compacto de episodio ignora chunks ja revisados. Na remediacao, o
   prelint mostrou zero drafts e nao atualizaria os reviews existentes.
4. Depois da atualizacao canonica dos reviews, o one-shot tentou reconciliar um
   receipt historico de zero drafts e parou antes do build. O finalizador oficial
   foi chamado diretamente por helper job-local, sem novo recorder.
5. O PATH herdado no WSL tentou executar o `rg` empacotado de WindowsApps. A
   verificacao foi refeita com ferramenta Linux nativa.

## Decisoes para o proximo episodio

- Manter fila persistente, bootstrap Linux e packet final unico.
- Manter dossier com ledger integral e validacao de reconstrucao.
- Manter auditoria Sol somente na fase final.
- Generalizar uma rota oficial de remediacao pos-auditoria para reviews completos,
  com preservacao de IDs e finalizacao sem recorder de zero drafts.
- Sanitizar o PATH do launcher WSL para impedir resolucao de binarios Windows.

O piloto validou a qualidade do fluxo, mas nao atingiu a meta de tempo
end-to-end por causa das duas rodadas de remediacao semantica e das lacunas da
rota pos-auditoria. O custo deterministico permaneceu baixo; o custo dominante
foi leitura e julgamento semantico.

## Linha do tempo completa

O primeiro comando duravel iniciou em `2026-07-16T02:41:16.245Z`. O julgamento
final passou em `2026-07-16T04:24:43.082Z`, depois de 1h43m27s. A retrospectiva
foi gravada aproximadamente as `2026-07-16T04:36:11Z`; a janela observavel do
epico foi, portanto, de cerca de 1h54m55s.

| Etapa | Tempo |
| --- | ---: |
| Selecao e bootstrap | 1m58s |
| Leitura integral e payload inicial | 11m10s |
| Cinco prelints e primeiro one-shot | 24m47s |
| Auditoria final 1 | 9m12s |
| Remediacao 1 | 20m37s |
| Auditoria final 2 | 6m40s |
| Remediacao 2 | 23m57s |
| Auditoria final 3 | 7m00s |
| Completion e documentacao | 9m33s |

As 13 invocacoes registradas do launcher somaram apenas 108,32 segundos. O
primeiro one-shot consumiu 754,68 ms internos e o one-shot de remediacao,
687,20 ms. O excesso de tempo nao veio do processamento Linux, mas dos ciclos
semanticos e da ausencia de uma rota oficial para remediar reviews completos.

O piloto 003 tinha 1.233 segmentos; este tinha 2.349, aumento de 90,5%. A
quantidade de chunks era parecida (21 contra 25), mas a carga real de leitura
nao era. A comparacao correta preserva metas proporcionais ao volume.

## Reversao seletiva

Nao reverter WSL, fila, contexto compacto, one-shot ou dossier integral.
Reverter somente a reentrada de um episodio completo no recorder de chunks
pendentes. O plano e a implementacao estao em
`msf-r20-gold-runtime-pilot-004-optimization-plan.md`.
