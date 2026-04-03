import json
import os

import chromadb
import requests

from minorag.config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    CODE_PATH,
    CHROMA_PATH,
    EMBED_MODEL,
    FILE_EXTENSIONS,
    IGNORE_DIRS,
    LLM_MODEL,
    OLLAMA_URL,
    TOP_K,
)


# -----------------------------
# Utils
# -----------------------------
def read_files(path):
    docs = []
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            if any(file.endswith(ext) for ext in FILE_EXTENSIONS):
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        docs.append((full_path, content))
                except Exception:
                    pass
    return docs


def chunk_text(text):
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end]
        chunks.append(chunk)
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def embed(text):
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
            timeout=120,
        )
        response.raise_for_status()
        return response.json()["embedding"]
    except requests.exceptions.ConnectionError:
        print("\nOllama não está respondendo. Inicie-o com:\n\n    ollama serve &\n")
        raise SystemExit(1)


def generate(prompt):
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": LLM_MODEL, "prompt": prompt, "stream": False},
            timeout=300,
        )
        response.raise_for_status()
        return response.json()["response"]
    except requests.exceptions.ConnectionError:
        print("\nOllama não está respondendo. Inicie-o com:\n\n    ollama serve &\n")
        raise SystemExit(1)


def generate_stream(prompt):
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": LLM_MODEL, "prompt": prompt, "stream": True},
            timeout=300,
            stream=True,
        )
        response.raise_for_status()
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                token = data.get("response", "")
                if token:
                    print(token, end="", flush=True)
                if data.get("done"):
                    break
    except requests.exceptions.ConnectionError:
        print("\nOllama não está respondendo. Inicie-o com:\n\n    ollama serve &\n")
        raise SystemExit(1)


def generate_stream_iter(prompt):
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": LLM_MODEL, "prompt": prompt, "stream": True},
            timeout=300,
            stream=True,
        )
        response.raise_for_status()
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                token = data.get("response", "")
                if token:
                    yield token
                if data.get("done"):
                    break
    except requests.exceptions.ConnectionError:
        yield "\nOllama não está respondendo. Inicie-o com:\n\n    ollama serve &\n"


# -----------------------------
# Indexação
# -----------------------------
def index_code():
    print("Lendo arquivos...")
    docs = read_files(CODE_PATH)

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection("codebase")

    print("Gerando embeddings...")

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

    print(f"Indexação concluída! ({id_counter} chunks)")


# -----------------------------
# Query
# -----------------------------
def query_loop():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection("codebase")

    while True:
        question = input("\nPergunta: ")

        if question.lower() in ["exit", "quit"]:
            break

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

        print("\nPensando...\n")
        generate_stream(prompt)
        print()
