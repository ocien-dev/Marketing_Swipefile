# MSF-R20-WAVE-005 — W5-R05: remediação pré-packet de `zoChfFHnlOQ`

Status: awaiting_worker
Worker: Extração Padrão-Ouro (`019f4c90-b9dc-7e32-8ff1-57f8896386d3`)
Modelo/esforço: `gpt-5.6-terra/high`
Coordenador: `019f4ee6-a00e-7c90-97bc-5c1aae5c8551`

## Objetivo

Fechar somente o inventário editorial finito que permanece depois dos Fast
Paths 003 e 004, gerar o primeiro packet cego válido de `zoChfFHnlOQ` e mantê-lo
em `awaiting_external_audit/pending_external`. Isto não é uma nova leitura do
episódio nem uma auditoria do próprio worker.

## Inventário fechado de entrada

- Números: `G002`, `G004`, `G006`, `G007`, `G008`, `G011`, `G012`, `G021`,
  `G024`, `G031`, `G032`, `G034`, `G037`, `G039`, `G040`, `G041`, `G042`,
  `G044`, `G045` e `G046`.
- Claim/evidência: `G037`.
- Sobreposição material: `G030` e `G034`, compartilhando `concorrentes`,
  `estrutura` e `modelar`.
- Calibração: 1 de 24 targets coberto; mínimo requerido é 6. A ação deve
  produzir pelo menos mais cinco targets distintos, somente quando a
  proposição for diretamente sustentada pelo transcript.

As ocorrências de linguagem de entrevista/promo em `G020`, `G030`, `G031`,
`G032`, `G041` e `G042` não são gate neste inventário: nenhuma é sustentada
somente por entrevistador ou promoção. Não alterar apenas por conter essas
palavras.

## Stories autorizadas

### W5-R05-S01 — Diagnóstico fonte a fonte

1. Registrar `git status --short --branch`.
2. Ler somente os reviews, work orders e segmentos necessários aos 20 números,
   `G037`, `G030/G034` e aos targets de calibração.
3. Criar um manifesto declarativo job-local, com hashes/asserts, que liste a
   ação de cada item: corrigir com literal verbatim, remover record não literal,
   ajustar evidence/claim, estabelecer relação simétrica, merge/removal
   justificado ou manter distinto com justificativa semântica.
4. Para calibração, escolher no mínimo cinco targets atualmente falhos e
   decidir fonte a fonte: cobrir com candidato existente, redirecionar para um
   segmento equivalente ou, somente quando indispensável, criar no máximo cinco
   candidatos novos source-backed para proposições não cobertas.

### W5-R05-S02 — Patches atômicos e limitados

1. Usar no máximo dois patches declarativos: um para candidatos/evidências/
   relações e outro, se necessário, para redireções de calibração.
2. Cada patch exige `--check` read-only, precondições e um único `--apply`
   atômico. Não repetir um apply.
3. Toda relação parent/child deve ser simétrica, acíclica e semanticamente
   necessária. Não adicionar relação apenas para silenciar o alerta de overlap.
4. Nenhum dado fora do inventário pode mudar; nenhuma revisão integral já
   válida pode ser reescrita.

### W5-R05-S03 — Gates e packet

1. Rodar autocheck estrito; itens restantes só podem receber receipt se forem
   verdadeiramente incidentais, com justificativa e hash atual.
2. Rodar readiness final, um build, um validador normal e a exportação do
   packet cego. Não rodar `--require-external-audit`.
3. Confirmar IDs únicos, relações, ledger, targets de calibração distintos,
   packet com cinco arquivos, fingerprints protegidos iguais e lifecycle
   `awaiting_external_audit/pending_external`.

## Ownership permitido

- `C:\MSF-data\Marketing_Swipe_File\processed\zoChfFHnlOQ\gold_extraction`;
- `C:\MSF-data\Marketing_Swipe_File\exports\msf_r20_wave_005_zoChfFHnlOQ`;
- `.codex-work/worker-jobs/MSF-R20-WAVE-005`.

As fontes raw e todos os scripts são somente leitura/execução. O worker não
edita plano, fila, documentação central, scripts, testes, schemas ou auditorias
seladas.

## Critérios de aceite

- os 20 alertas numéricos passam a ter literal verbatim válido ou record
  removido; nenhum número inferido permanece;
- `G037` fica lexicalmente sustentado ou é corrigido/removido com evidência;
- `G030/G034` fica semanticamente distinto com justificativa ou recebe a única
  relação/merge/removal que o transcript exigir;
- pelo menos 6 targets de calibração distintos passam semanticamente, sem dupla
  contagem e sem cobertura inventada;
- autocheck estrito, readiness, build e validador normal passam;
- há exatamente cinco arquivos no packet e fingerprints protegidos não mudam.

## Paradas

- uma correção requer alterar script, schema, contrato, auditoria ou episódio
  fora do ownership;
- correção adicional exigiria um terceiro patch ou segundo build;
- lock, `PermissionError`, inconsistência de hash ou precondição falha;
- número/candidato/calibração sem suporte direto do transcript;
- qualquer ação indivisível sem progresso por 30 minutos.

Nesse caso, pare antes de escrever fora do escopo e envie o evento final com o
inventário exato. O coordenador revisa a entrega e, se houver packet, faz a
auditoria cega independente.
