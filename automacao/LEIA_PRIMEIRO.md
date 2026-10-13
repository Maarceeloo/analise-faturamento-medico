# Automação local (Windows)

- `executar_carga.ps1` usa, por padrão, os CSVs incluídos em `data/raw/2025`. Sem `-Aplicar`, somente simula.
- Para gravar, revise o resultado da simulação, faça backup do banco e use `-Aplicar`.
- `instalar_agendamento.ps1` é **opcional** e cria uma NOVA tarefa `Faturamento Medico Portfolio - Carga Incremental`, diariamente às 09h30, em **modo simulação por padrão**. Não altera a tarefa antiga `Carga Incremental - Faturamento Médico` já criada no Windows.
- O agendador local requer computador ligado, acesso ao SQL Server, driver ODBC e dependências Python instaladas.
- Power BI Desktop requer clicar em **Atualizar**; a tarefa não configura Power BI Service/gateway.

Executar simulação, a partir da pasta raiz:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\automacao\executar_carga.ps1"
```

Nenhuma execução ou agendamento foi instalado neste ambiente de revisão.
