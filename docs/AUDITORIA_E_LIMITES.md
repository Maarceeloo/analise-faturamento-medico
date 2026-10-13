# Auditoria do pacote

Revisão estática de estrutura e conteúdo, sem acesso ao SQL Server PC03 nem ao Power BI Desktop.

- Todos os arquivos Python foram analisados sintaticamente.
- Arquivos CSV foram lidos para conferir estrutura e contagem de linhas.
- O ZIP foi validado quanto à integridade após criação.
- A automação agora aponta para `data/raw/2025`, pasta presente no pacote.
- O instalador não substitui tarefas existentes e mantém simulação por padrão.
- A planilha Excel é para consulta; CSV é a fonte para o script de carga.
- **Não testado neste ambiente:** execução de PowerShell/Windows Task Scheduler, conexão SQL Server, execução das views, atualização do PBIX e indicadores.

## Arquivos CSV

CSV: data/processed/despesas_2025.csv | 265 linhas | 13 colunas
CSV: data/processed/faturamento_consolidado.csv | 1290 linhas | 17 colunas
CSV: data/processed/previsoes_glosas_teste.csv | 504 linhas | 11 colunas
CSV: data/raw/2025/atendimentos_particulares_2025.csv | 1040 linhas | 21 colunas
CSV: data/raw/2025/bradesco_saude_2025.csv | 1236 linhas | 37 colunas
CSV: data/raw/2025/guias_unimed_2025.csv | 1344 linhas | 36 colunas
CSV: data/raw/2025/producao_bradesco_2025.csv | 1236 linhas | 37 colunas
CSV: data/raw/despesas_referencia_2026.csv | 134 linhas | 13 colunas
