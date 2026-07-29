# ============================================================
# Dockerfile — Ninho & Mimo Trends
# Build: docker build -t ninho-mimo-trends .
# ============================================================

FROM python:3.12-slim AS base

# Metadados
LABEL maintainer="Ninho & Mimo Trends"
LABEL description="Plataforma de inteligencia de produtos para gestantes, maes, bebes e criancas."

# Evita arquivos .pyc e garante saida de log em tempo real
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# ----------------------------------------------------------
# Instala dependencias de sistema (psycopg2 precisa de libpq)
# ----------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ----------------------------------------------------------
# Instala dependencias Python
# ----------------------------------------------------------
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ----------------------------------------------------------
# Copia o codigo-fonte
# ----------------------------------------------------------
COPY src/ ./src/
COPY configs/ ./configs/
COPY data/fixtures/ ./data/fixtures/
COPY migrations/ ./migrations/
COPY alembic.ini ./
COPY pyproject.toml ./

# Instala o pacote em modo editavel para que o CLI funcione
RUN pip install --no-cache-dir -e .

# ----------------------------------------------------------
# Usuario nao-root (boas praticas de seguranca)
# ----------------------------------------------------------
RUN useradd --create-home --shell /bin/bash appuser
RUN chown -R appuser:appuser /app

USER appuser

# ----------------------------------------------------------
# Entrypoint padrao: scheduler em modo continuo
# Sobrescreva com `docker run ... ninho-mimo-trends <outro-comando>`
# ----------------------------------------------------------
ENTRYPOINT ["ninho-mimo-trends"]
CMD ["scheduler", "start"]
