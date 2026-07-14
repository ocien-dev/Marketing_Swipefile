# Retrospectiva do piloto gold MSF-R20

Data: 2026-07-11
Job: MSF-R20-PILOT-LEARNINGS-001
Owner: coordenador Codex
Escopo: os cinco episódios selecionados em docs/msf-r20-pilot-plan.md

## Resultado

Os cinco episódios do piloto estão complete, com audit_status=passed, zero
findings abertos, calibrações aprovadas e fingerprints protegidos preservados.
O quality gate do coordenador continua separado do trabalho do executor. Nenhum
dado gold foi consolidado em v2, curated, pool ou master.

| Episódio | Segmentos limpos | Chunks | Candidatos | Entradas do ledger | Calibração |
| --- | ---: | ---: | ---: | ---: | ---: |
| awbrqeqq-io | 341 | 6 | 14 | 55 | 7/3 pass |
| 35uL_nCmZ0k | 688 | 12 | 17 | 208 | 5/3 pass |
| _hXmiIEac6w | 1.531 | 25 | 28 | 1.078 | 6/4 pass |
| aSFAve1klsc | 1.242 | 22 | 58 | 844 | 5/4 pass |
| cL3FuW8bAMA | 1.806 | 32 | 78 | 1.584 | 9/5 pass |
| **Total** | **5.608** | **97** | **195** | **3.769** | **32/19 pass** |

L7u7r6rOl68 é a baseline pré-piloto e também está gold complete, mas não entra
na tabela do piloto R20 de cinco episódios.

## Perfil dos findings

Os quatro packets R20 revisados inicialmente às cegas produziram 16 findings. O
follow-up posterior de _hXmiIEac6w adicionou um finding de recall e ledger.
Nesses 17 findings houve 8 major e 9 minor:

| Categoria | Quantidade |
| --- | ---: |
| Editorial | 7 |
| Calibração | 4 |
| Números | 3 |
| Ledger | 1 |
| Recall | 1 |
| Recall e ledger | 1 |

As falhas dominantes foram claims editoriais duplicados ou fracos, caveats
ausentes, material promocional ou de entrevistador promovido a insight,
problemas de normalização numérica, targets de calibração duplicados pela forma
superficial e relação semântica útil omitida apesar de sinais lexicais próximos
terem cobertura no ledger.

## Decisões para a próxima wave gold

### 1. Manter a arquitetura

Continue usando chunks cronológicos limpos, reviews persistentes, camada
exaustiva de candidatos, números tipados, evidência literal em camadas, ledger
com destino completo, calibrações semânticas, packet cego e auditoria Codex
separada. Não enfraqueça a auditoria independente para economizar tokens.

### 2. Adicionar gate de recall do executor antes da auditoria

Cobertura estrutural é necessária, mas não suficiente. Antes de exportar o
packet, o executor faz uma passagem adversarial separada e pergunta se toda
proposição útil está representada, inclusive relações que atravessam segmentos
adjacentes ou conectam história, mecanismo, pitch, retenção, oferta, causa,
resultado, condição e caveat.

Para cada item captured ou merged do ledger, o candidato referenciado precisa
dizer a mesma proposição útil. Candidato amplo, número próximo ou tópico
compartilhado não é cobertura semântica. Qualquer incompatibilidade reabre o
chunk afetado ou o par de chunks adjacentes antes da auditoria.

### 3. Rodar preflight técnico uma vez por job

Antes de escrever dados de episódio, registre estado do Git e confira runtime
Python selecionado, módulos exigidos, diretório temporário gravável específico
do job, acesso ao data root, caminhos do packet, snapshot de fingerprints
protegidos e ownership de scripts necessários para alcançar o lifecycle de
aceite. Não descubra lacunas de runtime ou ownership depois de concluir o
trabalho editorial.

### 4. Separar gates determinísticos e de aprovação

A validação determinística normal pode passar enquanto um relatório de auditoria
válido está changes_requested, com findings abertos. Somente a validação que
exige auditoria e o lifecycle complete exigem passed sem findings abertos. Teste
os dois caminhos explicitamente depois de uma correção.

### 5. Minimizar o contexto do worker

Envie ao worker apenas AGENTS.md, contrato ativo do job, caminhos relevantes de
artefatos, findings exatos ou segmentos alvo, critérios de aceite e comandos.
Não reenvie o chat histórico, o log de execução completo nem raciocínios
anteriores. Reutilize reviews de chunks e inventários de sinais correspondentes
por hash; reabra apenas chunks alterados e o contexto semântico adjacente
necessário para validá-los.

### 6. Acompanhar métricas da wave

Para cada episódio futuro, registre segmentos limpos, chunks, candidatos,
entradas do ledger, cobertura/mínimo de calibração, findings por categoria e
severidade, rodadas de correção, bloqueios e tempo decorrido. Registre uso de
tokens somente quando a superfície expuser valor confiável. Essas métricas
definirão o tamanho de lotes futuros e identificarão oportunidades repetíveis de
automação.

## Decisão de prontidão

O processo gold está pronto para continuar depois que os gates de preflight e
recall semântico adversarial forem incluídos em todo contrato novo de worker.
Uma wave ampla nova deve começar pequena e delimitada para o coordenador
verificar a queda na taxa de findings antes de aumentar concorrência ou
quantidade de episódios.
