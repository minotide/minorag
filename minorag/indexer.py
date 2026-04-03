import os

import chromadb

from minorag.config import (
    CHROMA_PATH,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    CODE_PATH,
    FILE_EXTENSIONS,
    IGNORE_DIRS,
)
from minorag.ollama import embed


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


def index_code():
    print("Lendo arquivos...")
    docs = read_files(CODE_PATH)

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection("codebase")

    print("Gerando embeddings...")

    id_counter = 0

    for path, content in docs:
        chunks = chunk_text(content)

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

    print(f"Indexação concluída! ({id_counter} chunks)")
