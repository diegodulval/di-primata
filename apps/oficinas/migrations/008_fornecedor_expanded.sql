-- Expande campos do fornecedor e adiciona CFOP/CST aos itens de rascunho

ALTER TABLE fornecedor
    ADD COLUMN IF NOT EXISTS nome_fantasia      TEXT,
    ADD COLUMN IF NOT EXISTS inscricao_estadual VARCHAR(20),
    ADD COLUMN IF NOT EXISTS telefone           VARCHAR(20),
    ADD COLUMN IF NOT EXISTS email              TEXT;

ALTER TABLE item_rascunho_entrada
    ADD COLUMN IF NOT EXISTS cfop VARCHAR(4),
    ADD COLUMN IF NOT EXISTS cst  VARCHAR(3);
