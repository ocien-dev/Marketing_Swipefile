# MSF-R20-GOLD-10-MINUTE-001 - Fast lane por episodio

Status: done - implementation and local quality gate passed
Owner: chat ativo
Production status: pre_production
Dados gold reais: somente leitura

## Problema

A qualidade gold justificou o reprocessamento, mas o caminho operacional ainda
repete estados demais. Na Wave 005 houve 22 gravacoes de batches, 14 patches e
8 builds para cinco episodios. O custo principal nao e o build final: e a
alternancia entre leitura, persistencia parcial, diagnostico tardio, patch e
rebuild.

O objetivo de dez minutos e uma media operacional. Ele nao autoriza reduzir a
leitura integral, a literalidade das evidencias, a estruturacao de numeros, o
recall adversarial, o ledger, a calibracao ou a auditoria final.

## Fluxo alvo

```text
work orders integrais
-> um draft semantico do episodio
-> compilacao e autocheck em memoria
-> correcao local do inventario completo
-> uma persistencia atomica e idempotente
-> uma finalizacao (readiness, build, validator, packet)
-> uma auditoria final da wave
```

## Stories

### T10-S01 - Baseline e metricas honestas

- Registrar tempos medidos de compilacao, autocheck, persistencia, finalizacao e
  total da invocacao.
- Registrar contagens reais de reviews, candidatos, gravacoes e finalizacoes.
- Nao inferir tempo historico nem inventar tokens.

### T10-S02 - Autocheck pre-write

- Extrair a avaliacao do autocheck para uma funcao pura que aceite reviews
  compiladas em memoria.
- Derivar ledger da composicao final em memoria, sem confiar em derivados
  persistidos de uma revisao anterior.
- Retornar o mesmo inventario de hard blockers e audit warnings usado pelo
  finalizador.

### T10-S03 - Entry point one-shot do episodio

- Criar um comando que receba o payload completo do episodio.
- `--check` compila e executa o autocheck sem qualquer escrita.
- `--apply` so persiste quando compilacao e autocheck estiverem limpos.
- A aplicacao usa o recorder atomico existente e chama o finalizador exatamente
  uma vez.
- Reexecucao da mesma revisao recupera receipts e permanece idempotente.

### T10-S04 - Compatibilidade e protecoes

- Preservar CLI, receipts e caminhos existentes.
- Episodio `complete/passed` permanece read-only.
- Nenhum packet e criado antes de hard blockers zero.
- Quotes verbatim, numeros, relacoes, ledger, calibracao e fingerprints mantem
  os validadores atuais.

### T10-S05 - Prova e contrato operacional

- Cobrir check read-only, hard blocker pre-write, persistencia unica,
  finalizacao unica, idempotencia e metricas.
- Atualizar contrato, prompt e skill para recomendar payload de episodio
  completo em vez de batches cronologicos quando a carga couber no contexto.
- Executar testes gold focados, `py_compile` e `git diff --check`.

## Criterios de aceite

1. Um episodio sintatico e semanticamente valido percorre check, uma gravacao e
   uma finalizacao ate packet de cinco arquivos.
2. Um hard blocker detectado no draft produz zero escrita no gold e no export.
3. O autocheck do preview usa os mesmos candidatos finais que seriam gravados.
4. A mesma revisao aplicada novamente e idempotente e nao duplica build/export.
5. O receipt informa duracoes reais por etapa e contagens de operacoes.
6. Testes existentes e novos passam sem escrever em dados gold reais.

## Meta de desempenho

- Episodios de ate 800 segmentos: 4 a 8 minutos.
- Episodios de 800 a 1.800 segmentos: mediana de ate 10 minutos.
- Episodios maiores: medir custo por mil segmentos; nao sacrificar recall para
  cumprir teto artificial.
- Overhead deterministico, excluindo leitura semantica: alvo inferior a 60
  segundos em fixture e inferior a 2 minutos em episodio real medio.

## Fora de escopo

- Reprocessar ou corrigir episodio real neste epico.
- Alterar schema publico ou lifecycle.
- Registrar auditoria, marcar `passed/complete` ou consolidar dados.
- Commit, push, deploy ou Supabase.

## Gate final

Depois das validacoes locais, a proxima wave usa a rota one-shot por episodio e
registra metricas reais. A auditoria continua sendo uma unica fase final com o
modelo Sol, nunca um gate intermediario.

## Resultado da execucao

- Implementado `scripts/run_gold_episode_fast.py` com `--check` pre-write e
  `--apply` one-shot.
- O autocheck passou a aceitar o estado compilado em memoria e a derivar o
  ledger de preview dos candidatos finais.
- O recorder e o finalizador existentes continuam sendo as autoridades de
  escrita, rollback, packet e idempotencia.
- Metricas reais por etapa sao retornadas e registradas no receipt operacional.
- Quatro regressoes novas provaram zero-write em blocker, uma persistencia, uma
  finalizacao, idempotencia e cobertura completa de chunks.
- Suite gold focada: 80 testes aprovados.
- `py_compile`, validacao da skill e `git diff --check`: aprovados.
- Nenhum episodio ou export gold real foi usado ou alterado; somente fixtures no
  temp isolado do job foram escritas.

A mediana real de dez minutos deve ser confirmada na proxima wave por faixa de
tamanho. Este epico remove o overhead repetitivo; ele nao promete que um
episodio excepcionalmente longo possa ser lido integralmente em dez minutos.
