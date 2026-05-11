# Di Mata

Plataforma de rastreabilidade de cadeia produtiva — agnóstica de setor.  
API REST em FastAPI · armazenamento in-memory · pronta para plugar ORM.

---

## Pré-requisitos

| Ferramenta | Versão mínima | Usado por |
|---|---|---|
| Python | 3.12 | API |
| [uv](https://docs.astral.sh/uv/) | qualquer | API |
| Node.js | 22 LTS | Frontend |
| pnpm | 9 | Frontend |
| Docker + Compose | opcional | Ambos |

Instalar `uv` (caso não tenha):
```bash
wget -qO- https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

Instalar Node.js 22 + pnpm via nvm (caso não tenha):
```bash
wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
source ~/.bashrc
nvm install 22
corepack enable && corepack prepare pnpm@latest --activate
```

---

## Setup

```bash
# clone e entre no diretório
git clone <repo> di-mata && cd di-mata

# copiar arquivo de variáveis de ambiente
cp .env.example .env

# ── API ────────────────────────────────────────────────────────────────────────
# criar virtualenv Python 3.12 + instalar dependências de produção
make install

# adicionar dependências de desenvolvimento (pytest, ruff, coverage)
make dev

# instalar git hooks (obrigatório após clonar)
make hooks

# ── Frontend ───────────────────────────────────────────────────────────────────
make web-install
```

---

## Rodando localmente

Execute cada ambiente em um terminal separado:

**Terminal 1 — API:**
```bash
make run
```

**Terminal 2 — Frontend:**
```bash
make web-dev
```

**Na primeira vez**, gere o cliente tipado da API (API deve estar no ar):
```bash
make web-generate
```

| Interface | URL | Descrição |
|---|---|---|
| Dashboard | `http://localhost:5173` | SPA autenticado (admin / manager / operador) |
| Portal QR | `http://localhost:5174/p/{hash}` | Portal público do consumidor |
| Swagger UI | `http://localhost:8000/docs` | Documentação interativa da API |
| ReDoc | `http://localhost:8000/redoc` | Documentação da API em formato ReDoc |
| Health check | `http://localhost:8000/health` | Status da API |

---

## Rodando com Docker

```bash
docker compose up --build
```

Sobe a API na porta `8000` e o frontend nas portas `5173` (dashboard) e `5174` (portal).  
Não há banco de dados externo — o estado vive em memória no processo.

---

## Seed de desenvolvimento

Popula a API com 3 tenants, usuários, ciclos e um lote publicado com QR escaneável.  
Execute sempre que reiniciar a API (o estado é in-memory).

```bash
make run     # Terminal 1 — API
make seed    # Terminal 2 — seed (aguarda API subir)
make web-dev # Terminal 3 — frontend
```

O seed imprime no terminal todas as credenciais e a URL do portal QR público.  
Documentação completa em [`docs/dev-access.md`](docs/dev-access.md).

---

## Testes

### Executar todos os testes

```bash
make test
# ou:
.venv/bin/pytest
```

### Com relatório de cobertura

```bash
make cov
# ou:
.venv/bin/pytest --cov=app --cov-report=term-missing --cov-report=html
```

O relatório HTML é gerado em `htmlcov/index.html`.  
A cobertura mínima configurada é **70%** — o comando falha abaixo disso.

### Estrutura dos testes

```
tests/
├── conftest.py              # fixtures compartilhadas: store, client, auth_headers, seeded
├── unit/
│   ├── test_auth_service.py # register, login, duplicata, senha errada
│   ├── test_cycle_service.py# criação, máquina de estados, eventos, etapas faltantes
│   └── test_lot_service.py  # geração de lote, QR, publicação, portal público
└── integration/
    └── test_cycle_flow.py   # golden path HTTP completo: register → QR scan
```

### Fixtures principais

| Fixture | Escopo | O que fornece |
|---|---|---|
| `store` | função | `Store` vazio e isolado por teste |
| `client` | função | `TestClient` com `store` injetado via `dependency_overrides` |
| `seeded` | função | store com account + user + unit + protocol pré-criados |
| `auth_headers` | função | `{"Authorization": "Bearer <token>"}` via `/auth/register` |

Cada teste recebe seu próprio `store` — **sem estado compartilhado entre testes**.

### Rodar apenas um módulo

```bash
.venv/bin/pytest tests/unit/test_cycle_service.py -v
```

### Rodar apenas um teste

```bash
.venv/bin/pytest tests/integration/test_cycle_flow.py::test_golden_path_completo -v
```

---

## Git Hooks

Os hooks ficam em `.githooks/` e são ativados com `make hooks` (usa `git config core.hooksPath`).  
**Rode `make hooks` uma vez após clonar o repositório.**

| Hook | Quando dispara | O que faz |
|---|---|---|
| `pre-commit` | `git commit` | ruff lint → ruff format check → pytest |
| `commit-msg` | `git commit` | valida formato Conventional Commits |
| `pre-push` | `git push` | valida nome da branch |

### Conventional Commits

```
<tipo>(<escopo opcional>): <descrição>

feat(auth): adicionar refresh token
fix(lot): corrigir geração de QR vazia
chore: atualizar dependências
docs: expandir README com seção de hooks
test(cycle): cobrir transições inválidas
```

Tipos aceitos: `feat` · `fix` · `docs` · `style` · `refactor` · `test` · `chore` · `ci` · `perf` · `build` · `revert`

### Nomenclatura de branches

```
main                    # produção
develop                 # integração contínua
feat/<descricao>        # nova funcionalidade
fix/<descricao>         # correção de bug
chore/<descricao>       # manutenção
docs/<descricao>        # documentação
test/<descricao>        # testes
refactor/<descricao>    # refatoração
ci/<descricao>          # pipeline
release/<versao>        # ex: release/1.2.0
```

Descrição em kebab-case, ex: `feat/autenticacao-jwt`.

---

## Linter

O projeto usa [Ruff](https://docs.astral.sh/ruff/) — checagem e formatação em um único binário.

```bash
# verificar erros e avisos
make lint

# formatar automaticamente
make fmt

# lint + testes + coverage em sequência
make check
```

Regras ativas: `E`, `W` (pycodestyle) · `F` (pyflakes) · `I` (isort) · `B` (bugbear) · `UP` (pyupgrade).  
Configuração completa em `pyproject.toml` → `[tool.ruff]`.

---

## Variáveis de ambiente

Copie `.env.example` para `.env` e ajuste os valores.

**API (`/.env`):**

| Variável | Padrão | Descrição |
|---|---|---|
| `APP_ENV` | `development` | Ambiente de execução |
| `SECRET_KEY` | *(inseguro)* | Chave de assinatura JWT — **trocar em produção** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Validade do token |
| `FRONT
POST /END_URL` | *(vazio)* | URL do frontend em produção — adicionada ao CORS |

**Frontend (`/web/apps/dashboard/.env.local` e `/web/apps/portal/.env.local`):**

| Variável | Padrão | Descrição |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | URL base da API |

---

## Fluxo principal da API

```
POST /auth/register          # cria account + usuário admin → retorna JWT
POST /auth/login             # retorna JWT

POST /units                  # cria unidade produtiva
POST /units/protocols        # cria protocolo com etapas obrigatórias

POST /cycles                 # abre ciclo produtivo (status: ABERTO)
POST /cycles/{id}/events     # registra evento no ciclo
PATCH /cycles/{id}/status    # avança estado: ABERTO→EM_PRODUCAO→ENCERRADO→VALIDANDO

POST /cycles/{id}/lots       # gera lote + QR (valida protocolo completo)
POST /cycles/lots/{id}/publish

GET  /p/{qr_hash}            # portal público — sem autenticação
```

---

## Integração WhatsApp (Twilio Sandbox)

Esta seção explica como conectar o webhook do WhatsApp ao Twilio durante o desenvolvimento local.

### 1. Pré-requisito: API rodando

```bash
make run   # API em http://localhost:8000
```

### 2. Expor a API com Cloudflare Tunnel

O Twilio precisa de uma URL pública para entregar mensagens. Use o `cloudflared` para criar um tunnel temporário sem precisar de conta:

```bash
# baixar o binário (apenas uma vez)
wget -O /tmp/cloudflared https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x /tmp/cloudflared

# iniciar o tunnel
/tmp/cloudflared tunnel --url http://localhost:8000 --no-autoupdate
```

O terminal exibirá uma linha como:

```
INF  +--------------------------------------------------------------------------------------------+
INF  |  Your quick Tunnel has been created! Visit it at (it may take some time to be reachable): |
INF  |  https://lending-practitioner-navigation-bird.trycloudflare.com                           |
INF  +--------------------------------------------------------------------------------------------+
```

Copie essa URL — ela muda a cada reinicialização.

### 3. Configurar no Twilio Console

Acesse [console.twilio.com](https://console.twilio.com) → **Messaging → Try it out → Send a WhatsApp message → Sandbox Settings** e preencha:

| Campo | Valor |
|---|---|
| **When a message comes in** | `https://<sua-url>/whatsapp/webhook` |
| **Status callback URL** | `https://<sua-url>/whatsapp/status` |

Ambos usam método **HTTP POST**.

### 4. Variáveis de ambiente (.env)

```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_FROM=+14155238886
TWILIO_VALIDATE_SIGNATURE=False   # True somente em produção
```

### 5. Testar

Envie qualquer mensagem para o número do sandbox no WhatsApp. O terminal da API mostrará os logs de entrada. O bot responde com o menu inicial.

> **Atenção:** A URL do tunnel é descartável — muda toda vez que você reinicia o `cloudflared`. Atualize o Twilio Console sempre que isso acontecer.

---

## Arquivos de referência

| Arquivo | Conteúdo |
|---|---|
| `dimata-requisitos.md` | Requisitos funcionais, entidades e regras de negócio |
| `dimata-uml.png` | Diagrama relacional (Core Universal) |
| `dimata-branding.html` | Identidade visual, paletas e posicionamento |
| `dimata-dashboard-admin.png` | Visão do painel administrativo |
