# Roadmap

Este documento descreve o que existe no MVP atual e sugestões de
evolução em fases, para orientar o planejamento de próximas versões.
Nenhum item abaixo está implementado — são recomendações.

## Estado atual (MVP, Etapas 1–10 + evoluções pós-MVP)

- Coleta simulada (`MockCollector`) e coleta real via API oficial de afiliados
  (`ShopeeAffiliateCollector`); estrutura pronta, mas desabilitada, para uma
  fonte pública genérica (`PublicSourceCollector`);
- Normalização e deduplicação de produtos (hash canônico + similaridade
  textual via `rapidfuzz`);
- Histórico de preços/métricas por fonte, incluindo taxa de comissão
  (`commission_rate`) quando a fonte fornece;
- Pontuações de tendência, potencial social, risco e oportunidade
  (incluindo componente de comissão), configuráveis via JSON;
- Log de indicações da automação (`tb_product_indications`) quando o
  `opportunity_score` atinge o limiar configurado, consumido por um
  dashboard Grafana (ver [docs/grafana.md](grafana.md));
- Agendador automático de coletas (`ninho-mimo-trends scheduler start`/
  `run-once`), rodando por fonte/categoria conforme
  `collection_interval_minutes`;
- Observabilidade do scheduler via Prometheus Pushgateway + dashboard
  Grafana dedicado (`nmt_observability.json`);
- Deploy via Docker Compose (Postgres, migrations, seed, scheduler,
  Pushgateway, Prometheus, Grafana) — ver `docker-compose.yml` e
  `Dockerfile`;
- Moderação manual (aprovação/rejeição) via CLI;
- Exportação para CSV/XLSX;
- CLI completa via `argparse`;
- Suíte de testes automatizados (unitários + integração).

Fora de escopo, propositalmente: framework web, autenticação de usuários,
automação de postagem em redes sociais (a divulgação continua manual),
Selenium/Playwright, APIs pagas sem uma conta/credencial legítima do
operador.

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

## Fase 4 — Notificações ✅ agendamento já implementado

~~Automatizar a execução periódica de `collect`~~ — feito via
`ninho-mimo-trends scheduler start` (ver [docs/grafana.md](grafana.md) e
`docker-compose.yml`). Falta apenas a parte de **notificações**
(e-mail/Slack/Telegram) quando produtos de alta oportunidade forem
indicados — hoje isso só é visível olhando o dashboard Grafana ou a
tabela `tb_product_indications` manualmente.

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

## Fase 8 — Observabilidade ✅ parcialmente implementado

~~Métricas estruturadas sobre execuções de coleta~~ — feito via
`MetricsPusher` (Prometheus Pushgateway) + dashboard
`nmt_observability.json`. Ainda falta: alertas automáticos quando uma
fonte historicamente confiável começa a falhar (hoje é preciso olhar o
dashboard ativamente, não há alerta push).
