-- migrations/003_rls_policies.sql
-- RLS garante isolamento de tenant sem lógica no código (Fator III / XII-Factor).
-- Padrão único: current_setting('app.current_tenant') setado pelo middleware a cada request.
-- FORCE ROW LEVEL SECURITY impede bypass mesmo pelo dono da tabela.
--
-- NÃO aplicado a: tenant (raiz), usuario (login ocorre sem tenant context),
--                 cliente_veiculo (protegido por FK + lógica de negócio).
-- Para as tabelas sem tenant_id direto (item_*), a policy usa subquery via FK.

-- ─── Habilitar RLS ───────────────────────────────────────────────────────────

ALTER TABLE cliente              ENABLE ROW LEVEL SECURITY;
ALTER TABLE produto              ENABLE ROW LEVEL SECURITY;
ALTER TABLE fornecedor           ENABLE ROW LEVEL SECURITY;
ALTER TABLE entrada_nfe          ENABLE ROW LEVEL SECURITY;
ALTER TABLE item_entrada         ENABLE ROW LEVEL SECURITY;
ALTER TABLE ordem_servico        ENABLE ROW LEVEL SECURITY;
ALTER TABLE item_os              ENABLE ROW LEVEL SECURITY;
ALTER TABLE venda                ENABLE ROW LEVEL SECURITY;
ALTER TABLE item_venda           ENABLE ROW LEVEL SECURITY;
ALTER TABLE nota_fiscal_saida    ENABLE ROW LEVEL SECURITY;
ALTER TABLE movimentacao_estoque ENABLE ROW LEVEL SECURITY;
ALTER TABLE agente_sessao        ENABLE ROW LEVEL SECURITY;

-- FORCE: garante que nem o owner da tabela (usuário DB do app) bypassa a policy.
ALTER TABLE cliente              FORCE ROW LEVEL SECURITY;
ALTER TABLE produto              FORCE ROW LEVEL SECURITY;
ALTER TABLE fornecedor           FORCE ROW LEVEL SECURITY;
ALTER TABLE entrada_nfe          FORCE ROW LEVEL SECURITY;
ALTER TABLE item_entrada         FORCE ROW LEVEL SECURITY;
ALTER TABLE ordem_servico        FORCE ROW LEVEL SECURITY;
ALTER TABLE item_os              FORCE ROW LEVEL SECURITY;
ALTER TABLE venda                FORCE ROW LEVEL SECURITY;
ALTER TABLE item_venda           FORCE ROW LEVEL SECURITY;
ALTER TABLE nota_fiscal_saida    FORCE ROW LEVEL SECURITY;
ALTER TABLE movimentacao_estoque FORCE ROW LEVEL SECURITY;
ALTER TABLE agente_sessao        FORCE ROW LEVEL SECURITY;

-- ─── Policies: tabelas com tenant_id direto ──────────────────────────────────
-- Padrão: USING filtra SELECT/UPDATE/DELETE. WITH CHECK filtra INSERT/UPDATE.
-- Mesmo current_setting garantido pelo middleware (SET LOCAL app.current_tenant = :tid).

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'cliente' AND policyname = 'tenant_iso') THEN
        CREATE POLICY tenant_iso ON cliente
            USING (tenant_id = current_setting('app.current_tenant')::uuid)
            WITH CHECK (tenant_id = current_setting('app.current_tenant')::uuid);
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'produto' AND policyname = 'tenant_iso') THEN
        CREATE POLICY tenant_iso ON produto
            USING (tenant_id = current_setting('app.current_tenant')::uuid)
            WITH CHECK (tenant_id = current_setting('app.current_tenant')::uuid);
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'fornecedor' AND policyname = 'tenant_iso') THEN
        CREATE POLICY tenant_iso ON fornecedor
            USING (tenant_id = current_setting('app.current_tenant')::uuid)
            WITH CHECK (tenant_id = current_setting('app.current_tenant')::uuid);
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'entrada_nfe' AND policyname = 'tenant_iso') THEN
        CREATE POLICY tenant_iso ON entrada_nfe
            USING (tenant_id = current_setting('app.current_tenant')::uuid)
            WITH CHECK (tenant_id = current_setting('app.current_tenant')::uuid);
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'ordem_servico' AND policyname = 'tenant_iso') THEN
        CREATE POLICY tenant_iso ON ordem_servico
            USING (tenant_id = current_setting('app.current_tenant')::uuid)
            WITH CHECK (tenant_id = current_setting('app.current_tenant')::uuid);
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'venda' AND policyname = 'tenant_iso') THEN
        CREATE POLICY tenant_iso ON venda
            USING (tenant_id = current_setting('app.current_tenant')::uuid)
            WITH CHECK (tenant_id = current_setting('app.current_tenant')::uuid);
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'nota_fiscal_saida' AND policyname = 'tenant_iso') THEN
        CREATE POLICY tenant_iso ON nota_fiscal_saida
            USING (tenant_id = current_setting('app.current_tenant')::uuid)
            WITH CHECK (tenant_id = current_setting('app.current_tenant')::uuid);
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'movimentacao_estoque' AND policyname = 'tenant_iso') THEN
        CREATE POLICY tenant_iso ON movimentacao_estoque
            USING (tenant_id = current_setting('app.current_tenant')::uuid)
            WITH CHECK (tenant_id = current_setting('app.current_tenant')::uuid);
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'agente_sessao' AND policyname = 'tenant_iso') THEN
        CREATE POLICY tenant_iso ON agente_sessao
            USING (tenant_id = current_setting('app.current_tenant')::uuid)
            WITH CHECK (tenant_id = current_setting('app.current_tenant')::uuid);
    END IF;
END $$;

-- ─── Policies: tabelas SEM tenant_id direto (join via FK) ────────────────────
-- item_entrada → entrada_nfe.tenant_id
-- item_os      → ordem_servico.tenant_id
-- item_venda   → venda.tenant_id
--
-- Subquery é reavaliada por row: correto e seguro (não há risco de short-circuit
-- que vaze dados entre tenants, pois o planner aplica a policy antes do join).

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'item_entrada' AND policyname = 'tenant_iso') THEN
        CREATE POLICY tenant_iso ON item_entrada
            USING (
                entrada_id IN (
                    SELECT id FROM entrada_nfe
                    WHERE tenant_id = current_setting('app.current_tenant')::uuid
                )
            )
            WITH CHECK (
                entrada_id IN (
                    SELECT id FROM entrada_nfe
                    WHERE tenant_id = current_setting('app.current_tenant')::uuid
                )
            );
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'item_os' AND policyname = 'tenant_iso') THEN
        CREATE POLICY tenant_iso ON item_os
            USING (
                os_id IN (
                    SELECT id FROM ordem_servico
                    WHERE tenant_id = current_setting('app.current_tenant')::uuid
                )
            )
            WITH CHECK (
                os_id IN (
                    SELECT id FROM ordem_servico
                    WHERE tenant_id = current_setting('app.current_tenant')::uuid
                )
            );
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'item_venda' AND policyname = 'tenant_iso') THEN
        CREATE POLICY tenant_iso ON item_venda
            USING (
                venda_id IN (
                    SELECT id FROM venda
                    WHERE tenant_id = current_setting('app.current_tenant')::uuid
                )
            )
            WITH CHECK (
                venda_id IN (
                    SELECT id FROM venda
                    WHERE tenant_id = current_setting('app.current_tenant')::uuid
                )
            );
    END IF;
END $$;
