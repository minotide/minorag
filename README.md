# 🧠 minorag

**Pergunte ao seu código usando Ollama + ChromaDB.**

Este projeto segue a filosofia Minotide:

> Ferramentas simples, locais e open source que funcionam sem fricção.

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

## 🚀 Começar

1. Abra a pasta do projeto no VS Code
2. Clique em **"Reopen in Container"**
3. Aguarde a configuração automática (apenas na primeira vez)
4. **Pronto.** Python, Ollama, modelos e dependências já estarão instalados

O servidor Ollama inicia automaticamente com o container.

---

## 🔧 Como usar

> Suporta: `.java` `.py` `.js` `.ts` `.go` `.rs` `.c` `.cpp` `.cs` `.rb` `.php` `.kt` `.scala` `.swift` `.sql` `.sh` `.yaml` `.json` `.xml` `.md` e mais. <br> Configure em `config.py`.

Após abrir o projeto no container, acesse **http://localhost:5000** — a interface web abre automaticamente no navegador.

### 1. Configurar repositório

Abra o painel **⚙ Repositório** no canto superior direito e informe:

- **URL** do repositório Git (HTTPS ou SSH)
- **Branch** desejada (padrão: `main`)
- **Token de acesso** para repositórios privados (opcional)
- **Caminho chave SSH** para autenticação (opcional, ex: `~/.ssh/id_rsa`)
- Clique em **Salvar no .env** para guardar as configurações. (São salvas **no arquivo `.env` do projeto**, dentro do seu container.)

> Não se esqueça de manter no .gitignore o arquivo .env para não vazar suas credenciais.

### 2. Sincronizar Codebase

Clique em **Sincronizar Codebase** para clonar o repositório e gerar o índice de busca automaticamente.

> Todo o processamento é local: o código fica em `codebase/`, os embeddings em `.chromadb/` — nada sai do seu container.

### 3. Fazer perguntas

Digite sua pergunta no campo de texto e pressione **Enter** ou clique em **Enviar**.

---

## ⚙️ Configuração

As configurações do repositório Git são feitas pela interface web (painel **⚙ Repositório**) e salvas automaticamente no arquivo `.env` do projeto.

Para ajustes avançados de modelos e performance, edite `minorag/config.py`:

### Indexação

| Parâmetro         | Padrão             | Descrição                                          |
| ----------------- | ------------------ | -------------------------------------------------- |
| `CODE_PATH`       | `./codebase`       | Pasta com o código fonte                           |
| `FILE_EXTENSIONS` | (ver config.py)    | Extensões de arquivo a indexar                     |
| `IGNORE_DIRS`     | (ver config.py)    | Pastas ignoradas na varredura                      |
| `CHUNK_SIZE`      | (ver config.py)    | Tamanho de cada chunk em caracteres                |
| `CHUNK_OVERLAP`   | (ver config.py)    | Sobreposição entre chunks (melhora contexto)       |
| `EMBED_MODEL`     | `nomic-embed-text` | Modelo de embeddings do Ollama                     |

### Recuperação e geração

| Parâmetro    | Padrão             | Descrição                                          |
| ------------ | ------------------ | -------------------------------------------------- |
| `LLM_MODEL`  | `qwen2.5-coder:3b` | Modelo LLM do Ollama                               |
| `TOP_K`      | (ver config.py)    | Chunks mais relevantes enviados como contexto      |

### Performance (`OLLAMA_OPTIONS`)

| Opção          | Descrição                                                                                 |
| -------------- | ----------------------------------------------------------------------------------------- |
| `num_ctx`      | Tamanho da janela de contexto em tokens. Afeta diretamente o uso de RAM e o tempo de prefill. Valores menores = mais rápido e menos memória |
| `num_predict`  | Limite máximo de tokens gerados na resposta                                               |
| `num_thread`   | Threads de CPU usadas pelo Ollama. Ajuste para o número de threads do seu processador     |
| `num_batch`    | Tamanho do lote no prefill. Valores maiores aceleram o processamento do prompt            |
| `temperature`  | Criatividade da resposta (0 = determinístico, 1 = mais criativo). Baixo é ideal para código |

---

## 🧠 Como funciona

1. **Leitura** — percorre `codebase/` e lê arquivos das extensões configuradas
2. **Chunking** — divide cada arquivo em pedaços menores
3. **Embeddings** — gera vetores via Ollama (`nomic-embed-text`)
4. **Armazenamento** — salva no ChromaDB (persistente em disco)
5. **Busca** — sua pergunta vira embedding e busca os chunks mais relevantes
6. **Resposta** — os chunks são passados como contexto para o LLM (`qwen2.5-coder:3b`)

---

## ⚡ Melhorias possíveis

### 🔢 Aumentar `TOP_K` para mais contexto nas respostas

`TOP_K` define quantos chunks do índice são recuperados e enviados como contexto para o LLM a cada pergunta.

Aumentar esse número pode melhorar a qualidade das respostas em projetos grandes, onde a informação relevante está espalhada em vários arquivos. Por outro lado, cada chunk extra aumenta o número de tokens no prompt, o que impacta diretamente o tempo de resposta (prefill) e o uso de memória.

**Referência prática:**

| `TOP_K` | Uso de contexto estimado | Quando usar |
| ------- | ------------------------ | ----------- |
| `3`     | ~3.000 chars             | Projetos pequenos, respostas rápidas |
| `5`     | ~5.000 chars             | Equilíbrio entre qualidade e velocidade |
| `8`     | ~8.000 chars             | Projetos grandes, perguntas amplas |
| `12`    | ~12.000 chars            | Máxima cobertura — exige `num_ctx` alto |

> Se aumentar `TOP_K` para `8` ou mais, aumente `num_ctx` proporcionalmente em `OLLAMA_OPTIONS` para garantir que o modelo consiga processar todo o contexto sem truncar.

---

### ✏️ Personalizar o prompt de resposta

O template do prompt fica em `minorag/config.py` na variável `PROMPT_TEMPLATE` e é usado por `build_prompt` em `minorag/retriever.py`. Para customizar, basta editar o `config.py`.

> Os marcadores `{chunks}` e `{question}` são obrigatórios — são substituídos automaticamente pelo retriever antes de enviar ao modelo.

---

### 📄 `architecture.md` como contexto extra

Uma técnica eficaz de RAG é criar manualmente um arquivo descrevendo a arquitetura do projeto indexado — informações que o código sozinho não deixa claro para a LLM, como intenções de design, padrões adotados e fluxos principais.

Crie o arquivo dentro da pasta do projeto em `codebase/`:

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
3. Rebuild o container e troque `LLM_MODEL` em `config.py` para um modelo maior (ex: `llama3`, `qwen2.5-coder:7b`)

---

## 📄 Licença

Use, modifique e compartilhe livremente.
