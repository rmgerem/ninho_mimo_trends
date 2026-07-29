# Dashboard Grafana — Indicações da Automação

Este projeto inclui um dashboard Grafana pronto para uso, que consome a
tabela `tb_product_indications` (ver [docs/database.md](database.md) e
[docs/scoring.md](scoring.md#indicações-da-automação)) para responder à
pergunta: **quais produtos a automação indicou como oportunidade, e
quando?**

Os artefatos ficam em `grafana/provisioning/`:

```
grafana/provisioning/
  datasources/postgres.yml               # config do data source PostgreSQL
  dashboards/dashboards.yml              # provider de provisionamento
  dashboards/ninho_mimo_trends_indicacoes.json   # o dashboard em si
```

Grafana não é uma dependência da aplicação (é uma ferramenta externa,
opcional) — nada aqui é executado pelo `ninho_mimo_trends`. O dashboard
lê diretamente do PostgreSQL via SQL.

## Design do dashboard

Estrutura pensada seguindo as boas práticas oficiais do Grafana
([Best practices for creating dashboards](https://grafana.com/docs/grafana/latest/best-practices/best-practices-for-creating-dashboards/)):
história clara (uma pergunta por dashboard), progressão do geral para o
específico, uso de variável de template para evitar duplicar dashboards
por categoria, cores com significado (verde = bom/baixo risco, vermelho
= risco alto) e documentação embutida (painel de texto no topo +
descrição em cada painel, visível ao passar o mouse no ícone "i").

| Linha | Painéis | Pergunta que responde |
|---|---|---|
| 1 | Texto explicativo | O que é este dashboard e como usá-lo |
| 2 | 4 KPIs (stat): indicações no período, produtos únicos, opportunity score médio, indicações de risco alto/crítico | Visão geral rápida |
| 3 | Série temporal: indicações por dia | "Baseado nas datas" — quando a automação indicou produtos |
| 4 | Gráfico de barras (por categoria) + pizza (por nível de risco) | Onde estão concentradas as indicações |
| 5 | Tabela detalhada (produto, categoria, scores, status, data) | Quais produtos, especificamente |

Variável de template **Categoria** (`$category`, multi-seleção com opção
"All") e o seletor de período (canto superior direito) filtram todos os
painéis simultaneamente. Refresh automático configurado para 5 minutos
(os dados só mudam a cada execução de `collect`, não em tempo real —
evita carga desnecessária no banco, conforme recomendado pela
documentação do Grafana).

## Como usar — Opção A: Grafana OSS local (Windows)

1. Baixe e instale o Grafana OSS (gratuito) em
   [grafana.com/grafana/download](https://grafana.com/grafana/download?platform=windows)
   ou via `choco install grafana` (Chocolatey), e inicie o serviço.
   Por padrão fica disponível em `http://localhost:3000` (login inicial
   `admin`/`admin`).
2. **Data source**: em *Connections > Data sources > Add data source >
   PostgreSQL*, configure:
   - Host: `localhost:5432`
   - Database: `ninho_mimo_trends`
   - User: `postgres` (ou o usuário configurado no seu `.env`)
   - Password: a senha do seu PostgreSQL
   - TLS/SSL Mode: `disable` (ambiente local)
   - Version: 16 (ou a versão do seu PostgreSQL)

   Alternativamente, use o provisionamento automático: copie
   `grafana/provisioning/datasources/postgres.yml` para o diretório de
   provisionamento do seu Grafana (`<instalação>/conf/provisioning/datasources/`)
   e defina a variável de ambiente `GF_NMT_DB_PASSWORD` antes de iniciar
   o serviço do Grafana.
3. **Importar o dashboard**: em *Dashboards > New > Import*, envie o
   arquivo `grafana/provisioning/dashboards/ninho_mimo_trends_indicacoes.json`.
   Quando solicitado, selecione o data source PostgreSQL criado no passo
   anterior para a variável `DS_POSTGRESQL`.
4. Rode `ninho-mimo-trends collect --source ...` normalmente — cada
   execução que gerar `opportunity_score` acima do limiar configurado
   alimenta `tb_product_indications` automaticamente, e o dashboard
   reflete os novos dados no próximo refresh.

## Como usar — Opção B: Grafana Cloud (online, conta gratuita)

A Grafana Labs oferece um plano **"Grafana Visualization" sempre gratuito**
(sem cartão de crédito, limitado a 3 usuários ativos/mês — mais que
suficiente para uso individual). Cadastro em
[grafana.com/auth/sign-up](https://grafana.com/auth/sign-up/create-user).

**Atenção — nunca exponha o PostgreSQL diretamente à internet** (abrir a
porta 5432 no roteador/firewall) só para o Grafana Cloud conseguir
acessá-lo. Isso exporia o banco (hoje com credenciais padrão
`postgres`/`postgres`) a qualquer atacante na internet. O caminho seguro
e oficial da própria Grafana Labs para isso é o **Private Data Source
Connect (PDC)**: um agente leve que você roda localmente e que abre um
túnel SSH criptografado **de saída** até o Grafana Cloud — nenhuma porta
precisa ser aberta no seu roteador/firewall, e o PostgreSQL é um dos
data sources oficialmente suportados pelo PDC.

Passo a passo:

1. Crie a conta gratuita em grafana.com e acesse seu "stack" (instância).
2. No menu do stack, vá em *Connections > Private data source connect* e
   crie uma nova conexão PDC. A interface gera um comando/token para
   instalar o `pdc-agent` na sua máquina (binário para Windows disponível).
3. Rode o `pdc-agent` localmente com o token gerado — ele mantém o túnel
   ativo (pode ser instalado como serviço do Windows para persistir).
4. Em *Connections > Data sources > Add data source > PostgreSQL*,
   preencha os mesmos dados da Opção A (host `localhost:5432`, banco
   `ninho_mimo_trends`, usuário/senha do seu `.env`), mas selecione a
   conexão PDC criada no passo 2 em vez de uma conexão direta.
5. Importe o dashboard normalmente (mesmo passo 3 da Opção A).

Documentação oficial: [Private data source connect (PDC)](https://grafana.com/docs/grafana-cloud/connect-externally-hosted/private-data-source-connect/).

Se preferir, me avise depois de criar a conta e gerar o token do PDC que
eu ajudo a instalar/configurar o agente localmente.

## Ajustando o limiar de indicação

O limiar que decide o que é "indicado" fica em
`configs/scoring_rules.json → indication.opportunity_threshold`
(padrão **70**). Ajustar esse valor não requer nenhuma mudança no
dashboard — apenas nas próximas coletas.

## Consultas usadas pelos painéis

Todas as consultas usam `tb_product_indications` (`pi`) unida a
`tb_categories` (`c`) e, na tabela de detalhe, também a `tb_products`
(`p`). O filtro de categoria usa `c.slug IN (${category:sqlstring})` e o
filtro de período usa a macro `$__timeFilter(pi.indicated_at)` do plugin
PostgreSQL do Grafana — ambos populados automaticamente pela variável de
template e pelo seletor de período do dashboard.
