-- Migration 010: adicionar ativo e tipo_pessoa ao fornecedor
ALTER TABLE fornecedor
    ADD COLUMN IF NOT EXISTS ativo       BOOLEAN NOT NULL DEFAULT true,
    ADD COLUMN IF NOT EXISTS tipo_pessoa VARCHAR(10) DEFAULT 'Juridica';
