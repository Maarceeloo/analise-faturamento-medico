param(
  [string]$Projeto = (Split-Path -Parent $PSScriptRoot),
  [string]$PastaEntrada = "",
  [switch]$HabilitarGravacao
)
$ErrorActionPreference = 'Stop'
if (-not $PastaEntrada) { $PastaEntrada = Join-Path $Projeto 'data\raw\2025' }
if (-not (Test-Path -LiteralPath $PastaEntrada -PathType Container)) { throw "Pasta de entrada ausente: $PastaEntrada" }
$executor = Join-Path $PSScriptRoot 'executar_carga.ps1'
if (-not (Test-Path -LiteralPath $executor)) { throw 'Executor nao encontrado' }
$comando = "& '$($executor.Replace("'","''"))' -Projeto '$($Projeto.Replace("'","''"))' -PastaEntrada '$($PastaEntrada.Replace("'","''"))'"
if ($HabilitarGravacao) { $comando += ' -Aplicar' }
$codificado = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($comando))
$acao = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -NonInteractive -ExecutionPolicy Bypass -EncodedCommand $codificado"
$gatilho = New-ScheduledTaskTrigger -Daily -At '09:30'
$opcoes = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 2)
$nome = 'Faturamento Medico Portfolio - Carga Incremental'
if (Get-ScheduledTask -TaskName $nome -ErrorAction SilentlyContinue) {
  throw "A tarefa '$nome' ja existe. Nao foi substituida."
}
Register-ScheduledTask -TaskName $nome -Action $acao -Trigger $gatilho -Settings $opcoes | Out-Null
$modo = if ($HabilitarGravacao) { 'GRAVACAO ATIVADA' } else { 'SOMENTE SIMULACAO' }
Write-Host "Tarefa instalada: $nome | $modo | diariamente as 09:30"
