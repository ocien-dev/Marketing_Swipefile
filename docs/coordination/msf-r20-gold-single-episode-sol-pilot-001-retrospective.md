# Retrospectiva do piloto gold single-episode Sol

Data: 2026-07-15
Job: `MSF-R20-GOLD-SINGLE-EPISODE-SOL-PILOT-001`
Episódio: `aFabW0i9K20`
Modelo: `gpt-5.6-sol/high`
Runtime: Ubuntu 24.04 / WSL 2

## Veredito

| Dimensão | Resultado | Decisão |
| --- | --- | --- |
| Qualidade | 19/19 reviews, 45 candidatos únicos, `hard_blockers=0`, auditoria final `passed/0`, fingerprints 4/4 | verde |
| Tempo | 2.279 segundos observados, aproximadamente 37:59, contra meta de 10:00 | vermelho |
| WSL | nenhuma escrita gold via PowerShell, nenhum Python Windows e nenhum fallback; um recovery de preflight e um warning não fatal de systemd | verde com ação de estabilidade |
| Sol/high | primeiro audit passou sem correção pós-auditoria, mas não houve controle A/B nem medição de tokens | sinal positivo, ainda inconclusivo |
| Subagentes | não usados; o histórico e a estrutura do episódio indicam custo de merge maior que o ganho provável | não usar no próximo piloto |

O piloto aprovou a arquitetura de qualidade e o uso direto do WSL, mas falhou no
objetivo de desempenho. Pelo próprio critério do plano, mais de 15 minutos é
resultado vermelho. O próximo passo não deve ser aumentar a wave; deve ser
eliminar o retrabalho pré-packet e reduzir o volume de contexto operacional.

## Evidência medida

O receipt job-local mede 2.279 segundos entre sua criação e a verificação final.
Como o timer monotônico por story não foi iniciado corretamente, a decomposição
abaixo é reconstruída pelos timestamps dos artefatos e deve ser lida como
aproximação observada, não como telemetria de alta precisão.

| Intervalo observado | Duração | Participação aproximada | Conteúdo |
| --- | ---: | ---: | --- |
| Preflight, leitura integral e composição do draft | 15:51 | 42% | 1.067 segmentos, 19 chunks e 45 candidatos |
| Emissão do payload e matriz de recall | 2:06 | 6% | payload de 130.959 bytes e matriz de 501.288 bytes |
| Diagnóstico e primeira correção pré-packet | 6:08 | 16% | seis alertas numéricos em cinco reviews |
| Correção residual de `G016` | 5:08 | 14% | falso positivo causado pelo artigo `uma` em `uma lead` |
| Finalizer, freeze, auditoria e conclusão | 7:33 | 20% | packet, audit `passed`, build `complete` e validator obrigatório |
| Fechamento de receipt e verificações finais | cerca de 1:13 | 3% | hashes, Git e resumo final |

O diretório job-local terminou com 14 arquivos e 945.320 bytes. Desse total,
62.526 bytes são helpers Python e 882.794 bytes são JSON. Os maiores artefatos
foram a matriz de recall com 501.288 bytes, o payload completo com 130.959 bytes
e dois probes de auditoria com 99.919 bytes cada. O volume em disco é aceitável,
mas sinaliza repetição de estrutura e contexto que o modelo precisou produzir,
inspecionar ou transportar.

## O que funcionou

1. O episódio inteiro foi lido antes da persistência inicial. Não houve packet
   parcial nem checkpoint editorial intermediário.
2. A persistência inicial foi uma única transação atômica de 19 reviews e 45
   candidatos.
3. O WSL foi a fonte de execução real: zero escritas gold por PowerShell, zero
   invocações do Python Windows e nenhum fallback para `C:\MSF-data`.
4. Os gates determinísticos foram rápidos quando finalmente receberam estado
   limpo. O finalizer levou cerca de 3,2 segundos e o validator obrigatório
   cerca de 7,7 segundos.
5. O packet final contém exatamente cinco arquivos, todos os candidatos são
   referenciados pelo ledger, as relações são válidas e a calibração passou com
   6 de 12 targets cobertos para mínimo 3.
6. A auditoria final Sol/high passou na primeira rodada, sem finding e sem
   correção pós-auditoria. Isso é uma melhora operacional clara em relação à
   Wave 006, que acumulou de quatro a seis patches, cinco builds e três audits
   por episódio.

## O que não funcionou

### 1. A rota one-shot existente foi contornada

O repositório já possui `scripts/run_gold_episode_fast.py`. Seu `--check`
compila o payload e executa `autocheck_state()` sobre a composição final em
memória; seu `--apply` só persiste quando o preview está limpo e chama o
finalizer uma vez.

No piloto, o payload passou pelo recorder, foi persistido e somente depois o
autocheck estrito foi executado. Com isso, seis hard blockers apareceram tarde
e exigiram dois patches. Esse desvio de rota explica aproximadamente 11:16, ou
30% do tempo observado. O problema principal não foi falta de script; foi falta
de enforcement do caminho aprovado.

### 2. A seleção de evidência ficou ampla demais

Dos seis alertas iniciais, `G004` tinha um número material real que precisava
ser estruturado. `G008`, `G015`, `G016`, `G023` e `G044` carregavam segmentos
numéricos incidentais além do necessário para sustentar sua proposição. A
evidência mínima deveria ter sido menor, deixando contexto adicional em suporte
somente quando ele realmente acrescentasse sustentação.

### 3. A heurística numérica produziu falso positivo em português

Depois da primeira correção, `G016` continuou bloqueado porque o regex tratou
`uma lead` como contagem material. A correção semanticamente correta foi
estreitar claim e evidência, não cadastrar um número falso. O detector precisa
usar o inventário de sinais e marcadores inequívocos de quantidade, distinguindo
artigos `um/uma` de numerais.

### 4. A instrumentação não cumpriu o plano

O receipt final registra o tempo total, mas não possui timers monotônicos por
story nem uso de tokens. Os tempos por fase precisaram ser reconstruídos por
mtime. Sem telemetria nativa, não é possível comparar modelos ou otimizações
com rigor suficiente.

### 5. A fronteira Windows/WSL ainda introduziu variância

Os dados e scripts gold rodaram no Linux, mas helpers e manifestos job-local
foram lidos e escritos por `/mnt/c/Users/.../OneDrive`. Uma geração levou 45,8
segundos, um check levou 18,7 segundos e o build final levou 35,1 segundos. Isso
não dominou o total, mas é variância evitável. O trabalho transitório deve ficar
em filesystem Linux e apenas o receipt final deve ser sincronizado para o
checkout Windows.

### 6. O audit bundle foi criado ad hoc

Foi necessário escrever um probe de auditoria para verificar identidade do
packet, cobertura de candidatos pelo ledger, relações e calibração. Essa prova
deve ser um derivado padrão do finalizer, não um helper novo por episódio.

## Avaliação do modelo 5.6 Sol/high

### Sinais favoráveis

- O primeiro audit final passou com zero findings.
- Houve uma única auditoria e nenhum loop pós-auditoria.
- O episódio gerou 45 proposições source-backed em 1.067 segmentos sem IDs
  duplicados, relação inválida ou lacuna de ledger.
- Comparativamente, a Wave 006 terminou bem, mas precisou de quatro a seis
  patches, cinco builds e três audits por episódio. O piloto reduziu muito essa
  superfície de retrabalho.

### Limitações da conclusão

- Não houve extração Terra e Sol do mesmo episódio sob o mesmo pipeline.
- O episódio e o processo diferem dos episódios da Wave 006.
- O mesmo modelo executou e auditou em fases distintas. O packet congelado e a
  provenance reduzem o risco, mas não dão a mesma independência de um revisor
  com contexto separado.
- A plataforma não expôs uso confiável de tokens. Não é possível quantificar o
  custo adicional do Sol/high.
- O draft ainda chegou ao primeiro autocheck com seis blockers. O modelo mais
  forte não compensou o desvio da rota one-shot nem a heurística defeituosa.

### Conclusão sobre o Sol

O ganho de qualidade é provável, mas não está causalmente provado. O resultado
mais defensável é: `Sol/high` mostrou bom desempenho semântico e eliminou o loop
pós-auditoria neste episódio, porém não trouxe ganho de velocidade e pode ter
custo maior de tokens. Manter Sol/high na leitura, composição, recall e audit
final é razoável durante mais dois pilotos; afirmar que ele é melhor que Terra
exige um experimento controlado.

## Avaliação de subagentes paralelos

### Dentro de um único episódio

Não recomendado. Dividir chunks entre subagentes pode reduzir a leitura bruta,
mas cria quatro custos novos: repetição do contrato e contexto, namespace de
candidatos, reconciliação de duplicatas e releitura global das fronteiras. Como
o episódio exige recall cruzado e relações entre proposições distantes, o merge
volta a concentrar trabalho no agente principal. O ganho de parede provável é
pequeno e o consumo total de tokens tende a aumentar materialmente.

Subagentes especializados para números, ledger ou calibração também não são
atraentes: o autocheck determinístico executa essas verificações em frações de
segundo quando recebe o draft correto.

### Entre episódios independentes

Pode haver ganho futuro, porque cada episódio possui gold, export e namespace
isolados. Ainda assim, o histórico do projeto mostrou que coordenação,
transporte e merge consumiram mais do que economizaram. Paralelismo entre
episódios só deve ser reavaliado depois de três episódios sequenciais cumprirem
zero patch pós-write e mediana estável. Nesse ponto, no máximo dois episódios
em paralelo, sem mensagens intermediárias e com gate final único, seria um
experimento aceitável.

### Paralelismo recomendado agora

Usar apenas paralelismo de ferramentas read-only para hashes, preflight,
inventários e provas finais. Isso reduz espera sem duplicar interpretação
semântica nem criar agentes adicionais.

## Backlog priorizado

### P0 - antes do próximo episódio

1. Tornar `run_gold_episode_fast.py --check` a rota obrigatória para payload
   completo. O finalizer deve exigir receipt de preview com o mesmo hash
   semântico antes da primeira persistência de um episódio novo.
2. Executar `--apply` somente sobre o mesmo payload/hash aprovado pelo check.
   Não chamar recorder e autocheck separadamente no caminho normal.
3. Corrigir a detecção de números escritos para não tratar artigo `um/uma` como
   quantidade sem sinal numérico ou marcador inequívoco. Adicionar regressões
   para `uma lead`, `um produto` e contagens reais como `uma única venda`.
4. Instrumentar timers monotônicos desde o primeiro preflight para leitura,
   composição, compiler, autocheck, persistência, finalizer, audit e conclusão.

Aceite P0: episódio sintético com falso artigo não bloqueia; número real ainda
bloqueia; payload real inválido produz zero write; episódio limpo usa um check,
uma persistência e um finalizer.

### P1 - redução de contexto e variância

1. Criar um formato compacto de draft com campos semânticos e IDs/ranges de
   evidência. Um expansor genérico deriva quotes e boilerplate. Não gerar helper
   Python de dezenas de kilobytes por episódio.
2. Substituir a matriz de recall materializada integralmente por uma visão
   esparsa para o modelo: mostrar apenas sinais sem destino, exclusões duvidosas,
   calibrações falhas, números pendentes, fronteiras e overlaps. A matriz cheia
   pode continuar derivada em disco.
3. Ler work orders em duas ou três faixas cronológicas grandes, com fronteiras
   explícitas, em vez de uma chamada por chunk.
4. Manter manifests, payloads e helpers transitórios em job-local Linux nativo,
   como `/home/luish/.cache/msf/jobs/<job_id>`, e sincronizar apenas receipts e
   artefatos finais necessários para o checkout Windows.
5. Fazer uma única invocação WSL do driver one-shot para check/apply/finalizer,
   preservando a auditoria como fase posterior separada.
6. Gerar automaticamente um `final_audit_bundle.json` compacto com candidatos,
   minimal evidence, números, caveats, warnings, ledger, calibração, relações,
   fingerprints e snapshot do packet.

Aceite P1: reduzir em pelo menos 60% os bytes job-local voltados ao modelo e
eliminar helpers corretivos/audit probes específicos do episódio.

### P2 - prova de modelo e escala

1. Rodar dois pilotos adicionais de 800 a 1.200 segmentos após P0/P1.
2. Só depois executar um A/B controlado em temp isolado: draft Sol/high versus
   draft Terra/high sobre a mesma fonte e mesmo compiler; auditoria Sol com
   rótulos ocultos; nenhuma das duas variantes escreve no gold real.
3. Medir tempo até preview limpo, blockers, findings major/minor, recall em
   amostra adversarial e tokens somente se a plataforma os expuser.
4. Reavaliar dois episódios paralelos somente se três execuções sequenciais
   tiverem zero patch pós-write e mediana previsível.

## Impacto esperado

As estimativas abaixo são de engenharia e devem ser validadas, não tratadas
como métricas já alcançadas.

| Mudança | Economia provável neste perfil |
| --- | ---: |
| Enforcement one-shot e correção da heurística numérica | 9 a 12 min |
| Draft compacto, leitura em faixas e recall esparso | 5 a 9 min |
| Job-local Linux e menos invocações WSL | 1 a 3 min |
| Audit bundle padrão | 1 a 3 min |

Para um episódio de 1.067 segmentos, a meta realista após P0/P1 é 14 a 20
minutos, não dez. Uma meta de dez minutos continua plausível para episódios de
até aproximadamente 600 segmentos. Para 600 a 1.200 segmentos, usar 12 a 18
minutos como faixa operacional inicial; acima disso, medir custo por 100
segmentos em vez de impor teto que incentive perda de recall.

## Próximo gate

Implementar P0 e P1 em um épico técnico sem tocar gold real. Depois repetir um
único episódio comparável, exigindo: um preview limpo antes da escrita, uma
persistência, um finalizer, primeiro audit sem finding, telemetria completa e
tempo total de até 18 minutos. Não usar subagentes nesse próximo teste.

## Implementação P0/P1

Status em 2026-07-15: implementado e validado em fixtures; nenhum episódio real
foi processado nesta mudança.

- `--check` agora produz um receipt job-local ligado aos hashes semânticos do
  payload, fontes preparadas, reviews compostos, revisão e export. `--apply`
  rejeita receipt ausente ou stale, e o finalizer reconfirma reviews e receipt
  do recorder antes do build.
- `--one-shot` reúne preview, receipt, persistência, finalização e bundle final
  de auditoria em um processo, mantendo todos os gates.
- O detector numérico não trata mais `um/uma` como quantidade sem qualificador;
  `uma lead` e `um produto` não bloqueiam, enquanto `uma única venda`, `apenas
  uma venda` e `duas vendas` continuam materiais.
- `gold_episode_compact_v1` adiciona defaults, aliases e ranges de clean index;
  a fixture ficou abaixo de 40% dos bytes do payload verboso equivalente.
- `--context --slabs 3` emite cada segmento uma única vez em no máximo três
  faixas e inicia telemetria monotônica desde o preflight.
- A saída normal usa recall esparso, e `final_audit_bundle.json` substitui probes
  ad hoc sem entrar no packet público de cinco arquivos.
- O job-dir da rota WSL é validado como Linux-native; `/mnt` é recusado dentro
  do WSL.

O próximo gate permanece um piloto real comparável com meta de 14 a 20 minutos
para aproximadamente mil segmentos e até 18 minutos como alvo operacional.

Validação técnica: 94 testes Fast Path/pipeline aprovados, `py_compile`,
`quick_validate` da skill e `git diff --check` aprovados. As varreduras read-only
dos data roots Windows e WSL encontraram zero arquivo real modificado durante o
épico técnico.
