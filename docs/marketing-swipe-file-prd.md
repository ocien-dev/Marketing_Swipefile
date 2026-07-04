# PRD - Marketing Swipe File

## 1. Visao

Marketing Swipe File e um sistema de agentes que transforma podcasts, videos, entrevistas, documentos complementares e materiais de bastidores de negocios digitais em inteligencia acionavel de marketing de resposta direta.

O sistema deve captar conteudos do YouTube, comecando pelo VTurb, importar transcricoes automaticas, detectar materiais complementares mencionados ou disponibilizados nos episodios, processar esses arquivos quando forem obtidos, extrair aprendizados estrategicos, taticos e operacionais, e organizar tudo em uma base consultavel por agentes.

A primeira versao deve funcionar dentro do Codex. A UI humana fica para depois. O foco inicial e criar uma memoria operacional para agentes de copy, anuncios, VSLs, quizzes, estrategia, gestao e produto.

## 2. Problema

Existe muito conhecimento pratico disperso em podcasts, entrevistas, aulas publicas, PDFs, planilhas, documentos, areas de membros e materiais citados por participantes. Esse conhecimento tem alto valor, mas hoje fica preso em formatos longos, fragmentados e dificeis de reutilizar.

Problemas atuais:

- Episodios longos exigem muito tempo humano para assistir e anotar.
- Materiais complementares ricos, como frameworks, templates, planilhas e copies completas, ficam perdidos fora do episodio.
- Muitos arquivos exigem acao manual para obtencao, como comentar uma palavra-chave, chamar no direct ou acessar uma area de membros.
- Insights ficam desconectados entre si, sem formar uma memoria estrategica acumulativa.
- Agentes de copy e criativos nao possuem uma base estruturada do que esta funcionando no mercado brasileiro.
- E dificil encontrar rapidamente referencias para uma tarefa especifica, como criar uma VSL, melhorar um hook, montar uma oferta ou pensar em anuncios.
- Sem evidencia, ha risco de agentes inventarem aprendizados ou criarem recomendacoes sem lastro.

## 3. Objetivos

Objetivos do produto:

- Processar episodios de negocios digitais em uma base estruturada de insights.
- Detectar e rastrear materiais complementares citados nos episodios.
- Avisar o usuario quando houver arquivo ou material que exija procedimento manual de obtencao.
- Processar PDFs, documentos, planilhas, slides, paginas e outros materiais complementares como fontes de inteligencia de primeira classe.
- Criar um "super cerebro" de marketing de resposta direta, com muitos nos pequenos conectaveis.
- Permitir que agentes consultem a base para gerar estrategias, copies, VSLs, anuncios, quizzes, criativos e planos melhores.
- Manter rastreabilidade ate fonte, episodio, timestamp, arquivo, pagina, aba, celula ou trecho.
- Suportar busca por linguagem natural e por filtros estruturados.
- Aceitar conteudo em portugues, ingles e espanhol, mantendo original e traducao para PT-BR.
- Evoluir a taxonomia, os prompts, as skills e os agentes conforme novos conteudos forem processados.

Objetivo do MVP:

- Processar 20 episodios do VTurb.
- Detectar materiais complementares mencionados nesses episodios.
- Criar fila de acoes manuais para materiais que dependem do usuario.
- Processar pelo menos 3 materiais complementares obtidos, se existirem nos episodios piloto.
- Extrair insights acionaveis em nivel estrategico, tatico e operacional.
- Permitir que um agente encontre referencias de VSLs sozinho.
- Permitir que um agente crie uma copy de VSL com 3 variacoes de lead no mesmo nivel ou melhor do que faria sem a base.
- Permitir que outro agente crie anuncios usando os insights da base e espionagem de mercado complementar.

## 4. Usuarios

### 4.1 Usuario humano

O usuario humano e o dono do Marketing Swipe File, estrategista e curador final. Ele precisa poder:

- Definir fontes e ordem de processamento.
- Fornecer links de episodios.
- Receber alertas quando um episodio mencionar arquivos, keywords, directs, areas de membros ou links externos que precisam ser obtidos manualmente.
- Inserir arquivos complementares obtidos.
- Solicitar analises e consultas via Codex.
- Conferir evidencias quando algum insight parecer duvidoso.
- Pedir a agentes que usem a base para criar VSLs, anuncios, ofertas, quizzes e estrategias.
- Futuramente navegar por uma UI propria, com filtros, grafo de conceitos e buscas.

### 4.2 Agentes consumidores

Agentes que usam o Marketing Swipe File como memoria estrategica:

- CEO agent: sintetiza direcao estrategica, oportunidades e posicionamento.
- CMO agent: transforma aprendizados em planos de marketing.
- COO agent: converte estrategias em processos, rotinas e sistemas.
- Copy strategist: monta estrategia de mensagem e persuasao.
- Copywriter de VSLs: cria VSLs, leads, mecanismos, provas, transicoes e calls to action.
- Copywriter de webinarios: cria estrutura de apresentacao, narrativa e pitch.
- Copywriter de anuncios: cria hooks, angulos e variacoes para trafego pago.
- Copywriter de quizzes: cria perguntas, logicas, resultados e pontes de oferta.
- Criador de anuncios, imagens e videos: transforma insights em criativos executaveis.
- Gestor de trafego: interpreta aprendizados para midia paga, testes e escalas.
- Head de lancamentos: aplica estrategias em campanhas, janelas e ofertas.
- Head de produto: conecta dores, desejos e promessas a produto.
- Estrategista de low ticket: identifica ofertas, funis e criativos de entrada.
- Gestor de projetos: transforma estrategias em backlog e execucao.

### 4.3 Agentes produtores da base

Agentes que alimentam e melhoram a base:

- Ingestion agent: coleta links, metadados e transcricoes.
- Asset detection agent: identifica materiais complementares mencionados.
- Acquisition task agent: cria instrucoes para o usuario obter arquivos referenciados.
- Asset processing agent: extrai texto e estrutura de PDFs, docs, planilhas, slides e paginas.
- Transcript normalizer: limpa e segmenta transcricoes.
- Extraction agent: extrai insights atomicos e evidencia.
- Taxonomy agent: classifica, cria e revisa temas.
- Strategy graph agent: conecta insights relacionados.
- Quality agent: verifica rastreabilidade e sinaliza baixa confianca.
- Retrieval agent: busca blocos relevantes para uma tarefa.

## 5. Escopo de fontes

Ordem planejada:

1. VTurb.
2. KiwiCast.
3. Hotmart Cast.
4. Fontes derivadas identificadas pela base.

No MVP, o sistema comeca com alguns episodios escolhidos manualmente do VTurb. Depois de validar a qualidade, processa 20 episodios. A ingestao automatica de novos episodios entra depois.

Fontes por episodio:

- Transcricao automatica do YouTube.
- Descricao do video.
- Comentarios fixados ou links publicos, quando disponiveis.
- Materiais citados verbalmente, como PDFs, docs, planilhas, templates, prompts, swipes, mapas, checklists e copies.
- Arquivos obtidos manualmente pelo usuario e adicionados ao projeto.

## 6. Casos de uso

### UC1 - Processar episodio manualmente

O usuario fornece uma URL do YouTube. O sistema coleta metadados, importa a transcricao automatica quando disponivel, divide o conteudo em blocos, detecta materiais complementares, extrai insights e grava tudo na base.

Resultado esperado:

- Episodio cadastrado.
- Transcricao preservada.
- Materiais complementares detectados.
- Alertas criados quando houver procedimento manual.
- Insights classificados.
- Evidencias por insight.
- Timestamps associados.
- Resumo executivo.

### UC2 - Detectar material complementar

O sistema encontra no episodio uma mencao como "comenta VSL que eu mando o PDF", "chama no direct com a palavra funil", "o template esta na area de membros" ou "baixem a planilha no link da descricao".

Resultado esperado:

- Material referenciado registrado.
- Tipo provavel do material inferido.
- Procedimento de obtencao descrito.
- Trecho/timestamp da mencao salvo.
- Status definido como `needs_user_action`.
- Usuario avisado com instrucao objetiva do que fazer.

### UC3 - Inserir e processar arquivo complementar

O usuario obtem um PDF, doc, planilha, slide ou outro arquivo citado no episodio e coloca no diretorio indicado.

Resultado esperado:

- Arquivo vinculado ao episodio.
- Texto e estrutura extraidos.
- Frameworks, exemplos, templates e copies identificados.
- Insights extraidos da mesma forma que na transcricao.
- Evidencias apontam para arquivo, pagina, aba, celula ou trecho.

### UC4 - Criar base inicial do VTurb

O usuario fornece uma lista de episodios VTurb. O sistema processa em lote ate chegar a 20 episodios validados.

Resultado esperado:

- Base pesquisavel com pelo menos 20 episodios.
- Fila de materiais complementares pendentes.
- Taxonomia inicial expandida conforme conteudo real.
- Temas recorrentes identificados.
- Padroes de estrategia mapeados.

### UC5 - Consultar insights por tarefa

Um agente pergunta: "Quais aprendizados do Marketing Swipe File ajudam a criar uma VSL para produto X?"

Resultado esperado:

- Lista priorizada de insights.
- Evidencias e fontes.
- Blocos aplicaveis por etapa da VSL.
- Diferenciacao entre evidencia vinda de video e evidencia vinda de material complementar.
- Alertas sobre lacunas ou baixa confianca.

### UC6 - Gerar copy de VSL

Um agente de VSL usa a base para criar uma copy completa e 3 variacoes de lead.

Resultado esperado:

- Estrategia da VSL.
- Angulos de lead.
- Big idea.
- Mecanismo unico.
- Provas sugeridas.
- Objecoes e quebras.
- CTA.
- Referencias da base usadas.

### UC7 - Gerar anuncios

Um agente de anuncios consulta a base e combina os aprendizados com espionagem de mercado.

Resultado esperado:

- Angulos de criativo.
- Hooks.
- Scripts curtos.
- Briefings para imagem/video.
- Hipoteses de teste.
- Vinculo com insights de origem.

### UC8 - Evoluir taxonomia

Ao encontrar padroes novos, o sistema sugere novos temas, subtemas e relacoes.

Resultado esperado:

- Taxonomia aumenta sem perder organizacao.
- Novos temas ficam ligados a temas pais.
- Itens antigos podem ser reclassificados quando necessario.

### UC9 - Evoluir skills e agentes

Depois que um fluxo funcionar repetidamente no Codex, ele vira skill. Depois que um conjunto de skills for validado, ele vira loop. Depois que loops estiverem estaveis, agentes especializados passam a usar essas skills.

Resultado esperado:

- Processo fica mais confiavel a cada iteracao.
- Menos contexto precisa ser reexplicado.
- Agentes passam a operar sobre procedimentos validados, nao prompts soltos.

## 7. Requisitos funcionais

### Ingestao

- Aceitar URLs manuais do YouTube.
- Cadastrar canal, episodio, convidado, titulo, data, URL e metadados.
- Importar transcricao automatica do YouTube quando disponivel.
- Guardar estado de processamento do episodio.
- Suportar reprocessamento sem duplicar dados.
- Futuramente detectar novos videos automaticamente por canal.

### Detecao de materiais complementares

- Analisar titulo, descricao, comentarios fixados quando disponiveis e transcricao.
- Detectar mencoes a PDFs, docs, planilhas, slides, aulas, areas de membros, templates, prompts, swipe files, checklists, mapas e exemplos.
- Detectar instrucoes de obtencao, como comentar palavra-chave, chamar no direct, acessar link da descricao, entrar em comunidade ou buscar na area de membros.
- Criar uma tarefa de aquisicao para cada material detectado.
- Avisar o usuario quando a tarefa exigir acao manual.
- Registrar timestamp, trecho original e contexto da mencao.
- Permitir anexar posteriormente o arquivo obtido.

### Processamento de arquivos complementares

- Aceitar PDF, DOCX, Google Docs exportado, XLSX, CSV, Google Sheets exportado, PPTX, imagens com texto e paginas HTML salvas.
- Preservar arquivo original.
- Extrair texto, tabelas, estrutura e metadados.
- Segmentar conteudo por pagina, secao, slide, aba, linha ou bloco.
- Detectar frameworks, exemplos, templates, prompts, copies completas, funis, checklists e modelos.
- Criar insights atomicos com evidencia vinculada ao arquivo.
- Vincular o arquivo ao episodio, canal e material referenciado.

### Transcricao e normalizacao

- Preservar a transcricao original.
- Dividir em segmentos com timestamps.
- Detectar idioma.
- Criar versao traduzida para PT-BR quando o original nao estiver em portugues.
- Remover lixo obvio da transcricao sem apagar conteudo relevante.
- Manter referencia ao trecho original para auditoria.

### Extracao de inteligencia

- Extrair muitos insights atomicos, nao apenas resumos.
- Classificar cada insight por nivel: estrategico, tatico ou operacional.
- Classificar por tema, subtema, nicho, funil, etapa, papel de agente e aplicabilidade.
- Extrair frameworks, principios, exemplos, promessas, objecoes, mecanismos, hooks, modelos de oferta e estruturas de copy.
- Identificar copies completas ou parciais dentro de materiais complementares.
- Atribuir confianca e necessidade de revisao.
- Registrar evidencia por insight com timestamp, trecho, arquivo, pagina, aba, celula ou slide.
- Criar conexoes entre insights relacionados.

### Consulta

- Permitir busca por linguagem natural.
- Permitir filtros estruturados: tema, canal, episodio, convidado, idioma, nicho, nivel, aplicabilidade, etapa do funil, tipo de ativo, tipo de fonte e confianca.
- Retornar referencias com evidencia.
- Permitir consultas orientadas a tarefa, como "criar VSL", "gerar anuncios" ou "montar oferta".

### Acesso por agentes

- Expor ferramentas para agentes consultarem:
  - buscar insights
  - buscar evidencias
  - buscar episodios
  - buscar materiais complementares
  - buscar frameworks
  - montar contexto para tarefa
  - registrar artefato gerado
- Recomenda-se MCP quando a base estiver minima e estavel, porque agentes diferentes poderao consumir a mesma fonte de verdade por ferramentas padronizadas.

### Skills, loops e agentes Codex

- Criar primeiro skills atomicas e reutilizaveis para etapas estaveis do processo.
- Agrupar skills validadas em loops operacionais.
- Criar agentes especializados apenas depois que as skills e loops estiverem funcionando com exemplos reais.
- Versionar prompts, instrucoes e criterios de qualidade usados por cada skill.
- Registrar evidencias de validacao de cada skill antes de ela virar base para agente.

Sequencia recomendada:

1. Prompts manuais e scripts locais.
2. Skills atomicas.
3. Loops compostos.
4. Agentes produtores da base.
5. Agentes consumidores da base.
6. MCP e automacoes quando o contrato estiver estavel.

### Aprendizado e aperfeicoamento

- Registrar quais insights foram usados em artefatos gerados.
- Registrar feedback humano ou de agente sobre utilidade.
- Permitir ajustar taxonomia e prompts de extracao.
- Permitir reprocessar episodios e arquivos com extratores melhores.
- Criar avaliacoes comparando outputs com e sem a base.

## 8. Requisitos nao funcionais

- Rastreabilidade: todo insight deve apontar para fonte, episodio e evidencia especifica.
- Baixa friccao no MVP: operar dentro do Codex, sem UI obrigatoria.
- Modularidade: pipeline dividido em etapas reexecutaveis.
- Idempotencia: reprocessar um episodio ou arquivo nao deve duplicar insights.
- Portabilidade: dados exportaveis em JSON/CSV/SQL.
- Seguranca: se usar Supabase exposto por API, aplicar RLS e separar chaves privadas.
- Escalabilidade: arquitetura preparada para centenas ou milhares de episodios e arquivos.
- Observabilidade: cada execucao deve gerar logs de status, erros e metricas.

## 9. Metricas de sucesso

MVP:

- 20 episodios do VTurb processados.
- 90% ou mais dos insights com fonte e evidencia.
- Pelo menos 500 insights atomicos extraidos dos 20 episodios.
- Materiais complementares detectados e registrados quando mencionados.
- Pelo menos 3 arquivos complementares processados, se houver arquivos disponiveis nos episodios piloto.
- Pelo menos 10 temas ou subtemas relevantes identificados alem da taxonomia inicial.
- Agente consegue recuperar referencias relevantes para VSL em menos de 5 consultas.
- Agente gera 1 VSL completa com 3 variacoes de lead usando referencias da base.
- Agente gera 10 ou mais anuncios com justificativa estrategica baseada na base.

Qualidade:

- Menos de 10% dos insights revisados manualmente considerados irrelevantes.
- Zero insights importantes sem fonte quando usados em artefatos finais.
- Outputs gerados com a base sao avaliados como iguais ou melhores que outputs sem a base.
- Nenhum material complementar detectado fica sem status: pendente, obtido, processado, indisponivel ou descartado.

Sistema:

- Reprocessamento de episodio e arquivo funciona sem duplicacao.
- Busca estruturada retorna resultados consistentes.
- Base exportavel e recuperavel.
- Skills MVP executam o fluxo sem depender de reexplicacao em cada nova conversa.

## 10. Fases

### Fase 0 - Design operacional

- Criar PRD, arquitetura e backlog do Marketing Swipe File.
- Definir taxonomia inicial.
- Definir modelo de dados.
- Definir formato dos arquivos intermediarios.
- Definir desenho inicial de skills Codex.

### Fase 1 - MVP Codex-first

- Processar links manualmente.
- Usar transcricao automatica do YouTube.
- Detectar materiais complementares.
- Criar fila de acoes manuais para obtencao de arquivos.
- Processar arquivos complementares inseridos pelo usuario.
- Extrair insights com agentes no Codex.
- Salvar dados estruturados em arquivos locais e/ou Supabase.
- Consultar via scripts, SQL ou agente de retrieval.
- Gerar primeiro output de VSL e anuncios usando a base.

### Fase 2 - Skills atomicas

- Criar skill `marketing-swipe-file-ingest`.
- Criar skill `marketing-swipe-file-detect-assets`.
- Criar skill `marketing-swipe-file-process-assets`.
- Criar skill `marketing-swipe-file-extract-insights`.
- Criar skill `marketing-swipe-file-retrieve`.
- Criar skill `marketing-swipe-file-quality-review`.
- Validar cada skill em episodios reais antes de compor loops.

### Fase 3 - Loops Codex

- Criar loop de processamento de episodio.
- Criar loop de processamento de material complementar.
- Criar loop de revisao de qualidade.
- Criar loop de strategy pack para agentes consumidores.
- Registrar inputs, outputs, logs e falhas de cada execucao.

### Fase 4 - Supabase como fonte de verdade

- Criar projeto Supabase.
- Implementar schema com episodios, fontes, materiais, segmentos, insights, taxonomia e evidencias.
- Adicionar busca full-text e filtros estruturados.
- Adicionar embeddings quando houver decisao de custo/API.
- Criar importadores idempotentes.

### Fase 5 - MCP para agentes

- Criar MCP server proprio do Marketing Swipe File.
- Expor ferramentas de consulta e composicao de contexto.
- Padronizar contratos para agentes consumidores.
- Registrar uso de insights por artefato.

### Fase 6 - Agentes especializados

- Criar agentes produtores da base usando skills e loops validados.
- Criar agentes consumidores da base para VSL, anuncios, quizzes, webinarios, oferta, produto e gestao.
- Criar avaliadores de qualidade para comparar outputs com e sem Marketing Swipe File.

### Fase 7 - Automacao e UI

- Monitorar canais e novos episodios.
- Reprocessar em lote.
- Criar UI de busca, revisao e grafo.
- Adicionar painel de metricas e qualidade.

### Fase 8 - Inteligencia composta

- Criar grafo de estrategias.
- Detectar padroes recorrentes entre fontes e materiais.
- Sugerir playbooks.
- Comparar estrategias por nicho, canal e resultado.
- Alimentar agentes autonomos de criacao e planejamento.

## 11. Fora de escopo do MVP

- UI visual amigavel.
- Automacao completa de novos episodios.
- Sistema de permissoes multiusuario.
- Avaliacao estatistica real de performance de anuncios.
- Garantia de que todo conteudo do YouTube tera transcricao disponivel.
- Garantia de acesso automatico a materiais bloqueados por direct, comentario, login ou area de membros.
- Embeddings via API caso o objetivo inicial seja evitar custos externos.

## 12. Riscos

- Transcricao automatica do YouTube pode estar ausente, incompleta ou imprecisa.
- Materiais complementares podem depender de acoes manuais, login, comunidade, direct ou permissoes externas.
- Conteudo longo pode gerar muitos insights redundantes se a deduplicacao for fraca.
- Arquivos complementares podem conter copies e frameworks muito ricos, exigindo extratores mais cuidadosos que transcricoes.
- Sem API de embeddings no MVP, a busca semantica pode ser inicialmente simulada por agente ou substituida por busca textual/tagging.
- Taxonomia pode crescer demais se nao houver governanca.
- Agentes podem usar insights fora de contexto se a consulta nao retornar evidencia e aplicabilidade.

## 13. Principios de produto

- Evidencia antes de opiniao.
- Insight atomico antes de resumo generico.
- Material complementar e fonte primaria, nao anexo secundario.
- Base para agentes antes de UI humana.
- Skills antes de agentes autonomos.
- Loops validados antes de automacao.
- Taxonomia evolutiva, mas controlada.
- Tudo que gera output deve registrar quais referencias usou.
- O sistema deve melhorar conforme processa mais conteudo.
