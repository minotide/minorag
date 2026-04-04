"""
Módulo da interface web do minorag.

Expõe uma aplicação Flask com rotas para indexação de código
e consulta ao índice via Server-Sent Events (SSE) com streaming de tokens.
"""

import json as _json
import os

import chromadb
from flask import Flask, Response, jsonify, request, send_from_directory, stream_with_context

from minorag.config import CHROMA_PATH, CODE_PATH, TOP_K
from minorag.indexer import chunk_text, read_files
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

    Reindexa do zero, removendo a coleção anterior para evitar duplicatas.

    @return: JSON com mensagem de sucesso e total de chunks, ou erro 400.
    """
    docs = read_files(CODE_PATH)

    if not docs:
        return jsonify({"error": "Nenhum arquivo encontrado em codebase/"}), 400

    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # Reset collection to avoid duplicates on re-index
    try:
        client.delete_collection("codebase")
    except Exception:
        pass

    collection = client.create_collection("codebase")

    id_counter = 0

    for path, content in docs:
        chunks = chunk_text(content)

        for i, chunk in enumerate(chunks):
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

    chunks = "\n\n---\n\n".join(results["documents"][0])

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
        chunks = "\n\n---\n\n".join(results["documents"][0])

        for token in generate_stream_iter(build_prompt(question, chunks)):
            yield f"data: {_json.dumps({'type': 'token', 'text': token})}\n\n"

        yield f"data: {_json.dumps({'type': 'done'})}\n\n"

    return Response(stream_with_context(event_stream()), mimetype="text/event-stream")
