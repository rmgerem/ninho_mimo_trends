# CLI

O ponto de entrada instalado é `ninho-mimo-trends` (via
`[project.scripts]` em [pyproject.toml](../pyproject.toml)). Também é
possível rodar via `python -m ninho_mimo_trends` (usa
`src/ninho_mimo_trends/__main__.py`).

```bash
ninho-mimo-trends --help
ninho-mimo-trends <comando> --help
```

Flag global (antes do subcomando):

| Flag | Descrição |
|---|---|
| `--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}` | Sobrescreve o nível de log configurado via `.env` (`LOG_LEVEL`). |

## `database` — gerenciamento do schema

```bash
ninho-mimo-trends database check
ninho-mimo-trends database upgrade [--revision head]
ninho-mimo-trends database downgrade --revision <rev>
```

- `check`: testa a conectividade com o PostgreSQL configurado.
- `upgrade`: aplica migrações Alembic até a revisão informada (padrão `head`).
- `downgrade`: reverte migrações até a revisão informada (**obrigatória**, ex.: `-1` ou um hash).

## `seed` — dados de referência

```bash
ninho-mimo-trends seed
```

Popula `tb_categories`, `tb_age_ranges` e `tb_sources` a partir de
`configs/categories.json` e `configs/sources.json`. **Idempotente**:
rodar novamente não duplica registros já existentes (usa
`get_or_create` em cada repositório). Imprime quantos registros novos
foram criados em cada execução.

## `collect` — executar uma coleta

```bash
ninho-mimo-trends collect --source mock
ninho-mimo-trends collect --source mock --category criancas-brinquedos --limit 20
ninho-mimo-trends collect --source mock --dry-run
ninho-mimo-trends collect --source mock --execution-id <uuid>
```

| Flag | Obrigatório | Descrição |
|---|---|---|
| `--source` | sim | Código da fonte cadastrada em `tb_sources` (ex.: `mock`). |
| `--category` | não | Filtra a coleta por slug de categoria. |
| `--limit` | não | Limite de itens a coletar. |
| `--dry-run` | não | Executa toda a validação/normalização sem gravar nada no banco (`rollback` ao final). |
| `--execution-id` | não | UUID customizado para identificar a execução em `tb_collection_runs`. |

Saída típica:

```
Itens encontrados: 76 | criados: 19 | atualizados: 57 | ignorados: 0 | erros: 0
```

## `products` — consulta e moderação

### `products list`

```bash
ninho-mimo-trends products list
ninho-mimo-trends products list --category bebes-desenvolvimento --status PENDING
ninho-mimo-trends products list --order-by trend_score --limit 10
```

| Flag | Descrição |
|---|---|
| `--category` | Filtra por slug de categoria. |
| `--age-range` | Filtra por código de faixa etária. |
| `--status {PENDING,APPROVED,REJECTED}` | Filtra por status de moderação. |
| `--source` | Filtra por código de fonte. |
| `--min-opportunity` | Filtra por `opportunity_score` mínimo. |
| `--max-risk` | Filtra por `risk_score` máximo. |
| `--order-by {opportunity_score,trend_score,social_score,risk_score}` | Campo de ordenação (padrão `opportunity_score`). |
| `--limit` | Máximo de produtos (padrão 20). |

### `products show <id>`

```bash
ninho-mimo-trends products show 8
```

Exibe o detalhe completo de um produto: marca, categoria, faixa etária,
todas as fontes/preços, histórico de pontuações e status de publicação.

### `products rank`

```bash
ninho-mimo-trends products rank --category criancas-brinquedos --limit 5
```

Atalho para `products list --order-by opportunity_score`.

### `products approve <id>` / `products reject <id>`

```bash
ninho-mimo-trends products approve 8 --notes "Bom potencial de conteúdo"
ninho-mimo-trends products reject 16 --notes "Risco de segurança alto"
```

Grava/atualiza `tb_publication_status` e sincroniza
`tb_products.moderation_status`. Produtos com risco `HIGH`/`CRITICAL`
**podem** ser aprovados manualmente (não são bloqueados), mas um aviso é
sempre registrado no log — ver [docs/architecture.md](architecture.md).

### `products export`

```bash
ninho-mimo-trends products export --format xlsx
ninho-mimo-trends products export --format csv --output data/exports/ranking.csv
ninho-mimo-trends products export --category bebes-desenvolvimento --min-opportunity 60 --max-risk 40
```

| Flag | Descrição |
|---|---|
| `--format {csv,xlsx}` | Formato de saída (padrão `xlsx`). |
| `--output` | Caminho do arquivo. Se omitido, gera um nome com timestamp em `data/exports/`. |
| `--category` | Filtra por slug de categoria. |
| `--min-opportunity` | `opportunity_score` mínimo. |
| `--max-risk` | `risk_score` máximo. |
| `--limit` | Máximo de linhas (padrão 100). |

Ver detalhes do formato do arquivo gerado em [docs/scoring.md](scoring.md)
e no serviço `business/export_service.py`.

## Exit codes

| Código | Constante | Quando ocorre |
|---|---|---|
| 0 | `SUCCESS` | Execução concluída sem erros. |
| 1 | `UNEXPECTED_ERROR` | Qualquer exceção não mapeada (bug, erro inesperado). |
| 2 | `ARGUMENT_ERROR` | `ProductValidationError` (ex.: produto/argumento inválido, ex.: `products show 9999`). |
| 3 | `CONFIGURATION_ERROR` | Configuração inválida ou ausente. |
| 4 | `DATABASE_ERROR` | Falha de conexão com o PostgreSQL. |
| 5 | `COLLECTION_ERROR` | Falha na coleta (`CollectorError`, ex.: fonte inexistente/desativada). |
| 6 | `EXPORT_ERROR` | Falha na exportação (ex.: formato inválido). |

Exemplos observados durante testes manuais:

```bash
$ ninho-mimo-trends collect --source fonte-inexistente; echo $?
Erro de coleta: Fonte 'fonte-inexistente' nao encontrada.
5

$ ninho-mimo-trends products show 9999; echo $?
Erro: Produto id=9999 nao encontrado.
2
```
