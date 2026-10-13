param(
  [string]$Projeto = (Split-Path -Parent $PSScriptRoot),
  [string]$PastaEntrada = "",
  [switch]$Aplicar
)
$ErrorActionPreference = 'Stop'
if (-not $PastaEntrada) { $PastaEntrada = Join-Path $Projeto 'data\raw\2025' }
$script = Join-Path $Projeto 'python\03_carga_incremental_segura_corrigida.py'
$dependencia = Join-Path $Projeto 'python\03_carga_automatica.py'
foreach ($arquivo in @($script,$dependencia)) { if (-not (Test-Path -LiteralPath $arquivo -PathType Leaf)) { throw "Arquivo ausente: $arquivo" } }
if (-not (Test-Path -LiteralPath $PastaEntrada -PathType Container)) { throw "Pasta de entrada ausente: $PastaEntrada" }
$logDir = Join-Path $Projeto 'logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$lockFile = Join-Path $logDir 'carga.lock'
$lock = $null
try {
  try { $lock = [System.IO.File]::Open($lockFile, 'OpenOrCreate', 'ReadWrite', 'None') }
  catch [System.IO.IOException] { Write-Host 'Outra execucao esta em andamento; esta sera ignorada.'; exit 0 }
  $modo = if ($Aplicar) { 'APLICAR' } else { 'SIMULACAO' }
  $log = Join-Path $logDir ("carga_{0}_{1}.log" -f (Get-Date -Format 'yyyyMMdd_HHmmss'),$modo)
  $argumentos = @($script,'--pasta',$PastaEntrada)
  if ($Aplicar) { $argumentos += '--aplicar' }
  "Inicio: $(Get-Date -Format s) | Modo: $modo" | Out-File -LiteralPath $log -Encoding utf8
  & python @argumentos 2>&1 | Out-File -LiteralPath $log -Encoding utf8 -Append
  $codigo = $LASTEXITCODE
  Get-Content -LiteralPath $log
  if ($codigo -ne 0) { throw "Erro na carga (codigo $codigo). Consulte: $log" }
  Write-Host "Concluido. Log: $log"
} finally {
  if ($null -ne $lock) { $lock.Dispose() }
}
