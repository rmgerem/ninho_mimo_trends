# Ninho & Mimo Trends

> Carinho em cada fase.

Plataforma de inteligencia de produtos voltada para gestantes, maes no
pos-parto, bebes e criancas de ate 10 anos. O sistema coleta, organiza,
compara e classifica produtos que estao ganhando relevancia na internet,
gerando um ranking de oportunidades para orientar a producao de conteudo
em redes sociais (divulgacao manual, sem automacao de postagem neste MVP).

> **Status:** projeto em construcao incremental. Este README sera
> completado ao final da Etapa 10 com instrucoes completas de instalacao,
> configuracao, execucao, testes e roadmap.

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

Documentacao detalhada sera adicionada em [docs/](docs) ao longo das
proximas etapas.

## Site institucional (protótipo)

Em [docs/ninho_mimo_site/](docs/ninho_mimo_site/) há um protótipo estático
(HTML/CSS/JS puro, sem build e sem backend) do site institucional da marca,
já com a identidade visual (logo, cores e tipografia) aplicada. Para rodar
localmente:

```bash
cd docs/ninho_mimo_site
python3 -m http.server 8000
# acesse http://localhost:8000
```

Hoje o site é independente da plataforma Python (dados de exemplo apenas).
A integração com o catálogo real (PostgreSQL/API) é tratada na
[Fase 5 do roadmap](docs/roadmap.md#fase-5--interface-web-read-only).