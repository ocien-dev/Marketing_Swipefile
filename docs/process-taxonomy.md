# Process Taxonomy - Marketing Swipe File

Data de criacao: 2026-07-07
Fonte: `data/processed/taxonomy_seed.json` (taxonomy_version 2026-07-07.1)

## 1. Proposito

Vocabulario canonico de processos de marketing que roteia insights para as
futuras skills e agentes (epico MSF-S, pos-gate R3). Cada processo e uma
capacidade operacional que pode virar uma skill; cada `process_area` agrupa
processos afins.

Derivada da analise do corpus real processado ate 2026-07-07: temas da base
v1 (1.223 insights), temas livres da base v2 (88 insights), titulos dos 253
itens do inventario (podcast Segredos da Escala, aulas da academy VTurb,
videos brutos de anuncio) e da lista de processos-alvo do owner.

Validacao de cobertura na criacao: 99.8% das 8.012 ocorrencias de tema em
v1+v2 mapeiam para pelo menos um processo via termo ou sinonimo.

## 2. Estrutura

Dois novos `term_type` no taxonomy seed:

- `process_area`: 12 areas de nivel superior. Sem sinonimos, servem de
  agrupamento e navegacao.
- `process`: 58 processos, cada um com `parent_id` apontando para uma area.
  Os sinonimos de cada processo incluem os temas observados nas bases v1/v2
  para permitir classificacao automatica por correspondencia.

### Areas e processos

1. **pesquisa e inteligencia**: pesquisa de avatar; pesquisa de mercado e
   nicho; analise de concorrencia e modelagem; validacao de oferta.
2. **estrategia e posicionamento**: posicionamento de marca; estrategia de
   negocio; planejamento de campanha; precificacao.
3. **oferta e produto**: construcao de oferta; criacao de produto low
   ticket; criacao de produto high ticket; escada de produtos e esteira;
   assinatura e recorrencia.
4. **copywriting**: copy para VSL; copy para carta de vendas; copy para
   anuncios; copy para email; copy para paginas; mecanismo e big idea;
   storytelling e narrativa; headlines e hooks; prova e depoimentos;
   argumentacao e objecoes.
5. **funis e paginas**: arquitetura de funil; criacao de quiz; webinario e
   aula de vendas; lancamento; funil perpetuo; captura e geracao de leads;
   checkout e order bump; upsell e downsell; criacao de paginas; area de
   membros e entrega.
6. **trafego e aquisicao**: trafego pago Meta; trafego pago Google e
   YouTube; trafego pago outros canais; trafego organico e conteudo;
   influenciadores e creators; afiliados e parcerias; SEO e busca organica.
7. **criativos**: criacao de video para anuncios; criacao de imagem para
   anuncios; teste e variacao de criativos; producao e player de VSL.
8. **conversao e otimizacao**: CRO e testes A/B; metricas e analise;
   recuperacao e remarketing.
9. **vendas e relacionamento**: time de vendas; atendimento e suporte.
10. **pos-venda e retencao**: onboarding e ativacao; retencao e churn;
    reembolso e chargeback; monetizacao da base.
11. **gestao e operacao**: gestao de time; processos e operacao; financas e
    margem; carreira e desenvolvimento.
12. **ia e automacao**: IA aplicada a marketing.

## 3. Regras de uso

- `process_tags` de um insight e uma lista de ids `process-*` (1 a 4 tags;
  preferir 1-2). Atribuir a tag mais especifica; a area e derivavel pelo
  `parent_id`, nunca gravada diretamente no insight.
- Classificacao automatica (bootstrap): correspondencia entre
  `themes`/`use_case`/`canonical_title` do insight e os termos+sinonimos dos
  processos. Casos sem correspondencia vao para fila de revisao manual, nao
  recebem tag generica.
- Governanca: vale a politica do seed (`new_term_policy`). Processo novo so
  entra com 3+ insights que nao se descrevem pelos existentes; preferir
  adicionar sinonimo a criar processo. Skills futuras (MSF-S) referenciam
  processos por id, portanto renomear/remover exige status `deprecated` ou
  `merged`, nunca delecao.

## 4. Integracao com o pipeline

- **Agora (nao bloqueia R07):** estender `scripts/classify_taxonomy.py` para
  atribuir `process_tags` como pos-processamento sobre v1 e v2, usando a
  correspondencia por sinonimos. Nao alterar o prompt de extracao do R07 em
  andamento.
- **MSF-R12 (emenda):** `curated_insights` passa a ter `process_tags` como
  campo obrigatorio (minimo 1 tag valida por insight curado).
- **MSF-R16 (Supabase):** processos viram tabela referenciada por FK;
  reservar espaco para anotacoes de outcome (resultados de campo) ligadas a
  insights usados em outputs.
- **MSF-S (skills, pos-gate R3):** cada skill de processo declara qual(is)
  `process-*` consome; a receita de retrieval da skill filtra por essas tags.

## 5. Validacao local

Validado em 2026-07-07:

- JSON parse OK em `data/processed/taxonomy_seed.json`.
- Scan non-ASCII OK em `data/processed/taxonomy_seed.json` e neste documento.
- Contagem esperada OK: 12 `process_area` e 58 `process`.
- Todos os ids `process-*` tem `parent_id` apontando para uma area valida.
