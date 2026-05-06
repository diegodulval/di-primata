# Di Mata — Frontend

Monorepo do frontend da plataforma Di Mata. Dois apps independentes sobre uma base de packages compartilhados.

---

## Estrutura

```
web/
├── apps/
│   ├── dashboard/        → SPA autenticado (admin, manager, operador)  :5173
│   └── portal/           → Portal público QR do consumidor             :5174
└── packages/
    ├── theme/            → Tokens CSS das 4 paletas + ThemeProvider
    ├── shared/           → Tipos de domínio, hooks, utilitários
    ├── api-client/       → Cliente tipado gerado do OpenAPI da API
    └── ui/               → Componentes base (Button, Card, Badge, Skeleton…)
```

---

## Pré-requisitos

| Ferramenta | Versão mínima |
|---|---|
| Node.js | 22 LTS |
| pnpm | 9 |

Instalar via nvm (caso não tenha):
```bash
wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
source ~/.bashrc
nvm install 22
corepack enable && corepack prepare pnpm@latest --activate
```

---

## Setup

```bash
# a partir da raiz do projeto
make web-install

# ou diretamente dentro de web/
cd web && pnpm install
```

---

## Rodando em desenvolvimento

A API deve estar no ar antes de subir o frontend.

**Terminal 1 — API:**
```bash
# na raiz do projeto
make run
```

**Terminal 2 — Frontend:**
```bash
make web-dev
# ou:
cd web && pnpm dev
```

| App | URL |
|---|---|
| Dashboard | http://localhost:5173 |
| Portal QR público | http://localhost:5174/p/{hash} |

> Se a API não estiver no ar, os apps exibem uma tela de indisponibilidade com botão "Tentar novamente".

---

## Gerando o cliente da API

O package `api-client` contém tipos TypeScript gerados automaticamente a partir do schema OpenAPI da API. Rode sempre que o backend mudar.

```bash
# na raiz do projeto (API precisa estar no ar)
make web-generate

# ou diretamente
cd web && pnpm generate:api
```

O arquivo gerado fica em `packages/api-client/src/generated/schema.ts` — não editar manualmente.

> Se a API não estiver no ar, o comando falha com uma mensagem indicando como subí-la.

---

## Scripts disponíveis

Execute a partir de `web/` com `pnpm <script>` ou da raiz com `make <alvo>`.

| Script (`pnpm`) | Make | O que faz |
|---|---|---|
| `pnpm dev` | `make web-dev` | Sobe dashboard (:5173) e portal (:5174) |
| `pnpm build` | `make web-build` | Build de produção dos dois apps |
| `pnpm check` | `make web-check` | Biome lint + format check |
| `pnpm fmt` | — | Formata todos os arquivos |
| `pnpm typecheck` | — | TypeScript strict em todos os packages |
| `pnpm generate:api` | `make web-generate` | Gera cliente tipado do OpenAPI |

---

## Qualidade de código

O projeto usa [Biome](https://biomejs.dev/) — lint e formatação em um único binário (equivalente ao Ruff no Python).

```bash
cd web

# verificar erros
pnpm check

# formatar automaticamente
pnpm fmt

# checar tipos TypeScript
pnpm typecheck
```

Configuração em `web/biome.json`. Arquivos gerados (`packages/api-client/src/generated/**`) são ignorados automaticamente.

---

## Paletas de tema (whitelabel)

Cada paleta é definida em `packages/theme/src/tokens/` como CSS custom properties e mapeada a um contexto de uso:

| Paleta | Classe CSS | Contexto |
|---|---|---|
| `floresta` | `.theme-floresta` | Institucional — B2B, landing, pitch |
| `oliva` | `.theme-oliva` | Dashboard admin/manager |
| `terra` | `.theme-terra` | App de campo — operador, Primata |
| `brisa` | `.theme-brisa` | Documentação técnica, portal dev |

O tenant configura a paleta via JSON servido pela API. O `ThemeProvider` aplica a classe no `<html>` automaticamente.

---

## Variáveis de ambiente

Crie `.env.local` dentro do app desejado:

```bash
# apps/dashboard/.env.local
VITE_API_URL=http://localhost:8000

# apps/portal/.env.local
VITE_API_URL=http://localhost:8000
```

Em desenvolvimento o proxy do Vite encaminha `/api → :8000` (dashboard) e `/p → :8000` (portal) sem precisar da variável.
