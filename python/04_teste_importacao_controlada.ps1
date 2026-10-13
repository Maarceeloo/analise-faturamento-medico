# Teste controlado da carga incremental. Execute no PowerShell dentro da pasta python.
$ErrorActionPreference = 'Stop'
$projeto = Split-Path -Parent $PSScriptRoot
$script = Join-Path $PSScriptRoot '03_carga_incremental_segura_corrigida.py'
$origem = Join-Path $projeto 'data\raw\2025\atendimentos_particulares_teste_incremental.csv'
$destino = Join-Path $projeto 'data\teste_incremental_isolado'
if (-not (Test-Path -LiteralPath $script)) { throw "Script Python nao encontrado: $script" }
if (-not (Test-Path -LiteralPath $origem)) { throw "CSV de teste nao encontrado: $origem" }
New-Item -ItemType Directory -Force -Path $destino | Out-Null
$arquivosExistentes = @(Get-ChildItem -LiteralPath $destino -File -Filter '*.csv')
if ($arquivosExistentes.Count -gt 0) { throw 'A pasta isolada ja contem CSV(s). Remova-os manualmente antes de continuar.' }
Copy-Item -LiteralPath $origem -Destination $destino
Write-Host 'SIMULACAO COM SOMENTE O CSV DE TESTE:' -ForegroundColor Cyan
& python $script --pasta $destino
if ($LASTEXITCODE -ne 0) { throw 'Simulacao falhou. Nada foi aplicado.' }
Write-Host ''
Write-Host 'Confira se aparece exatamente: 1 lido; 1 novo; 0 ja existentes.' -ForegroundColor Yellow
$resposta = Read-Host 'Digite APLICAR para gravar este arquivo de teste (qualquer outra resposta cancela)'
if ($resposta -cne 'APLICAR') { Write-Host 'Cancelado. Nenhum dado gravado por este teste.'; exit 0 }
& python $script --pasta $destino --aplicar
if ($LASTEXITCODE -ne 0) { throw 'Falha na importacao. Confira a mensagem acima.' }
Write-Host 'Importacao solicitada. Confira o resultado no SSMS.' -ForegroundColor Green
