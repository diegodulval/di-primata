-- 014: normaliza campo marca de produto → referência à tabela marca
--
-- 1. Cria registros em marca para cada valor distinto de produto.marca por tenant
-- 2. Preenche produto.marca_id apontando para o registro correspondente

INSERT INTO marca (tenant_id, nome)
SELECT DISTINCT tenant_id, trim(marca)
FROM produto
WHERE marca IS NOT NULL AND trim(marca) <> ''
ON CONFLICT (tenant_id, nome) DO NOTHING;

UPDATE produto p
SET marca_id = m.id
FROM marca m
WHERE m.tenant_id = p.tenant_id
  AND m.nome = trim(p.marca)
  AND p.marca IS NOT NULL
  AND trim(p.marca) <> ''
  AND p.marca_id IS NULL;
