"""Módulo para operações com repositórios Git.

Suporta clonagem e atualização de repositórios via HTTPS (com token de acesso
pessoal) ou SSH (com chave privada), seguido de re-indexação automática.
"""

import os
import shutil
import subprocess
from urllib.parse import urlparse, urlunparse

from minorag.config import (
    CODE_PATH,
    GIT_ACCESS_TOKEN,
    GIT_BRANCH,
    GIT_REPO_URL,
    GIT_SSH_KEY_PATH,
)


def _build_auth_url(repo_url: str, token: str) -> str:
    """Incorpora token de acesso pessoal na URL HTTPS.

    @param repo_url: URL original do repositório.
    @param token: Token de acesso pessoal (PAT).
    @return: URL com credenciais embutidas.
    """
    parsed = urlparse(repo_url)
    netloc = f"oauth2:{token}@{parsed.hostname}"
    if parsed.port:
        netloc += f":{parsed.port}"
    return urlunparse(parsed._replace(netloc=netloc))


def _get_git_env() -> dict[str, str]:
    """Retorna variáveis de ambiente configuradas para autenticação SSH.

    Se GIT_SSH_KEY_PATH estiver definido, configura GIT_SSH_COMMAND com
    a chave privada informada.

    @return: Cópia do ambiente com GIT_SSH_COMMAND configurado, se aplicável.
    """
    env = os.environ.copy()
    ssh_key = GIT_SSH_KEY_PATH.strip()
    if ssh_key:
        ssh_key_path = os.path.expanduser(ssh_key)
        env["GIT_SSH_COMMAND"] = (
            f"ssh -i {ssh_key_path} -o StrictHostKeyChecking=no -o BatchMode=yes"
        )
    return env


def _clean_directories():
    """Limpa a pasta .codebase/ para receber um novo clone."""
    if os.path.exists(CODE_PATH):
        shutil.rmtree(CODE_PATH)
    os.makedirs(CODE_PATH, exist_ok=True)


def clone_repo(
    repo_url: str | None = None,
    branch: str | None = None,
    token: str | None = None,
) -> bool:
    """Clona um repositório git na pasta .codebase.

    Limpa o diretório .codebase/ antes de clonar.
    Suporta autenticação via token (HTTPS) ou chave SSH.

    @param repo_url: URL do repositório. Usa GIT_REPO_URL se não informado.
    @param branch: Branch a clonar. Usa GIT_BRANCH se não informado.
    @param token: Token de acesso para repos privados. Usa GIT_ACCESS_TOKEN se não informado.
    @return: True se a clonagem foi bem-sucedida, False caso contrário.
    """
    url = (repo_url or GIT_REPO_URL).strip()
    ref = (branch or GIT_BRANCH).strip() or "main"
    access_token = (token or GIT_ACCESS_TOKEN).strip()

    if not url:
        print("URL do repositório não configurada.")
        return False

    parsed = urlparse(url)
    is_https = parsed.scheme in ("http", "https")

    if is_https and access_token:
        clone_url = _build_auth_url(url, access_token)
    else:
        clone_url = url

    print("Limpando diretórios...")
    _clean_directories()

    print(f"Clonando repositório ({ref})...")
    env = _get_git_env()

    try:
        result = subprocess.run(
            ["git", "clone", "--branch", ref, "--depth", "1", clone_url, CODE_PATH],
            env=env,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        print("Timeout ao clonar repositório.")
        return False
    except FileNotFoundError:
        print("Git não encontrado no sistema. Instale o git para continuar.")
        return False

    if result.returncode != 0:
        # Oculta a URL com credencial na mensagem de erro
        error_msg = result.stderr.replace(
            clone_url, url) if access_token else result.stderr
        print(f"Erro ao clonar repositório:\n{error_msg.strip()}")
        return False

    # Recria o .gitkeep para preservar a pasta no controle de versão
    open(os.path.join(CODE_PATH, ".gitkeep"), "w").close()

    print("Repositório clonado com sucesso!")
    return True


def update_repo(
    repo_url: str | None = None,
    branch: str | None = None,
    token: str | None = None,
) -> bool:
    """Atualiza a codebase a partir do repositório remoto.

    Realiza um re-clone completo para garantir que a versão mais recente
    do branch seja utilizada.

    @param repo_url: URL do repositório.
    @param branch: Branch a atualizar.
    @param token: Token de acesso.
    @return: True se a atualização foi bem-sucedida, False caso contrário.
    """
    return clone_repo(repo_url, branch, token)


def clone_and_index(
    repo_url: str | None = None,
    branch: str | None = None,
    token: str | None = None,
) -> bool:
    """Clona o repositório e re-indexa o código no ChromaDB.

    @param repo_url: URL do repositório.
    @param branch: Branch a clonar.
    @param token: Token de acesso para repos privados.
    @return: True se clone e indexação foram bem-sucedidos.
    """
    from minorag.indexer import index_code

    if not clone_repo(repo_url, branch, token):
        return False

    print("Re-indexando código...")
    index_code()
    return True


def update_and_index(
    repo_url: str | None = None,
    branch: str | None = None,
    token: str | None = None,
) -> bool:
    """Atualiza o repositório e re-indexa o código no ChromaDB.

    @param repo_url: URL do repositório.
    @param branch: Branch a atualizar.
    @param token: Token de acesso para repos privados.
    @return: True se atualização e indexação foram bem-sucedidas.
    """
    return clone_and_index(repo_url, branch, token)
