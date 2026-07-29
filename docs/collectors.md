# Coletores

Um coletor (`collectors/`) é responsável por buscar produtos de uma
fonte externa e retorná-los no formato padronizado `CollectedProduct`
(dataclass congelada em `collectors/base.py`), **antes** de qualquer
normalização/deduplicação — essas etapas acontecem depois, em
`business/product_service.py` e `deduplication/`.

## `BaseCollector`

Classe abstrata (`ABC`) que todo coletor implementa:

```python
class BaseCollector(ABC):
    def __init__(self, source: Source, settings: Settings): ...

    @abstractmethod
    def validate_configuration(self) -> None: ...   # levanta erro se a fonte não pode ser usada

    @abstractmethod
    def healthcheck(self) -> bool: ...               # a fonte está acessível agora?

    @abstractmethod
    def collect(self, *, category: str | None = None, limit: int | None = None) -> Iterator[CollectedProduct]: ...
```

`CollectorRegistry` (`collectors/registry.py`) mapeia o `code` de uma
`Source` (`tb_sources.code`) para a classe de coletor correspondente:

| `source.code` | Classe |
|---|---|
| `mock` | `MockCollector` |
| `public_open_data` | `PublicSourceCollector` |
| `shopee_affiliate` | `ShopeeAffiliateCollector` |

Registrar um novo coletor é feito chamando
`CollectorRegistry().register("codigo_da_fonte", MinhaClasseCollector)`.

## `MockCollector`

Coletor usado em desenvolvimento/testes e nas demonstrações da CLI. Lê
produtos de um arquivo fixo (`data/fixtures/mock_products.json`, 19
produtos com 4 snapshots de histórico cada = 76 itens) e os retorna como
`CollectedProduct`. Não faz nenhuma chamada de rede. Suporta os mesmos
filtros (`category`, `limit`) que um coletor real.

## `PublicSourceCollector` — desabilitado por padrão

Implementa o **mecanismo completo** de uma coleta HTTP respeitosa:

- Verificação de `robots.txt` antes de qualquer requisição
  (`urllib.robotparser`);
- Rate limiting configurável (`time.sleep` entre requisições);
- Timeout e retry com backoff exponencial (`utils/retry.retry_with_backoff`);
- `User-Agent` configurável;
- Mapeamento genérico de campos brutos → `CollectedProduct`
  (`_map_raw_item`, documentado como necessitando ajuste para o formato
  real de uma API/feed específico).

**Por que está desabilitado:** no momento da criação deste MVP, não foi
identificada uma fonte pública, aberta e permitida (sem exigir
credenciais ou API paga) cujos termos de uso autorizassem
explicitamente coleta automatizada e que fosse adequada ao nicho do
produto (gestantes/mães/bebês/crianças). Por isso, a entrada
`public_open_data` em [configs/sources.json](../configs/sources.json)
permanece com `"is_active": false`, e `PublicSourceCollector.validate_configuration()`
levanta `SourceUnavailableError` caso alguém tente usá-la mesmo assim.

### Como habilitar com uma fonte real

1. Verifique os termos de uso e o `robots.txt` da fonte escolhida —
   confirme que coleta automatizada é permitida.
2. Atualize `configs/sources.json`: ajuste `base_url` para a URL real e
   troque `is_active` para `true`.
3. Ajuste `PublicSourceCollector._map_raw_item()` para refletir o
   formato real da resposta (nomes de campos variam entre APIs/feeds).
4. Documente a decisão (fonte escolhida, data, link para os termos de
   uso consultados) neste arquivo.

### O que **não** fazer

Por design, este projeto **não** implementa:

- Selenium/Playwright ou qualquer automação de navegador;
- Bypass de CAPTCHA, login ou proteções tipo Cloudflare;
- Uso de APIs pagas sem uma abstração clara, opt-in e desabilitada por padrão;
- Scraping agressivo que ignore `robots.txt` ou limites de taxa.

## `ShopeeAffiliateCollector` — API oficial de afiliados (habilitado)

Integração com a **Shopee Affiliate Open API** (GraphQL,
`https://open-api.affiliate.shopee.com.br/graphql`), usando a query
`productOfferV2`. Diferente do `PublicSourceCollector`, esta é uma API
oficial que exige credenciais de uma conta de afiliado real — não é
scraping nem automação de navegador.

- **Credenciais**: `SHOPEE_AFFILIATE_APP_ID` e `SHOPEE_AFFILIATE_SECRET`
  no `.env` (nunca versionadas). Sem elas, `validate_configuration()`
  levanta `CollectorConfigurationError`.
- **Autenticação**: assinatura por requisição, cabeçalho
  `Authorization: SHA256 Credential={app_id}, Timestamp={ts}, Signature={sig}`,
  onde `sig = sha256(f"{app_id}{ts}{payload_json}{secret}").hexdigest()`.
  Verificado empiricamente contra a API real em 2026-07-29.
- **Categoria obrigatória**: a API da Shopee não usa a taxonomia interna
  deste projeto (busca é por `keyword` livre). Por isso, `--category`
  é **obrigatório** para este coletor: o slug é traduzido para um termo
  de busca a partir do nome legível em `configs/categories.json`, e todo
  produto retornado é marcado com esse mesmo slug.
- **Link de afiliado**: o campo `offerLink` retornado pela API (link
  monetizado, distinto da URL pública do produto) é persistido em
  `tb_product_sources.affiliate_url` e exibido em `products show` e
  `products export`.
- **Paginação**: 20 itens por página, respeitando `pageInfo.hasNextPage`,
  com um intervalo (`HTTP_RETRY_BACKOFF_SECONDS`) entre páginas.

```bash
ninho-mimo-trends collect --source shopee_affiliate --category criancas-brinquedos --limit 20
```

## Fluxo de erros

Erros de um único item durante `collect()` (ex.: um produto malformado)
não impedem o restante da iteração — são capturados por
`CollectionService`, contados e gravados em `tb_collection_errors`.
Já uma falha da fonte como um todo — `SourceUnavailableError` (fonte
desativada/não encontrada) ou `CollectorConfigurationError`
(configuração inválida, ex.: `base_url` ausente) levantada dentro de
`validate_configuration()` ou `collect()` — interrompe a execução
inteira e marca `tb_collection_runs.status = FAILED`.
