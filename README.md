# 🧠 minorag

**Pergunte ao seu código usando Ollama + ChromaDB.**

Este projeto segue a filosofia Minotide:

> Ferramentas simples, local-first e open source que funcionam sem fricção.

---

## ⚙️ Pré-requisitos

| Ferramenta             | Descrição                                         |
| ---------------------- | ------------------------------------------------- |
| **VS Code**            | Editor de código                                  |
| **Docker**             | Docker Desktop (Win/Mac) ou Docker Engine (Linux) |
| **Dev Containers**     | Extensão `ms-vscode-remote.remote-containers`     |

> **Windows:** Docker Desktop com WSL2. Clone o projeto dentro do Linux (`~/ws/rag`). Evite caminhos como `/mnt/c/Users/...`.
>
> **Linux:** garanta que o Docker pode ser executado sem `sudo`:
> ```bash
> sudo usermod -aG docker $USER
> ```
> Depois, faça logout/login.

O modelo utilizado (`qwen2.5-coder:3b`) é leve (~2 GB) e roda bem em CPU ***(GPU não é obrigatória)***.

---

## 🖼️ Observação sobre interface gráfica (Qt)

A interface gráfica do minorag usa Qt (PySide6) e é exibida diretamente no seu desktop, mesmo rodando dentro do container.

- **VS Code Dev Containers** normalmente já repassa o display do host para o container automaticamente, sem necessidade de configuração extra.
- **Se a janela não abrir** ou aparecer erro de permissão do X11, execute no terminal do host (fora do container):

```bash
xhost +local:docker
```

Isso libera o acesso do container ao seu servidor gráfico local. Em ambientes modernos, geralmente não é necessário, mas pode ser útil em casos de restrição de permissões.

---

## 🚀 Começar

1. Abra a pasta do projeto no VS Code
2. Clique em **"Reopen in Container"**
3. Aguarde a configuração automática (apenas na primeira vez)
4. **Pronto.** Python, Ollama, modelos e dependências já estarão instalados

Ao iniciar o container:
- O servidor **Ollama** sobe automaticamente (`postStartCommand`)
- A **janela da aplicação** abre automaticamente (`postAttachCommand`) diretamente no seu desktop
- Caso feche a janela, reabra pelo terminal do container `python main.py`

---

## 🔧 Como usar

> Suporta: `.java` `.py` `.js` `.ts` `.go` `.rs` `.c` `.cpp` `.h` `.cs` `.rb` `.php` `.kt` `.scala` `.swift` `.m` `.sql` `.sh` e mais. Configure pelo painel **⚙ Indexação**.

### 1. Configurar repositório

Clique na aba **⚙ Repositório** e informe:

- **URL** do repositório Git (HTTPS ou SSH)
- **Branch** desejada (padrão: `main`)
- **Token de acesso** para repositórios privados (opcional)
- **Caminho chave SSH** para autenticação (opcional, ex: `~/.ssh/id_rsa`)
- **Atualizar no startup** — marque para clonar/atualizar automaticamente ao abrir a aplicação

As configurações são **salvas automaticamente** no arquivo `.env` do projeto, dentro do seu container, a cada alteração.

> Não se esqueça de manter o arquivo `.env` no `.gitignore` para não vazar credenciais.

### 2. Sincronizar Codebase

Clique em **Sincronizar Codebase** para clonar o repositório e gerar o índice de busca. O progresso (clone, chunks indexados) é exibido em tempo real na interface.

Para recomeçar do zero, clique em **Limpar Codebase** — remove todos os arquivos clonados e o índice do ChromaDB.

> Todo o processamento é local: o código fica em `.codebase/`, os embeddings em `.chromadb/` e configurações no `.env`

### 3. Fazer perguntas

Digite sua pergunta no campo de texto e pressione **Enter** ou clique em **Enviar**.

> Se o índice estiver vazio, a interface exibe **"Índice não encontrado. Indexe o código primeiro. Caminho: Repositório / Sincronizar Codebase"** — clique em **Sincronizar Codebase** para resolver.

---

## ⚙️ Configuração via interface

Todos os parâmetros do projeto são configuráveis diretamente pela interface, sem precisar editar arquivos. Cada painel **salva automaticamente** as configurações no `.env` após uma breve pausa na digitação (debounce de ~700 ms) e aplica as mudanças imediatamente na sessão atual.

O botão **Restaurar .env** (canto superior direito da janela) sobrescreve o `.env` com todos os valores padrão e recarrega as configurações em memória — útil para desfazer edições manuais incorretas.

### Painel ⚙ Repositório

Configura o repositório Git e dispara o clone/indexação:

| Campo | Variável `.env` | Padrão | Descrição |
|---|---|---|---|
| URL do repositório | `GIT_REPO_URL` | *(vazio)* | URL HTTPS ou SSH do repositório |
| Branch | `GIT_BRANCH` | `main` | Branch a clonar |
| Token de acesso | `GIT_ACCESS_TOKEN` | *(vazio)* | PAT para repositórios privados (HTTPS) |
| Caminho da chave SSH | `GIT_SSH_KEY_PATH` | *(vazio)* | Caminho para a chave privada SSH |
| Atualizar no startup | `GIT_AUTO_UPDATE` | `false` | Clona/atualiza automaticamente ao iniciar |

Botões disponíveis no painel:

| Botão | Ação |
|---|---|
| **Sincronizar Codebase** | Salva imediatamente e clona o repositório / reindexa (progresso em tempo real) |
| **Limpar Codebase** | Remove `.codebase/` e o índice do ChromaDB |

### Painel ⚙ LLM

Configurações do Ollama e do modelo de linguagem:

| Campo | Variável `.env` | Padrão | Descrição |
|---|---|---|---|
| URL do Ollama | `OLLAMA_URL` | `http://localhost:11434` | Endereço da API do Ollama |
| Modelo de Embedding | `EMBED_MODEL` | `nomic-embed-text` | Modelo para geração de vetores |
| Modelo LLM | `LLM_MODEL` | `qwen2.5-coder:3b` | Modelo para geração de respostas |
| Top K | `TOP_K` | `5` | Chunks mais relevantes enviados como contexto |
| Contexto (num_ctx) | `OLLAMA_NUM_CTX` | `4096` | Janela de contexto em tokens |
| Tokens gerados | `OLLAMA_NUM_PREDICT` | `768` | Limite máximo de tokens na resposta |
| Threads (num_thread) | `OLLAMA_NUM_THREAD` | `8` | Threads de CPU usadas pelo Ollama |
| Batch (num_batch) | `OLLAMA_NUM_BATCH` | `256` | Tamanho do lote no prefill |
| Temperature | `OLLAMA_TEMPERATURE` | `0.2` | Criatividade da resposta (0 = determinístico) |
| Repeat Penalty | `OLLAMA_REPEAT_PENALTY` | `1.15` | Penalidade para evitar repetições |
| Prompt Template | `PROMPT_TEMPLATE` | *(ver abaixo)* | Instruções enviadas ao LLM a cada pergunta |

> Para alternar modelos (ex: `llama3.2`, `qwen2.5-coder:7b`), basta atualizar **Modelo LLM** pelo painel e re-indexar se quiser usar um modelo de embedding diferente.

### Painel ⚙ Indexação

Controla quais arquivos serão processados e como são divididos:

| Campo | Variável `.env` | Padrão | Descrição |
|---|---|---|---|
| Extensões de arquivo | `FILE_EXTENSIONS` | `.java,.py,.js,.ts,.go,.rs,.c,.cpp,.h,.cs,.rb,.php,.kt,.scala,.swift,.m,.sql,.sh` | Lista separada por vírgula |
| Nomes incluídos | `INCLUDE_FILENAMES` | `architecture.md` | Arquivos incluídos pelo nome exato |
| Diretórios ignorados | `IGNORE_DIRS` | `target,.git,...` | Pastas excluídas da varredura |
| Tamanho do chunk | `CHUNK_SIZE` | `1500` | Caracteres por chunk |
| Sobreposição | `CHUNK_OVERLAP` | `200` | Sobreposição entre chunks consecutivos |

> Alterações de indexação têm efeito na **próxima** vez que você clicar em Sincronizar Codebase.

---

## 🗂️ Organização do projeto

```
minorag/
├── main.py                      # Ponto de entrada — auto-indexação em thread + inicia a GUI
├── requirements.txt             # Dependências Python
├── .env                         # Configurações locais (não versionado)
│
└── minorag/
    ├── config.py                # Leitura do .env e valores padrão de todas as variáveis
    ├── chunkers.py              # Estratégias de chunking por linguagem (AST, blocos, SQL...)
    ├── indexer.py               # Leitura de arquivos do .codebase/
    ├── retriever.py             # Busca no ChromaDB e montagem do prompt
    ├── ollama.py                # Wrapper para embed e generate_stream_iter
    ├── git.py                   # Clone e atualização do repositório
    │
    └── gui/                     # Pacote da interface gráfica (PySide6)
        ├── __init__.py          # Exporta run_gui()
        ├── style.qss            # Stylesheet Qt
        ├── widgets.py           # Helpers visuais: make_label, make_separator, load_style
        ├── workers.py           # QThreads: QueryWorker (RAG) e SyncWorker (clone + indexação)
        ├── env_helpers.py       # Leitura/escrita do .env: save_env_vars, reset, clear_codebase
        ├── chat_panel.py        # Painel de chat com streaming de tokens
        ├── git_panel.py         # Painel de configuração Git
        ├── llm_panel.py         # Painel de configuração LLM e prompt
        ├── indexing_panel.py    # Painel de configuração de indexação
        └── main_window.py       # Janela principal com abas e header
```

---

## 🧠 Como funciona

1. **Leitura** — percorre `.codebase/` e lê arquivos das extensões configuradas
2. **Chunking semântico** — divide cada arquivo usando a estratégia mais adequada à linguagem:
   - **AST** para Python (funções, classes, métodos)
   - **Blocos `{}`** para Java, JS, TS, Go, C, C++, C#, Rust, Kotlin, PHP, Scala, Swift, Objective-C
   - **Blocos `end`** para Ruby (`def/class/module...end`)
   - **Statements** para SQL (separação por `;`, extrai nomes de funções/procedures/views)
   - **Tamanho fixo** como fallback para demais extensões
   - Cada chunk inclui metadados: arquivo, nome do símbolo, linha inicial, tipo (`function`, `class`, `method`, `statement`, `block`) e linguagem
3. **Embeddings** — gera vetores via Ollama (`nomic-embed-text`)
4. **Armazenamento** — salva no ChromaDB (persistente em disco)
5. **Busca** — sua pergunta vira embedding e busca os chunks mais relevantes
6. **Resposta** — os chunks (com metadados de localização) são passados como contexto para o LLM (`qwen2.5-coder:3b`), que detecta automaticamente as linguagens presentes e adapta a resposta

---

## ⚡ Melhorias possíveis

### 🔢 Aumentar `TOP_K` para mais contexto nas respostas

`TOP_K` define quantos chunks do índice são recuperados e enviados como contexto para o LLM a cada pergunta. Configure pelo painel **⚙ LLM** ou pela variável `TOP_K` no `.env`.

Aumentar esse número pode melhorar a qualidade das respostas em projetos grandes, onde a informação relevante está espalhada em vários arquivos. Por outro lado, cada chunk extra aumenta o número de tokens no prompt, o que impacta diretamente o tempo de resposta (prefill) e o uso de memória.

**Referência prática:**

| `TOP_K` | Uso de contexto estimado | Quando usar |
| ------- | ------------------------ | ----------- |
| `3`     | ~3.000 chars             | Projetos pequenos, respostas rápidas |
| `5`     | ~5.000 chars             | **Padrão** — equilíbrio entre qualidade e velocidade |
| `8`     | ~8.000 chars             | Projetos grandes, perguntas amplas |
| `12`    | ~12.000 chars            | Máxima cobertura — exige `num_ctx` alto |

> Se aumentar `TOP_K` para `8` ou mais, aumente `num_ctx` proporcionalmente pelo painel **⚙ LLM** para garantir que o modelo consiga processar todo o contexto sem truncar.

---

### ✏️ Personalizar o prompt de resposta

O template do prompt é configurável diretamente pelo painel **⚙ LLM**, no campo **Prompt Template**. A alteração tem efeito imediato e é persistida no `.env`.

> Os marcadores `{chunks}` e `{question}` são obrigatórios — são substituídos automaticamente pelo retriever antes de enviar ao modelo. O marcador opcional `{language_expertise}` é substituído automaticamente pelas linguagens detectadas nos chunks recuperados (ex: "Python, Java e análise de código").

O padrão é:

```
Você é um engenheiro de software sênior especializado em {language_expertise}.
Responda sempre em português. Seja conciso e direto.

REGRAS:
- Baseie-se EXCLUSIVAMENTE nos trechos de código fornecidos abaixo.
- NÃO invente informações. Se não houver dados suficientes, diga.
- Use os metadados (FILE, LINE, SYMBOL) dos cabeçalhos para citar localizações.
- Correlacione trechos quando a pergunta envolver múltiplos arquivos.

CÓDIGO:
{chunks}

PERGUNTA:
{question}

FORMATO DA RESPOSTA:
### Resposta
<resposta direta e objetiva>

### Localização no código
- Arquivo, símbolo, tipo e linha inicial de cada trecho relevante

### Evidências no código
<trechos ou descrição que sustentam a resposta>
```

---

### 📄 `architecture.md` como contexto extra

Uma técnica eficaz de RAG é criar manualmente um arquivo descrevendo a arquitetura do projeto indexado — informações que o código sozinho não deixa claro para a LLM, como intenções de design, padrões adotados e fluxos principais.

Crie o arquivo dentro da pasta do projeto em `.codebase/`:

```markdown
# architecture.md

## Visão geral
Sistema de e-commerce com arquitetura hexagonal...

## Módulos principais
- `domain/` — regras de negócio puras, sem dependências externas
- `infra/` — adaptadores de banco, filas, APIs externas
- `api/` — controllers REST, validação de entrada

## Decisões de design
- Repository pattern para abstrair o banco
- CQRS separando leitura e escrita em OrderService
- Autenticação via JWT stateless

## Fluxo principal
Requisição → AuthMiddleware → Controller → UseCase → Repository → DB
```

Como o indexer já processa arquivos `.md`, esse arquivo é incluído automaticamente nos embeddings ao rodar a indexação. Quando você faz perguntas sobre arquitetura ou design, o chunk do `architecture.md` tem alta probabilidade de ser retornado no `TOP_K` junto com o código, dando ao LLM contexto de intenção que não está explícito no fonte.

---

### 🎮 GPU (opcional)

Para rodar modelos maiores com aceleração por GPU NVIDIA:

1. Instale o [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
2. Adicione `"--gpus", "all"` ao `runArgs` em `.devcontainer/devcontainer.json`
3. Rebuild o container e troque o **Modelo LLM** pelo painel **⚙ LLM** para um modelo maior (ex: `llama3.2`, `qwen2.5-coder:7b`)

---

## 📄 Licença

Use, modifique e compartilhe livremente.
