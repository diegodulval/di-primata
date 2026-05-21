# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Commands

### Backend (Python / FastAPI) — uv workspace

```bash
make install      # uv sync (instala todos os packages do workspace)
make dev          # uv sync --all-extras (inclui pytest, ruff, httpx)
make hooks        # ativa git hooks (.githooks/)

make run          # alias para run-producao
make run-producao # fastapi dev apps/producao em :8000
make run-oficinas # fastapi dev apps/oficinas em :8001

make test         # pytest em apps/producao/tests
make cov          # pytest com cobertura HTML
make lint         # ruff check em todo o workspace Python
make fmt          # ruff format em todo o workspace Python
make check        # lint + pytest

# testes pontuais
cd apps/producao && uv run --package producao pytest tests/test_whatsapp.py -v
cd apps/producao && uv run --package producao pytest tests/unit/test_cycle_service.py::test_nome -v

# adicionar dependência a um package
cd apps/producao && uv add <pacote>        # dependência de producao
cd packages/core && uv add <pacote>        # dependência compartilhada
```

### Frontend (React / TypeScript)

```bash
cd web
pnpm install      # instala workspace completo
pnpm dev          # dashboard :5173 + portal :5174 em paralelo
pnpm build        # build de todos os apps
pnpm check        # biome lint + format check
pnpm fmt          # biome format --write
pnpm typecheck    # tsc --noEmit em todos os apps
pnpm generate:api # regenera web/packages/api-client/src/generated/schema.ts
                  # requer make run antes (lê /openapi.json em localhost:8000)
```

Comandos isolados por pacote:

```bash
pnpm --filter dashboard dev
pnpm --filter portal typecheck
pnpm --filter api-client generate
```

### Git hooks

Os hooks em `.githooks/` executam automaticamente no commit: ruff check, ruff format --check e pytest. Ativar com `make hooks`.

---

## Arquitetura

### Monorepo Python (uv workspaces)

```
pyproject.toml          ← workspace root (define members, ruff config)
packages/
  core/                 ← modelos de domínio, repositórios, db
  auth/                 ← JWT, hash, FastAPI dependencies
  utils/                ← utilitários genéricos (pagination, dates, validators)
apps/
  producao/             ← app de rastreabilidade (porta 8000)
  oficinas/             ← app de oficinas (porta 8001) — em desenvolvimento
```

**Regra de dependência — nunca violar:**
```
apps → packages      (permitido)
packages → packages  (permitido, cuidando de não criar ciclos)
packages → apps      (PROIBIDO)
```

### packages/core

Stack: Pydantic v2 + asyncpg. **Sem banco de dados** — tudo em memória via `InMemoryRepository[T]` (`packages/core/src/core/repositories/base.py`).

```
core/models/      ← Pydantic: Account, User, Cycle, Event, Lot, Protocol, Unit, Enums…
core/domains/     ← DomainSchema, rural.py, industrial.py, registry.py
core/repositories/← InMemoryRepository[T] genérico
core/db/          ← asyncpg pool (pool.py) — migrations em cada app
```

Quando houver migração para banco, apenas os repositórios mudam. O core já tem `db/pool.py` para criar o asyncpg pool.

### packages/auth

```
auth/jwt.py           ← TokenData, create_access_token, decode_token, hash_password, verify_password
auth/dependencies.py  ← get_token, require_roles, get_twilio_client, get_debounce_buffer, get_rate_limiter
auth/config.py        ← AuthSettings (SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES) lê de .env
```

**Autenticação:** JWT Bearer via `auth.dependencies.get_token()` decodifica; `require_roles(*roles)` protege rotas. O `account_id` no token isola dados entre tenants.

### apps/producao

```
producao/main.py          ← FastAPI app, lifespan, CORS, routers
producao/config.py        ← Settings completo (todos os campos de .env)
producao/routers/         ← HTTP: auth, accounts, units, cycles, events, lots, public, whatsapp, bff
producao/services/        ← regras de negócio: AuthService, CycleService, LotService, WhatsappService
producao/repositories/
  store.py                ← Store singleton (todos os InMemoryRepository)
producao/ingestion/       ← normalizer, DebounceBuffer, FixedWindowRateLimiter, models
producao/db/
  queue.py                ← operações asyncpg na message_queue
  migrations/             ← SQL migrations do producao
```

**Bootstrap admin:** ao subir sem contas, `lifespan` cria automaticamente o admin usando `BOOTSTRAP_ADMIN_*` do `.env`.

**Twilio / WhatsApp:**
- `producao/routers/whatsapp.py`: `POST /whatsapp/webhook` (inbound) e `POST /whatsapp/status` (entrega).
- `twilio.rest.Client` é singleton em `app.state.twilio_client`, injetado via `get_twilio_client(request)`.
- `WhatsappService` tem **máquina de estados** baseada em `EstadoAgente`. Para novo fluxo: criar `_handle_*` e registrar em `_despachar()`.
- Keywords `menu`, `reiniciar`, `0`, `voltar`, `cancelar`, `início`/`inicio` resetam para `OCIOSO`.
- Em testes, `get_twilio_client` é sobrescrito via `app.dependency_overrides` → modo simulado.

**BFF (`producao/routers/bff.py`):** montado em `/bff`. `POST /bff/users` diferencia criação por role: PRODUTOR cria Account + Units; OPERADOR/CONSULTOR são sub-usuários da conta do admin autenticado.

### Testes (apps/producao/tests/)

```
conftest.py         ← fixtures: store, client, seeded, auth_headers
test_whatsapp.py    ← webhook endpoint
unit/               ← test_auth_service, test_cycle_service, test_lot_service, test_whatsapp_service
integration/        ← test_cycle_flow (golden path HTTP)
```

### Frontend (web/)

Monorepo pnpm em `web/` com dois apps e quatro packages:

```
apps/
  dashboard/   ← SPA admin (port 5173) — TanStack Router + Query + Tailwind v4
  portal/      ← Portal público QR (port 5174) — mobile-first

packages/
  ui/          ← Componentes base: Card, Badge, Button, Input, Field, Select, StepIndicator, Skeleton…
  theme/       ← ThemeProvider + tokens CSS por paleta (floresta, oliva, terra, brisa)
  api-client/  ← Cliente tipado gerado do OpenAPI (openapi-fetch + openapi-typescript)
  shared/      ← Auth, QueryClient compartilhado, tipos de domínio, enums, hooks utilitários
```

**Dependência entre packages:** `shared` não importa nenhum outro package interno. `api-client` importa `shared`. `ui` e `theme` são independentes. Apps importam tudo.

**Auth compartilhado (`packages/shared/src/auth.ts`):** `getToken()`, `setToken()`, `clearToken()`, `restoreToken(cb)`. Token em `sessionStorage["access_token"]`. Nunca acessar `sessionStorage` diretamente nas rotas.

**Componentes de formulário (`packages/ui`):**
- `Input`: variante `inputSize` (sm/md) — **não `size`** (conflito com atributo nativo HTML).
- `Select`: idem — variante nomeada `selectSize`.
- `Field`: prop `error` tipado como `string | undefined` (compatível com `exactOptionalPropertyTypes: true`).

**Cliente API:** `schema.ts` em `src/generated/` é **gerado — nunca editar manualmente**. Rodar `pnpm generate:api` após mudanças na API Python.

---

## Variáveis de ambiente (.env)

| Variável | Escopo | Descrição |
|---|---|---|
| `APP_ENV` | global | `development` \| `production` |
| `SECRET_KEY` | global (auth) | Chave JWT — mesma para todas as apps |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | global (auth) | TTL do token (padrão: 60) |
| `FRONTEND_URL` | global | URL do frontend em produção (CORS) |
| `BOOTSTRAP_ADMIN_*` | producao | Admin criado na primeira inicialização |
| `TWILIO_ACCOUNT_SID` | producao | Account SID da Twilio |
| `TWILIO_AUTH_TOKEN` | producao | Auth Token da Twilio |
| `TWILIO_WHATSAPP_FROM` | producao | Número Twilio (ex: `+14155238886`) |
| `TWILIO_VALIDATE_SIGNATURE` | producao | `True` em produção (valida HMAC) |
| `DATABASE_URL` | producao | PostgreSQL para fila WhatsApp |
| `DEBOUNCE_WINDOW_SECONDS` | producao | Janela de debounce (padrão: 2.0s) |
| `RATE_LIMIT_MAX` / `RATE_LIMIT_WINDOW` | producao | Rate limit por phone |

Para expor o servidor localmente ao Twilio (desenvolvimento):

```bash
/tmp/cloudflared tunnel --url http://localhost:8000 --no-autoupdate
```

Configurar no Console Twilio → Sandbox Settings:
- **When a message comes in** → `https://<url>/whatsapp/webhook`
- **Status callback URL** → `https://<url>/whatsapp/status`

---

## Alembic / Migrations

Cada app tem suas próprias migrations — **nunca compartilhadas pelo core**.

```
apps/producao/src/producao/db/migrations/  ← SQL do producao (asyncpg direto por ora)
apps/oficinas/src/oficinas/db/migrations/  ← SQL do oficinas (quando tiver DB)
```

Quando o producao migrar para SQLAlchemy: `alembic init` dentro de `apps/producao/`.
O `packages/core` não tem Alembic — cada app gerencia sua própria história de schema.
