"""Utilitario para carregar arquivos JSON de configuracao nao sensivel."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from ninho_mimo_trends.exceptions import ConfigurationError

_PROJECT_MARKER_FILES = ("pyproject.toml", ".git")


@lru_cache(maxsize=1)
def find_project_root() -> Path:
    """Localiza a raiz do projeto subindo a partir deste arquivo.

    A raiz e identificada pela presenca de ``pyproject.toml`` ou ``.git``.
    Caso nenhum marcador seja encontrado, o diretorio de trabalho atual e
    utilizado como fallback.
    """
    current = Path(__file__).resolve()
    for parent in [current, *current.parents]:
        if any((parent / marker).exists() for marker in _PROJECT_MARKER_FILES):
            return parent
    return Path.cwd()


def get_configs_dir() -> Path:
    """Retorna o diretorio ``configs/`` na raiz do projeto."""
    return find_project_root() / "configs"


def load_json_config(filename: str) -> dict:
    """Carrega e retorna o conteudo de um arquivo JSON dentro de ``configs/``.

    Args:
        filename: nome do arquivo, por exemplo ``"application.json"``.

    Raises:
        ConfigurationError: quando o arquivo nao existe ou contem JSON invalido.
    """
    config_path = get_configs_dir() / filename
    if not config_path.is_file():
        raise ConfigurationError(f"Arquivo de configuracao nao encontrado: {config_path}")
    try:
        with config_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise ConfigurationError(f"JSON invalido em {config_path}: {exc}") from exc
