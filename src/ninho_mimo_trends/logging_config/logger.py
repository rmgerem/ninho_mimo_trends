"""Configuracao de logging estruturado (console + arquivo com rotacao)."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from ninho_mimo_trends.configuration.settings import find_project_root, get_settings

LOG_FILENAME = "ninho_mimo_trends.log"
_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
_BACKUP_COUNT = 5

_LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s | "
    "execution_id=%(execution_id)s | source_code=%(source_code)s | "
    "product_id=%(product_id)s | %(message)s"
)

_DEFAULT_CONTEXT = {
    "execution_id": "-",
    "source_code": "-",
    "product_id": "-",
}

_configured = False


class _ContextFilter(logging.Filter):
    """Garante valores padrao para os campos de contexto do log."""

    def filter(self, record: logging.LogRecord) -> bool:
        for key, default in _DEFAULT_CONTEXT.items():
            if not hasattr(record, key):
                setattr(record, key, default)
        return True


def configure_logging(logs_dir: Path | None = None) -> None:
    """Configura o logger raiz da aplicacao (console + arquivo rotativo).

    Idempotente: chamadas subsequentes nao duplicam handlers.
    """
    global _configured
    if _configured:
        return

    settings = get_settings()
    resolved_logs_dir = logs_dir or (find_project_root() / "logs")
    resolved_logs_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(_LOG_FORMAT)
    context_filter = _ContextFilter()

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(context_filter)

    file_handler = RotatingFileHandler(
        resolved_logs_dir / LOG_FILENAME,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(context_filter)

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level.upper())
    root_logger.handlers = [console_handler, file_handler]

    _configured = True


def get_logger(name: str, **context: Any) -> logging.LoggerAdapter:
    """Retorna um logger com contexto estruturado (execution_id, source_code, product_id).

    Args:
        name: nome do logger, tipicamente ``__name__`` do modulo chamador.
        **context: campos extras de contexto (``execution_id``, ``source_code``,
            ``product_id``) que serao anexados a cada mensagem de log.
    """
    if not _configured:
        configure_logging()
    merged_context = {**_DEFAULT_CONTEXT, **context}
    return logging.LoggerAdapter(logging.getLogger(name), merged_context)
