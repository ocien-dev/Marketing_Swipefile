# MSF-R20-WSL-DEFAULT-001 - WSL como runtime padrao

Status: planned - aguardando checkpoint Git/GitHub e instalacao da distro
Owner: chat ativo
Production status: pre_production
Distribuicao alvo: Ubuntu 24.04 LTS sobre WSL 2

## Objetivo

Migrar o runtime padrao do Marketing Swipe File para WSL 2, mantendo o
repositorio, o data root, o temp e a virtualenv no filesystem Linux. A mudanca
deve reduzir locks do OneDrive, erros de permissao, custo de milhares de
operacoes pequenas e divergencias de ambiente, sem alterar qualquer dado gold
ou lifecycle durante a migracao.

## Estado confirmado

- WSL 2 esta habilitado, mas nenhuma distribuicao esta instalada.
- `Ubuntu-24.04` esta disponivel para instalacao.
- Repositorio atual: aproximadamente 0,98 GB e 27.839 arquivos.
- Data root atual: aproximadamente 6,53 GB e 52.040 arquivos.
- O branch `main` esta quatro commits a frente de `origin/main` e possui um
  worktree grande com mudancas rastreadas e nao rastreadas.
- Os scripts e testes nao possuem paths Windows relevantes hardcoded; usam
  `pathlib`, `sys.executable` e `MSF_DATA_DIR`.
- Exemplos Windows permanecem em 41 arquivos de docs, skills, prompts e loops.
- Git Windows usa `core.autocrlf=true`; o repositorio nao possui
  `.gitattributes`.

## Arquitetura alvo

```text
Ubuntu-24.04 (WSL 2)
  /home/luish/src/Marketing_Swipe_File
  /home/luish/msf-data/Marketing_Swipe_File
  /home/luish/.cache/msf/tmp
  /home/luish/src/Marketing_Swipe_File/.venv

Windows
  Chrome e capturas que dependam da sessao visual do usuario
  C:\MSF-data\Marketing_Swipe_File como rollback read-only temporario
```

Nao usar `/mnt/c` como local primario de repositorio, data root, temp ou venv.
Essa rota manteria o custo de NTFS/OneDrive e pode ser mais lenta para dezenas
de milhares de arquivos pequenos.

## Estrategia de backup

### Repositorio

GitHub protege somente arquivos versionados. Antes da migracao:

1. revisar o diff e procurar segredos ou dados locais;
2. criar um branch de checkpoint;
3. commitar o estado aprovado, incluindo novos scripts e planos;
4. fazer push do branch para o GitHub;
5. registrar commit e branch usados como baseline WSL.

Arquivos ignorados, `.env`, `C:\MSF-data`, packets e raws nao entram nesse
backup.

### Dados

Supabase nao e backup deste data root e nao sera usado neste epico. O banco nao
preserva automaticamente raws, transcripts, reviews, packets, receipts,
auditorias e provenance como arvore de arquivos.

Para proteger a migracao:

1. manter `C:\MSF-data\Marketing_Swipe_File` sem alteracoes;
2. gerar inventario com paths, tamanhos e SHA-256 antes da copia;
3. copiar para o filesystem WSL sem apagar a origem;
4. gerar inventario equivalente no WSL e comparar;
5. manter a origem Windows read-only ate a validacao funcional e o piloto.

Isso protege contra erro de migracao. Protecao contra falha fisica do SSD exige
uma copia adicional em outro dispositivo ou storage privado aprovado; GitHub e
Supabase nao substituem esse backup de arquivos.

## Stories

### WSL-S01 - Checkpoint seguro do repositorio

- Inspecionar o worktree atual e separar dados/segredos.
- Rodar testes proporcionais antes do checkpoint.
- Criar branch, commit e push somente depois dos gates explicitos de release.
- Gerar `git bundle` local opcional como segunda rota de recuperacao.

### WSL-S02 - Instalar e preparar Ubuntu 24.04

- Executar `wsl --install -d Ubuntu-24.04`.
- Criar o usuario Linux e confirmar WSL version 2.
- Instalar `python3`, `python3-venv`, `python3-dev`, `build-essential`, `git`,
  `curl`, `ffmpeg`, `nodejs` e `npm`.
- Configurar Git Linux com `core.autocrlf=input` e identidade aprovada.

### WSL-S03 - Tornar o ambiente reproduzivel

- Criar `scripts/bootstrap_wsl.sh` idempotente.
- Criar `scripts/verify_wsl_environment.py` read-only.
- Criar `requirements-dev.txt` para pytest e ferramentas de validacao.
- Criar `.env.wsl.example` com paths Linux, sem segredos.
- Criar `.gitattributes` com LF para Python, shell, JSON e Markdown, evitando
  uma normalizacao massiva nao revisada no mesmo passo.

### WSL-S04 - Migrar o repositorio

- Clonar do branch de checkpoint no filesystem ext4 do WSL.
- Confirmar o commit baseline e o worktree esperado.
- Criar uma virtualenv Linux nova; nunca copiar a `.venv` Windows.
- Instalar requirements e executar `pip check`.

### WSL-S05 - Migrar e verificar o data root

- Criar `/home/luish/msf-data/Marketing_Swipe_File`.
- Copiar o data root a partir de `/mnt/c/MSF-data/Marketing_Swipe_File`.
- Preservar a origem e comparar contagem, tamanho e hashes.
- Configurar:

```bash
export MSF_DATA_DIR="$HOME/msf-data/Marketing_Swipe_File"
export TMPDIR="$HOME/.cache/msf/tmp"
```

- Garantir que staging e destino de packets fiquem no mesmo filesystem para
  preservar `os.replace` atomico.

### WSL-S06 - Compatibilidade operacional

- Atualizar README, `.env.example`, contrato gold e skills ativas.
- Corrigir mensagens que recomendam `.venv\\Scripts\\python.exe`.
- Preservar docs historicos e execution logs como provenance.
- Manter captura autenticada no Windows inicialmente, usando um inbox de
  importacao; nao compartilhar perfil Chrome entre Windows e WSL.
- Validar Playwright/Chromium WSL separadamente antes de torna-lo padrao.

### WSL-S07 - Testes e benchmark

- Rodar a suite gold atual, incluindo os 80 testes do fast lane.
- Rodar a suite completa do repositorio e `py_compile`.
- Validar raw preflight, recorder, finalizer, packet atomico e fingerprints.
- Rodar manifests gold read-only e comparar os resultados Windows/WSL.
- Medir um episodio curto, um medio e um longo por etapa.
- Confirmar que nenhum gold real mudou durante os testes read-only.

### WSL-S08 - Cutover e rollback

- Declarar WSL como runtime padrao somente depois dos gates anteriores.
- Manter a origem Windows read-only durante um ciclo completo de trabalho.
- Documentar comando unico para abrir/operar o projeto no WSL.
- Rollback: desativar `MSF_DATA_DIR` Linux e voltar ao branch/data root Windows
  preservados, sem conversao reversa de arquivos.

## Criterios de aceite

1. Ubuntu 24.04 roda em WSL 2 com Python 3.12 e dependencias validas.
2. Repositorio e data root ativos vivem no filesystem Linux, fora de `/mnt/c`.
3. Checkpoint do codigo existe no GitHub e corresponde ao baseline registrado.
4. Inventarios Windows/WSL dos dados sao equivalentes.
5. Suite gold e suite completa passam no WSL.
6. Fast lane, atomicidade, packets e fingerprints mantem o comportamento.
7. Chrome Windows continua disponivel como fronteira de aquisicao.
8. Origem Windows permanece recuperavel ate a aprovacao do cutover.
9. Nenhum upload para Supabase, consolidacao ou mudanca de lifecycle ocorre.

## Gates e acoes externas

- Instalacao da distro pode exigir elevacao, reinicio e criacao interativa do
  usuario Linux.
- Commit e push sao gates separados. Este plano nao os executa silenciosamente.
- Copia adicional para cloud ou dispositivo externo exige escolha explicita de
  destino por causa de privacidade e material possivelmente protegido.

## Proxima acao

Revisar e salvar o estado atual do repositorio em um branch de checkpoint no
GitHub. Depois instalar Ubuntu 24.04 e executar as stories de bootstrap,
migracao, validacao e benchmark em ordem.
