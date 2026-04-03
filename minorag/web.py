import os

import chromadb
from flask import Flask, jsonify, request, send_from_directory

from minorag.config import CHROMA_PATH, CODE_PATH, TOP_K
from minorag.core import chunk_text, embed, generate, read_files

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

app = Flask(__name__, static_folder=STATIC_DIR)


@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/api/index", methods=["POST"])
def api_index():
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

    prompt = f"""You are a senior software engineer.

Use the code context below to answer.

Context:
----------------
{chunks}
----------------

Question:
{question}

Answer clearly and technically."""

    answer = generate(prompt)

    return jsonify({"answer": answer})
