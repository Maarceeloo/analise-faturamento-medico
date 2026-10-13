USE [Projeto_Faturamento_Medico];
GO
SELECT 'Despesas' AS origem, COUNT(*) AS registros, MIN(data_competencia) AS inicio, MAX(data_competencia) AS fim FROM v2.Despesas
UNION ALL
SELECT 'Contas previstas',COUNT(*),MIN(data_prevista),MAX(data_prevista) FROM v2.Contas_Futuras;
SELECT YEAR(data_competencia) ano,MONTH(data_competencia) mes,COUNT(*) registros,
 SUM(valor_previsto_rs) previsto,SUM(valor_pago_rs) pago
FROM v2.Despesas GROUP BY YEAR(data_competencia),MONTH(data_competencia) ORDER BY ano,mes;
SELECT tipo,COUNT(*) registros,SUM(valor_previsto_rs) valor_previsto FROM v2.Contas_Futuras GROUP BY tipo;
SELECT COUNT(*) fora_2025 FROM v2.Despesas
WHERE YEAR(data_competencia)<>2025 OR YEAR(data_vencimento)<>2025 OR (data_pagamento IS NOT NULL AND YEAR(data_pagamento)<>2025);
