# Configura o dashboard do crypto-paper-trader para arrancar sozinho quando
# inicias sessao no Windows, e cria atalhos no ambiente de trabalho.
#
# Uso: corre este script a partir da pasta do projeto (ou de qualquer lado):
#   .\scripts\setup_windows.ps1
#
# Para desfazer tudo isto: .\scripts\remove_windows_setup.ps1

$ErrorActionPreference = "Stop"

$ProjectDir = Split-Path -Parent $PSScriptRoot
$VenvPythonW = Join-Path $ProjectDir ".venv\Scripts\pythonw.exe"
$AppScript = Join-Path $ProjectDir "webapp\app.py"
$Desktop = [Environment]::GetFolderPath("Desktop")
$TaskName = "CryptoPaperTraderDashboard"

if (-not (Test-Path $VenvPythonW)) {
    Write-Error "Nao encontrei $VenvPythonW`n`nCria o ambiente virtual e instala as dependencias primeiro:`n  python -m venv .venv`n  .venv\Scripts\Activate.ps1`n  pip install -r requirements.txt"
}

Write-Host "A criar tarefa agendada '$TaskName' (arranca o dashboard ao iniciar sessao)..."

$Action = New-ScheduledTaskAction -Execute $VenvPythonW -Argument "`"$AppScript`"" -WorkingDirectory $ProjectDir
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings `
    -Description "Arranca o dashboard local do crypto-paper-trader (webapp/app.py) ao iniciar sessao." | Out-Null

Write-Host "Tarefa criada. A arrancar o dashboard agora, sem esperar pelo proximo login..."
Start-ScheduledTask -TaskName $TaskName
Start-Sleep -Seconds 2

function New-UrlShortcut {
    param([string]$Name, [string]$Url)
    $Path = Join-Path $Desktop "$Name.url"
    $Content = "[InternetShortcut]`r`nURL=$Url`r`n"
    Set-Content -Path $Path -Value $Content -Encoding ASCII
    Write-Host "Atalho criado: $Path"
}

New-UrlShortcut "Crypto - Precos" "http://127.0.0.1:5000/"
New-UrlShortcut "Crypto - Risco" "http://127.0.0.1:5000/risk"
New-UrlShortcut "Crypto - DCA vs Lump Sum" "http://127.0.0.1:5000/dca"

Write-Host ""
Write-Host "Pronto:"
Write-Host "  - 3 atalhos no ambiente de trabalho (Precos, Risco, DCA vs Lump Sum)"
Write-Host "  - O dashboard arranca sozinho sempre que inicias sessao no Windows"
Write-Host "  - Os dados sao sempre em tempo real -- nao ha um 'refresh diario' a"
Write-Host "    esperar: cada vez que abres um atalho, a pagina vai buscar os"
Write-Host "    precos e calcula os indicadores nesse momento."
Write-Host ""
Write-Host "Para parar o dashboard agora: Stop-ScheduledTask -TaskName '$TaskName'"
Write-Host "Para desfazer tudo (tarefa + atalhos): .\scripts\remove_windows_setup.ps1"
