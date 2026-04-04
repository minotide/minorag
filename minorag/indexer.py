"""
Módulo de indexação de código-fonte no ChromaDB.
Responsável por ler arquivos do diretório de código e armazenar
seus embeddings no banco vetorial.
"""

import os

import chromadb

from minorag.chunkers import chunk_by_language
from minorag.config import (
    CHROMA_PATH,
    CODE_PATH,
    FILE_EXTENSIONS,
    IGNORE_DIRS,
)
from minorag.ollama import embed


def read_files(path: str) -> list[tuple[str, str]]:
    """
    Lê recursivamente os arquivos de código do diretório informado.

    Ignora diretórios definidos em IGNORE_DIRS e filtra apenas
    extensões definidas em FILE_EXTENSIONS.

    @param path: Caminho raiz para iniciar a leitura.
    @return: Lista de tuplas (caminho_absoluto, conteúdo) dos arquivos lidos.
    """
    docs: list[tuple[str, str]] = []
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            if any(file.endswith(ext) for ext in FILE_EXTENSIONS):
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        docs.append((full_path, f.read()))
                except Exception:
                    pass
    return docs


def index_code():
    """
    Indexa todos os arquivos de código da pasta codebase/ no ChromaDB.

    Lê os arquivos, divide em chunks, gera embeddings via Ollama
    e armazena os vetores na coleção 'codebase' do ChromaDB.
    """
    print("Lendo arquivos...")
    docs = read_files(CODE_PATH)

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection("codebase")

    print("Gerando embeddings...")

    id_counter = 0

    for path, content in docs:
        ext = os.path.splitext(path)[1].lower()
        chunks = chunk_by_language(content, ext)

        for chunk in chunks:
            if not chunk.strip():
                continue
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
