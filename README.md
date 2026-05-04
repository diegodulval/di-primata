# Di Mata

Plataforma de rastreabilidade de cadeia produtiva — agnóstica de setor.  
API REST em FastAPI · armazenamento in-memory · pronta para plugar ORM.

---

## Pré-requisitos

| Ferramenta | Versão mínima |
|---|---|
| Python | 3.12 |
| [uv](https://docs.astral.sh/uv/) | qualquer |
| Docker + Compose | opcional |

Instalar `uv` (caso não tenha):
```bash
wget -qO- https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

---

## Setup

```bash
# clone e entre no diretório
git clone <repo> di-mata && cd di-mata

# criar virtualenv Python 3.12 + instalar dependências de produção
make install

# adicionar dependências de desenvolvimento (pytest, ruff, coverage)
make dev

# instalar git hooks (obrigatório após clonar)
make hooks

# copiar arquivo de variáveis de ambiente
cp .env.example .env
```

---

## Rodando localmente

```bash
make run
# ou diretamente:
.venv/bin/uvicorn app.main:app --reload --port 8000
```

Acesse:
- **Swagger UI** → `http://localhost:8000/docs`
- **ReDoc** → `http://localhost:8000/redoc`
- **Health check** → `http://localhost:8000/health`

---

## Rodando com Docker

```bash
docker compose up --build
```

A API sobe na porta `8000`. Não há banco de dados externo — o estado vive em memória no processo.

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

| Variável | Padrão | Descrição |
|---|---|---|
| `APP_ENV` | `development` | Ambiente de execução |
| `SECRET_KEY` | *(inseguro)* | Chave de assinatura JWT — **trocar em produção** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Validade do token |

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

## Arquivos de referência

| Arquivo | Conteúdo |
|---|---|
| `dimata-requisitos.md` | Requisitos funcionais, entidades e regras de negócio |
| `dimata-uml.png` | Diagrama relacional (Core Universal) |
| `dimata-branding.html` | Identidade visual, paletas e posicionamento |
| `dimata-dashboard-admin.png` | Visão do painel administrativo |
