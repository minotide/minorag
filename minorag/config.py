CODE_PATH = "./codebase"
CHROMA_PATH = "./.chromadb"

FILE_EXTENSIONS = [
    ".java", ".py", ".js", ".ts", ".go", ".rs",
    ".c", ".cpp", ".h", ".cs", ".rb", ".php",
    ".kt", ".scala", ".swift", ".m",
    ".sql", ".sh", ".md",
]

IGNORE_DIRS = [
    "target", ".git", "node_modules",
    "__pycache__", ".venv", "dist", "build"
]

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

OLLAMA_URL = "http://localhost:11434"

EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "qwen2.5-coder:3b"

TOP_K = 8

OLLAMA_OPTIONS: dict[str, int | float] = {
    "num_ctx": 4096,
    "num_predict": 1024,
    "num_thread": 8,
    "num_batch": 512,
    "temperature": 0.2,
}

PROMPT_TEMPLATE = """
You are a senior software engineer answering questions about a codebase.

RULES:
- Answer ONLY based on the code context provided below.
- If the context does not contain enough information to answer, say "I don't have enough context to answer this accurately."

Context:
----------------
{chunks}
----------------

Question:
{question}

Answer clearly and technically
"""
