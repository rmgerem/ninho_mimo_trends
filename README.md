# Ninho & Mimo Trends

> Carinho em cada fase.

Plataforma de inteligencia de produtos voltada para gestantes, maes no
pos-parto, bebes e criancas de ate 10 anos. O sistema coleta, organiza,
compara e classifica produtos que estao ganhando relevancia na internet,
gerando um ranking de oportunidades para orientar a producao de conteudo
em redes sociais (divulgacao manual, sem automacao de postagem neste MVP).

> **Status:** MVP completo (Etapas 1-10 concluidas). Consulte
> [docs/roadmap.md](docs/roadmap.md) para as proximas evolucoes sugeridas.

## Instalacao e configuracao

Requisitos: Python 3.12+ e um PostgreSQL acessivel.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (PowerShell)
# source .venv/bin/activate     # Linux/Mac

pip install -e ".[dev]"

copy .env.example .env          # Windows; use `cp` no Linux/Mac
# edite .env com as credenciais do seu PostgreSQL
```

Crie os bancos de dados (a aplicacao nao cria o banco em si, apenas as
tabelas):

```sql
CREATE DATABASE ninho_mimo_trends;        -- uso normal
CREATE DATABASE ninho_mimo_trends_test;   -- necessario apenas para rodar os testes
```

Aplique as migracoes e popule os dados de referencia:

```bash
alembic upgrade head
python -m ninho_mimo_trends database check
python -m ninho_mimo_trends seed
```

## Execucao

```bash
python -m ninho_mimo_trends collect --source mock
python -m ninho_mimo_trends products rank --limit 10
python -m ninho_mimo_trends products export --format xlsx
```

Referencia completa de comandos em [docs/cli.md](docs/cli.md).

## Testes

```bash
pytest
```

A suite usa o banco `ninho_mimo_trends_test` dedicado (nunca aponte para
um banco de desenvolvimento/producao) e trunca as tabelas entre os testes.

## Escopo deste MVP

- Cadastro de fontes, categorias e faixas etarias;
- Coleta simulada (MockCollector) e estrutura para um coletor publico real;
- Normalizacao e deduplicacao de produtos;
- Historico de precos e metricas;
- Calculo de pontuacoes de tendencia, potencial social e risco;
- Ranking de oportunidades;
- Aprovacao/rejeicao manual de produtos;
- Exportacao para CSV/XLSX;
- CLI via `argparse`;
- Sem frameworks web, sem automacao de postagem, sem scraping agressivo.

Documentacao detalhada em [docs/](docs): [arquitetura](docs/architecture.md),
[banco de dados](docs/database.md), [coletores](docs/collectors.md),
[CLI](docs/cli.md), [pontuacao](docs/scoring.md) e [roadmap](docs/roadmap.md).