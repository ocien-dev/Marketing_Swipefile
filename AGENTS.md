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

### Arquitetura oficial

A única arquitetura gold de produção é `chronological_hybrid_v1`:

- leitura cronológica integral e composição semântica pelo modelo ativo;
- `transcript_semantic_index`, `semantic_workbench`, inventário numérico,
  calibrações e fronteiras usados apenas como navegação e controle;
- cada risco material fechado como candidato source-backed, suporte retido ou
  exclusão incidental com escopo fonte e justificativa;
- duplicatas exatas bloqueadas para decisão explícita, nunca mescladas
  automaticamente;
- prelint consolidado, persistência/finalização one-shot e auditoria Sol final
  única sobre o dossier source-complete.

Os módulos `gold_semantic_compiler.py`, `gold_semantic_adapter_benchmark.py`,
`gold_semantic_global_reducer.py` e `gold_semantic_inventory.py` são somente
artefatos de pesquisa. Não fazem parte da assinatura executável do runtime,
não substituem a leitura cronológica e não podem processar episódios gold reais
sem um novo épico de benchmark explicitamente autorizado pelo owner.

1. Registre `git status --short --branch` antes da primeira escrita.
2. Faça preflight de runtime, módulos, temp gravável, ownership, raw, metadata,
   transcript, export e fingerprints.
   A fila de prioridade ordena episódios, mas não certifica fontes: a
   disponibilidade real é sempre a leitura do data root ativo para o próximo ID.
   Nunca conclua que há staging WSL, perda de dados ou fonte pronta a partir de
   `source_status` histórico da fila.
3. Preserve reviews cujo `input_hash` continue válido.
4. Leia integralmente os chunks pendentes em ordem cronológica.
5. Na fast lane, inicie por `run_gold_episode_fast.py --context --slabs 3`, use
   `gold_authoring_manifest_v1` e mantenha o job-dir transitório no filesystem
   nativo do runtime Windows.
6. O manifesto autoral é a única fonte de decisões do modelo. Reviews, ledger,
   calibração e workbench são derivados dele; `ledger_updates`, redirects de
   calibração pós-build e helpers específicos do episódio não fazem parte do
   fluxo normal. Compile com `--check` e corrija o inventário esparso completo antes
   da primeira persistência. `--apply` deve consumir o receipt da mesma prévia;
   `--one-shot` pode reunir prévia, apply, finalizer e audit bundle num processo.
   `needs_revision`, `hard_blockers`, `review_gate` e issues do compilador são
   estados diagnósticos locais, não condições de encerramento do chat. Consuma
   o manifesto de reparo, corrija o mesmo manifesto source-backed e repita checks no
   mesmo épico. Não publique resposta final enquanto restar apenas esse tipo de
   inventário rotineiro. O CLI sinaliza isso com `terminal=false`,
   `continue_required=true` e `workflow_disposition` explícito.
7. Faça uma única passagem adversarial global dentro da autoria, inclusive
   ownership de evidência/números, blocos materiais excluídos, fala de host,
   equivalência de calibração, fronteiras adjacentes, comparações, testes,
   scripts, steps, condições, alertas e caveats. Grave o receipt da passagem no
   próprio manifesto; qualquer edição semântica posterior o invalida.
8. Corrija `hard_blockers` source-backed; mantenha ambiguidades editoriais como
   `audit_warnings` visíveis no packet.
9. Use o finalizador aprovado somente quando o episódio estiver semanticamente
   completo. Não gere packet intermediário. O dossier final cria antes da fase
   Sol um `audit_request_receipt` ligado ao seu hash. O primeiro artefato após o
   retorno Sol é o envelope validado; uma interrupção retoma apenas a auditoria.
   Findings geram um único patch do manifesto e reauditoria delta focal.
10. Em waves, processe os episódios sequencialmente e de forma isolada. Um ramo
   terminalmente bloqueado não impede os demais.
11. Depois de todos os ramos terminais, execute o gate consolidado e somente
    então inicie a auditoria final única em Sol.

Ledger e calibração são derivados dos candidatos finais. Uma disposição
`captured` ou `merged` só é válida quando o candidato expressa a mesma
proposição útil sustentada pelo segmento. Quotes verbatim nunca são
normalizadas. Campos editoriais internos seguem ASCII/NFKD conforme o contrato.

## Runtime gold canonico: Windows nativo

O agente do app e o runtime gold usam Windows nativo. Isso preserva a base de
projetos e o historico de chats do Codex, alem de manter o data root ativo.

- Toda operacao gold usa a `.venv` do repositorio e o data root Windows ativo:
  `.\.venv\Scripts\python.exe -m scripts.verify_gold_runtime --runtime windows_native --data-root C:\MSF-data\Marketing_Swipe_File`.
- Antes da primeira escrita, esse verificador deve retornar `status=pass`,
  Python 3.12 da `.venv` e temp gravavel.
- PowerShell e o shell integrado WSL sao somente formas de abrir um terminal.
  Nenhuma dessas preferencias instala, seleciona ou prova uma distribuicao WSL.
  O comando gold canonico continua sendo o Python da `.venv` Windows.
- WSL e opcional e experimental. So pode ser escolhido explicitamente quando
  uma distribuicao estiver registrada, o clone Linux, a `.venv` Linux e o data
  root Linux forem certificados. Nunca deduza isso de um shell configurado como
  WSL e nunca bloqueie um episodio Windows por ausencia de Ubuntu.
- `scripts/invoke_gold_wsl.ps1`, planos e receipts WSL anteriores sao
  provenance historico. Nao sao instrucoes de execucao para um episodio novo.
- Nao use `bash -lc`, here-string, loop ou pipeline PowerShell para encapsular
  uma execucao gold. Passe argumentos explicitos ao Python ou a um launcher
  certificado para evitar perda de quoting e saida.

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

Um `hard_blocker` do prelint bloqueia somente persistência/finalização até ser
corrigido. Ele não é, por si só, um bloqueio terminal do épico. A resposta pode
encerrar como incompleta apenas por uma das condições reais acima, nunca porque
um diagnóstico local ainda exige reparo editorial ou estrutural source-backed.

## Encerramento

Ao concluir, relate no próprio chat: estado, episódios, artefatos, validações,
bloqueios e próxima ação. Não gere handoff para coordenador ou worker.

Use `ÉPICO FINALIZADO — PROJETO CONTINUA` quando apenas o épico terminar. Use
`SESSÃO FINALIZADA` somente quando não houver trabalho ativo ou próxima ação
nesta sessão.
