"""
Módulo da interface web do minorag.

Expõe uma aplicação Flask com rotas para indexação de código
e consulta ao índice via Server-Sent Events (SSE) com streaming de tokens.
"""

import re as _re
import json as _json
import os
from collections.abc import Iterator

import chromadb
from flask import Flask, Response, jsonify, request, stream_with_context

from minorag.config import CHROMA_PATH, CODE_PATH, ENV_PATH
from minorag import config as _cfg
from minorag.chunkers import chunk_by_language
from minorag.indexer import read_files
from minorag.ollama import embed, generate, generate_stream_iter
from minorag.retriever import build_chunks_context, build_prompt

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

app = Flask(__name__, static_folder=STATIC_DIR)


def _asset_version(filename: str) -> str:
    """Retorna o mtime do arquivo como versão para cache-busting."""
    path = os.path.join(STATIC_DIR, filename)
    try:
        return str(int(os.path.getmtime(path)))
    except OSError:
        return "0"


@app.route("/")
def index():
    with open(os.path.join(STATIC_DIR, "index.html"), encoding="utf-8") as f:
        html = f.read()

    html = html.replace(
        "/static/style.css",
        f"/static/style.css?v={_asset_version('style.css')}"
    )

    html = html.replace(
        "/static/app.js",
        f"/static/app.js?v={_asset_version('app.js')}"
    )

    response = Response(html, mimetype="text/html")
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/api/index", methods=["POST"])
def api_index():
    """
    Indexa os arquivos de código da pasta codebase/ no ChromaDB.

    Se a codebase estiver vazia e GIT_REPO_URL estiver configurado,
    clona o repositório automaticamente antes de indexar.

    @return: JSON com mensagem de sucesso e total de chunks, ou erro 400.
    """
    docs = read_files(CODE_PATH)

    if not docs:
        repo_url = _cfg.GIT_REPO_URL.strip()
        if not repo_url:
            return jsonify({"error": "Nenhum arquivo encontrado em .codebase/. Configure e clone um repositório pelo painel Git."}), 400

        from minorag.git import clone_repo
        ok = clone_repo(repo_url, _cfg.GIT_BRANCH or "main",
                        _cfg.GIT_ACCESS_TOKEN or None)
        if not ok:
            return jsonify({"error": "Nenhum arquivo em .codebase/ e falha ao clonar o repositório configurado."}), 400

        docs = read_files(CODE_PATH)
        if not docs:
            return jsonify({"error": "Repositório clonado mas nenhum arquivo de código encontrado."}), 400

    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # Reset collection to avoid duplicates on re-index
    try:
        client.delete_collection("codebase")
    except Exception:
        pass

    collection = client.get_or_create_collection("codebase")

    id_counter = 0

    for path, content in docs:
        ext = os.path.splitext(path)[1].lower()
        chunks = chunk_by_language(content, ext)

        for chunk, chunk_meta in chunks:
            full_chunk = f"FILE: {path}\n\n{chunk}"
            emb = embed(full_chunk)

            collection.add(
                ids=[str(id_counter)],
                embeddings=[emb],
                documents=[full_chunk],
                metadatas=[{
                    "file": path,
                    "name": chunk_meta.get("name", ""),
                    "line": chunk_meta.get("line", 0),
                    "kind": chunk_meta.get("kind", ""),
                    "language": ext.lstrip("."),
                }],
            )
            id_counter += 1

    return jsonify({"message": f"Indexação concluída! ({id_counter} chunks)"})


@app.route("/api/query", methods=["POST"])
def api_query():
    """
    Responde uma pergunta sobre o código sem streaming.

    @body question: Pergunta enviada no corpo JSON.
    @return: JSON com a resposta completa, ou erro 400.
    """
    data = request.get_json()
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "Pergunta vazia"}), 400

    client = chromadb.PersistentClient(path=CHROMA_PATH)

    try:
        collection = client.get_collection("codebase")
    except Exception:
        return jsonify({"error": "Índice não encontrado. Indexe o código primeiro. Caminho: Repositório / Sincronizar Codebase"}), 400

    q_emb = embed(question)

    results = collection.query(query_embeddings=[q_emb], n_results=_cfg.TOP_K)

    docs = (results["documents"] or [[]])[0]
    metas = (results["metadatas"] or [[]])[0]
    chunks = build_chunks_context(docs, metas)

    answer = generate(build_prompt(question, chunks))

    return jsonify({"answer": answer})


@app.route("/api/query/stream", methods=["POST"])
def api_query_stream():
    """
    Responde uma pergunta sobre o código com streaming via SSE.

    Emite eventos do tipo 'log' durante o processamento, 'token' para
    cada fragmento da resposta gerada e 'done' ao finalizar.

    @body question: Pergunta enviada no corpo JSON.
    @return: Response SSE com Content-Type text/event-stream.
    """
    data = request.get_json()
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "Pergunta vazia"}), 400

    def event_stream() -> Iterator[str]:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        try:
            collection = client.get_collection("codebase")
        except Exception:
            yield f"data: {_json.dumps({'type': 'error', 'text': 'Índice não encontrado. Indexe o código primeiro. Caminho: Repositório / Sincronizar Codebase'})}\n\n"
            return

        yield f"data: {_json.dumps({'type': 'log', 'text': 'Gerando embedding da pergunta...'})}\n\n"
        q_emb = embed(question)

        yield f"data: {_json.dumps({'type': 'log', 'text': 'Buscando contexto no índice...'})}\n\n"
        results = collection.query(
            query_embeddings=[q_emb], n_results=_cfg.TOP_K)

        yield f"data: {_json.dumps({'type': 'log', 'text': 'Gerando resposta...'})}\n\n"
        chunks = build_chunks_context(
            (results["documents"] or [[]])[0],
            (results["metadatas"] or [[]])[0],
        )

        for token in generate_stream_iter(build_prompt(question, chunks)):
            yield f"data: {_json.dumps({'type': 'token', 'text': token})}\n\n"

        yield f"data: {_json.dumps({'type': 'done'})}\n\n"

    return Response(stream_with_context(event_stream()), mimetype="text/event-stream")


# ---------------------------------------------------------------------------
# Helpers para leitura/escrita do .env
# ---------------------------------------------------------------------------

_GIT_ENV_KEYS = ["GIT_REPO_URL", "GIT_BRANCH",
                 "GIT_AUTO_UPDATE", "GIT_ACCESS_TOKEN", "GIT_SSH_KEY_PATH"]

_LLM_ENV_KEYS = [
    "OLLAMA_URL", "EMBED_MODEL", "LLM_MODEL", "TOP_K",
    "OLLAMA_NUM_CTX", "OLLAMA_NUM_PREDICT", "OLLAMA_NUM_THREAD",
    "OLLAMA_NUM_BATCH", "OLLAMA_TEMPERATURE", "OLLAMA_REPEAT_PENALTY",
    "PROMPT_TEMPLATE",
]

_INDEXING_ENV_KEYS = [
    "FILE_EXTENSIONS", "INCLUDE_FILENAMES", "IGNORE_DIRS",
    "CHUNK_SIZE", "CHUNK_OVERLAP",
]

_ALL_KNOWN_KEYS = set(_GIT_ENV_KEYS + _LLM_ENV_KEYS + _INDEXING_ENV_KEYS)


def _check_env_integrity() -> list[str]:
    """Detecta problemas no .env que indiquem corrupção manual."""
    warnings: list[str] = []
    if not os.path.exists(ENV_PATH):
        return warnings

    key_counts: dict[str, int] = {}
    with open(ENV_PATH, encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                warnings.append(
                    f"Linha {lineno} sem '=': {stripped[:60]!r}"
                )
                continue
            key, _, value = stripped.partition("=")
            key_counts[key] = key_counts.get(key, 0) + 1
            # Detecta fusão de linhas: valor contém outro KEY= conhecido embutido
            for known_key in _ALL_KNOWN_KEYS:
                if known_key != key and f"{known_key}=" in value:
                    warnings.append(
                        f"Chave '{key}' tem valor corrompido: '{known_key}=' encontrado "
                        f"dentro do valor (provável fusão de linhas). Edite o .env manualmente."
                    )
                    break

    for key, count in key_counts.items():
        if count > 1:
            warnings.append(
                f"Chave '{key}' está duplicada no .env ({count} ocorrências)."
            )

    return warnings


def _read_env_vars() -> dict[str, str]:
    """Lê as variáveis de configuração Git diretamente do arquivo .env."""
    result: dict[str, str] = {k: "" for k in _GIT_ENV_KEYS}
    if not os.path.exists(ENV_PATH):
        return result
    with open(ENV_PATH, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                key, _, value = stripped.partition("=")
                if key in result:
                    result[key] = value
    return result


def _save_env_vars(updates: dict[str, str]) -> None:
    """Atualiza ou adiciona variáveis no arquivo .env sem remover as existentes."""
    lines: list[str] = []
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, encoding="utf-8") as f:
            lines = f.readlines()

    key_all_positions: dict[str, list[int]] = {}
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            k = stripped.split("=", 1)[0]
            key_all_positions.setdefault(k, []).append(i)

    indices_to_remove = {
        idx
        for positions in key_all_positions.values()
        if len(positions) > 1
        for idx in positions[:-1]
    }
    if indices_to_remove:
        lines = [line for i, line in enumerate(
            lines) if i not in indices_to_remove]

    key_positions: dict[str, int] = {}
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            k = stripped.split("=", 1)[0]
            key_positions[k] = i

    for key, value in updates.items():
        entry = f"{key}={value}\n"
        if key in key_positions:
            lines[key_positions[key]] = entry
        else:
            if lines and not lines[-1].endswith("\n"):
                lines[-1] += "\n"
            lines.append(entry)

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)


# ---------------------------------------------------------------------------
# Rotas Git
# ---------------------------------------------------------------------------

@app.route("/api/git/config", methods=["GET"])
def api_git_config_get():
    """Retorna a configuração atual do Git lida do .env."""
    return jsonify({**_read_env_vars(), "env_warnings": _check_env_integrity()})


@app.route("/api/git/config", methods=["POST"])
def api_git_config_save():
    """Salva a configuração do Git no arquivo .env e atualiza variáveis em memória."""
    data: dict[str, str] = request.get_json() or {}
    updates = {k: str(data[k]) for k in _GIT_ENV_KEYS if k in data}
    _save_env_vars(updates)

    if "GIT_REPO_URL" in updates:
        _cfg.GIT_REPO_URL = updates["GIT_REPO_URL"]
    if "GIT_BRANCH" in updates:
        _cfg.GIT_BRANCH = updates["GIT_BRANCH"]
    if "GIT_ACCESS_TOKEN" in updates:
        _cfg.GIT_ACCESS_TOKEN = updates["GIT_ACCESS_TOKEN"]
    if "GIT_SSH_KEY_PATH" in updates:
        _cfg.GIT_SSH_KEY_PATH = updates["GIT_SSH_KEY_PATH"]
    if "GIT_AUTO_UPDATE" in updates:
        _cfg.GIT_AUTO_UPDATE = updates["GIT_AUTO_UPDATE"].lower() in (
            "1", "true", "yes")

    return jsonify({"message": "Configuração salva com sucesso!"})


# ---------------------------------------------------------------------------
# Rotas LLM
# ---------------------------------------------------------------------------

@app.route("/api/llm/config", methods=["GET"])
def api_llm_config_get():
    """Retorna a configuração atual do LLM (valores em memória)."""
    return jsonify({
        "OLLAMA_URL": _cfg.OLLAMA_URL,
        "EMBED_MODEL": _cfg.EMBED_MODEL,
        "LLM_MODEL": _cfg.LLM_MODEL,
        "TOP_K": str(_cfg.TOP_K),
        "OLLAMA_NUM_CTX": str(_cfg.OLLAMA_OPTIONS.get("num_ctx", 8192)),
        "OLLAMA_NUM_PREDICT": str(_cfg.OLLAMA_OPTIONS.get("num_predict", 1024)),
        "OLLAMA_NUM_THREAD": str(_cfg.OLLAMA_OPTIONS.get("num_thread", 8)),
        "OLLAMA_NUM_BATCH": str(_cfg.OLLAMA_OPTIONS.get("num_batch", 512)),
        "OLLAMA_TEMPERATURE": str(_cfg.OLLAMA_OPTIONS.get("temperature", 0.2)),
        "OLLAMA_REPEAT_PENALTY": str(_cfg.OLLAMA_OPTIONS.get("repeat_penalty", 1.3)),
        "PROMPT_TEMPLATE": _cfg.PROMPT_TEMPLATE,
        "env_warnings": _check_env_integrity(),
    })


@app.route("/api/llm/config", methods=["POST"])
def api_llm_config_save():
    """Salva a configuração do LLM no .env e atualiza variáveis em memória."""
    data: dict[str, str] = request.get_json() or {}
    # Encode newlines before saving PROMPT_TEMPLATE to .env (single-line format)
    if "PROMPT_TEMPLATE" in data:
        data["PROMPT_TEMPLATE"] = data["PROMPT_TEMPLATE"].replace("\n", "\\n")
    updates = {k: str(data[k]) for k in _LLM_ENV_KEYS if k in data}
    _save_env_vars(updates)

    if "OLLAMA_URL" in updates:
        _cfg.OLLAMA_URL = updates["OLLAMA_URL"]
    if "EMBED_MODEL" in updates:
        _cfg.EMBED_MODEL = updates["EMBED_MODEL"]
    if "LLM_MODEL" in updates:
        _cfg.LLM_MODEL = updates["LLM_MODEL"]
    if "TOP_K" in updates:
        _cfg.TOP_K = int(updates["TOP_K"])
    if "OLLAMA_NUM_CTX" in updates:
        _cfg.OLLAMA_OPTIONS["num_ctx"] = int(updates["OLLAMA_NUM_CTX"])
    if "OLLAMA_NUM_PREDICT" in updates:
        _cfg.OLLAMA_OPTIONS["num_predict"] = int(updates["OLLAMA_NUM_PREDICT"])
    if "OLLAMA_NUM_THREAD" in updates:
        _cfg.OLLAMA_OPTIONS["num_thread"] = int(updates["OLLAMA_NUM_THREAD"])
    if "OLLAMA_NUM_BATCH" in updates:
        _cfg.OLLAMA_OPTIONS["num_batch"] = int(updates["OLLAMA_NUM_BATCH"])
    if "OLLAMA_TEMPERATURE" in updates:
        _cfg.OLLAMA_OPTIONS["temperature"] = float(
            updates["OLLAMA_TEMPERATURE"])
    if "OLLAMA_REPEAT_PENALTY" in updates:
        _cfg.OLLAMA_OPTIONS["repeat_penalty"] = float(
            updates["OLLAMA_REPEAT_PENALTY"])
    if "PROMPT_TEMPLATE" in updates:
        _cfg.PROMPT_TEMPLATE = updates["PROMPT_TEMPLATE"].replace("\\n", "\n")

    return jsonify({"message": "Configuração LLM salva com sucesso!"})


# ---------------------------------------------------------------------------
# Rotas Indexação
# ---------------------------------------------------------------------------

@app.route("/api/indexing/config", methods=["GET"])
def api_indexing_config_get():
    """Retorna a configuração atual de indexação (valores em memória)."""
    return jsonify({
        "FILE_EXTENSIONS": ",".join(_cfg.FILE_EXTENSIONS),
        "INCLUDE_FILENAMES": ",".join(_cfg.INCLUDE_FILENAMES),
        "IGNORE_DIRS": ",".join(_cfg.IGNORE_DIRS),
        "CHUNK_SIZE": str(_cfg.CHUNK_SIZE),
        "CHUNK_OVERLAP": str(_cfg.CHUNK_OVERLAP),
        "env_warnings": _check_env_integrity(),
    })


@app.route("/api/indexing/config", methods=["POST"])
def api_indexing_config_save():
    """Salva a configuração de indexação no .env e atualiza variáveis em memória."""
    data: dict[str, str] = request.get_json() or {}
    updates = {k: str(data[k]) for k in _INDEXING_ENV_KEYS if k in data}
    _save_env_vars(updates)

    if "FILE_EXTENSIONS" in updates:
        _cfg.FILE_EXTENSIONS = [
            x.strip() for x in updates["FILE_EXTENSIONS"].split(",") if x.strip()]
    if "INCLUDE_FILENAMES" in updates:
        _cfg.INCLUDE_FILENAMES = [
            x.strip() for x in updates["INCLUDE_FILENAMES"].split(",") if x.strip()]
    if "IGNORE_DIRS" in updates:
        _cfg.IGNORE_DIRS = [x.strip()
                            for x in updates["IGNORE_DIRS"].split(",") if x.strip()]
    if "CHUNK_SIZE" in updates:
        _cfg.CHUNK_SIZE = int(updates["CHUNK_SIZE"])
    if "CHUNK_OVERLAP" in updates:
        _cfg.CHUNK_OVERLAP = int(updates["CHUNK_OVERLAP"])

    return jsonify({"message": "Configuração de indexação salva com sucesso!"})


# ---------------------------------------------------------------------------
# Rota: Restaurar .env com valores padrão
# ---------------------------------------------------------------------------

@app.route("/api/env/reset", methods=["POST"])
def api_env_reset():
    """Sobrescreve o .env com todos os valores padrão e atualiza a memória."""
    _PROMPT_DEFAULT_ENCODED = _cfg.PROMPT_DEFAULT.replace("\n", "\\n")

    defaults = {
        "GIT_REPO_URL": "",
        "GIT_BRANCH": "main",
        "GIT_AUTO_UPDATE": "false",
        "GIT_ACCESS_TOKEN": "",
        "GIT_SSH_KEY_PATH": "",
        "OLLAMA_URL": "http://localhost:11434",
        "EMBED_MODEL": "nomic-embed-text",
        "LLM_MODEL": "qwen2.5-coder:3b",
        "TOP_K": "8",
        "OLLAMA_NUM_CTX": "8192",
        "OLLAMA_NUM_PREDICT": "1024",
        "OLLAMA_NUM_THREAD": "8",
        "OLLAMA_NUM_BATCH": "512",
        "OLLAMA_TEMPERATURE": "0.2",
        "OLLAMA_REPEAT_PENALTY": "1.3",
        "PROMPT_TEMPLATE": _PROMPT_DEFAULT_ENCODED,
        "FILE_EXTENSIONS": ",".join([
            ".java", ".py", ".js", ".ts", ".go", ".rs",
            ".c", ".cpp", ".h", ".cs", ".rb", ".php",
            ".kt", ".scala", ".swift", ".m", ".sql", ".sh",
        ]),
        "INCLUDE_FILENAMES": "architecture.md",
        "IGNORE_DIRS": "target,.git,node_modules,__pycache__,.venv,dist,build",
        "CHUNK_SIZE": "1500",
        "CHUNK_OVERLAP": "200",
    }

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        for key, value in defaults.items():
            f.write(f"{key}={value}\n")

    # Atualiza memória
    _cfg.GIT_REPO_URL = defaults["GIT_REPO_URL"]
    _cfg.GIT_BRANCH = defaults["GIT_BRANCH"]
    _cfg.GIT_AUTO_UPDATE = False
    _cfg.GIT_ACCESS_TOKEN = defaults["GIT_ACCESS_TOKEN"]
    _cfg.GIT_SSH_KEY_PATH = defaults["GIT_SSH_KEY_PATH"]
    _cfg.OLLAMA_URL = defaults["OLLAMA_URL"]
    _cfg.EMBED_MODEL = defaults["EMBED_MODEL"]
    _cfg.LLM_MODEL = defaults["LLM_MODEL"]
    _cfg.TOP_K = 8
    _cfg.OLLAMA_OPTIONS["num_ctx"] = 8192
    _cfg.OLLAMA_OPTIONS["num_predict"] = 1024
    _cfg.OLLAMA_OPTIONS["num_thread"] = 8
    _cfg.OLLAMA_OPTIONS["num_batch"] = 512
    _cfg.OLLAMA_OPTIONS["temperature"] = 0.2
    _cfg.OLLAMA_OPTIONS["repeat_penalty"] = 1.3
    _cfg.PROMPT_TEMPLATE = _cfg.PROMPT_DEFAULT
    _cfg.FILE_EXTENSIONS = [x.strip()
                            for x in defaults["FILE_EXTENSIONS"].split(",")]
    _cfg.INCLUDE_FILENAMES = ["architecture.md"]
    _cfg.IGNORE_DIRS = [x.strip() for x in defaults["IGNORE_DIRS"].split(",")]
    _cfg.CHUNK_SIZE = 1500
    _cfg.CHUNK_OVERLAP = 200

    return jsonify({"message": ".env restaurado para os valores padrão."})


# ---------------------------------------------------------------------------
# Rota: Limpar codebase e índice ChromaDB
# ---------------------------------------------------------------------------

_CHROMA_SEGMENT_RE = _re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
)


@app.route("/api/codebase/clear", methods=["POST"])
def api_codebase_clear():
    """Limpa a coleção do ChromaDB e o diretório .codebase/."""
    import shutil

    # Remove a coleção via API do ChromaDB (mantém o chroma.sqlite3 íntegro)
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        client.delete_collection("codebase")
    except Exception:
        pass

    # Remove subpastas UUID de segmentos HNSW órfãos
    if os.path.exists(CHROMA_PATH):
        for entry in os.scandir(CHROMA_PATH):
            if entry.is_dir() and _CHROMA_SEGMENT_RE.match(entry.name):
                shutil.rmtree(entry.path)

    # Limpa .codebase/ e recria a pasta vazia
    if os.path.exists(CODE_PATH):
        shutil.rmtree(CODE_PATH)
    os.makedirs(CODE_PATH, exist_ok=True)
    open(os.path.join(CODE_PATH, ".gitkeep"), "w").close()

    return jsonify({"message": "Codebase e índice removidos com sucesso."})


def _sse(event_type: str, text: str) -> str:
    return f"data: {_json.dumps({'type': event_type, 'text': text})}\n\n"


def _index_into_collection_stream() -> Iterator[str]:
    """Reindexa a codebase no ChromaDB emitindo eventos SSE de progresso."""
    docs = read_files(CODE_PATH)
    total_files = len(docs)

    all_chunks: list[tuple[str, str, dict[str, str | int]]] = []
    for path, content in docs:
        ext = os.path.splitext(path)[1].lower()
        for chunk, chunk_meta in chunk_by_language(content, ext):
            all_chunks.append((path, chunk, {
                              "file": path, "name": chunk_meta["name"], "line": chunk_meta["line"], "kind": chunk_meta["kind"], "language": ext.lstrip(".")}))

    total_chunks = len(all_chunks)
    yield _sse("log", f"{total_files} arquivo(s) encontrado(s) — {total_chunks} chunks para indexar...")

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    try:
        client.delete_collection("codebase")
    except Exception:
        pass
    collection = client.get_or_create_collection("codebase")

    for i, (path, chunk, metadata) in enumerate(all_chunks, start=1):
        full_chunk = f"FILE: {path}\n\n{chunk}"
        emb = embed(full_chunk)
        collection.add(
            ids=[str(i - 1)],
            embeddings=[emb],
            documents=[full_chunk],
            metadatas=[metadata],
        )
        yield _sse("log", f"Indexando chunk {i}/{total_chunks}...")

    yield _sse("done", f"Concluído! {total_chunks} chunks indexados de {total_files} arquivo(s).")


@app.route("/api/git/sync", methods=["POST"])
def api_git_sync():
    """Clona/atualiza repositório git e reindexa a codebase (SSE)."""
    data: dict[str, str] = request.get_json() or {}
    repo_url: str | None = data.get("repo_url") or None
    branch: str | None = data.get("branch") or None
    token: str | None = data.get("token") or None

    def event_stream() -> Iterator[str]:
        from minorag.git import clone_repo

        yield _sse("log", "Clonando repositório...")
        ok = clone_repo(repo_url, branch, token)
        if not ok:
            yield _sse("error", "Falha ao clonar. Verifique a URL e as credenciais.")
            return

        try:
            yield from _index_into_collection_stream()
        except Exception as exc:
            yield _sse("error", f"Erro na indexação: {exc}")

    return Response(stream_with_context(event_stream()), mimetype="text/event-stream")
