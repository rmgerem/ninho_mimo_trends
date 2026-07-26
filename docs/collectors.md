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

## Fluxo de erros

Erros de um único item durante `collect()` (ex.: um produto malformado)
não impedem o restante da iteração — são capturados por
`CollectionService`, contados e gravados em `tb_collection_errors`.
Já uma falha da fonte como um todo — `SourceUnavailableError` (fonte
desativada/não encontrada) ou `CollectorConfigurationError`
(configuração inválida, ex.: `base_url` ausente) levantada dentro de
`validate_configuration()` ou `collect()` — interrompe a execução
inteira e marca `tb_collection_runs.status = FAILED`.
