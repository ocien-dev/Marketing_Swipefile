# MSF-R20-WAVE-005 — W5-R07: manifesto extraído do estado atual

Status: awaiting_worker
Worker: Extração Padrão-Ouro (`019f4c90-b9dc-7e32-8ff1-57f8896386d3`)
Modelo/esforço: `gpt-5.6-terra/high`
Coordenador: `019f4ee6-a00e-7c90-97bc-5c1aae5c8551`

## Causa confirmada

O W5-R06 não escreveu no gold. A comparação do coordenador mostrou que os cinco
`quote_verbatim` do manifesto contêm caracteres literais `\\u00..`, enquanto
`calibration_tests.json` tem os mesmos caracteres em UTF-8. Assim, todos os
asserts de quote são falsos antes do patcher chegar a qualquer escrita.

Não é divergência semântica nem mudança no episódio. A correção usa uma rota
materialmente diferente: extrair os valores de assert diretamente do JSON atual
no momento de gerar o manifesto, sem reescrever quotes em código ou texto.

## Única story autorizada — W5-R07-S01

1. Registrar `git status --short --branch`; ler este plano e o W5-R06.
2. Criar um helper job-local apenas para gerar
   `zo_calibration_exact_manifest.json`. Ele deve:
   - ler `calibration_tests.json` atual;
   - localizar os cinco `calibration_id` já aprovados;
   - copiar diretamente para `assert` os valores atuais de `segment_ids` e
     `quote_verbatim`, sem `repr`, template interpolado ou escape manual;
   - manter os redirects previamente aprovados para `G004`, `G004`, `G042`,
     `G044` e `G046`, com cinco targets distintos;
   - incluir somente a atualização de `G031.caveats`, com assert do estado
     atual, sem alterar outro campo de candidato.
3. Compilar o helper sem `.pyc`, executar uma verificação read-only que imprima
   igualdade de string e UTF-8 hex para os cinco asserts, depois gerar o
   manifesto uma única vez.
4. Rodar `gold_review_patch --check` uma única vez. Se passar, rodar
   `--apply` uma única vez. Se falhar, parar; não criar outro manifesto e não
   tentar outra escrita.
5. Somente se o apply passar: autocheck estrito, readiness, um build, validador
   normal e export do packet cego.

## Critérios de aceite

- cinco quotes de assert são iguais byte a byte às strings UTF-8 lidas do JSON
  atual; não há barra invertida literal antes de `u00`;
- `G031` só recebe caveat de caso reportado;
- cobertura de calibração chega a pelo menos seis targets distintos;
- autocheck estrito, readiness, build e validador normal passam;
- packet contém cinco arquivos, lifecycle é `awaiting_external_audit/pending_external`
  e fingerprints protegidos permanecem iguais.

## Limites

Este é o segundo e último apply pré-packet: o primeiro patch editorial já foi
aplicado. É proibido reaplicá-lo, criar outro manifesto após este, tocar outro
episódio, scripts/testes/docs/auditorias, marcar `passed/complete`, consolidar,
usar Supabase ou executar release. Falha do check encerra o ramo sem nova
tentativa de escrita.
