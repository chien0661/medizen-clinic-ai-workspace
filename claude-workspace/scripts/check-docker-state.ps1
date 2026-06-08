Write-Host "=== Docker Desktop services ==="
Get-Service | Where-Object { $_.Name -match 'Docker|com.docker' } | Select-Object Name, Status, StartType | Format-Table -AutoSize | Out-String

Write-Host "=== Docker Desktop processes ==="
Get-Process | Where-Object { $_.Name -match 'Docker' } | Select-Object Name, Id, StartTime | Format-Table -AutoSize | Out-String

Write-Host "=== WSL distros (Docker uses WSL backend) ==="
& wsl --list --verbose 2>&1 | Out-String

Write-Host "=== Docker pipe existence ==="
Test-Path '\\.\pipe\dockerDesktopLinuxEngine'
