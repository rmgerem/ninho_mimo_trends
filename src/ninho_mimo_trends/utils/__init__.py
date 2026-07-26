"""Pacote de utilitarios genericos (datas, dinheiro, hashing, texto, retry)."""

from ninho_mimo_trends.utils.dates import now_in_default_timezone, now_utc
from ninho_mimo_trends.utils.hashing import compute_canonical_hash, compute_url_hash, sha256_hex
from ninho_mimo_trends.utils.money import format_brl, to_decimal
from ninho_mimo_trends.utils.retry import retry_with_backoff
from ninho_mimo_trends.utils.text import normalize_for_comparison, normalize_for_storage, normalize_url

__all__ = [
    "now_utc",
    "now_in_default_timezone",
    "compute_canonical_hash",
    "compute_url_hash",
    "sha256_hex",
    "format_brl",
    "to_decimal",
    "retry_with_backoff",
    "normalize_for_comparison",
    "normalize_for_storage",
    "normalize_url",
]
