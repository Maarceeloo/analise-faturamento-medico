/* DIAGNOSTICO SOMENTE LEITURA — Projeto Faturamento Medico
   Execute no SSMS, conectado ao banco Projeto_Faturamento_Medico.
   Nenhum dado sera alterado.
*/
SET NOCOUNT ON;
SELECT DB_NAME() AS banco_atual, @@SERVERNAME AS servidor;

-- 1. Estrutura das tabelas que recebem faturamento
SELECT s.name AS esquema, t.name AS tabela, c.column_id, c.name AS coluna,
       ty.name AS tipo, c.is_nullable, c.is_identity
FROM sys.tables t
JOIN sys.schemas s ON s.schema_id=t.schema_id
JOIN sys.columns c ON c.object_id=t.object_id
JOIN sys.types ty ON ty.user_type_id=c.user_type_id
WHERE s.name='v2' AND t.name IN ('atendimentos_particulares','faturamento_bradesco','faturamento_unimed','controle_cargas')
ORDER BY t.name, c.column_id;

-- 2. Chaves e indices existentes (evitar cargas duplicadas)
SELECT s.name AS esquema, t.name AS tabela, i.name AS indice,
       i.is_unique, i.is_primary_key, ic.key_ordinal, c.name AS coluna
FROM sys.tables t
JOIN sys.schemas s ON s.schema_id=t.schema_id
JOIN sys.indexes i ON i.object_id=t.object_id
JOIN sys.index_columns ic ON ic.object_id=i.object_id AND ic.index_id=i.index_id
JOIN sys.columns c ON c.object_id=ic.object_id AND c.column_id=ic.column_id
WHERE s.name='v2' AND t.name IN ('atendimentos_particulares','faturamento_bradesco','faturamento_unimed')
  AND i.index_id>0 AND ic.key_ordinal>0
ORDER BY t.name, i.name, ic.key_ordinal;

-- 3. Quantidade de registros atuais (nao modifica tabelas)
SELECT 'atendimentos_particulares' AS tabela, COUNT_BIG(*) AS linhas FROM v2.atendimentos_particulares
UNION ALL SELECT 'faturamento_bradesco', COUNT_BIG(*) FROM v2.faturamento_bradesco
UNION ALL SELECT 'faturamento_unimed', COUNT_BIG(*) FROM v2.faturamento_unimed;

-- 4. Situacao do historico de cargas, se a tabela existir
IF OBJECT_ID('v2.controle_cargas','U') IS NOT NULL
    EXEC(N'SELECT TOP (20) id_carga, nome_arquivo, origem, hash_arquivo, iniciado_em, finalizado_em, registros_lidos, registros_inseridos, registros_atualizados, status, mensagem FROM v2.controle_cargas ORDER BY id_carga DESC;');
