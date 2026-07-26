# Sistema de Pontuação

Todas as fórmulas de pontuação são funções puras (sem I/O) em
`src/ninho_mimo_trends/scoring/`, parametrizadas por
[configs/scoring_rules.json](../configs/scoring_rules.json) — os pesos e
limiares abaixo podem ser ajustados nesse arquivo sem alterar código.
`ScoringService.calculate_and_persist_score()` orquestra o cálculo das
quatro pontuações e grava uma nova linha em `tb_product_scores` a cada
recálculo (histórico de pontuações é sempre preservado).

Todas as pontuações são valores em `Decimal`, na escala **0–100**
(exceto quando não há dados suficientes, caso em que o valor é `None`).

## 1. Trend Score (`trend_score.py`)

Mede o quão bem um produto está performando ao longo do tempo, usando o
histórico de coletas (`tb_product_history`) de todas as suas fontes.

- **Requer no mínimo `minimum_history_points` (3) pontos de histórico.**
  Com menos que isso, `trend_score = None` e
  `trend_status = SEM_HISTORICO_SUFICIENTE` — o sistema nunca afirma uma
  tendência com base em uma única coleta.
- Componentes ponderados (pesos em `trend_score.weights`):

  | Componente | Peso |
  |---|---|
  | Crescimento de vendas | 0.30 |
  | Crescimento de avaliações | 0.20 |
  | Melhora de ranking | 0.20 |
  | Persistência da tendência | 0.15 |
  | Diversidade de fontes | 0.10 |
  | Recência da última coleta | 0.05 |

- **Amortecimento de amostra pequena** (`small_sample_dampening`):
  crescimentos percentuais calculados sobre valores absolutos pequenos
  (ex.: 1 → 3 vendas = +200%) são amortecidos para não gerarem pontuações
  artificialmente altas. Configurado por `minimum_absolute_increase` (5):
  um produto que passa de 1 para 3 vendas é penalizado em relação a um
  que passa de 500 para 800 vendas, mesmo que o segundo tenha um
  crescimento percentual menor. Validado numericamente em
  `tests/unit/test_scoring.py::TestTrendScore::test_small_sample_growth_is_dampened_below_large_absolute_growth`.
- **Classificação de status** (`trend_score.status_thresholds`), aplicada
  sobre um score assinado de -100 a 100 antes de normalizar para 0–100:

  | Status | Faixa |
  |---|---|
  | `CRESCIMENTO_FORTE` | ≥ 70 |
  | `CRESCIMENTO_MODERADO` | ≥ 40 |
  | `ESTAVEL` | entre -15 e 15 |
  | `QUEDA_MODERADA` | ≤ -40 |
  | `QUEDA_FORTE` | ≤ -70 |
  | `SEM_HISTORICO_SUFICIENTE` | histórico insuficiente |

## 2. Social Score (`social_score.py`)

Mede o "potencial de conteúdo" de um produto para redes sociais (quão
fácil é fazer um vídeo/post chamativo sobre ele), a partir de 8 fatores
ponderados (visual, facilidade de demonstração em vídeo, utilidade
explicável, potencial de antes/depois, conteúdo educativo, apelo
emocional, clareza do benefício, encaixe em vídeo curto — pesos em
`social_score.weights`, somando 1.0).

- **Base:** 50.0 pontos.
- **Bônus de categoria** (`social_score.category_bonus`):

  | Categoria | Bônus |
  |---|---|
  | `criancas-brinquedos` | +15 |
  | `criancas-educacao` | +15 |
  | `bebes-desenvolvimento` | +12 |
  | `gestantes-conforto` | +8 |

- **Bônus por palavra-chave** (`social_score.keyword_bonus`, aplicado ao
  nome + descrição normalizados):

  | Palavra-chave | Bônus |
  |---|---|
  | `montessori` | +10 |
  | `antes e depois` | +10 |
  | `sensorial` | +8 |
  | `educativo` | +8 |
  | `organizador` | +6 |
  | `portatil` | +4 |

- Resultado sempre limitado (`clip`) entre 0 e 100.

## 3. Risk Score (`risk_score.py`)

Mede o risco de segurança/regulatório de um produto, para evitar
recomendar itens problemáticos (ex.: risco de engasgo, alegações
médicas). **Quanto maior, mais arriscado** (o oposto de "bom").

- **Componente de palavra-chave** (`risk_score.keyword_risk`): usa o
  **maior** valor entre as palavras-chave encontradas no nome+descrição,
  mais +5 por cada correspondência adicional. Exemplos de valores:

  | Palavra-chave | Risco |
  |---|---|
  | `medicamento` | 90 |
  | `ingerivel` | 65 |
  | `suplemento` | 70 |
  | `peca pequena` / `pecas pequenas` | 60 |
  | `cadeirinha` / `bebe conforto` | 60 |
  | `berco` | 55 |
  | `vitamina` / `recem-nascido` | 55 |
  | `mordedor` / `cosmetico(s)` | 45 / 45 |
  | `sono` | 50 |
  | `eletrico` | 40 |
  | `mamadeira` | 35 |
  | `eletronico` | 30 |

- **Componente de categoria** (`risk_score.category_risk`, com peso 0.5):
  `bebes-sono` (55), `bebes-seguranca` (50), `bebes-alimentacao` (35),
  `criancas-tecnologia` (30).
- **Penalidade por faixa etária ausente**
  (`risk_score.missing_age_range_penalty`, +20): um produto sem faixa
  etária informada é considerado mais arriscado, pois não é possível
  confirmar a adequação etária.
- Resultado sempre limitado entre 0 e 100. Classificado em `RiskLevel`
  via `risk_score.thresholds`:

  | Nível | Faixa |
  |---|---|
  | `LOW` | < 30 |
  | `MEDIUM` | 30–54 |
  | `HIGH` | 55–74 |
  | `CRITICAL` | ≥ 75 |

  A função `classify_risk_level(score, thresholds)` é pública e
  reutilizada por `moderation_service.py` (aviso ao aprovar produto de
  risco alto) e `export_service.py` (coluna "Risco" no ranking).

## 4. Opportunity Score (`opportunity_score.py`)

Combina os três scores anteriores com dados agregados de todas as fontes
de um produto, para gerar o **ranking final de oportunidades**.

- Componentes ponderados (`opportunity_score.weights`):

  | Componente | Peso |
  |---|---|
  | Trend Score | 0.35 |
  | Social Score | 0.25 |
  | Qualidade das avaliações (nota × volume) | 0.15 |
  | Diversidade de fontes | 0.10 |
  | Encaixe na faixa de preço ideal | 0.10 |
  | Disponibilidade | 0.05 |

- Quando não há `trend_score` calculado (histórico insuficiente), usa-se
  um valor neutro no lugar, em vez de zerar o componente.
- **Faixa de preço ideal** (`opportunity_score.price_range_fit`):
  R$ 25,00 a R$ 250,00 — produtos com preço dentro dessa faixa recebem
  pontuação máxima nesse componente.
- **Penalidade de risco** (`opportunity_score.risk_penalty`), subtraída
  do score bruto após a soma ponderada:

  | Nível de risco | Penalidade |
  |---|---|
  | `low` | 0 |
  | `medium` | -10 |
  | `high` | -35 |
  | `critical` | -70 |

- Resultado final sempre limitado entre 0 e 100.

## Auditoria dos cálculos

Cada linha de `tb_product_scores` grava, na coluna JSONB
`calculation_details`, o detalhamento de todos os componentes usados no
cálculo (ex.: quais palavras-chave casaram, valor de cada componente
antes da ponderação) — útil para depurar por que um produto recebeu
determinada pontuação, sem precisar recalcular manualmente.

## Testes

Todas as fórmulas têm testes unitários determinísticos em
[tests/unit/test_scoring.py](../tests/unit/test_scoring.py), usando os
valores reais de `configs/scoring_rules.json` (carregados via
`load_json_config`, nunca hardcoded no teste) para evitar que os
asserts fiquem dessincronizados da configuração.
