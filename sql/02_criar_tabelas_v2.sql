/* Faturamento Medico V2 - estruturas iniciais (sem alterar a V1)
   Executar no banco Projeto_Faturamento_Medico.
   As tabelas são cópias vazias da estrutura original; NÃO importam dados.
   SELECT INTO não copia chaves, índices nem constraints: serão definidos após validação.
*/
SET NOCOUNT ON;
IF SCHEMA_ID(N'v2') IS NULL
    THROW 50001, 'O esquema v2 ainda nao existe.', 1;

IF OBJECT_ID(N'dbo.atendimentos_particulares', N'U') IS NULL
 OR OBJECT_ID(N'dbo.faturamento_bradesco', N'U') IS NULL
 OR OBJECT_ID(N'dbo.faturamento_unimed', N'U') IS NULL
    THROW 50002, 'Uma ou mais tabelas originais nao foram encontradas.', 1;

IF OBJECT_ID(N'v2.atendimentos_particulares', N'U') IS NULL
    SELECT TOP (0) * INTO v2.atendimentos_particulares FROM dbo.atendimentos_particulares;

IF OBJECT_ID(N'v2.faturamento_bradesco', N'U') IS NULL
    SELECT TOP (0) * INTO v2.faturamento_bradesco FROM dbo.faturamento_bradesco;

IF OBJECT_ID(N'v2.faturamento_unimed', N'U') IS NULL
    SELECT TOP (0) * INTO v2.faturamento_unimed FROM dbo.faturamento_unimed;

IF OBJECT_ID(N'v2.controle_cargas', N'U') IS NULL
BEGIN
    CREATE TABLE v2.controle_cargas (
        id_carga BIGINT IDENTITY(1,1) PRIMARY KEY,
        nome_arquivo NVARCHAR(260) NOT NULL,
        origem NVARCHAR(80) NOT NULL,
        hash_arquivo CHAR(64) NULL,
        iniciado_em DATETIME2(0) NOT NULL DEFAULT SYSDATETIME(),
        finalizado_em DATETIME2(0) NULL,
        registros_lidos INT NULL,
        registros_inseridos INT NULL,
        registros_atualizados INT NULL,
        status NVARCHAR(30) NOT NULL DEFAULT N'INICIADA',
        mensagem NVARCHAR(2000) NULL
    );
END;

SELECT s.name AS esquema, t.name AS tabela, SUM(CASE WHEN p.index_id IN (0,1) THEN p.rows ELSE 0 END) AS linhas
FROM sys.tables t
JOIN sys.schemas s ON s.schema_id = t.schema_id
JOIN sys.partitions p ON p.object_id = t.object_id
WHERE s.name = N'v2'
GROUP BY s.name, t.name
ORDER BY t.name;
