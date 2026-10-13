# Projeto Faturamento Médico — Integração financeira 2025

Este pacote **complementa** o SQL e Python v2 existentes. Não substitui as três bases de faturamento e não edita o PBIX automaticamente.

## O que foi preparado

- `despesas_referencia_2026.csv`: extração da aba Despesas do Excel original, **somente como referência sintética**.
- `gerar_e_carregar_despesas_2025.py`: gera `despesas_2025.csv` com as **mesmas 13 colunas** e carrega a tabela `v2.Despesas` via SQL Server.
- `despesas_2025.csv`: resultado gerado e validado, 265 registros, 12 meses, todos os campos de data em 2025.
- `01_criar_despesas_v2.sql`: tabela SQL `v2.Despesas`.
- `02_criar_previsoes_v2.sql`: view SQL `v2.Contas_Futuras` baseada nas **pendências das views v2 de faturamento e das despesas SQL**; não usa a aba antiga Contas_Futuras.
- `03_validacao_financeira_2025.sql`: conferências de período, valores e quantidades.
- `04_indicadores_sql_2025.sql`: view `v2.vw_fluxo_financeiro_mensal`, com faturamento por competência e fluxo de caixa por data de pagamento.
- `04_power_query_sql.txt`: código M para substituir somente a origem das consultas existentes `Despesas` e `Contas_Futuras`.

## Passos no seu computador

1. Salve uma **cópia de segurança** do PBIX atual.
2. Execute `01_criar_despesas_v2.sql` no SSMS, no banco `Projeto_Faturamento_Medico`.
3. Instale `pyodbc` se necessário: `pip install pyodbc`. Requer driver **ODBC Driver 17 for SQL Server** (ou ajuste o driver no script).
4. Na pasta deste pacote, execute: `python gerar_e_carregar_despesas_2025.py --carregar`. Por padrão conecta ao servidor `PC03` com autenticação Windows. **A carga substitui os registros existentes em `v2.Despesas`**, mas não altera outras tabelas.
5. Execute `02_criar_previsoes_v2.sql`, `04_indicadores_sql_2025.sql` e `03_validacao_financeira_2025.sql`, nessa ordem.
6. No Power Query, substitua **apenas** as consultas `Despesas` e `Contas_Futuras` pelo conteúdo indicado em `04_power_query_sql.txt`. Mantenha os nomes dessas consultas para preservar as referências dos visuais.
7. Clique em **Fechar e aplicar**. Confira medidas, filtros, datas e totais antes de considerar o dashboard validado.

## Decisões e limites importantes

- A referência original contém despesas apenas de fevereiro a julho de 2026. Para produzir 2025 completo, o script usa esses meses como padrões para os meses faltantes; os novos registros são **sintéticos**, não históricos reais. A coluna `observacao` documenta a origem de cada registro.
- **Não se trata de trocar apenas o ano** e alegar que os dados são reais. O dashboard e o GitHub devem indicar **dados simulados**.
- A view `v2.Contas_Futuras` representa compromissos previstos/pedidos pendentes de **2025**. Não é projeção futura a partir da data atual (2026), nem garantia de recebimento.
- O SQL da view usa `vw_faturamento_consolidado` e `Despesas`. A aba Excel antiga `Contas_Futuras` não é necessária nem usada.
- Os indicadores financeiros devem separar `data_atendimento` (competência), `data_pagamento` (caixa) e `data_prevista_pagamento` (vencimento). **Não chamar qualquer diferença de faturamento de inadimplência.**
- As **medidas DAX antigas** e a ligação do calendário às despesas **ainda precisam de verificação no Power BI**. Alterar as fontes não garante, por si só, que todos os cartões estejam corretos.
- Não publique dados reais de pacientes nem dados identificáveis no GitHub. Os arquivos de faturamento existentes no projeto devem ser revisados antes da publicação.

## Arquitetura padronizada

Bases sintéticas → Python (geração/carga) → SQL Server (`v2`) → Power BI.

**Novos indicadores**: priorizar views SQL e/ou medidas DAX sobre tabelas SQL, sem reintroduzir planilhas Excel como fontes diretas no Power BI.
