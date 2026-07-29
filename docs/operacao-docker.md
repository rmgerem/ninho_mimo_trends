# Guia operacional — Docker, extração e usuários

Este guia descreve a operação cotidiana do Ninho & Mimo Trends no Windows
com PowerShell. Execute os comandos na raiz do projeto, onde está o arquivo
`docker-compose.yml`.

## 1. Pré-requisitos

- Docker Desktop instalado e em execução;
- portas 3000, 5433, 8000, 9090 e 9091 disponíveis;
- arquivo `.env.docker.local` configurado;
- conta ativa na Shopee Affiliate Open API.

Crie o arquivo local de configuração na primeira instalação:

```powershell
Copy-Item .env.docker .env.docker.local
```

Edite `.env.docker.local` e preencha, no mínimo:

```dotenv
DB_NAME=ninho_mimo_trends
DB_USER=postgres
DB_PASSWORD=COLOQUE_UMA_SENHA_FORTE
POSTGRES_HOST_PORT=5433

SHOPEE_AFFILIATE_APP_ID=SEU_APP_ID
SHOPEE_AFFILIATE_SECRET=SEU_SECRET

GF_ADMIN_USER=admin
GF_ADMIN_PASSWORD=COLOQUE_UMA_SENHA_FORTE
GRAFANA_PORT=3000
PROMETHEUS_PORT=9090
```

Nunca envie essas senhas por chat, nunca as coloque na documentação e não
adicione `.env.docker.local` ao Git.

## 2. Subir o sistema

Na primeira execução, ou depois de alterar código/dependências:

```powershell
docker compose --env-file .env.docker.local up -d --build
```

O Compose executa automaticamente esta sequência:

1. inicia o PostgreSQL;
2. aplica as migrations;
3. executa o seed de categorias, fontes e usuário administrativo;
4. inicia o scheduler de extração;
5. inicia web, Grafana, Prometheus e Pushgateway.

Nas execuções seguintes, quando não houve alteração no código:

```powershell
docker compose --env-file .env.docker.local up -d
```

## 3. Endereços

| Serviço | Endereço |
|---|---|
| Dashboard Grafana | <http://localhost:3000> |
| API/roteador de afiliados | <http://localhost:8000/docs> |
| Prometheus | <http://localhost:9090> |
| Pushgateway | <http://localhost:9091> |
| PostgreSQL para pgAdmin | `localhost:5433` |

Entre containers, o PostgreSQL continua sendo acessado por `postgres:5432`.
A porta 5433 evita conflito com um PostgreSQL local na porta 5432.

## 4. Verificar o estado

Listar os serviços ativos:

```powershell
docker compose --env-file .env.docker.local ps
```

Incluir containers de migrations e seed que já terminaram:

```powershell
docker compose --env-file .env.docker.local ps -a
```

O estado esperado é:

- `postgres`: `Up (healthy)`;
- `scheduler`, `web`, `grafana`, `prometheus` e `pushgateway`: `Up`;
- `migrations` e `seed`: `Exited (0)`, pois são tarefas de execução única.

## 5. Extração de produtos

O serviço `scheduler` executa a coleta continuamente nos intervalos
configurados. Para acompanhar apenas a extração:

```powershell
docker compose --env-file .env.docker.local logs -f scheduler
```

Pressione `Ctrl+C` para sair da visualização. Isso não para o scheduler.

Executar uma rodada adicional manualmente:

```powershell
docker compose --env-file .env.docker.local exec scheduler ninho-mimo-trends scheduler run-once
```

Testar o coletor mock sem gravar dados:

```powershell
docker compose --env-file .env.docker.local exec scheduler ninho-mimo-trends collect --source mock --limit 5 --dry-run
```

Pausar somente as extrações:

```powershell
docker compose --env-file .env.docker.local stop scheduler
```

Retomar as extrações:

```powershell
docker compose --env-file .env.docker.local start scheduler
```

Reiniciar o scheduler:

```powershell
docker compose --env-file .env.docker.local restart scheduler
```

## 6. Logs

Logs de todos os serviços:

```powershell
docker compose --env-file .env.docker.local logs
```

Acompanhar todos em tempo real:

```powershell
docker compose --env-file .env.docker.local logs -f
```

Últimas 100 linhas de um serviço:

```powershell
docker compose --env-file .env.docker.local logs --tail 100 scheduler
docker compose --env-file .env.docker.local logs --tail 100 web
docker compose --env-file .env.docker.local logs --tail 100 grafana
docker compose --env-file .env.docker.local logs --tail 100 postgres
```

Logs produzidos nos últimos dez minutos:

```powershell
docker compose --env-file .env.docker.local logs --since 10m scheduler
```

Filtrar erros no PowerShell:

```powershell
docker compose --env-file .env.docker.local logs --since 30m 2>&1 |
    Select-String -Pattern 'ERROR|CRITICAL|Traceback|Falha'
```

## 7. Parar e reiniciar

Parar todos os containers sem removê-los:

```powershell
docker compose --env-file .env.docker.local stop
```

Iniciar novamente containers parados:

```powershell
docker compose --env-file .env.docker.local start
```

Reiniciar todos:

```powershell
docker compose --env-file .env.docker.local restart
```

Parar e remover os containers e a rede, preservando os dados:

```powershell
docker compose --env-file .env.docker.local down
```

Subir novamente:

```powershell
docker compose --env-file .env.docker.local up -d
```

> **Atenção:** `docker compose down -v` apaga os volumes do PostgreSQL,
> Grafana e Prometheus. Isso remove produtos, clientes, históricos e
> configurações persistidas. Não use `-v` em operação normal.

## 8. Atualizar depois de alterar o código

Reconstruir e recriar toda a aplicação:

```powershell
docker compose --env-file .env.docker.local up -d --build --force-recreate
```

Reconstruir somente web e scheduler:

```powershell
docker compose --env-file .env.docker.local up -d --build --force-recreate web scheduler
```

Aplicar migrations e executar o seed novamente:

```powershell
docker compose --env-file .env.docker.local run --rm migrations
docker compose --env-file .env.docker.local run --rm seed
```

O seed é idempotente: pode ser executado novamente sem duplicar os dados de
referência nem o usuário administrativo.

## 9. Acessar o banco pelo pgAdmin

Cadastre um servidor no pgAdmin usando:

```text
Host: localhost
Port: 5433
Maintenance database: ninho_mimo_trends
Username: mesmo DB_USER do .env.docker.local
Password: mesmo DB_PASSWORD do .env.docker.local
```

Não use a porta 5432 se houver outro PostgreSQL instalado localmente. O banco
correto do Docker contém a coluna `role` em `public.tb_customers`.

Validação:

```sql
SELECT id, grafana_username, role, created_at
FROM public.tb_customers
ORDER BY id;
```

## 10. Cadastrar um cliente que pagou

O cadastro possui duas partes. O username deve ser exatamente igual nas duas.
As comparações atuais diferenciam maiúsculas de minúsculas.

### 10.1 Criar o login no Grafana

Entre no Grafana como administrador e abra a administração de usuários.
Crie o usuário com:

```text
Username: e-mail ou identificador único do comprador
Password: senha temporária forte
Organization role: Viewer
```

Não use a role `Admin` para clientes. A role `Viewer` dá acesso à pasta
`Clientes`, mas não à pasta `Admin`.

### 10.2 Associar o login às credenciais Shopee

No pgAdmin conectado à porta 5433, execute o SQL abaixo substituindo os três
valores marcados. Não armazene a senha do Grafana nesta tabela.

```sql
INSERT INTO public.tb_customers (
    grafana_username,
    shopee_app_id,
    shopee_app_secret,
    role
)
VALUES (
    'USERNAME_EXATO_DO_GRAFANA',
    'APP_ID_SHOPEE_DO_CLIENTE',
    'SECRET_SHOPEE_DO_CLIENTE',
    'customer'
)
ON CONFLICT (grafana_username)
DO UPDATE SET
    shopee_app_id = EXCLUDED.shopee_app_id,
    shopee_app_secret = EXCLUDED.shopee_app_secret,
    role = 'customer';
```

Quando o cliente clicar em `Link Afiliado`, o dashboard envia o username
autenticado ao backend. O backend lê as credenciais correspondentes em
`tb_customers`, gera o link pela API da Shopee e redireciona o navegador.

### 10.3 Conferir sem mostrar secrets

```sql
SELECT
    id,
    grafana_username,
    role,
    shopee_app_id IS NOT NULL AS possui_app_id,
    shopee_app_secret IS NOT NULL AS possui_secret,
    created_at
FROM public.tb_customers
ORDER BY id;
```

### 10.4 Atualizar credenciais ou role

```sql
UPDATE public.tb_customers
SET
    shopee_app_id = 'NOVO_APP_ID',
    shopee_app_secret = 'NOVO_SECRET',
    role = 'customer'
WHERE grafana_username = 'USERNAME_EXATO_DO_GRAFANA';
```

### 10.5 Bloquear ou remover o acesso

Primeiro desative ou exclua o usuário no Grafana. Depois remova a associação:

```sql
DELETE FROM public.tb_customers
WHERE grafana_username = 'USERNAME_EXATO_DO_GRAFANA';
```

Sem a linha em `tb_customers`, o backend rejeita a geração do link afiliado.

## 11. Diagnóstico rápido

Verificar a saúde do PostgreSQL:

```powershell
docker inspect --format='{{json .State.Health}}' nmt_postgres
```

Verificar a API web:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:8000/docs
```

Abrir um shell no scheduler:

```powershell
docker compose --env-file .env.docker.local exec scheduler bash
```

Ver os processos dos containers:

```powershell
docker compose --env-file .env.docker.local top
```

Ver o consumo de recursos:

```powershell
docker stats
```

Se algum serviço estiver reiniciando, consulte primeiro:

```powershell
docker compose --env-file .env.docker.local ps -a
docker compose --env-file .env.docker.local logs --tail 200 NOME_DO_SERVICO
```
