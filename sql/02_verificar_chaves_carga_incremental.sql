/* Diagnostico somente leitura: candidatos a chave para carga incremental.
   Execute no banco Projeto_Faturamento_Medico. Nao altera dados. */
SET NOCOUNT ON;
SELECT DB_NAME() AS banco_atual, @@SERVERNAME AS servidor;

-- Particular: ID de atendimento
SELECT 'atendimentos_particulares' AS tabela,
       COUNT(*) AS total_linhas,
       COUNT(DISTINCT id_atendimento) AS ids_distintos,
       SUM(CASE WHEN id_atendimento IS NULL OR LTRIM(RTRIM(id_atendimento)) = '' THEN 1 ELSE 0 END) AS ids_vazios
FROM v2.atendimentos_particulares;

-- Bradesco: guia + item (chave candidata, ainda nao confirmada)
SELECT 'faturamento_bradesco' AS tabela,
       COUNT(*) AS total_linhas,
       COUNT(DISTINCT CONCAT(COALESCE(numero_guia_prestador,'<NULL>'), '|', COALESCE(CONVERT(nvarchar(100),sequencial_item),'<NULL>'))) AS combinacoes_guia_item,
       SUM(CASE WHEN numero_guia_prestador IS NULL OR sequencial_item IS NULL THEN 1 ELSE 0 END) AS linhas_chave_incompleta
FROM v2.faturamento_bradesco;

-- Unimed: guia + procedimento + data (apenas candidato; repeticoes podem ser validas)
SELECT 'faturamento_unimed' AS tabela,
       COUNT(*) AS total_linhas,
       COUNT(DISTINCT CONCAT(COALESCE(numero_guia_prestador,'<NULL>'), '|', COALESCE(codigo_tuss,'<NULL>'), '|', COALESCE(CONVERT(nvarchar(30),data_atendimento,126),'<NULL>'))) AS combinacoes_guia_procedimento_data,
       SUM(CASE WHEN numero_guia_prestador IS NULL OR codigo_tuss IS NULL OR data_atendimento IS NULL THEN 1 ELSE 0 END) AS linhas_chave_incompleta
FROM v2.faturamento_unimed;

-- Exemplos de repeticoes que exigem avaliacao antes de escolher uma chave
SELECT TOP (10) numero_guia_prestador, sequencial_item, COUNT(*) AS ocorrencias
FROM v2.faturamento_bradesco
GROUP BY numero_guia_prestador, sequencial_item
HAVING COUNT(*) > 1
ORDER BY ocorrencias DESC;

SELECT TOP (10) numero_guia_prestador, codigo_tuss, data_atendimento, COUNT(*) AS ocorrencias
FROM v2.faturamento_unimed
GROUP BY numero_guia_prestador, codigo_tuss, data_atendimento
HAVING COUNT(*) > 1
ORDER BY ocorrencias DESC;
