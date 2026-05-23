-- Migration 009: tabela de apontamentos de horas por OS
CREATE TABLE IF NOT EXISTS apontamento_os (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    os_id            UUID NOT NULL REFERENCES ordem_servico(id),
    usuario_id       UUID NOT NULL REFERENCES usuario(id),
    item_os_id       UUID REFERENCES item_os(id),
    descricao        TEXT NOT NULL,
    duracao_minutos  INTEGER NOT NULL DEFAULT 0,
    data_apontamento DATE NOT NULL DEFAULT CURRENT_DATE,
    criado_em        TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS apontamento_os_os_id_idx ON apontamento_os(os_id);
