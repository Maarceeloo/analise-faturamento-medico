/* Projeto Faturamento Médico V2 | Validação exploratória reproduzível
   Executar no banco Projeto_Faturamento_Medico, após a carga das tabelas v2.
   Consultas somente leitura. Nenhum dado é modificado.
*/
SET NOCOUNT ON;

-- 1. Cobertura e volume
SELECT 'Particular' AS Origem, COUNT(*) AS Registros, MIN(data_atendimento) AS Primeira_Data, MAX(data_atendimento) AS Ultima_Data FROM v2.atendimentos_particulares
UNION ALL SELECT 'Bradesco', COUNT(*), MIN(data_atendimento), MAX(data_atendimento) FROM v2.faturamento_bradesco
UNION ALL SELECT 'Unimed', COUNT(*), MIN(data_atendimento), MAX(data_atendimento) FROM v2.faturamento_unimed;

-- 2. Conferência financeira (totais históricos, não equivalem necessariamente a valores em aberto)
SELECT 'Particular' AS Origem, COUNT(*) AS Registros, SUM(valor_cobrado_rs) AS Valor_Apresentado, SUM(valor_recebido_rs) AS Valor_Recebido FROM v2.atendimentos_particulares
UNION ALL SELECT 'Bradesco', COUNT(*), SUM(valor_total_apresentado), SUM(valor_pago_item) FROM v2.faturamento_bradesco
UNION ALL SELECT 'Unimed', COUNT(*), SUM(valor_apresentado), SUM(valor_pago) FROM v2.faturamento_unimed;

-- 3. Nulos em campos fundamentais
SELECT 'Particular' AS Origem, SUM(CASE WHEN data_atendimento IS NULL THEN 1 ELSE 0 END) AS Datas_Nulas, SUM(CASE WHEN valor_cobrado_rs IS NULL THEN 1 ELSE 0 END) AS Valores_Nulos FROM v2.atendimentos_particulares
UNION ALL SELECT 'Bradesco', SUM(CASE WHEN data_atendimento IS NULL THEN 1 ELSE 0 END), SUM(CASE WHEN valor_total_apresentado IS NULL THEN 1 ELSE 0 END) FROM v2.faturamento_bradesco
UNION ALL SELECT 'Unimed', SUM(CASE WHEN data_atendimento IS NULL THEN 1 ELSE 0 END), SUM(CASE WHEN valor_apresentado IS NULL THEN 1 ELSE 0 END) FROM v2.faturamento_unimed;

-- 4. Duplicidades potenciais: a combinação de campos é diferente por fonte
SELECT id_atendimento, COUNT(*) AS Quantidade FROM v2.atendimentos_particulares GROUP BY id_atendimento HAVING COUNT(*) > 1 ORDER BY Quantidade DESC;
SELECT numero_guia_prestador, sequencial_item, COUNT(*) AS Quantidade FROM v2.faturamento_bradesco GROUP BY numero_guia_prestador, sequencial_item HAVING COUNT(*) > 1 ORDER BY Quantidade DESC;
SELECT numero_guia_prestador, codigo_tuss, data_atendimento, COUNT(*) AS Quantidade FROM v2.faturamento_unimed GROUP BY numero_guia_prestador, codigo_tuss, data_atendimento HAVING COUNT(*) > 1 ORDER BY Quantidade DESC;

-- 5. Glosas: valor e quantidade de itens
SELECT 'Bradesco' AS Operadora, COUNT(*) AS Total_Itens, SUM(CASE WHEN valor_glosado > 0 THEN 1 ELSE 0 END) AS Itens_Glosados, SUM(valor_total_apresentado) AS Valor_Apresentado, SUM(valor_glosado) AS Valor_Glosado, SUM(valor_pago_item) AS Valor_Pago FROM v2.faturamento_bradesco
UNION ALL SELECT 'Unimed', COUNT(*), SUM(CASE WHEN valor_glosado > 0 THEN 1 ELSE 0 END), SUM(valor_apresentado), SUM(valor_glosado), SUM(valor_pago) FROM v2.faturamento_unimed;

-- 6. Distribuição dos status originais, sem normalização prematura
SELECT 'Bradesco' AS Origem, status_pagamento AS Status_Original, COUNT(*) AS Quantidade FROM v2.faturamento_bradesco GROUP BY status_pagamento
UNION ALL SELECT 'Unimed', status_guia, COUNT(*) FROM v2.faturamento_unimed GROUP BY status_guia
UNION ALL SELECT 'Particular', status_recebimento, COUNT(*) FROM v2.atendimentos_particulares GROUP BY status_recebimento
ORDER BY Origem, Quantidade DESC;

-- 7. Triagem bruta de pendências na data de referência: NÃO é inadimplência líquida
DECLARE @DataReferencia date = '2025-12-31';
SELECT 'Bradesco' AS Operadora, COUNT(*) AS Itens_Sinalizados,
 SUM(CASE WHEN valor_total_apresentado > ISNULL(valor_pago_item,0) THEN valor_total_apresentado - ISNULL(valor_pago_item,0) ELSE 0 END) AS Saldo_Bruto
FROM v2.faturamento_bradesco
WHERE data_prevista_pagamento <= @DataReferencia
  AND (data_pagamento IS NULL OR data_pagamento > @DataReferencia OR valor_pago_item < valor_total_apresentado)
UNION ALL
SELECT 'Unimed', COUNT(*),
 SUM(CASE WHEN valor_apresentado > ISNULL(valor_pago,0) THEN valor_apresentado - ISNULL(valor_pago,0) ELSE 0 END)
FROM v2.faturamento_unimed
WHERE data_prevista_pagamento <= @DataReferencia
  AND (data_pagamento IS NULL OR data_pagamento > @DataReferencia OR valor_pago < valor_apresentado);

/* Limitação: valores recebidos são os presentes na base atual e podem incluir
   pagamentos posteriores à data de referência. O saldo bruto inclui glosas,
   diferenças e ajustes. Não usar esta triagem como KPI final de atraso. */
