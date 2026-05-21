-- migrations/005_iam_adjustments.sql
-- Ajustes no schema após decisões de IAM:
--
-- 1. ordem_servico.mecanico_id → nullable
--    OS pode ser aberta pelo ATENDENTE sem mecânico definido ainda.
--    Mecânico é obrigatório só ao mover para EM_EXECUCAO (regra no service).
--
-- 2. ordem_servico.aberto_por_id → novo campo de auditoria
--    Registra quem criou a OS (ATENDENTE, ADMIN ou MECANICO via WA).
--
-- 3. usuario.email → nullable
--    MECANICO se identifica por numero_whatsapp — email opcional para ele.
--    ADMIN e ATENDENTE: email obrigatório (validado no service, não no banco).
--    A constraint UNIQUE(email, tenant_id) permanece válida com NULLs
--    (PostgreSQL não indexa NULLs em unique constraints por padrão).

ALTER TABLE ordem_servico
    ALTER COLUMN mecanico_id DROP NOT NULL;

ALTER TABLE ordem_servico
    ADD COLUMN IF NOT EXISTS aberto_por_id UUID REFERENCES usuario(id);

ALTER TABLE usuario
    ALTER COLUMN email DROP NOT NULL;
