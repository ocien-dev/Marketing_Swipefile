# Protocolo de execução do Marketing Swipe File

Este repositório usa execução direta por épico no chat ativo. Não existe mais
modelo coordenador/worker, delegação entre chats, `WORKER_EVENT`, heartbeat,
autocontinuação, runner de recuperação ou checkpoint obrigatório.

## Fluxo padrão

- O chat ativo planeja, executa, diagnostica, corrige e valida o épico inteiro.
- Um pedido para iniciar ou executar um épico autoriza seguir todas as stories
  documentadas até o resultado final, salvo decisão material reservada ao owner.
- Erros rotineiros de draft, ASCII, enum, tema, campo, número, steps, relação,
  ledger, calibração, teste ou serialização são resolvidos localmente.
- Não interrompa o épico para revisão intermediária, faixa de chunks, episódio,
  readiness, patch, packet provisório ou limite artificial de tentativas.
- Não envie mensagens para outro chat durante a execução normal.
- Não crie automações, heartbeats, polling, runners persistentes ou mensagens de
  autocontinuação para manter o trabalho ativo.

## Auditoria final única

A auditoria acontece apenas depois que todo o épico estiver executado, corrigido
e deterministicamente validado. Não há auditoria intermediária.

- Antes da auditoria, todos os episódios do escopo devem ter revisão integral,
  recall adversarial, `hard_blockers=0`, finalização válida, packet final e
  fingerprints preservados, ou um bloqueio externo terminal documentado.
- A auditoria final é uma fase dedicada no mesmo fluxo e usa
  `gpt-5.6-sol` com raciocínio `high` ou superior.
- O relatório registra thread, modelo, esforço, rota e findings. O mesmo chat é
  permitido quando a provenance comprova a troca para a fase final Sol.
- `awaiting_external_audit` continua como nome de lifecycle por compatibilidade;
  aqui, `external` significa externo à fase executora, não outro chat.
- Somente auditoria final `passed`, zero findings abertos, validação obrigatória
  aprovada e fingerprints inalterados permitem derivar `complete`.
- Registros históricos de auditoria permanecem imutáveis como provenance.

## Execução gold por episódio e wave

O episódio é a unidade isolada de extração e persistência. A wave ou épico é a
unidade de execução e auditoria final.

1. Registre `git status --short --branch` antes da primeira escrita.
2. Faça preflight de runtime, módulos, temp gravável, ownership, raw, metadata,
   transcript, export e fingerprints.
3. Preserve reviews cujo `input_hash` continue válido.
4. Leia integralmente os chunks pendentes em ordem cronológica.
5. Compile drafts com o compilador oficial e corrija o inventário completo antes
   de cada persistência atômica.
6. Faça recall adversarial global, inclusive fronteiras adjacentes, números,
   comparações, testes, scripts, steps, condições, alertas e caveats.
7. Corrija `hard_blockers` source-backed; mantenha ambiguidades editoriais como
   `audit_warnings` visíveis no packet.
8. Use o finalizador aprovado somente quando o episódio estiver semanticamente
   completo. Não gere packet intermediário.
9. Em waves, processe os episódios sequencialmente e de forma isolada. Um ramo
   terminalmente bloqueado não impede os demais.
10. Depois de todos os ramos terminais, execute o gate consolidado e somente
    então inicie a auditoria final única em Sol.

Ledger e calibração são derivados dos candidatos finais. Uma disposição
`captured` ou `merged` só é válida quando o candidato expressa a mesma
proposição útil sustentada pelo segmento. Quotes verbatim nunca são
normalizadas. Campos editoriais internos seguem ASCII/NFKD conforme o contrato.

## Segurança e ownership

- Preserve mudanças existentes e arquivos não rastreados.
- Não use `reset`, `checkout`, `clean` destrutivo ou equivalente.
- Não force locks do OneDrive nem contorne `PermissionError` com escrita
  concorrente.
- Escreva somente nos caminhos do épico ativo e mantenha episódios isolados.
- Não edite auditorias seladas nem provenance histórico.
- Não consolide gold em `v2/curated/pool/master` nem inicie Supabase sem gate
  funcional separado.
- Não faça commit, push ou deploy sem autorização explícita do owner.
- Dados raw, transcripts, packets e exports locais não devem ser publicados.

## Condições reais de parada

Corrija problemas técnicos rotineiros dentro do épico. Pare e peça decisão
somente quando houver:

- mudança material de escopo, arquitetura, schema público ou fonte de verdade;
- migração, exclusão ou operação irreversível;
- risco de segurança, privacidade ou exposição de credencial;
- serviço pago ou ação externa material;
- produção, commit, push ou deploy sem autorização;
- fonte ausente ou incompatível;
- conflito de ownership;
- lock ou permissão persistente;
- duas rotas atômicas materialmente diferentes falhando;
- corrupção ou rollback impossível;
- fingerprint protegido divergente.

Uma ação indivisível sem progresso observável por 30 minutos deve ser
interrompida. Registre a ação, saída e tempo, escolha uma rota segura
materialmente diferente e continue quando ela permanecer no escopo.

## Encerramento

Ao concluir, relate no próprio chat: estado, episódios, artefatos, validações,
bloqueios e próxima ação. Não gere handoff para coordenador ou worker.

Use `ÉPICO FINALIZADO — PROJETO CONTINUA` quando apenas o épico terminar. Use
`SESSÃO FINALIZADA` somente quando não houver trabalho ativo ou próxima ação
nesta sessão.
