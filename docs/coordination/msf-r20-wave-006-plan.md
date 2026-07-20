# MSF-R20-WAVE-006 - Validacao real do runtime WSL e fast lane gold

Status: completed
Execucao: direta no chat ativo
Runtime: Ubuntu 24.04 / WSL 2
Dados ativos: `/home/luish/msf-data/Marketing_Swipe_File`
Manifesto: `docs/coordination/msf-r20-wave-006-manifest.json`
Auditoria final: fase unica com `gpt-5.6-sol/high`

## Objetivo

Processar cinco episodios elegiveis ainda sem gold final usando o fluxo one-shot
por episodio. A wave mede o custo real do fast lane no filesystem Linux e, ao
final, publica uma copia verificada dos exports no OneDrive para consumo em
leitura por outros projetos.

## Episodios

1. `9jZvoPzaXR4` - 1.537 segmentos
2. `ngHQnIq3Y2s` - 614 segmentos
3. `ccdmYIGYob0` - 1.708 segmentos
4. `7sa0JIa4RaQ` - 1.381 segmentos
5. `GSSh_3RoU98` - 1.420 segmentos

Carga prevista: 6.660 segmentos, dentro do orcamento de 9.000 segmentos,
160 chunks e cinco episodios.

## Stories

### W6-S01 - Preflight e preparacao

- Validar runtime Linux nativo, temp, fontes raw, metadata, transcript,
  ownership e fingerprints.
- Rodar o manifesto primeiro em leitura e depois preparar os cinco episodios.

### W6-S02 - Revisao one-shot por episodio

- Ler todos os work orders cronologicamente.
- Produzir um payload completo source-backed por episodio.
- Corrigir o inventario completo do compilador e do autocheck em memoria.
- Persistir uma unica transacao atomica limpa por episodio quando couber.

### W6-S03 - Recall e finalizacao

- Executar recall adversarial de numeros, comparacoes, scripts, steps,
  condicoes, caveats e fronteiras.
- Exigir `hard_blockers=0`.
- Finalizar uma vez, com packet de cinco arquivos e estado
  `awaiting_external_audit/pending_external`.

### W6-S04 - Gate e auditoria final

- Gravar receipt consolidado somente com cinco resultados terminais.
- Fazer uma unica auditoria final da wave com `gpt-5.6-sol/high`.
- Corrigir findings consolidados, reauditar e derivar `complete/passed` somente
  quando a auditoria tiver zero findings abertos.

### W6-S05 - Publicacao e metricas

- Registrar tempos reais de compilacao, autocheck, persistencia, finalizacao e
  total por episodio, sem estimativas.
- Publicar os exports verificados em
  `C:\Users\luish\OneDrive\Marketing_Swipe_File_Published`.
- Confirmar hash do snapshot e acesso Windows.

## Criterios de aceite

- Cinco episodios integralmente revisados e source-backed.
- IDs unicos, quotes verbatim, numeros sustentados, relacoes validas, ledger e
  calibracao coerentes.
- Packets finais de exatamente cinco arquivos e fingerprints preservados.
- Auditoria final unica aprovada antes de `complete/passed`.
- Receipt consolidado terminal e snapshot compartilhado verificado.
- Nenhuma escrita em `C:\MSF-data`, Supabase ou bases consolidadas.

## Condicoes reais de parada

Somente fonte ausente/incompativel, lock ou permissao persistente, duas rotas
atomicas materialmente diferentes falhando, corrupcao sem rollback ou
fingerprint protegido divergente. Erros rotineiros de draft, schema, ASCII,
enum, tema, numero, steps, relacao, ledger ou calibracao sao corrigidos dentro
da propria execucao.

## Resultado final

- Cinco episodios `complete/passed`, com 111/111 chunks e 133 candidatos
  unicos no total.
- Auditoria final `gpt-5.6-sol/high`: zero findings abertos.
- Gate consolidado `ready_for_audit`, com identidade de packet e fingerprints
  validos nos cinco episodios.
- Snapshot compartilhado publicado e verificado no OneDrive: 313 arquivos,
  50.749.368 bytes e hash de conteudo
  `e82b66725e5e876f7e6d3586ab90f31636734e9aa24e14b7d8b0d70a05e78701`.
- O runtime WSL eliminou a latencia relevante de filesystem nos gates
  mecanicos; a duracao total continuou dominada por recall e auditoria
  semantica. Tempos historicos por episodio nao estavam instrumentados e nao
  foram estimados.
