"""Utilitario de retentativas controladas (retry com backoff)."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

_P = ParamSpec("_P")
_T = TypeVar("_T")

_logger = logging.getLogger(__name__)


def retry_with_backoff(
    *,
    max_attempts: int = 3,
    backoff_seconds: float = 2.0,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
    non_retryable_exceptions: tuple[type[Exception], ...] = (),
) -> Callable[[Callable[_P, _T]], Callable[_P, _T]]:
    """Decorator que reexecuta a funcao decorada em caso de erro transitorio.

    Args:
        max_attempts: numero maximo de tentativas (>= 1).
        backoff_seconds: tempo base, em segundos, multiplicado a cada nova
            tentativa (backoff exponencial simples: ``backoff * tentativa``).
        retryable_exceptions: tupla de excecoes consideradas transitorias
            (serao repetidas).
        non_retryable_exceptions: tupla de excecoes que NUNCA devem ser
            repetidas (por exemplo, erros de validacao), mesmo que sejam
            subclasses de ``retryable_exceptions``.
    """

    def decorator(func: Callable[_P, _T]) -> Callable[_P, _T]:
        @wraps(func)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T:
            last_exception: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except non_retryable_exceptions:
                    raise
                except retryable_exceptions as exc:
                    last_exception = exc
                    _logger.warning(
                        "Tentativa %s/%s falhou para %s: %s",
                        attempt,
                        max_attempts,
                        func.__name__,
                        exc,
                    )
                    if attempt < max_attempts:
                        time.sleep(backoff_seconds * attempt)
            assert last_exception is not None  # noqa: S101 - invariante interna
            raise last_exception

        return wrapper

    return decorator
