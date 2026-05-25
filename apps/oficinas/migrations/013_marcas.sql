-- 013: cadastro de marcas (tenant-scoped) + FK em produto

CREATE TABLE IF NOT EXISTS marca (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id  UUID NOT NULL REFERENCES tenant(id),
    nome       TEXT NOT NULL,
    ativo      BOOLEAN NOT NULL DEFAULT true,
    UNIQUE (tenant_id, nome)
);

ALTER TABLE produto
    ADD COLUMN IF NOT EXISTS marca_id UUID REFERENCES marca(id);

-- RLS: mesmas políticas do padrão de tenant
ALTER TABLE marca ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'marca' AND policyname = 'marca_tenant_isolation'
    ) THEN
        CREATE POLICY marca_tenant_isolation ON marca
            USING (tenant_id = current_setting('app.tenant_id')::UUID);
    END IF;
END$$;
