# Wave 002 do MSF R20 — Épico E1

## Objetivo

Iniciar a próxima wave de forma pequena e mensurável depois do hardening: criar
um packet gold cego, íntegro e pronto para auditoria independente do episódio
`YcqJ_vrjf-g` — *A Fórmula dos Criativos que Vendem 7D/Dia*.

O episódio foi selecionado porque tem tema técnico de criativos de resposta
direta, 1.593 segmentos já disponíveis e fontes raw completas. É uma extensão
controlada do piloto e da Wave 001; não inicia outro episódio nesta delegação.

## Fontes e fronteiras

Somente leitura:

- `C:/MSF-data/Marketing_Swipe_File/raw/youtube/YcqJ_vrjf-g/metadata.json`;
- `C:/MSF-data/Marketing_Swipe_File/raw/youtube/YcqJ_vrjf-g/transcript_original.json`;
- `C:/MSF-data/Marketing_Swipe_File/processed/YcqJ_vrjf-g/content_segments.json`.

Escrita exclusiva do worker:

- `C:/MSF-data/Marketing_Swipe_File/processed/YcqJ_vrjf-g/gold_extraction`;
- `C:/MSF-data/Marketing_Swipe_File/exports/msf_r20_wave_002_YcqJ_vrjf-g`.

Não pertencem ao épico: código, testes, documentação, fila, auditorias seladas,
outros episódios, v2/curated/pool/master, release, consolidação e Supabase.

## Stories internas do épico

| Story | Ação e saída esperada |
| --- | --- |
| E1-S01 — preflight | Registrar `git status`, executar o preflight raw read-only e conferir runtime, fontes, diretórios de escrita exclusivos e fingerprints protegidos. Não escrever se o preflight falhar. |
| E1-S02 — preparação e revisão cronológica | Preparar o episódio e revisar todos os chunks em ordem. Cada review confirma leitura integral, candidatos atômicos, evidência literal, números, passos, condições, caveats, relações e decisões de ledger. Checkpoints ficam somente no chat do worker. |
| E1-S03 — recall adversarial | Repassar o episódio inteiro procurando números, percentuais, preços, períodos, comparações, antes/depois, testes, scripts, passos, mudanças, condições, alertas, caveats e proposições divididas entre chunks. Todo sinal alto recebe destino semântico válido. |
| E1-S04 — prontidão sem escrita | Executar `--check-readiness`. Se houver erro, parar com o inventário exato; não reparar dados no mesmo épico sem nova story planejada. |
| E1-S05 — build e packet | Com prontidão aprovada, rodar um build normal com `--export-suffix msf_r20_wave_002_YcqJ_vrjf-g`, validar normalmente uma vez e confirmar o packet de cinco arquivos em `awaiting_external_audit/pending_external`. |

## Critérios de aceite

- `python -m scripts.reprocess_gold_episode --preflight-raw` passa sem escrita;
- todos os chunks preparados têm review íntegra e candidatos com IDs únicos,
  evidência literal e destino válido no ledger;
- recall adversarial está concluído antes do build;
- `python -m scripts.build_gold_semantic_extraction --check-readiness` passa
  antes do build, sem escrever artefatos;
- build normal, validador normal, ledger e calibração passam sem erro;
- o status é `awaiting_external_audit` com `audit_status=pending_external`;
- o export explícito contém exatamente `packet_manifest.json`,
  `transcript_clean.json`, `insights_exhaustive.json`,
  `high_signal_coverage_ledger.json` e `calibration_tests.json`;
- os fingerprints protegidos permanecem iguais e nada fora do ownership muda.

## Condições de parada

Pare e entregue `blocked` se houver fonte raw inválida, lock/PermissionError,
inconsistência de runtime, falha de prontidão/build/validação, alteração de
fingerprint protegido ou necessidade de editar fora do ownership. A entrega
precisa listar a causa e o inventário exato. Não faça reparo editorial,
reclassificação, segundo build, auditoria ou conclusão `complete/passed` sem
novo épico do coordenador.

## Story corretiva E1-S04a — steps procedurais

O readiness read-only passou em calibração e encontrou somente quatro
frameworks sem `steps`. O coordenador confirmou que os quatro tipos procedurais
são semanticamente adequados; não haverá reclassificação. A correção permitida
é acrescentar apenas os passos abaixo, sustentados pelos claims e segmentos já
citados:

- `G003`: definir se o anúncio busca previsibilidade ou escala; aplicar o
  processo de bater o controle em quatro etapas quando a categoria for
  previsibilidade;
- `G028`: escolher o formato visual; desenvolver a copy; combinar formato e
  copy no criativo;
- `G040`: identificar o copywriter nos anúncios; medir mensalmente lucro ou
  receita atribuída; avaliar pelo resultado financeiro em vez da hit rate;
- `G043`: configurar o agente para produzir CTA com valor, bullets, benefícios
  e prova testimonial.

Somente os arrays `steps` desses quatro candidatos podem mudar. IDs, tipos,
títulos, claims, takeaways, evidências, números, condições, caveats, relações,
ledger e os outros 43 candidatos permanecem idênticos. Depois da correção, o
worker executa readiness uma vez. Se passar, executa um build com o sufixo da
Wave 002, um validador normal e confirma o packet. Qualquer novo erro encerra a
story sem segunda correção ou segundo build.

## Remediação da auditoria E1-S06/E1-S07

O julgamento selado em
`.codex-work/msf-r20-coordinator-audits/YcqJ_vrjf-g_audit.json` está
`changes_requested` com três findings abertos. O worker somente o registra pelo
script determinístico; não pode editar o julgamento.

| Story | Escopo fechado |
| --- | --- |
| E1-S06 — registrar auditoria | Registrar uma vez o audit JSON selado. Não editar candidato, revisão ou packet nesta etapa. |
| E1-S07a — números 001–012 | Revisar G001, G003, G008–G012; adicionar somente números materiais, com `raw` literal e tipagem coerente. |
| E1-S07b — números 014–028 | Revisar G014, G016–G019, G021–G023, G025–G026 e G028 sob a mesma regra. |
| E1-S07c — números 031–046 e encoding | Revisar G031, G033–G041 e G044–G046; corrigir apenas `pe?a` para `peca` em G004 e `portf?lio` para `portfolio` em G036/G039. |
| E1-S07d — evidência de G027 | Reescrever G027 estritamente como: quando só houver manchete e não vídeo, desenvolver a copy com repertório criativo. Sua minimal_quote usa somente 0770 e 0772; 0764 passa a `excluded/interviewer_restate` no ledger. IDs, tipo, relações e os demais candidatos permanecem. |
| E1-S07e — rederivação | Rodar readiness uma vez; se passar, um build com o sufixo da Wave 002 e um validador normal. Atualizar o packet explícito, que deve permanecer `awaiting_external_audit/pending_external` com três findings abertos. |

Para números, a regra é: estruturar somente afirmação quantitativa que sustenta
o claim/takeaway, com `raw` literal presente na minimal_quote, valores e
unidades coerentes e `value_status=reported` quando for caso ou estimativa do
entrevistado. Não transformar ordinais sem valor analítico nem rótulos de
produto, como VEO3, em métricas. Não criar valores, caveats, condições ou
evidência novos.

Qualquer erro novo no readiness, builder ou validator encerra este épico sem
segunda correção. O próximo passo, se o packet for rederivado, é nova auditoria
independente do coordenador.

## Fechamento E1-S08 — registrar reauditoria aprovada

A reauditoria selada
`.codex-work/msf-r20-coordinator-audits/YcqJ_vrjf-g_reaudit_001.json` passou
com `open_findings=0`. O worker só pode executar, nesta ordem: registrar esse
relatório pelo script determinístico, rodar um build com o sufixo explícito da
Wave 002 e rodar o validador com `--require-external-audit` uma vez.

Não pode editar candidato, review, ledger, evidência, packet, auditoria selada,
código ou documentação. O resultado obrigatório é `complete`,
`audit_status=passed`, zero findings abertos, 47 IDs distintos, packet de cinco
arquivos e fingerprints protegidos iguais. Falha do registrador, builder,
validador ou fingerprint encerra a story sem reparo.

## Resultado final

E1 da Wave 002 foi aprovado em 2026-07-11. O relatório de reauditoria passou
com zero findings abertos e foi registrado sem edição. O builder derivou
`complete/passed`; o validador com `--require-external-audit` passou; o episódio
tem 47 IDs distintos, packet com cinco arquivos e quatro fingerprints
protegidos idênticos antes/depois. Nenhum commit, push, deploy, consolidação ou
ação Supabase foi executado.

## Próximo gate

Se o packet estiver pronto, o coordenador faz a auditoria independente. Se
houver bloqueio, o coordenador decide uma story de correção limitada pelo
inventário retornado.
