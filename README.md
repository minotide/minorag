# 🧠 minorag

**Busca inteligente para código usando Ollama + ChromaDB.**

Este projeto segue a filosofia Minotide:

> Ferramentas simples, locais e open source que funcionam sem fricção.

---

## ⚙️ Pré-requisitos

| Ferramenta             | Descrição                                         |
| ---------------------- | ------------------------------------------------- |
| **VS Code**            | Editor de código                                  |
| **Docker**             | Docker Desktop (Win/Mac) ou Docker Engine (Linux) |
| **Dev Containers**     | Extensão `ms-vscode-remote.remote-containers`     |

> **Windows:** Docker Desktop com backend WSL2. Clone o projeto dentro do Linux (`~/ws/rag`). Evite caminhos como `/mnt/c/Users/...`.
>
> **Linux:** garanta que o Docker pode ser executado sem `sudo`:
> ```bash
> sudo usermod -aG docker $USER
> ```
> Depois, faça logout/login.

O modelo utilizado (`qwen2.5-coder:3b`) é leve (~2 GB) e roda bem em CPU. GPU não é necessária.

---

## 🚀 Começar

1. Abra a pasta do projeto no VS Code
2. Clique em **"Reopen in Container"**
3. Aguarde a configuração automática (apenas na primeira vez)
4. **Pronto.** Python, Ollama, modelos e dependências já estarão instalados

O servidor Ollama inicia automaticamente com o container.

> **Fallback:** se o Ollama não estiver respondendo, inicie manualmente no terminal:
> ```bash
> ollama serve &
> ```

---

## 🔧 Como usar

> Suporta: `.java` `.py` `.js` `.ts` `.go` `.rs` `.c` `.cpp` `.cs` `.rb` `.php` `.kt` `.scala` `.swift` `.sql` `.sh` `.yaml` `.json` `.xml` `.md` e mais. Configure em `config.py`.

### 1. Adicionar código

Clone o repositório que deseja analisar para dentro da pasta `codebase/`:

```bash
git clone https://github.com/usuario/repo.git codebase/repo
```

### 2. Indexar código

```bash
python main.py
```

Escolha a opção `1`. Isso vai ler os arquivos, gerar embeddings e armazenar no ChromaDB.

### 3. Fazer perguntas

```bash
python main.py
```

Escolha a opção `2`. Digite suas perguntas no terminal. Use `exit` para sair.

---

## 💬 Exemplos de perguntas

```text
Explique a arquitetura geral do projeto
Quais são os principais módulos e suas responsabilidades?
Como está organizada a estrutura de pastas?
Quais endpoints ou rotas existem?
Quais classes/funções acessam o banco de dados?
Existe algum padrão de design sendo usado (MVC, Clean Architecture, etc)?
Como funciona a autenticação no sistema?
Quais dependências externas o projeto utiliza?
Onde está a lógica de negócio principal?
Quais testes existem e o que eles cobrem?
Existe tratamento de erros centralizado?
Como os dados são validados antes de persistir?
Quais configurações o projeto espera (env vars, configs)?
Explique o fluxo completo de uma requisição
Quais pontos do código poderiam ser melhorados?
```

---

## ⚙️ Configuração

Edite `config.py` para ajustar:

| Parâmetro         | Padrão             | Descrição                        |
| ----------------- | ------------------- | -------------------------------- |
| `CODE_PATH`       | `./codebase`        | Pasta com o código fonte         |
| `FILE_EXTENSIONS` | (ver config.py)     | Extensões de arquivo a indexar   |
| `IGNORE_DIRS`     | (ver config.py)     | Pastas ignoradas na varredura    |
| `CHUNK_SIZE`      | `800`               | Tamanho de cada chunk (chars)    |
| `CHUNK_OVERLAP`   | `100`               | Sobreposição entre chunks        |
| `EMBED_MODEL`     | `nomic-embed-text`  | Modelo de embeddings (Ollama)    |
| `LLM_MODEL`       | `qwen2.5-coder:3b`| Modelo de geração (Ollama)       |
| `TOP_K`           | `5`                 | Quantidade de chunks retornados  |

---

## 🧠 Como funciona

1. **Leitura** — percorre `codebase/` e lê arquivos das extensões configuradas
2. **Chunking** — divide cada arquivo em pedaços menores
3. **Embeddings** — gera vetores via Ollama (`nomic-embed-text`)
4. **Armazenamento** — salva no ChromaDB (persistente em disco)
5. **Busca** — sua pergunta vira embedding e busca os chunks mais relevantes
6. **Resposta** — os chunks são passados como contexto para o LLM (`qwen2.5-coder:3b`)

---

## 📂 Estrutura

```text
minorag/
  .devcontainer/
    devcontainer.json   ← configura o ambiente automaticamente
    setup.sh            ← instala dependências e modelos
  codebase/             ← clone seu projeto aqui
  config.py             ← configurações do RAG
  main.py               ← indexação + query loop
  requirements.txt      ← dependências Python
```

---

## ⚡ Melhorias possíveis

- Aumentar `TOP_K` para mais contexto nas respostas
- Personalizar o prompt de resposta
- Adicionar um `architecture.md` como contexto extra
- Habilitar GPU para modelos maiores (ver seção abaixo)

---

## 🎮 GPU (opcional)

Para rodar modelos maiores com aceleração por GPU NVIDIA:

1. Instale o [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
2. Adicione `"--gpus", "all"` ao `runArgs` em `.devcontainer/devcontainer.json`
3. Rebuild o container e troque `LLM_MODEL` em `config.py` para um modelo maior (ex: `llama3`, `qwen2.5-coder:7b`)

---

## 📄 Licença

Use, modifique e compartilhe livremente.
