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

O modelo utilizado (`qwen2.5-coder:3b`) é leve (~2 GB) e roda bem em CPU ***(GPU não é obrigatória)***.

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

**Via terminal:**
```bash
python main.py
```
Escolha a opção `2`. Digite suas perguntas. Use `exit` para sair.

**Via interface web:**
```bash
python main.py
```
Escolha a opção `3`. Acesse `http://localhost:5000` no navegador.

---

## 💬 Exemplos de perguntas

```text
- Explique a arquitetura geral do projeto
- Quais são os principais módulos e suas responsabilidades?
- Quais endpoints ou rotas existem?
- Quais funções acessam o banco de dados?
- Como funciona a autenticação no sistema?
- Quais dependências externas o projeto utiliza?
- Onde está a lógica de negócio principal?
- Quais testes existem e o que eles cobrem?
- Existe tratamento de erros centralizado?
- Como os dados são validados antes de persistir?
- Quais configurações o projeto espera (env vars, configs)?
- Quais pontos do código poderiam ser melhorados?
```

---

## ⚙️ Configuração

Edite `minorag/config.py` para ajustar:

### Indexação

| Parâmetro         | Padrão             | Descrição                                          |
| ----------------- | ------------------ | -------------------------------------------------- |
| `CODE_PATH`       | `./codebase`       | Pasta com o código fonte                           |
| `FILE_EXTENSIONS` | (ver config.py)    | Extensões de arquivo a indexar                     |
| `IGNORE_DIRS`     | (ver config.py)    | Pastas ignoradas na varredura                      |
| `CHUNK_SIZE`      | `1000`             | Tamanho de cada chunk em caracteres                |
| `CHUNK_OVERLAP`   | `150`              | Sobreposição entre chunks (melhora contexto)       |
| `EMBED_MODEL`     | `nomic-embed-text` | Modelo de embeddings do Ollama                     |

### Recuperação e geração

| Parâmetro    | Padrão             | Descrição                                          |
| ------------ | ------------------ | -------------------------------------------------- |
| `LLM_MODEL`  | `qwen2.5-coder:3b` | Modelo LLM do Ollama                               |
| `TOP_K`      | `5`                | Chunks mais relevantes enviados como contexto      |

### Performance (`OLLAMA_OPTIONS`)

| Opção          | Padrão | Descrição                                                                                 |
| -------------- | ------ | ----------------------------------------------------------------------------------------- |
| `num_ctx`      | `4096` | Tamanho da janela de contexto em tokens. Afeta diretamente o uso de RAM e o tempo de prefill. Valores menores = mais rápido e menos memória |
| `num_predict`  | `1024` | Limite máximo de tokens gerados na resposta                                               |
| `num_thread`   | `8`    | Threads de CPU usadas pelo Ollama. Ajuste para o número de threads do seu processador     |
| `num_batch`    | `512`  | Tamanho do lote no prefill. Valores maiores aceleram o processamento do prompt            |
| `temperature`  | `0.2`  | Criatividade da resposta (0 = determinístico, 1 = mais criativo). Baixo é ideal para código |

> **Sobre uso de memória RAM:** o consumo é fixo pelo tamanho do modelo (~2 GB para o qwen2.5-coder:3b) mais o KV cache, proporcional ao `num_ctx`. Com `num_ctx=4096`, o total fica em ~2.5–3 GB. Não há parâmetro de "limite de RAM" na API do Ollama — o controle é feito ajustando `num_ctx` e escolhendo um modelo compatível com o hardware disponível.

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
    devcontainer.json     ← configura o ambiente automaticamente
    setup.sh              ← instala dependências e modelos
  minorag/                ← pacote Python
    __init__.py
    config.py             ← configurações do RAG
    core.py               ← lógica de indexação, embeddings e query
    web.py                ← servidor web (Flask)
    static/
      index.html          ← interface web
  codebase/               ← clone seu projeto aqui
  main.py                 ← entry point
  requirements.txt        ← dependências Python
```

---

## ⚡ Melhorias possíveis

### 🔢 Aumentar `TOP_K` para mais contexto nas respostas

`TOP_K` define quantos chunks do índice são recuperados e enviados como contexto para o LLM a cada pergunta. O valor padrão é `5`.

Aumentar esse número pode melhorar a qualidade das respostas em projetos grandes, onde a informação relevante está espalhada em vários arquivos. Por outro lado, cada chunk extra aumenta o número de tokens no prompt, o que impacta diretamente o tempo de resposta (prefill) e o uso de memória.

**Referência prática:**

| `TOP_K` | Uso de contexto estimado | Quando usar |
| ------- | ------------------------ | ----------- |
| `3`     | ~3.000 chars             | Projetos pequenos, respostas rápidas |
| `5`     | ~5.000 chars *(padrão)*  | Equilíbrio entre qualidade e velocidade |
| `8`     | ~8.000 chars             | Projetos grandes, perguntas amplas |
| `12`    | ~12.000 chars            | Máxima cobertura — exige `num_ctx` alto |

> Se aumentar `TOP_K` para `8` ou mais, aumente `num_ctx` proporcionalmente em `OLLAMA_OPTIONS` para garantir que o modelo consiga processar todo o contexto sem truncar.

---

### ✏️ Personalizar o prompt de resposta

O prompt enviado ao LLM é construído pela função `build_prompt` em `minorag/retriever.py`. Editar essa função permite ajustar o comportamento do modelo sem mudar nada mais.

**Prompt atual:**

```python
def build_prompt(question: str, chunks: str) -> str:
    return f"""You are a senior software engineer.

Use the code context below to answer.

Context:
----------------
{chunks}
----------------

Question:
{question}

Answer clearly and technically."""
```

**Exemplos de customização:**

Responder em português:
```python
return f"""Você é um engenheiro de software sênior.
Use o contexto de código abaixo para responder em português.
...
```

Focar em um domínio específico:
```python
return f"""You are a senior backend engineer specialized in Java Spring Boot.
Prioritize explaining business rules and data flow.
...
```

Forçar um formato de resposta:
```python
return f"""You are a senior software engineer.
Always structure your answer in three sections:
1. Direct answer
2. Code references (file + line if possible)
3. Caveats or edge cases
...
```

As variáveis `{chunks}` (contexto recuperado do índice) e `{question}` (pergunta do usuário) devem sempre estar presentes no prompt.

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
