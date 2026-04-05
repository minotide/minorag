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
TOP_K: int = int(os.getenv("TOP_K", "5"))

OLLAMA_OPTIONS: dict[str, int | float] = {
    "num_ctx": int(os.getenv("OLLAMA_NUM_CTX", "4096")),
    "num_predict": int(os.getenv("OLLAMA_NUM_PREDICT", "768")),
    "num_thread": int(os.getenv("OLLAMA_NUM_THREAD", "8")),
    "num_batch": int(os.getenv("OLLAMA_NUM_BATCH", "256")),
    "temperature": float(os.getenv("OLLAMA_TEMPERATURE", "0.2")),
    "repeat_penalty": float(os.getenv("OLLAMA_REPEAT_PENALTY", "1.15")),
}

PROMPT_DEFAULT = (
    "Você é um engenheiro de software sênior especializado em {language_expertise}.\n"
    "Responda sempre em português. Seja conciso e direto.\n"
    "\n"
    "REGRAS:\n"
    "- Baseie-se EXCLUSIVAMENTE nos trechos de código fornecidos abaixo.\n"
    "- NÃO invente informações. Se não houver dados suficientes, diga.\n"
    "- Use os metadados (FILE, LINE, SYMBOL) dos cabeçalhos para citar localizações.\n"
    "- Correlacione trechos quando a pergunta envolver múltiplos arquivos.\n"
    "\n"
    "CÓDIGO:\n"
    "{chunks}\n"
    "\n"
    "PERGUNTA:\n"
    "{question}\n"
    "\n"
    "FORMATO DA RESPOSTA:\n"
    "### Resposta\n"
    "<resposta direta e objetiva>\n"
    "\n"
    "### Localização no código\n"
    "- Arquivo, símbolo, tipo e linha inicial de cada trecho relevante\n"
    "\n"
    "### Evidências no código\n"
    "<trechos ou descrição que sustentam a resposta>\n"
)

_prompt_raw = os.getenv("PROMPT_TEMPLATE", "").strip()
PROMPT_TEMPLATE: str = _prompt_raw.replace(
    "\\n", "\n") if _prompt_raw else PROMPT_DEFAULT

# ---------------------------------------------------------------------------
# Mapeamento extensão → nome da linguagem
# ---------------------------------------------------------------------------

LANG_NAMES: dict[str, str] = {
    "py": "Python",
    "java": "Java",
    "js": "JavaScript",
    "ts": "TypeScript",
    "go": "Go",
    "rs": "Rust",
    "c": "C",
    "cpp": "C++",
    "h": "C/C++",
    "cs": "C#",
    "rb": "Ruby",
    "php": "PHP",
    "kt": "Kotlin",
    "scala": "Scala",
    "swift": "Swift",
    "m": "Objective-C",
    "sql": "SQL",
    "sh": "Shell Script",
}

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
