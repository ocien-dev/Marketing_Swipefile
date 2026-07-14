# Histórico de tarefas do MSF

Este arquivo preserva o histórico dos jobs anteriores. O owner encerrou o
modelo coordenador/worker em 2026-07-14. Ele não é mais fila operacional e não
cria delegações, eventos, checkpoints, heartbeats ou gates intermediários.
O épico ativo é executado integralmente no chat atual; somente a auditoria final
usa `gpt-5.6-sol/high` depois do gate completo.

Status de produção: pre_production. Os gates de release são separados. O gate
de commit foi executado como 3d224f7 e sua validação posterior passou. Push foi
aprovado para main -> origin/main e aguarda execução. Deploy não tem gate porque
nenhum destino não produtivo foi identificado. O job do worker não tem
autoridade de release.

Execução ativa: chat atual, sem papéis separados e sem automação de continuidade.

| Job | Worker | Escopo | Status | Último evento | Gate |
| --- | --- | --- | --- | --- | --- |
| MSF-R20-GATE-001 | Extração Padrão-Ouro (019f4c90-b9dc-7e32-8ff1-57f8896386d3, gpt-5.6-terra/high) | Hardening do gate, correção e rebuild de packet dos quatro episódios R20 pendentes | done | MSF-R20-GATE-001-004 (completed, confirmado no chat do worker) | approved |
| MSF-R20-EXTERNAL-FINDING-001 (tentativa 6: complete) | Extração Padrão-Ouro (019f4c90-b9dc-7e32-8ff1-57f8896386d3, gpt-5.6-terra/high) | Corrigir G028, reparar validação determinística de auditoria pendente, reauditar e derivar conclusão | done | MSF-R20-EXTERNAL-FINDING-001-008 (completed, confirmado no chat do worker) | approved: reauditoria exclusiva Codex aprovada; validação final de auditoria exigida aprovada; complete/passed/zero findings abertos |
| MSF-R20-PILOT-LEARNINGS-001 | Coordenador (gpt-5.6-terra/xhigh) | Medir o piloto de cinco episódios, registrar aprendizados e endurecer gates de preflight e recall semântico | done | fechamento do coordenador | approved: documentação de processo atualizada; nenhum dado de episódio mudou |
| MSF-R20-WAVE-001 (tentativa 28: wave concluída) | Extração Padrão-Ouro (019f4c90-b9dc-7e32-8ff1-57f8896386d3, gpt-5.6-terra/high) | E1 `mCaFyZpXJdE` e E2 `TOW0sWhPaZw` completos, com packets e auditorias aprovadas | done | MSF-R20-WAVE-001-031: E2 complete/passed, 72 IDs, finding resolvido e fingerprints iguais | approved: wave concluída; nenhum commit, push, deploy, consolidação ou Supabase |
| MSF-R20-NEXT-WAVE-HARDENING-001 (tentativa 2) | Extração Padrão-Ouro (019f4c90-b9dc-7e32-8ff1-57f8896386d3, gpt-5.6-terra/high) | Hardening compatível concluído: sufixo explícito de export, preflight raw que também bloqueia `metadata.transcript_status` inválido e prontidão sem escrita | done | WORKER-002 confirmado; revisão independente do coordenador e 16 testes reproduzidos | approved: pronto para a próxima wave; sem dados reais, commit, push, deploy, consolidação ou Supabase |
| MSF-R20-WAVE-002-E1 (tentativa 4: concluída) | Extração Padrão-Ouro (019f4c90-b9dc-7e32-8ff1-57f8896386d3, gpt-5.6-terra/high) | `YcqJ_vrjf-g` completo após reauditoria Codex, 58 números tipados e packet da Wave 002 preservado | done | WORKER-004 confirmado; quality gate independente e `--require-external-audit` reproduzido | approved: `complete/passed`, zero findings, 47 IDs e quatro fingerprints iguais; nenhum commit, push, deploy, consolidação ou Supabase |
| MSF-R20-WAVE-002-E2 (tentativa 6: concluída) | Extração Padrão-Ouro (019f4c90-b9dc-7e32-8ff1-57f8896386d3, gpt-5.6-terra/high) | `qj04cUeaRAw` completo após reauditoria Codex e registro determinístico | done | MSF-R20-WAVE-002-E2-006 confirmado; quality gate reproduziu `--require-external-audit` | approved: `complete/passed`, zero findings, 23 IDs, packet com cinco arquivos e quatro fingerprints iguais; sem commit, push, deploy, consolidação ou Supabase |
| MSF-R20-WAVE-003 (concluída) | Extração Padrão-Ouro (019f4c90-b9dc-7e32-8ff1-57f8896386d3, gpt-5.6-terra/high) | Três episódios padrão-ouro auditados e concluídos | done | WORKER-010 confirmado; coordenador reproduziu 3 validadores com auditoria, 47 IDs únicos, packets 5/5/5 e fingerprints 4/4 em cada episódio | approved: VQJ 24, ICRY 11 e 4Ad 12, todos complete/passed e zero findings; sem commit/push/deploy/consolidação/Supabase |
| MSF-R20-GOLD-FASTPATH-001 (concluído; 2 rodadas corretivas) | Extração Padrão-Ouro (019f4c90-b9dc-7e32-8ff1-57f8896386d3, gpt-5.6-terra/high) | Fast Path unificado para novos/retomáveis/protegidos, com compactação, recorder/patch transacionais, autocheck, runner e delta | done | MSF-R20-GOLD-FASTPATH-001-003 confirmado; 46 testes, compile, help, runner e fingerprints reproduzidos | approved: FP-001 a FP-006 resolvidos; reduções 66%–69%; Wave 003 protegida e 12/12 fingerprints iguais; pronto para nova wave |
| MSF-R20-WAVE-004 (tentativa 26: concluída) | Extração Padrão-Ouro (019f4c90-b9dc-7e32-8ff1-57f8896386d3, gpt-5.6-terra/high) | yyo, 8WE e v6lu completos e protegidos | done | Evento 026 confirmado; quality gate final reproduziu v6lu com auditoria obrigatória | approved: yyo 54, 8WE 42 e v6lu 41 candidatos; todos complete/passed, zero findings e fingerprints preservados |
| MSF-R20-GOLD-FASTPATH-002 (concluído; owner autorizou FP2-002c) | Extração Padrão-Ouro (019f4c90-b9dc-7e32-8ff1-57f8896386d3, gpt-5.6-terra/high) | Otimização ponta a ponta, inclusive reconciliação de exclusões finais válidas | done | Turno final do worker confirmado sem evento 004; coordenador reproduziu 59 testes e rota real de v6lu | approved: previews falsos 779→0, runners read-only e seis status preservados, fingerprints v6lu 4/4 |
| MSF-PROCESS-LEARNING-001 | Coordenador (gpt-5.6-terra/xhigh) | Esteira enxuta de aprendizado, pendências visíveis e encerramento objetivo | done | documentação, fila e skill validadas; nenhum dado gold alterado | approved: registro por recorrência, promoção executável e encerramento objetivo incorporados |
| MSF-R20-WAVE-005 (execução direta) | Chat ativo | zo/JF protegidos; qoh packet-ready; wHdy reviews 001-010 persistidos com 12 IDs; concluir wHdy e Bbh | running | modelo de delegação, heartbeat e runner encerrados pelo owner | concluir o épico neste chat; depois executar uma única auditoria final em gpt-5.6-sol/high |
| MSF-R20-GOLD-FASTPATH-003 (concluído) | Extração Padrão-Ouro (019f4c90-b9dc-7e32-8ff1-57f8896386d3, gpt-5.6-terra/high) | Corrigir prévia automática de ledger antes do build, com regressões | done | evento 001; 48 testes, preview 3009→0 e hash gold igual | approved: precedência do ledger final e prévia automática validadas; dados reais read-only |
| MSF-R20-GOLD-FASTPATH-004 | Extração Padrão-Ouro (019f4c90-b9dc-7e32-8ff1-57f8896386d3, gpt-5.6-terra/high) | Corrigir overlaps lexicais genéricos no autocheck, com regressões | done | evento 001; 51 testes coordenador, compilação e autocheck read-only | approved: overlaps 53→1, ledger automático 0 e demais diagnósticos preservados |
| MSF-R20-GOLD-PIPELINE-SIMPLIFICATION-001 (concluído) | Extração Padrão-Ouro (019f4c90-b9dc-7e32-8ff1-57f8896386d3, gpt-5.6-terra/high) | Revisão completa do episódio, blocker/warning e um packet final transacional | done | evento 003; coordenador reproduziu 65 testes, probes, compilação, skill, diff e read-only | approved: PS-QG-001..005 resolvidos; Wave 005 liberada |
| MSF-R20-GOLD-WAVE-ONE-SHOT-001 (concluído) | Extração Padrão-Ouro (019f4c90-b9dc-7e32-8ff1-57f8896386d3, gpt-5.6-terra/high) | Compilador de batch, recorder idempotente e gate consolidado 5/5 para eliminar microgates | done | 74 testes; probe estrangeiro rejeitado; skill/diff/compile e 509 arquivos read-only aprovados | approved: OS-QG-001..004/003b fechados; Wave 005 liberada |

## Histórico anterior — não é política operacional atual

As seções abaixo documentam decisões e resultados passados. Referências a
coordenador, worker, delegação, evento ou checkpoint não devem ser usadas para
novas execuções.

## Checkpoint de contexto — gate final de 2026-07-11

- Job: MSF-R20-GATE-001 foi aprovado pelo coordenador; ownership e critérios de
  aceite foram preservados.
- Decisões: as quatro reauditorias passaram sem findings abertos; conclusão do
  build foi derivada de relatórios válidos de revisores separados; gates de
  release em pré-produção continuam separados.
- Artefatos: quatro auditorias iniciais seladas, quatro reauditorias aprovadas,
  docs/fila de coordenação e snapshot de fingerprints protegidos.
- Validação: 18 testes puros isolados passaram; cinco casos de diretório temp
  foram bloqueados por permissões do OneDrive, enquanto o worker passou em todos
  os 23. O coordenador rodou validação determinística independentemente, antes
  e depois do registro de auditoria, nos quatro diretórios reais de episódios;
  todos passaram.
- Bloqueios: nenhum. MSF-R20-EXTERNAL-FINDING-001 está completo e aprovado pelo
  coordenador. O worker designado está idle e pronto para job separado.
- Ação ativa: MSF-R20-WAVE-001 está no E1-S08, limitado ao registro
  determinístico da reauditoria aprovada e à validação final. `TOW0sWhPaZw`
  continua bloqueado até o E1 ficar `complete/passed` com zero finding aberto.
  Consolidação gold, Supabase, push e deploy não estão autorizados.
- Contexto: checkpoint durável preservado. Não é alegada compactação manual,
  preventiva ou automática.

Política de contexto: mantenha o mesmo coordenador e worker. Não use App
Server, CLI, scripts, hooks, automações, mensagens slash ou rotação para
compactação preventiva e não bloqueie trabalho por percentual de contexto. O
Codex só pode compactar automaticamente no próprio limite nativo; nenhuma
compactação é alegada sem interface/evento real.

## Regra de processamento

Após despachar um job, o coordenador encerra o turno e não faz polling,
heartbeat, leitura do chat, acompanhamento ou processamento em paralelo enquanto
o worker executa. Checkpoints de progresso ficam no chat do worker e não o
reativam. Ele só retoma quando recebe WORKER_EVENT final de conclusão, bloqueio
ou decisão necessária — ou nova instrução do owner. Ao retomar, deduplica
event_id/job_id e revisa a entrega sequencialmente. Um evento completed é apenas
sinal de entrega, nunca aprovação. Eventos de
segurança, bloqueio e decision_required têm prioridade; as demais conclusões
seguem dependências e FIFO por completed_at.

Antes de cada delegação ao worker, o coordenador publica na conversa um
EXECUTION BRIEF em pt-BR simples e registra sua versão concisa no plano do
épico e em pre_delegation_brief da fila durável. O brief informa propósito,
ações ordenadas, escritas permitidas, artefatos/validações esperados, não ações
explícitas, condições de parada e próximo gate do coordenador. É apenas plano;
a execução começa somente na delegação posterior ao worker.

Para cada job/subtask, registre retornos consecutivos sem progresso. No
terceiro, pare de repetir a mesma instrução, documente a causa comum e envie
alternativa delimitada materialmente diferente. Instalação, comando ou ação
indivisível sem progresso por mais de 30 minutos precisa ser relatado com
tempo e substituído por comando/caminho diferente; esse limite é por ação, não
pela tarefa inteira. Pausas seguras por locks, permissões ou risco de dano
continuam valendo.
