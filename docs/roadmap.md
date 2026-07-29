# Roadmap

Este documento descreve o que existe no MVP atual e sugestões de
evolução em fases, para orientar o planejamento de próximas versões.
Nenhum item abaixo está implementado — são recomendações.

## Estado atual (MVP, Etapas 1–10)

- Coleta simulada (`MockCollector`) + estrutura pronta, mas desabilitada,
  para um coletor HTTP real (`PublicSourceCollector`);
- Normalização e deduplicação de produtos (hash canônico + similaridade
  textual via `rapidfuzz`);
- Histórico de preços/métricas por fonte;
- Pontuações de tendência, potencial social, risco e oportunidade,
  configuráveis via JSON;
- Moderação manual (aprovação/rejeição) via CLI;
- Exportação para CSV/XLSX;
- CLI completa via `argparse`;
- Suíte de testes automatizados (unitários + integração) com cobertura
  ≥ 80%.

Fora de escopo deste MVP, propositalmente: framework web, autenticação,
automação de postagem em redes sociais, Docker/Redis/Celery,
Selenium/Playwright, APIs pagas.

## Fase 1 — Fonte pública real

Identificar e habilitar uma fonte de dados pública, aberta e com termos
de uso que permitam coleta automatizada, adequada ao nicho do produto.
Conectar via `PublicSourceCollector` (ver [docs/collectors.md](collectors.md)).

## Fase 2 — Revisão de deduplicação (`POSSIBLE_MATCH`)

Hoje, matches "possíveis" (similaridade alta mas não exata) apenas geram
um log de aviso. Uma evolução natural é criar uma tabela
`tb_product_match_candidates` para registrar esses casos e uma
interface (ainda que via CLI) para um humano confirmar ou descartar o
match manualmente, em vez de depender de grep em logs.

## Fase 3 — Conectar `safety_service` ao pipeline de coleta

`generate_safety_alerts()` já existe e é testado isoladamente, mas não é
chamado durante a coleta nem persistido. Definir onde armazenar esses
alertas (nova tabela `tb_product_safety_alerts` ou coluna JSONB em
`tb_products`) e exibi-los em `products show`/`products export`.

## Fase 4 — Notificações e agendamento

Automatizar a execução periódica de `collect` (ex.: via `cron` ou um
agendador simples) e notificar (e-mail/Slack/Telegram) quando produtos
de alta oportunidade forem encontrados, sem introduzir um serviço web.

## Fase 5 — Interface web read-only

Uma interface web simples (somente leitura, sem framework pesado) para
visualizar o ranking e o histórico de um produto, como alternativa à
CLI/planilha exportada — mantendo toda a lógica de negócio em
`business/` reutilizável por ambas as interfaces.

Já existe um protótipo estático institucional em
[docs/ninho_mimo_site/](ninho_mimo_site/) (HTML/CSS/JS puro, sem
build/backend) com a identidade visual da marca aplicada. Ele hoje é
independente da plataforma Python — a integração real (catálogo vindo do
PostgreSQL via API, links de afiliado reais, etc.) é o objetivo desta
fase, conforme descrito no [README do site](ninho_mimo_site/README.md).

## Fase 6 — Múltiplas fontes simultâneas

Expandir `CollectorRegistry` para orquestrar múltiplas fontes reais em
paralelo (ex.: `asyncio`/threads controladas), com limites de
concorrência por fonte respeitando o `collection_interval_minutes`
já existente em `tb_sources`.

## Fase 7 — Enriquecimento de conteúdo

Sugestões automáticas de legendas/roteiros de vídeo curto a partir dos
campos de `social_score.details` (ex.: quais fatores pesaram mais),
para acelerar a produção de conteúdo pelas pessoas que usam o ranking.

## Fase 8 — Observabilidade

Métricas estruturadas sobre execuções de coleta (duração, taxa de erro
por fonte) e alertas quando uma fonte historicamente confiável começa a
falhar — construído sobre o `logging_config/` e `tb_collection_runs`
já existentes, sem necessidade de infraestrutura nova.
