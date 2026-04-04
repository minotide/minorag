"""Módulo de comunicação com o servidor Ollama.

Responsável por gerar embeddings e respostas de texto usando
os modelos configurados via API REST do Ollama.
"""

import json

import requests

from minorag.config import EMBED_MODEL, LLM_MODEL, OLLAMA_URL

_OFFLINE_MSG = "\nOllama não está respondendo. Inicie-o com:\n\n    ollama serve &\n"


def embed(text):
    """Gera o embedding vetorial de um texto usando o modelo de embeddings.

    @param text: Texto a ser convertido em vetor.
    @return: Lista de floats representando o embedding.
    @raises SystemExit: Se o Ollama não estiver acessível.
    """
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
            timeout=120,
        )
        response.raise_for_status()
        return response.json()["embedding"]
    except requests.exceptions.ConnectionError:
        print(_OFFLINE_MSG)
        raise SystemExit(1)


def generate(prompt):
    """
    Gera uma resposta completa para o prompt fornecido (sem streaming).

    @param prompt: Texto de entrada enviado ao modelo LLM.
    @return: String com a resposta completa gerada pelo modelo.
    @raises SystemExit: Se o Ollama não estiver acessível.
    """
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": LLM_MODEL, "prompt": prompt, "stream": False},
            timeout=300,
        )
        response.raise_for_status()
        return response.json()["response"]
    except requests.exceptions.ConnectionError:
        print(_OFFLINE_MSG)
        raise SystemExit(1)


def generate_stream(prompt):
    """
    Gera uma resposta em streaming e imprime os tokens diretamente no stdout.

    @param prompt: Texto de entrada enviado ao modelo LLM.
    @raises SystemExit: Se o Ollama não estiver acessível.
    """
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": LLM_MODEL, "prompt": prompt, "stream": True},
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
    except requests.exceptions.ConnectionError:
        print(_OFFLINE_MSG)
        raise SystemExit(1)


def generate_stream_iter(prompt):
    """
    Gera uma resposta em streaming e retorna os tokens como um gerador.

    @param prompt: Texto de entrada enviado ao modelo LLM.
    @return: Gerador de strings, cada uma contendo um token da resposta.
    """
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": LLM_MODEL, "prompt": prompt, "stream": True},
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
    except requests.exceptions.ConnectionError:
        yield _OFFLINE_MSG
