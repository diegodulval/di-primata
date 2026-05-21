-- migrations/001_global_schema.sql
-- Schema cross-tenant: veiculo existe uma única vez no banco, sem RLS.
-- Veículo é entidade global — consulta por placa funciona entre tenants.
-- historico_veiculo é APPEND-ONLY: nunca UPDATE ou DELETE.

CREATE SCHEMA IF NOT EXISTS global;

CREATE TABLE IF NOT EXISTS global.veiculo (
    id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    placa     VARCHAR(8) UNIQUE NOT NULL,
    chassi    VARCHAR(17),
    marca     TEXT,
    modelo    TEXT,
    ano_fab   SMALLINT,
    ano_mod   SMALLINT,
    cor       TEXT,
    tipo      TEXT CHECK (tipo IN ('carro', 'moto', 'caminhao', 'van')),
    criado_em TIMESTAMPTZ DEFAULT now()
);

-- Append-only. NUNCA UPDATE ou DELETE. É a memória do veículo.
-- resumo_publico fica NULL quando compartilhar_historico = false na OS.
CREATE TABLE IF NOT EXISTS global.historico_veiculo (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    veiculo_id      UUID NOT NULL REFERENCES global.veiculo(id),
    tenant_id       UUID NOT NULL,
    os_id           UUID,                  -- referência lógica (sem FK cross-schema)
    data_servico    DATE NOT NULL,
    km_entrada      INTEGER,
    resumo_publico  TEXT,                  -- NULL se compartilhar_historico=false
    detalhe_privado TEXT NOT NULL,         -- sempre populado, visível só ao tenant
    criado_em       TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_historico_veiculo_veiculo_id
    ON global.historico_veiculo(veiculo_id);
