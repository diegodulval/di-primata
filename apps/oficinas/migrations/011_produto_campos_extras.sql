-- Campos adicionais no produto: unidade de medida, referência do fabricante,
-- pesos (obrigatórios na NF-e saída), origem da mercadoria e observações internas.

ALTER TABLE produto
    ADD COLUMN IF NOT EXISTS unidade_medida    VARCHAR(10)    NOT NULL DEFAULT 'UN',
    ADD COLUMN IF NOT EXISTS ref_fabricante    TEXT,
    ADD COLUMN IF NOT EXISTS peso_liquido      NUMERIC(10, 3) NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS peso_bruto        NUMERIC(10, 3) NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS origem_mercadoria VARCHAR(1)     NOT NULL DEFAULT '0',
    ADD COLUMN IF NOT EXISTS observacoes       TEXT;
