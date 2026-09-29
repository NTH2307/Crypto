# Desfaz o que scripts/setup_windows.ps1 configurou: remove o atalho de
# arranque automatico e os atalhos do ambiente de trabalho, e termina o
# dashboard se estiver a correr.
#
# Uso: .\scripts\remove_windows_setup.ps1

$ErrorActionPreference = "Stop"

$Desktop = [Environment]::GetFolderPath("Desktop")
$StartupFolder = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $StartupFolder "CryptoPaperTraderDashboard.lnk"

# Compatibilidade com uma instalacao antiga feita via Tarefa Agendada.
$TaskName = "CryptoPaperTraderDashboard"
Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

if (Test-Path $ShortcutPath) {
    Remove-Item $ShortcutPath -Force
    Write-Host "Atalho de arranque removido: $ShortcutPath"
}

Write-Host "A terminar qualquer processo do dashboard ainda a correr..."
Get-CimInstance Win32_Process -Filter "Name = 'pythonw.exe'" |
    Where-Object { $_.CommandLine -like "*webapp\app.py*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

$Shortcuts = @(
    "Crypto - Precos.url",
    "Crypto - Risco.url",
    "Crypto - DCA vs Lump Sum.url"
)
foreach ($Name in $Shortcuts) {
    $Path = Join-Path $Desktop $Name
    if (Test-Path $Path) {
        Remove-Item $Path -Force
        Write-Host "Atalho removido: $Path"
    }
}

Write-Host "Feito. O dashboard ja nao arranca sozinho e os atalhos foram removidos."
