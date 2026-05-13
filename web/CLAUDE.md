# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in the `web/` monorepo.

---

## Comandos

```bash
# Na raiz de web/
pnpm install          # instala workspace inteiro
pnpm dev              # dashboard :5173 + portal :5174 em paralelo
pnpm build            # build de todos os apps
pnpm typecheck        # tsc --noEmit em todos os packages/apps
pnpm check            # biome lint + format check
pnpm fmt              # biome format --write
pnpm generate:api     # regenera schema.ts (requer API rodando em :8000)

# Filtrado por pacote
pnpm --filter dashboard dev
pnpm --filter portal typecheck
pnpm --filter ui typecheck
pnpm --filter api-client generate
```

---

## Estrutura do workspace

```
web/
  apps/
    dashboard/     port 5173 — SPA de gestão (admin/operador)
    portal/        port 5174 — portal público (rastreio + área do produtor)
  packages/
    shared/        auth, queryClient, tipos de domínio, enums, utils
    ui/            componentes React reutilizáveis
    theme/         ThemeProvider + tokens CSS por paleta
    api-client/    cliente HTTP tipado gerado do OpenAPI
```

**Grafo de dependências entre packages (sem ciclos):**

```
shared  ←  api-client  ←  apps
ui                      ←  apps
theme                   ←  apps
```

`shared` não pode importar nenhum outro package interno.

---

## packages/shared

Fonte de verdade para infraestrutura compartilhada entre os dois apps.

### Auth (`src/auth.ts`)

```ts
getToken(): string | null
setToken(token: string): void
clearToken(): void
restoreToken(cb: (token: string) => void): void  // chama cb se token existir no sessionStorage
```

- Token vive em `sessionStorage["access_token"]`.
- **Nunca** acessar `sessionStorage` diretamente nas rotas — usar sempre essas funções.
- `restoreToken(setAuthToken)` é chamado no `main.tsx` de cada app para reidratar o cliente API após reload de página.

### QueryClient (`src/query-client.ts`)

Instância única com `staleTime: 30_000` e `retry: 1`. Ambos os apps importam e passam para `QueryClientProvider` — nunca instanciar um novo `QueryClient` localmente.

### Tipos de domínio (`src/types/domain.ts`)

Interfaces canônicas: `Account`, `Unit`, `PlatformUser`, `DomainSchema`, `SelectOption`, `EntityLabel`. Declarar novos tipos de resposta de API aqui, nunca localmente dentro de um arquivo de rota.

### Enums (`src/types/enums.ts`)

Espelho dos enums Python: `RolePerfil`, `TipoUnidade`, `StatusCiclo`, `TipoEvento`, etc. Manter sincronizado com `app/models/enums.py` no backend.

---

## packages/ui

Componentes base com CVA (class-variance-authority) + Tailwind v4.

### Armadilhas de nomenclatura de variantes

`<input>` e `<select>` têm atributos nativos `size` com tipo `number`. Nomear uma variante CVA `size: "sm" | "md"` gera conflito de tipos com o HTML nativo.

| Componente | Variante correta | Não usar |
|---|---|---|
| `Input` | `inputSize` | `size` |
| `Select` | `selectSize` | `size` |

### Field

Wrapper de campo de formulário com `label`, `hint` e `error`. O prop `error` é `string | undefined` (não apenas `string`) por causa do `exactOptionalPropertyTypes: true` no tsconfig — passar `string | undefined` para `error?: string` é erro de tipos.

### Exportações (`src/index.ts`)

`Button`, `Badge`, `Card` (+ sub-componentes), `Field`, `Input`, `Select`, `StepIndicator`, `Skeleton`, `ApiUnavailable`, `cn`.

---

## packages/theme

`ThemeProvider` aplica `theme-<paleta>` no `<html>`. Os tokens CSS em `src/tokens/` definem `--color-*`, `--font-*`, `--shadow-*`. Tailwind v4 consome via `@theme inline`.

**Cada app importa em `styles.css` apenas o token da sua paleta:**

| App | Paleta | Imports em styles.css |
|---|---|---|
| dashboard | oliva | `base.css` + `oliva.css` |
| portal | floresta | `base.css` + `floresta.css` |

Não importar todas as paletas em ambos os apps.

---

## packages/api-client

Cliente HTTP tipado gerado via `openapi-typescript` + `openapi-fetch`.

- `src/generated/schema.ts` — **nunca editar manualmente**. Regenerar com `pnpm generate:api` após qualquer mudança na API Python.
- `src/client.ts` — exporta `api` (instância `openapi-fetch`) e `setAuthToken(token | null)`. O middleware injeta o `Bearer` token em toda requisição e emite `auth:unauthorized` no `window` em respostas 401.
- O dashboard ouve `auth:unauthorized` em `dashboard.tsx` para fazer logout automático.

---

## apps/dashboard

SPA de gestão em `port 5173`. Proxia `/api` → `http://localhost:8000` via Vite.

**Rotas:**

```
/                   → redirect para /dashboard ou /login
/login              → LoginPage
/dashboard          → layout raiz (autenticado)
  /                 → índice / resumo
  /usuarios         → lista de usuários da plataforma
  /usuarios/novo    → wizard 3-passos de criação
  /registros        → eventos
  /whatsapp         → sessões WhatsApp
  /whatsapp/:id     → detalhe de sessão
  /settings         → configurações da conta
```

**Autenticação:** `beforeLoad` em `dashboard.tsx` chama `getToken()` — redireciona para `/login` se ausente.

**DomainProvider:** wraps todo o layout `/dashboard`. Busca `GET /api/bff/schema` para obter labels e opções do domínio do tenant. Fornece `useDomain()` para labels dinâmicos nos componentes de navegação e formulários.

**Criação de usuário (`/usuarios/novo`):** wizard com 3 passos — credenciais → role → dados org (só para PRODUTOR). Roles PRODUTOR criam conta própria + unidades; OPERADOR/CONSULTOR são sub-usuários da conta admin.

---

## apps/portal

Portal público em `port 5174`. Mobile-first. Proxia `/api` → `http://localhost:8000` via Vite.

**Rotas:**

```
/                   → home (rastrear por código + login)
/p/:hash            → rastreabilidade pública de produto
/minha-area         → área autenticada do produtor (protegida)
```

**Autenticação:** `beforeLoad` em `/minha-area` chama `getToken()` — redireciona para `/` se ausente.

---

## TypeScript — configurações críticas

O `tsconfig.base.json` habilita flags estritas que geram erros não-óbvios:

| Flag | Consequência prática |
|---|---|
| `exactOptionalPropertyTypes` | `prop?: string` rejeita `undefined` explícito — usar `prop?: string \| undefined` em interfaces de componentes |
| `noUncheckedIndexedAccess` | acesso a array/objeto por índice retorna `T \| undefined` — sempre verificar antes de usar |
| `strict` | `noImplicitAny`, `strictNullChecks` etc. ativos |

---

## Linting e formatação

Biome gerencia lint + format no workspace inteiro (arquivo `biome.json` na raiz de `web/`).

- Indentação: 2 espaços
- Aspas: duplas
- Trailing commas: ES5
- Line width: 100
- `packages/api-client/src/generated/**` está no ignore — não formatar o schema gerado.
