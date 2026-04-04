CODE_PATH = "./codebase"
CHROMA_PATH = "./.chromadb"

FILE_EXTENSIONS = [
    ".java", ".py", ".js", ".ts", ".go", ".rs",
    ".c", ".cpp", ".h", ".cs", ".rb", ".php",
    ".kt", ".scala", ".swift", ".m",
    ".sql", ".sh",
]

INCLUDE_FILENAMES = [
    "architecture.md",
]

IGNORE_DIRS = [
    "target", ".git", "node_modules",
    "__pycache__", ".venv", "dist", "build"
]

CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200

OLLAMA_URL = "http://localhost:11434"

EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "qwen2.5-coder:3b"

TOP_K = 8

OLLAMA_OPTIONS: dict[str, int | float] = {
    "num_ctx": 8192,
    "num_predict": 1024,
    "num_thread": 8,
    "num_batch": 512,
    "temperature": 0.2,
    "repeat_penalty": 1.3,
}

PROMPT_TEMPLATE = """
You are a code assistant. Answer the question using ONLY the code snippets provided below.
If the answer is not present in the snippets, say: "I don't have enough context to answer this accurately."
Do not use any knowledge beyond what is shown.

Code snippets: {chunks}

Question: {question}

Answer:
"""
