/* Camada de indicadores SQL reutilizável para o Power BI e futuros painéis.
   Recebimentos pelo mês de pagamento; despesas pelo mês de pagamento.
   Faturamento pelo mês do atendimento (competência operacional).
*/
USE [Projeto_Faturamento_Medico];
GO
CREATE OR ALTER VIEW v2.vw_fluxo_financeiro_mensal AS
WITH meses AS (
 SELECT v.mes FROM (VALUES (1),(2),(3),(4),(5),(6),(7),(8),(9),(10),(11),(12)) v(mes)
), faturamento AS (
 SELECT MONTH(data_atendimento) mes, SUM(valor_apresentado) valor
 FROM v2.vw_faturamento_consolidado
 WHERE data_atendimento >= '20250101' AND data_atendimento < '20260101'
 GROUP BY MONTH(data_atendimento)
), recebimentos AS (
 SELECT MONTH(data_pagamento) mes,SUM(valor_pago) valor
 FROM v2.vw_faturamento_consolidado
 WHERE data_pagamento >= '20250101' AND data_pagamento < '20260101'
 GROUP BY MONTH(data_pagamento)
), despesas AS (
 SELECT MONTH(data_pagamento) mes,SUM(valor_pago_rs) valor
 FROM v2.Despesas
 WHERE data_pagamento >= '20250101' AND data_pagamento < '20260101'
 GROUP BY MONTH(data_pagamento)
)
SELECT CAST(DATEFROMPARTS(2025,m.mes,1) AS date) AS mes_referencia,
 CAST(COALESCE(f.valor,0) AS decimal(19,2)) AS faturamento_competencia,
 CAST(COALESCE(r.valor,0) AS decimal(19,2)) AS recebimentos_caixa,
 CAST(COALESCE(d.valor,0) AS decimal(19,2)) AS despesas_pagas_caixa,
 CAST(COALESCE(r.valor,0)-COALESCE(d.valor,0) AS decimal(19,2)) AS resultado_caixa
FROM meses m
LEFT JOIN faturamento f ON f.mes=m.mes
LEFT JOIN recebimentos r ON r.mes=m.mes
LEFT JOIN despesas d ON d.mes=m.mes;
GO
