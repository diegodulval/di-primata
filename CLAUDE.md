# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Commands

### Backend (Python / FastAPI)

```bash
make dev          # cria .venv e instala dependências incluindo [dev]
make run          # uvicorn em http://localhost:8000 com reload
make test         # pytest
make cov          # pytest com cobertura HTML em htmlcov/
make lint         # ruff check app tests
make fmt          # ruff format app tests
make check        # lint + pytest em sequência

# testes pontuais
.venv/bin/pytest tests/test_whatsapp.py -v
.venv/bin/pytest tests/unit/test_cycle_service.py::test_nome -v

# instalar pacote novo
source $HOME/.local/bin/env && uv pip install <pacote>
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

### Backend

Stack: FastAPI + Pydantic v2 + Python 3.12. **Sem banco de dados** — tudo em memória via `InMemoryRepository[T]` (`app/repositories/base.py`). A store singleton (`app/repositories/store.py`) centraliza todos os repositórios. Quando houver migração para banco, apenas os repositórios mudam.

**Camadas:**

```
routers/      ← HTTP, validação de entrada, injeção de dependências
services/     ← regras de negócio, orquestra repositories
repositories/ ← acesso a dados (InMemoryRepository)
models/       ← Pydantic (entidades + schemas de request/response)
core/         ← config (Settings/pydantic-settings), auth (JWT), deps (FastAPI Depends)
```

**Autenticação:** JWT Bearer via `app/core/deps.py`. `get_token()` decodifica; `require_roles(*roles)` protege rotas. O `account_id` no token isola dados entre tenants.

**Bootstrap admin:** ao subir a API sem contas cadastradas, `lifespan` cria automaticamente o admin usando variáveis `BOOTSTRAP_ADMIN_*` do `.env`.

**Twilio / WhatsApp:**
- `app/routers/whatsapp.py` expõe dois endpoints: `POST /whatsapp/webhook` (mensagens inbound) e `POST /whatsapp/status` (status de entrega — mantido separado para não poluir o log principal).
- O `twilio.rest.Client` é um **singleton** inicializado no `lifespan` e armazenado em `app.state.twilio_client`. Injetado via `get_twilio_client(request)` em `app/core/deps.py`.
- `WhatsappService` contém uma **máquina de estados** baseada em `EstadoAgente`. Para adicionar um novo fluxo: criar um `_handle_*` e registrá-lo no dicionário `handlers` em `_despachar()`.
- Keywords `menu`, `reiniciar`, `0`, `voltar`, `cancelar`, `início`/`inicio` resetam qualquer sessão de volta ao `OCIOSO` e exibem o menu.
- Em testes, `get_twilio_client` é sobrescrito via `app.dependency_overrides` para retornar `None` — o service entra no modo simulado (sem chamada real à Twilio).

### Frontend

Monorepo pnpm em `web/` com dois apps e quatro packages:

```
apps/
  dashboard/   ← SPA admin (port 5173) — TanStack Router + Query + Tailwind v4
  portal/      ← Portal público QR (port 5174) — mobile-first, acesso produtor + rastreio público

packages/
  ui/          ← Componentes base: Card, Badge, Button, Input, Field, Select, StepIndicator, Skeleton…
  theme/       ← ThemeProvider + tokens CSS por paleta (floresta, oliva, terra, brisa)
  api-client/  ← Cliente tipado gerado do OpenAPI (openapi-fetch + openapi-typescript)
  shared/      ← Auth, QueryClient compartilhado, tipos de domínio, enums, hooks utilitários
```

**Dependência entre packages:** `shared` não importa nenhum outro package interno. `api-client` importa `shared`. `ui` e `theme` são independentes. Apps importam tudo.

**Auth compartilhado (`packages/shared/src/auth.ts`):** `getToken()`, `setToken()`, `clearToken()`, `restoreToken(cb)`. O token vive em `sessionStorage` sob a chave `"access_token"`. Nunca acessar `sessionStorage` diretamente nas rotas — usar sempre essas funções. `restoreToken(setAuthToken)` é chamado no `main.tsx` de cada app para reidratar o cliente API no reload de página.

**QueryClient compartilhado (`packages/shared/src/query-client.ts`):** instância única exportada como `queryClient`. Ambos os apps importam e passam para `QueryClientProvider` — não instanciar um novo.

**Tipos de domínio (`packages/shared/src/types/domain.ts`):** `Account`, `Unit`, `PlatformUser`, `DomainSchema`, `SelectOption` etc. Adicionar novos tipos de API aqui, nunca declarar localmente nas rotas.

**Componentes de formulário (`packages/ui`):**
- `Input`: CVA com variante `inputSize` (sm/md) — **não `size`**, pois `size` é atributo nativo do `<input>` com tipo `number` e causa conflito de tipos.
- `Select`: mesma razão — variante nomeada `selectSize`.
- `Field`: wrapper com `label`, `hint` e `error`. O prop `error` é tipado como `string | undefined` (necessário com `exactOptionalPropertyTypes: true`).

**Theming:** `ThemeProvider` aplica `theme-<paleta>` no `<html>`. Cada app importa em `styles.css` apenas o token CSS da sua paleta: dashboard usa `oliva.css`, portal usa `floresta.css`. Não importar todas as paletas nos dois apps.

**Cliente API:** `web/packages/api-client/src/client.ts` exporta a instância `api`. O `schema.ts` em `src/generated/` é **gerado — nunca editar manualmente**. Rodar `pnpm generate:api` após qualquer mudança na API Python. O dashboard proxia `/api` → `http://localhost:8000` via Vite.

**Roteamento:** TanStack Router com file-based routing. Rotas do dashboard protegidas via `beforeLoad` usando `getToken()` de `@di-mata/shared`. Portal usa o mesmo padrão — `getToken()` em `beforeLoad` das rotas autenticadas.

**BFF (`app/routers/bff.py`):** router montado em `/bff` com endpoints `GET /bff/users`, `POST /bff/users` e `GET /bff/stats`. O `POST /bff/users` diferencia criação por role: PRODUTOR cria Account própria + Units; outros roles (OPERADOR, CONSULTOR) são sub-usuários vinculados à conta do admin autenticado.

---

## Variáveis de ambiente (.env)

| Variável | Descrição |
|---|---|
| `APP_ENV` | `development` \| `production` |
| `SECRET_KEY` | Chave JWT |
| `TWILIO_ACCOUNT_SID` | Account SID da Twilio |
| `TWILIO_AUTH_TOKEN` | Auth Token da Twilio |
| `TWILIO_WHATSAPP_FROM` | Número Twilio sem prefixo (ex: `+14155238886`) |
| `TWILIO_VALIDATE_SIGNATURE` | `True` em produção para validar HMAC do webhook |
| `FRONTEND_URL` | URL do frontend em produção (para CORS) |

Para expor o servidor localmente ao Twilio (desenvolvimento):

```bash
/tmp/cloudflared tunnel --url http://localhost:8000 --no-autoupdate
```

Configurar no Console Twilio → Sandbox Settings:
- **When a message comes in** → `https://<url>/whatsapp/webhook`
- **Status callback URL** → `https://<url>/whatsapp/status`
