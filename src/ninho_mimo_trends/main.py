"""Ponto de entrada da aplicacao (funcao ``main`` reutilizada pela CLI)."""

from __future__ import annotations

import sys

from ninho_mimo_trends.cli.parser import main

if __name__ == "__main__":
    sys.exit(main())
