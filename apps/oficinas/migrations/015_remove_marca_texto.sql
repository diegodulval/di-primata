-- 015: remove campo texto marca de produto (normalizado para FK marca_id na 014)

ALTER TABLE produto DROP COLUMN IF EXISTS marca;
