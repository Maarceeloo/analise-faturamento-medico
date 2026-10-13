/* Execute em Projeto_Faturamento_Medico ANTES do Python. Não altera as 3 tabelas v2 existentes. */
USE [Projeto_Faturamento_Medico];
GO
IF SCHEMA_ID(N'v2') IS NULL EXEC(N'CREATE SCHEMA v2');
GO
IF OBJECT_ID(N'v2.Despesas', N'U') IS NULL
CREATE TABLE v2.Despesas (
 id_despesa nvarchar(60) NOT NULL PRIMARY KEY,
 data_competencia date NULL,
 data_vencimento date NULL,
 data_pagamento date NULL,
 categoria nvarchar(150) NULL,
 fornecedor nvarchar(200) NULL,
 descricao nvarchar(300) NULL,
 forma_pagamento nvarchar(100) NULL,
 valor_previsto_rs decimal(19,2) NULL,
 valor_pago_rs decimal(19,2) NULL,
 status nvarchar(60) NULL,
 recorrente nvarchar(30) NULL,
 observacao nvarchar(500) NULL
);
GO
