# Configura o dashboard do crypto-paper-trader para arrancar sozinho quando
# inicias sessao no Windows, e cria atalhos no ambiente de trabalho.
#
# Usa a pasta de Arranque do Windows (shell:startup) em vez de uma tarefa
# agendada -- nao precisa de privilegios de Administrador.
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
$StartupFolder = [Environment]::GetFolderPath("Startup")
$ShortcutName = "CryptoPaperTraderDashboard.lnk"
$ShortcutPath = Join-Path $StartupFolder $ShortcutName

if (-not (Test-Path $VenvPythonW)) {
    Write-Error "Nao encontrei $VenvPythonW`n`nCria o ambiente virtual e instala as dependencias primeiro:`n  python -m venv .venv`n  .venv\Scripts\Activate.ps1`n  pip install -r requirements.txt"
}

Write-Host "A criar atalho de arranque automatico em $StartupFolder ..."

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $VenvPythonW
$Shortcut.Arguments = "`"$AppScript`""
$Shortcut.WorkingDirectory = $ProjectDir
$Shortcut.WindowStyle = 7  # minimizado
$Shortcut.Save()

Write-Host "Atalho de arranque criado: $ShortcutPath"
Write-Host "A arrancar o dashboard agora, sem esperar pelo proximo login..."

Start-Process -FilePath $VenvPythonW -ArgumentList "`"$AppScript`"" -WorkingDirectory $ProjectDir
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
Write-Host "    (via $ShortcutName na pasta de Arranque)"
Write-Host "  - Os dados sao sempre em tempo real -- nao ha um 'refresh diario' a"
Write-Host "    esperar: cada vez que abres um atalho, a pagina vai buscar os"
Write-Host "    precos e calcula os indicadores nesse momento."
Write-Host ""
Write-Host "Para parar o dashboard agora, abre o Gestor de Tarefas e termina 'pythonw.exe'."
Write-Host "Para desfazer tudo (atalho de arranque + atalhos): .\scripts\remove_windows_setup.ps1"
