# Insight Quality Review - 2026-07-04

## Objetivo

Avaliar se os 1.223 insights consolidados do Marketing Swipe File ja estao prontos para alimentar retrieval, strategy packs e agentes sem supervisao humana pesada.

## Amostra Revisada

- Base: `data/exports/insights_master.json`
- Total: 1.223 insights
- Amostra estruturada: 80 insights em `data/exports/insight_quality_review_sample.csv`
- Amostra incluiu:
  - Insights usados nos strategy packs de VSL e anuncios.
  - Insights de alta e media confianca.
  - Temas criticos: VSL, anuncios, criativos, oferta, quiz, funil, prova, mecanismo, gestao, produto e retencao.

## Diagnostico Curto

A base e boa como materia-prima e ja tem muita evidencia util. Ainda nao esta ideal como camada final para agentes autonomos.

O principal problema nao e falta de evidencia. O principal problema e que muitos insights usam titulos e conclusoes muito genericos, derivados de regras fixas, enquanto a evidencia contem uma pepita mais especifica.

## Numeros Relevantes

- 1.198 insights vieram de transcript.
- 25 insights antigos vieram de descricao e devem continuar com menor prioridade.
- 831 insights estao como `needs_review`.
- 392 insights estao como `auto_accepted`.
- 925 insights estao em titulos/regra com 50+ repeticoes.
- 656 insights estao em titulos/regra com 100+ repeticoes.
- 82 insights da base tem ruido explicito de transcricao detectavel em evidencia.
- 25 insights tem locator fraco, concentrados nos antigos de descricao.
- 4 insights da base tem sinais fortes de contaminacao por descricao/recomendacao externa dentro da quote.

## Exemplos Bons

### Mini VSL como ponte de conversao

`TOW0sWhPaZw-tr-insight-0003`

Forca:

- Evidencia direta.
- Traz mudanca de pagina estatica para mini VSL.
- Traz numero concreto: de 30.000 para 100.000 no mes.

Risco:

- Quote tem ruido de transcricao, mas nao compromete a ideia.

Uso recomendado:

- Pode entrar em strategy pack, mas como caso anedotico, nao como promessa universal.

### Quiz precisa fechar o loop que abriu

`mCaFyZpXJdE-tr-insight-0013`

Forca:

- Evidencia muito especifica: a pergunta "o que voce vai receber?" abriu um loop que nao foi fechado.
- Ajuda diretamente copywriter de quiz.

Uso recomendado:

- Promover para insight curado com titulo mais especifico: "Toda promessa aberta no quiz precisa ser fechada antes da oferta".

### Criativo validado deve gerar variacoes controladas

`BbhJn8NXRso-tr-insight-0005`

Forca:

- A evidencia fala de encontrar dores, curiosidades e personas validadas e recombinar esses elementos.
- Boa aplicacao pratica para ads.

Uso recomendado:

- Manter, mas reescrever de forma mais atomica: "Varie persona, dor e curiosidade a partir dos elementos que ja validaram".

## Exemplos Que Precisam De Reescrita

### "Expert real aumenta autoridade no low ticket"

Esse titulo aparece 105 vezes. Algumas evidencias falam de autoridade real, mas outras falam de:

- historia na VSL;
- prova demonstrativa;
- expert como backend;
- conteudo organico;
- congruencia entre criativo e VSL;
- VSL white vs VSL com expert.

Recomendacao:

- Nao usar esse titulo como insight final.
- Clusterizar e quebrar em sub-insights especificos.

### "Um criativo validado deve virar uma esteira de variacoes"

Esse titulo aparece 135 vezes. A ideia central e boa, mas o cluster mistura varios mecanismos diferentes:

- variar formato;
- modelar organico no pago;
- testar ABO e CBO;
- isolar conta de anuncio;
- mudar post text/titulo;
- recombinar persona, dor e curiosidade;
- usar ticket para definir budget inicial.

Recomendacao:

- Excelente cluster bruto.
- Fraco como unidade final de retrieval.
- Deve virar 6-10 insights atomicos.

## Exemplos Problematicos

### Contaminacao por recomendacao externa

`TOW0sWhPaZw-tr-insight-0008`

Problema:

- A quote mistura o trecho do episodio com titulo de outro conteudo: "O Segredo para lucrar MILHOES com Produtos LOW TICKET | Pedro Aredes - Hotmart Cast #243".

Acao:

- Marcar como `needs_review`.
- Corrigir janela de evidencia ou rejeitar se nao houver quote limpa.

### Promo/intro confundido com insight

Alguns insights pegam introducoes, chamadas comerciais ou contextualizacoes do episodio e transformam em principio.

Acao:

- Penalizar evidencia com termos como "inscreva-se", "assista tambem", nomes de outros podcasts, hashtags, e blocos promocionais.

## Veredito

Eu usaria a base hoje para:

- pesquisa;
- rascunhos;
- strategy packs internos;
- exploracao de angulos;
- apoio a brainstorming e planejamento.

Eu ainda nao usaria a base hoje para:

- agente que escreve copy final sem revisao;
- promessa comercial sensivel;
- claims numericos sem checagem;
- ranking automatico sem diversidade e clusterizacao.

## Gate Que Eu Usaria

Cada insight deveria receber uma nota editorial de 0 a 100:

- Evidencia direta e limpa: 25 pontos.
- Especificidade da tese: 25 pontos.
- Aplicabilidade operacional: 20 pontos.
- Portabilidade de contexto: 15 pontos.
- Novidade em relacao a insights ja existentes: 10 pontos.
- Limpeza de transcript/quote: 5 pontos.

Classificacao:

- 85-100: `curated_use_direct`
- 70-84: `curated_use_with_context`
- 50-69: `rewrite_before_use`
- 0-49: `reject_or_archive`

## Mudanca De Arquitetura Recomendada

Manter dois niveis:

1. `raw_insights`
   - Tudo que sai da extracao.
   - Pode ser redundante e ruidoso.

2. `curated_insights`
   - Menos itens.
   - Titulo especifico.
   - Quote limpa.
   - Contexto de uso.
   - Risco/limite de claim.
   - Cluster e relacoes com insights semelhantes.

Campos que eu adicionaria em `curated_insights`:

- `canonical_title`
- `specific_takeaway`
- `use_case`
- `when_to_use`
- `when_not_to_use`
- `claim_risk`
- `evidence_cleanliness`
- `cluster_id`
- `supporting_insight_ids`
- `editorial_score`
- `reviewed_by`
- `reviewed_at`

## Proximo Passo Recomendado

Criar um primeiro lote curado com 100-150 insights, nao tentar curar os 1.223 de uma vez.

Ordem:

1. Curar top insights de VSL e anuncios porque ja aparecem nos strategy packs.
2. Clusterizar titulos repetidos em sub-insights especificos.
3. Regerar strategy packs usando `curated_insights` em vez de `insights_master`.
4. Comparar output antigo vs novo.

Minha expectativa: menos volume aparente, mas muito mais qualidade por item recuperado.
