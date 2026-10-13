# Análise de Faturamento Médico | SQL, Python, Power BI e IA

Projeto de portfólio com **dados simulados**, voltado à análise financeira de faturamento médico, glosas, contas a receber e priorização de cobranças.

## O que foi desenvolvido

- **SQL Server:** estrutura `v2`, consolidação de faturamento e views analíticas.
- **Python:** importação incremental de CSV, comparação de chaves e prevenção de duplicidades.
- **Power BI:** três páginas — Visão Financeira, Contas a Receber, Glosas e Prioridades.
- **IA / machine learning:** experimentos de classificação de risco de glosa e exportação de previsões; resumo gerencial com apoio de IA generativa.
- **Automação local:** tarefa diária do Windows configurada no ambiente de desenvolvimento para executar a carga incremental às 9h30.

## Arquitetura

`CSV sintético → Python (carga incremental) → SQL Server (v2) → Power BI`

`SQL Server → Python (modelo experimental de glosas) → análise gerencial`

## Visualização

- [Dashboard em PDF](docs/Dashboard_Gestao_Financeira_e_Glosas.pdf)
- [Arquivo Power BI Desktop](powerbi/Dashboard_Gestao_Financeira_e_Glosas.pbix)
- [Resumo gerencial de IA](docs/resumo_gerencial_ia.md)
- [Demonstração em vídeo](docs/Faturamento_Medico.mp4)

## Organização

- `sql/`: scripts SQL de estrutura, views e verificações.
- `python/`: scripts de carga e experimentos de modelagem.
- `powerbi/`: arquivo `.pbix` do painel.
- `docs/`: relatório PDF, resumo gerencial e documentação técnica histórica.
- `automacao/`: scripts auxiliares de automação; **não execute instaladores sem revisar as configurações**.
- `data/raw/2025/`: CSVs sintéticos de entrada. `data/processed/`: exportações e contexto de análise. `excel/`: planilha de consulta (não usada na carga).

## Execução em ambiente próprio

Requer SQL Server, Python, driver ODBC do SQL Server e as bibliotecas em `requirements.txt`. Os scripts foram criados para o ambiente local `PC03` e o banco `Projeto_Faturamento_Medico`: **adapte servidor, banco e caminhos** antes de executar em outro computador. Execute os SQLs de acordo com as dependências do banco; não execute cargas iniciais ou scripts de substituição de despesas em uma base existente sem backup e revisão.

A carga incremental principal está em `python/03_carga_incremental_segura_corrigida.py`: por padrão, roda em simulação; `--aplicar` habilita gravação. Os scripts de automação usam `data/raw/2025` por padrão, em modo simulação. O instalador cria uma NOVA tarefa diária às 09h30 somente quando executado manualmente; não altera a tarefa já configurada no Windows. Para gravação, use `-Aplicar` apenas depois de verificar a simulação e fazer backup.

## Status e limites

- Consultas do Power BI conectadas ao SQL Server e atualização **manual** conferida no ambiente de desenvolvimento.
- Agendamento local do Python configurado; o Windows retornou `0x0` em uma execução. A execução de uma carga nova por esse agendamento ainda não foi comprovada com um novo CSV.
- **Não foi configurada atualização agendada do Power BI Service** (gateway/licença podem ser necessários).
- O modelo de glosas é **experimental**, não é ferramenta clínica nem sistema validado para decisões reais. Os resultados apresentados no resumo se referem a uma base simulada e a um recorte específico.
- Os CSVs incluídos nesta versão pública foram preparados como dados sintéticos; nomes e identificadores potencialmente pessoais nas bases brutas foram substituídos por marcadores genéricos. Não inclua dados de pacientes reais neste repositório.

## Observação sobre os dados

Todos os resultados são demonstrativos e usam dados sintéticos. A edição pública anonimiza campos de identificação das bases brutas, mantendo valores e datas para fins analíticos. A carga SQL local e o vídeo foram realizados sobre uma cópia de desenvolvimento e podem apresentar nomes de exemplo diferentes.

## Execução segura, sem alterar dados

No PowerShell, a partir da pasta raiz do projeto:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\automacao\executar_carga.ps1"
```

Para importar **somente registros novos** (depois de backup e conferência), acrescente `-Aplicar`. A carga do Python **não atualiza automaticamente a interface do Power BI Desktop**: use Página Inicial > Atualizar.

**Não execute** `python/03_carga_automatica.py` ou `python/03_carga_inicial_2025.py` sobre o banco já utilizado: esses arquivos são cargas de snapshot e substituem registros.

### Planilha Excel

`excel/Consulta_Bases_2025_AMOSTRA.xlsx` é uma planilha de **consulta com índice e amostras de até 30 registros por base**, não contém todas as linhas. As bases completas estão nos arquivos CSV em `data/raw/2025` e `data/processed`.

## Reprodutibilidade e publicação

Os CSVs da pasta `data/raw/2025/` estão incluídos para estudo. O arquivo `atendimentos_particulares_nova_atualizacao_dezembro_2025.csv` representa um lote sintético de seis registros para demonstração da carga incremental. **Não execute novamente o lote sobre uma base já atualizada**, pois ele foi importado no ambiente original.

O Power BI usa uma conexão local (`PC03`) e não funciona automaticamente em outros computadores; ajuste a origem no Power Query. As consultas SQL, os dados e o PBIX foram preservados; **a execução ponta a ponta em outro ambiente não foi validada**. O agendamento Windows é opcional e o Power BI Desktop é atualizado manualmente.

Consulte [a revisão para publicação](docs/REVISAO_GITHUB.md) antes de executar qualquer carga ou automação.
