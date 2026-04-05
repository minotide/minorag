"""Worker threads para operações RAG e sincronização."""

import os

import chromadb
from PySide6.QtCore import QThread, Signal

from minorag import config as _cfg
from minorag.config import CHROMA_PATH, CODE_PATH
from minorag.chunkers import chunk_by_language
from minorag.indexer import read_files
from minorag.ollama import embed, generate_stream_iter
from minorag.retriever import build_chunks_context, build_prompt


class QueryWorker(QThread):
    """Executa a consulta RAG em thread separada com streaming de tokens."""
    token_received = Signal(str)
    log_received = Signal(str)
    error_occurred = Signal(str)
    finished_signal = Signal()

    def __init__(self, question: str) -> None:
        super().__init__()
        self.question = question

    def run(self) -> None:
        try:
            client = chromadb.PersistentClient(path=CHROMA_PATH)
            try:
                collection = client.get_collection("codebase")
            except Exception:
                self.error_occurred.emit(
                    "Índice não encontrado. Indexe o código primeiro. "
                    "Caminho: Repositório → Sincronizar Codebase"
                )
                return

            self.log_received.emit("Gerando embedding da pergunta...")
            q_emb = embed(self.question)

            self.log_received.emit("Buscando contexto no índice...")
            results = collection.query(
                query_embeddings=[q_emb], n_results=_cfg.TOP_K
            )

            self.log_received.emit("Gerando resposta...")
            docs = (results["documents"] or [[]])[0]
            metas = (results["metadatas"] or [[]])[0]
            chunks = build_chunks_context(docs, metas)

            for token in generate_stream_iter(build_prompt(self.question, chunks, metas)):
                self.token_received.emit(token)

        except Exception as exc:
            self.error_occurred.emit(str(exc))
        finally:
            self.finished_signal.emit()


class SyncWorker(QThread):
    """Clona repositório e reindexa a codebase em thread separada."""
    log_received = Signal(str)
    error_occurred = Signal(str)
    finished_signal = Signal(str)

    def __init__(self, repo_url: str | None = None, branch: str | None = None, token: str | None = None) -> None:
        super().__init__()
        self.repo_url = repo_url
        self.branch = branch
        self.token = token

    def run(self) -> None:
        try:
            from minorag.git import clone_repo

            self.log_received.emit("Clonando repositório...")
            ok = clone_repo(self.repo_url, self.branch, self.token)
            if not ok:
                self.error_occurred.emit(
                    "Falha ao clonar. Verifique a URL e as credenciais."
                )
                return

            docs = read_files(CODE_PATH)
            total_files = len(docs)

            all_chunks: list[tuple[str, str, dict[str, str | int]]] = []
            for path, content in docs:
                ext = os.path.splitext(path)[1].lower()
                for chunk, chunk_meta in chunk_by_language(content, ext):
                    all_chunks.append((path, chunk, {
                        "file": path,
                        "name": chunk_meta["name"],
                        "line": chunk_meta["line"],
                        "kind": chunk_meta["kind"],
                        "language": ext.lstrip("."),
                    }))

            total_chunks = len(all_chunks)
            self.log_received.emit(
                f"{total_files} arquivo(s) encontrado(s) — {total_chunks} chunks para indexar..."
            )

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
                self.log_received.emit(
                    f"Indexando chunk {i}/{total_chunks}...")

            self.finished_signal.emit(
                f"Concluído! {total_chunks} chunks indexados de {total_files} arquivo(s)."
            )
        except Exception as exc:
            self.error_occurred.emit(str(exc))
