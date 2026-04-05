"""Helpers para leitura/escrita do arquivo .env."""

import os
import re as _re
import shutil

import chromadb

from minorag import config as _cfg
from minorag.config import CHROMA_PATH, CODE_PATH, ENV_PATH


def save_env_vars(updates: dict[str, str]) -> None:
    lines: list[str] = []
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, encoding="utf-8") as f:
            lines = f.readlines()

    key_all_positions: dict[str, list[int]] = {}
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            k = stripped.split("=", 1)[0]
            key_all_positions.setdefault(k, []).append(i)

    indices_to_remove = {
        idx
        for positions in key_all_positions.values()
        if len(positions) > 1
        for idx in positions[:-1]
    }
    if indices_to_remove:
        lines = [line for i, line in enumerate(
            lines) if i not in indices_to_remove]

    key_positions: dict[str, int] = {}
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            k = stripped.split("=", 1)[0]
            key_positions[k] = i

    for key, value in updates.items():
        entry = f"{key}={value}\n"
        if key in key_positions:
            lines[key_positions[key]] = entry
        else:
            if lines and not lines[-1].endswith("\n"):
                lines[-1] += "\n"
            lines.append(entry)

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)


def reset_env_defaults() -> None:
    _PROMPT_DEFAULT_ENCODED = _cfg.PROMPT_DEFAULT.replace("\n", "\\n")
    defaults = {
        "GIT_REPO_URL": "",
        "GIT_BRANCH": "main",
        "GIT_AUTO_UPDATE": "false",
        "GIT_ACCESS_TOKEN": "",
        "GIT_SSH_KEY_PATH": "",
        "OLLAMA_URL": "http://localhost:11434",
        "EMBED_MODEL": "nomic-embed-text",
        "LLM_MODEL": "qwen2.5-coder:3b",
        "TOP_K": "5",
        "OLLAMA_NUM_CTX": "4096",
        "OLLAMA_NUM_PREDICT": "768",
        "OLLAMA_NUM_THREAD": "8",
        "OLLAMA_NUM_BATCH": "256",
        "OLLAMA_TEMPERATURE": "0.2",
        "OLLAMA_REPEAT_PENALTY": "1.15",
        "PROMPT_TEMPLATE": _PROMPT_DEFAULT_ENCODED,
        "FILE_EXTENSIONS": ",".join([
            ".java", ".py", ".js", ".ts", ".go", ".rs",
            ".c", ".cpp", ".h", ".cs", ".rb", ".php",
            ".kt", ".scala", ".swift", ".m", ".sql", ".sh",
        ]),
        "INCLUDE_FILENAMES": "architecture.md",
        "IGNORE_DIRS": "target,.git,node_modules,__pycache__,.venv,dist,build",
        "CHUNK_SIZE": "1500",
        "CHUNK_OVERLAP": "200",
    }

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        for key, value in defaults.items():
            f.write(f"{key}={value}\n")

    _cfg.GIT_REPO_URL = defaults["GIT_REPO_URL"]
    _cfg.GIT_BRANCH = defaults["GIT_BRANCH"]
    _cfg.GIT_AUTO_UPDATE = False
    _cfg.GIT_ACCESS_TOKEN = defaults["GIT_ACCESS_TOKEN"]
    _cfg.GIT_SSH_KEY_PATH = defaults["GIT_SSH_KEY_PATH"]
    _cfg.OLLAMA_URL = defaults["OLLAMA_URL"]
    _cfg.EMBED_MODEL = defaults["EMBED_MODEL"]
    _cfg.LLM_MODEL = defaults["LLM_MODEL"]
    _cfg.TOP_K = 5
    _cfg.OLLAMA_OPTIONS["num_ctx"] = 4096
    _cfg.OLLAMA_OPTIONS["num_predict"] = 768
    _cfg.OLLAMA_OPTIONS["num_thread"] = 8
    _cfg.OLLAMA_OPTIONS["num_batch"] = 256
    _cfg.OLLAMA_OPTIONS["temperature"] = 0.2
    _cfg.OLLAMA_OPTIONS["repeat_penalty"] = 1.15
    _cfg.PROMPT_TEMPLATE = _cfg.PROMPT_DEFAULT
    _cfg.FILE_EXTENSIONS = [x.strip()
                            for x in defaults["FILE_EXTENSIONS"].split(",")]
    _cfg.INCLUDE_FILENAMES = ["architecture.md"]
    _cfg.IGNORE_DIRS = [x.strip() for x in defaults["IGNORE_DIRS"].split(",")]
    _cfg.CHUNK_SIZE = 1500
    _cfg.CHUNK_OVERLAP = 200


def clear_codebase() -> None:
    _CHROMA_SEGMENT_RE = _re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    )
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        client.delete_collection("codebase")
    except Exception:
        pass

    if os.path.exists(CHROMA_PATH):
        for entry in os.scandir(CHROMA_PATH):
            if entry.is_dir() and _CHROMA_SEGMENT_RE.match(entry.name):
                shutil.rmtree(entry.path)

    if os.path.exists(CODE_PATH):
        shutil.rmtree(CODE_PATH)
    os.makedirs(CODE_PATH, exist_ok=True)
    open(os.path.join(CODE_PATH, ".gitkeep"), "w").close()
