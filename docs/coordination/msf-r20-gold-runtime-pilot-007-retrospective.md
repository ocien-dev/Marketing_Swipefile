# MSF-R20 Gold Runtime Pilot 007 - Retrospectiva

Status: complete
Episode: `beFYVzSv2bw`
Run: `gold-runtime-pilot-007-beFYVzSv2bw-7cd49720c4`

## Resultado

- 20/20 reviews validos;
- 37 candidatos unicos;
- `hard_blockers=0`;
- calibracao `5/12`, minimo 3, status `pass`;
- auditoria final Sol `passed`, zero findings abertos;
- lifecycle `complete/passed`;
- validador com auditoria obrigatoria `pass/errors=[]`;
- packet com exatamente cinco arquivos;
- fingerprints protegidos inalterados.

## Tempo medido

| Etapa | Wall |
| --- | ---: |
| Selecao, preflight e contexto | 1,67 s |
| Leitura integral e autoria do payload | 13m05s |
| Fechamento semantico e reparo de prelint | 25m13s |
| One-shot inicial e dossier | 1,00 s |
| Auditoria Sol integral inicial | 19m39s |
| Remediacao, reauditoria e completion | ~29m53s |
| Total ate receipt terminal | 1h31m12s |

Os comandos deterministas somaram apenas 4,28 s. O custo permaneceu quase todo
na leitura, julgamento, composicao e navegacao dos inventarios.

## O que funcionou

1. `StartEpisode` selecionou, preparou e congelou o runtime em uma unica rota;
   selecao e contexto ficaram abaixo de dois segundos.
2. O payload completo de 20 chunks foi persistido em uma unica operacao e o
   one-shot gerou packet e dossier em aproximadamente um segundo.
3. O autocheck impediu apply com lacunas numericas; nenhuma escrita parcial
   ocorreu nos checks falhos da remediacao.
4. O scaffold trouxe ranges, quotes e asserts source-canonical e permitiu uma
   unica aplicacao transacional para os quatro findings.
5. Completion registrou audit, build complete e validador obrigatorio em 208 ms,
   com receipt terminal e sem verificacao redundante posterior.

## O que nao funcionou como esperado

1. O `semantic_closure_index` apresentou 80 superficies. A classificacao manual
   desse volume dominou o prelint e superou em muito a meta de 45-90 s.
2. A auditoria integral ainda exigiu 19m39s para 1.989 segmentos e dossier de
   455 KB. O mapa v3 ajudou a navegacao, mas nao reduziu a leitura ao alvo de
   6-8 minutos.
3. Quatro lacunas reais chegaram a auditoria: limite 95, sequencia de cinco
   segundos, dois resultados com sinal sonoro e trajetoria intermediaria de
   escala. O fechamento pre-packet nao priorizou adequadamente continuacoes com
   numero, resultado ou mecanismo imediatamente adjacentes.
4. A remediacao fez dois checks read-only falharem porque a matriz numerica exige
   um record por ocorrencia quando preserva multiplicidade. O scaffold nao
   entregou essa contagem nem o `raw` completo `40 semana`.
5. O delta de reauditoria rejeitou o estado por `unaffected_candidates`,
   `protected_fingerprints` e `calibration`: inserts validos e metadados
   derivados foram tratados como drift. Foi necessario reabrir o dossier
   integral, embora os invariantes finais estivessem corretos.

## Aprendizados promovidos

- Ordenar fechamento semantico por risco: resultado numerico, continuacao de
  mecanismo, before/after e outcome reportado antes de caudas genericas.
- Produzir no repair scaffold a matriz completa de ocorrencias numericas e os
  `raw` literais esperados por segmento, inclusive unidades adjacentes.
- Na reauditoria delta, derivar candidatos afetados por diff e ranges, incluindo
  inserts; comparar fingerprints protegidos como `before==after` no dossier
  final e excluir metadados derivados do conjunto de invariantes.
- Para episodios longos, separar a auditoria em mapa de risco + passagem fonte
  unica, sem duplicar warnings de fechamento ja dispostos.

## Autoridades

- receipt: `.codex-work/worker-jobs/MSF-R20-GOLD-RUNTIME-PILOT-007/episode_completion_receipt.json`;
- performance: `.codex-work/worker-jobs/MSF-R20-GOLD-RUNTIME-PILOT-007/episode_performance_report.json`;
- audit final: `.codex-work/worker-jobs/MSF-R20-GOLD-RUNTIME-PILOT-007/final_reaudit_sol_001.json`;
- packet: `/home/luish/msf-data/Marketing_Swipe_File/exports/msf_r20_gold_runtime_pilot_007_beFYVzSv2bw`.
