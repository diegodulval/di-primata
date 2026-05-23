-- Expansão do cadastro de clientes: campos para importação, NF-e e busca.

ALTER TABLE cliente
    ADD COLUMN IF NOT EXISTS tipo_pessoa       VARCHAR(10)  DEFAULT 'Fisica',
    ADD COLUMN IF NOT EXISTS celular           VARCHAR(20),
    ADD COLUMN IF NOT EXISTS rg                VARCHAR(20),
    ADD COLUMN IF NOT EXISTS data_nascimento   DATE,
    ADD COLUMN IF NOT EXISTS sexo              VARCHAR(10),
    ADD COLUMN IF NOT EXISTS apelido           TEXT,
    ADD COLUMN IF NOT EXISTS cep               VARCHAR(8),
    ADD COLUMN IF NOT EXISTS cidade            TEXT,
    ADD COLUMN IF NOT EXISTS uf                VARCHAR(2),
    ADD COLUMN IF NOT EXISTS observacoes       TEXT,
    ADD COLUMN IF NOT EXISTS consumidor_final  BOOLEAN NOT NULL DEFAULT true,
    ADD COLUMN IF NOT EXISTS indicador_ie      VARCHAR(1) NOT NULL DEFAULT '9',
    ADD COLUMN IF NOT EXISTS inscricao_estadual VARCHAR(20),
    ADD COLUMN IF NOT EXISTS ativo             BOOLEAN NOT NULL DEFAULT true;
