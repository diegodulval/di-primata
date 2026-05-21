# CLAUDE.md — DiAuto - Sistema de Gestão de Oficina Mecânica & Auto Peças

> Leia este arquivo inteiro antes de qualquer tarefa.
> Ele define não só o que construir, mas **como pensar** antes de escrever qualquer linha.

---

## 0. Princípios que governam cada decisão

Antes de escrever qualquer código, responda mentalmente:

### KISS — Keep It Simple, Stupid
> "A solução mais simples que funciona é a correta."

- Se você está cogitando adicionar uma fila, um cache ou um serviço extra: pare. Existe uma forma mais simples?
- Funções com mais de 30 linhas provavelmente estão fazendo coisas demais.
- Se você precisar comentar o que um bloco de código faz, considere extrair para uma função com nome claro.

### YAGNI — You Aren't Gonna Need It
> "Não construa o que não foi pedido ainda."

- Sem abstrações para casos futuros hipotéticos.
- Sem parâmetros de configuração que ninguém vai usar no MVP.
- Sem suporte a múltiplas estratégias antes de ter uma funcionando.
- A lista de tarefas futura está na seção 11. Deixe lá.

### DRY — Don't Repeat Yourself
> "Cada pedaço de conhecimento tem uma única representação."

- Lógica de negócio vive no `service`, nunca duplicada no `router` e no `worker`.
- Queries repetidas viram métodos no repositório, não copiadas entre endpoints.
- Constantes (status, perfis, tipos) vivem em um único `enums.py` por módulo.
- DRY é sobre **conhecimento**, não sobre linhas de código. Duas linhas similares podem ser coincidência; duas regras de negócio iguais em lugares diferentes são um problema.

### Mantenha a Visão
> "Cada arquivo escrito deve fazer sentido para o sistema como um todo."

- A visão está na seção 1. Releia antes de cada tarefa.
- Ao propor uma solução, pergunte: isso se encaixa ou cria uma exceção?
- Nomenclatura consistente é parte da visão: `tenant_id` é sempre `tenant_id`, nunca `org_id`, `company_id` ou `loja`.

### Fique em Construção de Testes
> "Código sem teste não está pronto, está rascunhado."

- Todo `service` tem `tests/test_<modulo>_service.py` antes de ser considerado entregue.
- Testes de regras de negócio primeiro (unitários). Testes de rota depois (integração).
- Use `pytest` + `pytest-asyncio`. Fixtures de banco usam schema de teste isolado.
- Um teste que passa sem verificar nada é pior que nenhum teste. Seja específico.
- Red → Green → Refactor. Nessa ordem.

### Os Doze Fatores (The Twelve-Factor App)
> "Aplicações bem-comportadas são fáceis de operar, escalar e depurar."

Aplicados ao contexto deste projeto:

| Fator | Aplicação aqui |
|-------|---------------|
| **I. Codebase** | Um repositório, um app. Sem submodules no MVP. |
| **II. Dependências** | `requirements.txt` explícito. Sem dependências implícitas do sistema. |
| **III. Config** | Toda config vem de variável de ambiente via `.env`. Zero hardcode de URLs, senhas ou tokens. |
| **IV. Backing services** | PostgreSQL é um recurso anexo — `DATABASE_URL` muda, o código não. |
| **V. Build/Release/Run** | `docker compose build` (build) → imagem versionada (release) → `docker compose up` (run). Separados. |
| **VI. Processos** | O backend é stateless. Estado de sessão fica no banco (`agente_sessao`). Matar e reiniciar o container não perde nada. |
| **VII. Port binding** | FastAPI expõe porta 8000. Nginx faz o proxy. Nenhum servidor externo embutido. |
| **VIII. Concorrência** | Escala por réplica do container, não por threads internas. No MVP: 1 réplica é suficiente. |
| **IX. Descartabilidade** | Startup < 5s. Shutdown graceful com `SIGTERM`. Sem estado em memória que não pode ser perdido. |
| **X. Dev/Prod parity** | `docker compose` local é idêntico ao da VPS. Sem "funciona na minha máquina". |
| **XI. Logs** | Logs vão para `stdout` em JSON. Nunca para arquivo dentro do container. `docker compose logs` resolve. |
| **XII. Admin processes** | Migrations são um processo separado (`python -m migrations`), não rodam no startup do app. |

---

## 1. Visão do Produto

SaaS multi-tenant para gestão de oficinas mecânicas e auto peças.
MVP focado em **uma loja**, arquitetura preparada para crescer sem reescrever.

**O que nos diferencia:**
- Veículo é entidade global — consulta por placa funciona entre tenants
- Histórico do veículo persiste quando troca de dono ou de oficina
- Compartilhamento do histórico é opt-in por OS
- Mecânico de campo abre OS via WhatsApp em linguagem natural (agente Claude)

**O que não somos** (YAGNI — não construa isso ainda):
- Não somos ERP financeiro completo
- Não temos marketplace de peças
- Não temos app nativo iOS/Android
- Não temos multi-filial no MVP

---

## 2. Stack — Mínimo Operável

| Camada | Tecnologia | Por quê esta, não outra |
|--------|-----------|------------------------|
| Backend | Python 3.12 + FastAPI | Async nativo, tipagem, ecossistema fiscal |
| Banco | PostgreSQL 16 | Um banco faz tudo: dados, sessão do agente, RLS |
| Frontend | React 18 + Vite + TypeScript | PWA, responsivo, build estático servido pelo nginx |
| Agente IA | claude-sonnet-4 via HTTP | Tool use nativo, custo por uso, sem infra extra |
| Infra | Docker Compose numa VPS | Simples de operar, backup trivial, sem vendor lock-in |
| Proxy | Nginx | HTTPS Let's Encrypt + serve frontend |
| Backup | `pg_dump` via cron no container `pgbackup` | Uma linha para restaurar |
| Secrets | `.env` na VPS, fora do repositório | KISS: sem Secret Manager no MVP |
| CI/CD | GitHub Actions → SSH + docker compose | Zero dependência de plataforma adicional |
| Fiscal | nfelib + certificado A1 em `/secrets/` | Padrão do mercado, bem documentado |

**Não existe nesta stack** (e não vai existir sem uma razão concreta):
Redis · Pub/Sub · Cloud Run · Kubernetes · Secret Manager · Celery · RabbitMQ · S3

---

## 3. Estrutura de Diretórios

```
.
├── CLAUDE.md
├── docker-compose.yml
├── nginx.conf
├── .env.example              ← template documentado, nunca commitar .env
├── backend/
│   ├── main.py               ← app factory: registra routers, middlewares
│   ├── core/
│   │   ├── config.py         ← Settings via pydantic-settings lendo .env
│   │   ├── database.py       ← engine async, session factory, RLS middleware
│   │   ├── security.py       ← JWT, RBAC, get_usuario_atual
│   │   ├── enums.py          ← StatusOS, TipoMov, Perfil — fonte única de verdade
│   │   └── exceptions.py     ← exceções de domínio (NaoEncontrado, EstoqueInsuficiente…)
│   ├── modules/
│   │   ├── iam/
│   │   │   ├── router.py
│   │   │   ├── service.py    ← regras de negócio aqui, nunca no router
│   │   │   ├── schemas.py    ← Pydantic: request/response, sem lógica
│   │   │   ├── models.py     ← SQLAlchemy ORM
│   │   │   └── tests/
│   │   │       └── test_iam_service.py
│   │   ├── cadastros/
│   │   ├── estoque/
│   │   ├── vendas/
│   │   └── ordens_servico/
│   ├── shared/
│   │   ├── veiculo_global/   ← schema global, sem tenant_id
│   │   ├── fiscal/           ← NF-e, NFCe, SEFAZ
│   │   └── notificacoes/     ← WhatsApp e e-mail: HTTP simples
│   └── agente/
│       ├── webhook.py        ← recebe POST Meta, valida HMAC, chama worker
│       ├── worker.py         ← monta contexto, chama Claude, executa tools
│       ├── tools.py          ← definição + execução das tools
│       ├── sessao.py         ← lê/salva histórico na tabela agente_sessao
│       └── prompts.py        ← system prompt
├── frontend/
│   └── src/
│       ├── modules/          ← espelha módulos do backend
│       ├── components/       ← componentes compartilhados
│       └── lib/              ← api client, auth, hooks
├── migrations/               ← SQL puro, executado em ordem, idempotente
│   ├── 001_global_schema.sql
│   ├── 002_tenant_schema.sql
│   ├── 003_rls_policies.sql
│   └── 004_seed.sql
└── .github/
    └── workflows/
        ├── ci.yml            ← lint (ruff) + tipos (mypy) + testes (pytest)
        └── deploy.yml        ← SSH na VPS + git pull + docker compose up
```

**Regra de ouro da estrutura:**
- Router → valida input, chama service, retorna output. Sem lógica.
- Service → regras de negócio. Sem HTTP, sem ORM direto.
- Model → mapeamento ORM. Sem lógica de negócio.
- Schema → contrato de API. Sem acesso a banco.

---

## 4. Modelo de Dados

### 4.1 Dois schemas no mesmo PostgreSQL (Fator IV)

```
banco: oficina
├── schema: global   ← entidades cross-tenant, sem RLS
│   ├── veiculo
│   └── historico_veiculo
└── schema: public   ← todas as entidades tenant-scoped, com RLS
    ├── tenant · usuario · cliente · cliente_veiculo
    ├── produto · fornecedor · entrada_nfe · item_entrada
    ├── ordem_servico · item_os
    ├── venda · item_venda · nota_fiscal_saida
    ├── movimentacao_estoque
    └── agente_sessao
```

### 4.2 DDL

```sql
-- migrations/001_global_schema.sql
CREATE SCHEMA IF NOT EXISTS global;

CREATE TABLE global.veiculo (
  id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  placa     VARCHAR(8) UNIQUE NOT NULL,
  chassi    VARCHAR(17),
  marca     TEXT,
  modelo    TEXT,
  ano_fab   SMALLINT,
  ano_mod   SMALLINT,
  cor       TEXT,
  tipo      TEXT CHECK (tipo IN ('carro','moto','caminhao','van')),
  criado_em TIMESTAMPTZ DEFAULT now()
);

-- Append-only. NUNCA UPDATE ou DELETE. É a memória do veículo.
CREATE TABLE global.historico_veiculo (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  veiculo_id      UUID NOT NULL REFERENCES global.veiculo(id),
  tenant_id       UUID NOT NULL,
  os_id           UUID,
  data_servico    DATE NOT NULL,
  km_entrada      INTEGER,
  resumo_publico  TEXT,           -- NULL se opt-in=false
  detalhe_privado TEXT NOT NULL,  -- sempre populado, visível só ao tenant
  criado_em       TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX ON global.historico_veiculo(veiculo_id);
```

```sql
-- migrations/002_tenant_schema.sql

CREATE TABLE tenant (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  razao_social      TEXT NOT NULL,
  cnpj              VARCHAR(14) UNIQUE NOT NULL,
  regime_tributario TEXT CHECK (regime_tributario IN
                      ('simples','lucro_presumido','lucro_real')),
  ativo             BOOLEAN DEFAULT true,
  criado_em         TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE usuario (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id        UUID NOT NULL REFERENCES tenant(id),
  nome             TEXT NOT NULL,
  email            TEXT NOT NULL,
  senha_hash       TEXT NOT NULL,
  perfil           TEXT NOT NULL CHECK (perfil IN ('ADMIN','ATENDENTE','MECANICO')),
  numero_whatsapp  VARCHAR(20) UNIQUE,
  ativo            BOOLEAN DEFAULT true,
  criado_em        TIMESTAMPTZ DEFAULT now(),
  UNIQUE(email, tenant_id)
);

CREATE TABLE cliente (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id  UUID NOT NULL REFERENCES tenant(id),
  nome       TEXT NOT NULL,
  cpf_cnpj   VARCHAR(14),
  telefone   VARCHAR(20),
  email      TEXT,
  endereco   TEXT,
  criado_em  TIMESTAMPTZ DEFAULT now()
);

-- Histórico de posse — data_fim NULL significa dono atual neste tenant
CREATE TABLE cliente_veiculo (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id   UUID NOT NULL REFERENCES tenant(id),
  cliente_id  UUID NOT NULL REFERENCES cliente(id),
  veiculo_id  UUID NOT NULL,
  data_inicio DATE NOT NULL DEFAULT CURRENT_DATE,
  data_fim    DATE,
  ativo       BOOLEAN DEFAULT true
);
CREATE INDEX ON cliente_veiculo(veiculo_id, tenant_id);

CREATE TABLE fornecedor (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id    UUID NOT NULL REFERENCES tenant(id),
  razao_social TEXT NOT NULL,
  cnpj         VARCHAR(14),
  contato      TEXT
);

CREATE TABLE produto (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id      UUID NOT NULL REFERENCES tenant(id),
  codigo         TEXT NOT NULL,
  descricao      TEXT NOT NULL,
  ncm            VARCHAR(8),
  marca          TEXT,
  localizacao    TEXT,
  preco_custo    NUMERIC(12,2) NOT NULL DEFAULT 0,
  preco_venda    NUMERIC(12,2) NOT NULL DEFAULT 0,
  estoque_atual  NUMERIC(12,3) DEFAULT 0,
  estoque_minimo NUMERIC(12,3) DEFAULT 0,
  estoque_maximo NUMERIC(12,3) DEFAULT 0,
  ativo          BOOLEAN DEFAULT true,
  UNIQUE(codigo, tenant_id)
);

CREATE TABLE entrada_nfe (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id     UUID NOT NULL REFERENCES tenant(id),
  fornecedor_id UUID REFERENCES fornecedor(id),
  chave_nfe     VARCHAR(44) UNIQUE,
  numero_nf     TEXT,
  data_emissao  DATE,
  valor_total   NUMERIC(12,2),
  xml_path      TEXT,
  status        TEXT DEFAULT 'processada',
  criado_em     TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE item_entrada (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entrada_id        UUID NOT NULL REFERENCES entrada_nfe(id),
  produto_id        UUID REFERENCES produto(id),
  codigo_fornecedor TEXT,
  quantidade        NUMERIC(12,3) NOT NULL,
  preco_unitario    NUMERIC(12,2) NOT NULL,
  icms              NUMERIC(5,2) DEFAULT 0,
  ipi               NUMERIC(5,2) DEFAULT 0
);

CREATE TABLE ordem_servico (
  id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id              UUID NOT NULL REFERENCES tenant(id),
  cliente_id             UUID NOT NULL REFERENCES cliente(id),
  veiculo_id             UUID NOT NULL,
  mecanico_id            UUID NOT NULL REFERENCES usuario(id),
  numero_os              TEXT NOT NULL,
  km_entrada             INTEGER,
  descricao_problema     TEXT NOT NULL,
  status                 TEXT NOT NULL DEFAULT 'ABERTA'
                           CHECK (status IN
                             ('ABERTA','EM_EXECUCAO','AGUARDANDO_PECA','FECHADA','CANCELADA')),
  compartilhar_historico BOOLEAN NOT NULL DEFAULT false,
  aberta_em              TIMESTAMPTZ DEFAULT now(),
  fechada_em             TIMESTAMPTZ,
  total_pecas            NUMERIC(12,2) DEFAULT 0,
  total_servicos         NUMERIC(12,2) DEFAULT 0,
  desconto               NUMERIC(12,2) DEFAULT 0,
  total_final            NUMERIC(12,2) DEFAULT 0,
  UNIQUE(numero_os, tenant_id)
);

CREATE TABLE item_os (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  os_id          UUID NOT NULL REFERENCES ordem_servico(id),
  produto_id     UUID REFERENCES produto(id),
  tipo           TEXT NOT NULL CHECK (tipo IN ('PECA','SERVICO')),
  descricao      TEXT NOT NULL,
  quantidade     NUMERIC(12,3) NOT NULL,
  preco_unitario NUMERIC(12,2) NOT NULL,
  subtotal       NUMERIC(12,2) NOT NULL
);

CREATE TABLE venda (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id    UUID NOT NULL REFERENCES tenant(id),
  cliente_id   UUID REFERENCES cliente(id),
  usuario_id   UUID NOT NULL REFERENCES usuario(id),
  numero_venda TEXT NOT NULL,
  origem       TEXT NOT NULL CHECK (origem IN ('BALCAO','OS')),
  total        NUMERIC(12,2) NOT NULL,
  status       TEXT DEFAULT 'CONCLUIDA',
  criado_em    TIMESTAMPTZ DEFAULT now(),
  UNIQUE(numero_venda, tenant_id)
);

CREATE TABLE item_venda (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  venda_id       UUID NOT NULL REFERENCES venda(id),
  produto_id     UUID NOT NULL REFERENCES produto(id),
  quantidade     NUMERIC(12,3) NOT NULL,
  preco_unitario NUMERIC(12,2) NOT NULL,
  subtotal       NUMERIC(12,2) NOT NULL
);

CREATE TABLE nota_fiscal_saida (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id    UUID NOT NULL REFERENCES tenant(id),
  venda_id     UUID REFERENCES venda(id),
  os_id        UUID REFERENCES ordem_servico(id),
  chave_nfe    VARCHAR(44) UNIQUE,
  numero_nf    TEXT,
  serie        VARCHAR(3),
  tipo         TEXT CHECK (tipo IN ('NFE','NFCE')),
  status_sefaz TEXT DEFAULT 'PENDENTE'
                 CHECK (status_sefaz IN
                   ('PENDENTE','AUTORIZADA','REJEITADA','CANCELADA')),
  xml_path     TEXT,
  danfe_path   TEXT,
  emitida_em   TIMESTAMPTZ DEFAULT now()
);

-- Append-only. A trilha é a fonte de verdade do estoque.
CREATE TABLE movimentacao_estoque (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id        UUID NOT NULL REFERENCES tenant(id),
  produto_id       UUID NOT NULL REFERENCES produto(id),
  referencia_id    UUID,
  tipo_ref         TEXT CHECK (tipo_ref IN ('OS','VENDA','ENTRADA','AJUSTE')),
  tipo_mov         TEXT NOT NULL
                     CHECK (tipo_mov IN ('ENTRADA','SAIDA','RESERVA','LIBERACAO')),
  quantidade       NUMERIC(12,3) NOT NULL,
  estoque_anterior NUMERIC(12,3) NOT NULL,
  estoque_novo     NUMERIC(12,3) NOT NULL,
  criado_em        TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX ON movimentacao_estoque(produto_id, criado_em);

-- Sessão do agente WhatsApp — substitui Redis com uma tabela simples
CREATE TABLE agente_sessao (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID NOT NULL REFERENCES tenant(id),
  usuario_id      UUID NOT NULL REFERENCES usuario(id),
  numero_whatsapp VARCHAR(20) NOT NULL,
  mensagens       JSONB NOT NULL DEFAULT '[]',
  atualizado_em   TIMESTAMPTZ DEFAULT now()
);
CREATE UNIQUE INDEX ON agente_sessao(numero_whatsapp);
```

```sql
-- migrations/003_rls_policies.sql
-- RLS garante isolamento de tenant sem lógica no código (Fator III)

ALTER TABLE cliente             ENABLE ROW LEVEL SECURITY;
ALTER TABLE produto             ENABLE ROW LEVEL SECURITY;
ALTER TABLE fornecedor          ENABLE ROW LEVEL SECURITY;
ALTER TABLE entrada_nfe         ENABLE ROW LEVEL SECURITY;
ALTER TABLE item_entrada        ENABLE ROW LEVEL SECURITY;
ALTER TABLE ordem_servico       ENABLE ROW LEVEL SECURITY;
ALTER TABLE item_os             ENABLE ROW LEVEL SECURITY;
ALTER TABLE venda               ENABLE ROW LEVEL SECURITY;
ALTER TABLE item_venda          ENABLE ROW LEVEL SECURITY;
ALTER TABLE nota_fiscal_saida   ENABLE ROW LEVEL SECURITY;
ALTER TABLE movimentacao_estoque ENABLE ROW LEVEL SECURITY;
ALTER TABLE agente_sessao       ENABLE ROW LEVEL SECURITY;

-- Uma policy por tabela. Mesmo padrão. DRY no SQL.
CREATE POLICY tenant_iso ON cliente
  USING (tenant_id = current_setting('app.current_tenant')::uuid);
-- (repetir para cada tabela acima)
```

### 4.3 Regras de Negócio Invioláveis

Estas regras valem mais do que qualquer conveniência de implementação:

1. **Estoque em dois tempos:** adicionar peça na OS → `RESERVA`. Fechar OS → `SAIDA`. Cancelar OS → `LIBERACAO`. Nunca baixar na abertura.
2. **`historico_veiculo` é imutável** — apenas `INSERT`. Nunca `UPDATE` ou `DELETE`.
3. **`movimentacao_estoque` é append-only** — a trilha é a fonte da verdade. Nunca alterar registros passados.
4. **`compartilhar_historico` default = `false`** — opt-in explícito pelo mecânico.
5. **`resumo_publico` só é populado se `compartilhar_historico = true`** no fechamento da OS.
6. **Troca de dono do veículo:** `cliente_veiculo.ativo=false, data_fim=hoje` no registro anterior → novo registro.
7. **Veículo global — upsert idempotente:** `INSERT ... ON CONFLICT (placa) DO UPDATE`.
8. **NF-e XML jamais deletado** — obrigação fiscal de 5 anos.
9. **Certificado A1** lido de `/secrets/cert.pfx` em memória no startup. Nunca em variável de ambiente.

---

## 5. Padrões de Código

### 5.1 Camadas — responsabilidade única por arquivo

```python
# router.py — só orquestra: valida, delega, responde
@router.post("/os/", response_model=OSResponse)
async def abrir_os(
    payload: OSCreate,
    usuario=Depends(get_usuario_atual),
    db=Depends(get_db),
):
    return await OrdensServicoService(db).abrir(payload, usuario)

# service.py — só regras de negócio, sem HTTP
class OrdensServicoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def abrir(self, payload: OSCreate, usuario: Usuario) -> OrdemServico:
        await self._validar_mecanico(usuario)
        await self._reservar_pecas(payload.itens)
        return await self._persistir(payload, usuario.id)

# models.py — só mapeamento ORM, sem lógica
class OrdemServico(Base):
    __tablename__ = "ordem_servico"
    id = Column(UUID, primary_key=True, default=uuid4)
    status = Column(String, nullable=False, default=StatusOS.ABERTA)
    ...
```

### 5.2 Enums centralizados (DRY)

```python
# backend/core/enums.py — fonte única de verdade para constantes
from enum import StrEnum

class StatusOS(StrEnum):
    ABERTA          = "ABERTA"
    EM_EXECUCAO     = "EM_EXECUCAO"
    AGUARDANDO_PECA = "AGUARDANDO_PECA"
    FECHADA         = "FECHADA"
    CANCELADA       = "CANCELADA"

class TipoMovimentacao(StrEnum):
    ENTRADA   = "ENTRADA"
    SAIDA     = "SAIDA"
    RESERVA   = "RESERVA"
    LIBERACAO = "LIBERACAO"

class Perfil(StrEnum):
    ADMIN     = "ADMIN"
    ATENDENTE = "ATENDENTE"
    MECANICO  = "MECANICO"
```

### 5.3 Config via ambiente (Fator III)

```python
# backend/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ANTHROPIC_API_KEY: str
    CERT_A1_PATH: str = "/secrets/cert.pfx"
    CERT_A1_PASSWORD: str
    WHATSAPP_TOKEN: str
    WHATSAPP_VERIFY_TOKEN: str
    WHATSAPP_PHONE_ID: str
    AMBIENTE_SEFAZ: str = "homologacao"

    model_config = {"env_file": ".env"}

settings = Settings()
# Nunca: DATABASE_URL = "postgresql://localhost/oficina" hardcoded
```

### 5.4 RLS Middleware (Fator VI — stateless)

```python
# backend/core/database.py
async def get_db(usuario=Depends(get_usuario_atual)):
    async with AsyncSessionLocal() as session:
        # RLS seta o tenant antes de qualquer query — sem lógica de filtro espalhada
        await session.execute(
            text("SET LOCAL app.current_tenant = :tid"),
            {"tid": str(usuario.tenant_id)}
        )
        yield session
```

### 5.5 Logs estruturados em JSON (Fator XI)

```python
# Nunca: print("OS aberta")
# Nunca: logger.info(f"OS {os_id} aberta pelo mecânico {mecanico_id}")
import structlog
log = structlog.get_logger()

log.info("os_aberta",
    os_id=str(os.id),
    tenant_id=str(os.tenant_id),
    mecanico_id=str(mecanico_id)
)
# Saída JSON para stdout — docker compose logs entende, ferramentas de busca entendem
```

### 5.6 Exceções de domínio (KISS — sem HTTP nos services)

```python
# backend/core/exceptions.py
class OficinaDomainError(Exception): pass
class NaoEncontrado(OficinaDomainError): pass
class EstoqueInsuficiente(OficinaDomainError): pass
class OSJaFechada(OficinaDomainError): pass
class PlacaInvalida(OficinaDomainError): pass

# No service: raise EstoqueInsuficiente("filtro de óleo")
# No router: handler converte para HTTPException 422
# Service nunca importa HTTPException — não sabe que existe HTTP
```

---

## 6. Testes — Construção Contínua

### 6.1 Estrutura

```
backend/modules/ordens_servico/tests/
├── conftest.py          ← fixtures: db de teste, tenant, usuario, produto
├── test_service.py      ← regras de negócio (unitário com db de teste)
└── test_router.py       ← contrato da API (integração com TestClient)
```

### 6.2 Exemplo de teste de regra de negócio

```python
# test_service.py
import pytest
from modules.ordens_servico.service import OrdensServicoService
from core.exceptions import EstoqueInsuficiente

@pytest.mark.asyncio
async def test_reserva_estoque_ao_adicionar_peca(db, os_aberta, produto_com_estoque_2):
    """Adicionar peça na OS deve gerar movimentação RESERVA, não SAIDA."""
    service = OrdensServicoService(db)

    await service.adicionar_item(os_aberta.id, produto_com_estoque_2.id, quantidade=1)

    movs = await service.listar_movimentacoes(produto_com_estoque_2.id)
    assert len(movs) == 1
    assert movs[0].tipo_mov == "RESERVA"
    assert movs[0].estoque_novo == 1   # 2 - 1 reservado

@pytest.mark.asyncio
async def test_nao_permite_reserva_sem_estoque(db, os_aberta, produto_sem_estoque):
    """Deve lançar EstoqueInsuficiente se não houver saldo."""
    service = OrdensServicoService(db)

    with pytest.raises(EstoqueInsuficiente):
        await service.adicionar_item(os_aberta.id, produto_sem_estoque.id, quantidade=1)

@pytest.mark.asyncio
async def test_fechamento_converte_reserva_em_saida(db, os_com_pecas):
    """Fechar OS deve converter RESERVA em SAIDA no estoque."""
    service = OrdensServicoService(db)

    await service.fechar(os_com_pecas.id, compartilhar_historico=False)

    movs = await service.listar_movimentacoes(os_com_pecas.itens[0].produto_id)
    tipos = [m.tipo_mov for m in movs]
    assert "RESERVA" in tipos
    assert "SAIDA" in tipos

@pytest.mark.asyncio
async def test_cancelamento_libera_reserva(db, os_com_pecas):
    """Cancelar OS deve gerar LIBERACAO para cada peça reservada."""
    service = OrdensServicoService(db)

    await service.cancelar(os_com_pecas.id)

    movs = await service.listar_movimentacoes(os_com_pecas.itens[0].produto_id)
    assert any(m.tipo_mov == "LIBERACAO" for m in movs)

@pytest.mark.asyncio
async def test_historico_publico_apenas_com_optin(db, os_aberta):
    """resumo_publico só deve ser populado se compartilhar_historico=True."""
    service = OrdensServicoService(db)

    await service.fechar(os_aberta.id, compartilhar_historico=False)

    historico = await service.buscar_historico_veiculo(os_aberta.veiculo_id)
    assert historico.resumo_publico is None
    assert historico.detalhe_privado is not None
```

### 6.3 Executar testes (Fator X — dev/prod parity)

```bash
# Localmente (com postgres rodando via docker compose)
pytest backend/ -v --asyncio-mode=auto

# No CI (ci.yml roda exatamente o mesmo comando)
docker compose -f docker-compose.test.yml run --rm backend pytest -v
```

### 6.4 CI pipeline (Fator V — build separado de deploy)

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.12'}
      - run: pip install -r backend/requirements.txt
      - run: ruff check backend/         # lint
      - run: mypy backend/               # tipos
      - run: pytest backend/ -v          # testes
  # deploy.yml só roda se CI passar
```

---

## 7. Docker Compose

```yaml
# docker-compose.yml
services:

  postgres:
    image: postgres:16-alpine
    restart: always
    environment:
      POSTGRES_DB: oficina
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      retries: 5

  backend:
    build: ./backend
    restart: always
    env_file: .env
    volumes:
      - ./data/arquivos:/data/arquivos
      - ./secrets:/secrets:ro
    depends_on:
      postgres:
        condition: service_healthy
    expose:
      - "8000"
    # Fator IX — shutdown graceful
    stop_grace_period: 30s

  frontend:
    build: ./frontend
    restart: always
    expose:
      - "80"

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./data/certbot:/etc/letsencrypt
    depends_on:
      - backend
      - frontend

  pgbackup:
    image: postgres:16-alpine
    restart: always
    env_file: .env
    volumes:
      - ./data/backups:/backups
    entrypoint: >
      sh -c "while true; do
        pg_dump postgresql://${DB_USER}:${DB_PASSWORD}@postgres/oficina
        | gzip > /backups/oficina_$$(date +%Y%m%d_%H%M).sql.gz;
        find /backups -mtime +7 -delete;
        sleep 86400;
      done"
    depends_on:
      - postgres

  # Migrations rodam separado do app (Fator XII)
  migrations:
    build: ./backend
    env_file: .env
    command: python -m migrations
    depends_on:
      postgres:
        condition: service_healthy
    profiles: ["migrate"]   # só roda com: docker compose --profile migrate up migrations
```

**Operação do dia a dia:**
```bash
# Subir tudo
docker compose up -d

# Rodar migrations (só quando necessário)
docker compose --profile migrate up migrations

# Ver logs do backend em tempo real (Fator XI)
docker compose logs -f backend

# Atualizar só o backend sem derrubar banco
docker compose up -d --no-deps backend

# Backup manual imediato
docker compose exec pgbackup pg_dump postgresql://$DB_USER:$DB_PASSWORD@postgres/oficina \
  | gzip > ./data/backups/manual_$(date +%Y%m%d_%H%M).sql.gz

# Restaurar
gunzip -c ./data/backups/oficina_20250520_0300.sql.gz \
  | docker compose exec -T postgres psql -U $DB_USER oficina
```

---

## 8. Agente Claude — WhatsApp

### 8.1 Fluxo (KISS — sem fila)

```
Meta POST /webhook/whatsapp
    │
    ▼
webhook.py
  1. Verifica HMAC-SHA256 (segurança)
  2. Identifica usuario pelo numero_whatsapp
  3. Chama worker.processar() de forma síncrona
     (FastAPI async + timeout 55s — suficiente para 1 mecânico)
  4. Retorna 200 com resposta
```

Para 1 mecânico, chamada síncrona é mais simples, mais fácil de depurar e suficiente. Fila só quando houver necessidade real (YAGNI).

### 8.2 Sessão no PostgreSQL (Fator VI — stateless)

```python
# backend/agente/sessao.py
from datetime import datetime, timedelta, timezone
from sqlalchemy import text

TIMEOUT = timedelta(hours=2)

async def carregar(db, numero: str) -> list[dict]:
    row = (await db.execute(
        text("SELECT mensagens, atualizado_em FROM agente_sessao WHERE numero_whatsapp = :n"),
        {"n": numero}
    )).fetchone()

    if not row:
        return []
    if datetime.now(timezone.utc) - row.atualizado_em > TIMEOUT:
        return []   # sessão expirada — nova conversa
    return row.mensagens

async def salvar(db, numero: str, tenant_id: str, usuario_id: str, msgs: list):
    await db.execute(text("""
        INSERT INTO agente_sessao
          (numero_whatsapp, tenant_id, usuario_id, mensagens, atualizado_em)
        VALUES (:n, :tid, :uid, :msgs::jsonb, now())
        ON CONFLICT (numero_whatsapp)
        DO UPDATE SET mensagens = :msgs::jsonb, atualizado_em = now()
    """), {"n": numero, "tid": tenant_id, "uid": usuario_id, "msgs": msgs})
    await db.commit()
```

### 8.3 Tools

```python
# backend/agente/tools.py
TOOLS = [
    {
        "name": "buscar_veiculo",
        "description": "Busca veículo pela placa. Retorna dados e histórico público.",
        "input_schema": {
            "type": "object",
            "properties": {
                "placa": {"type": "string", "description": "Formato: ABC1234 ou ABC1D23"}
            },
            "required": ["placa"]
        }
    },
    {
        "name": "criar_veiculo",
        "description": "Cadastra veículo novo. Usar só se buscar_veiculo retornar não encontrado.",
        "input_schema": {
            "type": "object",
            "properties": {
                "placa":  {"type": "string"},
                "marca":  {"type": "string"},
                "modelo": {"type": "string"},
                "cor":    {"type": "string"},
                "tipo":   {"type": "string", "enum": ["carro","moto","caminhao","van"]}
            },
            "required": ["placa"]
        }
    },
    {
        "name": "buscar_cliente",
        "description": "Busca cliente no tenant por nome parcial, CPF ou telefone.",
        "input_schema": {
            "type": "object",
            "properties": {"q": {"type": "string"}},
            "required": ["q"]
        }
    },
    {
        "name": "abrir_os",
        "description": "Abre OS. Confirme cliente e veículo com o mecânico antes de chamar.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cliente_id":             {"type": "string"},
                "veiculo_id":             {"type": "string"},
                "km_entrada":             {"type": "integer"},
                "descricao_problema":     {"type": "string"},
                "compartilhar_historico": {"type": "boolean", "default": False}
            },
            "required": ["cliente_id", "veiculo_id", "descricao_problema"]
        }
    },
    {
        "name": "minhas_os",
        "description": "Lista OS abertas do mecânico autenticado.",
        "input_schema": {"type": "object", "properties": {}}
    }
]
```

### 8.4 System Prompt

```python
# backend/agente/prompts.py

def build_system_prompt(nome_tenant: str, nome_mecanico: str) -> str:
    return f"""Você é o assistente da {nome_tenant}.
Fala com {nome_mecanico}, mecânico autenticado.

Funções: abrir OS, consultar veículo por placa, buscar cliente.

Regras:
1. Confirme cliente + veículo + problema antes de abrir a OS
2. Antes de confirmar, pergunte sobre compartilhamento no histórico público
3. Se veículo não existir: colete placa, marca, modelo, cor — depois crie
4. Se cliente não encontrado: oriente cadastrar no sistema web
5. Seja direto — o mecânico está trabalhando
6. Português informal sempre

Não pode: fechar OS, consultar preços, emitir notas, ver dados de outros mecânicos."""
```

---

## 9. Variáveis de Ambiente

```env
# .env — fica na VPS em /opt/oficina/.env
# Nunca commitar. .gitignore já ignora.

DATABASE_URL=postgresql+asyncpg://oficina:senha@postgres:5432/oficina
SECRET_KEY=gere-com-openssl-rand-hex-32

ANTHROPIC_API_KEY=sk-ant-...

CERT_A1_PATH=/secrets/cert.pfx
CERT_A1_PASSWORD=senha-do-certificado

WHATSAPP_TOKEN=token-do-meta
WHATSAPP_VERIFY_TOKEN=string-que-voce-define
WHATSAPP_PHONE_ID=id-do-numero

AMBIENTE_SEFAZ=homologacao

DB_USER=oficina
DB_PASSWORD=senha-forte
```

---

## 10. Deploy (CI/CD)

```yaml
# .github/workflows/deploy.yml
# Só roda se o CI (lint + tipos + testes) passou

name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    needs: [quality]   # bloqueia se CI falhou
    steps:
      - uses: actions/checkout@v4
      - name: Deploy na VPS
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            cd /opt/oficina
            git pull origin main
            docker compose build --no-cache backend frontend
            docker compose up -d
            docker image prune -f
```

**GitHub Secrets necessários:** `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY`.
Só três. O `.env` fica na VPS — o CI nunca vê credenciais de produção.

---

## 11. Ordem de Implementação (MVP)

Cada passo entrega algo testável. Não avance sem testes no passo atual.

| # | Entrega | Critério de saída |
|---|---------|------------------|
| 1 | `migrations/` | DDL + RLS rodando, `psql` retorna tabelas |
| 2 | `core/` | Config, DB, security, enums, exceptions |
| 3 | `modules/iam/` | Login retorna JWT, RBAC bloqueia rota errada |
| 4 | `shared/veiculo_global/` | Upsert por placa, histórico append-only |
| 5 | `modules/cadastros/` | CRUD cliente, vínculo cliente-veículo |
| 6 | `modules/estoque/` | Produto, movimentação, parser XML NF-e |
| 7 | `modules/ordens_servico/` | Ciclo completo: abrir → itens → fechar |
| 8 | `agente/` | Mecânico abre OS pelo WhatsApp |
| 9 | `shared/fiscal/` | NF-e saída autorizada em homologação |
| 10 | `modules/vendas/` | PDV balcão + NFCe |
| 11 | `frontend/` | React por módulo |
| 12 | Infra | docker-compose + nginx + CI/CD rodando na VPS |

---

## 12. O Que Não Construir Agora (YAGNI — lista pública)

Estas features existem como ideia. Só entram quando houver demanda real:

- Relatórios e dashboards gerenciais
- Multi-filial / multi-tenant management
- App nativo iOS/Android
- Marketplace de peças
- Módulo financeiro (contas a pagar/receber, DRE)
- Agendamento de serviços
- Notificação automática de retorno ao cliente
- Integração com maquininha de pagamento
- Curva ABC de produtos
- Cotação online de peças
