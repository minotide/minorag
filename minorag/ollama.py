"""Módulo de comunicação com o servidor Ollama.

Responsável por gerar embeddings e respostas de texto usando
os modelos configurados via API REST do Ollama.
"""

import json
import subprocess
import time
from collections.abc import Iterator

import requests

from minorag import config as _cfg


def _try_start_ollama() -> bool:
    """Tenta iniciar o servidor Ollama automaticamente via subprocess."""
    print("\nOllama não está respondendo. Tentando iniciar automaticamente...")
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        print("Ollama não encontrado no sistema. Instale em: https://ollama.ai")
        return False

    print("Aguardando Ollama iniciar", end="", flush=True)
    for _ in range(15):
        time.sleep(2)
        print(".", end="", flush=True)
        try:
            requests.get(_cfg.OLLAMA_URL, timeout=3)
            print(" pronto!")
            return True
        except requests.exceptions.ConnectionError:
            continue

    print("\nNão foi possível iniciar o Ollama automaticamente.")
    print("Inicie manualmente com: ollama serve &")
    return False


def ensure_ollama_running() -> bool:
    """Verifica se Ollama está rodando e tenta iniciar automaticamente se necessário."""
    try:
        requests.get(_cfg.OLLAMA_URL, timeout=5)
        return True
    except requests.exceptions.ConnectionError:
        return _try_start_ollama()


def embed(text: str) -> list[float]:
    """
    Gera o embedding vetorial de um texto usando o modelo de embeddings.

    @param text: Texto a ser convertido em vetor.
    @return: Lista de floats representando o embedding.
    @raises SystemExit: Se o Ollama não estiver acessível.
    """
    def _do_request():
        response = requests.post(
            f"{_cfg.OLLAMA_URL}/api/embeddings",
            json={"model": _cfg.EMBED_MODEL, "prompt": text},
            timeout=120,
        )
        response.raise_for_status()
        return response.json()["embedding"]

    try:
        return _do_request()
    except requests.exceptions.ConnectionError:
        if _try_start_ollama():
            return _do_request()
        raise SystemExit(1)


def generate(prompt: str) -> str:
    """
    Gera uma resposta completa para o prompt fornecido (sem streaming).

    @param prompt: Texto de entrada enviado ao modelo LLM.
    @return: String com a resposta completa gerada pelo modelo.
    @raises SystemExit: Se o Ollama não estiver acessível.
    """
    def _do_request():
        response = requests.post(
            f"{_cfg.OLLAMA_URL}/api/generate",
            json={
                "model": _cfg.LLM_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": _cfg.OLLAMA_OPTIONS,
            },
            timeout=300,
        )
        response.raise_for_status()
        return response.json()["response"]

    try:
        return _do_request()
    except requests.exceptions.ConnectionError:
        if _try_start_ollama():
            return _do_request()
        raise SystemExit(1)


def generate_stream(prompt: str) -> None:
    """
    Gera uma resposta em streaming e imprime os tokens diretamente no stdout.

    @param prompt: Texto de entrada enviado ao modelo LLM.
    @raises SystemExit: Se o Ollama não estiver acessível.
    """
    def _do_stream():
        response = requests.post(
            f"{_cfg.OLLAMA_URL}/api/generate",
            json={
                "model": _cfg.LLM_MODEL,
                "prompt": prompt,
                "stream": True,
                "options": _cfg.OLLAMA_OPTIONS,
            },
            timeout=300,
            stream=True,
        )
        response.raise_for_status()
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                token = data.get("response", "")
                if token:
                    print(token, end="", flush=True)
                if data.get("done"):
                    break

    try:
        _do_stream()
    except requests.exceptions.ConnectionError:
        if _try_start_ollama():
            _do_stream()
        else:
            raise SystemExit(1)


def generate_stream_iter(prompt: str) -> Iterator[str]:
    """
    Gera uma resposta em streaming e retorna os tokens como um gerador.

    @param prompt: Texto de entrada enviado ao modelo LLM.
    @return: Gerador de strings, cada uma contendo um token da resposta.
    """
    if not ensure_ollama_running():
        raise SystemExit(1)

    response = requests.post(
        f"{_cfg.OLLAMA_URL}/api/generate",
        json={
            "model": _cfg.LLM_MODEL,
            "prompt": prompt,
            "stream": True,
            "options": _cfg.OLLAMA_OPTIONS,
        },
        timeout=300,
        stream=True,
    )
    response.raise_for_status()
    for line in response.iter_lines():
        if line:
            data = json.loads(line)
            token = data.get("response", "")
            if token:
                yield token
            if data.get("done"):
                break
