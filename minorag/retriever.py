import chromadb

from minorag.config import CHROMA_PATH, TOP_K
from minorag.ollama import embed, generate_stream


def build_prompt(question, chunks):
    return f"""You are a senior software engineer.

Use the code context below to answer.

Context:
----------------
{chunks}
----------------

Question:
{question}

Answer clearly and technically."""


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
        prompt = build_prompt(question, chunks)

        print("\nPensando...\n")
        generate_stream(prompt)
        print()
