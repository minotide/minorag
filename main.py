import os
import requests
import chromadb
from config import *

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
    response = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={
            "model": EMBED_MODEL,
            "prompt": text
        },
        timeout=120
    )
    response.raise_for_status()
    return response.json()["embedding"]


def generate(prompt):
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": LLM_MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=300
    )
    response.raise_for_status()
    return response.json()["response"]


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
                metadatas=[{"file": path}]
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

        results = collection.query(
            query_embeddings=[q_emb],
            n_results=TOP_K
        )

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

        print("\nResposta:\n")
        print(answer)


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    print("1 - Indexar código")
    print("2 - Fazer perguntas")

    choice = input("> ")

    if choice == "1":
        index_code()
    else:
        query_loop()
