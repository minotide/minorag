"""
Módulo da interface web do minorag.

Expõe uma aplicação Flask com rotas para indexação de código
e consulta ao índice via Server-Sent Events (SSE) com streaming de tokens.
"""

import json as _json
import os

import chromadb
from flask import Flask, Response, jsonify, request, send_from_directory, stream_with_context

from minorag.config import CHROMA_PATH, CODE_PATH, ENV_PATH, GIT_ACCESS_TOKEN, GIT_BRANCH, GIT_REPO_URL, TOP_K
from minorag.chunkers import chunk_by_language
from minorag.indexer import read_files
from minorag.ollama import embed, generate, generate_stream_iter
from minorag.retriever import build_prompt

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

app = Flask(__name__, static_folder=STATIC_DIR)


@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


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
        repo_url = GIT_REPO_URL.strip()
        if not repo_url:
            return jsonify({"error": "Nenhum arquivo encontrado em .codebase/. Configure e clone um repositório pelo painel Git."}), 400

        from minorag.git import clone_repo
        ok = clone_repo(repo_url, GIT_BRANCH or "main",
                        GIT_ACCESS_TOKEN or None)
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

        for chunk in chunks:
            full_chunk = f"FILE: {path}\n\n{chunk}"
            emb = embed(full_chunk)

            collection.add(
                ids=[str(id_counter)],
                embeddings=[emb],
                documents=[full_chunk],
                metadatas=[{"file": path}],
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
        return jsonify({"error": "Índice não encontrado. Indexe o código primeiro."}), 400

    q_emb = embed(question)

    results = collection.query(query_embeddings=[q_emb], n_results=TOP_K)

    chunks = "\n\n---\n\n".join((results["documents"] or [[]])[0])

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

    def event_stream():
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        try:
            collection = client.get_collection("codebase")
        except Exception:
            yield f"data: {_json.dumps({'type': 'error', 'text': 'Índice não encontrado. Indexe o código primeiro.'})}\n\n"
            return

        yield f"data: {_json.dumps({'type': 'log', 'text': 'Gerando embedding da pergunta...'})}\n\n"
        q_emb = embed(question)

        yield f"data: {_json.dumps({'type': 'log', 'text': 'Buscando contexto no índice...'})}\n\n"
        results = collection.query(query_embeddings=[q_emb], n_results=TOP_K)

        yield f"data: {_json.dumps({'type': 'log', 'text': 'Gerando resposta...'})}\n\n"
        chunks = "\n\n---\n\n".join((results["documents"] or [[]])[0])

        for token in generate_stream_iter(build_prompt(question, chunks)):
            yield f"data: {_json.dumps({'type': 'token', 'text': token})}\n\n"

        yield f"data: {_json.dumps({'type': 'done'})}\n\n"

    return Response(stream_with_context(event_stream()), mimetype="text/event-stream")


# ---------------------------------------------------------------------------
# Helpers para leitura/escrita do .env
# ---------------------------------------------------------------------------

_GIT_ENV_KEYS = ["GIT_REPO_URL", "GIT_BRANCH",
                 "GIT_AUTO_UPDATE", "GIT_ACCESS_TOKEN", "GIT_SSH_KEY_PATH"]


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
            lines.append(entry)

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)


# ---------------------------------------------------------------------------
# Rotas Git
# ---------------------------------------------------------------------------

@app.route("/api/git/config", methods=["GET"])
def api_git_config_get():
    """Retorna a configuração atual do Git lida do .env."""
    return jsonify(_read_env_vars())


@app.route("/api/git/config", methods=["POST"])
def api_git_config_save():
    """Salva a configuração do Git no arquivo .env."""
    data = request.get_json() or {}
    updates = {k: str(data[k]) for k in _GIT_ENV_KEYS if k in data}
    _save_env_vars(updates)
    return jsonify({"message": "Configuração salva com sucesso!"})


def _sse(event_type: str, text: str) -> str:
    return f"data: {_json.dumps({'type': event_type, 'text': text})}\n\n"


def _index_into_collection() -> int:
    """Reindexa a codebase no ChromaDB e retorna o total de chunks."""
    docs = read_files(CODE_PATH)

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    try:
        client.delete_collection("codebase")
    except Exception:
        pass
    collection = client.get_or_create_collection("codebase")

    id_counter = 0
    for path, content in docs:
        ext = os.path.splitext(path)[1].lower()
        chunks = chunk_by_language(content, ext)
        for chunk in chunks:
            full_chunk = f"FILE: {path}\n\n{chunk}"
            emb = embed(full_chunk)
            collection.add(
                ids=[str(id_counter)],
                embeddings=[emb],
                documents=[full_chunk],
                metadatas=[{"file": path}],
            )
            id_counter += 1

    return id_counter


@app.route("/api/git/sync", methods=["POST"])
def api_git_sync():
    """Clona/atualiza repositório git e reindexa a codebase (SSE)."""
    data = request.get_json() or {}
    repo_url = data.get("repo_url") or None
    branch = data.get("branch") or None
    token = data.get("token") or None

    def event_stream():
        from minorag.git import clone_repo

        yield _sse("log", "Clonando repositório...")
        ok = clone_repo(repo_url, branch, token)
        if not ok:
            yield _sse("error", "Falha ao clonar. Verifique a URL e as credenciais.")
            return

        yield _sse("log", "Indexando código...")
        try:
            total = _index_into_collection()
        except Exception as exc:
            yield _sse("error", f"Erro na indexação: {exc}")
            return

        yield _sse("done", f"Concluído! {total} chunks indexados.")

    return Response(stream_with_context(event_stream()), mimetype="text/event-stream")
