# MSF-R20 Gold Runtime Pilot 009 - Retrospectiva

Status: complete
Episode: `NiT0-ABoVnk`
Date: 2026-07-17

## Resultado

- 21/21 reviews atuais;
- 59 candidate IDs unicos;
- `hard_blockers=0`;
- calibracao `pass`, 5 cobertos de 16 e minimo contratual 4;
- auditoria final `passed`, zero findings abertos;
- lifecycle `complete` e audit status `passed`;
- packet exato de cinco arquivos;
- fingerprints protegidos inalterados.

## Linha do tempo reconciliada

O receipt mede 74 min 26,5 s entre a selecao e a geracao dos artefatos de
encerramento. Apenas 7,4 s foram comandos deterministas ativos. Os spans
semanticos explicitamente medidos somaram 33 min 46,5 s; 40 min 32,6 s ficaram
como gap nao classificado, portanto nao devem ser atribuidos artificialmente a
uma fase especifica.

| Etapa | Tempo medido |
| --- | ---: |
| Selecao | 0,08 s |
| Preflight e contexto | 1,30 s |
| Leitura/composicao ate o primeiro prelint | dentro do gap inicial de 36 min 16,8 s |
| Reparos de prelint | 6 min 16,8 s |
| Tres prelints deterministas | 1,83 s |
| Apply, finalizer, build e dossier inicial | 1,59 s |
| Auditoria final inicial | 16 min 48,2 s |
| Autoria da remediacao | 6 min 32,2 s |
| Checks e aplicacao determinista da remediacao | 2,52 s |
| Reauditoria do delta | 4 min 9,3 s |
| Registro, build e validacao obrigatoria finais | 0,11 s |

O gap inicial inclui a leitura cronologica e a composicao do payload, mas o
instrumentador atual nao separa esse trabalho de pausas do ambiente. A soma de
spans semanticos e comandos ativos reconcilia 33 min 53,8 s; o restante deve
continuar reportado como nao classificado ate haver marcadores mais granulares.

## Auditoria e remediacao

A auditoria inicial encontrou cinco lacunas materiais:

1. mecanica e numeros do trial product-led em G049;
2. comparacao de custo manual versus KYC automatizado;
3. evidencia incorreta em G051;
4. contraste entre lift de headline e utilidade valorizada pelo cliente;
5. evidencia e calibracao de PMF em G052.

A remediacao unica fechou o inventario sem alterar a fonte ou resolver
contradicoes por inferencia. G058 preserva como caveat a divergencia oral do
custo de pessoal; G059 mantem o lift de 20-30% como relato sem baseline,
amostra, janela, controle ou verificacao independente.

## Aprendizados

- O pipeline determinista deixou de ser o gargalo: selecao, contexto, checks,
  persistencia, builds, dossiers e completion consumiram poucos segundos.
- O maior custo esta na leitura/composicao e na auditoria semantica, seguido da
  autoria da remediacao. Otimizacoes futuras devem atuar nesses tres pontos,
  nao adicionar novos gates tecnicos.
- O risk brief reduziu a superficie de triagem, mas ainda nao evitou lacunas em
  blocos de produto proximos ao fim do episodio. A matriz de risco deve marcar
  explicitamente comparacoes economicas, mudancas de produto e calibracoes
  semanticamente proximas.
- A reauditoria por delta foi bem menor que a auditoria inicial e deve continuar
  restrita aos findings e aos efeitos colaterais do patch.
- O snapshot do piloto protege tres arquivos, e os tres ficaram iguais. Os
  relatos futuros devem usar a contagem efetiva do receipt, sem declarar 4/4
  quando o contrato material registra tres entradas.

## Proximas melhorias

1. Instrumentar inicio/fim de leitura cronologica, composicao e cada rodada de
   reparo para eliminar o gap nao classificado.
2. Gerar, antes do primeiro prelint, uma fila de risco por blocos economicos,
   produto/roadmap, before/after e targets de calibracao ainda sem candidato.
3. Fazer o dossier final incluir uma tabela direta `target -> candidate ->
   evidence`, reduzindo a verificacao manual de calibracao.
4. Na auditoria, revisar primeiro os riscos fechados pelo indice e depois fazer
   uma varredura curta de recall residual, evitando releitura irrestrita.
5. Produzir o manifesto de remediacao diretamente dos findings selados e da
   evidencia canonica atual, preservando asserts e evitando redigitacao de raw.
