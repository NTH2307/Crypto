# Desfaz o que scripts/setup_windows.ps1 configurou: remove a tarefa agendada
# e os atalhos do ambiente de trabalho.
#
# Uso: .\scripts\remove_windows_setup.ps1

$ErrorActionPreference = "Stop"

$Desktop = [Environment]::GetFolderPath("Desktop")
$TaskName = "CryptoPaperTraderDashboard"

Write-Host "A parar e remover a tarefa agendada '$TaskName'..."
Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

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
