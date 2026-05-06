Plano: Whitelabel para a Camada de Visualização — Di Mata
Role: Staff Engineer | Horizonte: 3 fases | Escopo: frontend completo, design system tokenizado, multi-tenant

1. Diagnóstico & Restrições
O que existe hoje:

API FastAPI completa: auth, accounts, units, cycles, events, lots, portal público /p/{qr_hash}
Sistema de branding definido (dimata-branding.html): 4 paletas (Floresta, Oliva, Terra, Brisa), 4 pilares funcionais, tipografia (Nunito + Fira Code)
Mockup de dashboard admin (dimata-dashboard-admin.png) — referência visual
Zero frontend integrado; Swagger UI é a única UI atual
Restrições arquiteturais:

In-memory store hoje → troca futura para banco de dados real; frontend não deve assumir nada sobre latência ou paginação
Multi-tenant via account_id no JWT — whitelabel é a mesma codebase com theming por tenant
Portal QR é público (sem auth) — deve ser rápido, indexável, acessível
2. Decisões Técnicas Fundamentais
Stack de Frontend

React 19 + TypeScript
Vite (build)
TanStack Router (file-based routing, type-safe)
TanStack Query (server state, caching, optimistic updates)
Tailwind CSS v4 + CSS custom properties (tokens do design system)
shadcn/ui (base de componentes, headless, totalmente sobrescrevível)
Recharts (gráficos supply chain)
i18next (internacionalização — pt-BR default, EN ready)
Por que não Next.js: O portal QR precisa de SSR para SEO, mas o dashboard é SPA puro. Separar em dois apps é complexidade desnecessária agora. Vite + SSG/prerender resolve o portal; o resto é SPA.

Por que shadcn/ui: O whitelabel exige componentes que o tenant consegue substituir. shadcn copia o código para o repo — sem dependência de versão de lib de terceiro que bloqueia customização.

3. Arquitetura do Whitelabel
Modelo de Theming
O branding já define o mapeamento: cada paleta serve uma camada do produto. Traduzimos isso em CSS custom properties com troca por tenant via JSON de configuração.


theme/
├── tokens/
│   ├── base.css          ← variáveis raiz (radius, spacing, font-family)
│   ├── floresta.css      ← paleta institucional (B2B, landing)
│   ├── oliva.css         ← paleta dashboard admin/manager
│   ├── terra.css         ← paleta app operador/campo (Primata)
│   └── brisa.css         ← paleta técnica/API (dev portal)
├── tenant-config.ts      ← schema Zod do JSON de configuração por tenant
└── ThemeProvider.tsx     ← carrega tokens + logo + strings customizáveis
Como o tenant configura:


{
  "tenantId": "cooperativa-cacau-sul",
  "palette": "terra",
  "logoUrl": "/tenants/cacau-sul/logo.svg",
  "brandName": "Rastreio Cacau Sul",
  "primaryColor": "#7A4E2D",
  "modules": ["transparency", "integration"],
  "publicPortal": { "showMap": true, "certificationBadge": true }
}
Arquivo servido pelo próprio FastAPI em /tenants/{slug}/config — sem rebuildar o frontend.

4. Estrutura de Apps (Monorepo)

di-primata/
├── app/                          ← FastAPI (atual)
├── web/                          ← NEW: monorepo frontend
│   ├── apps/
│   │   ├── dashboard/            ← SPA: admin + manager + operator
│   │   └── portal/               ← Portal público QR (pre-renderizável)
│   ├── packages/
│   │   ├── ui/                   ← Design system: componentes base
│   │   ├── theme/                ← Tokens CSS + ThemeProvider
│   │   ├── api-client/           ← Cliente tipado gerado do OpenAPI
│   │   └── shared/               ← Types, utils, i18n
│   └── package.json              ← pnpm workspaces
Geração do cliente API: FastAPI expõe /openapi.json. Usamos openapi-typescript + openapi-fetch para gerar um cliente 100% tipado. Qualquer mudança na API quebra o build do frontend — segurança de contrato automática.

5. Mapa de Telas por Perfil
App Dashboard (autenticado)
Perfil	Telas
Admin	Contas, Usuários, Protocolos, Auditoria, Config Tenant
Manager	Unidades Produtivas, Ciclos, Lotes, Relatórios
Operator	Abertura de Ciclo, Registro de Eventos (Primata UI)
Viewer	Dashboard read-only, exportação
Visualizações de Dados (core do whitelabel)
Timeline de Ciclo — eventos em linha do tempo, cada etapa do protocolo com status de validação, ícone por tipo de evento (insumo, operação, QC, anomalia)
Grafo de Rastreabilidade — supply chain como DAG: fornecedor → insumo → lote. Usa React Flow ou D3 dependendo da complexidade
Mapa de Unidades — geolocalização das unidades produtivas (campo, talhão, linha) com GeoJSON se disponível
Dashboard de KPIs — ciclos abertos/fechados, taxa de conformidade de protocolo, anomalias, volume por período. Recharts.
Certificado de Lote — view imprimível do lote gerado, compatível com QR code
App Portal Público (sem auth)
Entrada pelo QR code (/p/{qr_hash})
Exibe: origem do produto, cadeia produtiva, certificações, rastreabilidade completa
Mobile-first (é escaneado por consumidor com celular)
Paleta configurável pelo tenant (pode ser Floresta para branding institucional forte)
Open Graph tags para compartilhamento social
6. Fases de Execução
Fase 1 — Foundation (Semanas 1–4)
Objetivo: Infraestrutura pronta, nenhum desenvolvedor bloqueado.

 Setup monorepo web/ com pnpm workspaces
 packages/theme — implementar os 4 tokens CSS, ThemeProvider, test visual com Storybook
 packages/api-client — script de geração do OpenAPI, CI quebra se contrato muda
 packages/ui — Button, Input, Badge, Card, Table, Skeleton, Toast (shadcn base)
 apps/dashboard — scaffolding: roteamento, autenticação (JWT storage seguro: httpOnly cookie via BFF ou memory only), layout base
 Endpoint GET /tenants/{slug}/config no FastAPI para servir tenant JSON
 Docker Compose atualizado com serviço web (nginx serving Vite build)
Critério de saída: Dev consegue logar no dashboard com o tenant "default" e ver uma tela em branco com o tema correto aplicado.

Fase 2 — Core Visualization (Semanas 5–10)
Objetivo: As 5 visualizações de dados funcionando ponta a ponta.

 Timeline de Ciclo com integração real de GET /cycles/{id}/events
 Dashboard KPIs — TanStack Query com polling configurável (dados em memória mudam ao vivo)
 Portal público /p/{qr_hash} — mobile-first, pre-renderizado, < 2s FCP
 Certificado de Lote (view + impressão CSS)
 Grafo de rastreabilidade (insumo → lote, Fase 2 pode ser mais simples: lista hierárquica com Recharts TreeMap; grafo D3 vai para Fase 3)
 Operator UI — formulário de registro de evento (tipo, payload, foto upload via multipart)
 Storybook documentando todos os componentes com variantes de tema
Critério de saída: Um tenant consegue abrir um ciclo, registrar eventos, gerar um lote e um consumidor consegue escanear o QR e ver a cadeia completa.

Fase 3 — Whitelabel Self-Service (Semanas 11–16)
Objetivo: Tenant consegue se configurar sem ajuda de engenharia.

 UI de configuração de tenant (customização de logo, cores primárias dentro da paleta, módulos habilitados)
 Grafo de rastreabilidade D3 (supply chain visual completo)
 Mapa de unidades produtivas (Leaflet.js com GeoJSON)
 Exportação de relatórios (PDF do certificado, CSV de eventos)
 Suporte a domínio customizado por tenant (nginx + CNAME)
 Internacionalização completa pt-BR / EN
 Documentação do whitelabel (como onboar um novo tenant em < 1 hora)
7. Decisões de Segurança (não negociáveis)
JWT storage: Memory only (React state + refresh token em httpOnly cookie). Nunca localStorage — XSS roubaria o token.
BFF pattern: Se precisar de refresh silencioso, adicionar um endpoint /auth/refresh no FastAPI que lê o cookie — frontend nunca vê o refresh token.
CSP: Content-Security-Policy header no nginx — bloquear inline scripts, restringir fontes.
Portal público: Rate limiting no nginx para /p/ — não deixar QR scraping em massa.
Tenant isolation: account_id do JWT deve validar que o tenant config carregado pertence ao usuário logado — não confiar só no slug da URL.
8. Métricas de Qualidade
Métrica	Target
Lighthouse Performance (portal QR)	≥ 90
First Contentful Paint (portal QR)	< 2s em 4G simulado
TypeScript strict mode	0 erros
Cobertura de testes (componentes críticos)	≥ 70%
Novo tenant onboardado	< 1h de trabalho de engenharia
Build time	< 60s
9. Riscos & Mitigações
Risco	Probabilidade	Mitigação
In-memory store sem paginação trava o frontend com dados grandes	Alta	TanStack Query com select para transformar + virtualização de listas (TanStack Virtual) desde o início
Contrato API quebra sem aviso	Média	CI gera cliente OpenAPI + build falha se tipos mudam
Tenant customiza além do permitido (CSS injection)	Baixa	Tenant config é JSON com schema Zod; cores passam por chroma.js para validar e gerar palette segura
Portal QR precisa de SEO antes da Fase 3	Alta	Pre-render com Vite SSG no início da Fase 2, não esperar Fase 3
10. Próximo Passo Imediato
A decisão mais crítica antes de codar qualquer linha: onde o tenant config vive.

Opção A: FastAPI como fonte da verdade (adicionar endpoint + model TenantConfig) — mais simples, config versionada junto com a API.
Opção B: Arquivo estático por tenant em web/public/tenants/ — mais rápido de servir, mas não pode ser editado pela UI da Fase 3.

Minha recomendação: Opção A. A Fase 3 depende de uma UI de configuração, então o config precisa ser persistido no backend desde o início. Custo: +1 model + 2 endpoints no FastAPI, ~2h de trabalho.

Quer que eu comece pela Fase 1 — setup do monorepo e dos tokens do design system? Ou prefere discutir alguma das decisões acima primeiro?

pyproject.toml
Vamos começar pela estrutura de apps item 4. Como lider e manutenedor elabore um plano para criaçao do scafolding basico para receber o web.
Vou ler os arquivos de configuração antes de planejar o scaffolding.

Read pyproject.toml
Read docker-compose.yml
Read Makefile
Read main.py
Bash List git hooks and read pre-commit hook
IN
ls /home/dd/di-primata/.githooks/ && cat /home/dd/di-primata/.githooks/pre-commit

OUT
commit-msg
pre-commit
pre-push
#!/bin/sh
# Executado antes de cada commit.
# Falha se lint, formatação ou testes falharem.

set -e

VENV=".venv/bin"

if [ ! -d ".venv" ]; then
  echo "❌  Virtualenv não encontrado. Rode: make dev"
  exit 1
fi

echo "🔍  lint (ruff check)..."
$VENV/ruff check app tests

echo "🎨  format (ruff format --check)..."
$VENV/ruff format --check app tests

echo "🧪  testes (pytest -q)..."
$VENV/pytest -q --tb=short

echo "✅  pre-commit OK"
Agora tenho tudo. Vou elaborar o plano de scaffolding como um líder técnico — concreto, ordenado, sem ambiguidade.

Plano de Scaffolding: web/
Princípio: nenhum desenvolvedor deve precisar tomar decisão de tooling. O scaffolding entrega estrutura, convenções e um pnpm dev que funciona end-to-end.

Pré-requisitos (verificar antes de começar)

node --version   # >= 22 LTS
pnpm --version   # >= 9.x   (corepack enable && corepack prepare pnpm@latest)
O projeto Python usa uv com filosofia de tooling rápido — no JS vamos seguir o mesmo padrão: pnpm + Biome (substitui ESLint + Prettier, assim como ruff substitui flake8 + black).

Estrutura Final Esperada

di-primata/
├── app/                          ← FastAPI (sem mudanças)
├── web/
│   ├── package.json              ← pnpm workspace root
│   ├── pnpm-workspace.yaml
│   ├── biome.json                ← lint + format (substitui ESLint+Prettier)
│   ├── tsconfig.base.json        ← strict mode compartilhado
│   │
│   ├── packages/
│   │   ├── theme/                ← tokens CSS + ThemeProvider
│   │   │   ├── package.json
│   │   │   ├── src/
│   │   │   │   ├── tokens/
│   │   │   │   │   ├── base.css
│   │   │   │   │   ├── floresta.css
│   │   │   │   │   ├── oliva.css
│   │   │   │   │   ├── terra.css
│   │   │   │   │   └── brisa.css
│   │   │   │   ├── ThemeProvider.tsx
│   │   │   │   └── index.ts
│   │   │   └── tsconfig.json
│   │   │
│   │   ├── shared/               ← types, utils, i18n, constants
│   │   │   ├── package.json
│   │   │   ├── src/
│   │   │   │   ├── types/        ← types de domínio compartilhados
│   │   │   │   └── index.ts
│   │   │   └── tsconfig.json
│   │   │
│   │   ├── api-client/           ← cliente tipado gerado do OpenAPI
│   │   │   ├── package.json
│   │   │   ├── scripts/
│   │   │   │   └── generate.ts   ← chama openapi-typescript
│   │   │   ├── src/
│   │   │   │   ├── generated/    ← NUNCA editar manualmente
│   │   │   │   └── client.ts     ← instância configurada do openapi-fetch
│   │   │   └── tsconfig.json
│   │   │
│   │   └── ui/                   ← componentes base (shadcn)
│   │       ├── package.json
│   │       ├── src/
│   │       │   ├── components/
│   │       │   │   └── .gitkeep  ← shadcn vai popular aqui
│   │       │   └── index.ts
│   │       └── tsconfig.json
│   │
│   └── apps/
│       ├── portal/               ← portal QR público (mobile-first)
│       │   ├── package.json
│       │   ├── vite.config.ts
│       │   ├── tsconfig.json
│       │   ├── index.html
│       │   └── src/
│       │       ├── main.tsx
│       │       ├── App.tsx
│       │       └── routes/
│       │           └── p.$hash.tsx   ← rota /p/:hash (TanStack Router)
│       │
│       └── dashboard/            ← SPA admin/manager/operator
│           ├── package.json
│           ├── vite.config.ts
│           ├── tsconfig.json
│           ├── index.html
│           └── src/
│               ├── main.tsx
│               ├── App.tsx
│               └── routes/
│                   ├── __root.tsx
│                   ├── index.tsx     ← redirect para /dashboard
│                   ├── login.tsx
│                   └── dashboard/
│                       └── index.tsx
Sequência de Execução
Etapa 1 — Workspace Root
Responsável: líder técnico (setup feito uma vez)

Criar web/package.json — workspace root, sem código próprio:


{
  "name": "di-mata-web",
  "private": true,
  "engines": { "node": ">=22", "pnpm": ">=9" },
  "scripts": {
    "dev": "pnpm --filter dashboard dev & pnpm --filter portal dev",
    "build": "pnpm -r build",
    "check": "biome check .",
    "fmt": "biome format --write .",
    "typecheck": "pnpm -r typecheck",
    "generate:api": "pnpm --filter api-client generate"
  }
}
Criar web/pnpm-workspace.yaml:


packages:
  - "apps/*"
  - "packages/*"
Criar web/biome.json — configuração única de lint + format:


{
  "$schema": "https://biomejs.dev/schemas/1.9.0/schema.json",
  "organizeImports": { "enabled": true },
  "linter": {
    "enabled": true,
    "rules": { "recommended": true }
  },
  "formatter": {
    "indentStyle": "space",
    "indentWidth": 2,
    "lineWidth": 100
  },
  "javascript": {
    "formatter": { "quoteStyle": "double" }
  }
}
Criar web/tsconfig.base.json — TypeScript strict compartilhado:


{
  "compilerOptions": {
    "strict": true,
    "exactOptionalPropertyTypes": true,
    "noUncheckedIndexedAccess": true,
    "moduleDetection": "force",
    "jsx": "react-jsx",
    "esModuleInterop": true,
    "skipLibCheck": true,
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true
  }
}
Etapa 2 — Package theme
Prioridade: alta — bloqueia qualquer trabalho de UI.

Dependências: react, @types/react
Entrega mínima para desbloquear equipe:

Os 4 arquivos CSS de tokens com as variáveis do dimata-branding.html traduzidas para --color-*, --font-*, --radius-*
ThemeProvider que lê o JSON de config do tenant e aplica a classe CSS correta no <html>
Export limpo pelo index.ts
O token --color-primary por exemplo troca de valor dependendo da paleta ativa — Tailwind v4 vai consumir essas variáveis diretamente via @theme.

Etapa 3 — Package shared
Prioridade: média — necessário antes dos apps, mas não bloqueia theme.

Conteúdo inicial mínimo:

Tipos TypeScript espelhando os enums do backend (app/models/enums.py): StatusCiclo, TipoEvento, TipoUnidade, etc.
Constante API_BASE_URL configurável via import.meta.env
Utilitário formatDate (pt-BR por padrão)
Regra: shared não importa de ui, theme ou api-client. Dependência unidirecional.

Etapa 4 — Package api-client
Prioridade: alta — desbloqueia qualquer tela com dado real.

Dependências: openapi-typescript, openapi-fetch, tsx (para rodar o script de geração)

Script generate.ts faz:


GET http://localhost:8000/openapi.json → salva em src/generated/schema.ts
client.ts exporta uma instância configurada com baseUrl e Authorization header:


export const api = createClient<paths>({
  baseUrl: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
});
Contrato de qualidade: o script de geração entra no pnpm check do CI. Build falha se o schema da API mudou e o cliente não foi regenerado.

Etapa 5 — Package ui
Prioridade: baixa no scaffolding — shadcn é instalado depois.

Scaffolding mínimo:

components/ vazio com .gitkeep
index.ts vazio
package.json com re-export de @radix-ui/react-slot (dependência base do shadcn)
Após scaffold, rodar pnpm dlx shadcn@latest init dentro de packages/ui com estilo "New York" e variáveis CSS. Os primeiros componentes a adicionar: Button, Card, Badge, Skeleton, Table.

Etapa 6 — App portal
Prioridade: alta — é a entrega mais crítica para o produto (QR do consumidor).

Setup:


cd web/apps/portal
pnpm create vite . --template react-ts
pnpm add @tanstack/react-router
pnpm add -D tailwindcss @tailwindcss/vite vite-plugin-ssr
Rota inicial: web/apps/portal/src/routes/p.$hash.tsx

Recebe hash da URL
Chama GET /p/{hash} via api-client
Renderiza skeleton enquanto carrega
Aplica tema do tenant (lido do JSON de config)
vite.config.ts do portal já configura o proxy para /api → http://localhost:8000 em dev.

Etapa 7 — App dashboard
Prioridade: média — mais complexo, pode começar após portal estar funcional.

Setup similar ao portal, com adição:


pnpm add @tanstack/react-router @tanstack/react-query
pnpm add -D @tanstack/router-devtools @tanstack/react-query-devtools
Rotas iniciais mínimas:

/login — form de auth, chama POST /auth/login, guarda token em memória
/dashboard — protegida, redireciona para /login se sem token
/dashboard/cycles — placeholder
__root.tsx define o layout base: sidebar + topbar. O componente de sidebar já recebe a config do tenant para esconder módulos não habilitados.

Etapa 8 — Infraestrutura
Makefile — adicionar ao Makefile existente:


web-install:
    cd web && pnpm install

web-dev:
    cd web && pnpm dev

web-build:
    cd web && pnpm build

web-check:
    cd web && pnpm check && pnpm typecheck
Docker Compose — adicionar serviço web ao docker-compose.yml:


web:
  image: node:22-alpine
  working_dir: /app/web
  command: pnpm dev
  ports:
    - "5173:5173"   # dashboard
    - "5174:5174"   # portal
  volumes:
    - .:/app
  depends_on:
    - api
CORS no FastAPI — allow_origins=["*"] é aceitável em dev, mas antes da Fase 2 trocar para:


allow_origins=[
    "http://localhost:5173",
    "http://localhost:5174",
    os.getenv("FRONTEND_URL", ""),
]
Git hook — adicionar ao .githooks/pre-commit existente:


if [ -d "web/node_modules" ]; then
  echo "🔍  web: biome check..."
  cd web && pnpm check && pnpm typecheck
  cd ..
fi
Critério de Saída do Scaffolding
O scaffolding está completo quando um desenvolvedor novo consegue:

git clone + make dev → API rodando em :8000
cd web && pnpm install && pnpm dev → dashboard em :5173, portal em :5174
Acessar http://localhost:5173/login e ver tela (mesmo que vazia)
Acessar http://localhost:5174/p/qualquer-hash e ver skeleton (mesmo que API retorne 404)
pnpm typecheck → 0 erros
pnpm check → 0 warnings de lint
Ordem de Implementação (por desbloqueio)

1. Workspace root (Etapa 1)       ← ninguém pode trabalhar sem isso
2. shared + theme (Etapas 2-3)    ← paralelo, sem dependência entre si
3. api-client (Etapa 4)           ← depende de shared para os tipos
4. ui (Etapa 5)                   ← paralelo com api-client
5. portal (Etapa 6)               ← depende de theme + api-client
6. dashboard (Etapa 7)            ← depende de ui + api-client + theme
7. Infra (Etapa 8)                ← pode ir junto com portal
Quer que eu execute a implementação do scaffolding agora, começando pela Etapa 1 (workspace root) e avançando em sequência?
