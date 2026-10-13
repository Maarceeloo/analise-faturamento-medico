
IF NOT EXISTS (
    SELECT 1
    FROM sys.schemas
    WHERE name = 'v2'
)
BEGIN
    EXEC('CREATE SCHEMA v2');
END;

SELECT name AS Esquema
FROM sys.schemas
WHERE name = 'v2';
