"""Permite executar o pacote com ``python -m ninho_mimo_trends``."""

from __future__ import annotations

import sys

from ninho_mimo_trends.cli.parser import main

if __name__ == "__main__":
    sys.exit(main())
