-- migrations/002_tenant_schema.sql
-- Todas as entidades tenant-scoped vivem no schema public.
-- RLS aplicada na migration 003. tenant_id presente em toda tabela que isola dados.
-- movimentacao_estoque e historico_veiculo são APPEND-ONLY.

-- ─── IAM ─────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS tenant (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    razao_social      TEXT NOT NULL,
    cnpj              VARCHAR(14) UNIQUE NOT NULL,
    regime_tributario TEXT CHECK (regime_tributario IN
                          ('simples', 'lucro_presumido', 'lucro_real')),
    ativo             BOOLEAN DEFAULT true,
    criado_em         TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS usuario (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id        UUID NOT NULL REFERENCES tenant(id),
    nome             TEXT NOT NULL,
    email            TEXT NOT NULL,
    senha_hash       TEXT NOT NULL,
    perfil           TEXT NOT NULL CHECK (perfil IN ('ADMIN', 'ATENDENTE', 'MECANICO')),
    numero_whatsapp  VARCHAR(20) UNIQUE,
    ativo            BOOLEAN DEFAULT true,
    criado_em        TIMESTAMPTZ DEFAULT now(),
    UNIQUE (email, tenant_id)
);

-- ─── Cadastros ────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS cliente (
    id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id),
    nome      TEXT NOT NULL,
    cpf_cnpj  VARCHAR(14),
    telefone  VARCHAR(20),
    email     TEXT,
    endereco  TEXT,
    criado_em TIMESTAMPTZ DEFAULT now()
);

-- Histórico de posse: data_fim NULL = dono atual neste tenant.
-- Troca de dono: ativo=false + data_fim=hoje no registro anterior → novo INSERT.
CREATE TABLE IF NOT EXISTS cliente_veiculo (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID NOT NULL REFERENCES tenant(id),
    cliente_id  UUID NOT NULL REFERENCES cliente(id),
    veiculo_id  UUID NOT NULL,             -- referência lógica ao global.veiculo
    data_inicio DATE NOT NULL DEFAULT CURRENT_DATE,
    data_fim    DATE,
    ativo       BOOLEAN DEFAULT true
);

CREATE INDEX IF NOT EXISTS idx_cliente_veiculo_veiculo_tenant
    ON cliente_veiculo(veiculo_id, tenant_id);

CREATE TABLE IF NOT EXISTS fornecedor (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id    UUID NOT NULL REFERENCES tenant(id),
    razao_social TEXT NOT NULL,
    cnpj         VARCHAR(14),
    contato      TEXT
);

-- ─── Estoque ──────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS produto (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id      UUID NOT NULL REFERENCES tenant(id),
    codigo         TEXT NOT NULL,
    descricao      TEXT NOT NULL,
    ncm            VARCHAR(8),
    marca          TEXT,
    localizacao    TEXT,
    preco_custo    NUMERIC(12, 2) NOT NULL DEFAULT 0,
    preco_venda    NUMERIC(12, 2) NOT NULL DEFAULT 0,
    estoque_atual  NUMERIC(12, 3) DEFAULT 0,
    estoque_minimo NUMERIC(12, 3) DEFAULT 0,
    estoque_maximo NUMERIC(12, 3) DEFAULT 0,
    ativo          BOOLEAN DEFAULT true,
    UNIQUE (codigo, tenant_id)
);

CREATE TABLE IF NOT EXISTS entrada_nfe (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id     UUID NOT NULL REFERENCES tenant(id),
    fornecedor_id UUID REFERENCES fornecedor(id),
    chave_nfe     VARCHAR(44) UNIQUE,
    numero_nf     TEXT,
    data_emissao  DATE,
    valor_total   NUMERIC(12, 2),
    xml_path      TEXT,                    -- NF-e XML nunca deletado (obrigação 5 anos)
    status        TEXT DEFAULT 'processada',
    criado_em     TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS item_entrada (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entrada_id        UUID NOT NULL REFERENCES entrada_nfe(id),
    produto_id        UUID REFERENCES produto(id),
    codigo_fornecedor TEXT,
    quantidade        NUMERIC(12, 3) NOT NULL,
    preco_unitario    NUMERIC(12, 2) NOT NULL,
    icms              NUMERIC(5, 2) DEFAULT 0,
    ipi               NUMERIC(5, 2) DEFAULT 0
);

-- Append-only: ENTRADA, SAIDA, RESERVA, LIBERACAO.
-- Regra de dois tempos: adicionar peça → RESERVA. Fechar OS → SAIDA. Cancelar → LIBERACAO.
-- Nunca alterar registros passados. A trilha é a fonte da verdade.
CREATE TABLE IF NOT EXISTS movimentacao_estoque (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id        UUID NOT NULL REFERENCES tenant(id),
    produto_id       UUID NOT NULL REFERENCES produto(id),
    referencia_id    UUID,
    tipo_ref         TEXT CHECK (tipo_ref IN ('OS', 'VENDA', 'ENTRADA', 'AJUSTE')),
    tipo_mov         TEXT NOT NULL
                         CHECK (tipo_mov IN ('ENTRADA', 'SAIDA', 'RESERVA', 'LIBERACAO')),
    quantidade       NUMERIC(12, 3) NOT NULL,
    estoque_anterior NUMERIC(12, 3) NOT NULL,
    estoque_novo     NUMERIC(12, 3) NOT NULL,
    criado_em        TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_movimentacao_estoque_produto_em
    ON movimentacao_estoque(produto_id, criado_em);

-- ─── Ordens de Serviço ────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ordem_servico (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id              UUID NOT NULL REFERENCES tenant(id),
    cliente_id             UUID NOT NULL REFERENCES cliente(id),
    veiculo_id             UUID NOT NULL,  -- referência lógica ao global.veiculo
    mecanico_id            UUID NOT NULL REFERENCES usuario(id),
    numero_os              TEXT NOT NULL,
    km_entrada             INTEGER,
    descricao_problema     TEXT NOT NULL,
    status                 TEXT NOT NULL DEFAULT 'ABERTA'
                               CHECK (status IN
                                   ('ABERTA', 'EM_EXECUCAO', 'AGUARDANDO_PECA',
                                    'FECHADA', 'CANCELADA')),
    compartilhar_historico BOOLEAN NOT NULL DEFAULT false,  -- opt-in explícito
    aberta_em              TIMESTAMPTZ DEFAULT now(),
    fechada_em             TIMESTAMPTZ,
    total_pecas            NUMERIC(12, 2) DEFAULT 0,
    total_servicos         NUMERIC(12, 2) DEFAULT 0,
    desconto               NUMERIC(12, 2) DEFAULT 0,
    total_final            NUMERIC(12, 2) DEFAULT 0,
    UNIQUE (numero_os, tenant_id)
);

CREATE TABLE IF NOT EXISTS item_os (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    os_id          UUID NOT NULL REFERENCES ordem_servico(id),
    produto_id     UUID REFERENCES produto(id),
    tipo           TEXT NOT NULL CHECK (tipo IN ('PECA', 'SERVICO')),
    descricao      TEXT NOT NULL,
    quantidade     NUMERIC(12, 3) NOT NULL,
    preco_unitario NUMERIC(12, 2) NOT NULL,
    subtotal       NUMERIC(12, 2) NOT NULL
);

-- ─── Vendas e Fiscal ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS venda (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id    UUID NOT NULL REFERENCES tenant(id),
    cliente_id   UUID REFERENCES cliente(id),
    usuario_id   UUID NOT NULL REFERENCES usuario(id),
    numero_venda TEXT NOT NULL,
    origem       TEXT NOT NULL CHECK (origem IN ('BALCAO', 'OS')),
    total        NUMERIC(12, 2) NOT NULL,
    status       TEXT DEFAULT 'CONCLUIDA',
    criado_em    TIMESTAMPTZ DEFAULT now(),
    UNIQUE (numero_venda, tenant_id)
);

CREATE TABLE IF NOT EXISTS item_venda (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    venda_id       UUID NOT NULL REFERENCES venda(id),
    produto_id     UUID NOT NULL REFERENCES produto(id),
    quantidade     NUMERIC(12, 3) NOT NULL,
    preco_unitario NUMERIC(12, 2) NOT NULL,
    subtotal       NUMERIC(12, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS nota_fiscal_saida (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id    UUID NOT NULL REFERENCES tenant(id),
    venda_id     UUID REFERENCES venda(id),
    os_id        UUID REFERENCES ordem_servico(id),
    chave_nfe    VARCHAR(44) UNIQUE,
    numero_nf    TEXT,
    serie        VARCHAR(3),
    tipo         TEXT CHECK (tipo IN ('NFE', 'NFCE')),
    status_sefaz TEXT DEFAULT 'PENDENTE'
                     CHECK (status_sefaz IN
                         ('PENDENTE', 'AUTORIZADA', 'REJEITADA', 'CANCELADA')),
    xml_path     TEXT,                    -- NF-e XML nunca deletado (obrigação 5 anos)
    danfe_path   TEXT,
    emitida_em   TIMESTAMPTZ DEFAULT now()
);

-- ─── Agente WhatsApp ──────────────────────────────────────────────────────────

-- Substitui Redis com uma tabela simples (KISS, Fator VI — stateless).
-- Sessão expira por lógica no código (2h sem atividade = nova conversa).
CREATE TABLE IF NOT EXISTS agente_sessao (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenant(id),
    usuario_id      UUID NOT NULL REFERENCES usuario(id),
    numero_whatsapp VARCHAR(20) NOT NULL,
    mensagens       JSONB NOT NULL DEFAULT '[]',
    atualizado_em   TIMESTAMPTZ DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_agente_sessao_whatsapp
    ON agente_sessao(numero_whatsapp);
