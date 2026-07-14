# MSF-R20-WAVE-005 — W5-R08: alinhamento semântico autorizado pelo owner

Status: awaiting_worker
Autorização: owner escolheu Opção A em 2026-07-14
Worker: Extração Padrão-Ouro (`019f4c90-b9dc-7e32-8ff1-57f8896386d3`)
Modelo/esforço: `gpt-5.6-terra/high`
Coordenador: `019f4ee6-a00e-7c90-97bc-5c1aae5c8551`

## Decisão aplicada

O owner autorizou uma terceira e última correção, limitada a alinhar o texto
editorial de dois claims às evidências que já constam nos próprios candidatos.
Os redirects de calibração, números, relações, quotes, ledger e todos os outros
candidatos ficam imutáveis.

## Única story — W5-R08-S01

1. Registrar `git status --short --branch` e ler este plano.
2. Criar um único manifesto job-local
   `zo_semantic_alignment_patch.json`, com `patch_window` igual a
   `owner_authorized_semantic_alignment` para registrar explicitamente a
   exceção autorizada. Não usar `pre_packet` nem alterar o histórico anterior.
3. Incluir somente estas atualizações, com assert do `source_claim` atual:

   - `G004.source_claim`:
     `Apos testar outros funis, o entrevistado afirma que a VSL e a estrategia mais forte para aquisicao: ela leva publico frio e inconsciente a conversao e reduz as etapas de captacao e aquecimento do lancamento.`
   - `G042.source_claim`:
     `O entrevistado usa o algoritmo do YouTube para identificar videos virais do nicho e transforma-los em referencias de headlines e hooks, cuidando dos direitos autorais e sem reutilizar indevidamente material de concorrentes.`

4. Executar `gold_review_patch --check` uma vez e, se aprovado, `--apply` uma
   vez. Nenhum outro patch ou manifesto de escrita é permitido.
5. Se o apply passar, rodar autocheck estrito, readiness, um build, validador
   normal e export do packet cego. Não executar `--require-external-audit`.

## Critérios de aceite

- somente `source_claim` de `G004` e `G042` muda;
- o autocheck não reporta equivalência semântica pendente nem outro
  `review_required`;
- cobertura continua em 6+ targets distintos;
- readiness, build e validador normal passam;
- o episódio fica em `awaiting_external_audit/pending_external`, com packet de
  cinco arquivos e fingerprints protegidos iguais.

## Limites e parada

Não editar redirects, evidência, números, relações, títulos, takeaways, reviews
de outro candidato, scripts, testes, schemas, docs, auditorias ou outro
episódio. Não criar quarto patch, não reaplicar qualquer patch anterior e não
marcar `passed/complete`. Falha do check/apply ou novo finding encerra o ramo e
é reportada sem outra escrita.
