/*
Projeto: Faturamento Medico V2 | 05_views_analiticas.sql
Objetivo: camada analitica para Power BI, sem modificar tabelas de origem.
Executar no banco Projeto_Faturamento_Medico, apos as cargas v2.
IMPORTANTE: saldos e flags de pendencia sao triagem operacional, nao inadimplencia contábil.
Nao publicar dados reais de pacientes, beneficiarios ou prestadores no GitHub.
*/

USE [Projeto_Faturamento_Medico];
GO

CREATE OR ALTER VIEW v2.vw_faturamento_consolidado AS
SELECT
    CAST('Particular' AS nvarchar(20)) AS operadora,
    CAST(id_atendimento AS nvarchar(100)) AS id_registro,
    CAST(NULL AS nvarchar(100)) AS numero_guia,
    data_atendimento,
    data_prevista_recebimento AS data_prevista_pagamento,
    data_recebimento AS data_pagamento,
    CAST(status_recebimento AS nvarchar(100)) AS status_original,
    CAST(CASE
        WHEN status_recebimento IN (N'Cancelado', N'Cortesia') THEN N'Excluido da cobranca'
        WHEN status_recebimento = N'Recebido' THEN N'Recebido'
        WHEN status_recebimento = N'Pendente' THEN N'Pendente'
        ELSE N'Verificar'
    END AS nvarchar(50)) AS status_padronizado,
    CAST(valor_cobrado_rs AS decimal(19,2)) AS valor_apresentado,
    CAST(valor_recebido_rs AS decimal(19,2)) AS valor_pago,
    CAST(0 AS decimal(19,2)) AS valor_glosado,
    CAST(NULL AS decimal(19,2)) AS valor_recuperado,
    CAST(CASE WHEN status_recebimento IN (N'Cancelado', N'Cortesia') THEN 0 ELSE 1 END AS bit) AS elegivel_cobranca
FROM v2.atendimentos_particulares
UNION ALL
SELECT
    CAST('Bradesco' AS nvarchar(20)),
    CAST(CONCAT(COALESCE(numero_guia_prestador,N''),N'|',COALESCE(CONVERT(nvarchar(20),sequencial_item),N''),N'|',COALESCE(codigo_tuss,N'')) AS nvarchar(100)),
    CAST(numero_guia_prestador AS nvarchar(100)),
    data_atendimento,
    data_prevista_pagamento,
    data_pagamento,
    CAST(status_pagamento AS nvarchar(100)),
    CAST(CASE
        WHEN status_pagamento = N'PAGO' THEN N'Recebido'
        WHEN status_pagamento = N'EM ANÁLISE' THEN N'Em processamento'
        ELSE N'Verificar'
    END AS nvarchar(50)),
    CAST(valor_total_apresentado AS decimal(19,2)),
    CAST(valor_pago_item AS decimal(19,2)),
    CAST(valor_glosado AS decimal(19,2)),
    CAST(valor_recuperado AS decimal(19,2)),
    CAST(1 AS bit)
FROM v2.faturamento_bradesco
UNION ALL
SELECT
    CAST('Unimed' AS nvarchar(20)),
    CAST(CONCAT(COALESCE(numero_guia_prestador,N''),N'|',COALESCE(codigo_tuss,N''),N'|',COALESCE(CONVERT(nvarchar(10),data_atendimento,23),N'')) AS nvarchar(100)),
    CAST(numero_guia_prestador AS nvarchar(100)),
    data_atendimento,
    data_prevista_pagamento,
    data_pagamento,
    CAST(status_guia AS nvarchar(100)),
    CAST(CASE
        WHEN status_guia = N'Paga integralmente' THEN N'Recebido'
        WHEN status_guia = N'Paga com glosa parcial' THEN N'Glosa parcial'
        WHEN status_guia = N'Glosada integralmente' THEN N'Glosa integral'
        WHEN status_guia IN (N'Aguardando processamento', N'Em análise pela operadora', N'Protocolada') THEN N'Em processamento'
        ELSE N'Verificar'
    END AS nvarchar(50)),
    CAST(valor_apresentado AS decimal(19,2)),
    CAST(valor_pago AS decimal(19,2)),
    CAST(valor_glosado AS decimal(19,2)),
    CAST(valor_recuperado AS decimal(19,2)),
    CAST(1 AS bit)
FROM v2.faturamento_unimed;
GO

/* Visao de glosas: uma linha por item com valor glosado positivo. */
CREATE OR ALTER VIEW v2.vw_glosas_analiticas AS
SELECT
    operadora, id_registro, numero_guia, data_atendimento,
    status_original, status_padronizado,
    valor_apresentado, valor_pago, valor_glosado, valor_recuperado,
    CAST(CASE WHEN valor_recuperado IS NOT NULL AND valor_recuperado > 0
              THEN valor_recuperado ELSE 0 END AS decimal(19,2)) AS recuperacao_informada
FROM v2.vw_faturamento_consolidado
WHERE operadora IN (N'Bradesco', N'Unimed')
  AND valor_glosado > 0;
GO

/* Triagem de saldo bruto: nao equivale a inadimplencia ou saldo exigivel.
   A data de referencia deve ser aplicada no Power BI ou em consulta parametrizada.
   A view usa dados do snapshot, que podem incluir recebimentos posteriores. */
CREATE OR ALTER VIEW v2.vw_pendencias_financeiras AS
SELECT
    operadora, id_registro, numero_guia,
    data_atendimento, data_prevista_pagamento, data_pagamento,
    status_original, status_padronizado,
    valor_apresentado, valor_pago, valor_glosado, valor_recuperado,
    CAST(CASE WHEN valor_apresentado > COALESCE(valor_pago,0)
              THEN valor_apresentado - COALESCE(valor_pago,0)
              ELSE 0 END AS decimal(19,2)) AS saldo_bruto_nao_recebido,
    CAST(CASE WHEN data_prevista_pagamento IS NULL THEN N'Sem vencimento informado'
              WHEN data_prevista_pagamento < CONVERT(date, GETDATE())
                   AND valor_apresentado > COALESCE(valor_pago,0) THEN N'Vencimento ultrapassado - verificar'
              WHEN valor_apresentado > COALESCE(valor_pago,0) THEN N'A vencer ou em processamento'
              ELSE N'Sem saldo bruto' END AS nvarchar(60)) AS classificacao_preliminar
FROM v2.vw_faturamento_consolidado
WHERE elegivel_cobranca = 1
  AND valor_apresentado > COALESCE(valor_pago,0);
GO

/* Conferencia rapida apos executar: resultados esperados no snapshot de 2025:
   Particular 1040; Bradesco 1236; Unimed 1344. */
SELECT operadora, COUNT(*) AS registros,
       SUM(valor_apresentado) AS apresentado,
       SUM(valor_pago) AS pago
FROM v2.vw_faturamento_consolidado
GROUP BY operadora
ORDER BY operadora;

SELECT operadora, COUNT(*) AS itens_glosados,
       SUM(valor_glosado) AS total_glosado
FROM v2.vw_glosas_analiticas
GROUP BY operadora
ORDER BY operadora;
