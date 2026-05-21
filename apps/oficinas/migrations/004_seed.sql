-- migrations/004_seed.sql
-- Dados iniciais mínimos para desenvolvimento e testes.
-- Apenas dev: não rodar em produção sem ajustar senhas e CNPJs.
-- Senha hash abaixo corresponde a "dev1234" — trocar antes do deploy.

-- Tenant de desenvolvimento
INSERT INTO tenant (id, razao_social, cnpj, regime_tributario)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'Oficina Demo Ltda',
    '00000000000191',
    'simples'
)
ON CONFLICT (cnpj) DO NOTHING;

-- Usuário admin de desenvolvimento
-- senha: dev1234  →  hash gerado com bcrypt rounds=12
INSERT INTO usuario (id, tenant_id, nome, email, senha_hash, perfil)
VALUES (
    '00000000-0000-0000-0000-000000000002',
    '00000000-0000-0000-0000-000000000001',
    'Admin Demo',
    'admin@oficina.dev',
    '$2b$12$Uhhvxplr7A4A9couIWxifO9q5/MiU3yI8G/d1IVNctT6A8bsLmaDW',
    'ADMIN'
)
ON CONFLICT DO NOTHING;
