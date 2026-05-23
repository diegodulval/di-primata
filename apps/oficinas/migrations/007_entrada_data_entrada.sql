-- Entrada NF-e: data de entrada editável + status ABERTA/PROCESSADA

-- data_entrada: data efetiva de entrada da mercadoria (editável pelo atendente)
ALTER TABLE entrada_nfe  ADD COLUMN IF NOT EXISTS data_entrada DATE;
ALTER TABLE item_entrada ADD COLUMN IF NOT EXISTS data_entrada DATE;
