.PHONY: install test coverage lint format typecheck check migrate seed run clean

PYTHON ?= python3
PIP ?= pip

install:
	$(PIP) install -e ".[dev]"

test:
	pytest

coverage:
	pytest --cov=src --cov-report=term-missing

lint:
	ruff check .

format:
	black .

typecheck:
	mypy src

check: lint
	black --check .
	mypy src
	pytest

migrate:
	alembic upgrade head

seed:
	$(PYTHON) -m ninho_mimo_trends seed

run:
	$(PYTHON) -m ninho_mimo_trends

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov build dist *.egg-info
