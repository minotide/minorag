import os
from pathlib import Path

from dotenv import load_dotenv

_ENV_PATH = Path(__file__).parent.parent / ".env"
ENV_PATH = str(_ENV_PATH)

load_dotenv(_ENV_PATH)

CODE_PATH = "./.codebase"
CHROMA_PATH = "./.chromadb"


def _parse_list_env(key: str, default: list[str]) -> list[str]:
    """Lê uma variável do .env como lista separada por vírgulas."""
    val = os.getenv(key, "").strip()
    if not val:
        return list(default)
    return [item.strip() for item in val.split(",") if item.strip()]


# ---------------------------------------------------------------------------
# Repositório Git
# ---------------------------------------------------------------------------

GIT_REPO_URL: str = os.getenv("GIT_REPO_URL", "")
GIT_BRANCH: str = os.getenv("GIT_BRANCH", "main")
GIT_AUTO_UPDATE: bool = os.getenv(
    "GIT_AUTO_UPDATE", "false").lower() in ("1", "true", "yes")
GIT_ACCESS_TOKEN: str = os.getenv("GIT_ACCESS_TOKEN", "")
GIT_SSH_KEY_PATH: str = os.getenv("GIT_SSH_KEY_PATH", "")

# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------

OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL: str = os.getenv("EMBED_MODEL", "nomic-embed-text")
LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen2.5-coder:3b")
TOP_K: int = int(os.getenv("TOP_K", "8"))

OLLAMA_OPTIONS: dict[str, int | float] = {
    "num_ctx": int(os.getenv("OLLAMA_NUM_CTX", "8192")),
    "num_predict": int(os.getenv("OLLAMA_NUM_PREDICT", "1024")),
    "num_thread": int(os.getenv("OLLAMA_NUM_THREAD", "8")),
    "num_batch": int(os.getenv("OLLAMA_NUM_BATCH", "512")),
    "temperature": float(os.getenv("OLLAMA_TEMPERATURE", "0.2")),
    "repeat_penalty": float(os.getenv("OLLAMA_REPEAT_PENALTY", "1.3")),
}

_PROMPT_DEFAULT = (
    "Você é um assistente de código. Responda SEMPRE em português.\n"
    "Responda a pergunta utilizando APENAS os trechos de código fornecidos abaixo.\n"
    "Não utilize nenhum conhecimento além do que está nos trechos.\n"
    "Se a pergunta não estiver relacionada ao código fornecido, responda exatamente:\n"
    "\"Essa pergunta está fora do contexto do seu código.\"\n"
    "\n"
    "Trechos de código: {chunks}\n"
    "\n"
    "Pergunta: {question}\n"
    "\n"
    "Resposta:"
)

_prompt_raw = os.getenv("PROMPT_TEMPLATE", "").strip()
PROMPT_TEMPLATE: str = _prompt_raw.replace(
    "\\n", "\n") if _prompt_raw else _PROMPT_DEFAULT

# ---------------------------------------------------------------------------
# Indexação
# ---------------------------------------------------------------------------

_DEFAULT_FILE_EXTENSIONS = [
    ".java", ".py", ".js", ".ts", ".go", ".rs",
    ".c", ".cpp", ".h", ".cs", ".rb", ".php",
    ".kt", ".scala", ".swift", ".m",
    ".sql", ".sh",
]
_DEFAULT_INCLUDE_FILENAMES = ["architecture.md"]
_DEFAULT_IGNORE_DIRS = [
    "target", ".git", "node_modules",
    "__pycache__", ".venv", "dist", "build",
]

FILE_EXTENSIONS: list[str] = _parse_list_env(
    "FILE_EXTENSIONS", _DEFAULT_FILE_EXTENSIONS)
INCLUDE_FILENAMES: list[str] = _parse_list_env(
    "INCLUDE_FILENAMES", _DEFAULT_INCLUDE_FILENAMES)
IGNORE_DIRS: list[str] = _parse_list_env("IGNORE_DIRS", _DEFAULT_IGNORE_DIRS)

CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1500"))
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))

# ---------------------------------------------------------------------------
# Interface web
# ---------------------------------------------------------------------------

WEB_PORT: int = int(os.getenv("WEB_PORT", "5000"))
