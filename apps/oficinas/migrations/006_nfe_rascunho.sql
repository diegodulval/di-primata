-- NF-e import review flow: mapeamento de códigos, rascunho e itens pendentes

-- EAN no produto para matching por código de barras
ALTER TABLE produto ADD COLUMN IF NOT EXISTS ean VARCHAR(14);
CREATE INDEX IF NOT EXISTS idx_produto_ean ON produto(ean) WHERE ean IS NOT NULL;

-- Mapeamento persistente: fornecedor × cProd → produto interno
-- Aprendido em cada confirmação; elimina revisão manual nas importações seguintes
CREATE TABLE IF NOT EXISTS mapeamento_fornecedor_produto (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         UUID NOT NULL REFERENCES tenant(id),
  fornecedor_id     UUID NOT NULL REFERENCES fornecedor(id),
  codigo_fornecedor TEXT NOT NULL,
  produto_id        UUID NOT NULL REFERENCES produto(id),
  UNIQUE(tenant_id, fornecedor_id, codigo_fornecedor)
);

-- Rascunho da NF-e: estado transitório antes da confirmação
-- Nenhum estoque é movimentado até POST /confirmar
CREATE TABLE IF NOT EXISTS rascunho_entrada (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id     UUID NOT NULL REFERENCES tenant(id),
  fornecedor_id UUID REFERENCES fornecedor(id),
  chave_nfe     VARCHAR(44),
  numero_nf     TEXT,
  data_emissao  DATE,
  valor_total   NUMERIC(12,2),
  status        TEXT NOT NULL DEFAULT 'PENDENTE'
                  CHECK (status IN ('PENDENTE','CONFIRMADA','CANCELADA')),
  criado_em     TIMESTAMPTZ DEFAULT now()
);

-- Itens do rascunho: um por <det> da NF-e
CREATE TABLE IF NOT EXISTS item_rascunho_entrada (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  rascunho_id       UUID NOT NULL REFERENCES rascunho_entrada(id) ON DELETE CASCADE,
  produto_id        UUID REFERENCES produto(id),
  codigo_fornecedor TEXT NOT NULL,
  codigo_ref        TEXT,
  ean               VARCHAR(14),
  descricao_nfe     TEXT NOT NULL,
  ncm               VARCHAR(8),
  quantidade        NUMERIC(12,3) NOT NULL,
  preco_unitario    NUMERIC(12,2) NOT NULL,
  icms              NUMERIC(5,2) DEFAULT 0,
  ipi               NUMERIC(5,2) DEFAULT 0,
  status_item       TEXT NOT NULL DEFAULT 'PENDENTE'
                      CHECK (status_item IN ('AUTO_VINCULADO','VINCULADO','NOVO','PENDENTE'))
);

-- RLS
ALTER TABLE mapeamento_fornecedor_produto ENABLE ROW LEVEL SECURITY;
ALTER TABLE rascunho_entrada              ENABLE ROW LEVEL SECURITY;
ALTER TABLE item_rascunho_entrada         ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_iso ON mapeamento_fornecedor_produto;
CREATE POLICY tenant_iso ON mapeamento_fornecedor_produto
  USING (tenant_id = current_setting('app.current_tenant')::uuid);

DROP POLICY IF EXISTS tenant_iso ON rascunho_entrada;
CREATE POLICY tenant_iso ON rascunho_entrada
  USING (tenant_id = current_setting('app.current_tenant')::uuid);

-- item_rascunho_entrada não tem tenant_id; herda via rascunho_entrada
DROP POLICY IF EXISTS tenant_iso ON item_rascunho_entrada;
CREATE POLICY tenant_iso ON item_rascunho_entrada
  USING (
    EXISTS (
      SELECT 1 FROM rascunho_entrada r
      WHERE r.id = item_rascunho_entrada.rascunho_id
        AND r.tenant_id = current_setting('app.current_tenant')::uuid
    )
  );
