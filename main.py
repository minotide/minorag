import threading


def _auto_index():
    """Executa indexação automática na inicialização quando aplicável.

    - Se GIT_AUTO_UPDATE=true: atualiza o repositório e re-indexa.
    - Caso contrário: indexa automaticamente se a codebase tiver arquivos
      mas ainda não existir um índice no ChromaDB.
    """
    from minorag import config as _cfg
    from minorag.config import CHROMA_PATH, CODE_PATH
    from minorag.indexer import read_files

    if _cfg.GIT_AUTO_UPDATE:
        from minorag.git import update_and_index
        print("GIT_AUTO_UPDATE ativo: atualizando repositório e re-indexando...")
        update_and_index()
        return

    if read_files(CODE_PATH):
        import chromadb
        try:
            client = chromadb.PersistentClient(path=CHROMA_PATH)
            client.get_collection("codebase")
        except Exception:
            from minorag.indexer import index_code
            print("Codebase encontrada sem índice: indexando automaticamente...")
            index_code()


if __name__ == "__main__":
    threading.Thread(target=_auto_index, daemon=True).start()
    from minorag.gui import run_gui
    run_gui()
