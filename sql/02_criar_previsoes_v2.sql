/* Projecoes sinteticas de compromissos para 2026, a partir de saldos de 2025.
   Nao modifica dados realizados nem trata glosas como recebimentos certos.
   A data projetada e deslocada 12 meses da data de referencia em 2025.
*/
USE [Projeto_Faturamento_Medico];
GO
CREATE OR ALTER VIEW v2.Contas_Futuras AS
WITH entradas_base AS (
 SELECT
  CAST(CONCAT(N'ENT-',ROW_NUMBER() OVER (ORDER BY operadora,id_registro,data_atendimento)) AS nvarchar(80)) AS id_conta,
  CAST(N'Entrada' AS nvarchar(30)) AS tipo,
  CAST(CONCAT(N'Recebimento pendente - ',operadora,N' / ',id_registro) AS nvarchar(300)) AS descricao,
  CAST(N'Faturamento' AS nvarchar(150)) AS categoria,
  CAST(COALESCE(data_prevista_pagamento,data_atendimento) AS date) AS data_referencia,
  CAST(CASE WHEN valor_apresentado - COALESCE(valor_pago,0) - COALESCE(valor_glosado,0) > 0
       THEN valor_apresentado - COALESCE(valor_pago,0) - COALESCE(valor_glosado,0) ELSE 0 END AS decimal(19,2)) AS valor_previsto_rs,
  CAST(N'Previsto' AS nvarchar(60)) AS status,
  CAST(NULL AS nvarchar(100)) AS forma_prevista,
  CAST(N'Financeiro' AS nvarchar(100)) AS responsavel,
  CAST(N'Projecao sintetica para 2026 baseada em saldo de 2025; nao representa data confirmada' AS nvarchar(500)) AS observacao
 FROM v2.vw_faturamento_consolidado
 WHERE elegivel_cobranca = 1 AND status_padronizado NOT IN (N'Recebido',N'Excluido da cobranca')
), saidas_base AS (
 SELECT
  CAST(CONCAT(N'SAI-',id_despesa) AS nvarchar(80)) AS id_conta,
  CAST(N'Saida' AS nvarchar(30)) AS tipo,
  CAST(descricao AS nvarchar(300)) AS descricao,
  CAST(categoria AS nvarchar(150)) AS categoria,
  CAST(data_vencimento AS date) AS data_referencia,
  CAST(CASE WHEN COALESCE(valor_previsto_rs,0)-COALESCE(valor_pago_rs,0)>0
       THEN COALESCE(valor_previsto_rs,0)-COALESCE(valor_pago_rs,0) ELSE 0 END AS decimal(19,2)) AS valor_previsto_rs,
  CAST(N'Previsto' AS nvarchar(60)) AS status,
  CAST(forma_pagamento AS nvarchar(100)) AS forma_prevista,
  CAST(N'Financeiro' AS nvarchar(100)) AS responsavel,
  CAST(N'Projecao sintetica de pagamento para 2026 baseada em despesa pendente de 2025' AS nvarchar(500)) AS observacao
 FROM v2.Despesas WHERE status <> N'Pago'
), contas AS (
 SELECT * FROM entradas_base
 UNION ALL
 SELECT * FROM saidas_base
)
SELECT id_conta, tipo, descricao, categoria,
       CAST(DATEADD(year,1,data_referencia) AS date) AS data_prevista,
       valor_previsto_rs, status, forma_prevista, responsavel, observacao
FROM contas
WHERE valor_previsto_rs > 0 AND data_referencia >= '20250101' AND data_referencia < '20260101';
GO
