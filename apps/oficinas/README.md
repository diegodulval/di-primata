# Di Mata — Oficinas

API de gestão de oficina mecânica e auto peças. Roda na porta **8001**.

## Pré-requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) instalado
- PostgreSQL 16 acessível
- `psql` no PATH (para rodar migrations)

---

## Configuração

Copie o arquivo de exemplo e preencha as variáveis:

```bash
cp .env.example .env
```

Variáveis relevantes para o app de oficinas:

```env
# Banco de dados
OFICINAS_DATABASE_URL=postgresql://user:senha@localhost/oficinas

# JWT — mesma chave para todos os apps do workspace
SECRET_KEY=troque-por-um-segredo-forte
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Ambiente
APP_ENV=development
```

> `OFICINAS_DATABASE_URL` é usada pelos targets do Makefile. O app em si lê `DATABASE_URL` — defina ambas no `.env` se rodar localmente sem o Makefile.

---

## Instalação

Na raiz do monorepo:

```bash
make install   # uv sync — instala todas as dependências
```

---

## Banco de dados

### Criar o banco

```bash
createdb oficinas
# ou via psql:
psql -c "CREATE DATABASE oficinas;"
```

### Aplicar migrations

```bash
make migrate-oficinas
```

Isso executa em ordem:

| Arquivo | Conteúdo |
|---------|----------|
| `001_global_schema.sql` | Schema `global` — veículo e histórico cross-tenant |
| `002_tenant_schema.sql` | Tabelas do tenant — usuário, cliente, produto, OS, etc. |
| `003_rls_policies.sql` | Row Level Security por tenant |
| `004_seed.sql` | Tenant e admin de desenvolvimento |
| `005_iam_adjustments.sql` | Ajustes de IAM (índices, constraints adicionais) |

### Credenciais criadas pelo seed

| Campo | Valor |
|-------|-------|
| E-mail | `admin@oficina.dev` |
| Senha | `dev1234` |
| Perfil | `ADMIN` |

---

## Executar a API

```bash
make run-oficinas
```

A API sobe em `http://localhost:8001`.

Endpoints disponíveis:

- `GET  /health` — status do serviço
- `POST /auth/login` — login (`identificador` + `senha`)
- `GET  /usuarios/me` — perfil do usuário autenticado
- `GET/POST /clientes` — cadastro de clientes
- `GET/POST /veiculos` — veículos (schema global, cross-tenant)
- `GET/POST /produtos` — estoque de produtos
- `GET/POST /fornecedores` — fornecedores
- `POST /entradas/xml` — importação de NF-e (XML)
- Documentação interativa: `http://localhost:8001/docs`

---

## Popular dados de exemplo

Com a API rodando (`make run-oficinas`) e as migrations aplicadas:

```bash
make seed-oficinas
```

O seed cria:

- 2 clientes: **João da Silva** e **Auto Peças Rápida LTDA**
- 2 veículos: **ABC1234** (Toyota Corolla) e **XYZ9J87** (Honda CG 160)
- 3 produtos em estoque: **FLT001**, **VLA001**, **OLM001**

---

## Frontend

O frontend do app de oficinas roda na porta **5175**:

```bash
cd web
pnpm install
pnpm --filter oficinas dev
```

Acesse `http://localhost:5175` e faça login com `admin@oficina.dev` / `dev1234`.

---

## Fluxo completo (primeira vez)

```bash
# 1. Instalar dependências
make install

# 2. Configurar banco
createdb oficinas
OFICINAS_DATABASE_URL=postgresql://localhost/oficinas make migrate-oficinas

# 3. Subir a API
make run-oficinas

# 4. Popular dados de exemplo (em outro terminal)
make seed-oficinas

# 5. Subir o frontend (em outro terminal)
cd web && pnpm install && pnpm --filter oficinas dev
```

---

## Testes

```bash
cd apps/oficinas
uv run --package oficinas pytest tests -v
```

---

## Estrutura do app

```
apps/oficinas/
├── src/oficinas/
│   ├── main.py           ← FastAPI app factory, middlewares, routers
│   ├── config.py         ← Settings via pydantic-settings
│   ├── core/
│   │   ├── database.py   ← asyncpg pool, RLS middleware
│   │   ├── security.py   ← bcrypt, JWT
│   │   ├── enums.py      ← Perfil, StatusOS, TipoMovimentacao…
│   │   └── exceptions.py ← exceções de domínio
│   └── modules/
│       ├── iam/          ← autenticação e usuários
│       ├── cadastros/    ← clientes e vínculos cliente-veículo
│       └── estoque/      ← produtos, fornecedores, NF-e entrada
├── migrations/           ← SQL puro, aplicado pelo make migrate-oficinas
├── tests/
└── Dockerfile
```
