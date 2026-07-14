# MSF-R20-WAVE-005 — W5-R06: patch final de calibração de `zoChfFHnlOQ`

Status: awaiting_worker
Worker: Extração Padrão-Ouro (`019f4c90-b9dc-7e32-8ff1-57f8896386d3`)
Modelo/esforço: `gpt-5.6-terra/high`
Coordenador: `019f4ee6-a00e-7c90-97bc-5c1aae5c8551`

## Estado aprovado de entrada

O primeiro patch W5-R05 foi auditado pelo coordenador e está aprovado. Ele
alterou exatamente os 21 candidatos permitidos, mantém 48 IDs únicos e eliminou
os alertas numéricos, claim/evidência e overlap. Não pode ser reexecutado.

O segundo patch não foi aplicado: o `--check` falhou antes de escrever a
calibração, porque o manifesto comparou `semantic_candidate_ids: []` com um
campo que está ausente no target original. Campo ausente não é lista vazia no
contrato de assert do patcher.

O autocheck posterior revelou também um único caveat pendente em `G031`, que
foi alterado pelo primeiro patch. A correção de caveat entra no patch final, em
vez de abrir um terceiro patch.

## Única story autorizada — W5-R06-S01

1. Registrar `git status --short --branch` e ler o plano W5-R05 e este plano.
2. Criar um novo manifesto job-local `zo_calibration_final_patch.json`.
   - Para cada redirect, o assert deve verificar somente campos que realmente
     existem no JSON atual: `segment_ids` e `quote_verbatim`.
   - Não usar `semantic_candidate_ids` no assert quando o campo estiver ausente.
   - Manter os cinco redirects previamente revisados para `G004`, `G004`,
     `G042`, `G044` e `G046`, com targets distintos e provenance de origem.
   - Incluir somente a atualização de caveat de `G031`, com assert do seu
     estado atual e texto honesto de caso reportado; não alterar claim, número,
     evidence, relação, título ou takeaway de `G031`.
3. Compilar qualquer helper sem gerar `.pyc`; rodar um único `--check`.
4. Se o check passar, rodar um único `--apply` atômico. Se não passar, parar;
   não criar outro manifesto nem repetir apply.
5. Rodar autocheck estrito, readiness final, um build, validador normal e
   export do packet cego. Não rodar `--require-external-audit`.

## Critérios de aceite

- a precondição usa o estado real do target, sem transformar campo ausente em
  lista vazia;
- seis ou mais targets de calibração distintos passam, sem duplicatas;
- `G031` deixa de ter caveat pendente e nenhum campo além de `caveats` muda;
- autocheck estrito, readiness, build e validador normal passam;
- lifecycle final é `awaiting_external_audit/pending_external`, packet tem cinco
  arquivos e fingerprints protegidos permanecem iguais.

## Ownership e proibições

Escritas permitidas: somente
`C:\MSF-data\Marketing_Swipe_File\processed\zoChfFHnlOQ\gold_extraction`,
`C:\MSF-data\Marketing_Swipe_File\exports\msf_r20_wave_005_zoChfFHnlOQ` e
`.codex-work/worker-jobs/MSF-R20-WAVE-005`.

Não tocar outros episódios, scripts, testes, schemas, documentação central,
auditorias, release, master ou Supabase. Não reexecutar o primeiro patch, não
criar terceiro patch e não marcar `passed` ou `complete`.

## Parada

Se o check falhar, se algum redirect não for semanticamente sustentado, se a
atualização exigir alterar outro candidato ou se houver lock/PermissionError,
pare e envie o inventário exato ao coordenador. Nenhuma tentativa alternativa
de escrita é autorizada nesta story.
