# Revisão para publicação no GitHub

## Conferido

- Integridade do ZIP original e presença dos 51 arquivos.
- Sintaxe de todos os arquivos Python `.py`.
- Estrutura e leitura dos CSVs.
- Vídeo MP4 incluído e arquivo PBIX presente.
- `.gitignore` ajustado para permitir os CSVs sintéticos públicos.
- Campos de nome e identificação em `data/raw/` substituídos por marcadores sintéticos na cópia de publicação.

## Limites da revisão

- Não houve conexão ao SQL Server PC03, execução dos scripts PowerShell ou abertura do PBIX no Power BI Desktop.
- O banco local já recebeu o lote de seis registros; **não o reaplique no mesmo banco**.
- O vídeo documenta o ambiente local original, não uma execução sobre esta cópia sanitizada.
- A planilha Excel contém apenas amostras; as bases completas estão nos CSVs.
- Scripts antigos de carga inicial podem sobrescrever dados: use somente em banco de testes e após backup.
- O agendamento de Windows e a atualização do Power BI são processos separados.

## Atenção

Antes de executar em outra máquina, configure servidor SQL, driver ODBC e credenciais de acesso. Os dados são fictícios e não devem ser utilizados para decisões clínicas ou financeiras reais.
