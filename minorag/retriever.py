
"""
Módulo de recuperação e geração de respostas (RAG).

Responsável por buscar chunks relevantes no índice vetorial,
construir o prompt e acionar o modelo LLM para responder perguntas.
"""

from collections import Counter

import chromadb
from typing import Sequence, Mapping, Any

from minorag import config as _cfg
from minorag.config import CHROMA_PATH, LANG_NAMES, TOP_K
from minorag.ollama import embed, generate_stream


def build_chunks_context(
    docs: Sequence[str],
    metas: Sequence[Mapping[str, Any]],
) -> str:
    """
    Monta a string de contexto enriquecida com metadados de localização.

    Cada chunk recebe um cabeçalho com arquivo, linha e símbolo extraídos
    dos metadados do ChromaDB, permitindo que o LLM cite localizações precisas.

    @param docs: Lista de documentos retornados pelo ChromaDB.
    @param metas: Lista de metadados correspondentes a cada documento.
    @return: String formatada com cabeçalhos de localização entre separadores.
    """
    parts: list[str] = []
    for doc, meta in zip(docs, metas):
        header_parts = [f"FILE: {meta.get('file', '')}"]
        line = meta.get("line")
        if line is not None:
            header_parts.append(f"LINE: {line}")
        name = meta.get("name")
        if name:
            kind = meta.get("kind", "")
            symbol = f"SYMBOL: {name}"
            if kind:
                symbol += f" [{kind}]"
            header_parts.append(symbol)
        header = " | ".join(header_parts)
        parts.append(f"### {header}\n\n{doc}")
    return "\n\n---\n\n".join(parts)


def build_prompt(question: str, chunks: str, metas: Sequence[Mapping[str, Any]] = ()) -> str:
    """
    Constrói o prompt completo para envio ao modelo LLM.

    Usa o template definido em PROMPT_TEMPLATE (config.py).
    O template deve conter os marcadores {question} e {chunks}.
    Se o template contiver {language_expertise}, injeta a especialização
    detectada dinamicamente a partir dos metadados dos chunks recuperados.

    @param question: Pergunta feita pelo usuário.
    @param chunks: Trechos de código recuperados do índice, concatenados como contexto.
    @param metas: Metadados dos chunks para detecção de linguagem.
    @return: String com o prompt formatado para o modelo.
    """
    template = _cfg.PROMPT_TEMPLATE
    if "{language_expertise}" in template:
        expertise = _build_language_expertise(metas)
        template = template.replace("{language_expertise}", expertise)
    return template.format(question=question, chunks=chunks)


def detect_languages(metas: Sequence[Mapping[str, Any]]) -> list[str]:
    """
    Detecta as linguagens presentes nos chunks recuperados, ordenadas por frequência.

    @param metas: Lista de metadados dos chunks (campo 'language').
    @return: Lista de nomes de linguagens ordenadas da mais frequente para a menos.
    """
    counts: Counter[str] = Counter()
    for m in metas:
        lang = m.get("language", "")
        if lang:
            counts[lang] += 1
    return [LANG_NAMES.get(ext, ext) for ext, _ in counts.most_common()]


def _build_language_expertise(metas: Sequence[Mapping[str, Any]]) -> str:
    """Monta a string de especialização em linguagem para o prompt."""
    langs = detect_languages(metas)
    if not langs:
        return "análise de código"
    if len(langs) == 1:
        return f"{langs[0]} e análise de código"
    # ex: "Python, Java e análise de código"
    return f"{', '.join(langs[:-1])}, {langs[-1]} e análise de código"


def query_loop():
    """
    Inicia o loop interativo de perguntas no terminal.

    Aguarda perguntas do usuário via stdin, busca o contexto relevante
    no ChromaDB e exibe a resposta da LLM em streaming.
    Use 'exit' ou 'quit' para encerrar.
    """
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection("codebase")

    while True:
        question = input("\nPergunta: ")

        if question.lower() in ["exit", "quit"]:
            break

        print("\nGerando embedding da pergunta...")
        q_emb = embed(question)
        print("Buscando contexto no índice...")
        results = collection.query(query_embeddings=[q_emb], n_results=TOP_K)
        print("Gerando resposta...\n")

        docs = (results["documents"] or [[]])[0]
        metas = (results["metadatas"] or [[]])[0]
        chunks = build_chunks_context(docs, metas)
        prompt = build_prompt(question, chunks, metas)
        generate_stream(prompt)
        print()
