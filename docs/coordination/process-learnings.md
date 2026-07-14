# Aprendizados do processo

Registro canônico de fricções recorrentes e prevenções do Marketing Swipe File.
O chat ativo atualiza este arquivo no encerramento de um épico. O objetivo é
transformar repetição em regra executável, não acumular relatos de sessão.

## Critério de entrada

- Primeira ocorrência: registrar apenas no execution log ou no fechamento local
  do épico.
- Segunda ocorrência concreta: criar ou atualizar uma entrada aqui.
- Terceira ocorrência: impedir a quarta repetição do mesmo caminho até haver
  prevenção ou alternativa materialmente diferente.
- Risco crítico, corrupção possível ou quebra de proteção: promover de imediato.

Uma entrada só conta como recorrência quando há evidência da mesma causa, e não
apenas sintomas parecidos. Aprendizados já prevenidos por código ou teste ficam
como `promoted`; limitações externas aceitas ficam como `accepted_limitation`.

## Destino da promoção

| Natureza | Destino preferencial |
| --- | --- |
| Falha determinística recorrente | script, guard ou teste |
| Regra estável de execução | `AGENTS.md` |
| Heurística específica da extração gold | skill ou prompt gold |
| Decisão de projeto | plano e `docs/execution-log.md` |
| Limitação externa não corrigível | esta lista como limitação conhecida |

Não duplicar a mesma regra em todos os destinos. A documentação aponta para o
mecanismo canônico; testes e scripts são preferidos quando puderem impedir a
falha antes da escrita.

## Registro

| ID | Estado | Escopo | Evidência e causa | Prevenção permanente | Promovido para |
| --- | --- | --- | --- | --- | --- |
| MSF-PL-001 | promoted | patches de gold e ledger | Em v6lu, tentou-se editar manualmente decisões de ledger ausentes; o ledger canônico é derivado da evidência dos candidatos durante o build. | Alterar a evidência source-backed, rederivar e validar o ledger; só criar `ledger_decisions` quando o contrato realmente exigir decisão manual. | skill gold e fluxo transacional existente |
| MSF-PL-002 | promoted | hashes de packet | CRLF/LF produziu hashes físicos diferentes para JSON semanticamente idêntico. | Comparar hash físico e hash semântico JSON e tratar newline isolado como provenance de serialização. | Fast Path 002 e skill gold |
| MSF-PL-003 | promoted | carga ativa de waves | Planejar somente por quantidade de episódios ocultava waves com muitos chunks ativos. | Orçar segmentos/chunks ativos e dividir revisão em faixas planejadas de 8–12 chunks. | `run_gold_wave.py` e skill gold |
| MSF-PL-004 | promoted | remediação gold | Helpers ad hoc e reaplicações geraram loops e risco de estado parcial. | Exigir `--check` read-only, asserts/precondições, um único `--apply` atômico e validação final. | `gold_review_patch.py`, testes e skill gold |
| MSF-PL-005 | retired | transporte entre chats | O transporte de eventos entre papéis separados acrescentou latência, custo e falhas de continuidade. | Modelo removido pelo owner; executar o épico integralmente no chat ativo e reservar troca de modelo apenas para a auditoria final. | `AGENTS.md` e contrato gold |
| MSF-PL-006 | promoted | autocheck pré-build | Em Wave 005, 3.009 sinais viraram pendência porque a prévia consultava somente ledger manual antes do ledger derivado existir. | Usar `ledger_for_signals()` em memória antes do build e manter pendente apenas decisão inválida ou ausente. | Fast Path 003, regressões e diagnóstico read-only; validado por 0 previews na Wave 005 |
| MSF-PL-007 | promoted | unidade de execução da wave | Mesmo após a simplificação, erros mecânicos de payload e checkpoints de chunks encerraram turnos e provocaram retornos sucessivos ao coordenador. A causa era a validação fail-fast acoplada ao recorder e a ausência de um gate consolidado de cinco episódios. | Compilador read-only com inventário completo, recorder idempotente verificável e gate 5/5 que não emite receipt em progresso e vincula cada packet ao episódio/manifesto. | `MSF-R20-GOLD-WAVE-ONE-SHOT-001`, aprovado com 74 testes e probes adversariais |
| MSF-PL-008 | retired | continuidade automatizada | Self-message, heartbeat e runner persistente não entregaram avanço proporcional e aumentaram o custo operacional. | Não automatizar continuidade do chat; executar diretamente e tratar apenas ações individuais sem progresso por 30 minutos. | `AGENTS.md`; automação e runner removidos |
| MSF-PL-009 | promoted | encerramento direto de waves | A Wave 005 só avançou de forma consistente quando a execução, as correções source-backed, o gate 5/5 e a revisão final ficaram no mesmo chat. Coordenação inter-chat multiplicou contexto, transporte e paradas sem aumentar a qualidade. | Executar todo o épico no chat ativo; reservar `gpt-5.6-sol/high` para uma única auditoria final após o gate consolidado. | `AGENTS.md`; Wave 005 concluída 5/5, reauditoria final sem findings |

## Modelo para novas entradas

~~~text
ID:
estado: observed | recurring | action_required | promoted | closed | accepted_limitation
escopo:
primeira_ocorrencia:
ultima_ocorrencia:
recorrencias_confirmadas:
sintoma:
causa_confirmada:
evidencia:
contencao_imediata:
prevencao_permanente:
promovido_para:
responsavel:
validacao:
~~~

## Revisão no fechamento de épico

No encerramento do épico, o chat ativo:

1. analisa somente observações concretas de `process_learnings`;
2. deduplica por causa confirmada;
3. atualiza contagem e estado;
4. promove para o destino mais específico, se necessário;
5. registra como a prevenção foi validada;
6. mantém a entrada aberta apenas quando ainda houver ação real.
